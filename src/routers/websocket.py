from fastapi import APIRouter, WebSocket
from src.classes.relay import Relay

router = APIRouter()
relay = Relay()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await relay.register_client(websocket)

def get_relay() -> Relay:
    return relay
