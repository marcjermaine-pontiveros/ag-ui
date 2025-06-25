"""
WebSocket client handlers for AG-UI demo.
"""
import asyncio
import json
import logging
import websockets
from ag_ui.core.events import EventType

logger = logging.getLogger("ag_ui_demo")

async def ag_ui_client(secure=True):
    """Basic WebSocket client that connects and receives events."""
    from .ssl_utils import get_websocket_uri
    
    uri = get_websocket_uri(secure)
    logger.info(f"Connecting to {uri}...")
    
    try:
        # Connect with SSL context if secure
        if secure:
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            async with websockets.connect(uri, ssl=ssl_context) as websocket:
                await _handle_client_messages(websocket, "Basic Client")
        else:
            async with websockets.connect(uri) as websocket:
                await _handle_client_messages(websocket, "Basic Client")
                
    except ConnectionRefusedError:
        logger.error(f"Could not connect to WebSocket server at {uri}")
        logger.info("Make sure the server is running with: python websocket_demo.py server")
    except Exception as e:
        logger.error(f"Client error: {e}")

async def enhanced_ag_ui_client(secure=True):
    """Enhanced WebSocket client that handles all event types with detailed logging."""
    from .ssl_utils import get_websocket_uri
    
    uri = get_websocket_uri(secure)
    logger.info(f"Enhanced client connecting to {uri}...")
    
    try:
        # Connect with SSL context if secure
        if secure:
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            async with websockets.connect(uri, ssl=ssl_context) as websocket:
                await _handle_enhanced_client_messages(websocket)
        else:
            async with websockets.connect(uri) as websocket:
                await _handle_enhanced_client_messages(websocket)
                
    except ConnectionRefusedError:
        logger.error(f"Could not connect to WebSocket server at {uri}")
        logger.info("Make sure the comprehensive server is running with: python websocket_demo.py comprehensive_server")
    except Exception as e:
        logger.error(f"Enhanced client error: {e}")

async def _handle_client_messages(websocket, client_type):
    """Handle incoming messages for basic client."""
    message_count = 0
    
    logger.info(f"{client_type} connected! Listening for events...")
    
    async for message in websocket:
        try:
            message_count += 1
            event_data = json.loads(message)
            event_type = event_data.get("type", "UNKNOWN")
            
            logger.info(f"📨 [{message_count}] Received: {event_type}")
            
            # Basic event handling
            if event_type == EventType.RUN_STARTED:
                thread_id = event_data.get("threadId", "unknown")
                run_id = event_data.get("runId", "unknown")
                logger.info(f"   🚀 Run started - Thread: {thread_id[:8]}..., Run: {run_id[:8]}...")
                
            elif event_type == EventType.TEXT_MESSAGE_START:
                message_id = event_data.get("messageId", "unknown")
                logger.info(f"   💬 Message starting - ID: {message_id[:8]}...")
                
            elif event_type == EventType.TEXT_MESSAGE_CONTENT:
                delta = event_data.get("delta", "")
                logger.info(f"   📝 Content: '{delta.strip()}'")
                
            elif event_type == EventType.TEXT_MESSAGE_END:
                logger.info(f"   ✅ Message completed")
                
            elif event_type == EventType.RUN_FINISHED:
                logger.info(f"   🏁 Run finished")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {message}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    logger.info(f"{client_type} received {message_count} events total")

