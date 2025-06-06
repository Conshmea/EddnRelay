import logging
from fastapi import APIRouter, WebSocket
from src.classes.relay import Relay

router = APIRouter()
relay = Relay()
logger = logging.getLogger('EddnRelay')

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "unknown"
    logger.info("New WebSocket connection attempt from %s", client)
    try:
        await relay.register_client(websocket)
    except Exception as e:
        logger.error("Error handling WebSocket connection from %s: %s", client, e, exc_info=True)
        raise
    finally:
        logger.info("WebSocket connection from %s closed", client)

def get_relay() -> Relay:
    return relay
