import json
import asyncio
import logging
import zlib
import zmq
import zmq.asyncio

from src.constants import EDDN_URL, EDDN_TIMEOUT, USE_MONGODB
from src.classes.mongo_handler import MongoHandler

class EddnListener:
    """
    A class that listens to the EDDN ZeroMQ feed and processes incoming messages.
    
    Attributes:
        relay: The relay instance that will receive processed messages
        running (bool): Flag indicating if the listener is active
        logger: Logger instance for the class
        context: ZeroMQ context for async operations
        subscriber: ZeroMQ SUB socket for receiving messages
    """

    def __init__(self, relay):
        """
        Initialize the EDDN listener with a relay instance.
        
        Args:
            relay: The relay instance that will handle processed messages
        """
        self.relay = relay
        self.running = True
        self.logger = logging.getLogger('EddnRelay')

        # Initialize ZMQ with asyncio context
        self.logger.info("Initializing EDDN listener, connecting to %s", EDDN_URL)
        try:
            self.context = zmq.asyncio.Context()
            self.subscriber = self.context.socket(zmq.SUB)
            self.subscriber.setsockopt(zmq.SUBSCRIBE, b"")
            self.subscriber.setsockopt(zmq.RCVTIMEO, EDDN_TIMEOUT)
            self.subscriber.connect(EDDN_URL)
            self.logger.info("Successfully connected to EDDN")
        except zmq.ZMQError as e:
            self.logger.error("Failed to initialize ZMQ connection: %s", e, exc_info=True)
            raise

    async def start(self):
        """
        Start listening for EDDN messages asynchronously.
        Processes incoming messages, decompresses them, and forwards them to the relay.
        Handles errors and maintains connection stability.
        """
        self.logger.info("Starting EDDN listener...")
        message_count = 0
        error_count = 0
        
        if USE_MONGODB:
            self.mongo_handler = MongoHandler()
            await self.mongo_handler.initialize()
            
        self.logger.info("EDDnListener started, waiting for messages...")
        while self.running:
            try:
                # Receive and process ZMQ message
                message = await self.subscriber.recv()
                if not message:
                    self.logger.debug("Received empty message, skipping")
                    continue

                # Decompress and parse the message
                message = zlib.decompress(message)
                message = json.loads(message)

                self.logger.debug("Received message: %s",
                                message.get('$schemaRef', 'unknown schema'))
                await self.relay.process_message(message)
                if USE_MONGODB:
                    await self.mongo_handler.store_message(message)
                message_count += 1

                # Log processing statistics periodically
                if message_count % 10000 == 0:
                    self.logger.info("Processed %d messages, %d errors", message_count, error_count)

            except (zmq.ZMQError, json.JSONDecodeError, zlib.error) as e:
                error_count += 1
                self.logger.error("Error processing EDDN message: %s", str(e), exc_info=True)
                if error_count % 10 == 0:
                    self.logger.warning("High error rate: %d errors in %d messages",
                                      error_count, message_count)
                await asyncio.sleep(5)  # Back off on errors

    def stop(self):
        """
        Stop the listener and clean up ZMQ resources.
        """
        self.logger.info("Stopping EDDN listener...")
        self.running = False
        self.subscriber.close()
        self.context.term()
