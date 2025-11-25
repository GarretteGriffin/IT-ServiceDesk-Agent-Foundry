"""
Logging utility with Azure Application Insights integration
"""

import logging
import sys
from pythonjsonlogger import jsonlogger
from src.config import settings


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance with proper configuration
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Set level
        logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        
        # Create handler
        handler = logging.StreamHandler(sys.stdout)
        
        # Set format based on configuration
        if settings.LOG_FORMAT.lower() == "json":
            formatter = jsonlogger.JsonFormatter(
                fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        else:
            formatter = logging.Formatter(
                fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger
