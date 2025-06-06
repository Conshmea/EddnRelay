import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Request

from src.classes.mongo_handler import MongoHandler

router = APIRouter(prefix="/messages", tags=["messages"])
mongo_handler = MongoHandler()
logger = logging.getLogger('EddnRelay')

@router.post("/24-hour-cache")
async def filter_messages(request: Request, filters: Dict[str, Any], after_timestamp: str | None = None, max_items: int | None = None) -> List[Dict[str, Any]]:
    client_host = request.client.host if request.client else "unknown"
    logger.info("Message filter request received from %s", client_host)
    logger.debug("Filter parameters: filters=%s, timestamp=%s, max_items=%s", filters, after_timestamp, max_items)
    try:
        messages = await mongo_handler.get_messages(filters, after_timestamp, max_items)
        logger.info("Successfully returned %d messages", len(messages))
        return messages
    except Exception as e:
        logger.error("Error processing filter request: %s", e, exc_info=True)
        raise
