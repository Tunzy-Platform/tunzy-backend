from asyncio import Queue, Condition
import asyncio
import threading

from app.core.logging import get_logger

logger = get_logger(__name__)


class AdjustableSemaphore:
    def __init__(self, total_limit: int) -> None:
        self.total_limit = total_limit
        self.total_tasks = 0
        self._condition = Condition()

    async def acquire(self):
        async with self._condition:
            while self.total_tasks >= self.total_limit:
                await self._condition.wait()
            self.total_tasks += 1

    async def release(self):
        async with self._condition:
            self.total_tasks -= 1
            self._condition.notify_all()

    async def update_limit(self, new_limit):
        async with self._condition:
            logger.info(
                "update semaphore limit from %d to %d", self.total_limit, new_limit
            )
            self.total_limit = new_limit
            self._condition.notify_all()


class DownloadManager:
    def __init__(self, total_concurrent_downloads: int) -> None:
        self.semaphore = AdjustableSemaphore(total_concurrent_downloads)
        self.queue = Queue()
        self.tasks: dict[int, tuple[asyncio.Task, threading.Event]] = {}
        self.progress_reports: dict[int, int] = {}

    async def worker(self):
        while True:
            (
                download_id,
                download_task,
                cancel_event,
                priority,
            ) = await self.queue.get()
            task = asyncio.create_task(
                self.task_runner(
                    download_task,
                )
            )
            self.tasks[download_id] = (task, cancel_event)

    async def task_runner(self, task: asyncio.Task):
        await self.semaphore.acquire()
        try:
            await task
        finally:
            await self.semaphore.release()

    async def add_to_queue(self, download_id, download_task, cancel_event, priority):
        await self.queue.put((download_id, download_task, cancel_event, priority))

    async def cancel_download(self, download_id):
        logger.info("Start Canceling %d", download_id)
        task, cancel_event = self.tasks.get(download_id, (None, threading.Event()))
        if not task:
            return
        cancel_event.set()
        task.cancel()
        logger.info("Start Canceling %d Done", download_id)
