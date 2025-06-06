import logging
from time import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time()
        logger = logging.getLogger('EddnRelay')
        
        # Get client info
        client_host = request.client.host if request.client else "unknown"
        
        logger.debug("Incoming request: %s %s from %s", 
                   request.method, request.url.path, client_host)
        
        try:
            response = await call_next(request)
            
            # Calculate request processing time
            process_time = time() - start_time
            logger.debug("Request completed: %s %s from %s - Status: %d - Time: %.2fs",
                    request.method, request.url.path, client_host, 
                    response.status_code, process_time)
            
            return response
        except Exception as e:
            process_time = time() - start_time
            logger.error("Request failed: %s %s from %s - Error: %s - Time: %.2fs",
                      request.method, request.url.path, client_host,
                      str(e), process_time, exc_info=True)
            raise
