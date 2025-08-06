#!/usr/bin/env python3
"""
Redis Shopping Cart Demo
Demonstrates Redis usage for shopping cart functionality.
"""

import time
import json
from typing import Dict, Any
from redis_manager import cart_manager


def print_separator(title: str):
    """Print a formatted separator."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def demo_redis_connection():
    """Demonstrate Redis connection."""
    print_separator("Redis Connection Test")
    
    if cart_manager.is_connected():
        print("✅ Redis connection successful!")
        
        # Get Redis info
        redis_info = cart_manager.get_redis_info()
        print(f"📊 Redis Info:")
        for key, value in redis_info.items():
            print(f"  {key}: {value}")
    else:
        print("❌ Redis connection failed!")
        print("💡 Make sure Redis is running:")
        print("   docker-compose up -d redis")
        return False
    
    return True


def demo_shopping_cart():
    """Demonstrate shopping cart functionality."""
    print_separator("Shopping Cart Demo")
    
    user_id = f"demo_user_{int(time.time())}"
    print(f"👤 Using user ID: {user_id}")
    
    # Sample products
    products = {
        "laptop": {
            "name": "MacBook Pro",
            "price": 1299.99,
            "description": "High-performance laptop",
            "image_url": "https://example.com/macbook.jpg"
        },
        "mouse": {
            "name": "Wireless Mouse",
            "price": 29.99,
            "description": "Ergonomic wireless mouse",
            "image_url": "https://example.com/mouse.jpg"
        },
        "keyboard": {
            "name": "Mechanical Keyboard",
            "price": 149.99,
            "description": "RGB mechanical keyboard",
            "image_url": "https://example.com/keyboard.jpg"
        }
    }
    
    # 1. Add items to cart
    print("\n🛒 Adding items to cart...")
    
    for product_id, product_data in products.items():
        success = cart_manager.add_to_cart(
            user_id=user_id,
            product_id=product_id,
            quantity=1,
            product_data=product_data
        )
        
        if success:
            print(f"  ✅ Added {product_data['name']} (${product_data['price']})")
        else:
            print(f"  ❌ Failed to add {product_data['name']}")
    
    # 2. Get cart contents
    print("\n📋 Cart contents:")
    cart = cart_manager.get_cart(user_id)
    
    if cart:
        total_price = 0.0
        for product_id, item_data in cart.items():
            name = item_data.get('name', 'Unknown')
            price = item_data.get('price', 0.0)
            quantity = item_data.get('quantity', 0)
            item_total = price * quantity
            total_price += item_total
            
            print(f"  📦 {name}: {quantity}x ${price:.2f} = ${item_total:.2f}")
        
        print(f"  💰 Total: ${total_price:.2f}")
    else:
        print("  🛒 Cart is empty")
    
    # 3. Get cart count
    cart_count = cart_manager.get_cart_count(user_id)
    print(f"\n🔢 Total items in cart: {cart_count}")
    
    # 4. Update item quantity
    print("\n✏️  Updating quantities...")
    
    # Update laptop quantity to 2
    success = cart_manager.update_cart_item(user_id, "laptop", 2)
    if success:
        print("  ✅ Updated laptop quantity to 2")
    else:
        print("  ❌ Failed to update laptop quantity")
    
    # 5. Remove an item
    print("\n🗑️  Removing item...")
    success = cart_manager.remove_from_cart(user_id, "mouse")
    if success:
        print("  ✅ Removed mouse from cart")
    else:
        print("  ❌ Failed to remove mouse")
    
    # 6. Show updated cart
    print("\n📋 Updated cart contents:")
    cart = cart_manager.get_cart(user_id)
    
    if cart:
        total_price = 0.0
        for product_id, item_data in cart.items():
            name = item_data.get('name', 'Unknown')
            price = item_data.get('price', 0.0)
            quantity = item_data.get('quantity', 0)
            item_total = price * quantity
            total_price += item_total
            
            print(f"  📦 {name}: {quantity}x ${price:.2f} = ${item_total:.2f}")
        
        print(f"  💰 Total: ${total_price:.2f}")
    
    return user_id


def demo_session_management():
    """Demonstrate session management."""
    print_separator("Session Management Demo")
    
    user_id = f"session_user_{int(time.time())}"
    
    # 1. Create session
    print("🔐 Creating session...")
    session_data = {
        "user_id": user_id,
        "cart_count": 3,
        "last_activity": time.time(),
        "preferences": {
            "theme": "dark",
            "language": "en"
        }
    }
    
    session_id = cart_manager.create_session(user_id, session_data)
    if session_id:
        print(f"  ✅ Session created: {session_id}")
    else:
        print("  ❌ Failed to create session")
        return
    
    # 2. Get session data
    print("\n📄 Retrieving session data...")
    retrieved_session = cart_manager.get_session(session_id)
    if retrieved_session:
        print(f"  ✅ Session data retrieved:")
        for key, value in retrieved_session.items():
            print(f"    {key}: {value}")
    else:
        print("  ❌ Failed to retrieve session data")
    
    # 3. Delete session
    print("\n🗑️  Deleting session...")
    success = cart_manager.delete_session(session_id)
    if success:
        print("  ✅ Session deleted")
    else:
        print("  ❌ Failed to delete session")


def demo_product_caching():
    """Demonstrate product caching."""
    print_separator("Product Caching Demo")
    
    # Sample product data
    product_data = {
        "name": "Gaming Headset",
        "price": 89.99,
        "description": "7.1 surround sound gaming headset",
        "image_url": "https://example.com/headset.jpg",
        "specifications": {
            "brand": "GamingPro",
            "connectivity": "USB",
            "weight": "350g"
        }
    }
    
    product_id = "headset_001"
    
    # 1. Cache product
    print("💾 Caching product data...")
    success = cart_manager.cache_product(product_id, product_data)
    if success:
        print(f"  ✅ Product {product_id} cached successfully")
    else:
        print(f"  ❌ Failed to cache product {product_id}")
        return
    
    # 2. Retrieve cached product
    print("\n📖 Retrieving cached product...")
    cached_product = cart_manager.get_cached_product(product_id)
    if cached_product:
        print(f"  ✅ Cached product retrieved:")
        for key, value in cached_product.items():
            if isinstance(value, dict):
                print(f"    {key}:")
                for sub_key, sub_value in value.items():
                    print(f"      {sub_key}: {sub_value}")
            else:
                print(f"    {key}: {value}")
    else:
        print("  ❌ Failed to retrieve cached product")


def demo_redis_operations():
    """Demonstrate various Redis operations."""
    print_separator("Redis Operations Demo")
    
    if not cart_manager.is_connected():
        print("❌ Redis not connected")
        return
    
    try:
        # 1. Set and get a simple key
        print("🔑 Setting and getting simple key...")
        cart_manager.redis.set("demo:greeting", "Hello Redis!")
        greeting = cart_manager.redis.get("demo:greeting")
        print(f"  ✅ Greeting: {greeting}")
        
        # 2. Set key with expiry
        print("\n⏰ Setting key with expiry...")
        cart_manager.redis.setex("demo:temp", 10, "This will expire in 10 seconds")
        temp_value = cart_manager.redis.get("demo:temp")
        print(f"  ✅ Temp value: {temp_value}")
        
        # 3. List operations
        print("\n📝 List operations...")
        cart_manager.redis.lpush("demo:list", "item1", "item2", "item3")
        list_items = cart_manager.redis.lrange("demo:list", 0, -1)
        print(f"  ✅ List items: {list_items}")
        
        # 4. Hash operations
        print("\n🗂️  Hash operations...")
        cart_manager.redis.hset("demo:user", mapping={
            "name": "John Doe",
            "email": "john@example.com",
            "age": "30"
        })
        user_data = cart_manager.redis.hgetall("demo:user")
        print(f"  ✅ User data: {user_data}")
        
        # 5. Clean up demo keys
        print("\n🧹 Cleaning up demo keys...")
        keys_to_delete = ["demo:greeting", "demo:temp", "demo:list", "demo:user"]
        for key in keys_to_delete:
            cart_manager.redis.delete(key)
        print("  ✅ Demo keys cleaned up")
        
    except Exception as e:
        print(f"  ❌ Error in Redis operations: {e}")


def main():
    """Main demo function."""
    print("🚀 Redis Shopping Cart Demo")
    print("=" * 60)
    
    # Check Redis connection
    if not demo_redis_connection():
        print("\n💡 To start Redis:")
        print("   1. Make sure Docker is running")
        print("   2. Run: docker-compose up -d redis")
        print("   3. Run this demo again")
        return
    
    # Run demos
    try:
        # Shopping cart demo
        user_id = demo_shopping_cart()
        
        # Session management demo
        demo_session_management()
        
        # Product caching demo
        demo_product_caching()
        
        # Redis operations demo
        demo_redis_operations()
        
        # Clean up demo cart
        print_separator("Cleanup")
        success = cart_manager.clear_cart(user_id)
        if success:
            print(f"✅ Cleared demo cart for user {user_id}")
        else:
            print(f"❌ Failed to clear demo cart")
        
        print("\n🎉 Demo completed successfully!")
        print("\n💡 Next steps:")
        print("   1. Start the shopping cart API: python shopping_cart_api.py")
        print("   2. Visit: http://localhost:8001/docs")
        print("   3. Test the API endpoints")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 