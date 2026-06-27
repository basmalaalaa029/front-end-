"""
interview_planner.py — Blueprint-based interview planner.
Produces EXACTLY 8 main question slots with diverse question styles.
Follow-up budget: max 1 per question, 4 total for the session.
"""
import re
from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class QuestionSlot:
    slot_id: int
    phase: str              # warmup | technical | definition | deep_technical | behavioral | closing
    category: str           # technical | definition | scenario | behavioral | project | comparison | trade_off | debug
    competency: str
    max_followups: int      # hard cap: 1 per slot
    priority: str           # high | medium | low
    jd_term: str = ""       # JD term for definition slots
    filled: bool = False
    question: str = ""
    followup_depth: int = 0
    score: float = 0.0


PHASE_CONFIG = {
    "warmup":         {"category": "project",     "max_followups": 1, "max_slots": 1},
    "technical":      {"category": "technical",   "max_followups": 1, "max_slots": 3},
    "definition":     {"category": "definition",  "max_followups": 1, "max_slots": 1},
    "deep_technical": {"category": "scenario",    "max_followups": 1, "max_slots": 2},
    "behavioral":     {"category": "behavioral",  "max_followups": 1, "max_slots": 1},
    "closing":        {"category": "trade_off",   "max_followups": 1, "max_slots": 1},
}

# 8-question diversity rotation — every question type is different
EIGHT_QUESTION_BLUEPRINT = [
    # (phase, category)
    ("warmup",         "project"),        # Q1: warmup — tell me about your work
    ("technical",      "technical"),      # Q2: direct technical skill
    ("definition",     "definition"),     # Q3: define a key JD term
    ("technical",      "comparison"),     # Q4: compare two approaches
    ("deep_technical", "scenario"),       # Q5: real-world problem scenario
    ("technical",      "trade_off"),      # Q6: trade-off / design decision
    ("behavioral",     "behavioral"),     # Q7: behavioral / soft skill
    ("closing",        "debug"),          # Q8: debug or closing challenge
]

# Rotated so no two consecutive questions are the same type
TECHNICAL_CATEGORY_ROTATION = [
    "technical",
    "comparison",
    "scenario",
    "trade_off",
    "implementation",
    "debug",
    "definition",
]


def extract_jd_terms(job_description: str, max_terms: int = 5) -> List[str]:
    """Extract key technical terms from JD for definition questions."""
    if not job_description:
        return []

    patterns = [
        r'\b(?:RAG|LLM|API|REST|GraphQL|gRPC|CI/?CD|MLOps|DevOps|IaC|ETL|OLAP|OLTP|'
        r'BERT|GPT|CNN|RNN|LSTM|GAN|NLP|CV|RL|SVM|XGBoost|SHAP|'
        r'Kubernetes|Docker|Terraform|Ansible|Kafka|Spark|Airflow|'
        r'PostgreSQL|MongoDB|Redis|Elasticsearch|Cassandra|'
        r'PyTorch|TensorFlow|JAX|scikit.learn|Pandas|NumPy|'
        r'React|Vue|Angular|FastAPI|Django|Flask|Spring|'
        r'AWS|GCP|Azure|S3|Lambda|BigQuery|Vertex)\b',
        r'\b(?:microservices?|event.driven|serverless|containerization|'
        r'vector (?:database|search|embeddings?)|fine.tuning|RAG pipeline|'
        r'attention mechanism|backpropagation|gradient descent|overfitting|'
        r'regularization|ACID|CAP theorem|eventual consistency|idempotency|'
        r'blue.green deployment|canary release|circuit breaker|'
        r'sharding|replication|distributed tracing|observability)\b',
        r'(?:experience (?:with|in)|knowledge of|proficiency in|familiar with)\s+([A-Za-z0-9\+\#\.\-]{3,25})',
    ]

    found = []
    stop = {'the', 'and', 'for', 'with', 'this', 'that', 'you', 'our',
            'will', 'have', 'are', 'years', 'team', 'role', 'work',
            'able', 'good', 'plus', 'must', 'nice', 'also', 'strong'}
    seen = set()

    for pat in patterns:
        for m in re.finditer(pat, job_description, re.IGNORECASE):
            term = (m.group(1) if m.lastindex else m.group(0)).strip()
            if len(term) >= 3 and term.lower() not in stop and term.lower() not in seen:
                seen.add(term.lower())
                found.append(term)

    return found[:max_terms]


