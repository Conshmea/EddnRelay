import asyncio
import sys
import logging

from src.classes.relay import Relay
from src.classes.eddn_listener import EddnListener
from src.utils.logging_config import setup_logging

# Set Windows-specific event loop policy to handle async operations properly
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    """
    Main asynchronous function that initializes and runs the EDDN relay system.
    Sets up logging, creates relay and listener instances, and manages their lifecycle.
    Handles graceful shutdown on interrupt signals.
    """
    logger = setup_logging()
    logger.info("Starting EDDN Relay application...")

    # Initialize listener outside try block to ensure it's accessible in except blocks
    listener = None

    try:
        # Initialize core components
        relay = Relay()
        listener = EddnListener(relay)

        # Create tasks for concurrent execution
        relay_task = asyncio.create_task(relay.start())
        listener_task = asyncio.create_task(listener.start())

        # Wait for both tasks to complete or for interruption
        await asyncio.gather(relay_task, listener_task)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal, stopping services...")
        if listener:
            listener.stop()
    except Exception as e:
        logger.error("Unexpected error occurred %s", e, exc_info=True)
        if listener:
            listener.stop()
        raise
    finally:
        logger.info("Application shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error("Fatal error in main loop %s", e, exc_info=True)
        sys.exit(1)