async def _handle_enhanced_client_messages(websocket):
    """Handle incoming messages for enhanced client with comprehensive event handling."""
    message_count = 0
    event_counts = {}
    current_message_content = ""
    current_thinking_content = ""
    current_tool_args = ""
    
    logger.info("🔍 Enhanced client connected! Listening for ALL event types...")
    
    async for message in websocket:
        try:
            message_count += 1
            event_data = json.loads(message)
            event_type = event_data.get("type", "UNKNOWN")
            
            # Track event type counts
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            logger.info(f"📨 [{message_count}] Received: {event_type} (#{event_counts[event_type]})")
            
            # Enhanced event handling with detailed logging
            if event_type == EventType.RUN_STARTED:
                thread_id = event_data.get("threadId", "unknown")
                run_id = event_data.get("runId", "unknown")
                timestamp = event_data.get("timestamp", "unknown")
                logger.info(f"   🚀 Run started")
                logger.info(f"      Thread ID: {thread_id}")
                logger.info(f"      Run ID: {run_id}")
                logger.info(f"      Timestamp: {timestamp}")
                
            elif event_type == EventType.STEP_STARTED:
                step_name = event_data.get("stepName", "unknown")
                logger.info(f"   📋 Step started: {step_name}")
                
            elif event_type == EventType.STATE_SNAPSHOT:
                state = event_data.get("state", {})
                logger.info(f"   📊 State snapshot received")
                logger.info(f"      State keys: {list(state.keys())}")
                
            elif event_type == EventType.MESSAGES_SNAPSHOT:
                messages = event_data.get("messages", [])
                logger.info(f"   💬 Messages snapshot: {len(messages)} messages")
                for i, msg in enumerate(messages):
                    role = msg.get("role", "unknown")
                    content_preview = str(msg.get("content", ""))[:50]
                    logger.info(f"      [{i+1}] {role}: {content_preview}...")
                    
            elif event_type == EventType.THINKING_START:
                logger.info(f"   🤔 AI thinking process started")
                current_thinking_content = ""
                
            elif event_type == EventType.THINKING_TEXT_MESSAGE_START:
                message_id = event_data.get("messageId", "unknown")
                logger.info(f"   💭 Thinking message started - ID: {message_id[:8]}...")
                
            elif event_type == EventType.THINKING_TEXT_MESSAGE_CONTENT:
                delta = event_data.get("delta", "")
                current_thinking_content += delta
                logger.info(f"   🧠 Thinking: '{delta.strip()}'")
                
            elif event_type == EventType.THINKING_TEXT_MESSAGE_END:
                logger.info(f"   ✅ Thinking message complete")
                logger.info(f"      Full thought: '{current_thinking_content.strip()}'")
                
            elif event_type == EventType.THINKING_END:
                logger.info(f"   🎯 AI thinking process completed")
                
            elif event_type == EventType.TEXT_MESSAGE_START:
                message_id = event_data.get("messageId", "unknown")
                logger.info(f"   💬 Assistant message starting - ID: {message_id[:8]}...")
                current_message_content = ""
                
            elif event_type == EventType.TEXT_MESSAGE_CONTENT:
                delta = event_data.get("delta", "")
                current_message_content += delta
                logger.info(f"   📝 Content: '{delta.strip()}'")
                
            elif event_type == EventType.TEXT_MESSAGE_END:
                logger.info(f"   ✅ Assistant message completed")
                logger.info(f"      Full message: '{current_message_content.strip()}'")
                
            elif event_type == EventType.TOOL_CALL_START:
                tool_call_id = event_data.get("toolCallId", "unknown")
                tool_name = event_data.get("toolName", "unknown")
                logger.info(f"   🔧 Tool call started: {tool_name}")
                logger.info(f"      Tool call ID: {tool_call_id}")
                current_tool_args = ""
                
            elif event_type == EventType.TOOL_CALL_ARGS:
                args_delta = event_data.get("argsDelta", "")
                current_tool_args += args_delta
                logger.info(f"   🔧 Tool args: '{args_delta}'")
                
            elif event_type == EventType.TOOL_CALL_END:
                logger.info(f"   ✅ Tool call completed")
                logger.info(f"      Full args: {current_tool_args}")
                
            elif event_type == EventType.STATE_DELTA:
                delta = event_data.get("delta", [])
                logger.info(f"   🔄 State delta: {len(delta)} operations")
                for op in delta:
                    logger.info(f"      {op.get('op', 'unknown')} {op.get('path', 'unknown')}")
                    
            elif event_type == EventType.RAW:
                source = event_data.get("source", "unknown")
                data = event_data.get("data", {})
                logger.info(f"   📡 Raw event from {source}")
                logger.info(f"      Data keys: {list(data.keys())}")
                
            elif event_type == EventType.CUSTOM:
                event_subtype = event_data.get("eventType", "unknown")
                data = event_data.get("data", {})
                logger.info(f"   🎛️ Custom event: {event_subtype}")
                logger.info(f"      Data keys: {list(data.keys())}")
                
            elif event_type == EventType.STEP_FINISHED:
                step_name = event_data.get("stepName", "unknown")
                logger.info(f"   ✅ Step completed: {step_name}")
                
            elif event_type == EventType.RUN_FINISHED:
                logger.info(f"   🏁 Run finished")
                
            elif event_type == EventType.RUN_ERROR:
                error = event_data.get("error", "unknown")
                error_code = event_data.get("errorCode", "unknown")
                logger.error(f"   ❌ Run error: {error_code} - {error}")
                
            else:
                logger.info(f"   ❓ Unhandled event type: {event_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {message}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    logger.info("🔍 Enhanced client session completed!")
    logger.info(f"📊 Event Summary:")
    logger.info(f"   Total events: {message_count}")
    for event_type, count in sorted(event_counts.items()):
        logger.info(f"   {event_type}: {count}")
