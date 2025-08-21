from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import os

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

# Crear las tablas en la base de datos al iniciar aplicación
@app.on_event("startup")
def create_db_tables():
    Base.metadata.create_all(bind=engine)

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