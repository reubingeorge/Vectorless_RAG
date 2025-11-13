"""Connection and disconnection event handlers"""
import logging

logger = logging.getLogger(__name__)


async def handle_connect(sio, sid, environ):
    """Handle client connection"""
    logger.info(f"Client connected: {sid}")
    await sio.emit('connected', {
        'message': 'Connected to chat service',
        'sid': sid
    }, to=sid)


async def handle_disconnect(sio, sid):
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {sid}")
