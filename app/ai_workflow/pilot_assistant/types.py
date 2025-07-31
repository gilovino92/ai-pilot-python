import asyncio

class WorkflowSubscriber:
    id: str
    message_queue: asyncio.Queue

    def __init__(self, id: str):
        self.id = id
        self.message_queue = asyncio.Queue()

    async def get_message(self):
        return await self.message_queue.get()

    async def put_message(self, message: str):
        await self.message_queue.put(message)