"""
main.py — Session management and turn orchestration.
Uses main_question_index (not questions_asked) for progress display.
Exposes session_locked to prevent post-completion submissions.
"""
import os, uuid, shutil, time, logging
from typing import Dict, Any, Optional
from config import Config
from graph.state import InterviewState

log = logging.getLogger("main")
_sessions: Dict[str, dict] = {}


def _blank_state(user_id, cv_path, interview_mode, job_description) -> dict:
    return dict(
        user_id=user_id, level="mid", level_reasoning="", level_signals=[],
        role="other", role_label="Professional", role_description="",
        primary_domain="technology", detected_technologies=[],
        job_description=job_description, cv_path=cv_path,
        interview_mode=interview_mode, retriever=None,
        # ── Competency ──
        competency_plan=[], competency_status={},
        current_competency="core_domain_knowledge",
        interview_blueprint=[],
        # ── Question hierarchy ──
        main_question_index=0,
        followup_depth=0,
        max_followups_per_question=2,
        # ── Topic memory ──
        asked_topic_fingerprints=[],
        asked_competencies=[],
        asked_skills=[],
        # ── Profile ──
        unverified_claims=[],
        candidate_profile={"strengths":[],"weaknesses":[],"bluff_count":0,"score_trend":[],"archetype":"unknown"},
        contradiction_log=[],
        # ── Dataset scoring ──
        dataset_entries=[],
        current_llm_score=None,
        current_dataset_score=None,
        current_dataset_result=None,
        interview_phase="warmup", last_transition_note="",
        forced_question_category="auto",
        # ── Current turn ──
        current_question="", current_answer="", current_mode=interview_mode,
        current_question_category="technical", current_competency_tag="",
        current_score=None, current_feedback="", current_improvements=[],
        current_transcription=None, current_soft_skill_notes="",
        current_audio_analysis=None, current_video_analysis=None,
        current_correctness_note="", current_clarity_note="",
        current_depth_note="", current_confidence_note="",
        # ── Tracking ──
        consecutive_followups=0, consecutive_low_scores=0, consecutive_high_scores=0,
        turns=[], questions_asked=0, topics_covered=[], weak_areas=[],
        soft_scores_history=[], audio_scores_history=[], video_scores_history=[],
        # ── Flow control ──
        next_action="new_question", end_reason="",
        interview_complete=False,
        session_locked=False,
        error=None, final_evaluation=None,
        media_file_path=None, original_video_path=None,
        # ── Meta ──
        is_practice_turn=False,
    )


def start_session(cv_path: str, interview_mode: str, job_description: str = "") -> Dict[str, Any]:
    user_id = str(uuid.uuid4())
    saved = _save_file(cv_path)
    state = _blank_state(user_id, saved, interview_mode, job_description)

    from graph.nodes import load_cv, generate_question
    s = {**state, **load_cv(state)}
    if s.get("error"):
        return {"status": "error", "message": s["error"]}
    s = {**s, **generate_question(s)}
    if s.get("error"):
        return {"status": "error", "message": s["error"]}

    s["timestamp"] = time.time()
    s["candidate_name"] = ""
    _sessions[user_id] = s

    briefing = s.get("interview_briefing") or _build_briefing(s)
    return {
        "status":              "success",
        "user_id":             user_id,
        "question":            s.get("current_question", ""),
        "practice_question":   s.get("current_question", ""),  # first Q is practice
        "question_number":     1,
        "main_question_index": 0,
        "level":               s.get("level", "mid"),
        "level_reasoning":     s.get("level_reasoning", ""),
        "level_signals":       s.get("level_signals", []),
        "role":                s.get("role", "other"),
        "role_label":          s.get("role_label", "Professional"),
        "role_description":    s.get("role_description", ""),
        "primary_domain":      s.get("primary_domain", "technology"),
        "detected_technologies": s.get("detected_technologies", []),
        "competency_plan":     s.get("competency_plan", []),
        "interview_phase":     s.get("interview_phase", "warmup"),
        "current_competency":  s.get("current_competency", ""),
        "interview_briefing":  briefing,
    }


