"""Shared dependencies for API Gateway"""
from service_client import ServiceRegistry

# Global service registry instance
service_registry = ServiceRegistry()


def get_service_registry() -> ServiceRegistry:
    """Dependency to inject service registry"""
    return service_registry
