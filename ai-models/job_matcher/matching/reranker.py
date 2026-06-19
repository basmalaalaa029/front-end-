"""
matching/reranker.py
--------------------
Cross-encoder re-ranking stage.

Re-scores top-N candidates with cross-encoder/ms-marco-MiniLM-L-6-v2,
blending the result with the existing composite score.
Gracefully degrades if sentence-transformers is not installed.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np

log = logging.getLogger("job_matcher")

_MODEL_ID = "cross-encoder/ms-marco-MiniLM-L-6-v2"
BLEND_ALPHA = 0.35
_MAX_JD_CHARS = 512


class CrossEncoderReranker:
    def __init__(self, model_id: str = _MODEL_ID):
        self._model_id = model_id
        self._model = None
        self._available: Optional[bool] = None

    def _load(self) -> bool:
        if self._available is not None:
            return self._available

        try:
            from sentence_transformers import CrossEncoder
            try:
                self._model = CrossEncoder(self._model_id, local_files_only=True)
                log.info(f"Cross-encoder loaded from local cache: {self._model_id}")
            except Exception:
                log.info(f"Downloading cross-encoder: {self._model_id} …")
                self._model = CrossEncoder(self._model_id)
                log.info("Cross-encoder downloaded and ready")
            self._available = True
        except ImportError:
            log.warning(
                "sentence-transformers not installed — cross-encoder re-ranking disabled.")
            self._available = False
        except Exception as exc:
            log.warning(f"Could not load cross-encoder ({exc}) — skipping re-ranking")
            self._available = False

        return self._available

    @staticmethod
    def _build_query(profile: dict) -> str:
        parts = []

        title = profile.get("current_title") or ""
        if title:
            parts.append(title)

        skills = profile.get("skills_hard", [])
        if skills:
            parts.append("Skills: " + ", ".join(skills[:12]))

        seniority = profile.get("seniority", "")
        domain = profile.get("domain", "")
        if seniority and domain:
            parts.append(f"{seniority} level {domain} professional")

        preferred = profile.get("preferred_roles", [])
        if preferred:
            parts.append("Looking for: " + ", ".join(preferred[:4]))

        summary = profile.get("summary_for_search", "")
        if summary:
            parts.append(summary)

        return " | ".join(parts)[:400]

    @staticmethod
    def _build_passage(job: dict) -> str:
        title = job.get("title", "")
        desc = job.get("description", "")
        tags = " ".join(job.get("tags", []) or [])
        combined = f"{title}. {tags}. {desc}"
        return combined[:_MAX_JD_CHARS]

    def rerank(self, profile: dict, jobs: list, top_n: int = 50) -> list:
        if not jobs:
            return jobs

        if not self._load():
            log.info("Cross-encoder unavailable — skipping re-rank")
            return jobs

        candidates = jobs[:top_n]
        tail = jobs[top_n:]

        query = self._build_query(profile)
        pairs = [(query, self._build_passage(j)) for j in candidates]

        try:
            raw_scores = self._model.predict(pairs, show_progress_bar=False)
        except Exception as exc:
            log.warning(f"Cross-encoder inference failed: {exc} — skipping re-rank")
            return jobs

        raw = np.array(raw_scores, dtype=float)
        rmin, rmax = raw.min(), raw.max()
        if rmax > rmin:
            ce_norm = (raw - rmin) / (rmax - rmin) * 100
        else:
            ce_norm = np.full_like(raw, 50.0)

        for job, ce in zip(candidates, ce_norm):
            orig = float(job.get("score", 50))
            blended = (1 - BLEND_ALPHA) * orig + BLEND_ALPHA * float(ce)
            job["score_before_rerank"] = orig
            job["score_ce"] = round(float(ce), 1)
            job["score"] = round(blended, 1)

        candidates.sort(key=lambda j: j["score"], reverse=True)

        log.info(f"Cross-encoder re-ranked {len(candidates)} jobs "
                 f"(α={BLEND_ALPHA}, model={self._model_id})")
        return candidates + tail

    def is_available(self) -> bool:
        return self._load()
