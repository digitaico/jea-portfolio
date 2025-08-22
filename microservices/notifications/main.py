from events.nats_client import EventBus 
import asyncio
import json

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

event_bus = EventBus()

app = FastAPI(title="Notification Service")

class Notification(BaseModel):
    message: str

@app.on_event("startup")
async def startup_event():
    """ Evento de inicio para conectar al bus de eventos """
    try:
        await event_bus.connect()
        print("Connected to NATS server")
        await event_bus.subscribe("orders", handle_order_event)
    except Exception as e:
        print(f"Error connecting to NATS server: {e}")
        raise HTTPException(status_code=500, detail="Failed to connect to NATS server")



async def handle_order_event(event_data: dict):
    """
    Maneja el evento de orden recibido desde el bus de eventos.
    """
    order_data = event_data.get("data", {})
    print(f"Enviando notificacion para orden: {order_data}")

    print(f"Notificacion enviada para orden: {order_data.get('item_id')}")
    # Por ahora, solo imprimimos el evento



@app.get("/")
async def welcome():
    """ Welcome endpoint para notificaciones """
    return {"message":"Hola desde Notificaciones Service!"}

@app.post("/send-notification/")
async def send_notification(notification: Notification):
    """
    Endpoint para enviar una notificación.
    """
    # Aquí iría la lógica para enviar la notificación
    # Por ahora, solo simulamos el envío
    print(f"NOTIFICATION RECEIVED: {notification.message}")
    return {"status": "success", "message": "Notification sent successfully!"}

