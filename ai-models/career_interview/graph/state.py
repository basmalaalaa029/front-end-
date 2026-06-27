"""
InterviewState — single source of truth for the entire interview engine.
Structured around question hierarchy (main questions + follow-ups),
explicit phase control, and topic memory for deduplication.
"""
from typing import TypedDict, List, Optional, Any, Dict


class TurnRecord(TypedDict):
    # Identity
    turn: int               # absolute turn number (includes follow-ups)
    main_q_index: int       # which main question (0-based)
    followup_index: int     # 0 = main question, 1+ = follow-up depth
    is_followup: bool

    # Content
    question: str
    question_category: str  # technical | scenario | behavioral | problem_solving | project | followup
    answer: str
    mode: str
    is_practice: bool

    # Scores (None only before evaluation; always float after)
    score: float
    feedback: str
    improvements: List[str]
    transcription: Optional[str]

    # Dimension breakdown
    correctness_note: str
    clarity_note: str
    depth_note: str
    confidence_note: str
    soft_skill_notes: str

    # Competency
    competency_tag: str
    bluff_detected: bool

    # Dataset scoring
    llm_score: Optional[float]
    dataset_score: Optional[float]
    dataset_similarity: Optional[float]
    matched_concepts: List[str]
    missing_concepts: List[str]
    dataset_scoring_method: str
    score_explanation: str

    # Audio analytics
    audio_pace_score: Optional[float]
    audio_fluency_score: Optional[float]
    audio_confidence_score: Optional[float]
    audio_observations: List[str]
    audio_summary: str

    # Video analytics
    video_score: Optional[float]
    video_eye_contact: Optional[float]
    video_expression: Optional[float]
    video_posture: Optional[float]
    video_observations: List[str]
    video_method: str


class CompetencyStatus(TypedDict):
    name: str
    depth: int          # 0=untested, 1=surface, 2=moderate, 3=deep
    confidence: float
    score: float
    tested: bool


class InterviewState(TypedDict):
    # ── Identity ─────────────────────────────────────────────────────────
    user_id: str
    level: str
    level_reasoning: str
    level_signals: List[str]
    job_description: str
    role: str
    role_label: str
    role_description: str
    primary_domain: str
    detected_technologies: list
    cv_path: str
    interview_mode: str
    retriever: Optional[Any]

    # ── Competency planning ───────────────────────────────────────────────
    competency_plan: List[str]
    competency_status: Dict[str, CompetencyStatus]
    current_competency: str
    interview_phase: str    # warmup | technical | deep_technical | behavioral | closing

    # ── Interview blueprint (structured question plan) ────────────────────
    # Populated by load_cv; drives phase/category/competency for each main question
    interview_blueprint: List[Dict]   # List of QuestionSlot dicts

    # ── Question hierarchy (THE FIX for counter bugs) ─────────────────────
    # main_question_index: increments ONLY on new main questions, never on follow-ups
    main_question_index: int
    # followup_depth: resets to 0 on every new main question
    followup_depth: int
    # max follow-ups per main question before forced transition
    max_followups_per_question: int

    # ── Topic memory (prevents repetition) ───────────────────────────────
    # Fingerprints of asked questions for novelty checks
    asked_topic_fingerprints: List[str]
    # Explicit tags covered
    asked_competencies: List[str]
    asked_skills: List[str]

    # ── Current turn ─────────────────────────────────────────────────────
    current_question: str
    current_question_category: str
    current_competency_tag: str
    current_answer: str
    current_mode: str
    current_score: Optional[float]
    current_feedback: str
    current_improvements: List[str]
    current_transcription: Optional[str]
    current_soft_skill_notes: str
    current_audio_analysis: Optional[Dict]
    current_video_analysis: Optional[Dict]

    # Per-question dimensions
    current_correctness_note: str
    current_clarity_note: str
    current_depth_note: str
    current_confidence_note: str

    # ── Candidate intelligence ────────────────────────────────────────────
    unverified_claims: List[str]
    candidate_profile: Dict
    contradiction_log: List[str]
    consecutive_followups: int
    consecutive_low_scores: int
    consecutive_high_scores: int

    # ── History ───────────────────────────────────────────────────────────
    turns: List[TurnRecord]
    questions_asked: int        # total turns (including follow-ups) — for display
    topics_covered: List[str]
    weak_areas: List[str]
    soft_scores_history: List[Dict]
    audio_scores_history: List[Dict]
    video_scores_history: List[Dict]
    last_transition_note: str
    forced_question_category: str

    # ── Flow control ──────────────────────────────────────────────────────
    next_action: str
    end_reason: str
    interview_complete: bool
    session_locked: bool        # once True, no more generation/recording
    error: Optional[str]
    final_evaluation: Optional[Dict]

    # ── Media ─────────────────────────────────────────────────────────────
    media_file_path: Optional[str]
    original_video_path: Optional[str]

    # ── Dataset scoring ───────────────────────────────────────────────────
    dataset_entries: List           # pre-embedded dataset entries (loaded at session start)
    current_llm_score: Optional[float]
    current_dataset_score: Optional[float]
    current_dataset_result: Optional[dict]
