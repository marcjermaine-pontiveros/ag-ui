# AG-UI Python SDK WebSocket Examples

This directory contains WebSocket example scripts demonstrating how to use the AG-UI Python SDK with comprehensive WebSocket communication.

## WebSocket Demo

The `websocket_demo.py` script demonstrates secure WebSocket communication using the AG-UI protocol with comprehensive coverage of ALL event types and parameters.

## Event Encoder Architecture

The AG-UI Python SDK uses a clean, maintainable encoder architecture with dedicated classes for different communication protocols:

### SSE (Server-Sent Events) Encoding
```python
from ag_ui.encoder import EventEncoder

# For SSE/HTTP streaming
encoder = EventEncoder()
sse_data = encoder.encode(event)
# Output: "data: {...json...}\n\n"
```

### WebSocket Encoding  
```python
from ag_ui.encoder import WebSocketEventEncoder

# For WebSocket connections
encoder = WebSocketEventEncoder()
json_data = encoder.encode(event)        # JSON string
binary_data = encoder.encode_binary(event)  # UTF-8 bytes
can_compress = encoder.can_compress()     # True
```

### Benefits
- **Single Responsibility**: Each encoder has one clear purpose
- **Better Performance**: Protocol-specific optimizations
- **Extensibility**: Easy to add new transport protocols  
- **Maintainability**: Changes isolated to specific protocols
- **Clean API**: No confusing protocol parameters

## Project Structure

The WebSocket demo has been refactored for better maintainability:

```
websocket_demo.py           # Main demo script (refactored)
generate_ssl_certs.py       # SSL certificate generation
utils/
├── __init__.py            # Common utilities
├── sample_data.py         # Sample data creation functions
├── ssl_utils.py           # SSL/security utilities
├── state_utils.py         # State management and JSON Patch operations
├── server_handlers.py     # WebSocket server handlers
└── client_handlers.py     # WebSocket client handlers
```

### Benefits of Refactored Structure
- **Modular Design**: Utilities organized by function
- **Maintainability**: Easier to modify specific components
- **Reusability**: Utilities can be imported by other projects
- **Clarity**: Main demo file focuses on orchestration
- **Testing**: Individual modules can be tested separately

### Available Demos

1. **Basic Demo** (`run_demo`) - Simple demonstration with core events
2. **Comprehensive Demo** (`comprehensive_demo`) - **COMPLETE** demonstration of ALL 20+ event types

### Security Features

- **Secure WebSocket (WSS)**: Uses TLS encryption by default
- **SSL Certificate Support**: Automatically uses SSL certificates if available
- **Graceful Fallback**: Falls back to insecure WebSocket for local development when certificates are unavailable
- **Development Mode**: Includes `--insecure` flag for testing without SSL

## Quick Start

1. **Generate SSL Certificates** (for secure connections):
   ```bash
   python generate_ssl_certs.py
   ```

2. **Run the Comprehensive Demo** (recommended):
   ```bash
   # Secure mode (default) - demonstrates ALL events
   python websocket_demo.py comprehensive_demo
   
   # Insecure mode (for testing)
   python websocket_demo.py comprehensive_demo --insecure
   ```

3. **Run Individual Components**:
   ```bash
   # Start server only
   python websocket_demo.py comprehensive_server
   
   # Connect client only (in another terminal)
   python websocket_demo.py enhanced_client
   ```

### Available Commands

#### Server Commands
- `python websocket_demo.py server [--insecure]` - Run basic WebSocket server
- `python websocket_demo.py comprehensive_server [--insecure]` - Run server demonstrating ALL events

#### Client Commands  
- `python websocket_demo.py client [--insecure]` - Run basic WebSocket client
- `python websocket_demo.py enhanced_client [--insecure]` - Run enhanced client handling ALL events

#### Demo Commands
- `python websocket_demo.py run_demo [--insecure]` - Run basic demo (server + client)
- `python websocket_demo.py comprehensive_demo [--insecure]` - **Run COMPREHENSIVE demo covering ALL events**

### Comprehensive Demo Features

The comprehensive demo demonstrates **ALL 20+ event types** with realistic parameters:

#### 🚀 **Run Management Events**
- `RUN_STARTED` - Start of interaction with thread and run IDs
- `RUN_FINISHED` - End of interaction
- `RUN_ERROR` - Error handling with codes and messages

#### 📝 **Message Events**
- `TEXT_MESSAGE_START` - Begin assistant message
- `TEXT_MESSAGE_CONTENT` - Streaming message content 
- `TEXT_MESSAGE_END` - Complete message assembly
- `TEXT_MESSAGE_CHUNK` - Alternative chunked content

