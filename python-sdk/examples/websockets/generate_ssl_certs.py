#!/usr/bin/env python3
"""
Generate self-signed SSL certificates for testing WebSocket secure connections.

This script creates a self-signed certificate and private key for local development
and testing of secure WebSocket connections.

WARNING: Self-signed certificates should NEVER be used in production environments.
"""

import subprocess
import sys
import os
import shlex
from pathlib import Path

def generate_ssl_certificates():
    """Generate self-signed SSL certificates for local testing."""
    
    cert_file = "cert.pem"
    key_file = "key.pem"
    
    # Check if certificates already exist
    if Path(cert_file).exists() and Path(key_file).exists():
        print(f"SSL certificates already exist: {cert_file}, {key_file}")
        return True
    
    # Generate self-signed certificate
    # Using hardcoded, safe values to prevent command injection
    cmd = [
        "openssl", "req", "-x509", "-newkey", "rsa:4096",
        "-keyout", key_file, "-out", cert_file,
        "-days", "365", "-nodes",
        "-subj", "/C=US/ST=Test/L=Test/O=Test/OU=Test/CN=localhost"
    ]
    
    try:
        print("Generating self-signed SSL certificates...")
        print(f"Command: {' '.join(shlex.quote(arg) for arg in cmd)}")
        
        # Use shell=False and pass list directly for security
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=False)
        
        print(f"✓ SSL certificates generated successfully:")
        print(f"  Certificate: {cert_file}")
        print(f"  Private key: {key_file}")
        print(f"\nThese certificates are for LOCAL TESTING ONLY!")
        print(f"Do NOT use self-signed certificates in production.")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Error generating SSL certificates: {e}")
        print(f"stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print("✗ OpenSSL not found. Please install OpenSSL:")
        print("  On Ubuntu/Debian: sudo apt-get install openssl")
        print("  On macOS: brew install openssl")
        print("  On Windows: Download from https://slproweb.com/products/Win32OpenSSL.html")
        return False

def main():
    """Main function."""
    print("SSL Certificate Generator for AG-UI WebSocket Demo")
    print("=" * 50)
    
    if generate_ssl_certificates():
        print("\nYou can now run the secure WebSocket demo:")
        print("  python websocket_demo.py run_demo")
        print("\nOr run the insecure version for testing:")
        print("  python websocket_demo.py run_demo --insecure")
    else:
        print("\nFailed to generate SSL certificates.")
        print("You can still run the demo in insecure mode:")
        print("  python websocket_demo.py run_demo --insecure")
        sys.exit(1)

if __name__ == "__main__":
    main()
