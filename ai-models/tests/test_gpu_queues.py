"""CV analysis inference queue."""

from __future__ import annotations

import threading
import time

from cv_agent.app.queue import ModelQueue
from cv_analysis.judges.queue import inference_queue


def test_inference_queue_singleton():
    assert inference_queue.name == "cv-analysis-judge"


def test_model_queue_serializes_calls():
    q = ModelQueue("test-serialize")
    q.mark_ready()
    results: list[int] = []

    def work(n: int) -> int:
        time.sleep(0.05)
        results.append(n)
        return n

    threads = [
        threading.Thread(target=lambda n=i: q.submit(work, n))
        for i in range(3)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)

    assert sorted(results) == [0, 1, 2]
