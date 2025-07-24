import asyncio
from collections import defaultdict
from typing import Awaitable, Callable, Dict, List
import contextlib

from shared.models.events import BaseEvent

# Type alias for event handler coroutine
EventHandler = Callable[[BaseEvent], Awaitable[None]]


class EventBus:
    """A minimal async Pub/Sub event bus.

    Production deployments can swap this with a RabbitMQ, Kafka, or Redis implementation
    by providing a compatible `publish` and `subscribe` API.
    """

    def __init__(self):
        self._subscribers: Dict[str, List[EventHandler]] = defaultdict(list)
        # Use a shared queue for async processing
        self._queue: "asyncio.Queue[BaseEvent]" = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None

    async def start(self):
        """Launch background task that dispatches events to subscribers."""
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._worker())

    async def stop(self):
        if self._worker_task:
            self._worker_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._worker_task
            self._worker_task = None

    async def publish(self, event: BaseEvent):
        await self._queue.put(event)

    def subscribe(self, event_type: str, handler: EventHandler):
        self._subscribers[event_type].append(handler)

    async def _worker(self):
        while True:
            event = await self._queue.get()
            handlers = self._subscribers.get(event.event_type, [])
            for h in handlers:
                try:
                    asyncio.create_task(h(event))  # type: ignore[arg-type]
                except TypeError:
                    # If handler is synchronous, run in default executor
                    loop = asyncio.get_running_loop()
                    loop.run_in_executor(None, h, event)
            self._queue.task_done() 