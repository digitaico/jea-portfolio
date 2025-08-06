"""
Redis manager for shopping cart functionality.
Demonstrates Redis usage with FastAPI for session management and caching.
"""

import json
import time
from typing import Optional, Dict, List, Any
from redis import Redis, ConnectionPool
from redis.exceptions import RedisError, ConnectionError
import logging

from config import get_redis_url, settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RedisManager:
    """
    Redis manager for shopping cart and session management.
    Handles connection, cart operations, and data persistence.
    """
    
    def __init__(self):
        """Initialize Redis connection."""
        self.redis_url = get_redis_url()
        self.redis: Optional[Redis] = None
        self._connect()
    
    def _connect(self):
        """Establish Redis connection."""
        try:
            # Parse Redis URL
            if self.redis_url.startswith('redis://'):
                # Remove redis:// prefix
                url = self.redis_url[8:]
                
                # Handle authentication
                if '@' in url:
                    auth_part, host_part = url.split('@', 1)
                    if ':' in auth_part:
                        password = auth_part.split(':', 1)[1]
                    else:
                        password = auth_part
                else:
                    host_part = url
                    password = None
                
                # Parse host and port
                if ':' in host_part:
                    host_port, db_part = host_part.split('/', 1)
                    if ':' in host_port:
                        host, port = host_port.split(':')
                        port = int(port)
                    else:
                        host = host_port
                        port = 6379
                else:
                    host = host_part
                    port = 6379
                    db_part = '0'
                
                # Parse database number
                db = int(db_part) if db_part.isdigit() else 0
                
                # Create connection pool
                pool = ConnectionPool(
                    host=host,
                    port=port,
                    password=password,
                    db=db,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                
                self.redis = Redis(connection_pool=pool)
                
                # Test connection
                self.redis.ping()
                logger.info(f"✅ Connected to Redis at {host}:{port}")
                
            else:
                # Fallback to direct connection
                self.redis = Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    password=settings.redis_password,
                    db=settings.redis_db,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                self.redis.ping()
                logger.info(f"✅ Connected to Redis at {settings.redis_host}:{settings.redis_port}")
                
        except (RedisError, ConnectionError) as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self.redis = None
    
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        if not self.redis:
            return False
        try:
            self.redis.ping()
            return True
        except (RedisError, ConnectionError):
            return False
    
    def _get_cart_key(self, user_id: str) -> str:
        """Generate Redis key for user's cart."""
        return f"cart:{user_id}"
    
    def _get_session_key(self, session_id: str) -> str:
        """Generate Redis key for session."""
        return f"session:{session_id}"
    
    def _get_product_key(self, product_id: str) -> str:
        """Generate Redis key for product cache."""
        return f"product:{product_id}"


class ShoppingCartManager(RedisManager):
    """
    Shopping cart manager using Redis.
    Handles cart operations, session management, and product caching.
    """
    
    def __init__(self):
        """Initialize shopping cart manager."""
        super().__init__()
        self.cart_expiry = 24 * 60 * 60  # 24 hours
        self.session_expiry = 60 * 60  # 1 hour
        self.product_cache_expiry = 30 * 60  # 30 minutes
    
    def add_to_cart(self, user_id: str, product_id: str, quantity: int = 1, 
                   product_data: Optional[Dict] = None) -> bool:
        """
        Add product to user's cart.
        
        Args:
            user_id: User identifier
            product_id: Product identifier
            quantity: Quantity to add
            product_data: Product information (name, price, etc.)
            
        Returns:
            bool: Success status
        """
        if not self.is_connected():
            logger.error("Redis not connected")
            return False
        
        try:
            cart_key = self._get_cart_key(user_id)
            
            # Get current cart
            cart_data = self.redis.hgetall(cart_key)
            
            # Get current quantity (handle JSON data)
            current_quantity = 0
            if product_id in cart_data:
                try:
                    # Try to parse as JSON first
                    item_data = json.loads(cart_data[product_id])
                    current_quantity = item_data.get('quantity', 0)
                except (json.JSONDecodeError, TypeError):
                    # If not JSON, try to parse as integer
                    try:
                        current_quantity = int(cart_data[product_id])
                    except (ValueError, TypeError):
                        current_quantity = 0
            
            new_quantity = current_quantity + quantity
            
            if new_quantity <= 0:
                # Remove item if quantity is 0 or negative
                self.redis.hdel(cart_key, product_id)
                logger.info(f"Removed product {product_id} from cart for user {user_id}")
            else:
                # Add/update item
                item_data = {
                    'quantity': new_quantity,
                    'added_at': time.time()
                }
                
                # Add product data if provided
                if product_data:
                    item_data.update(product_data)
                
                # Store as JSON
                self.redis.hset(cart_key, product_id, json.dumps(item_data))
                logger.info(f"Added {quantity} of product {product_id} to cart for user {user_id}")
            
            # Set expiry
            self.redis.expire(cart_key, self.cart_expiry)
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding to cart: {e}")
            return False
    
    def remove_from_cart(self, user_id: str, product_id: str) -> bool:
        """
        Remove product from user's cart.
        
        Args:
            user_id: User identifier
            product_id: Product identifier
            
        Returns:
            bool: Success status
        """
        if not self.is_connected():
            return False
        
        try:
            cart_key = self._get_cart_key(user_id)
            result = self.redis.hdel(cart_key, product_id)
            logger.info(f"Removed product {product_id} from cart for user {user_id}")
            return result > 0
            
        except RedisError as e:
            logger.error(f"Error removing from cart: {e}")
            return False
    
    def get_cart(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's cart contents.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict: Cart contents with product details
        """
        if not self.is_connected():
            return {}
        
        try:
            cart_key = self._get_cart_key(user_id)
            cart_data = self.redis.hgetall(cart_key)
            
            cart_items = {}
            for product_id, item_json in cart_data.items():
                try:
                    item_data = json.loads(item_json)
                    cart_items[product_id] = item_data
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in cart for product {product_id}")
                    continue
            
            return cart_items
            
        except RedisError as e:
            logger.error(f"Error getting cart: {e}")
            return {}
    
    def update_cart_item(self, user_id: str, product_id: str, quantity: int) -> bool:
        """
        Update quantity of a cart item.
        
        Args:
            user_id: User identifier
            product_id: Product identifier
            quantity: New quantity
            
        Returns:
            bool: Success status
        """
        if quantity <= 0:
            return self.remove_from_cart(user_id, product_id)
        
        return self.add_to_cart(user_id, product_id, quantity)
    
    def clear_cart(self, user_id: str) -> bool:
        """
        Clear user's entire cart.
        
        Args:
            user_id: User identifier
            
        Returns:
            bool: Success status
        """
        if not self.is_connected():
            return False
        
        try:
            cart_key = self._get_cart_key(user_id)
            result = self.redis.delete(cart_key)
            logger.info(f"Cleared cart for user {user_id}")
            return result > 0
            
        except RedisError as e:
            logger.error(f"Error clearing cart: {e}")
            return False
    
    def get_cart_count(self, user_id: str) -> int:
        """
        Get total number of items in user's cart.
        
        Args:
            user_id: User identifier
            
        Returns:
            int: Total number of items
        """
        if not self.is_connected():
            return 0
        
        try:
            cart_key = self._get_cart_key(user_id)
            cart_data = self.redis.hgetall(cart_key)
            
            total_count = 0
            for item_json in cart_data.values():
                try:
                    item_data = json.loads(item_json)
                    total_count += item_data.get('quantity', 0)
                except json.JSONDecodeError:
                    continue
            
            return total_count
            
        except RedisError as e:
            logger.error(f"Error getting cart count: {e}")
            return 0
    
    def create_session(self, user_id: str, session_data: Dict) -> Optional[str]:
        """
        Create a new session for user.
        
        Args:
            user_id: User identifier
            session_data: Session data to store
            
        Returns:
            str: Session ID or None if failed
        """
        if not self.is_connected():
            return None
        
        try:
            session_id = f"{user_id}_{int(time.time())}_{hash(str(session_data))}"
            session_key = self._get_session_key(session_id)
            
            # Store session data
            self.redis.setex(
                session_key,
                self.session_expiry,
                json.dumps(session_data)
            )
            
            logger.info(f"Created session {session_id} for user {user_id}")
            return session_id
            
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Error creating session: {e}")
            return None
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get session data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dict: Session data or None if not found
        """
        if not self.is_connected():
            return None
        
        try:
            session_key = self._get_session_key(session_id)
            session_data = self.redis.get(session_key)
            
            if session_data:
                return json.loads(session_data)
            return None
            
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Error getting session: {e}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: Success status
        """
        if not self.is_connected():
            return False
        
        try:
            session_key = self._get_session_key(session_id)
            result = self.redis.delete(session_key)
            logger.info(f"Deleted session {session_id}")
            return result > 0
            
        except RedisError as e:
            logger.error(f"Error deleting session: {e}")
            return False
    
    def cache_product(self, product_id: str, product_data: Dict, expiry: Optional[int] = None) -> bool:
        """
        Cache product data.
        
        Args:
            product_id: Product identifier
            product_data: Product data to cache
            expiry: Cache expiry time in seconds
            
        Returns:
            bool: Success status
        """
        if not self.is_connected():
            return False
        
        try:
            product_key = self._get_product_key(product_id)
            expiry = expiry or self.product_cache_expiry
            
            self.redis.setex(
                product_key,
                expiry,
                json.dumps(product_data)
            )
            
            logger.info(f"Cached product {product_id}")
            return True
            
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Error caching product: {e}")
            return False
    
    def get_cached_product(self, product_id: str) -> Optional[Dict]:
        """
        Get cached product data.
        
        Args:
            product_id: Product identifier
            
        Returns:
            Dict: Product data or None if not cached
        """
        if not self.is_connected():
            return None
        
        try:
            product_key = self._get_product_key(product_id)
            product_data = self.redis.get(product_key)
            
            if product_data:
                return json.loads(product_data)
            return None
            
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Error getting cached product: {e}")
            return None
    
    def get_redis_info(self) -> Dict[str, Any]:
        """
        Get Redis server information.
        
        Returns:
            Dict: Redis server info
        """
        if not self.is_connected():
            return {"status": "disconnected"}
        
        try:
            info = self.redis.info()
            return {
                "status": "connected",
                "version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed")
            }
        except RedisError as e:
            logger.error(f"Error getting Redis info: {e}")
            return {"status": "error", "message": str(e)}


# Global shopping cart manager instance
cart_manager = ShoppingCartManager() 