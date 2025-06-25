"""
WebSocket server handlers for AG-UI demo.
"""
import asyncio
import uuid
import copy
import logging
import websockets
from ag_ui.encoder import WebSocketEventEncoder
from ag_ui.core.events import *
from .sample_data import create_sample_messages, create_sample_tools, create_sample_context, create_sample_state
from .state_utils import create_progressive_state_changes, apply_json_patch
from . import current_timestamp_ms, log_state_summary

logger = logging.getLogger("ag_ui_demo")

async def comprehensive_ag_ui_server_handler(websocket):
    """Comprehensive server handler demonstrating all event types and parameters."""
    logger.info(f"Client connected from {websocket.remote_address}")

    encoder = WebSocketEventEncoder()

    # Generate IDs for the demo
    thread_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    message_id = str(uuid.uuid4())
    thinking_message_id = str(uuid.uuid4())
    tool_call_id = str(uuid.uuid4())
    
    # Create sample data
    sample_messages = create_sample_messages()
    sample_tools = create_sample_tools()
    sample_context = create_sample_context()
    sample_state = create_sample_state()
    state_changes = create_progressive_state_changes()
    
    # Track current state for demonstration
    current_state = copy.deepcopy(sample_state)

    try:
        # 1. RUN_STARTED - Start of the interaction
        logger.info("=== SENDING RUN_STARTED EVENT ===")
        run_started_event = RunStartedEvent(
            type=EventType.RUN_STARTED, 
            thread_id=thread_id, 
            run_id=run_id,
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(run_started_event))
        logger.info(f"Sent: {run_started_event.type}")
        await asyncio.sleep(0.1)

        # 2. STEP_STARTED - Beginning of processing step
        logger.info("=== SENDING STEP_STARTED EVENT ===")
        step_started_event = StepStartedEvent(
            type=EventType.STEP_STARTED,
            step_name="weather_query_processing",
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(step_started_event))
        logger.info(f"Sent: {step_started_event.type}")
        await asyncio.sleep(0.1)

        # 3. STATE_SNAPSHOT - Initial state
        logger.info("=== SENDING STATE_SNAPSHOT EVENT ===")
        state_snapshot_event = StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            snapshot=current_state,
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(state_snapshot_event))
        logger.info(f"Sent: {state_snapshot_event.type}")
        log_state_summary(current_state, "Initial ")
        await asyncio.sleep(0.1)

        # 4. MESSAGES_SNAPSHOT - Current conversation
        logger.info("=== SENDING MESSAGES_SNAPSHOT EVENT ===")
        messages_snapshot_event = MessagesSnapshotEvent(
            type=EventType.MESSAGES_SNAPSHOT,
            messages=sample_messages,
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(messages_snapshot_event))
        logger.info(f"Sent: {messages_snapshot_event.type} with {len(sample_messages)} messages")
        await asyncio.sleep(0.1)

        # 5. THINKING_START - Begin reasoning process
        logger.info("=== SENDING THINKING_START EVENT ===")
        thinking_start_event = ThinkingStartEvent(
            type=EventType.THINKING_START,
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(thinking_start_event))
        logger.info(f"Sent: {thinking_start_event.type}")
        await asyncio.sleep(0.1)

        # 6. THINKING_TEXT_MESSAGE_START - Start of thinking content
        logger.info("=== SENDING THINKING_TEXT_MESSAGE_START EVENT ===")
        thinking_text_start_event = ThinkingTextMessageStartEvent(
            type=EventType.THINKING_TEXT_MESSAGE_START,
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(thinking_text_start_event))
        logger.info(f"Sent: {thinking_text_start_event.type}")
        await asyncio.sleep(0.1)

        # 7. THINKING_TEXT_MESSAGE_CONTENT - Streaming thought process
        thinking_content_parts = [
            "I need to check the weather for San Francisco. ",
            "Let me use the weather tool to get current conditions. ",
            "I'll make sure to provide temperature, conditions, and any relevant details."
        ]
        
        for i, content_part in enumerate(thinking_content_parts):
            logger.info(f"=== SENDING THINKING_TEXT_MESSAGE_CONTENT EVENT {i+1}/3 ===")
            thinking_content_event = ThinkingTextMessageContentEvent(
                type=EventType.THINKING_TEXT_MESSAGE_CONTENT,
                delta=content_part,
                timestamp=current_timestamp_ms()
            )
            await websocket.send(encoder.encode(thinking_content_event))
            logger.info(f"Sent: {thinking_content_event.type} - '{content_part.strip()}'")
            await asyncio.sleep(0.1)

        # 8. THINKING_TEXT_MESSAGE_END - End of thinking content
        logger.info("=== SENDING THINKING_TEXT_MESSAGE_END EVENT ===")
        thinking_text_end_event = ThinkingTextMessageEndEvent(
            type=EventType.THINKING_TEXT_MESSAGE_END,
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(thinking_text_end_event))
        logger.info(f"Sent: {thinking_text_end_event.type}")
        await asyncio.sleep(0.1)

        # 9. THINKING_END - Complete reasoning process
        logger.info("=== SENDING THINKING_END EVENT ===")
        thinking_end_event = ThinkingEndEvent(
            type=EventType.THINKING_END,
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(thinking_end_event))
        logger.info(f"Sent: {thinking_end_event.type}")
        await asyncio.sleep(0.1)

        # 10. TEXT_MESSAGE_START - Begin assistant response
        logger.info("=== SENDING TEXT_MESSAGE_START EVENT ===")
        text_start_event = TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant",
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(text_start_event))
        logger.info(f"Sent: {text_start_event.type}")
        await asyncio.sleep(0.1)

        # 11. TEXT_MESSAGE_CONTENT - Streaming message content
        message_content_parts = [
            "I'll help you check the weather in San Francisco. ",
            "Let me use the weather tool to get that information for you."
        ]

        for i, content_part in enumerate(message_content_parts):
            logger.info(f"=== SENDING TEXT_MESSAGE_CONTENT EVENT {i+1}/2 ===")
            text_content_event = TextMessageContentEvent(
                type=EventType.TEXT_MESSAGE_CONTENT,
                message_id=message_id,
                delta=content_part,
                timestamp=current_timestamp_ms()
            )
            await websocket.send(encoder.encode(text_content_event))
            logger.info(f"Sent: {text_content_event.type} - '{content_part.strip()}'")
            await asyncio.sleep(0.1)

        # 12. TOOL_CALL_START - Begin tool execution
        logger.info("=== SENDING TOOL_CALL_START EVENT ===")
        tool_call_start_event = ToolCallStartEvent(
            type=EventType.TOOL_CALL_START,
            tool_call_id=tool_call_id,
            tool_call_name="get_weather",
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(tool_call_start_event))
        logger.info(f"Sent: {tool_call_start_event.type}")
        await asyncio.sleep(0.1)

        # 13. TOOL_CALL_ARGS - Streaming tool arguments
        args_parts = ['{"location": ', '"San Francisco, CA", ', '"unit": "fahrenheit"}']
        
        for i, args_part in enumerate(args_parts):
            logger.info(f"=== SENDING TOOL_CALL_ARGS EVENT {i+1}/3 ===")
            tool_args_event = ToolCallArgsEvent(
                type=EventType.TOOL_CALL_ARGS,
                tool_call_id=tool_call_id,
                delta=args_part,
                timestamp=current_timestamp_ms()
            )
            await websocket.send(encoder.encode(tool_args_event))
            logger.info(f"Sent: {tool_args_event.type} - '{args_part}'")
            await asyncio.sleep(0.1)

        # 14. STATE_DELTA - Apply state changes
        for i, patch_operations in enumerate(state_changes):
            logger.info(f"=== SENDING STATE_DELTA EVENT {i+1}/{len(state_changes)} ===")
            
            # Apply changes to our tracked state
            current_state = apply_json_patch(current_state, patch_operations)
            
            state_delta_event = StateDeltaEvent(
                type=EventType.STATE_DELTA,
                delta=patch_operations,
                timestamp=current_timestamp_ms()
            )
            await websocket.send(encoder.encode(state_delta_event))
            logger.info(f"Sent: {state_delta_event.type} with {len(patch_operations)} operations")
            await asyncio.sleep(0.1)

        # 15. TOOL_CALL_END - Tool execution complete
        logger.info("=== SENDING TOOL_CALL_END EVENT ===")
        tool_call_end_event = ToolCallEndEvent(
            type=EventType.TOOL_CALL_END,
            tool_call_id=tool_call_id,
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(tool_call_end_event))
        logger.info(f"Sent: {tool_call_end_event.type}")
        await asyncio.sleep(0.1)

        # 16. TEXT_MESSAGE_CONTENT - Continue with response
        final_content_parts = [
            "Based on the weather data, ",
            "it's currently 68°F in San Francisco ",
            "with partly cloudy skies and 65% humidity. ",
            "It's a pleasant day!"
        ]

        for i, content_part in enumerate(final_content_parts):
            logger.info(f"=== SENDING TEXT_MESSAGE_CONTENT EVENT (final {i+1}/4) ===")
            text_content_event = TextMessageContentEvent(
                type=EventType.TEXT_MESSAGE_CONTENT,
                message_id=message_id,
                delta=content_part,
                timestamp=current_timestamp_ms()
            )
            await websocket.send(encoder.encode(text_content_event))
            logger.info(f"Sent: {text_content_event.type} - '{content_part.strip()}'")
            await asyncio.sleep(0.1)

        # 17. TEXT_MESSAGE_END - Complete message assembly
        logger.info("=== SENDING TEXT_MESSAGE_END EVENT ===")
        text_end_event = TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id,
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(text_end_event))
        logger.info(f"Sent: {text_end_event.type}")
        await asyncio.sleep(0.1)

        # 18. RAW - Raw system event with source attribution
        logger.info("=== SENDING RAW EVENT ===")
        raw_event = RawEvent(
            type=EventType.RAW,
            event={"system": "weather_service", "status": "completed", "response_time_ms": 245},
            source="weather_api",
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(raw_event))
        logger.info(f"Sent: {raw_event.type}")
        await asyncio.sleep(0.1)

        # 19. CUSTOM - Custom application-specific event
        logger.info("=== SENDING CUSTOM EVENT ===")
        custom_event = CustomEvent(
            type=EventType.CUSTOM,
            name="weather_analysis_complete",
            value={
                "analysis": {
                    "location": "San Francisco, CA",
                    "weather_quality": "good",
                    "recommendation": "Great day for outdoor activities"
                },
                "metadata": {
                    "analysis_duration_ms": 150,
                    "confidence": 0.95
                }
            },
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(custom_event))
        logger.info(f"Sent: {custom_event.type}")
        await asyncio.sleep(0.1)

        # 20. STEP_FINISHED - Complete processing step
        logger.info("=== SENDING STEP_FINISHED EVENT ===")
        step_finished_event = StepFinishedEvent(
            type=EventType.STEP_FINISHED,
            step_name="weather_query_processing",
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(step_finished_event))
        logger.info(f"Sent: {step_finished_event.type}")
        await asyncio.sleep(0.1)

        # 21. RUN_FINISHED - End of interaction
        logger.info("=== SENDING RUN_FINISHED EVENT ===")
        run_finished_event = RunFinishedEvent(
            type=EventType.RUN_FINISHED,
            thread_id=thread_id,
            run_id=run_id,
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(run_finished_event))
        logger.info(f"Sent: {run_finished_event.type}")

        # Summary
        logger.info("=== COMPREHENSIVE DEMO SUMMARY ===")
        interaction_count = current_state.get('session', {}).get('interaction_count', 0)
        logger.info(f"✅ Successfully demonstrated all 21 event types")
        logger.info(f"✅ Processed {len(sample_messages)} message types")
        logger.info(f"✅ Applied {len(state_changes)} state transitions")
        logger.info(f"✅ Total interactions processed: {interaction_count}")
        
        # Check that temporary data was cleaned up
        temp_data = current_state.get('temporary_data', {})
        if not temp_data:
            logger.info("✅ Temporary data successfully cleaned up")
        else:
            logger.info(f"ℹ️ Remaining temporary data: {list(temp_data.keys())}")

        logger.info("=== COMPREHENSIVE DEMO COMPLETED ===")
        logger.info(f"Demonstrated 21 different event types with all their parameters")
        logger.info(f"Applied {len([item for sublist in state_changes for item in sublist])} JSON Patch operations across 7 state transitions")

    except websockets.exceptions.ConnectionClosedOK:
        logger.info(f"WebSocket connection for {websocket.remote_address} was closed gracefully during demo.")
    except websockets.exceptions.ConnectionClosedError as e:
        logger.warning(f"WebSocket connection for {websocket.remote_address} was closed with error during demo: {e}")
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"WebSocket connection for {websocket.remote_address} was closed during demo: {e}")
    except Exception as e:
        logger.error(f"Error in comprehensive server handler: {e}", exc_info=True)
        
        # Send error event if possible
        try:
            error_event = RunErrorEvent(
                type=EventType.RUN_ERROR,
                error=str(e),
                error_code="DEMO_ERROR",
                timestamp=current_timestamp_ms()
            )
            await websocket.send(encoder.encode(error_event))
        except:
            # If we can't send the error event, just log it
            logger.error("Failed to send error event to client")

