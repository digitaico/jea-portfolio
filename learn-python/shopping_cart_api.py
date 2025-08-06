"""
Shopping Cart API using FastAPI and Redis.
Demonstrates Redis usage for session management and cart operations.
"""

from fastapi import FastAPI, HTTPException, Depends, Query, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
import uuid
import time

from redis_manager import cart_manager
from config import settings

# Create FastAPI app
app = FastAPI(
    title="Shopping Cart API",
    description="Redis-powered shopping cart with session management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# Pydantic models
class ProductData(BaseModel):
    name: str = Field(..., description="Product name")
    price: float = Field(..., ge=0, description="Product price")
    description: Optional[str] = Field(None, description="Product description")
    image_url: Optional[str] = Field(None, description="Product image URL")


class CartItem(BaseModel):
    product_id: str = Field(..., description="Product identifier")
    quantity: int = Field(..., ge=1, description="Quantity")
    product_data: Optional[ProductData] = Field(None, description="Product information")


class CartResponse(BaseModel):
    user_id: str
    items: Dict[str, Any]
    total_items: int
    total_price: float


class SessionData(BaseModel):
    user_id: str
    cart_count: int
    last_activity: float


class RedisInfoResponse(BaseModel):
    status: str
    version: Optional[str] = None
    used_memory: Optional[str] = None
    connected_clients: Optional[int] = None
    total_commands_processed: Optional[int] = None


# Dependency for user identification (in real app, this would be JWT token)
def get_user_id(x_user_id: Optional[str] = Header(None)) -> str:
    """Get user ID from header or generate a temporary one."""
    if x_user_id:
        return x_user_id
    
    # Generate temporary user ID for demo
    return f"temp_user_{int(time.time())}"


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {
        "message": "Shopping Cart API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint."""
    redis_info = cart_manager.get_redis_info()
    
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "redis": redis_info,
        "services": {
            "redis": "connected" if cart_manager.is_connected() else "disconnected"
        }
    }


@app.post("/cart/add", response_model=Dict[str, Any])
async def add_to_cart(
    item: CartItem,
    user_id: str = Depends(get_user_id)
):
    """
    Add item to shopping cart.
    
    - **product_id**: Product identifier
    - **quantity**: Quantity to add
    - **product_data**: Product information (optional)
    """
    if not cart_manager.is_connected():
        raise HTTPException(status_code=503, detail="Redis service unavailable")
    
    # Prepare product data
    product_data = None
    if item.product_data:
        product_data = item.product_data.dict()
    
    # Add to cart
    success = cart_manager.add_to_cart(
        user_id=user_id,
        product_id=item.product_id,
        quantity=item.quantity,
        product_data=product_data
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add item to cart")
    
    # Get updated cart
    cart = cart_manager.get_cart(user_id)
    cart_count = cart_manager.get_cart_count(user_id)
    
    return {
        "message": "Item added to cart successfully",
        "user_id": user_id,
        "product_id": item.product_id,
        "quantity": item.quantity,
        "cart_count": cart_count,
        "cart": cart
    }


@app.get("/cart", response_model=CartResponse)
async def get_cart(user_id: str = Depends(get_user_id)):
    """Get user's shopping cart."""
    if not cart_manager.is_connected():
        raise HTTPException(status_code=503, detail="Redis service unavailable")
    
    cart_items = cart_manager.get_cart(user_id)
    cart_count = cart_manager.get_cart_count(user_id)
    
    # Calculate total price
    total_price = 0.0
    for product_id, item_data in cart_items.items():
        price = item_data.get('price', 0.0)
        quantity = item_data.get('quantity', 0)
        total_price += price * quantity
    
    return CartResponse(
        user_id=user_id,
        items=cart_items,
        total_items=cart_count,
        total_price=round(total_price, 2)
    )


@app.put("/cart/update/{product_id}", response_model=Dict[str, Any])
async def update_cart_item(
    product_id: str,
    quantity: int = Query(..., ge=0, description="New quantity"),
    user_id: str = Depends(get_user_id)
):
    """
    Update cart item quantity.
    
    - **product_id**: Product identifier
    - **quantity**: New quantity (0 to remove item)
    """
    if not cart_manager.is_connected():
        raise HTTPException(status_code=503, detail="Redis service unavailable")
    
    success = cart_manager.update_cart_item(user_id, product_id, quantity)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update cart item")
    
    cart_count = cart_manager.get_cart_count(user_id)
    
    return {
        "message": "Cart item updated successfully",
        "user_id": user_id,
        "product_id": product_id,
        "quantity": quantity,
        "cart_count": cart_count
    }


@app.delete("/cart/remove/{product_id}", response_model=Dict[str, Any])
async def remove_from_cart(
    product_id: str,
    user_id: str = Depends(get_user_id)
):
    """
    Remove item from cart.
    
    - **product_id**: Product identifier to remove
    """
    if not cart_manager.is_connected():
        raise HTTPException(status_code=503, detail="Redis service unavailable")
    
    success = cart_manager.remove_from_cart(user_id, product_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Product not found in cart")
    
    cart_count = cart_manager.get_cart_count(user_id)
    
    return {
        "message": "Item removed from cart successfully",
        "user_id": user_id,
        "product_id": product_id,
        "cart_count": cart_count
    }


@app.delete("/cart/clear", response_model=Dict[str, Any])
async def clear_cart(user_id: str = Depends(get_user_id)):
    """Clear entire shopping cart."""
    if not cart_manager.is_connected():
        raise HTTPException(status_code=503, detail="Redis service unavailable")
    
    success = cart_manager.clear_cart(user_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to clear cart")
    
    return {
        "message": "Cart cleared successfully",
        "user_id": user_id
    }


@app.get("/cart/count", response_model=Dict[str, Any])
async def get_cart_count(user_id: str = Depends(get_user_id)):
    """Get total number of items in cart."""
    if not cart_manager.is_connected():
        raise HTTPException(status_code=503, detail="Redis service unavailable")
    
    cart_count = cart_manager.get_cart_count(user_id)
    
    return {
        "user_id": user_id,
        "cart_count": cart_count
    }


@app.post("/session/create", response_model=Dict[str, Any])
async def create_session(
    session_data: SessionData,
    user_id: str = Depends(get_user_id)
):
    """
    Create a new session for user.
    
    - **user_id**: User identifier
    - **cart_count**: Current cart count
    - **last_activity**: Last activity timestamp
    """
    if not cart_manager.is_connected():
        raise HTTPException(status_code=503, detail="Redis service unavailable")
    
    session_id = cart_manager.create_session(user_id, session_data.dict())
    
    if not session_id:
        raise HTTPException(status_code=500, detail="Failed to create session")
    
    return {
        "message": "Session created successfully",
        "session_id": session_id,
        "user_id": user_id,
        "expires_in": cart_manager.session_expiry
    }


@app.get("/session/{session_id}", response_model=Dict[str, Any])
async def get_session(session_id: str):
    """
    Get session data.
    
    - **session_id**: Session identifier
    """
    if not cart_manager.is_connected():
        raise HTTPException(status_code=503, detail="Redis service unavailable")
    
    session_data = cart_manager.get_session(session_id)
    
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "session_data": session_data
    }


@app.delete("/session/{session_id}", response_model=Dict[str, Any])
async def delete_session(session_id: str):
    """
    Delete a session.
    
    - **session_id**: Session identifier
    """
    if not cart_manager.is_connected():
        raise HTTPException(status_code=503, detail="Redis service unavailable")
    
    success = cart_manager.delete_session(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "message": "Session deleted successfully",
        "session_id": session_id
    }


@app.post("/cache/product/{product_id}", response_model=Dict[str, Any])
async def cache_product(
    product_id: str,
    product_data: ProductData
):
    """
    Cache product data.
    
    - **product_id**: Product identifier
    - **product_data**: Product information to cache
    """
    if not cart_manager.is_connected():
        raise HTTPException(status_code=503, detail="Redis service unavailable")
    
    success = cart_manager.cache_product(product_id, product_data.dict())
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to cache product")
    
    return {
        "message": "Product cached successfully",
        "product_id": product_id,
        "expires_in": cart_manager.product_cache_expiry
    }


@app.get("/cache/product/{product_id}", response_model=Dict[str, Any])
async def get_cached_product(product_id: str):
    """
    Get cached product data.
    
    - **product_id**: Product identifier
    """
    if not cart_manager.is_connected():
        raise HTTPException(status_code=503, detail="Redis service unavailable")
    
    product_data = cart_manager.get_cached_product(product_id)
    
    if not product_data:
        raise HTTPException(status_code=404, detail="Product not found in cache")
    
    return {
        "product_id": product_id,
        "product_data": product_data
    }


@app.get("/redis/info", response_model=RedisInfoResponse)
async def get_redis_info():
    """Get Redis server information."""
    redis_info = cart_manager.get_redis_info()
    return RedisInfoResponse(**redis_info)


# Sample data for testing
SAMPLE_PRODUCTS = {
    "prod_001": {
        "name": "Laptop",
        "price": 999.99,
        "description": "High-performance laptop",
        "image_url": "https://example.com/laptop.jpg"
    },
    "prod_002": {
        "name": "Mouse",
        "price": 29.99,
        "description": "Wireless mouse",
        "image_url": "https://example.com/mouse.jpg"
    },
    "prod_003": {
        "name": "Keyboard",
        "price": 79.99,
        "description": "Mechanical keyboard",
        "image_url": "https://example.com/keyboard.jpg"
    }
}


@app.post("/demo/setup", response_model=Dict[str, Any])
async def setup_demo(user_id: str = Depends(get_user_id)):
    """Setup demo data for testing."""
    if not cart_manager.is_connected():
        raise HTTPException(status_code=503, detail="Redis service unavailable")
    
    # Cache sample products
    for product_id, product_data in SAMPLE_PRODUCTS.items():
        cart_manager.cache_product(product_id, product_data)
    
    # Add some items to cart
    cart_manager.add_to_cart(user_id, "prod_001", 1, SAMPLE_PRODUCTS["prod_001"])
    cart_manager.add_to_cart(user_id, "prod_002", 2, SAMPLE_PRODUCTS["prod_002"])
    
    return {
        "message": "Demo data setup completed",
        "user_id": user_id,
        "cached_products": list(SAMPLE_PRODUCTS.keys()),
        "cart_items_added": ["prod_001", "prod_002"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "shopping_cart_api:app",
        host=settings.api_host,
        port=8001,  # Different port to avoid conflict
        reload=settings.debug
    ) 