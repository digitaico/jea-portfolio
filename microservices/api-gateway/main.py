from events.schemas import OrderCreatedEvent, NotificationSentEvent
from events.nats_client import EventBus
from events.events_store import EventStore
import asyncio
import uuid
from fastapi import FastAPI, APIRouter, Request, HTTPException
from starlette.responses import JSONResponse

event_bus = EventBus() 
event_store = EventStore()

app = FastAPI(title="API Gateway", version="1.0.0")
api_router = APIRouter()


@app.on_event("startup")
async def startup_event():
    """
    Inicializa el cliente HTTP y el EventBus al iniciar la aplicacion.
    """
    await event_bus.connect()
    print("EventBus conectado exitosamente.")
    print("EventStore inicializando.")

@api_router.get("/")
async def welcome():
    return {"message": "Bienvenido al API Gateway - JEA"}

@api_router.get("/orders/list")
async def get_orders_list():
    """
    Manda un request al servicio orders.
    """
    return {"message": "Endpoint de orders list", "status": "ok"}


@api_router.get("/orders/{order_id}")
async def get_order_by_id(order_id: int):
    """
    Manda un request al servicio orders para recibir data de orden especifica.
    """
    return {"message": f"Order {order_id} disponible via events. Buscar en eventos"}


@api_router.post("/orders/create")
async def create_order_endpoint(request: Request):
    """
    Acepta POST request y redirije un payload JSON al servicio orders.
    Luego envia notificacion al servicio notifications si la orden fue creada exitosamente.
    """
    try:
        # 1. lee JSON body del request
        payload = await request.json()
    
        event = OrderCreatedEvent(
            correlation_id=request.headers.get("X-Correlation-ID", str(uuid.uuid4())),
            data=payload
        )

        # Store event
        event_id = await event_store.store_event(event.dict())
        # publica evento a NATS solo si la orden fue creada exitosamente
        await event_bus.publish("orders", event)

        # return inmediate response, no waiting for HTTP
        return {
            "status": "accepted",
            "event_id": event_id,
            "correlation_id": event.correlation_id,
            "message": "Orden creada exitosamente, evento publicado."
        }
    except Exception as e:
        raise HTTPException(
            detail={"error": f"Fallo al crear orden: {e}"},
            status_code=400
        )


@api_router.post("/notifications/send-notification/")
async def send_notification(request: Request):
    """
    Acepta POST request y redirije un payload JSON al servicio notifications.
    """
    try:
        # lee JSON body del request
        payload = await request.json()
        # manda el payload al servicio notifications
        notification_event = {
            "event_type": "notification.requested",
            "correlation_id": request.headers.get("X-Correlation-ID", str(uuid.uuid4())),
            "data": payload 
        }

        event:id = await event_store.store_event(notification_event)
        await event_bus.publish("notifications", notification_event)

        return {
            "status": "accepted",
            "event_id": event_id,
            "correlation_id": notification_event["correlation_id"],
        }

    except Exception as e: 
        raise HTTPException(
            detail={"error": f"Fallo al enviar notificacion: {e}"},
            status_code=400
        )
        

@api_router.get("/products")
async def get_products_service_status():
    """
    Manda un request al servicio products.
    """
    return {"message": "Data de Productos disponible via eventos. Use eventos para consultar"} 



# --. Events endpoints --- 
@api_router.get("/events")
async def get_all_events():
    """
    Endpoint para obtener todos los eventos almacenados.
    """
    events = await event_store.get_all_events()
    return {"events": events, "total": len(events)}

@api_router.get("/events/{event_type}")
async def get_events_by_type(event_type: str):
    """
    Endpoint para obtener eventos por tipo.
    """
    events = await event_store.get_events_by_type(event_type)
    return {"events": events, "total": len(events)}

@api_router.get("/events/correlation/{correlation_id}")
async def get_events_by_correlation_id(correlation_id: str):
    """
    Endpoint para obtener eventos por correlation_id.
    """
    events = await event_store.get_events_by_correlation_id(correlation_id)
    return {"events": events, "total": len(events)}

# Agregar router a la aplicacion principal
app.include_router(api_router)