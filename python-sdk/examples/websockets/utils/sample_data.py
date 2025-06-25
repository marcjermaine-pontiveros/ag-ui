"""
Sample data creation utilities for WebSocket demo.
"""
import uuid
from ag_ui.core.types import (
    Message, AssistantMessage, UserMessage, SystemMessage, 
    DeveloperMessage, ToolMessage, FunctionCall, ToolCall
)

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
            content="What's the weather like in San Francisco today?"
        ),
        AssistantMessage(
            id=str(uuid.uuid4()),
            role="assistant",
            content="I'll help you check the weather in San Francisco. Let me use the weather tool to get that information.",
            tool_calls=[
                ToolCall(
                    id=str(uuid.uuid4()),
                    type="function",
                    function=FunctionCall(
                        name="get_weather",
                        arguments='{"location": "San Francisco, CA", "unit": "fahrenheit"}'
                    )
                )
            ]
        ),
        ToolMessage(
            id=str(uuid.uuid4()),
            role="tool",
            content='{"temperature": 68, "condition": "partly cloudy", "humidity": 65}',
            tool_call_id=str(uuid.uuid4())
        ),
        AssistantMessage(
            id=str(uuid.uuid4()),
            role="assistant",
            content="Based on the weather data, it's currently 68°F in San Francisco with partly cloudy skies and 65% humidity. It's a pleasant day!"
        ),
        DeveloperMessage(
            id=str(uuid.uuid4()),
            role="developer",
            content="Debug: Weather API call completed successfully"
        )
    ]

def create_sample_tools():
    """Create sample tools for demonstration."""
    return [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather information for a specific location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state/country, e.g. 'San Francisco, CA'"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "description": "Temperature unit"
                        }
                    },
                    "required": ["location"]
                }
            }
        },
        {
            "type": "function", 
            "function": {
                "name": "search_web",
                "description": "Search the web for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]

def create_sample_context():
    """Create sample context for demonstration."""
    return {
        "user_preferences": {
            "language": "en",
            "temperature_unit": "fahrenheit",
            "timezone": "America/Los_Angeles"
        },
        "session_info": {
            "session_id": str(uuid.uuid4()),
            "user_id": "user_123",
            "start_time": "2024-01-01T12:00:00Z"
        }
    }

def create_sample_state():
    """Create sample state for demonstration."""
    return {
        "conversation": {
            "total_messages": 6,
            "user_messages": 1,
            "assistant_messages": 2,
            "system_messages": 1,
            "tool_messages": 1,
            "developer_messages": 1
        },
        "tools": {
            "available_tools": ["get_weather", "search_web"],
            "last_tool_used": "get_weather",
            "tool_call_count": 1
        },
        "user_profile": {
            "name": "John Doe", 
            "preferences": {
                "response_style": "detailed",
                "include_reasoning": True
            }
        },
        "session": {
            "duration_seconds": 45,
            "interaction_count": 3,
            "last_activity": "2024-01-01T12:00:45Z"
        },
        "temporary_data": {
            "weather_cache": {
                "san_francisco": {
                    "temperature": 68,
                    "condition": "partly cloudy",
                    "cached_at": "2024-01-01T12:00:30Z"
                }
            },
            "pending_operations": ["update_user_preferences"]
        }
    }
