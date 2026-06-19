"""Single inference queue for CV analysis judges (max_concurrent=1)."""

from __future__ import annotations

from cv_agent.app.queue import ModelQueue
from cv_analysis.config import get_cv_analysis_config

inference_queue = ModelQueue("cv-analysis-judge")
