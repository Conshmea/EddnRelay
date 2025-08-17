import logging
from datetime import timedelta, datetime, timezone
from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import DESCENDING

from src.classes.filter import Filter
from src.constants import MONGODB_URI, MONGODB_DATABASE, CACHE_TTL

class MongoHandler:
    def __init__(self, uri: str = MONGODB_URI, database: str = MONGODB_DATABASE):
        self.logger = logging.getLogger('EddnRelay')
        self.logger.info("Initializing MongoDB connection to %s, database: %s", uri, database)
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[database]
        self.messages = self.db.messages
        self.message_expiry = timedelta(hours=CACHE_TTL)

    async def initialize(self):
        self.logger.info("Creating MongoDB indexes...")
        try:
            await self.messages.create_index("timestamp", expireAfterSeconds=int(self.message_expiry.total_seconds()))
            await self.messages.create_index([("timestamp", DESCENDING)])
            self.logger.info("Successfully created MongoDB indexes")
        except Exception as e:
            self.logger.error("Failed to create MongoDB indexes: %s", e, exc_info=True)
            raise

    async def store_message(self, message: Dict[str, Any]):
        try:
            timestamp = message.get('message', {}).get('timestamp', None)
            if not timestamp:
                timestamp = message.get('header', {}).get('gatewayTimestamp', None)
            if not timestamp:
                self.logger.error("Message does not contain a timestamp")
                raise ValueError("Message must contain a timestamp")

            timestamp = datetime.fromisoformat(timestamp)
            if timestamp.tzinfo is None:
                self.logger.warning("Timestamp is naive, assuming UTC")
                timestamp = timestamp.replace(tzinfo=timezone.utc)

            message['timestamp'] = timestamp

            result = await self.messages.insert_one(message)
            self.logger.debug("Stored message with ID %s", result.inserted_id)
        except Exception as e:
            self.logger.error("Failed to store message: %s", e, exc_info=True)
            raise

    async def get_messages(self, conditions: dict, after_timestamp: str | None = None, max_items: int | None = None) -> List[Dict[str, Any]] | None:
        self.logger.debug("Retrieving messages with conditions: %s, afterTimestamp: %s, max_items: %s",
                         conditions, after_timestamp, max_items)
        try:
            filters = Filter()
            filters.set_filter_from_json(conditions)

            query = filters.to_mongo_query()

            if after_timestamp:
                timestamp = datetime.fromisoformat(after_timestamp)
                if timestamp.tzinfo is None:
                    self.logger.warning("afterTimestamp is naive, assuming UTC")
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                if query:
                    query = {
                        '$and': [
                            query,
                            {'timestamp': {'$gt': timestamp}}
                        ]
                    }
                else:
                    query = {'timestamp': {'$gt': timestamp}}
            
            self.logger.debug("Executing MongoDB query: %s", query)
            
            if max_items is not None:
                cursor = self.messages.find(query).sort('timestamp', DESCENDING).limit(max_items)
            else:
                cursor = self.messages.find(query).sort('timestamp', DESCENDING)
            messages = []
            
            async for message in cursor:
                message.pop('_id', None)
                message.pop('timestamp', None)
                messages.append(message)
            
            self.logger.info("Retrieved %d messages matching query", len(messages))
            return messages
            
        except Exception as e:
            self.logger.error("Failed to retrieve messages: %s", e, exc_info=True)
            return None