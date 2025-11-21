"""
Rate limiting setup for the application using slowapi.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

# Initialize limiter with remote address as key function
limiter = Limiter(key_func=get_remote_address)

def get_limiter():
    """Get limiter instance for dependency injection"""
    return limiter
