# AG-UI Python SDK Examples

This directory contains example scripts demonstrating how to use the AG-UI Python SDK.

## Examples Overview

### WebSocket Examples

The `websockets/` directory contains comprehensive WebSocket communication examples:

- **WebSocket Demo** (`websockets/websocket_demo.py`) - Secure WebSocket communication with ALL event types
- **SSL Certificate Generator** (`websockets/generate_ssl_certs.py`) - Generate self-signed certificates for testing
- **WebSocket README** (`websockets/README.md`) - Detailed WebSocket examples documentation

### Quick Start with WebSocket Examples

1. **Navigate to the WebSocket examples**:
   ```bash
   cd /workspaces/ag-ui/python-sdk/examples/websockets
   ```

2. **Generate SSL Certificates** (for secure connections):
   ```bash
   python generate_ssl_certs.py
   ```

3. **Run the Comprehensive WebSocket Demo** (recommended):
   ```bash
   # Secure mode (default) - demonstrates ALL events with JSON Patch state transitions
   python websocket_demo.py comprehensive_demo
   
   # Insecure mode (for testing)
   python websocket_demo.py comprehensive_demo --insecure
   ```

### WebSocket Demo Features

- **Complete Event Coverage**: Demonstrates ALL 20+ AG-UI event types
- **JSON Patch State Management**: RFC 6902 compliant state transitions
- **Secure Communication**: TLS encryption with SSL certificate support
- **Comprehensive Logging**: Detailed state validation and transition tracking
- **Production Ready**: Robust error handling and validation  
- `python websocket_demo.py client [--insecure]` - Run basic WebSocket client
- `python websocket_demo.py enhanced_client [--insecure]` - Run enhanced client handling ALL events

#### Demo Commands
- `python websocket_demo.py run_demo [--insecure]` - Run basic demo (server + client)
- `python websocket_demo.py comprehensive_demo [--insecure]` - **Run COMPREHENSIVE demo covering ALL events**

## Additional Examples

As the AG-UI Python SDK grows, additional example categories will be added to this directory:

- `websockets/` - WebSocket communication examples with comprehensive event coverage
- Future: HTTP/REST API examples
- Future: Streaming examples
- Future: Integration examples

## Development Notes

For detailed WebSocket examples including:
- **Complete Event Coverage**: All 20+ AG-UI event types
- **JSON Patch State Management**: RFC 6902 compliant state transitions  
- **Security Features**: SSL/TLS encryption and certificate handling
- **Production Examples**: Error handling, validation, and logging

Please see the `websockets/` directory and its dedicated README.

## Contributing

When adding new examples:
1. Create a dedicated subdirectory for each example category
2. Include a README.md with usage instructions
3. Provide both basic and comprehensive examples
4. Include proper error handling and logging
5. Add tests where appropriate

## Contributing

When adding new examples:
1. Create a dedicated subdirectory for each example category
2. Include a README.md with usage instructions
3. Provide both basic and comprehensive examples
4. Include proper error handling and logging
5. Add tests where appropriate

## Getting Started

1. **Install the AG-UI Python SDK**:
   ```bash
   pip install ag-ui
   ```

2. **Choose an example category**:
   ```bash
   cd examples/websockets  # For WebSocket examples
   ```

3. **Follow the specific README** in each subdirectory for detailed instructions

## Example Categories

### WebSockets (`websockets/`)

Comprehensive WebSocket communication examples including:
- Complete AG-UI event coverage (20+ event types)
- JSON Patch (RFC 6902) state management
- SSL/TLS security features
- Production-ready error handling

See `websockets/README.md` for detailed documentation.

## Development and Testing

Each example category includes:
- **Basic examples** for getting started
- **Comprehensive examples** for production use
- **Testing utilities** for validation
- **Security examples** with proper practices

## Support

For questions about specific examples:
1. Check the README in the relevant subdirectory
2. Review the example code comments
3. Run examples with verbose logging for debugging