def build_interview_blueprint(
    competency_plan: List[str],
    level: str,
    min_q: int = 8,
    max_q: int = 8,
    job_description: str = "",
) -> List[QuestionSlot]:
    """
    Build a FIXED 8-question blueprint with diverse question styles:
    Q1: Project/warmup
    Q2: Direct technical
    Q3: Definition (JD term)
    Q4: Comparison
    Q5: Scenario
    Q6: Trade-off
    Q7: Behavioral
    Q8: Debug/closing
    Each slot allows max 1 follow-up. Session total follow-ups capped at 4.
    """
    slots: List[QuestionSlot] = []
    slot_id = 0

    behavioral_set = {
        "behavioral", "communication", "teamwork", "leadership",
        "conflict_resolution", "collaboration", "learning_mindset",
        "adaptability", "ownership",
    }
    project_set = {"projects", "experience", "background", "journey"}

    warmup_comp        = next((c for c in competency_plan if c in project_set), "background")
    behavioral_comps   = [c for c in competency_plan if c in behavioral_set]
    technical_comps    = [c for c in competency_plan if c not in behavioral_set and c not in project_set]

    jd_terms = extract_jd_terms(job_description)

    # Pick competencies for each slot (cycling if needed)
    def pick_comp(idx, pool, fallback="general"):
        return pool[idx % len(pool)] if pool else fallback

    behav_comp = behavioral_comps[0] if behavioral_comps else "communication"
    closing_comp = technical_comps[-1] if technical_comps else (competency_plan[-1] if competency_plan else "general")

    # Build exactly 8 slots following the blueprint
    blueprint_template = [
        # (phase, category, comp_source, jd_term_slot)
        ("warmup",         "project",      warmup_comp,                False),
        ("technical",      "technical",    pick_comp(0, technical_comps), False),
        ("definition",     "definition",   pick_comp(1, technical_comps), True),
        ("technical",      "comparison",   pick_comp(2, technical_comps), False),
        ("deep_technical", "scenario",     pick_comp(3, technical_comps), False),
        ("technical",      "trade_off",    pick_comp(4, technical_comps), False),
        ("behavioral",     "behavioral",   behav_comp,                 False),
        ("closing",        "debug",        closing_comp,               False),
    ]

    jd_terms_copy = list(jd_terms)

    for i, (phase, category, comp, use_jd) in enumerate(blueprint_template):
        jd_term = ""
        if use_jd and jd_terms_copy:
            jd_term = jd_terms_copy.pop(0)
        priority = "high" if phase in ("technical", "deep_technical") else "medium"
        slots.append(QuestionSlot(
            slot_id=slot_id,
            phase=phase,
            category=category,
            competency=comp,
            max_followups=1,   # max 1 follow-up per question
            priority=priority,
            jd_term=jd_term,
        ))
        slot_id += 1

    return slots  # Always exactly 8


def get_current_slot(blueprint: List[QuestionSlot], main_q_index: int) -> Optional[QuestionSlot]:
    if main_q_index < len(blueprint):
        return blueprint[main_q_index]
    return None


def get_slot_max_followups(blueprint: List[QuestionSlot], main_q_index: int) -> int:
    slot = get_current_slot(blueprint, main_q_index)
    return min(slot.max_followups if slot else 1, 1)  # hard cap at 1


def get_slot_phase(blueprint: List[QuestionSlot], main_q_index: int) -> str:
    slot = get_current_slot(blueprint, main_q_index)
    return slot.phase if slot else "technical"


def get_slot_category(blueprint: List[QuestionSlot], main_q_index: int) -> str:
    slot = get_current_slot(blueprint, main_q_index)
    return slot.category if slot else "technical"


def get_slot_competency(blueprint: List[QuestionSlot], main_q_index: int) -> str:
    slot = get_current_slot(blueprint, main_q_index)
    return slot.competency if slot else "general"


def get_slot_jd_term(blueprint: List[QuestionSlot], main_q_index: int) -> str:
    slot = get_current_slot(blueprint, main_q_index)
    return slot.jd_term if slot else ""


def blueprint_to_summary(blueprint: List[QuestionSlot]) -> str:
    lines = ["Interview Blueprint (8 questions):"]
    for s in blueprint:
        fu = f"+{s.max_followups}fu"
        term = f" [{s.jd_term}]" if s.jd_term else ""
        lines.append(f"  Q{s.slot_id+1} [{s.phase}] {s.competency} ({s.category}){fu}{term}")
    return "\n".join(lines)
