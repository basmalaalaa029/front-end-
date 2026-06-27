"""
question_validator.py — Pre-display question validation.
Runs every check before any question reaches the candidate.
Uses fingerprint-based dedup (fast, no embedding model needed).
"""
import re
import logging
from typing import List, Tuple, Optional

log = logging.getLogger("validator")

# Similarity threshold: questions sharing this fraction of keywords are duplicates
DUPLICATE_THRESHOLD = 0.60


def _fingerprint(text: str) -> set:
    """Extract meaningful keywords from a question for overlap comparison."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9 ]', ' ', text)
    stop = {
        'what', 'would', 'could', 'should', 'your', 'have', 'that', 'this',
        'with', 'from', 'when', 'were', 'been', 'they', 'will', 'about',
        'describe', 'explain', 'tell', 'walk', 'through', 'example', 'give',
        'how', 'does', 'did', 'approach', 'experience', 'used', 'using',
        'please', 'share', 'discuss', 'talk', 'based', 'given', 'think',
        'consider', 'imagine', 'scenario', 'situation', 'time', 'work',
    }
    words = [w for w in text.split() if len(w) > 3 and w not in stop]
    return set(words)


def _similarity(q1: str, q2: str) -> float:
    """Jaccard similarity between two question fingerprints. 0=different, 1=identical."""
    fp1 = _fingerprint(q1)
    fp2 = _fingerprint(q2)
    if not fp1 or not fp2:
        return 0.0
    intersection = len(fp1 & fp2)
    union = len(fp1 | fp2)
    return intersection / union if union > 0 else 0.0


def check_duplicate(question: str, asked_questions: List[str]) -> Tuple[bool, float]:
    """
    Returns (is_duplicate, max_similarity).
    is_duplicate=True means reject this question.
    """
    if not asked_questions:
        return False, 0.0
    max_sim = 0.0
    for prev in asked_questions[-10:]:  # only check recent questions
        sim = _similarity(question, prev)
        if sim > max_sim:
            max_sim = sim
    return max_sim >= DUPLICATE_THRESHOLD, max_sim


def check_phase_match(
    question: str,
    expected_category: str,
    expected_phase: str,
) -> Tuple[bool, str]:
    """
    Returns (is_valid, reason).
    Checks that question content matches the expected phase.
    """
    q_lower = question.lower()

    # Detect question type from content
    is_behavioral = any(kw in q_lower for kw in [
        'team', 'conflict', 'difficult', 'challenge', 'colleague', 'leadership',
        'communicate', 'disagreement', 'deadline', 'mistake', 'learned', 'feedback',
        'tell me about a time', 'describe a situation', 'give an example of'
    ])
    is_technical = any(kw in q_lower for kw in [
        'implement', 'algorithm', 'complexity', 'optimize', 'architecture', 'design',
        'database', 'api', 'code', 'function', 'class', 'model', 'train', 'deploy',
        'debug', 'error', 'performance', 'scale', 'memory', 'runtime', 'framework'
    ])
    is_scenario = any(kw in q_lower for kw in [
        'hypothetically', 'imagine', 'suppose', 'if you were', 'how would you approach',
        'given a scenario', 'you are asked to', 'design a system'
    ])

    if expected_phase == "behavioral" and is_technical and not is_behavioral:
        return False, "Technical question generated for behavioral phase"

    if expected_phase == "warmup" and (is_scenario or (is_technical and not any(
        kw in q_lower for kw in ['project', 'experience', 'background', 'work', 'built', 'created']
    ))):
        return False, "Overly technical question for warmup phase"

    return True, "ok"


def check_topic_overuse(
    competency: str,
    asked_competencies: List[str],
    max_occurrences: int = 3,
) -> Tuple[bool, str]:
    """Returns (is_overused, reason)."""
    count = asked_competencies.count(competency)
    if count >= max_occurrences:
        return True, f"Competency '{competency}' already covered {count}x"
    return False, "ok"


def check_followup_limit(followup_depth: int, max_followups: int) -> bool:
    """Returns True if follow-up limit exceeded."""
    return followup_depth >= max_followups


def validate_question(
    question: str,
    asked_questions: List[str],
    expected_category: str,
    expected_phase: str,
    competency: str,
    asked_competencies: List[str],
    followup_depth: int,
    max_followups: int,
    is_followup: bool = False,
) -> Tuple[bool, str]:
    """
    Full validation pipeline. Returns (is_valid, rejection_reason).
    Call this before displaying any question to the candidate.
    """
    if not question or len(question.strip()) < 15:
        return False, "Question too short or empty"

    # Check 1: Follow-up limit
    if is_followup and check_followup_limit(followup_depth, max_followups):
        return False, f"Follow-up limit ({max_followups}) exceeded"

    # Check 2: Duplicate detection
    is_dup, sim = check_duplicate(question, asked_questions)
    if is_dup:
        return False, f"Too similar to previous question (similarity={sim:.2f})"

    # Check 3: Phase match (soft check — warn but don't reject closing questions)
    if expected_phase not in ("closing",):
        phase_ok, phase_reason = check_phase_match(question, expected_category, expected_phase)
        if not phase_ok:
            log.warning(f"Phase mismatch: {phase_reason}")
            # Warn but don't hard-reject — LLM sometimes produces valid cross-phase Qs

    # Check 4: Topic overuse
    overused, overuse_reason = check_topic_overuse(competency, asked_competencies)
    if overused:
        return False, overuse_reason

    return True, "ok"


def select_best_candidate(
    candidates: List[str],
    asked_questions: List[str],
    expected_category: str,
    expected_phase: str,
    competency: str,
    asked_competencies: List[str],
) -> Optional[str]:
    """
    Given multiple candidate questions, return the most novel one.
    Returns None if all candidates fail validation.
    """
    scored = []
    for q in candidates:
        is_dup, sim = check_duplicate(q, asked_questions)
        if not is_dup and len(q.strip()) >= 15:
            scored.append((1.0 - sim, q))

    if not scored:
        return None

    scored.sort(reverse=True)
    return scored[0][1]
