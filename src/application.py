import asyncio
import sys
import logging
import os
import platform
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI

from src.classes.eddn_listener import EddnListener
from src.utils.logging_config import setup_logging
from src.utils.middleware import RequestLoggingMiddleware
from src.routers.websocket import router as ws_router, get_relay
from src.routers.messages import router as messages_router
from src.constants import RELAY_HOST, RELAY_PORT, USE_MONGODB

# Set Windows-specific event loop policy to handle async operations properly
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def start_eddn_listener():
    logger = logging.getLogger('EddnRelay')
    try:
        listener = EddnListener(get_relay())
        await listener.start()
    except Exception as e:
        logger.error("EDDN listener error: %s", e, exc_info=True)
        raise

@asynccontextmanager
async def lifespan(_: FastAPI):
    # Startup
    logger = logging.getLogger('EddnRelay')
    logger.info("Application startup initiated")
    logger.info("System information: Python %s, OS: %s", 
                sys.version.split()[0], platform.platform())
    logger.info("Working directory: %s", os.getcwd())
    
    listener_task = asyncio.create_task(start_eddn_listener())
    logger.info("EDDN listener task created")
    
    yield
    
    # Shutdown
    logger.info("Application shutdown initiated")
    listener_task.cancel()
    try:
        await listener_task
    except asyncio.CancelledError:
        logger.info("EDDN listener stopped")
    logger.info("Application shutdown completed")

app = FastAPI(lifespan=lifespan)
app.add_middleware(RequestLoggingMiddleware)
app.include_router(ws_router)
if USE_MONGODB:
    app.include_router(messages_router)

def main():
    logger = setup_logging()
    logger.info("Starting EDDN Relay application...")
    
    try:
        logger.info("Starting web server on %s:%d", RELAY_HOST, RELAY_PORT)
        uvicorn.run(
            app,
            host=RELAY_HOST,
            port=RELAY_PORT,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("Received shutdown signal, stopping services...")
    except Exception as e:
        logger.error("Unexpected error occurred %s", e, exc_info=True)
        raise
    finally:
        logger.info("Application shutdown complete")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error("Fatal error in main loop %s", e, exc_info=True)
        sys.exit(1)
