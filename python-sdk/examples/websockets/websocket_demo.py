import asyncio
import websockets
import json
import uuid
import logging
import ssl
import os
import copy
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ag_ui_demo")

def current_timestamp_ms():
    """Helper function to get current timestamp in milliseconds."""
    return int(datetime.now().timestamp() * 1000)

# Assuming the ag_ui package is installable or in PYTHONPATH
try:
    from ag_ui.core.events import (
        # All event types
        RunStartedEvent,
        TextMessageStartEvent,
        TextMessageContentEvent,
        TextMessageEndEvent,
        TextMessageChunkEvent,
        ThinkingTextMessageStartEvent,
        ThinkingTextMessageContentEvent,
        ThinkingTextMessageEndEvent,
        ToolCallStartEvent,
        ToolCallArgsEvent,
        ToolCallEndEvent,
        ToolCallChunkEvent,
        ThinkingStartEvent,
        ThinkingEndEvent,
        StateSnapshotEvent,
        StateDeltaEvent,
        MessagesSnapshotEvent,
        RawEvent,
        CustomEvent,
        RunFinishedEvent,
        RunErrorEvent,
        StepStartedEvent,
        StepFinishedEvent,
        EventType
    )
    from ag_ui.core.types import (
        Message,
        AssistantMessage,
        UserMessage,
        SystemMessage,
        DeveloperMessage,
        ToolMessage,
        ToolCall,
        FunctionCall,
        Tool,
        Context,
        RunAgentInput
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
SECURE_PORT = 8766

# SSL Configuration
SSL_CERT_PATH = os.environ.get("SSL_CERT_PATH", "cert.pem")
SSL_KEY_PATH = os.environ.get("SSL_KEY_PATH", "key.pem")

def create_ssl_context():
    """
    Create SSL context for secure WebSocket connections.
    Returns None if SSL certificates are not available (falls back to insecure for local development).
    """
    cert_file = Path(SSL_CERT_PATH)
    key_file = Path(SSL_KEY_PATH)
    
    if cert_file.exists() and key_file.exists():
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(cert_file, key_file)
        logger.info("SSL context created successfully")
        return ssl_context
    else:
        logger.warning(f"SSL certificates not found at {SSL_CERT_PATH} and {SSL_KEY_PATH}")
        logger.warning("To generate self-signed certificates for testing, run:")
        logger.warning(f"openssl req -x509 -newkey rsa:4096 -keyout {SSL_KEY_PATH} -out {SSL_CERT_PATH} -days 365 -nodes")
        return None

def get_websocket_uri(secure=True):
    """
    Get the appropriate WebSocket URI based on security preference.
    
    SECURITY WARNING: Only use insecure WebSocket (ws://) for local development!
    Production environments should ALWAYS use secure WebSocket (wss://).
    """
    if secure:
        return f"wss://{HOST}:{SECURE_PORT}"
    else:
        logger.warning("⚠️  SECURITY WARNING: Using insecure WebSocket connection (ws://)!")
        logger.warning("⚠️  This should ONLY be used for local development!")
        logger.warning("⚠️  Production environments must use secure WebSocket (wss://)!")
        return f"ws://{HOST}:{PORT}"

def create_sample_messages():
    """Create sample messages for demonstration."""
    return [
        SystemMessage(
            id=str(uuid.uuid4()),
            role="system",
            content="You are a helpful AI assistant that can use tools to help users."
        ),
        UserMessage(
            id=str(uuid.uuid4()),
            role="user", 
            content="What's the weather like in New York?"
        ),
        AssistantMessage(
            id=str(uuid.uuid4()),
            role="assistant",
            content="I'll check the weather for you in New York.",
            tool_calls=[
                ToolCall(
                    id="call_123",
                    type="function",
                    function=FunctionCall(
                        name="get_weather",
                        arguments='{"city": "New York", "units": "fahrenheit"}'
                    )
                )
            ]
        ),
        ToolMessage(
            id=str(uuid.uuid4()),
            role="tool",
            content='{"temperature": 72, "condition": "sunny", "humidity": 45}',
            tool_call_id="call_123"
        )
    ]

def create_sample_tools():
    """Create sample tools for demonstration."""
    return [
        Tool(
            name="get_weather",
            description="Get current weather information for a city",
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "The city name"},
                    "units": {"type": "string", "enum": ["celsius", "fahrenheit"], "default": "celsius"}
                },
                "required": ["city"]
            }
        ),
        Tool(
            name="calculate",
            description="Perform mathematical calculations",
            parameters={
                "type": "object", 
                "properties": {
                    "expression": {"type": "string", "description": "Mathematical expression to evaluate"}
                },
                "required": ["expression"]
            }
        )
    ]

def create_sample_context():
    """Create sample context for demonstration."""
    return [
        Context(
            description="User's location",
            value="New York, NY, USA"
        ),
        Context(
            description="User's timezone", 
            value="America/New_York"
        )
    ]

def create_sample_state():
    """Create sample state for demonstration."""
    return {
        "conversation_id": str(uuid.uuid4()),
        "user_preferences": {
            "language": "en",
            "temperature_unit": "fahrenheit",
            "time_format": "12h",
            "theme": "light"
        },
        "session_data": {
            "start_time": datetime.now().isoformat(),
            "interaction_count": 0,
            "last_activity": datetime.now().isoformat(),
            "user_id": "user_123"
        },
        "context": {
            "location": "New York",
            "weather_requested": False,
            "current_step": "initialization",
            "tools_available": ["get_weather", "calculate"],
            "last_tool_call": None
        },
        "history": {
            "total_messages": 0,
            "tool_calls_made": 0,
            "errors_encountered": 0,
            "thinking_sessions": 0
        },
        "temporary_data": {
            "pending_operations": [],
            "cache": {},
            "flags": {
                "debug_mode": False,
                "verbose_logging": True
            }
        }
    }

