import unittest
import json
from datetime import datetime

from ag_ui.encoder.encoder import EventEncoder, AGUI_MEDIA_TYPE # Protocol will be imported in test methods where needed
from ag_ui.core.events import BaseEvent, EventType, TextMessageContentEvent, ToolCallStartEvent


class TestEventEncoder(unittest.TestCase):
    """Test suite for EventEncoder class"""

    def test_encoder_initialization(self):
        """Test initializing an EventEncoder"""
        encoder = EventEncoder()
        self.assertIsInstance(encoder, EventEncoder)

        # Test with accept parameter
        encoder_with_accept = EventEncoder(accept=AGUI_MEDIA_TYPE)
        self.assertIsInstance(encoder_with_accept, EventEncoder)

    def test_encode_method_sse_default(self): # Renamed for clarity
        """Test the encode method which calls encode_sse by default"""
        # Create a test event
        timestamp = int(datetime.now().timestamp() * 1000)
        event = BaseEvent(type=EventType.RAW, timestamp=timestamp)
        
        # Create encoder and encode event
        encoder = EventEncoder() # Default protocol is SSE
        encoded = encoder.encode(event)
        
        expected = f"data: {event.model_dump_json(by_alias=True, exclude_none=True)}\n\n"
        self.assertEqual(encoded, expected)
        
        self.assertIn('"type":', encoded)
        self.assertIn('"timestamp":', encoded)
        self.assertNotIn('"rawEvent":', encoded)
        self.assertNotIn('"raw_event":', encoded)

    def test_encode_sse_method_explicit(self): # Renamed for clarity
        """Test the _encode_sse method via encode() when SSE protocol is explicit"""
        from ag_ui.encoder.encoder import Protocol
        event = TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id="msg_123",
            delta="Hello, world!",
            timestamp=1648214400000
        )
        
        encoder = EventEncoder(protocol=Protocol.SSE) # Explicitly SSE
        encoded_sse = encoder.encode(event) # Uses public encode method
        
        self.assertTrue(encoded_sse.startswith("data: "))
        self.assertTrue(encoded_sse.endswith("\n\n"))
        
        json_content = encoded_sse[6:-2]
        decoded = json.loads(json_content)
        
        self.assertEqual(decoded["type"], "TEXT_MESSAGE_CONTENT")
        self.assertEqual(decoded["messageId"], "msg_123")
        self.assertEqual(decoded["delta"], "Hello, world!")
        self.assertEqual(decoded["timestamp"], 1648214400000)
        self.assertIn("messageId", decoded)
        self.assertNotIn("message_id", decoded)

    def test_encode_with_different_event_types_sse(self): # Suffix _sse
        """Test encoding different types of events using SSE protocol"""
        from ag_ui.encoder.encoder import Protocol
        encoder = EventEncoder(protocol=Protocol.SSE)
        
        base_event = BaseEvent(type=EventType.RAW, timestamp=1648214400000)
        encoded_base = encoder.encode(base_event)
        self.assertIn('"type":"RAW"', encoded_base)
        
        content_event = TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id="msg_456",
            delta="Testing different events",
            timestamp=1648214400000
        )
        encoded_content = encoder.encode(content_event)
        
        self.assertIn('"type":"TEXT_MESSAGE_CONTENT"', encoded_content)
        self.assertIn('"messageId":"msg_456"', encoded_content)
        self.assertIn('"delta":"Testing different events"', encoded_content)
        
        json_content = encoded_content.split("data: ")[1].rstrip("\n\n")
        decoded = json.loads(json_content)
        
        self.assertIn("messageId", decoded)
        self.assertNotIn("message_id", decoded)
        
    def test_null_value_exclusion_sse(self): # Suffix _sse
        """Test that fields with None values are excluded from JSON output for SSE"""
        from ag_ui.encoder.encoder import Protocol
        encoder = EventEncoder(protocol=Protocol.SSE)

        event = BaseEvent(
            type=EventType.RAW,
            timestamp=1648214400000,
            raw_event=None
        )
        encoded = encoder.encode(event)
        json_content = encoded.split("data: ")[1].rstrip("\n\n")
        decoded = json.loads(json_content)
        
        self.assertIn("type", decoded)
        self.assertIn("timestamp", decoded)
        self.assertNotIn("rawEvent", decoded)
        
        event_with_optional = ToolCallStartEvent(
            type=EventType.TOOL_CALL_START,
            tool_call_id="call_123",
            tool_call_name="test_tool",
            parent_message_id=None,
            timestamp=1648214400000
        )
        encoded_optional = encoder.encode(event_with_optional)
        json_content_optional = encoded_optional.split("data: ")[1].rstrip("\n\n")
        decoded_optional = json.loads(json_content_optional)
        
        self.assertIn("toolCallId", decoded_optional)
        self.assertIn("toolCallName", decoded_optional)
        self.assertNotIn("parentMessageId", decoded_optional)
        
    def test_round_trip_serialization(self):
        """Test that events can be serialized to JSON with camelCase and deserialized back correctly"""
        original_event = ToolCallStartEvent(
            type=EventType.TOOL_CALL_START,
            tool_call_id="call_abc123",
            tool_call_name="search_tool",
            parent_message_id="msg_parent_456",
            timestamp=1648214400000
        )
        
        json_str = original_event.model_dump_json(by_alias=True, exclude_none=True) # Added exclude_none
        
        json_data = json.loads(json_str)
        self.assertIn("toolCallId", json_data)
        self.assertIn("toolCallName", json_data)
        self.assertIn("parentMessageId", json_data)
        self.assertNotIn("tool_call_id", json_data)
        self.assertNotIn("tool_call_name", json_data)
        self.assertNotIn("parent_message_id", json_data)
        
        deserialized_event = ToolCallStartEvent.model_validate_json(json_str)
        
        self.assertEqual(deserialized_event.type, original_event.type)
        self.assertEqual(deserialized_event.tool_call_id, original_event.tool_call_id)
        self.assertEqual(deserialized_event.tool_call_name, original_event.tool_call_name)
        self.assertEqual(deserialized_event.parent_message_id, original_event.parent_message_id)
        self.assertEqual(deserialized_event.timestamp, original_event.timestamp)
        
        self.assertEqual(
            original_event.model_dump(exclude_none=True), # Added exclude_none
            deserialized_event.model_dump(exclude_none=True) # Added exclude_none
        )

    # --- Tests for WebSocket Encoding ---

    def test_websocket_encoder_initialization(self):
        """Test initializing an EventEncoder for WebSocket"""
        from ag_ui.encoder.encoder import Protocol
        encoder = EventEncoder(protocol=Protocol.WEBSOCKET)
        self.assertIsInstance(encoder, EventEncoder)
        self.assertEqual(encoder.protocol, Protocol.WEBSOCKET)

    def test_websocket_get_content_type(self):
        """Test get_content_type for WebSocket protocol"""
        from ag_ui.encoder.encoder import Protocol
        encoder = EventEncoder(protocol=Protocol.WEBSOCKET)
        self.assertEqual(encoder.get_content_type(), "application/json")

    def test_encode_websocket_method(self):
        """Test the encode() method for WebSocket protocol"""
        from ag_ui.encoder.encoder import Protocol

        event = TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id="ws_msg_789",
            delta="WebSocket test message!",
            timestamp=1648214500000
        )

        encoder = EventEncoder(protocol=Protocol.WEBSOCKET)
        encoded_json = encoder.encode(event) # Use public encode method

        decoded = json.loads(encoded_json)

        self.assertEqual(decoded["type"], "TEXT_MESSAGE_CONTENT")
        self.assertEqual(decoded["messageId"], "ws_msg_789")
        self.assertEqual(decoded["delta"], "WebSocket test message!")
        self.assertEqual(decoded["timestamp"], 1648214500000)
        self.assertNotIn("message_id", decoded)

    def test_websocket_encode_with_optional_fields_null(self):
        """Test WebSocket encoding with optional fields set to None"""
        from ag_ui.encoder.encoder import Protocol
        encoder = EventEncoder(protocol=Protocol.WEBSOCKET)

        event_with_optional_none = ToolCallStartEvent(
            type=EventType.TOOL_CALL_START,
            tool_call_id="ws_call_456",
            tool_call_name="ws_test_tool",
            parent_message_id=None,
            timestamp=1648214600000
        )

        encoded_json = encoder.encode(event_with_optional_none)
        decoded = json.loads(encoded_json)

        self.assertIn("toolCallId", decoded)
        self.assertIn("toolCallName", decoded)
        self.assertNotIn("parentMessageId", decoded)

    def test_default_protocol_is_sse(self):
        """Test that the default protocol for EventEncoder is SSE"""
        from ag_ui.encoder.encoder import Protocol
        encoder = EventEncoder()
        self.assertEqual(encoder.protocol, Protocol.SSE)
        self.assertEqual(encoder.get_content_type(), "text/event-stream")

        event = BaseEvent(type=EventType.RAW)
        encoded = encoder.encode(event)
        self.assertTrue(encoded.startswith("data: "))
        self.assertTrue(encoded.endswith("\n\n"))

if __name__ == '__main__':
    unittest.main()
