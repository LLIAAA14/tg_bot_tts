import asyncio
from collections import deque

class TTSQueueManager:
    def __init__(self, max_concurrent: int = 3):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.queue = deque()
        self.lock = asyncio.Lock()

    async def run(self, coro_func, user_id=None, notify_func=None):
        future = asyncio.get_event_loop().create_future()

        async with self.lock:
            self.queue.append((future, coro_func, user_id, notify_func))
            position = len(self.queue)
            if notify_func and user_id:
                await notify_func(user_id, "⏱ Немного подождите")

        await self._try_run_next()
        return await future

    async def _try_run_next(self):
        async with self.lock:
            if not self.queue or self.semaphore.locked():
                return

            future, coro_func, user_id, notify_func = self.queue.popleft()

            async def task():
                async with self.semaphore:
                    try:
                        result = await coro_func()
                        future.set_result(result)
                    except Exception as e:
                        future.set_exception(e)
                    finally:
                        await self._try_run_next()

            asyncio.create_task(task())

# Глобальный экземпляр очереди
tts_queue = TTSQueueManager(max_concurrent=3)