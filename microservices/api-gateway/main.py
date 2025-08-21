from fastapi import FastAPI, APIRouter, Request, HTTPException
import httpx
from starlette.responses import JSONResponse

app = FastAPI(title="API Gateway", version="1.0.0")
api_router = APIRouter()

# async HTTP client to make requests to other services in docker network
client = httpx.AsyncClient()

@api_router.get("/")
async def welcome():
    return {"message": "Bienvenido al API Gateway - JEA"}

@api_router.get("/orders/list")
async def get_orders_list():
    """
    Manda un request al servicio orders.
    """
    try:
        response = await client.get("http://orders:8001/get-orders")
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail={"error": "Servicio 'Orders' no esta disponible."}
        )
@api_router.get("/orders/{order_id}")
async def get_order_by_id(order_id: int):
    """
    Manda un request al servicio orders para recibir data de orden especifica.
    """
    try:
        response = await client.get(f"http://orders:8001/get-orders/{order_id}")
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail={"error": "Servicio 'Orders' no esta disponible."}
        )   


@api_router.post("/orders/create")
async def create_order_endpoint(request: Request):
    """
    Acepta POST request y redirije un payload JSON al servicio orders.
    """
    try:
        # lee JSON body del request
        payload = await request.json()
        # manda el payload al servicio orders
        response = await client.post("http://orders:8001/create-order", json=payload)
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except httpx.ConnectError:
        raise HTTPException(
            detail={"error": "Servicio 'Orders' no esta disponible."},
            status_code=503
        )
    # caso en que body no es JSON valido
    except Exception as e:
        raise HTTPException(
            detail={"error": f"Peticion invalida, body no conforme: {e}"},
            status_code=400
        )

@api_router.post("/notifications/send")
async def send_notification(request: Request):
    """
    Acepta POST request y redirije un payload JSON al servicio notifications.
    """
    try:
        # lee JSON body del request
        payload = await request.json()
        # manda el payload al servicio notifications
        response = await client.post("http://notifications:8003/send-notification", json=payload)
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except httpx.ConnectError:
        raise HTTPException(
            detail={"error": "Servicio 'Notifications' no esta disponible."},
            status_code=503
        )
    # caso en que body no es JSON valido
    except Exception as e:
        raise HTTPException(
            detail={"error": f"Peticion invalida, body no conforme: {e}"},
            status_code=400
        )   
        

@api_router.get("/products")
async def get_products_service_status():
    """
    Manda un request al servicio products.
    """
    try:
        response = await client.get("http://products:8002")
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except httpx.ConnectError:
        raise HTTPException(
            detail={"error": "Servicio 'Products' no esta disponible."},
            status_code=503
        )

# Agregar router a la aplicacion principal
app.include_router(api_router)