def create_progressive_state_changes():
    """Create a series of JSON Patch operations to demonstrate state evolution."""
    return [
        # Initial setup changes
        [
            {"op": "replace", "path": "/context/current_step", "value": "user_query_received"},
            {"op": "replace", "path": "/session_data/interaction_count", "value": 1},
            {"op": "replace", "path": "/session_data/last_activity", "value": datetime.now().isoformat()},
            {"op": "add", "path": "/temporary_data/current_query", "value": "weather request for New York"}
        ],
        
        # Thinking phase changes
        [
            {"op": "replace", "path": "/context/current_step", "value": "analyzing_request"},
            {"op": "replace", "path": "/history/thinking_sessions", "value": 1},
            {"op": "add", "path": "/temporary_data/thinking_topic", "value": "weather_query_analysis"},
            {"op": "add", "path": "/temporary_data/flags/thinking_active", "value": True}
        ],
        
        # Tool preparation changes
        [
            {"op": "replace", "path": "/context/current_step", "value": "preparing_tool_call"},
            {"op": "replace", "path": "/context/weather_requested", "value": True},
            {"op": "add", "path": "/temporary_data/pending_operations", "value": ["tool_call_get_weather"]},
            {"op": "remove", "path": "/temporary_data/flags/thinking_active"}
        ],
        
        # Tool execution changes
        [
            {"op": "replace", "path": "/context/current_step", "value": "executing_tool"},
            {"op": "replace", "path": "/context/last_tool_call", "value": "get_weather"},
            {"op": "replace", "path": "/history/tool_calls_made", "value": 1},
            {"op": "add", "path": "/temporary_data/active_tool", "value": {"name": "get_weather", "status": "running", "start_time": datetime.now().isoformat()}},
            {"op": "replace", "path": "/temporary_data/pending_operations", "value": []}
        ],
        
        # Tool completion and response changes
        [
            {"op": "replace", "path": "/context/current_step", "value": "processing_tool_result"},
            {"op": "replace", "path": "/temporary_data/active_tool/status", "value": "completed"},
            {"op": "add", "path": "/temporary_data/active_tool/result", "value": {"temperature": 72, "condition": "sunny", "humidity": 45}},
            {"op": "add", "path": "/temporary_data/cache/weather_nyc", "value": {"data": {"temp": 72, "condition": "sunny"}, "timestamp": datetime.now().isoformat(), "ttl": 300}}
        ],
        
        # Response generation changes
        [
            {"op": "replace", "path": "/context/current_step", "value": "generating_response"},
            {"op": "replace", "path": "/history/total_messages", "value": 1},
            {"op": "add", "path": "/temporary_data/response_metadata", "value": {"type": "weather_report", "confidence": 0.95, "sources": ["weather_api"]}}
        ],
        
        # Completion and cleanup changes
        [
            {"op": "replace", "path": "/context/current_step", "value": "completed"},
            {"op": "replace", "path": "/session_data/interaction_count", "value": 2},
            {"op": "replace", "path": "/session_data/last_activity", "value": datetime.now().isoformat()},
            {"op": "remove", "path": "/temporary_data/current_query"},
            {"op": "remove", "path": "/temporary_data/thinking_topic"},
            {"op": "remove", "path": "/temporary_data/active_tool"},
            {"op": "remove", "path": "/temporary_data/response_metadata"},
            {"op": "add", "path": "/history/successful_interactions", "value": 1}
        ]
    ]

def apply_json_patch(state, patch_operations):
    """
    Apply JSON Patch (RFC 6902) operations to a state object.
    This is a robust implementation that validates operations and provides detailed logging.
    """
    logger.debug(f"Applying {len(patch_operations)} JSON Patch operations")
    
    def navigate_to_path(obj, path_parts, create_missing=False):
        """Navigate to a path in the object, optionally creating missing intermediate objects."""
        current = obj
        for i, part in enumerate(path_parts):
            # Handle array indices
            if isinstance(current, list):
                try:
                    index = int(part)
                    if index < 0 or index >= len(current):
                        if create_missing and index == len(current):
                            # Allow appending to end of array
                            current.append(None)
                        else:
                            raise IndexError(f"Array index {index} out of bounds")
                    current = current[index]
                except ValueError:
                    raise ValueError(f"Invalid array index: {part}")
            else:
                # Handle object properties
                if part not in current:
                    if create_missing:
                        # Determine if next part is an array index
                        next_is_array = (i + 1 < len(path_parts) and 
                                       path_parts[i + 1].isdigit())
                        current[part] = [] if next_is_array else {}
                    else:
                        raise KeyError(f"Path does not exist: {'/'.join(path_parts[:i+1])}")
                current = current[part]
        return current
    
    def set_value_at_path(obj, path_parts, value):
        """Set a value at the specified path."""
        if not path_parts:
            raise ValueError("Empty path")
        
        parent = navigate_to_path(obj, path_parts[:-1], create_missing=True)
        key = path_parts[-1]
        
        if isinstance(parent, list):
            try:
                index = int(key)
                if index == len(parent):
                    parent.append(value)
                elif 0 <= index < len(parent):
                    parent[index] = value
                else:
                    raise IndexError(f"Array index {index} out of bounds")
            except ValueError:
                raise ValueError(f"Invalid array index: {key}")
        else:
            parent[key] = value
    
    def get_value_at_path(obj, path_parts):
        """Get a value at the specified path."""
        return navigate_to_path(obj, path_parts, create_missing=False)
    
    def remove_value_at_path(obj, path_parts):
        """Remove a value at the specified path."""
        if not path_parts:
            raise ValueError("Cannot remove root")
        
        parent = navigate_to_path(obj, path_parts[:-1], create_missing=False)
        key = path_parts[-1]
        
        if isinstance(parent, list):
            try:
                index = int(key)
                if 0 <= index < len(parent):
                    removed_value = parent.pop(index)
                    return removed_value
                else:
                    raise IndexError(f"Array index {index} out of bounds")
            except ValueError:
                raise ValueError(f"Invalid array index: {key}")
        else:
            if key in parent:
                removed_value = parent[key]
                del parent[key]
                return removed_value
            else:
                raise KeyError(f"Key does not exist: {key}")
    
    for i, operation in enumerate(patch_operations):
        try:
            op = operation["op"]
            path = operation["path"]
            logger.debug(f"  Operation {i+1}: {op} {path}")
            
            # Parse the path into parts
            path_parts = [p for p in path.split("/") if p] if path != "/" else [""]
            
            if op == "replace":
                value = operation["value"]
                # Get current value for logging
                try:
                    old_value = get_value_at_path(state, path_parts)
                except (KeyError, IndexError):
                    raise ValueError(f"Path does not exist for replace operation: {path}")
                
                set_value_at_path(state, path_parts, value)
                logger.debug(f"    Replaced {path}: {old_value} -> {value}")
                
            elif op == "add":
                value = operation["value"]
                set_value_at_path(state, path_parts, value)
                logger.debug(f"    Added {path}: {value}")
                
            elif op == "remove":
                try:
                    removed_value = remove_value_at_path(state, path_parts)
                    logger.debug(f"    Removed {path}: {removed_value}")
                except (KeyError, IndexError) as e:
                    logger.warning(f"    Path does not exist for remove operation: {path}")
                        
            elif op == "test":
                # RFC 6902 test operation - verify a value matches
                expected_value = operation["value"]
                try:
                    actual_value = get_value_at_path(state, path_parts)
                except (KeyError, IndexError):
                    raise ValueError(f"Test failed: path does not exist: {path}")
                
                if actual_value != expected_value:
                    raise ValueError(f"Test failed: {path} expected {expected_value}, got {actual_value}")
                
                logger.debug(f"    Test passed {path}: {actual_value}")
                
            elif op == "copy":
                # RFC 6902 copy operation
                from_path = operation["from"]
                from_parts = [p for p in from_path.split("/") if p] if from_path != "/" else [""]
                
                # Get value from source
                try:
                    source_value = get_value_at_path(state, from_parts)
                except (KeyError, IndexError):
                    raise ValueError(f"Copy source path does not exist: {from_path}")
                
                # Deep copy the value to avoid reference issues
                import copy
                copied_value = copy.deepcopy(source_value)
                
                # Add to destination
                set_value_at_path(state, path_parts, copied_value)
                logger.debug(f"    Copied from {from_path} to {path}: {copied_value}")
                
            elif op == "move":
                # RFC 6902 move operation
                from_path = operation["from"]
                from_parts = [p for p in from_path.split("/") if p] if from_path != "/" else [""]
                
                # Get and remove value from source
                try:
                    source_value = remove_value_at_path(state, from_parts)
                except (KeyError, IndexError):
                    raise ValueError(f"Move source path does not exist: {from_path}")
                
                # Add to destination
                set_value_at_path(state, path_parts, source_value)
                logger.debug(f"    Moved from {from_path} to {path}: {source_value}")
                
            else:
                raise ValueError(f"Unsupported JSON Patch operation: {op}")
                
        except Exception as e:
            logger.error(f"Failed to apply JSON Patch operation {i+1} ({op} {path}): {e}")
            raise ValueError(f"JSON Patch operation failed: {e}") from e


