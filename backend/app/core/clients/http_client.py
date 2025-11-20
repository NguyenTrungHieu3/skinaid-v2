import asyncio
import logging
from typing import Dict, Any, Optional
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

logger = logging.getLogger(__name__)

class HTTPClient:
    _client: Optional[httpx.AsyncClient] = None
    _lock = asyncio.Lock()
    
    @classmethod
    async def get_client(cls) -> httpx.AsyncClient:
        if cls._client is None:
            async with cls._lock:
                if cls._client is None:
                    cls._client = httpx.AsyncClient(
                        timeout=30.0,
                        follow_redirects=True,
                        limits=httpx.Limits(
                            max_keepalive_connections=20,
                            max_connections=100
                        )
                    )
        return cls._client
    
    @classmethod
    async def close(cls):
        if cls._client is not None:
            await cls._client.aclose()
            cls._client = None
    
    @classmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((
            httpx.TimeoutException,
            httpx.NetworkError,
            httpx.ConnectError,
            httpx.ReadError
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
    async def post_with_retry(
        cls,
        url: str,
        files: Optional[Dict] = None,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[float] = None,
    ) -> httpx.Response:
        client = await cls.get_client()
        
        try:
            logger.info(f"[HTTP] POST {url}")
            
            # Custom timeout if provided
            request_timeout = timeout if timeout is not None else 30.0
            
            response = await client.post(
                url,
                files=files,
                data=data,
                json=json,
                headers=headers,
                timeout=request_timeout
            )
            
            logger.info(f"[HTTP] POST {url} - Status: {response.status_code}")
            return response
            
        except Exception as e:
            logger.error(f"[HTTP] POST {url} failed: {e}")
            raise
    
    @classmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((
            httpx.TimeoutException,
            httpx.NetworkError,
            httpx.ConnectError,
            httpx.ReadError
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
    async def get_with_retry(
        cls,
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[float] = None,
    ) -> httpx.Response:
        client = await cls.get_client()
        
        try:
            logger.info(f"[HTTP] GET {url}")
            
            # Custom timeout if provided
            request_timeout = timeout if timeout is not None else 30.0
            
            response = await client.get(
                url,
                params=params,
                headers=headers,
                timeout=request_timeout
            )
            
            logger.info(f"[HTTP] GET {url} - Status: {response.status_code}")
            return response
            
        except Exception as e:
            logger.error(f"[HTTP] GET {url} failed: {e}")
            raise
    
    @classmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((
            httpx.TimeoutException,
            httpx.NetworkError,
            httpx.ConnectError,
            httpx.ReadError
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
    async def put_with_retry(
        cls,
        url: str,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[float] = None,
    ) -> httpx.Response:
        client = await cls.get_client()
        
        try:
            logger.info(f"[HTTP] PUT {url}")
            request_timeout = timeout if timeout is not None else 30.0
            
            response = await client.put(
                url,
                data=data,
                json=json,
                headers=headers,
                timeout=request_timeout
            )
            
            logger.info(f"[HTTP] PUT {url} - Status: {response.status_code}")
            return response
            
        except Exception as e:
            logger.error(f"[HTTP] PUT {url} failed: {e}")
            raise
    
    @classmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((
            httpx.TimeoutException,
            httpx.NetworkError,
            httpx.ConnectError,
            httpx.ReadError
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
    async def delete_with_retry(
        cls,
        url: str,
        headers: Optional[Dict] = None,
        timeout: Optional[float] = None,
    ) -> httpx.Response:
        client = await cls.get_client()
        
        try:
            logger.info(f"[HTTP] DELETE {url}")
            request_timeout = timeout if timeout is not None else 30.0
            
            response = await client.delete(
                url,
                headers=headers,
                timeout=request_timeout
            )
            
            logger.info(f"[HTTP] DELETE {url} - Status: {response.status_code}")
            return response
            
        except Exception as e:
            logger.error(f"[HTTP] DELETE {url} failed: {e}")
            raise