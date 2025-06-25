import unittest
import json
from datetime import datetime

from ag_ui.encoder import EventEncoder, WebSocketEventEncoder, AGUI_MEDIA_TYPE
from ag_ui.core.events import BaseEvent, EventType, TextMessageContentEvent, ToolCallStartEvent


class TestEventEncoder(unittest.TestCase):
    """Test suite for EventEncoder class (SSE-only)"""

    def test_encoder_initialization(self):
        """Test initializing an EventEncoder"""
        encoder = EventEncoder()
        self.assertIsInstance(encoder, EventEncoder)
        
        # Test with accept parameter
        encoder_with_accept = EventEncoder(accept="text/event-stream")
        self.assertIsInstance(encoder_with_accept, EventEncoder)

    def test_get_content_type_sse(self):
        """Test get_content_type returns SSE content type"""
        encoder = EventEncoder()
        content_type = encoder.get_content_type()
        self.assertEqual(content_type, "text/event-stream")

    def test_encode_method_sse(self):
        """Test the encode method for SSE"""
        # Create a test event
        timestamp = int(datetime.now().timestamp() * 1000)
        event = BaseEvent(type=EventType.RAW, timestamp=timestamp)
        
        # Create encoder and encode event
        encoder = EventEncoder()
        encoded = encoder.encode(event)
        
        expected = f"data: {event.model_dump_json(by_alias=True, exclude_none=True)}\n\n"
        self.assertEqual(encoded, expected)
        
        self.assertIn('"type":', encoded)
        self.assertIn('"timestamp":', encoded)
        self.assertNotIn('"rawEvent":', encoded)
        self.assertNotIn('"raw_event":', encoded)

    def test_encode_sse_method_direct(self):
        """Test the _encode_sse method directly"""
        event = TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id="msg_123",
            delta="Hello, world!",
            timestamp=1648214400000
        )
        
        encoder = EventEncoder()
        encoded = encoder._encode_sse(event)
        
        # Check that it's properly formatted for SSE
        self.assertTrue(encoded.startswith("data: "))
        self.assertTrue(encoded.endswith("\n\n"))
        
        # Parse the JSON part
        json_part = encoded[6:-2]  # Remove "data: " and "\n\n"
        parsed = json.loads(json_part)
        
        self.assertEqual(parsed["type"], "TEXT_MESSAGE_CONTENT")
        self.assertEqual(parsed["messageId"], "msg_123")
        self.assertEqual(parsed["delta"], "Hello, world!")
        self.assertEqual(parsed["timestamp"], 1648214400000)

    def test_encode_with_different_event_types_sse(self):
        """Test encoding different types of events using SSE"""
        encoder = EventEncoder()
        
        # Test with TextMessageContentEvent
        text_event = TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id="msg_456",
            delta="Test message",
            timestamp=1648214400000
        )
        encoded_text = encoder.encode(text_event)
        self.assertIn('"type":"TEXT_MESSAGE_CONTENT"', encoded_text)
        
        # Test with ToolCallStartEvent
        tool_event = ToolCallStartEvent(
            type=EventType.TOOL_CALL_START,
            tool_call_id="tool_789",
            tool_call_name="get_weather",
            timestamp=1648214400000
        )
        encoded_tool = encoder.encode(tool_event)
        self.assertIn('"type":"TOOL_CALL_START"', encoded_tool)

    def test_null_value_exclusion_sse(self):
        """Test that fields with None values are excluded from JSON output for SSE"""
        encoder = EventEncoder()
        
        # Create event with optional fields
        event = BaseEvent(
            type=EventType.RAW,
            timestamp=1648214400000
        )
        
        encoded = encoder.encode(event)
        json_part = encoded[6:-2]  # Remove "data: " and "\n\n"
        parsed = json.loads(json_part)
        
        # Check that only non-None fields are present
        self.assertIn("type", parsed)
        self.assertIn("timestamp", parsed)

    def test_round_trip_serialization(self):
        """Test that events can be serialized to JSON with camelCase and deserialized back correctly"""
        encoder = EventEncoder()
        
        original_event = TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id="test_123",
            delta="Test content",
            timestamp=1648214400000
        )
        
        # Encode to SSE format
        encoded = encoder.encode(original_event)
        
        # Extract JSON from SSE format
        json_part = encoded[6:-2]  # Remove "data: " and "\n\n"
        
        # Parse JSON and verify camelCase
        parsed = json.loads(json_part)
        self.assertEqual(parsed["messageId"], "test_123")  # camelCase
        self.assertNotIn("message_id", parsed)  # No snake_case
        
        # Verify round-trip
        recreated_event = TextMessageContentEvent.model_validate(parsed)
        self.assertEqual(recreated_event.message_id, original_event.message_id)
        self.assertEqual(recreated_event.delta, original_event.delta)


