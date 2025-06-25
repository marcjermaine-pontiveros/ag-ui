#!/usr/bin/env python3
"""
AG-UI Python SDK WebSocket Demo

A comprehensive demonstration of the AG-UI protocol over WebSocket connections,
showcasing all event types and real-time communication patterns.

This demo has been refactored for better maintainability with modular utilities.
"""

import asyncio
import sys
import logging
import websockets
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ag_ui_demo")

# Import utilities
try:
    from utils.ssl_utils import create_ssl_context, get_websocket_uri, HOST, PORT, SECURE_PORT, should_use_secure_connection
    from utils.server_handlers import comprehensive_ag_ui_server_handler, ag_ui_server_handler
    from utils.client_handlers import ag_ui_client, enhanced_ag_ui_client
    from ag_ui.encoder import WebSocketEventEncoder
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Make sure you're running from the correct directory and ag_ui is installed")
    sys.exit(1)

async def start_server_once(secure=True):
    """Start the basic WebSocket server."""
    if secure:
        ssl_context = create_ssl_context()
        if ssl_context is None:
            logger.error("Cannot start secure server without SSL certificates")
            logger.info("Run 'python generate_ssl_certs.py' to create certificates, or use --insecure flag")
            return
        
        logger.info(f"Starting secure WebSocket server on wss://{HOST}:{SECURE_PORT}")
        async with websockets.serve(ag_ui_server_handler, HOST, SECURE_PORT, ssl=ssl_context):
            logger.info("✓ Secure server started successfully")
            await asyncio.Future()  # Run forever
    else:
        logger.warning("Running in insecure mode (for local development only)")
        logger.info(f"Starting WebSocket server on ws://{HOST}:{PORT}")
        async with websockets.serve(ag_ui_server_handler, HOST, PORT):
            logger.info("✓ Insecure server started successfully")
            await asyncio.Future()  # Run forever

async def start_comprehensive_server_once(secure=True):
    """Start the comprehensive WebSocket server demonstrating ALL event types."""
    if secure:
        ssl_context = create_ssl_context()
        if ssl_context is None:
            logger.error("Cannot start secure server without SSL certificates")
            logger.info("Run 'python generate_ssl_certs.py' to create certificates, or use --insecure flag")
            return
        
        logger.info(f"Starting comprehensive secure WebSocket server on wss://{HOST}:{SECURE_PORT}")
        async with websockets.serve(comprehensive_ag_ui_server_handler, HOST, SECURE_PORT, ssl=ssl_context):
            logger.info("✓ Comprehensive secure server started successfully")
            logger.info("🚀 Ready to demonstrate ALL 21 event types")
            await asyncio.Future()  # Run forever
    else:
        logger.warning("Running in insecure mode (for local development only)")
        logger.info(f"Starting comprehensive WebSocket server on ws://{HOST}:{PORT}")
        async with websockets.serve(comprehensive_ag_ui_server_handler, HOST, PORT):
            logger.info("✓ Comprehensive insecure server started successfully")
            logger.info("🚀 Ready to demonstrate ALL 21 event types")
            await asyncio.Future()  # Run forever

async def run_basic_demo(secure=True):
    """Run a complete basic demo (server + client)."""
    logger.info("🎬 Starting basic WebSocket demo...")
    
    # Start server in background
    if secure:
        ssl_context = create_ssl_context()
        if ssl_context is None:
            logger.error("Cannot run secure demo without SSL certificates")
            logger.info("Run 'python generate_ssl_certs.py' to create certificates, or use --insecure flag")
            return
        
        server = await websockets.serve(ag_ui_server_handler, HOST, SECURE_PORT, ssl=ssl_context)
        logger.info(f"✓ Basic demo server started on wss://{HOST}:{SECURE_PORT}")
    else:
        logger.warning("Running demo in insecure mode (for local development only)")
        server = await websockets.serve(ag_ui_server_handler, HOST, PORT)
        logger.info(f"✓ Basic demo server started on ws://{HOST}:{PORT}")
    
    # Wait a moment for server to be ready
    await asyncio.sleep(0.5)
    
    # Run client
    logger.info("🔌 Starting basic demo client...")
    await ag_ui_client(secure)
    
    # Close server
    server.close()
    await server.wait_closed()
    logger.info("🎬 Basic demo completed!")

