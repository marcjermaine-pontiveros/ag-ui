"""
This module contains event encoder classes for the AG-UI Python SDK.
"""
from ag_ui.core.events import BaseEvent

AGUI_MEDIA_TYPE = "application/vnd.ag-ui.event+proto"

class EventEncoder:
    """
    SSE (Server-Sent Events) encoder for Agent User Interaction events.
    
    This encoder is specifically designed for SSE/HTTP streaming use cases.
    For WebSocket connections, use WebSocketEventEncoder instead.
    """
    def __init__(self, accept: str = None):
        """
        Initialize EventEncoder for SSE.
        
        Args:
            accept: Accept header (for future use)
        """
        pass

    def get_content_type(self) -> str:
        """
        Returns the content type for SSE.
        
        Returns:
            str: Content type for Server-Sent Events
        """
        return "text/event-stream"

    def encode(self, event: BaseEvent) -> str:
        """
        Encodes an event for SSE transmission.
        
        Args:
            event: The event to encode
            
        Returns:
            str: Encoded event as SSE string
        """
        return self._encode_sse(event)

    def _encode_sse(self, event: BaseEvent) -> str:
        """
        Encodes an event into an SSE string.
        
        Args:
            event: The event to encode
            
        Returns:
            str: Event formatted for SSE with 'data:' prefix and double newlines
        """
        return f"data: {event.model_dump_json(by_alias=True, exclude_none=True)}\n\n"


class WebSocketEventEncoder:
    """
    WebSocket-specific encoder for Agent User Interaction events.
    
    This encoder is optimized for WebSocket connections and provides
    WebSocket-specific features like binary encoding and compression support.
    """
    
    def __init__(self, accept: str = None):
        """
        Initialize WebSocketEventEncoder.
        
        Args:
            accept: Accept header (for future use)
        """
        pass

    def get_content_type(self) -> str:
        """
        Returns the content type for WebSocket messages.
        
        Returns:
            str: Content type for WebSocket JSON messages
        """
        return "application/json"

    def encode(self, event: BaseEvent) -> str:
        """
        Encodes an event for WebSocket transmission.
        
        Args:
            event: The event to encode
            
        Returns:
            str: Encoded event as JSON string
        """
        return event.model_dump_json(by_alias=True, exclude_none=True)

    def encode_binary(self, event: BaseEvent) -> bytes:
        """
        Encodes an event as binary data for WebSocket transmission.
        Useful for performance optimization with large payloads.
        
        Args:
            event: The event to encode
            
        Returns:
            bytes: Encoded event as UTF-8 bytes
        """
        json_str = self.encode(event)
        return json_str.encode('utf-8')

    def can_compress(self) -> bool:
        """
        Indicates whether this encoder supports compression.
        WebSocket connections can benefit from per-message compression.
        
        Returns:
            bool: True if compression is supported
        """
        return True
