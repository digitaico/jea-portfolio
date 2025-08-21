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
    Luego envia notificacion al servicio notifications si la orden fue creada exitosamente.
    """
    try:
        # 1. lee JSON body del request
        payload = await request.json()
    except json.JSONDecodeError as e:
        raise HTTPException(
            detail={"error": f"Peticion invalida, JSON no conforme: {e}"},
            status_code=400
        )
    except Exception as e:
        raise HTTPException(
            detail={"error": f"Peticion invalida: {e}"},
            status_code=400
        )

    # 2. manda payload al servicio orders
    try:
        order_service_response = await client.post("http://orders:8001/create-order", json=payload)
    except httpx.ConnectError:
        raise HTTPException(
            detail={"error": "Servicio 'Notifications' no esta disponible."},
            status_code=503
        )

    #3. si hubo error creando la orden, retorna error sin mandar notificacion
    if order_service_response.status_code != 200:
        try:
            return JSONResponse(
                content=order_service_response.json(), 
                status_code=order_service_response.status_code
            )
        except json.JSONDecodeError:
            return JSONResponse(
                content={"error": "Error desconocido non-JSON del servicio Orders."}, 
                status_code=order_service_response.status_code
            )

    #4. si la orden fue creada exitosamente, manda notificacion
    try:
        order_data = order_service_response.json()

        if not isinstance(order_data, dict):
            print("ERROR CRITICO: Respuesta 200 pero no contiene data de orden.")
            raise TypeError("Orders retorno una respuesta no Dictionary.")

    except json.JSONDecodeError:
        print("ERROR CRITICO: Respuesta 200 pero non-JSON del servicio Orders.")
        raise HTTPException(
            detail={"error": "Orders retorno una respuesta no JSON."},
            status_code=500
        )
    except TypeError as e:
            print(f"ERROR CRITICO: {e}")
            raise HTTPException(
            detail={"error": f"Orders retorno una respuesta invalida: {e}"},
            status_code=500
        )
    
    # 5. prepara y manda notificacion al servicio notifications
    try:
        notification_payload = {
            "message": f"Orden {order_data.get('id', 'N/A')} creada exitosamente."
        }
        # manda notificacion al servicio notifications
        notification_response = await client.post("http://notifications:8003/send-notification/", json=notification_payload)

        if notification_response.status_code != 200:
            print(f"Error al enviar notificacion: {notification_response.status_code} {notification_response.text}")

    except httpx.ConnectError:
        print("Servicio 'Notifications' no esta disponible para enviar notificacion.")
    except Exception as e:
        print(f"Error inesperado al enviar notificacion: {e}")
    
    # 6. retorna la data de la orden creada
    return JSONResponse(content=order_data, status_code=order_service_response.status_code)


@api_router.post("/notifications/send-notification/")
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
