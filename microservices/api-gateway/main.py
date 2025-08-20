from fastapi import FastAPI, APIRouter
import httpx
from starlette.responses import JSONResponse

app = FastAPI(title="API Gateway", version="1.0.0")
api_router = APIRouter()

# async HTTP client to make requests to other services in docker network
client = httpx.AsyncClient()

@api_router.get("/")
async def welcome():
    return {"message": "Bienvenido al API Gateway - JEA"}

@api_router.get("/orders")
async def get_orders_service_status():
    """
    Manda un request al servicio orders.
    """
    try:
        response = await client.get("http://orders:8002")
        return JSONResponse(content=response.json(), satatus_code=response.status_code)
    except httpx.ConnectError:
        return JSONResponse(
            content={"error": "Servicio 'Orders' no esta disponible."},
            status_code=503
        )

@api_router.get("/products")
async def get_products_service_status():
    """
    Manda un request al servicio products.
    """
    try:
        response = await client.get("http://products:8001")
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except httpx.ConnectError:
        return JSONResponse(
            content={"error": "Servicio 'Products' no esta disponible."},
            status_code=503
        )

# Agregar router a la aplicacion principal
app.include_router(api_router)
