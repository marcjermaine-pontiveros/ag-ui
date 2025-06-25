import asyncio
import websockets
import json
import uuid
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ag_ui_demo")

# Assuming the ag_ui package is installable or in PYTHONPATH
try:
    from ag_ui.core.events import (
        RunStartedEvent,
        TextMessageStartEvent,
        TextMessageContentEvent,
        TextMessageEndEvent,
        RunFinishedEvent,
        EventType
    )
    from ag_ui.encoder import EventEncoder, Protocol
except ImportError as e:
    logger.error(f"Failed to import ag_ui modules: {e}. Ensure 'ag-ui-protocol' is installed and in PYTHONPATH.")
    logger.error("You can install it in editable mode from the python-sdk directory: pip install -e .")
    import sys
    sys.exit(1)

# Configuration Constants
HOST = "localhost"
PORT = 8765


# --- WebSocket Server ---
async def ag_ui_server_handler(websocket):
    logger.info(f"Client connected from {websocket.remote_address}")

    encoder = EventEncoder(protocol=Protocol.WEBSOCKET)

    thread_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    message_id = str(uuid.uuid4()) # This will be camelCased to messageId in JSON

    try:
        run_started_event = RunStartedEvent(type=EventType.RUN_STARTED, thread_id=thread_id, run_id=run_id)
        await websocket.send(encoder.encode(run_started_event))
        logger.info(f"Sent: {run_started_event.type}")
        await asyncio.sleep(0.05)

        text_message_start_event = TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START, message_id=message_id, role="assistant"
        )
        await websocket.send(encoder.encode(text_message_start_event))
        logger.info(f"Sent: {text_message_start_event.type}")
        await asyncio.sleep(0.05)

        text_message_content_event = TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT, message_id=message_id, delta="Hello from AG-UI WebSocket server!"
        )
        await websocket.send(encoder.encode(text_message_content_event))
        logger.info(f"Sent: {text_message_content_event.type}")
        await asyncio.sleep(0.05)

        text_message_content_event_2 = TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT, message_id=message_id, delta=" This is a demonstration of WebSocket communication."
        )
        await websocket.send(encoder.encode(text_message_content_event_2))
        logger.info(f"Sent: {text_message_content_event_2.type} (2)")
        await asyncio.sleep(0.05)

        text_message_end_event = TextMessageEndEvent(type=EventType.TEXT_MESSAGE_END, message_id=message_id)
        await websocket.send(encoder.encode(text_message_end_event))
        logger.info(f"Sent: {text_message_end_event.type}")
        await asyncio.sleep(0.05)

        run_finished_event = RunFinishedEvent(type=EventType.RUN_FINISHED, thread_id=thread_id, run_id=run_id)
        await websocket.send(encoder.encode(run_finished_event))
        logger.info(f"Sent: {run_finished_event.type}")

    except websockets.exceptions.ConnectionClosedOK:
        logger.info(f"Client {websocket.remote_address} disconnected normally.")
    except websockets.exceptions.ConnectionClosedError as e:
        logger.warning(f"Client {websocket.remote_address} disconnected with error: {e}")
    except Exception as e:
        logger.error(f"An error occurred with client {websocket.remote_address}: {e}", exc_info=True)
    finally:
        logger.info(f"Connection handler for {websocket.remote_address} exiting.")
        # Attempt to close the connection gracefully if it's not already closed.
        # The close() method is idempotent.
        try:
            await websocket.close(reason="Handler finished")
            logger.info(f"WebSocket connection for {websocket.remote_address} closed by server.")
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket connection for {websocket.remote_address} was already closed.")
        except Exception as e:
            logger.debug(f"Error during final websocket close for {websocket.remote_address}: {e}")


# Single-shot helper to host for X seconds or until one client interaction completes
async def start_server_once():
    logger.info(f"Attempting to start WebSocket server once on ws://{HOST}:{PORT} for a short duration.")

    stop_event = asyncio.Event()

    async def handler_wrapper(websocket):
        try:
            await ag_ui_server_handler(websocket)
        finally:
            logger.info("Client interaction finished (handler_wrapper), signaling server to stop.")
            stop_event.set()

    server = None
    try:
        server = await websockets.serve(handler_wrapper, HOST, PORT)
    except OSError as e:
        logger.error(f"Failed to start server on ws://{HOST}:{PORT}: {e} (Address already in use?)")
        return
    except Exception as e:
        logger.error(f"Unexpected error starting server: {e}", exc_info=True)
        return

    server_lifetime = 5  # seconds
    logger.info(f"Server will run for {server_lifetime} seconds or until client interaction finishes.")

    try:
        await asyncio.wait_for(stop_event.wait(), timeout=server_lifetime)
        logger.info("Server stop condition met (event set or timeout).")
    except asyncio.TimeoutError:
        logger.info(f"Server lifetime of {server_lifetime}s reached.")
    except asyncio.CancelledError:
        logger.info("start_server_once's stop_event.wait() was cancelled.")
    finally:
        if server:
            logger.info("Server (start_server_once) shutting down...")
            server.close()
            await server.wait_closed()
            logger.info("Server (start_server_once) shut down complete.")


