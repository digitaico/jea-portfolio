import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))

from shared.utils.redis_client import RedisClient as BaseRedisClient

class RedisClient(BaseRedisClient):
    """Redis client for API Gateway"""
    pass 