"""
orchestrator.py — Interview strategy engine.
Handles: saturation, novelty, topic memory, phase progression,
follow-up depth limits, and hard completion logic.
"""
import re
from typing import Tuple, List, Dict


# ── Saturation detection ──────────────────────────────────────────────────
def compute_saturation(comp_status: dict, current_comp: str) -> bool:
    s = comp_status.get(current_comp, {})
    return (s.get("depth", 0) >= 2 and s.get("confidence", 0) >= 6) or s.get("depth", 0) >= 3


# ── Topic memory & novelty ────────────────────────────────────────────────
def make_topic_fingerprint(question: str) -> str:
    """Create a normalized fingerprint from a question for dedup."""
    q = question.lower()
    q = re.sub(r'[^a-z0-9 ]', ' ', q)
    words = [w for w in q.split() if len(w) > 3]
    # Keep the 6 most distinctive words
    stop = {'what', 'would', 'could', 'should', 'your', 'have', 'that', 'this',
            'with', 'from', 'when', 'were', 'been', 'they', 'will', 'about',
            'describe', 'explain', 'tell', 'walk', 'through', 'example', 'give',
            'how', 'does', 'did', 'approach', 'experience', 'used', 'using'}
    keywords = [w for w in words if w not in stop][:6]
    return ' '.join(sorted(keywords))


def compute_novelty(question: str, fingerprints: List[str]) -> float:
    """0.0 = identical to past question, 1.0 = completely novel."""
    if not fingerprints:
        return 1.0
    new_fp = make_topic_fingerprint(question)
    new_words = set(new_fp.split())
    if not new_words:
        return 1.0
    max_overlap = 0.0
    for fp in fingerprints[-8:]:
        fp_words = set(fp.split())
        if not fp_words:
            continue
        overlap = len(new_words & fp_words) / max(len(new_words), 1)
        max_overlap = max(max_overlap, overlap)
    return 1.0 - max_overlap


def is_topic_duplicate(question: str, fingerprints: List[str], threshold: float = 0.55) -> bool:
    """Returns True if question is too similar to something already asked."""
    return compute_novelty(question, fingerprints) < (1.0 - threshold)


# ── Phase progression ─────────────────────────────────────────────────────
def get_next_phase(main_q_index: int, level: str) -> str:
    """Phase is driven by main question index, not total turns."""
    if main_q_index == 0:
        return "warmup"
    elif main_q_index < 2:
        return "technical"
    elif main_q_index < 5:
        return "deep_technical"
    elif main_q_index < 7:
        return "behavioral"
    else:
        return "closing"


PHASE_LABELS = {
    "warmup": "Warm-up",
    "technical": "Core Technical",
    "deep_technical": "Deep Dive",
    "behavioral": "Behavioral",
    "closing": "Wrap-up",
}


def get_phase_category(phase: str, competency: str) -> str:
    behavioral_comps = {"behavioral", "communication", "teamwork", "leadership",
                        "conflict_resolution", "collaboration", "learning_mindset"}
    if competency in behavioral_comps:
        return "behavioral"
    return {"warmup": "project", "technical": "technical",
            "deep_technical": "scenario", "behavioral": "behavioral",
            "closing": "behavioral"}.get(phase, "technical")


# ── Follow-up depth control ───────────────────────────────────────────────
def should_force_new_question(followup_depth: int, max_followups: int,
                               comp_status: dict, current_comp: str) -> bool:
    """
    Force transition to new main question if:
    - Exceeded max follow-up depth for this question
    - Competency is saturated
    """
    if followup_depth >= max_followups:
        return True
    if compute_saturation(comp_status, current_comp):
        return True
    return False


# ── Completion check ──────────────────────────────────────────────────────
def should_end_early(comp_status: dict, plan: list, main_q_index: int,
                     min_q: int, consecutive_low: int, early_stop: int) -> Tuple[bool, str]:
    """Hard stop logic based on MAIN question index (not total turns)."""
    if main_q_index < min_q:
        return False, ""

    if consecutive_low >= early_stop:
        return True, f"Interview ended — {consecutive_low} consecutive weak answers."

    tested = [c for c in plan if comp_status.get(c, {}).get("tested")]
    coverage = len(tested) / max(len(plan), 1)

    if coverage >= 0.75 and main_q_index >= min_q + 1:
        avg_conf = sum(comp_status.get(c, {}).get("confidence", 0) for c in tested) / max(len(tested), 1)
        if avg_conf >= 6.5:
            return True, f"Sufficient signal across {len(tested)} competencies."

    return False, ""


# ── Difficulty hint ───────────────────────────────────────────────────────
def get_difficulty_hint(level: str, candidate_profile: dict) -> str:
    strengths = len(candidate_profile.get("strengths", []))
    weaknesses = len(candidate_profile.get("weaknesses", []))
    bluffs = candidate_profile.get("bluff_count", 0)

    if bluffs >= 2:
        return "REDUCE difficulty — candidate appears to be bluffing. Test fundamentals."
    if weaknesses >= 3 and strengths <= 1:
        return "REDUCE difficulty — candidate is struggling. Validate basics first."
    if strengths >= 3 and weaknesses == 0:
        return "INCREASE difficulty — strong candidate. Push with edge cases and architecture."
    return "MAINTAIN current difficulty."


# ── Next competency selection ─────────────────────────────────────────────
def get_next_competency(plan: List[str], comp_status: Dict, current: str) -> str:
    """Pick the next least-tested competency."""
    untested = [c for c in plan if not comp_status.get(c, {}).get("tested") and c != current]
    if untested:
        return untested[0]
    # Fall back to least-confident tested
    tested = sorted(plan, key=lambda c: comp_status.get(c, {}).get("confidence", 0))
    for c in tested:
        if c != current:
            return c
    return plan[0] if plan else "general"