# --- Comprehensive WebSocket Server Handler ---
async def comprehensive_ag_ui_server_handler(websocket):
    """Comprehensive server handler demonstrating all event types and parameters."""
    logger.info(f"Client connected from {websocket.remote_address}")

    encoder = EventEncoder(protocol=Protocol.WEBSOCKET)

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
        logger.info(f"Sent: {step_started_event.type} - {step_started_event.step_name}")
        await asyncio.sleep(0.1)

        # 3. STATE_SNAPSHOT - Initial state
        logger.info("=== SENDING INITIAL STATE_SNAPSHOT EVENT ===")
        state_snapshot_event = StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            snapshot=current_state,
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(state_snapshot_event))
        logger.info(f"Sent: {state_snapshot_event.type} - Initial state with current_step: {current_state['context']['current_step']}")
        await asyncio.sleep(0.1)

        # 4. STATE_DELTA - User query received (applying JSON Patch operations)
        logger.info("=== SENDING STATE_DELTA EVENT 1: User Query Received ===")
        state_delta_event_1 = StateDeltaEvent(
            type=EventType.STATE_DELTA,
            delta=state_changes[0],  # Initial setup changes
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(state_delta_event_1))
        logger.info(f"Sent: {state_delta_event_1.type} - Transitioning to 'user_query_received'")
        logger.info(f"  Operations: {len(state_changes[0])} JSON Patch operations applied")
        # Apply changes to our tracking state
        apply_json_patch(current_state, state_changes[0])
        log_state_summary(current_state, "after user query received")
        await asyncio.sleep(0.1)

        # 5. MESSAGES_SNAPSHOT - Current conversation
        logger.info("=== SENDING MESSAGES_SNAPSHOT EVENT ===")
        messages_snapshot_event = MessagesSnapshotEvent(
            type=EventType.MESSAGES_SNAPSHOT,
            messages=sample_messages,
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(messages_snapshot_event))
        logger.info(f"Sent: {messages_snapshot_event.type} with {len(sample_messages)} messages")
        await asyncio.sleep(0.1)

        # 6. STATE_DELTA - Entering thinking phase
        logger.info("=== SENDING STATE_DELTA EVENT 2: Entering Thinking Phase ===")
        state_delta_event_2 = StateDeltaEvent(
            type=EventType.STATE_DELTA,
            delta=state_changes[1],  # Thinking phase changes
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(state_delta_event_2))
        logger.info(f"Sent: {state_delta_event_2.type} - Transitioning to 'analyzing_request'")
        apply_json_patch(current_state, state_changes[1])
        log_state_summary(current_state, "after thinking phase started")
        await asyncio.sleep(0.1)

        # 7. THINKING_START - AI thinking process begins
        logger.info("=== SENDING THINKING_START EVENT ===")
        thinking_start_event = ThinkingStartEvent(
            type=EventType.THINKING_START,
            title="Analyzing weather request",
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(thinking_start_event))
        logger.info(f"Sent: {thinking_start_event.type}")
        await asyncio.sleep(0.1)

        # 8. THINKING_TEXT_MESSAGE_START - Start of thinking content
        logger.info("=== SENDING THINKING_TEXT_MESSAGE_START EVENT ===")
        thinking_text_start_event = ThinkingTextMessageStartEvent(
            type=EventType.THINKING_TEXT_MESSAGE_START,
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(thinking_text_start_event))
        logger.info(f"Sent: {thinking_text_start_event.type}")
        await asyncio.sleep(0.1)

        # 9. THINKING_TEXT_MESSAGE_CONTENT - Thinking process content
        thinking_parts = [
            "The user is asking about weather in New York.",
            " I need to use the get_weather tool to fetch current conditions.",
            " Let me prepare the tool call with the appropriate parameters."
        ]
        
        for i, part in enumerate(thinking_parts):
            logger.info(f"=== SENDING THINKING_TEXT_MESSAGE_CONTENT EVENT {i+1} ===")
            thinking_content_event = ThinkingTextMessageContentEvent(
                type=EventType.THINKING_TEXT_MESSAGE_CONTENT,
                delta=part,
                timestamp=current_timestamp_ms()
            )
            await websocket.send(encoder.encode(thinking_content_event))
            logger.info(f"Sent: {thinking_content_event.type} - Content: '{part[:30]}...'")
            await asyncio.sleep(0.1)

        # 10. THINKING_TEXT_MESSAGE_END - End of thinking content
        logger.info("=== SENDING THINKING_TEXT_MESSAGE_END EVENT ===")
        thinking_text_end_event = ThinkingTextMessageEndEvent(
            type=EventType.THINKING_TEXT_MESSAGE_END,
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(thinking_text_end_event))
        logger.info(f"Sent: {thinking_text_end_event.type}")
        await asyncio.sleep(0.1)

        # 11. THINKING_END - End of thinking process
        logger.info("=== SENDING THINKING_END EVENT ===")
        thinking_end_event = ThinkingEndEvent(
            type=EventType.THINKING_END,
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(thinking_end_event))
        logger.info(f"Sent: {thinking_end_event.type}")
        await asyncio.sleep(0.1)

        # 12. STATE_DELTA - Tool preparation phase
        logger.info("=== SENDING STATE_DELTA EVENT 3: Tool Preparation ===")
        state_delta_event_3 = StateDeltaEvent(
            type=EventType.STATE_DELTA,
            delta=state_changes[2],  # Tool preparation changes
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(state_delta_event_3))
        logger.info(f"Sent: {state_delta_event_3.type} - Transitioning to 'preparing_tool_call'")
        logger.info(f"  Pending operations: {state_changes[2][2]['value']}")
        apply_json_patch(current_state, state_changes[2])
        log_state_summary(current_state, "after tool preparation")
        await asyncio.sleep(0.1)

        # 13. STATE_DELTA - Tool execution begins
        logger.info("=== SENDING STATE_DELTA EVENT 4: Tool Execution ===")
        state_delta_event_4 = StateDeltaEvent(
            type=EventType.STATE_DELTA,
            delta=state_changes[3],  # Tool execution changes
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(state_delta_event_4))
        logger.info(f"Sent: {state_delta_event_4.type} - Transitioning to 'executing_tool'")
        logger.info(f"  Active tool status: running")
        apply_json_patch(current_state, state_changes[3])
        log_state_summary(current_state, "after tool execution started")
        await asyncio.sleep(0.1)

        # 14. TOOL_CALL_START - Begin tool execution
        logger.info("=== SENDING TOOL_CALL_START EVENT ===")
        tool_call_start_event = ToolCallStartEvent(
            type=EventType.TOOL_CALL_START,
            tool_call_id=tool_call_id,
            tool_call_name="get_weather",
            parent_message_id=message_id,
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(tool_call_start_event))
        logger.info(f"Sent: {tool_call_start_event.type} - Tool: {tool_call_start_event.tool_call_name}")
        await asyncio.sleep(0.1)

        # 15. TOOL_CALL_ARGS - Tool arguments
        tool_args_parts = [
            '{"city": "New York"',
            ', "units": "fahrenheit"}'
        ]
        
        for i, args_part in enumerate(tool_args_parts):
            logger.info(f"=== SENDING TOOL_CALL_ARGS EVENT {i+1} ===")
            tool_call_args_event = ToolCallArgsEvent(
                type=EventType.TOOL_CALL_ARGS,
                tool_call_id=tool_call_id,
                delta=args_part,
                timestamp=current_timestamp_ms()
            )
            await websocket.send(encoder.encode(tool_call_args_event))
            logger.info(f"Sent: {tool_call_args_event.type} - Args: '{args_part}'")
            await asyncio.sleep(0.1)

        # 16. TOOL_CALL_END - End tool execution
        logger.info("=== SENDING TOOL_CALL_END EVENT ===")
        tool_call_end_event = ToolCallEndEvent(
            type=EventType.TOOL_CALL_END,
            tool_call_id=tool_call_id,
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(tool_call_end_event))
        logger.info(f"Sent: {tool_call_end_event.type}")
        await asyncio.sleep(0.1)

        # 17. STATE_DELTA - Tool completion and result processing
        logger.info("=== SENDING STATE_DELTA EVENT 5: Tool Completion ===")
        state_delta_event_5 = StateDeltaEvent(
            type=EventType.STATE_DELTA,
            delta=state_changes[4],  # Tool completion changes
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(state_delta_event_5))
        logger.info(f"Sent: {state_delta_event_5.type} - Tool completed, caching result")
        logger.info(f"  Tool result: temperature=72°F, condition=sunny")
        logger.info(f"  Cache entry added for NYC weather")
        apply_json_patch(current_state, state_changes[4])
        log_state_summary(current_state, "after tool completion")
        await asyncio.sleep(0.1)
        timestamp=current_timestamp_ms()
        await websocket.send(encoder.encode(tool_call_end_event))
        logger.info(f"Sent: {tool_call_end_event.type}")
        await asyncio.sleep(0.1)

        # 13. STATE_DELTA - State change after tool call
        logger.info("=== SENDING STATE_DELTA EVENT ===")
        state_delta_event = StateDeltaEvent(
            type=EventType.STATE_DELTA,
            delta=[
                {"op": "replace", "path": "/context/weather_requested", "value": True},
                {"op": "add", "path": "/context/last_tool_call", "value": "get_weather"},
                {"op": "replace", "path": "/session_data/interaction_count", "value": 2}
            ],
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(state_delta_event))
        logger.info(f"Sent: {state_delta_event.type} with {len(state_delta_event.delta)} operations")
        await asyncio.sleep(0.1)

        # 14. STATE_DELTA - Response generation phase
        logger.info("=== SENDING STATE_DELTA EVENT 6: Response Generation ===")
        state_delta_event_6 = StateDeltaEvent(
            type=EventType.STATE_DELTA,
            delta=state_changes[5],  # Response generation changes
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(state_delta_event_6))
        logger.info(f"Sent: {state_delta_event_6.type} - Transitioning to 'generating_response'")
        apply_json_patch(current_state, state_changes[5])
        log_state_summary(current_state, "after response generation started")
        await asyncio.sleep(0.1)

        # 15. TEXT_MESSAGE_START - Start response message
        logger.info("=== SENDING TEXT_MESSAGE_START EVENT ===")
        text_message_start_event = TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START, 
            message_id=message_id, 
            role="assistant",
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(text_message_start_event))
        logger.info(f"Sent: {text_message_start_event.type} - Message ID: {message_id}")
        await asyncio.sleep(0.1)

        # 16. TEXT_MESSAGE_CONTENT - Response content parts
        response_parts = [
            "Based on the weather data I retrieved, ",
            "the current weather in New York is 72°F ",
            "with sunny conditions and 45% humidity. ",
            "It's a beautiful day in the city!"
        ]
        
        for i, content_part in enumerate(response_parts):
            logger.info(f"=== SENDING TEXT_MESSAGE_CONTENT EVENT {i+1} ===")
            text_message_content_event = TextMessageContentEvent(
                type=EventType.TEXT_MESSAGE_CONTENT,
                message_id=message_id,
                delta=content_part,
                timestamp=current_timestamp_ms()
            )
            await websocket.send(encoder.encode(text_message_content_event))
            logger.info(f"Sent: {text_message_content_event.type} - Content: '{content_part[:30]}...'")
            await asyncio.sleep(0.1)

        # 16. TEXT_MESSAGE_END - End response message
        logger.info("=== SENDING TEXT_MESSAGE_END EVENT ===")
        text_message_end_event = TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END, 
            message_id=message_id,
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(text_message_end_event))
        logger.info(f"Sent: {text_message_end_event.type} - Message ID: {message_id}")
        await asyncio.sleep(0.1)

        # 17. STATE_DELTA - Completion and cleanup
        logger.info("=== SENDING STATE_DELTA EVENT 7: Completion and Cleanup ===")
        state_delta_event_7 = StateDeltaEvent(
            type=EventType.STATE_DELTA,
            delta=state_changes[6],  # Completion and cleanup changes
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(state_delta_event_7))
        logger.info(f"Sent: {state_delta_event_7.type} - Transitioning to 'completed'")
        logger.info(f"  Cleaning up temporary data and finalizing state")
        apply_json_patch(current_state, state_changes[6])
        log_state_summary(current_state, "after completion and cleanup")
        await asyncio.sleep(0.1)

        # 18. RAW_EVENT - Raw event from underlying system
        logger.info("=== SENDING RAW EVENT ===")
        raw_event = RawEvent(
            type=EventType.RAW,
            event={
                "system": "weather_api",
                "request_id": str(uuid.uuid4()),
                "response_time_ms": 234,
                "cache_hit": False,
                "api_version": "v2.1"
            },
            source="weather_service",
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(raw_event))
        logger.info(f"Sent: {raw_event.type} from source: {raw_event.source}")
        await asyncio.sleep(0.1)

        # 19. CUSTOM_EVENT - Custom application event
        logger.info("=== SENDING CUSTOM EVENT ===")
        custom_event = CustomEvent(
            type=EventType.CUSTOM,
            name="user_engagement_metric",
            value={
                "metric_type": "weather_query_completion",
                "duration_ms": 2340,
                "tools_used": 1,
                "satisfaction_score": 0.95,
                "location": "New York"
            },
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(custom_event))
        logger.info(f"Sent: {custom_event.type} - Name: {custom_event.name}")
        await asyncio.sleep(0.1)

        # 20. STEP_FINISHED - End of processing step
        logger.info("=== SENDING STEP_FINISHED EVENT ===")
        step_finished_event = StepFinishedEvent(
            type=EventType.STEP_FINISHED,
            step_name="weather_query_processing",
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(step_finished_event))
        logger.info(f"Sent: {step_finished_event.type} - {step_finished_event.step_name}")
        await asyncio.sleep(0.1)

        # 21. RUN_FINISHED - End of the interaction
        logger.info("=== SENDING RUN_FINISHED EVENT ===")
        run_finished_event = RunFinishedEvent(
            type=EventType.RUN_FINISHED, 
            thread_id=thread_id, 
            run_id=run_id,
            timestamp=current_timestamp_ms()
        )
        await websocket.send(encoder.encode(run_finished_event))
        logger.info(f"Sent: {run_finished_event.type}")
        await asyncio.sleep(0.1)

        # Final state validation
        logger.info("=== FINAL STATE VALIDATION ===")
        log_state_summary(current_state, "FINAL")
        
        # Validate that we've properly completed the state transitions
        final_step = current_state.get('context', {}).get('current_step')
        if final_step == 'completed':
            logger.info("✅ State transitions completed successfully - final step is 'completed'")
        else:
            logger.warning(f"⚠️ Expected final step 'completed', but got '{final_step}'")
        
        interaction_count = current_state.get('session_data', {}).get('interaction_count', 0)
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
                message=str(e),
                code="DEMO_ERROR",
                timestamp=current_timestamp_ms()
            )
            await websocket.send(encoder.encode(error_event))
            logger.info(f"Sent error event: {error_event.type}")
        except Exception as error_send_exception:
            logger.error(f"Failed to send error event: {error_send_exception}")
    finally:
        try:
            await websocket.close(reason="Handler finished")
            logger.info(f"WebSocket connection for {websocket.remote_address} closed by server.")
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket connection for {websocket.remote_address} was already closed.")
        except Exception as e:
            logger.debug(f"Error during final websocket close for {websocket.remote_address}: {e}")


