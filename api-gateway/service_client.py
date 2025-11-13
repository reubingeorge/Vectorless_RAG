"""
Service Client with Retry Logic and Circuit Breakers - Phase 3
"""
import httpx
from httpx_retries import RetryTransport, Retry
from circuitbreaker import circuit
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ServiceClient:
    """HTTP client with retry logic and circuit breaker for microservice communication"""

    def __init__(
        self,
        service_name: str,
        base_url: str,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        timeout: float = 30.0
    ):
        self.service_name = service_name
        self.base_url = base_url
        self.timeout = timeout

        # Configure retry policy
        retry = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[408, 429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
        )

        # Create transport with retry
        transport = RetryTransport(retry=retry)

        # Create sync client
        self.client = httpx.Client(
            transport=transport,
            base_url=base_url,
            timeout=timeout
        )

        # Create async client
        self.async_client = httpx.AsyncClient(
            transport=RetryTransport(retry=retry),
            base_url=base_url,
            timeout=timeout
        )

        logger.info(
            f"Initialized {service_name} client with {max_retries} retries, "
            f"{timeout}s timeout"
        )

    @circuit(failure_threshold=5, recovery_timeout=60, expected_exception=httpx.HTTPError)
    async def get(self, path: str, **kwargs) -> httpx.Response:
        """GET request with circuit breaker"""
        try:
            logger.debug(f"[{self.service_name}] GET {path}")
            response = await self.async_client.get(path, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPError as e:
            logger.error(f"[{self.service_name}] GET {path} failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"[{self.service_name}] Unexpected error: {str(e)}")
            raise

    @circuit(failure_threshold=5, recovery_timeout=60, expected_exception=httpx.HTTPError)
    async def post(self, path: str, **kwargs) -> httpx.Response:
        """POST request with circuit breaker"""
        try:
            logger.debug(f"[{self.service_name}] POST {path}")
            response = await self.async_client.post(path, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPError as e:
            logger.error(f"[{self.service_name}] POST {path} failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"[{self.service_name}] Unexpected error: {str(e)}")
            raise

    @circuit(failure_threshold=5, recovery_timeout=60, expected_exception=httpx.HTTPError)
    async def delete(self, path: str, **kwargs) -> httpx.Response:
        """DELETE request with circuit breaker"""
        try:
            logger.debug(f"[{self.service_name}] DELETE {path}")
            response = await self.async_client.delete(path, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPError as e:
            logger.error(f"[{self.service_name}] DELETE {path} failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"[{self.service_name}] Unexpected error: {str(e)}")
            raise

    @circuit(failure_threshold=5, recovery_timeout=60, expected_exception=httpx.HTTPError)
    async def patch(self, path: str, **kwargs) -> httpx.Response:
        """PATCH request with circuit breaker"""
        try:
            logger.debug(f"[{self.service_name}] PATCH {path}")
            response = await self.async_client.patch(path, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPError as e:
            logger.error(f"[{self.service_name}] PATCH {path} failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"[{self.service_name}] Unexpected error: {str(e)}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """Health check without circuit breaker (so it doesn't trip on failures)"""
        try:
            response = await self.async_client.get(
                "/health",
                timeout=5.0  # Short timeout for health checks
            )
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "service": self.service_name,
                    **response.json()
                }
            else:
                return {
                    "status": "unhealthy",
                    "service": self.service_name,
                    "http_status": response.status_code
                }
        except httpx.TimeoutException:
            return {
                "status": "timeout",
                "service": self.service_name,
                "error": "Health check timed out"
            }
        except httpx.ConnectError:
            return {
                "status": "unreachable",
                "service": self.service_name,
                "error": "Cannot connect to service"
            }
        except Exception as e:
            return {
                "status": "error",
                "service": self.service_name,
                "error": str(e)
            }

    def close(self):
        """Close client connections"""
        self.client.close()

    async def aclose(self):
        """Close async client connections"""
        await self.async_client.aclose()


class ServiceRegistry:
    """Central registry for all microservice clients"""

    def __init__(self):
        self.services: Dict[str, ServiceClient] = {}
        logger.info("Initializing service registry")

    def register(
        self,
        name: str,
        url: str,
        max_retries: int = 3,
        timeout: float = 30.0
    ) -> ServiceClient:
        """Register a service client"""
        client = ServiceClient(
            service_name=name,
            base_url=url,
            max_retries=max_retries,
            timeout=timeout
        )
        self.services[name] = client
        logger.info(f"Registered service: {name} at {url}")
        return client

    def get(self, name: str) -> Optional[ServiceClient]:
        """Get a service client by name"""
        return self.services.get(name)

    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all registered services"""
        health_status = {}
        for name, client in self.services.items():
            health_status[name] = await client.health_check()
        return health_status

    async def close_all(self):
        """Close all service clients"""
        for client in self.services.values():
            await client.aclose()
