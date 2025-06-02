import logging
import sys

from src.constants import LOG_LEVEL

def setup_logging():
    """
    Configure and initialize the application's logging system.
    
    Creates a logger with:
    - Console output handler
    - Timestamp and context information in log messages
    - Log level configured via environment variables
    
    Returns:
        logging.Logger: Configured logger instance for the application
    """
    # Create logger
    logger = logging.getLogger('EddnRelay')

    # Set log level based on environment variable
    match LOG_LEVEL:
        case 'DEBUG':
            logger.setLevel(logging.DEBUG)
        case 'INFO':
            logger.setLevel(logging.INFO)
        case 'WARNING':
            logger.setLevel(logging.WARNING)
        case 'ERROR':
            logger.setLevel(logging.ERROR)
        case 'CRITICAL':
            logger.setLevel(logging.CRITICAL)
        case _:
            logger.setLevel(logging.INFO)  # Default to INFO if LOG_LEVEL is not recognized

    # Configure console output
    console_handler = logging.StreamHandler(sys.stdout)
    console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)

    # Add handlers to logger
    logger.addHandler(console_handler)

    return logger
