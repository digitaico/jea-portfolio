from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Notification Service")

class Notification(BaseModel):
    message: str

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

