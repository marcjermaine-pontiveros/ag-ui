"""
Utility functions for WebSocket demo.
"""

def current_timestamp_ms():
    """Helper function to get current timestamp in milliseconds."""
    from datetime import datetime
    return int(datetime.now().timestamp() * 1000)

def log_state_summary(state, context=""):
    """Log a summary of the current state."""
    import logging
    logger = logging.getLogger("ag_ui_demo")
    
    if not state:
        logger.info(f"{context}State is empty")
        return
    
    logger.info(f"{context}State summary:")
    for key, value in state.items():
        if isinstance(value, dict):
            logger.info(f"  {key}: {len(value)} items")
        elif isinstance(value, list):
            logger.info(f"  {key}: {len(value)} items")
        else:
            logger.info(f"  {key}: {type(value).__name__}")
