import asyncio
import sys
import logging
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI

from src.classes.eddn_listener import EddnListener
from src.utils.logging_config import setup_logging
from src.routers.websocket import router as ws_router, get_relay
from src.constants import RELAY_HOST, RELAY_PORT

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
async def lifespan(app: FastAPI):
    # Startup
    logger = logging.getLogger('EddnRelay')
    listener_task = asyncio.create_task(start_eddn_listener())
    yield
    # Shutdown
    listener_task.cancel()
    try:
        await listener_task
    except asyncio.CancelledError:
        logger.info("EDDN listener stopped")

app = FastAPI(lifespan=lifespan)
app.include_router(ws_router)

def main():
    logger = setup_logging()
    logger.info("Starting EDDN Relay application...")
    
    try:
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
