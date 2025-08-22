from events.nats_client import EventBus
from events.events_store import EventStore
import asyncio
import json
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import os


event_bus = EventBus()
event_store = EventStore()

app = FastAPI(Title="Orders Service", description="Service for managing orders", version="1.0.0")

# DB setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db_1:5432/orders_db")
engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Definir modelo pydantic de base de datos para órdenes
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=True)    

# Definir Pydantic model para validar datos de órdenes
class OrderCreate(BaseModel):
    item_id: int
    quantity: int
    price: Optional[float] = None

# Modelo para la respuesta de órdenes
class OrderResponse(BaseModel):
    id: int
    item_id: int
    quantity: int
    price: Optional[float] = None

    class Config:
        orm_mode = True

# Dependencia para obtener DB session por cada request
def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def create_db_tables():
    Base.metadata.create_all(bind=engine)

# Crear las tablas en la base de datos al iniciar aplicación
@app.on_event("startup")
async def startup_event():
    await event_bus.connect()
    # subscribe to events
    await event_bus.subscribe("orders", handle_order_event)
    #  create tables if they do not exist 
    await create_db_tables()

async def handle_order_event(event_data: dict):
    print(f"Servicio ordenes recibió evento: {event_data}")

    # Guardar evento en event store
    await event_store.store_event(event_data)

    if event_data.get("event_type") == "order.created":
        order_data = event_data.get("data", {})
        print(f"Procesando orden creada: {order_data}")

        # crear orden en la base de datos
        db_order = Order(
            item_id=order_data.get("item_id"),
            quantity=order_data.get("quantity"),
            price=order_data.get("price")
        )

        # Añadir la orden a la base de datos
        db = next(get_db())
        db.add(db_order)
        db.commit()
        db.refresh(db_order) # Refrescar el objeto para obtener el ID generado

        print(f"Orden {db_order.id} creada en la base de datos.")

        # guardar evento en event store
        order_created_event = {
            "event_type": "order.created",
            "correlation_id": event_data.get("correlation_id"),
            "data": {
                "order_id": db_order.id,
                "item_id": db_order.item_id,
                "quantity": db_order.quantity,
                "price": db_order.price,
                "status": "created"
            }
        }

        await event_store.store_event(order_created_event)

        # publicar eventos para otros servicios
        await event_bus.publish("inventory", {
            "event_type": "inventory.reserved",
            "correlation_id": event_data.get("correlation_id"),
            "data": {
                "item_id": db_order.item_id,
                "quantity": db_order.quantity,
                "order_id": db_order.id
            }        
        })


    await event_bus.publish("inventory", {
        "event_type": "inventory.reserved",
        "correlation_id": event_data.get("correlation_id"),
        "data": {
            "item_id": order.item_id,
            "quantity": order.quantity,
            "order_id": order.id
        }
    })

    await event_bus.publish("notifications", {
        "event_type": "order.confirmation",
        "correlation_id": event_data.get("correlation_id"),
        "data": {
            "order_id": order.id,
            "item_id": order.item_id,
            "quantity": order.quantity,
            "status": "created"
        }
    })


# --- Endpoints --- 
@app.get("/")
async def welcome():
    return {"message": "Hola desade Orders Service"}


@app.get("/get-orders", response_model=List[OrderResponse])
async def get_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).all()
    return orders

@app.get("/get-orders/{order_id}", response_model=OrderResponse)
async def get_orders_by_id(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.post("/create-order", response_model=OrderResponse)
async def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    db_order = Order(
        item_id=order.item_id, 
        quantity=order.quantity, 
        price=order.price
    )
    # Añadir la orden a la base de datos
    db.add(db_order)
    db.commit()
    db.refresh(db_order) # Refrescar el objeto para obtener el ID generado
    return db_order