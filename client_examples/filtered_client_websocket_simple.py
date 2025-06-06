# This script implements a WebSocket client for the EDDN relay
import asyncio
import json
from websockets import exceptions as ws_exceptions
import websockets

class EddnRelayClient:
    """A WebSocket client for connecting to and receiving data from an EDDN relay."""
    def __init__(self, uri: str, new_filter: dict):
        """Initialize the client with connection details and message filters.
        
        Args:
            host (str): The relay server hostname
            port (int): The relay server port
            new_filter (dict): Filter configuration for message filtering
        """
        self.uri = uri
        self.filters = new_filter

    async def update_filters(self, websocket, new_filter: dict):
        """Send filter updates to the relay server.
        
        Args:
            websocket: Active websocket connection
            new_filter (dict): New filter configuration to apply
        """
        await websocket.send(json.dumps({
            'type': 'filter',
            'filter': new_filter
        }))

    async def connect(self):
        """Establish and maintain a WebSocket connection to the relay.
        
        Implements automatic reconnection on connection loss.
        Handles incoming messages and prints them to console.
        """
        while True:
            try:
                async with websockets.connect(self.uri) as websocket:
                    print("Connected to relay")

                    await self.update_filters(websocket, self.filters)

                    try:
                        async for message in websocket:
                            data = json.loads(message)
                            print(f"Received message: {json.dumps(data, indent=2)}")
                    except websockets.ConnectionClosed:
                        print("Connection lost, attempting to reconnect...")
            except (ws_exceptions.WebSocketException, OSError) as e:
                print(f"Connection failed: {e}")
                print("Retrying in 5 seconds...")
                await asyncio.sleep(5)

    async def run(self):
        """Start the client operation."""
        await self.connect()

def main():
    new_filter = {
                "type": "all",
                "conditions": [
                    {
                        "type": "exact",
                        "path": "message.event",
                        "value": "Scan"
                    }
                ]
            }

    # Create and run the client
    client = EddnRelayClient("ws://localhost:9600/ws", new_filter)
    asyncio.run(client.run())

if __name__ == "__main__":
    main()
