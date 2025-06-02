# This script implements a WebSocket client for the EDDN relay
import asyncio
import json
from websockets import exceptions as ws_exceptions
import websockets

class EddnRelayClient:
    """A WebSocket client for connecting to and receiving data from an EDDN relay."""
    def __init__(self, host: str, port: int, new_filter: dict):
        """Initialize the client with connection details and message filters.
        
        Args:
            host (str): The relay server hostname
            port (int): The relay server port
            new_filter (dict): Filter configuration for message filtering
        """
        self.uri = f"ws://{host}:{port}"
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
    # Define a filter for EDDN messages
    # This filter will only pass messages that:
    # 1. Match the journal schema reference
    # 2. AND (have event type "Scan" OR match any event containing "Jump" (e.g., "FSDJump", "CarrierJump"))
    new_filter = {
        "type": "all",  # Root condition: ALL conditions must match
        "conditions": [
            {
                "type": "exact",  # Exact match condition
                "path": "$schemaRef",
                "value": "https://eddn.edcd.io/schemas/journal/1"
            },
            {
                "type": "any",    # ANY of these conditions must match
                "conditions": [
                    {
                        "type": "exact",
                        "path": "message.event",
                        "value": "Scan"
                    },
                    {
                        "type": "regex",
                        "path": "message.event",
                        "pattern": ".*Jump.*"
                    }
                ]
            }
        ]
    }

    # Create and run the client
    client = EddnRelayClient("localhost", 9600, new_filter)
    asyncio.run(client.run())

if __name__ == "__main__":
    main()
