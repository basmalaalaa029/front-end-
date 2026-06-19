"""
app.queue — Per-model GPU worker queue primitive.

Each feature instantiates its own _ModelQueue; no global singleton.
"""

from __future__ import annotations

import os
import queue
import threading
from typing import Any, Callable, Dict, Optional

from cv_agent.app.config import logger


class ModelQueue:
    """Serialise inference for one model through a dedicated worker thread."""

    SUBMIT_TIMEOUT_S: float = float(os.getenv("GPU_SUBMIT_TIMEOUT_S", "300"))

    def __init__(self, name: str) -> None:
        self.name = name
        self._q: queue.Queue = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._restart_count = 0
        self._stop_event = threading.Event()
        self._ready = threading.Event()

    def _make_thread(self) -> threading.Thread:
        return threading.Thread(
            target=self._worker,
            daemon=True,
            name=f"gpu-{self.name}-{self._restart_count}",
        )

    def _ensure_worker(self) -> None:
        with self._lock:
            if self._thread is None or not self._thread.is_alive():
                if self._thread is not None:
                    self._restart_count += 1
                    logger.warning(
                        "ModelQueue[%s]: worker dead — restarting (#%d)",
                        self.name, self._restart_count,
                    )
                self._thread = self._make_thread()
                self._thread.start()

    def mark_ready(self) -> None:
        self._ready.set()

    def start(self) -> None:
        self._ensure_worker()

    def _worker(self) -> None:
        logger.info("ModelQueue[%s] worker started", self.name)
        while not self._stop_event.is_set():
            try:
                fn, args, kwargs, holder, event = self._q.get(timeout=1.0)
            except queue.Empty:
                continue
            except Exception as exc:
                logger.error("ModelQueue[%s]: queue read error: %s", self.name, exc)
                continue
            try:
                holder["result"] = fn(*args, **kwargs)
            except BaseException as exc:
                holder["error"] = exc
                logger.error("ModelQueue[%s]: inference failed: %s", self.name, exc)
            finally:
                event.set()
                self._q.task_done()
        logger.info("ModelQueue[%s] worker stopped", self.name)

    def submit(
        self,
        fn: Callable,
        *args: Any,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> Any:
        self._ensure_worker()
        holder: Dict[str, Any] = {}
        done = threading.Event()
        self._q.put((fn, args, kwargs, holder, done))
        wait_s = timeout_s if timeout_s is not None else self.SUBMIT_TIMEOUT_S
        wait_s = wait_s if wait_s > 0 else None
        finished = done.wait(timeout=wait_s)
        if wait_s is not None and not finished:
            with self._lock:
                self._thread = None
            raise RuntimeError(
                f"ModelQueue[{self.name}] timed out after {wait_s}s"
            )
        if "error" in holder:
            raise holder["error"]
        return holder["result"]

    @property
    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def queue_size(self) -> int:
        return self._q.qsize()

    @property
    def restart_count(self) -> int:
        return self._restart_count

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
