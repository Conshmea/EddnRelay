import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Request, HTTPException

from src.classes.mongo_handler import MongoHandler

router = APIRouter(prefix="/messages", tags=["messages"])
mongo_handler = MongoHandler()
logger = logging.getLogger('EddnRelay')

@router.post("/24-hour-cache")
async def filter_messages(request: Request, data: Dict[str, Any]) -> List[Dict[str, Any]]:
    
    filters = data.get("filters", {})
    after_timestamp = data.get("after_timestamp", None)
    max_items = data.get("max_items", None)
    
    client_host = request.client.host if request.client else "unknown"
    logger.info("Message filter request received from %s", client_host)
    logger.debug("Filter parameters: filters=%s, timestamp=%s, max_items=%s", filters, after_timestamp, max_items)
    try:
        messages = await mongo_handler.get_messages(filters, after_timestamp, max_items)
        
        if messages is None:
            raise HTTPException(status_code=500, detail="Internal server error")
        
        logger.info("Successfully returned %d messages", len(messages))
        return messages
    except Exception as e:
        logger.error("Error processing filter request: %s", e, exc_info=True)
        raise
