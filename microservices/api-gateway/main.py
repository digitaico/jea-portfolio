import os
import httpx
from fastapi import FastAPI, Request, HTTPException

app = FastAPI(title="API Gateway", version="1.0.0")

# Service URLs from environment variables, provided by docker-compose.
PRODUCTS_SERVICE_URL = os.getenv("PRODUCTS_SERVICE_URL")

@app.get("/")
async def root():
    return {"message": "Welcome to the API Gateway"}

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def route_request(path: str, request: Request):
    """
    Routes incoming requests to the correct microservice based on the path.
    This is a basic, generic routing function.
    """
    async with httpx.AsyncClient() as client:
        # Determine the target service based on the path prefix
        if path.startswith("products"):
            target_url = f"{PRODUCTS_SERVICE_URL}/{path}"
        else:
            raise HTTPException(status_code=404, detail="Path not found in any service")
        
        # Forward the request to the target service
        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=request.headers,
                data=await request.body()
            )
            response.raise_for_status() # Raise exception for 4xx or 5xx status codes
            
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Service unavailable: {e}")
