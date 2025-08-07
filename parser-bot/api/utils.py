import asyncio
import time
from functools import wraps
from typing import Callable, Any

def rate_limit(requests_per_second: int):
    """Декоратор для ограничения количества запросов в секунду"""
    def decorator(func: Callable) -> Callable:
        last_called = 0
        
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            nonlocal last_called
            elapsed = time.time() - last_called
            wait_time = max(0, 1/requests_per_second - elapsed)
            
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            
            last_called = time.time()
            return await func(*args, **kwargs)
        return wrapper
    return decorator