from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings

class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip API key check for OpenAPI documentation and health check
        if request.url.path in [ "/", "/api/v1/utils/health-check/"]:
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        
        if not api_key:
            raise HTTPException(
                status_code=401,
                detail="X-API-Key header is missing. Please provide it as 'X-API-Key'."
            )
        
        try:
            if not api_key:
                raise ValueError("API key is missing")
            
            if api_key != settings.APP_API_KEY:
                raise HTTPException(
                    status_code=403,
                    detail="Invalid API key."
                )
            
            return await call_next(request)
            
        except ValueError as e:
            raise HTTPException(
                status_code=401,
                detail=str(e)
            ) 