def submit_answer(
    user_id: str,
    answer: str = "",
    media_file_path: Optional[str] = None,
    is_practice: bool = False,
) -> Dict[str, Any]:
    if user_id not in _sessions:
        return {"status": "error", "message": "Session not found or expired."}

    state = dict(_sessions[user_id])

    # ── Hard gate: locked session ──────────────────────────────────────────
    if state.get("session_locked") or state.get("interview_complete"):
        return {"status": "error", "message": "Interview already complete. Please start a new session."}

    state["current_answer"] = answer
    state["current_mode"] = state.get("interview_mode", "text")
    state["media_file_path"] = media_file_path
    state["is_practice_turn"] = is_practice

    updated = _run_turn(state)
    _sessions[user_id] = updated

    turns = updated.get("turns", [])
    last = turns[-1] if turns else {}

    # ── Use main_question_index for progress display ───────────────────────
    main_qi = updated.get("main_question_index", 0)
    followup_depth = updated.get("followup_depth", 0)
    total_q = updated.get("session_max_questions",
                len(updated.get("competency_plan", [])) + 2)

    response = {
        "status":              "success",
        "turn":                last.get("turn", 0),
        "main_question_index": main_qi,
        "followup_depth":      followup_depth,
        "transcription":       last.get("transcription"),
        "mode":                state.get("interview_mode", "text"),
        "is_followup":         last.get("is_followup", False),
        "is_practice":         last.get("is_practice", False),
        "interview_complete":  updated.get("interview_complete", False),
        "session_locked":      updated.get("session_locked", False),
        "questions_asked":     updated.get("questions_asked", 0),
        # Progress: next question number to display (main_qi = completed, so next = main_qi+1)
        "question_number":     main_qi + 1,
        "total_questions":     total_q,
        "interview_phase":     updated.get("interview_phase", "technical"),
        "current_competency":  updated.get("current_competency", ""),
    }

    if updated.get("interview_complete"):
        ev = updated.get("final_evaluation") or {}
        log.info(
            f"Interview complete: user={user_id}, "
            f"score={ev.get('overall_score','?')}, "
            f"rec={ev.get('hiring_recommendation','?')}, "
            f"main_q={main_qi}, turns={len(turns)}"
        )
        response["final_evaluation"] = ev
        response["end_reason"] = updated.get("end_reason", "")
        response["all_turns"] = _serialize_turns(turns)
        response["topics_covered"] = updated.get("topics_covered", [])
    else:
        response["next_question"] = updated.get("current_question", "")
        response["next_action"]   = updated.get("next_action", "new_question")

    # Always include dataset scoring breakdown in response
    dr = last.get("current_dataset_result") or updated.get("current_dataset_result") or {}
    response["scoring"] = {
        "final_score":      last.get("score", updated.get("current_score")),
        "llm_score":        last.get("llm_score", updated.get("current_llm_score")),
        "dataset_score":    last.get("dataset_score", updated.get("current_dataset_score")),
        "dataset_available":dr.get("available", False),
        "similarity_pct":   round((dr.get("similarity", 0) or 0) * 100, 1),
        "matched_concepts": last.get("matched_concepts", []),
        "missing_concepts": last.get("missing_concepts", []),
        "scoring_method":   dr.get("scoring_method", "none"),
        "score_explanation":dr.get("score_explanation", ""),
    }

    return response


def _run_turn(state: dict) -> dict:
    from graph.nodes import (
        process_answer, evaluate, record_turn, decide,
        generate_question, generate_followup,
        generate_final_eval, end_interview,
    )
    s = dict(state)
    # ── Process media (transcription, audio/video analysis) ──
    s = {**s, **process_answer(s)}
    # ── If no answer at all after processing, only skip for text mode ──
    mode = s.get("interview_mode", "text")
    if not s.get("current_answer", "").strip() and mode == "text":
        return s
    # For audio/video: if transcription empty, set placeholder so evaluation runs
    if not s.get("current_answer", "").strip() and mode in ("audio", "video"):
        s["current_answer"] = "[No speech detected in recording]"
    # ── Evaluate ──
    eval_result = evaluate(s)
    s = {**s, **eval_result}
    log.info(f"[_run_turn] after evaluate: score={s.get('current_score')}, turns_before={len(s.get('turns', []))}")
    # ── Record turn into history ──
    record_result = record_turn(s)
    s = {**s, **record_result}
    log.info(f"[_run_turn] after record_turn: turns={len(s.get('turns', []))}, is_practice={s.get('is_practice_turn')}")
    # ── Decide next action ──
    s = {**s, **decide(s)}
    action = s.get("next_action", "new_question")
    log.info(f"[_run_turn] action={action}, main_qi={s.get('main_question_index')}, total_fu={s.get('total_followups_asked',0)}")
    # ── Route to next state ──
    if action == "end":
        # Preserve turns before final eval (session_locked must not clear them)
        turns_snapshot = list(s.get("turns", []))
        fe_result = generate_final_eval(s)
        s = {**s, **fe_result}
        # Ensure turns are not lost after final eval
        if not s.get("turns"):
            s["turns"] = turns_snapshot
        log.info(f"[_run_turn] final_eval done: overall={s.get('final_evaluation', {}).get('overall_score','?')}, turns={len(s.get('turns',[]))}")
        s = {**s, **end_interview(s)}
    elif action == "followup":
        s = {**s, **generate_followup(s)}
    else:
        s = {**s, **generate_question(s)}
    return s


