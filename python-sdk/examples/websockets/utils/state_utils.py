"""
State management utilities for WebSocket demo.
"""
import copy
import logging

logger = logging.getLogger("ag_ui_demo")

def create_progressive_state_changes():
    """
    Create a series of progressive state changes using JSON Patch operations.
    
    Returns:
        list: List of JSON Patch operation sets for demonstrating state evolution
    """
    return [
        # Step 1: Initial conversation state update
        [
            {"op": "replace", "path": "/conversation/total_messages", "value": 7},
            {"op": "replace", "path": "/conversation/assistant_messages", "value": 3}
        ],
        
        # Step 2: Add tool usage tracking
        [
            {"op": "add", "path": "/tools/recent_calls", "value": [
                {"tool": "get_weather", "timestamp": "2024-01-01T12:00:30Z", "success": True}
            ]},
            {"op": "replace", "path": "/tools/tool_call_count", "value": 2}
        ],
        
        # Step 3: Update user interaction metrics
        [
            {"op": "replace", "path": "/session/interaction_count", "value": 4},
            {"op": "replace", "path": "/session/duration_seconds", "value": 67},
            {"op": "replace", "path": "/session/last_activity", "value": "2024-01-01T12:01:07Z"}
        ],
        
        # Step 4: Add new temporary data
        [
            {"op": "add", "path": "/temporary_data/search_cache", "value": {
                "query_history": ["San Francisco weather", "weather forecast"],
                "last_search": "2024-01-01T12:01:00Z"
            }}
        ],
        
        # Step 5: Update user preferences based on interaction
        [
            {"op": "replace", "path": "/user_profile/preferences/response_style", "value": "concise"},
            {"op": "add", "path": "/user_profile/preferences/preferred_topics", "value": ["weather", "technology"]}
        ],
        
        # Step 6: Add processing status
        [
            {"op": "add", "path": "/processing", "value": {
                "current_step": "weather_analysis",
                "progress": 0.75,
                "estimated_completion": "2024-01-01T12:01:15Z"
            }}
        ],
        
        # Step 7: Clean up temporary data (final state)
        [
            {"op": "remove", "path": "/temporary_data/pending_operations"},
            {"op": "replace", "path": "/processing/current_step", "value": "completed"},
            {"op": "replace", "path": "/processing/progress", "value": 1.0}
        ]
    ]

def apply_json_patch(state, patch_operations):
    """
    Apply JSON Patch operations to a state object.
    
    Args:
        state: The state object to modify
        patch_operations: List of JSON Patch operations
        
    Returns:
        dict: The modified state
    """
    # Create a deep copy to avoid modifying the original
    modified_state = copy.deepcopy(state)
    
    for operation in patch_operations:
        op = operation["op"]
        path = operation["path"]
        
        # Parse path into components
        path_components = [p for p in path.split("/") if p]
        
        if op == "replace":
            _set_nested_value(modified_state, path_components, operation["value"])
        elif op == "add":
            _set_nested_value(modified_state, path_components, operation["value"])
        elif op == "remove":
            _remove_nested_value(modified_state, path_components)
        else:
            logger.warning(f"Unsupported JSON Patch operation: {op}")
    
    return modified_state

def _set_nested_value(obj, path_components, value):
    """Set a value at a nested path in an object."""
    current = obj
    
    # Navigate to the parent of the target
    for component in path_components[:-1]:
        if component not in current:
            current[component] = {}
        current = current[component]
    
    # Set the final value
    if path_components:
        current[path_components[-1]] = value

def _remove_nested_value(obj, path_components):
    """Remove a value at a nested path in an object."""
    current = obj
    
    # Navigate to the parent of the target
    for component in path_components[:-1]:
        if component not in current:
            return  # Path doesn't exist
        current = current[component]
    
    # Remove the final key
    if path_components and path_components[-1] in current:
        del current[path_components[-1]]

def _get_nested_value(obj, path_components):
    """Get a value at a nested path in an object."""
    current = obj
    
    for component in path_components:
        if isinstance(current, dict) and component in current:
            current = current[component]
        else:
            return None
    
    return current
