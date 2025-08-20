from fastapi import FastAPI

app = FastAPI(Title="Orders Service", description="Service for managing orders", version="1.0.0")

@app.get("/")
async def welvome():
    return {"message": "Hola desade Orders Service"}

@app.post("/create-order")
async def create_order(item_id: int):
    return {"message": f"Orden para item {item_id} creada exitosamente"}