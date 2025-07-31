from fastapi import Request
import logging
import asyncio
from datetime import datetime
MESSAGE_STREAM_RETRY_TIMEOUT = 1000
MESSAGE_STREAM_DELAY = 1 

logger = logging.getLogger(__name__)

def get_message(conversation_id: str):
    return f"conversation_id: {conversation_id} - Counter value {datetime.now()}", True

async def event_generator(request: Request, conversation_id: str):
        while True:
            if await request.is_disconnected():
                logger.debug("Request disconnected")
                break

            # Checks for new messages and return them to client if any
            message, exists = get_message(conversation_id)
            if exists:
                yield {
                    "event": "new_message",
                    "id": "message_id",
                    "retry": MESSAGE_STREAM_RETRY_TIMEOUT,
                    "data": message,
                }
            else:
                yield {
                    "event": "end_event",
                    "id": "message_id",
                    "retry": MESSAGE_STREAM_RETRY_TIMEOUT,
                    "data": f"conversation_id: {conversation_id} - End of the stream",
                }

            await asyncio.sleep(MESSAGE_STREAM_DELAY)