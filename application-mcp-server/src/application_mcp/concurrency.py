"""Concurrency control for Graph API requests"""
import asyncio
from contextlib import asynccontextmanager
from .config import config
from .logging_config import get_logger

logger = get_logger(__name__)

# Global semaphore for limiting concurrent requests
_request_semaphore: asyncio.Semaphore = None


def get_request_semaphore() -> asyncio.Semaphore:
    """
    Get or create the global request semaphore.
    
    Returns:
        Semaphore for controlling concurrent requests
    """
    global _request_semaphore
    
    if _request_semaphore is None:
        _request_semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_REQUESTS)
        logger.info(
            f"Request semaphore initialized with limit: {config.MAX_CONCURRENT_REQUESTS}"
        )
    
    return _request_semaphore


@asynccontextmanager
async def request_slot():
    """
    Context manager for acquiring a request slot.
    
    Usage:
        async with request_slot():
            # Make API request
            pass
    
    This ensures no more than MAX_CONCURRENT_REQUESTS are running simultaneously.
    """
    semaphore = get_request_semaphore()
    
    # Try to acquire slot
    await semaphore.acquire()
    
    try:
        yield
    finally:
        # Release slot
        semaphore.release()