# Original simple handler for backward compatibility
async def ag_ui_server_handler(websocket):
    """Simple server handler for basic demo (backward compatibility)."""
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
async def start_server_once(secure=True):
    """
    Start a secure WebSocket server for a short duration or until client interaction completes.
    
    Args:
        secure (bool): Whether to use secure WebSocket (wss) or fallback to ws for local development
    """
    ssl_context = create_ssl_context() if secure else None
    port = SECURE_PORT if secure and ssl_context else PORT
    protocol = "wss" if secure and ssl_context else "ws"
    
    if secure and not ssl_context:
        logger.warning("Falling back to insecure WebSocket for local development")
        protocol = "ws"
        port = PORT
    
    logger.info(f"Attempting to start WebSocket server once on {protocol}://{HOST}:{port} for a short duration.")

    stop_event = asyncio.Event()

    async def handler_wrapper(websocket):
        try:
            await ag_ui_server_handler(websocket)
        finally:
            logger.info("Client interaction finished (handler_wrapper), signaling server to stop.")
            stop_event.set()

    server = None
    try:
        server = await websockets.serve(
            handler_wrapper, 
            HOST, 
            port,
            ssl=ssl_context
        )
    except OSError as e:
        logger.error(f"Failed to start server on {protocol}://{HOST}:{port}: {e} (Address already in use?)")
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
async def ag_ui_client(secure=True):
    """
    Secure WebSocket client that connects to the server.
    
    Args:
        secure (bool): Whether to use secure WebSocket (wss) or fallback to ws for local development
    """
    uri = get_websocket_uri(secure)
    
    # SSL context for client (for self-signed certificates in development)
    ssl_context = None
    if secure and uri.startswith("wss://"):
        ssl_context = ssl.create_default_context()
        # For self-signed certificates in development, disable certificate verification
        # WARNING: Only use this in development environments
        if HOST == "localhost":
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            logger.warning("SSL certificate verification disabled for localhost development")
    
    logger.info(f"Connecting to {uri}")
    try:
        connect_kwargs = {"uri": uri, "open_timeout": 5}
        if ssl_context:
            connect_kwargs["ssl"] = ssl_context
            
        async with websockets.connect(**connect_kwargs) as websocket:
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

