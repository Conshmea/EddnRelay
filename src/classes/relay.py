import logging
from typing import Dict
import json
from fastapi import WebSocket

from src.classes.filter import Filter

class Relay:
    """
    A WebSocket server that relays filtered EDDN messages to connected clients.
    
    Attributes:
        clients (Dict[WebSocket, Filter]): Connected clients and their filters
        logger: Logger instance for the class
    """

    def __init__(self):
        """Initialize the relay with an empty client dictionary."""
        self.clients: Dict[WebSocket, Filter] = {}
        self.logger = logging.getLogger('EddnRelay')
        self.logger.info("Relay instance initialized")

    async def register_client(self, websocket: WebSocket):
        """
        Handle new client connections and their filter messages.
        
        Args:
            websocket: The WebSocket connection to the client
            
        Maintains the connection until the client disconnects or an error occurs.
        Processes filter update messages from the client.
        """
        await websocket.accept()
        self.logger.info("New client connected")
        self.clients[websocket] = Filter()
        try:
            while True:
                message = await websocket.receive_json()
                if message['type'] == 'filter':
                    self.logger.debug("Client updated filters")
                    new_filter = Filter()
                    new_filter.set_filter_from_json(message['filter'])
                    self.clients[websocket] = new_filter
        except Exception as e:
            self.logger.info("Client disconnected: %s", str(e))
        finally:
            await self.disconnect_client(websocket)

    async def disconnect_client(self, websocket: WebSocket):
        """
        Handle client disconnection.
        
        Args:
            websocket: The WebSocket connection to the client
            
        Removes the client from the connected clients list.
        """
        if websocket in self.clients:
            del self.clients[websocket]

    async def process_message(self, message: Dict) -> None:
        """
        Process and relay an EDDN message to matching clients.
        
        Args:
            message: The EDDN message to process and relay
            
        Forwards the message to all clients whose filters match the message.
        """
        schema_ref = message.get('$schemaRef', 'unknown schema')
        self.logger.debug("Processing message of type: %s", schema_ref)

        # Convert message to JSON once for efficiency
        json_message = json.dumps(message)
        matched_clients = 0

        # Send to all clients with matching filters
        for websocket, client_filter in list(self.clients.items()):
            if client_filter.matches(message):
                try:
                    await websocket.send_text(json_message)
                    matched_clients += 1
                except Exception:
                    await self.disconnect_client(websocket)

        self.logger.debug("Message forwarded to %d clients", matched_clients)
        if matched_clients == 0:
            self.logger.debug("No clients matched message of type: %s", schema_ref)
