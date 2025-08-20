import asyncio
import json
import os
import asyncio
import json
import os
import nats
from nats.errors import ConnectionClosedError, TimeoutError, NoServersError
from fastapi import FastAPI, HTTPException
from pydantic import BaseModelats
from nats.errors import ConnectionClosedError, TimeoutError, NoServersError
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# NATS client setup
nc = None

# in-memory mock "database"
products_db = {}

# pydantic model for request body validation
class Product(BaseModel):
    name: str
    price: float
    description: str

app = FastAPI(title= "Servicio Productos", version= "1.0.0")

@app.on_event("startup")
async def startup_event():
    """ Conectarse a NATS at startup"""
    global nc
    nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
    try:
        nc = await nats.connect(servers=[nats_url])
        print("Conectado a Servidor NATS")
    except Exception as e:
        print(f"No se pudo conectar a NATS: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """ Desconectarse de NATS en shutdown"""
    if nc and not nc.is_closed:
        await nc.close()
        print("Desconectado del servidor NATS")
@app.get("/")
async def root():
    return {"message": "Bienvenido al servicio Products"}


@app.post("/products")
async def create_product(product: Product):
    """
    Crea un nuevo producto y publica en evento a NATS.
    Es un endpoint RESTful y tambien dispara un evento async.
    """
    # Simula almacenar el producto
    product_id = len(products_db) + 1
    product_data = product.dict()
    product_data["id"] = product_id
    products_db[product_id] = product_data
    
    # Crear payload del evento
    event_payload = {
        "event_type": "product.created",
        "data": product_data
    }
    
    # Publicar el evento a NATS. Subject `product.created`
    # `orders-service` listener lo detectara -listen.
    try:
        if nc and nc.is_connected:
            await nc.publish("product.created", json.dumps(event_payload).encode('utf-8'))
            print(f"Evento publicado 'product.created' para el producto con ID {product_id}")
    except (ConnectionClosedError, TimeoutError) as e:
        print(f"Error publicando a NATS: {e}")

    return {"message": "Producto creado exitosamente" , "product_id": product_id}


@app.get("/products/{product_id}")
async def get_product(product_id: int):
    """Retorna  un producto por su ID."""
    product = products_db.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product no encontrado")
    return product