async def start_comprehensive_server_once(secure=True):
    """
    Start a comprehensive WebSocket server for demonstration.
    
    Args:
        secure (bool): Whether to use secure WebSocket (wss) or fallback to ws for local development
    """
    ssl_context = create_ssl_context() if secure else None
    port = SECURE_PORT if secure and ssl_context else PORT
    protocol = "wss" if secure and ssl_context else "ws"
    
    if secure and not ssl_context:
        logger.warning("Falling back to insecure WebSocket for local development")
        protocol = "ws"
        port = PORT
    
    logger.info(f"Starting comprehensive WebSocket server on {protocol}://{HOST}:{port}")

    stop_event = asyncio.Event()

    async def handler_wrapper(websocket):
        try:
            await comprehensive_ag_ui_server_handler(websocket)
        finally:
            logger.info("Comprehensive demo completed, signaling server to stop.")
            stop_event.set()

    server = None
    try:
        server = await websockets.serve(
            handler_wrapper, 
            HOST, 
            port,
            ssl=ssl_context
        )
    except OSError as e:
        logger.error(f"Failed to start comprehensive server on {protocol}://{HOST}:{port}: {e} (Address already in use?)")
        return
    except Exception as e:
        logger.error(f"Unexpected error starting comprehensive server: {e}", exc_info=True)
        return

    server_lifetime = 30  # seconds - longer for comprehensive demo
    logger.info(f"Comprehensive server will run for {server_lifetime} seconds or until demo finishes.")

    try:
        await asyncio.wait_for(stop_event.wait(), timeout=server_lifetime)
        logger.info("Comprehensive server stop condition met.")
    except asyncio.TimeoutError:
        logger.info(f"Comprehensive server lifetime of {server_lifetime}s reached.")
    except asyncio.CancelledError:
        logger.info("Comprehensive server was cancelled.")
    finally:
        if server:
            logger.info("Comprehensive server shutting down...")
            server.close()
            await server.wait_closed()
            logger.info("Comprehensive server shut down complete.")