class TestWebSocketEventEncoder(unittest.TestCase):
    """Test suite for WebSocketEventEncoder class"""

    def test_websocket_encoder_initialization(self):
        """Test initializing a WebSocketEventEncoder"""
        encoder = WebSocketEventEncoder()
        self.assertIsInstance(encoder, WebSocketEventEncoder)
        
        # Test with accept parameter
        encoder_with_accept = WebSocketEventEncoder(accept="application/json")
        self.assertIsInstance(encoder_with_accept, WebSocketEventEncoder)

    def test_websocket_get_content_type(self):
        """Test get_content_type for WebSocket encoder"""
        encoder = WebSocketEventEncoder()
        content_type = encoder.get_content_type()
        self.assertEqual(content_type, "application/json")

    def test_websocket_encode_method(self):
        """Test the encode() method for WebSocket encoder"""
        encoder = WebSocketEventEncoder()
        
        event = TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id="ws_msg_123",
            delta="WebSocket message",
            timestamp=1648214400000
        )
        
        encoded = encoder.encode(event)
        
        # Should be pure JSON without SSE formatting
        self.assertFalse(encoded.startswith("data: "))
        self.assertFalse(encoded.endswith("\n\n"))
        
        # Should be valid JSON
        parsed = json.loads(encoded)
        self.assertEqual(parsed["type"], "TEXT_MESSAGE_CONTENT")
        self.assertEqual(parsed["messageId"], "ws_msg_123")
        self.assertEqual(parsed["delta"], "WebSocket message")

    def test_websocket_encode_binary(self):
        """Test binary encoding for WebSocket"""
        encoder = WebSocketEventEncoder()
        
        event = BaseEvent(
            type=EventType.RAW,
            timestamp=1648214400000
        )
        
        binary_encoded = encoder.encode_binary(event)
        self.assertIsInstance(binary_encoded, bytes)
        
        # Should be the same as JSON encoding but as bytes
        json_encoded = encoder.encode(event)
        self.assertEqual(binary_encoded, json_encoded.encode('utf-8'))

    def test_websocket_can_compress(self):
        """Test compression capability indication"""
        encoder = WebSocketEventEncoder()
        self.assertTrue(encoder.can_compress())

    def test_websocket_encode_with_optional_fields_null(self):
        """Test WebSocket encoding with optional fields set to None"""
        encoder = WebSocketEventEncoder()
        
        event = BaseEvent(
            type=EventType.RAW,
            timestamp=1648214400000
        )
        
        encoded = encoder.encode(event)
        parsed = json.loads(encoded)
        
        # Check that only non-None fields are present
        self.assertIn("type", parsed)
        self.assertIn("timestamp", parsed)


class TestEventEncoderComparison(unittest.TestCase):
    """Test comparison between SSE and WebSocket encoders"""

    def test_both_encoders_produce_same_json_content(self):
        """Test that both encoders produce the same JSON content (just different formats)"""
        sse_encoder = EventEncoder()
        ws_encoder = WebSocketEventEncoder()
        
        event = TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id="test_123",
            delta="Test content",
            timestamp=1648214400000
        )
        
        # Encode with both
        sse_encoded = sse_encoder.encode(event)
        ws_encoded = ws_encoder.encode(event)
        
        # Extract JSON from SSE format
        sse_json = sse_encoded[6:-2]  # Remove "data: " and "\n\n"
        
        # Should be the same JSON content
        self.assertEqual(sse_json, ws_encoded)

    def test_content_types_are_different(self):
        """Test that the two encoders return different content types"""
        sse_encoder = EventEncoder()
        ws_encoder = WebSocketEventEncoder()
        
        self.assertEqual(sse_encoder.get_content_type(), "text/event-stream")
        self.assertEqual(ws_encoder.get_content_type(), "application/json")
        self.assertNotEqual(sse_encoder.get_content_type(), ws_encoder.get_content_type())


if __name__ == '__main__':
    unittest.main()