# --- WebSocket Client ---
async def ag_ui_client():
    uri = f"ws://{HOST}:{PORT}"
    logger.info(f"Connecting to {uri}")
    try:
        async with websockets.connect(uri, open_timeout=5) as websocket:
            logger.info("Connected to server.")
            full_message = ""
            current_message_id = None

            while True:
                try:
                    message_str = await asyncio.wait_for(websocket.recv(), timeout=5.0)

                    try:
                        event_data = json.loads(message_str)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Received non-JSON message: '{message_str[:100]}...' (Type: {type(message_str)}). Error: {e}")
                        continue

                    raw_event_type_str = event_data.get('type')
                    # logger.debug(f"Received raw event data: {event_data}") # Use debug for very verbose

                    try:
                        event_type = EventType(raw_event_type_str)
                    except ValueError:
                        logger.warning(f"Unknown event type '{raw_event_type_str}' received. Full event: {event_data}")
                        continue

                    logger.info(f"Processed event type: {event_type.value}")

                    # Use .get("messageId") due to Pydantic's camelCase alias generator
                    message_id_from_event = event_data.get("messageId")

                    if event_type is EventType.TEXT_MESSAGE_START:
                        current_message_id = message_id_from_event
                        full_message = ""
                        logger.info(f"  Message Start (ID: {current_message_id})")
                    elif event_type is EventType.TEXT_MESSAGE_CONTENT:
                        if message_id_from_event == current_message_id:
                            delta = event_data.get("delta", "")
                            full_message += delta
                            logger.info(f"  Content delta: '{delta}'")
                    elif event_type is EventType.TEXT_MESSAGE_END:
                        if message_id_from_event == current_message_id:
                            logger.info(f"  Message End (ID: {current_message_id})")
                            logger.info(f"  Full assembled message: '{full_message}'")
                            current_message_id = None
                    elif event_type is EventType.RUN_FINISHED:
                        logger.info("Run finished. Closing client.")
                        break
                    else:
                        # Log threadId and runId for other event types if present
                        thread_id_log = event_data.get("threadId", "N/A")
                        run_id_log = event_data.get("runId", "N/A")
                        logger.info(f"  Unhandled event type {event_type.value}. ThreadID: {thread_id_log}, RunID: {run_id_log}. FullData: {event_data}")


                except asyncio.TimeoutError:
                    logger.warning("Client timed out waiting for message from server.")
                    break
                except websockets.exceptions.ConnectionClosed:
                    logger.info("Connection closed by server.")
                    break
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    break

    except ConnectionRefusedError:
        logger.error(f"Connection refused to {uri}. Is the server running?")
    except websockets.exceptions.InvalidURI:
        logger.error(f"Invalid URI: {uri}")
    except websockets.exceptions.WebSocketException as e:
        logger.error(f"WebSocket connection failed for {uri}: {e}")
    except Exception as e:
        logger.error(f"Client error: {e}", exc_info=True)
    finally:
        logger.info("Client finished.")

async def main():
    import sys
    script_name = sys.argv[0]
    if len(sys.argv) > 1:
        if sys.argv[1] == "server":
            logger.info(f"Starting WebSocket server indefinitely on ws://{HOST}:{PORT}. Press Ctrl+C to stop.")
            server = None
            try:
                server = await websockets.serve(ag_ui_server_handler, HOST, PORT)
                await asyncio.Event().wait()
            except OSError as e:
                 logger.error(f"Failed to start server on ws://{HOST}:{PORT}: {e} (Address already in use?)")
            except KeyboardInterrupt:
                logger.info("\nServer stopping due to Ctrl+C...")
            except Exception as e:
                logger.error(f"Unexpected error in server mode: {e}", exc_info=True)
            finally:
                if server:
                    logger.info("Shutting down server...")
                    server.close()
                    await server.wait_closed()
                    logger.info("Server stopped.")
        elif sys.argv[1] == "client":
            await asyncio.sleep(0.5)
            await ag_ui_client()
        elif sys.argv[1] == "run_demo":
            logger.info("Running demo: Server will start, then client will connect.")
            server_task = None
            client_task = None
            try:
                server_task = asyncio.create_task(start_server_once())
                await asyncio.sleep(1.5)
                if server_task.done():
                    exc = server_task.exception()
                    if exc:
                        logger.error(f"Server task failed to start or finished prematurely: {exc}", exc_info=exc)

                client_task = asyncio.create_task(ag_ui_client())
                await client_task
                if server_task and not server_task.done():
                    await server_task
            except Exception as e:
                logger.error(f"Exception during demo run orchestration: {e}", exc_info=True)
            finally:
                tasks_to_cancel_and_gather = []
                if client_task and not client_task.done():
                    client_task.cancel()
                    tasks_to_cancel_and_gather.append(client_task)
                if server_task and not server_task.done():
                    server_task.cancel()
                    tasks_to_cancel_and_gather.append(server_task)

                if tasks_to_cancel_and_gather:
                    results = await asyncio.gather(*tasks_to_cancel_and_gather, return_exceptions=True)
                    for i, result in enumerate(results):
                        task = tasks_to_cancel_and_gather[i]
                        task_name = "Client" if task == client_task else "Server"
                        if isinstance(result, asyncio.CancelledError):
                            logger.info(f"{task_name} task was cancelled.")
                        elif isinstance(result, Exception):
                            logger.error(f"Exception in {task_name} task after gather: {result}", exc_info=result)
            logger.info("Demo finished.")
        else:
            print(f"Usage: python {script_name} [server|client|run_demo]")
    else:
        print(f"Usage: python {script_name} [server|client|run_demo]")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nDemo script interrupted by user (Ctrl+C at top level).")
