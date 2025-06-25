"""
This module contains the EventEncoder class
"""
from enum import Enum
from ag_ui.core.events import BaseEvent

AGUI_MEDIA_TYPE = "application/vnd.ag-ui.event+proto"

class Protocol(Enum):
    SSE = "sse"
    WEBSOCKET = "websocket"

class EventEncoder:
    """
    Encodes Agent User Interaction events.
    """
    def __init__(self, protocol: Protocol = Protocol.SSE, accept: str = None):
        self.protocol = protocol
        # The accept parameter is not used in this version but kept for compatibility
        # self.accept = accept

    def get_content_type(self) -> str:
        """
        Returns the content type of the encoder based on the protocol.
        """
        if self.protocol == Protocol.SSE:
            return "text/event-stream"
        elif self.protocol == Protocol.WEBSOCKET:
            return "application/json"  # Assuming JSON text messages for WebSockets
        else:
            # Default or raise an error for unsupported protocols
            return "application/octet-stream"

    def encode(self, event: BaseEvent) -> str:
        """
        Encodes an event based on the configured protocol.
        """
        if self.protocol == Protocol.SSE:
            return self._encode_sse(event)
        elif self.protocol == Protocol.WEBSOCKET:
            return self._encode_websocket(event)
        else:
            # Fallback or error for unsupported protocols
            # For now, defaulting to JSON representation
            return event.model_dump_json(by_alias=True, exclude_none=True)

    def _encode_sse(self, event: BaseEvent) -> str:
        """
        Encodes an event into an SSE string.
        """
        return f"data: {event.model_dump_json(by_alias=True, exclude_none=True)}\n\n"

    def _encode_websocket(self, event: BaseEvent) -> str:
        """
        Encodes an event into a JSON string for WebSocket.
        """
        return event.model_dump_json(by_alias=True, exclude_none=True)
