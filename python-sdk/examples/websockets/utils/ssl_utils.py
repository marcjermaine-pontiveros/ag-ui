"""
SSL and security utilities for WebSocket demo.
"""
import ssl
import os
import logging
from pathlib import Path

logger = logging.getLogger("ag_ui_demo")

# Configuration
HOST = "localhost"
PORT = 8765
SECURE_PORT = 8766
SSL_CERT_PATH = "cert.pem"
SSL_KEY_PATH = "key.pem"

def create_ssl_context():
    """
    Create an SSL context for secure WebSocket connections.
    
    Returns:
        ssl.SSLContext or None: SSL context if certificates are available, None otherwise
    """
    if not (Path(SSL_CERT_PATH).exists() and Path(SSL_KEY_PATH).exists()):
        logger.warning(f"SSL certificates not found at {SSL_CERT_PATH} and {SSL_KEY_PATH}")
        logger.info("Run 'python generate_ssl_certs.py' to create self-signed certificates for testing")
        return None
    
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(SSL_CERT_PATH, SSL_KEY_PATH)
        logger.info("✓ SSL context created successfully")
        return context
    except Exception as e:
        logger.error(f"Failed to create SSL context: {e}")
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

def should_use_secure_connection():
    """
    Determine if secure connection should be used based on SSL certificate availability.
    
    Returns:
        bool: True if SSL certificates are available, False otherwise
    """
    return (Path(SSL_CERT_PATH).exists() and Path(SSL_KEY_PATH).exists())