async def enhanced_ag_ui_client(secure=True):
    """
    Enhanced WebSocket client that handles all event types comprehensively.
    
    Args:
        secure (bool): Whether to use secure WebSocket (wss) or fallback to ws for local development
    """
    uri = get_websocket_uri(secure)
    
    # SSL context for client (for self-signed certificates in development)
    ssl_context = None
    if secure and uri.startswith("wss://"):
        ssl_context = ssl.create_default_context()
        # For self-signed certificates in development, disable certificate verification
        # WARNING: Only use this in development environments
        if HOST == "localhost":
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            logger.warning("SSL certificate verification disabled for localhost development")
    
    logger.info(f"Enhanced client connecting to {uri}")
    try:
        connect_kwargs = {"uri": uri, "open_timeout": 5}
        if ssl_context:
            connect_kwargs["ssl"] = ssl_context
            
        async with websockets.connect(**connect_kwargs) as websocket:
            logger.info("Enhanced client connected to server.")
            
            # Track message assembly for all message types
            current_messages = {}  # message_id -> content
            current_thinking_content = ""
            current_tool_args = {}  # tool_call_id -> args
            
            # Event counters for comprehensive tracking
            event_counts = {}
            total_events = 0

            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    event_data = json.loads(message)
                    event_type = EventType(event_data["type"])
                    total_events += 1
                    
                    # Count events by type
                    event_counts[event_type.value] = event_counts.get(event_type.value, 0) + 1
                    
                    logger.info(f"[{total_events:2d}] Processed event: {event_type.value}")

                    # Handle each event type comprehensively
                    if event_type == EventType.RUN_STARTED:
                        thread_id = event_data.get("threadId")
                        run_id = event_data.get("runId")
                        timestamp = event_data.get("timestamp")
                        logger.info(f"  🚀 Run Started - Thread: {thread_id}, Run: {run_id}, Time: {timestamp}")
                        
                    elif event_type == EventType.STEP_STARTED:
                        step_name = event_data.get("stepName")
                        logger.info(f"  ▶️  Step Started: {step_name}")
                        
                    elif event_type == EventType.STATE_SNAPSHOT:
                        snapshot = event_data.get("snapshot", {})
                        logger.info(f"  📸 State Snapshot received with {len(snapshot)} keys")
                        if "conversation_id" in snapshot:
                            logger.info(f"    Conversation ID: {snapshot['conversation_id']}")
                        if "user_preferences" in snapshot:
                            prefs = snapshot["user_preferences"]
                            logger.info(f"    User Preferences: {prefs}")
                            
                    elif event_type == EventType.MESSAGES_SNAPSHOT:
                        messages = event_data.get("messages", [])
                        logger.info(f"  💬 Messages Snapshot with {len(messages)} messages:")
                        for i, msg in enumerate(messages):
                            role = msg.get("role", "unknown")
                            content = msg.get("content", "")[:50]
                            logger.info(f"    [{i+1}] {role}: {content}...")
                            
                    elif event_type == EventType.THINKING_START:
                        title = event_data.get("title", "No title")
                        logger.info(f"  🤔 Thinking Started: {title}")
                        current_thinking_content = ""
                        
                    elif event_type == EventType.THINKING_TEXT_MESSAGE_START:
                        logger.info(f"  💭 Thinking Text Started")
                        
                    elif event_type == EventType.THINKING_TEXT_MESSAGE_CONTENT:
                        delta = event_data.get("delta", "")
                        current_thinking_content += delta
                        logger.info(f"  💭 Thinking Content: '{delta}'")
                        
                    elif event_type == EventType.THINKING_TEXT_MESSAGE_END:
                        logger.info(f"  💭 Thinking Text Ended")
                        logger.info(f"  🧠 Complete Thinking: '{current_thinking_content}'")
                        
                    elif event_type == EventType.THINKING_END:
                        logger.info(f"  🤔 Thinking Process Completed")
                        
                    elif event_type == EventType.TOOL_CALL_START:
                        tool_call_id = event_data.get("toolCallId")
                        tool_name = event_data.get("toolCallName")
                        parent_id = event_data.get("parentMessageId")
                        logger.info(f"  🔧 Tool Call Started: {tool_name} (ID: {tool_call_id}, Parent: {parent_id})")
                        current_tool_args[tool_call_id] = ""
                        
                    elif event_type == EventType.TOOL_CALL_ARGS:
                        tool_call_id = event_data.get("toolCallId")
                        delta = event_data.get("delta", "")
                        if tool_call_id in current_tool_args:
                            current_tool_args[tool_call_id] += delta
                        logger.info(f"  🔧 Tool Args Delta: '{delta}'")
                        
                    elif event_type == EventType.TOOL_CALL_END:
                        tool_call_id = event_data.get("toolCallId")
                        complete_args = current_tool_args.get(tool_call_id, "")
                        logger.info(f"  🔧 Tool Call Ended (ID: {tool_call_id})")
                        logger.info(f"  🔧 Complete Args: {complete_args}")
                        
                    elif event_type == EventType.STATE_DELTA:
                        delta = event_data.get("delta", [])
                        logger.info(f"  🔄 State Delta with {len(delta)} operations:")
                        for op in delta:
                            op_type = op.get("op", "unknown")
                            path = op.get("path", "unknown")
                            value = op.get("value", "N/A")
                            logger.info(f"    {op_type}: {path} = {value}")
                            
                    elif event_type == EventType.TEXT_MESSAGE_START:
                        message_id = event_data.get("messageId")
                        role = event_data.get("role")
                        logger.info(f"  📝 Message Started (ID: {message_id}, Role: {role})")
                        current_messages[message_id] = ""
                        
                    elif event_type == EventType.TEXT_MESSAGE_CONTENT:
                        message_id = event_data.get("messageId")
                        delta = event_data.get("delta", "")
                        if message_id in current_messages:
                            current_messages[message_id] += delta
                        logger.info(f"  📝 Message Content: '{delta}'")
                        
                    elif event_type == EventType.TEXT_MESSAGE_END:
                        message_id = event_data.get("messageId")
                        complete_message = current_messages.get(message_id, "")
                        logger.info(f"  📝 Message Ended (ID: {message_id})")
                        logger.info(f"  📋 Complete Message: '{complete_message}'")
                        
                    elif event_type == EventType.RAW:
                        raw_event = event_data.get("event", {})
                        source = event_data.get("source", "unknown")
                        logger.info(f"  🔍 Raw Event from {source}:")
                        if isinstance(raw_event, dict):
                            for key, value in raw_event.items():
                                logger.info(f"    {key}: {value}")
                                
                    elif event_type == EventType.CUSTOM:
                        name = event_data.get("name")
                        value = event_data.get("value", {})
                        logger.info(f"  ⚡ Custom Event: {name}")
                        if isinstance(value, dict):
                            for key, val in value.items():
                                logger.info(f"    {key}: {val}")
                                
                    elif event_type == EventType.STEP_FINISHED:
                        step_name = event_data.get("stepName")
                        logger.info(f"  ✅ Step Finished: {step_name}")
                        
                    elif event_type == EventType.RUN_FINISHED:
                        thread_id = event_data.get("threadId")
                        run_id = event_data.get("runId")
                        logger.info(f"  🏁 Run Finished - Thread: {thread_id}, Run: {run_id}")
                        break
                        
                    elif event_type == EventType.RUN_ERROR:
                        message = event_data.get("message")
                        code = event_data.get("code")
                        logger.error(f"  ❌ Run Error: {message} (Code: {code})")
                        
                    else:
                        logger.info(f"  ❓ Unhandled event type: {event_type.value}")
                        logger.info(f"    Data: {event_data}")

                except asyncio.TimeoutError:
                    logger.warning("Enhanced client timed out waiting for message from server.")
                    break
                except websockets.exceptions.ConnectionClosed:
                    logger.info("Connection closed by server.")
                    break
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    break
            
            # Print comprehensive summary
            logger.info("="*60)
            logger.info("📊 COMPREHENSIVE DEMO SUMMARY")
            logger.info("="*60)
            logger.info(f"Total Events Processed: {total_events}")
            logger.info("Event Type Breakdown:")
            for event_type, count in sorted(event_counts.items()):
                logger.info(f"  {event_type}: {count}")
            logger.info("="*60)

    except ConnectionRefusedError:
        logger.error(f"Connection refused to {uri}. Is the server running?")
    except websockets.exceptions.InvalidURI:
        logger.error(f"Invalid URI: {uri}")
    except websockets.exceptions.WebSocketException as e:
        logger.error(f"WebSocket connection failed for {uri}: {e}")
    except Exception as e:
        logger.error(f"Enhanced client error: {e}", exc_info=True)
    finally:
        logger.info("Enhanced client finished.")


