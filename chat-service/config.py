"""Configuration and service URLs"""
import os

# Service URLs
QUERY_SERVICE = os.getenv("QUERY_SERVICE_URL", "http://query-service:8003")
STORAGE_SERVICE = os.getenv("STORAGE_SERVICE_URL", "http://storage-service:8005")
SETTINGS_SERVICE = os.getenv("SETTINGS_SERVICE_URL", "http://settings-service:8007")