def _serialize_turns(turns: list) -> list:
    """Serialize turns for API response — ensures all numeric fields are float-safe."""
    def sf(v, d=0.0):
        try: return float(v) if v is not None else None
        except: return None

    return [
        {
            "turn":              t.get("turn"),
            "main_q_index":      t.get("main_q_index", 0),
            "followup_index":    t.get("followup_index", 0),
            "question":          t.get("question", ""),
            "answer":            t.get("answer", ""),
            "score":             sf(t.get("score"), 0.0),  # 0 for unanswered/hard-ignorance
            "feedback":          t.get("feedback", ""),
            "improvements":      t.get("improvements", []),
            "transcription":     t.get("transcription"),
            "is_followup":       bool(t.get("is_followup")),
            "is_practice":       bool(t.get("is_practice")),
            "competency_tag":    t.get("competency_tag", ""),
            "question_category": t.get("question_category", ""),
            "correctness_note":  t.get("correctness_note", ""),
            "clarity_note":      t.get("clarity_note", ""),
            "depth_note":        t.get("depth_note", ""),
            "confidence_note":   t.get("confidence_note", ""),
            # Dataset scoring
            "llm_score":              sf(t.get("llm_score")),
            "dataset_score":          sf(t.get("dataset_score")),
            "dataset_similarity":     sf(t.get("dataset_similarity")),
            "matched_concepts":       t.get("matched_concepts", []),
            "missing_concepts":       t.get("missing_concepts", []),
            "dataset_scoring_method": t.get("dataset_scoring_method", "none"),
            "score_explanation":      t.get("score_explanation", ""),
            "audio_pace_score":        sf(t.get("audio_pace_score")),
            "audio_fluency_score":     sf(t.get("audio_fluency_score")),
            "audio_confidence_score":  sf(t.get("audio_confidence_score")),
            "audio_engagement_score":  sf(t.get("audio_engagement_score")),
            "audio_hesitation_level":  t.get("audio_hesitation_level", 0),
            "audio_observations":      t.get("audio_observations", []),
            "audio_summary":           t.get("audio_summary", ""),
            "video_score":             sf(t.get("video_score")),
            "video_eye_contact":       sf(t.get("video_eye_contact")),
            "video_expression":        sf(t.get("video_expression")),
            "video_posture":           sf(t.get("video_posture")),
            "video_observations":      t.get("video_observations", []),
            "video_method":            t.get("video_method", "none"),
        }
        for t in turns
    ]


def _build_briefing(s: dict) -> dict:
    level = s.get("level", "mid")
    level_labels = {"junior": "Junior", "mid": "Mid-Level", "senior": "Senior"}
    plan = s.get("competency_plan", [])
    focus_areas = [c.replace("_", " ").title() for c in plan[:5]]
    return {
        "role_label":           s.get("role_label", "Professional"),
        "level_label":          level_labels.get(level, "Mid-Level"),
        "primary_domain":       s.get("primary_domain", "technology"),
        "detected_technologies": s.get("detected_technologies", [])[:6],
        "focus_areas":          focus_areas,
        "estimated_questions":  f"{Config.MIN_QUESTIONS}–{Config.MAX_QUESTIONS}",
        "interview_style":      "Technical + Behavioral + Scenario-Based",
        "role_description":     s.get("role_description", ""),
    }


def _save_file(src: str) -> str:
    os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
    dest = os.path.join(Config.UPLOAD_DIR, os.path.basename(src))
    if os.path.abspath(src) != os.path.abspath(dest):
        shutil.copy2(src, dest)
    return dest


def get_sessions() -> dict:
    return _sessions
