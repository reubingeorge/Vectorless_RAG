"""
Chat Service with WebSocket Support
Refactored with modular handlers and routes for better maintainability
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
import logging

# Import handlers
from handlers.connection import handle_connect, handle_disconnect
from handlers.query import handle_query
from handlers.message import handle_message

# Import routes
from routes.health import router as health_router
from routes.emit import create_emit_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True
)

# Create FastAPI app
app = FastAPI(title="Chat Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    await handle_connect(sio, sid, environ)

@sio.event
async def disconnect(sid):
    await handle_disconnect(sio, sid)

@sio.event
async def query(sid, data):
    await handle_query(sio, sid, data)

@sio.event
async def message(sid, data):
    await handle_message(sio, sid, data)

# Include REST API routers
app.include_router(health_router)
app.include_router(create_emit_router(sio))

# Combine FastAPI and Socket.IO into single ASGI app
socket_app = socketio.ASGIApp(
    sio,
    other_asgi_app=app,
    socketio_path='/socket.io'
)

# Export the combined app
app = socket_app

if __name__ == "__main__":
    import uvicorn
    # Note: When running directly, use the socket_app
    uvicorn.run("main:socket_app", host="0.0.0.0", port=8004, reload=True)