#### 🤔 **Thinking Events**
- `THINKING_START` - AI reasoning process begins
- `THINKING_TEXT_MESSAGE_START` - Start of thinking content
- `THINKING_TEXT_MESSAGE_CONTENT` - Streaming thought process
- `THINKING_TEXT_MESSAGE_END` - End of thinking content
- `THINKING_END` - Complete reasoning process

#### 🔧 **Tool Call Events**
- `TOOL_CALL_START` - Begin tool execution
- `TOOL_CALL_ARGS` - Streaming tool arguments
- `TOOL_CALL_END` - Tool execution complete
- `TOOL_CALL_CHUNK` - Alternative chunked tool calls

#### 📊 **State Management Events**
- `STATE_SNAPSHOT` - Complete application state
- `STATE_DELTA` - JSON Patch state changes
- `MESSAGES_SNAPSHOT` - Complete conversation history

#### ⚙️ **Process Events**
- `STEP_STARTED` - Begin processing step
- `STEP_FINISHED` - Complete processing step

#### 🔍 **System Events**
- `RAW` - Raw system events with source attribution
- `CUSTOM` - Custom application-specific events

### Event Parameters Coverage

Each event demonstrates **ALL available parameters**:

- **Timestamps** - All events include proper timestamp handling
- **IDs and References** - Thread IDs, run IDs, message IDs, tool call IDs
- **Content and Deltas** - Streaming content with proper assembly
- **Tool Integration** - Complete tool call lifecycle with arguments
- **State Management** - JSON Patch operations for state changes
- **Metadata** - Source attribution, error codes, custom metrics

### Example Output

The comprehensive demo produces detailed output like:

```
[1] Processed event: RUN_STARTED
  🚀 Run Started - Thread: abc123, Run: def456, Time: 1750842998715

[5] Processed event: THINKING_START  
  🤔 Thinking Started: Analyzing weather request

[12] Processed event: TOOL_CALL_START
  🔧 Tool Call Started: get_weather (ID: xyz789, Parent: msg123)

[24] Processed event: CUSTOM
  ⚡ Custom Event: user_engagement_metric
    metric_type: weather_query_completion
    tools_used: 1
    satisfaction_score: 0.95

📊 COMPREHENSIVE DEMO SUMMARY
Total Events Processed: 26
Event Type Breakdown:
  TEXT_MESSAGE_CONTENT: 4
  TOOL_CALL_ARGS: 2
  THINKING_TEXT_MESSAGE_CONTENT: 3
  [... all event types with counts]
```

### SSL Certificate Configuration

The script looks for SSL certificates in the following locations:
- Certificate: `cert.pem` (configurable via `SSL_CERT_PATH` environment variable)
- Private Key: `key.pem` (configurable via `SSL_KEY_PATH` environment variable)

### Environment Variables

- `SSL_CERT_PATH`: Path to SSL certificate file (default: `cert.pem`)
- `SSL_KEY_PATH`: Path to SSL private key file (default: `key.pem`)

### Security Notes

⚠️ **Important Security Information**:

1. **Self-signed certificates** are included for local development only
2. **Never use self-signed certificates in production**
3. The `--insecure` flag is for local testing only
4. Always use proper CA-signed certificates in production environments
5. The demo disables certificate verification for localhost connections with self-signed certificates

### Production Deployment

For production deployment:

1. Obtain proper SSL certificates from a trusted Certificate Authority
2. Remove the `--insecure` flag and certificate verification bypass
3. Use environment variables to specify certificate paths
4. Consider using a reverse proxy (nginx, Apache) for SSL termination

### Integration Examples

The comprehensive demo provides real-world examples for:

- **AI Assistant Applications** - Complete conversation flows
- **Tool-Using Agents** - Weather API integration example  
- **State Management** - User preferences and session data
- **Real-time Streaming** - Message and thinking content
- **Error Handling** - Proper error event usage
- **Custom Metrics** - Application-specific event tracking

### Troubleshooting

**SSL Certificate Issues**:
```bash
# Generate new certificates
python generate_ssl_certs.py

# Or run in insecure mode
python websocket_demo.py comprehensive_demo --insecure
```

**Connection Issues**:
- Check if the port is already in use
- Verify firewall settings
- Ensure SSL certificates are valid and readable

### Dependencies

The examples require:
- `websockets` library
- `ssl` module (built-in)
- `openssl` (for certificate generation)

Install dependencies:
```bash
pip install websockets
```

### Development and Testing

Use the comprehensive demo to:
- **Test complete event flows** in your applications
- **Validate event handling** logic
- **Debug WebSocket communication** issues
- **Understand event sequencing** and timing
- **Learn proper parameter usage** for each event type
