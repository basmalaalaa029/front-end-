"""Interview feature — lightweight answer heuristics (no analysis dependency)."""

from __future__ import annotations

import re


def score_answer_quality(answer: str, question_text: str) -> int:
    """Rule-based 0–100 score for interview answers."""
    text = answer.strip()
    if len(text) < 20:
        return 25
    words = text.split()
    score = 40
    score += min(len(words) // 10 * 5, 25)
    if re.search(r"\d+%|\d+\s*(?:years?|months?|people|users|team)", text, re.I):
        score += 15
    if any(v in text.lower() for v in ("i led", "i built", "i designed", "i implemented", "result")):
        score += 10
    q_words = set(re.findall(r"[a-z]{4,}", question_text.lower()))
    overlap = sum(1 for w in set(re.findall(r"[a-z]{4,}", text.lower())) if w in q_words)
    score += min(overlap * 3, 15)
    return min(100, score)
