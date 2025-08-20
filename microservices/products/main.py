from fastapi import FastAPI

app = FastAPI(title="Products Service API", version="1.0.0")

@app.get("/")
async def welcome():
    return {"message": "Hola desde Products Service API!"}

@app.get("/list-products")
async def list_products():
    products = [
        {"id": 1, "name": "Product 1", "price": 10.99},
        {"id": 2, "name": "Product 2", "price": 19.99},
        {"id": 3, "name": "Product 3", "price": 29.99},
        {"id": 4, "name": "Product 4", "price": 39.99},
        {"id": 5, "name": "Product 5", "price": 49.99} 
    ]
    return {"products": products}