"""Message event handler"""
import logging

logger = logging.getLogger(__name__)


async def handle_message(sio, sid, data):
    """Legacy message handler"""
    logger.info(f"Message from {sid}: {data}")
    await sio.emit('response', {'message': 'Message received'}, to=sid)