async def run_comprehensive_demo(secure=True):
    """Run a complete comprehensive demo (server + client) covering ALL events."""
    logger.info("🎬 Starting COMPREHENSIVE WebSocket demo...")
    logger.info("🚀 This demo will showcase ALL 21 event types!")
    
    # Start comprehensive server in background
    if secure:
        ssl_context = create_ssl_context()
        if ssl_context is None:
            logger.error("Cannot run secure demo without SSL certificates")
            logger.info("Run 'python generate_ssl_certs.py' to create certificates, or use --insecure flag")
            return
        
        server = await websockets.serve(comprehensive_ag_ui_server_handler, HOST, SECURE_PORT, ssl=ssl_context)
        logger.info(f"✓ Comprehensive demo server started on wss://{HOST}:{SECURE_PORT}")
    else:
        logger.warning("Running demo in insecure mode (for local development only)")
        server = await websockets.serve(comprehensive_ag_ui_server_handler, HOST, PORT)
        logger.info(f"✓ Comprehensive demo server started on ws://{HOST}:{PORT}")
    
    # Wait a moment for server to be ready
    await asyncio.sleep(0.5)
    
    # Run enhanced client
    logger.info("🔍 Starting comprehensive demo client...")
    await enhanced_ag_ui_client(secure)
    
    # Close server
    server.close()
    await server.wait_closed()
    logger.info("🎬 COMPREHENSIVE demo completed!")

def print_usage(script_name=None):
    """Print usage information."""
    if script_name is None:
        script_name = Path(__file__).name
        
    if "--help" in sys.argv:
        print(f"AG-UI Python SDK WebSocket Demo")
        print(f"")
        print(f"A comprehensive demonstration of the AG-UI protocol over WebSocket connections.")
        print(f"")
        print(f"Usage: python {script_name} [COMMAND] [OPTIONS]")
        print(f"")
        print(f"Commands:")
        print(f"  server              - Run basic WebSocket server")
        print(f"  comprehensive_server - Run server demonstrating ALL event types")
        print(f"  client              - Run basic WebSocket client")
        print(f"  enhanced_client     - Run enhanced client that handles all event types")
        print(f"  run_demo            - Run basic demo (server + client)")
        print(f"  comprehensive_demo  - Run COMPREHENSIVE demo covering ALL events")
        print(f"")
        print(f"Options:")
        print(f"  --insecure          - Use insecure WebSocket (ws://) for LOCAL DEVELOPMENT ONLY")
        print(f"                        ⚠️  WARNING: Do NOT use --insecure in production!")
        print(f"                        By default, uses secure WebSocket (wss://) if SSL certificates are available")
        print(f"")
        print(f"Examples:")
        print(f"  python {script_name} comprehensive_demo")
        print(f"  python {script_name} comprehensive_demo --insecure")
        print(f"  python {script_name} server")
        print(f"  python {script_name} client --insecure")
        print(f"")
        print(f"To generate SSL certificates for testing:")
        print(f"  python generate_ssl_certs.py")
    else:
        print(f"Usage: python {script_name} [server|comprehensive_server|client|enhanced_client|run_demo|comprehensive_demo] [--insecure]")
        print(f"")
        print(f"Commands:")
        print(f"  server              - Run basic WebSocket server")
        print(f"  comprehensive_server - Run server demonstrating ALL event types")
        print(f"  client              - Run basic WebSocket client")
        print(f"  enhanced_client     - Run enhanced client that handles all event types")
        print(f"  run_demo            - Run basic demo (server + client)")
        print(f"  comprehensive_demo  - Run COMPREHENSIVE demo covering ALL events")
        print(f"")
        print(f"Options:")
        print(f"  --insecure          - Use insecure WebSocket (ws://) for LOCAL DEVELOPMENT ONLY")
        print(f"                        ⚠️  WARNING: Do NOT use --insecure in production!")
        print(f"                        By default, uses secure WebSocket (wss://) if SSL certificates are available")
        print(f"")
        print(f"To generate SSL certificates for testing:")
        print(f"  python generate_ssl_certs.py")
        print(f"  # OR manually:")
        print(f"  openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes")

async def main():
    """Main entry point for the WebSocket demo."""
    if len(sys.argv) < 2:
        print_usage()
        return

    command = sys.argv[1]
    insecure = "--insecure" in sys.argv
    
    # Determine security mode
    if insecure:
        secure = False
        logger.warning("⚠️  Using insecure WebSocket connection for local development!")
    else:
        secure = should_use_secure_connection()
        if not secure:
            logger.info("SSL certificates not found, falling back to insecure connection")
            logger.info("For secure connections, run: python generate_ssl_certs.py")

    try:
        if command == "server":
            logger.info("Starting basic WebSocket server indefinitely. Press Ctrl+C to stop.")
            await start_server_once(secure)
            
        elif command == "comprehensive_server":
            logger.info("Starting comprehensive WebSocket server indefinitely. Press Ctrl+C to stop.")
            await start_comprehensive_server_once(secure)
            
        elif command == "client":
            await ag_ui_client(secure)
            
        elif command == "enhanced_client":
            await enhanced_ag_ui_client(secure)
            
        elif command == "run_demo":
            await run_basic_demo(secure)
            
        elif command == "comprehensive_demo":
            await run_comprehensive_demo(secure)
            
        elif command in ["--help", "-h", "help"]:
            print_usage()
            
        else:
            logger.error(f"Unknown command: {command}")
            print_usage()
            
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
