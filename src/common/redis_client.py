import redis
from common.config import get_settings

settings = get_settings()

class RedisClient:
    def __init__(self, settings):
        self.settings = settings
        
        r = self.redis.Redis(
            host=self.,
            port=6379,
            db=0  # The default Redis database index
        )