async def ag_ui_server_handler(websocket):
    """Simple server handler for basic demo (backward compatibility)."""
    logger.info(f"Client connected from {websocket.remote_address}")

    encoder = WebSocketEventEncoder()

    thread_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    message_id = str(uuid.uuid4()) # This will be camelCased to messageId in JSON

    try:
        # Send RUN_STARTED event
        logger.info("Sending RUN_STARTED event...")
        run_started_event = RunStartedEvent(
            type=EventType.RUN_STARTED, 
            thread_id=thread_id, 
            run_id=run_id,
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(run_started_event))

        # Wait a bit
        await asyncio.sleep(0.5)

        # Send TEXT_MESSAGE_START event
        logger.info("Sending TEXT_MESSAGE_START event...")
        text_start_event = TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant",
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(text_start_event))

        # Send some TEXT_MESSAGE_CONTENT events
        content_parts = ["Hello! ", "This is a ", "streaming message ", "from the AG-UI ", "WebSocket demo."]
        for part in content_parts:
            await asyncio.sleep(0.1)
            logger.info(f"Sending TEXT_MESSAGE_CONTENT event: '{part.strip()}'")
            text_content_event = TextMessageContentEvent(
                type=EventType.TEXT_MESSAGE_CONTENT,
                message_id=message_id,
                delta=part,
                timestamp=current_timestamp_ms()
            )
            await websocket.send(encoder.encode(text_content_event))

        # Send TEXT_MESSAGE_END event
        await asyncio.sleep(0.1)
        logger.info("Sending TEXT_MESSAGE_END event...")
        text_end_event = TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id,
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(text_end_event))

        # Send RUN_FINISHED event
        await asyncio.sleep(0.5)
        logger.info("Sending RUN_FINISHED event...")
        run_finished_event = RunFinishedEvent(
            type=EventType.RUN_FINISHED,
            thread_id=thread_id,
            run_id=run_id,
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(run_finished_event))

        logger.info("Demo completed successfully!")

    except websockets.exceptions.ConnectionClosedOK:
        logger.info(f"WebSocket connection for {websocket.remote_address} was closed gracefully during demo.")
    except websockets.exceptions.ConnectionClosedError as e:
        logger.warning(f"WebSocket connection for {websocket.remote_address} was closed with error during demo: {e}")
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"WebSocket connection for {websocket.remote_address} was closed during demo: {e}")
    except Exception as e:
        logger.error(f"Error in basic server handler: {e}", exc_info=True)