def log_state_summary(state, context=""):
    """Log a summary of the current state for validation."""
    logger.info(f"=== STATE SUMMARY {context} ===")
    logger.info(f"  Current Step: {state.get('context', {}).get('current_step', 'unknown')}")
    logger.info(f"  Interaction Count: {state.get('session_data', {}).get('interaction_count', 0)}")
    logger.info(f"  Tool Calls Made: {state.get('history', {}).get('tool_calls_made', 0)}")
    logger.info(f"  Weather Requested: {state.get('context', {}).get('weather_requested', False)}")
    
    # Log temporary data if it exists
    temp_data = state.get('temporary_data', {})
    if temp_data:
        logger.info(f"  Temporary Data Keys: {list(temp_data.keys())}")
        if 'active_tool' in temp_data:
            tool = temp_data['active_tool']
            logger.info(f"    Active Tool: {tool.get('name', 'unknown')} (status: {tool.get('status', 'unknown')})")
    
    # Log cache if it exists
    cache_data = temp_data.get('cache', {})
    if cache_data:
        logger.info(f"  Cache Entries: {list(cache_data.keys())}")


async def main():
    import sys
    script_name = sys.argv[0]
    
    # Parse command line arguments
    secure = True  # Default to secure
    if "--insecure" in sys.argv:
        secure = False
        logger.warning("Running in insecure mode (for local development only)")
        sys.argv.remove("--insecure")
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "server":
            ssl_context = create_ssl_context() if secure else None
            port = SECURE_PORT if secure and ssl_context else PORT
            protocol = "wss" if secure and ssl_context else "ws"
            
            if secure and not ssl_context:
                logger.warning("SSL certificates not found, falling back to insecure WebSocket")
                protocol = "ws"
                port = PORT
            
            logger.info(f"Starting WebSocket server indefinitely on {protocol}://{HOST}:{port}. Press Ctrl+C to stop.")
            server = None
            try:
                server = await websockets.serve(
                    ag_ui_server_handler, 
                    HOST, 
                    port,
                    ssl=ssl_context
                )
                await asyncio.Event().wait()
            except OSError as e:
                logger.error(f"Failed to start server on {protocol}://{HOST}:{port}: {e} (Address already in use?)")
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
                    
        elif sys.argv[1] == "comprehensive_server":
            ssl_context = create_ssl_context() if secure else None
            port = SECURE_PORT if secure and ssl_context else PORT
            protocol = "wss" if secure and ssl_context else "ws"
            
            if secure and not ssl_context:
                logger.warning("SSL certificates not found, falling back to insecure WebSocket")
                protocol = "ws"
                port = PORT
            
            logger.info(f"Starting comprehensive WebSocket server indefinitely on {protocol}://{HOST}:{port}. Press Ctrl+C to stop.")
            server = None
            try:
                server = await websockets.serve(
                    comprehensive_ag_ui_server_handler, 
                    HOST, 
                    port,
                    ssl=ssl_context
                )
                await asyncio.Event().wait()
            except OSError as e:
                logger.error(f"Failed to start comprehensive server on {protocol}://{HOST}:{port}: {e} (Address already in use?)")
            except KeyboardInterrupt:
                logger.info("\nComprehensive server stopping due to Ctrl+C...")
            except Exception as e:
                logger.error(f"Unexpected error in comprehensive server mode: {e}", exc_info=True)
            finally:
                if server:
                    logger.info("Shutting down comprehensive server...")
                    server.close()
                    await server.wait_closed()
                    logger.info("Comprehensive server stopped.")
                    
        elif sys.argv[1] == "client":
            await asyncio.sleep(0.5)
            await ag_ui_client(secure)
            
        elif sys.argv[1] == "enhanced_client":
            await asyncio.sleep(0.5)
            await enhanced_ag_ui_client(secure)
            
        elif sys.argv[1] == "run_demo":
            logger.info("Running basic demo: Server will start, then client will connect.")
            server_task = None
            client_task = None
            try:
                server_task = asyncio.create_task(start_server_once(secure))
                await asyncio.sleep(1.5)
                if server_task.done():
                    exc = server_task.exception()
                    if exc:
                        logger.error(f"Server task failed to start or finished prematurely: {exc}", exc_info=exc)

                client_task = asyncio.create_task(ag_ui_client(secure))
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
            logger.info("Basic demo finished.")
            
        elif sys.argv[1] == "comprehensive_demo":
            logger.info("Running COMPREHENSIVE demo: All events and parameters will be demonstrated.")
            server_task = None
            client_task = None
            try:
                server_task = asyncio.create_task(start_comprehensive_server_once(secure))
                await asyncio.sleep(2.0)  # Give server more time to start
                if server_task.done():
                    exc = server_task.exception()
                    if exc:
                        logger.error(f"Comprehensive server task failed: {exc}", exc_info=exc)

                client_task = asyncio.create_task(enhanced_ag_ui_client(secure))
                await client_task
                if server_task and not server_task.done():
                    await server_task
            except Exception as e:
                logger.error(f"Exception during comprehensive demo: {e}", exc_info=True)
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
                        task_name = "Enhanced Client" if task == client_task else "Comprehensive Server"
                        if isinstance(result, asyncio.CancelledError):
                            logger.info(f"{task_name} task was cancelled.")
                        elif isinstance(result, Exception):
                            logger.error(f"Exception in {task_name} task: {result}", exc_info=result)
            logger.info("Comprehensive demo finished.")
            
        else:
            print(f"Usage: python {script_name} [server|comprehensive_server|client|enhanced_client|run_demo|comprehensive_demo] [--insecure]")
            print("")
            print("Commands:")
            print("  server              - Run basic WebSocket server")
            print("  comprehensive_server - Run server demonstrating ALL event types")
            print("  client              - Run basic WebSocket client")
            print("  enhanced_client     - Run enhanced client that handles all event types")
            print("  run_demo            - Run basic demo (server + client)")
            print("  comprehensive_demo  - Run COMPREHENSIVE demo covering ALL events")
            print("")
            print("Options:")
            print("  --insecure          - Use insecure WebSocket (ws://) for LOCAL DEVELOPMENT ONLY")
            print("                        ⚠️  WARNING: Do NOT use --insecure in production!")
            print("                        By default, uses secure WebSocket (wss://) if SSL certificates are available")
    else:
        print(f"Usage: python {script_name} [server|comprehensive_server|client|enhanced_client|run_demo|comprehensive_demo] [--insecure]")
        print("")
        print("Commands:")
        print("  server              - Run basic WebSocket server")
        print("  comprehensive_server - Run server demonstrating ALL event types")
        print("  client              - Run basic WebSocket client")
        print("  enhanced_client     - Run enhanced client that handles all event types")
        print("  run_demo            - Run basic demo (server + client)")
        print("  comprehensive_demo  - Run COMPREHENSIVE demo covering ALL events")
        print("")
        print("Options:")
        print("  --insecure          - Use insecure WebSocket (ws://) for LOCAL DEVELOPMENT ONLY")
        print("                        ⚠️  WARNING: Do NOT use --insecure in production!")
        print("                        By default, uses secure WebSocket (wss://) if SSL certificates are available")
        print("")
        print("To generate SSL certificates for testing:")
        print(f"  python generate_ssl_certs.py")
        print(f"  # OR manually:")
        print(f"  openssl req -x509 -newkey rsa:4096 -keyout {SSL_KEY_PATH} -out {SSL_CERT_PATH} -days 365 -nodes")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nDemo script interrupted by user (Ctrl+C at top level).")
