"""
nodes.py — Interview engine nodes.
Architecture: question hierarchy (main_question_index + followup_depth),
topic memory deduplication, session locking on completion,
and None-safe scoring throughout.
"""
import logging, time
from typing import Optional

from chains.llm_factory import get_llm
from chains.question_chain import generate_question_chain
from chains.followup_chain import generate_followup_chain
from chains.evaluation_chain import evaluate_answer_chain
from chains.final_evaluation_chain import final_evaluation_chain
from chains.decision_chain import decide_next_action_chain
from chains.orchestrator import (
    compute_saturation, compute_novelty, is_topic_duplicate,
    make_topic_fingerprint, get_next_phase, get_phase_category,
    should_force_new_question, should_end_early, get_difficulty_hint,
    get_next_competency,
)
from chains.interview_planner import (
    build_interview_blueprint, get_current_slot,
    get_slot_max_followups, get_slot_phase,
    get_slot_category, get_slot_competency,
    blueprint_to_summary,
)
from chains.question_validator import validate_question, select_best_candidate
from chains.dataset_scorer import (
    load_dataset, precompute_dataset_embeddings,
    score_against_dataset, blend_scores,
)
from config import Config
from utils.parser import parse_json_output

log = logging.getLogger("nodes")
MAX_FOLLOWUPS = 2  # per main question — up to 2 follow-ups per question
MAX_SESSION_FOLLOWUPS = 5   # hard ceiling for whole session
MIN_SESSION_FOLLOWUPS = 3   # guaranteed minimum follow-ups per session


def _avg(lst, key):
    vals = [float(item[key]) for item in lst if key in item and item[key] is not None and float(item[key]) > 0]
    return round(sum(vals) / len(vals), 1) if vals else 0.0


def _safe_float(val, default=0.0):
    """Convert to float, return default on None or error."""
    try:
        return float(val) if val is not None else default
    except (TypeError, ValueError):
        return default


def _get_cv_context(retriever, user_id: str, query: str) -> str:
    if not retriever:
        return ""
    try:
        docs = retriever.get_relevant_documents(query)
        return "\n".join(d.page_content for d in docs[:3])
    except Exception:
        return ""


def _build_coverage_str(plan, comp_status):
    lines = []
    for c in plan:
        s = comp_status.get(c, {})
        tested = s.get("tested", False)
        score = s.get("score", 0) if tested else "—"
        depth = s.get("depth", 0)
        lines.append(f"  {c}: {'✓' if tested else '○'} depth={depth} score={score}")
    return "\n".join(lines) or "No competencies planned."


# ── 1. Load CV ────────────────────────────────────────────────────────────
def load_cv(state):
    # Use the actual APIs that exist in this codebase
    from rag.cv_loader import CVLoader
    from rag.vector_store import get_vector_store, save_vector_store
    from rag.cv_summary_cache import build_summary_from_docs, set_summary, get_summary
    from chains.role_detection_chain import detect_role_chain
    from chains.level_detection_chain import detect_level_chain
    from chains.competency_planner import get_competency_plan

    cv_path = state.get("cv_path", "")
    user_id = state.get("user_id", "")
    job_desc = state.get("job_description", "")
    log.info(f"load_cv: user={user_id}")

    try:
        # ── Load and chunk CV ──────────────────────────────────────────
        loader = CVLoader(cv_path)
        chunks = loader.load_and_split()

        # ── Build vector store and retriever ──────────────────────────
        vs = get_vector_store(user_id, documents=chunks)
        save_vector_store(vs, user_id)
        retriever = vs.as_retriever(search_kwargs={"k": 4})

        # ── CV summary ────────────────────────────────────────────────
        cached = get_summary(user_id)
        if not cached:
            summary_text = build_summary_from_docs(chunks)
            set_summary(user_id, summary_text)

        # ── Role detection ────────────────────────────────────────────
        role_raw = detect_role_chain(retriever).invoke({
            "job_description": job_desc or "Not provided"
        })
        role_info = _safe_parse(role_raw, {
            "role": "software_engineer",
            "role_label": "Software Engineer",
            "role_description": "",
            "primary_domain": "technology",
            "detected_technologies": [],
        })

        role       = role_info.get("role", "software_engineer")
        role_label = role_info.get("role_label", "Software Engineer")

        # ── Level detection ───────────────────────────────────────────
        level_raw = detect_level_chain(retriever).invoke({
            "job_description": job_desc or "Not provided"
        })
        level_info = _safe_parse(level_raw, {
            "level": "mid",
            "reasoning": "",
            "signals": [],
            "confidence": 7,
        })

        level = level_info.get("level", "mid")
        if level not in ("junior", "mid", "senior"):
            level = "mid"

        # ── Competency plan ───────────────────────────────────────────
        techs = role_info.get("detected_technologies", [])
        comp_plan = get_competency_plan(role, detected_technologies=techs)
        if not comp_plan:
            comp_plan = ["core_domain_knowledge", "problem_solving",
                         "communication", "behavioral"]

        estimated_q = max(Config.MIN_QUESTIONS,
                          min(len(comp_plan) + 2, Config.MAX_QUESTIONS))

        # ── Interview blueprint ───────────────────────────────────────────
        blueprint = build_interview_blueprint(
            comp_plan, level,
            min_q=Config.MIN_QUESTIONS,
            max_q=Config.MAX_QUESTIONS,
            job_description=state.get("job_description", ""),
        )
        blueprint_dicts = [
            {"slot_id": s.slot_id, "phase": s.phase, "category": s.category,
             "competency": s.competency, "max_followups": s.max_followups,
             "priority": s.priority, "filled": s.filled, "jd_term": s.jd_term}
            for s in blueprint
        ]
        log.info(blueprint_to_summary(blueprint))

        # ── Dataset loading & embedding pre-computation ───────────────────
        ollama_url = getattr(Config, "OLLAMA_BASE_URL", "http://localhost:11434")
        try:
            raw_dataset = load_dataset(role, user_id=state.get("user_id", ""))
            dataset_entries = precompute_dataset_embeddings(raw_dataset, ollama_url)
            log.info(f"Dataset ready: {len(dataset_entries)} entries for role={role}")
        except Exception as _de:
            log.warning(f"Dataset loading failed: {_de} — scoring will use LLM only")
            dataset_entries = []

        estimated_q = len(blueprint)

        interview_briefing = {
            "role_label": role_label,
            "primary_domain": role_info.get("primary_domain", "Technology"),
            "detected_technologies": techs,
            "focus_areas": [c.replace("_", " ").title() for c in comp_plan[:4]],
            "estimated_questions": str(estimated_q),
                "session_max_questions": estimated_q,
            "seniority_confidence": level_info.get("confidence", 7),
        }

        return {
            "level":              level,
            "level_reasoning":    level_info.get("reasoning", ""),
            "level_signals":      level_info.get("signals", []),
            "role":               role,
            "role_label":         role_label,
            "role_description":   role_info.get("role_description", ""),
            "primary_domain":     role_info.get("primary_domain", "technology"),
            "detected_technologies": techs,
            "retriever":          retriever,
            "competency_plan":    comp_plan,
            "competency_status":  {},
            "current_competency": comp_plan[0] if comp_plan else "general",
            "interview_blueprint": blueprint_dicts,
            "unverified_claims":  [],
            "candidate_profile":  {"strengths":[], "weaknesses":[], "bluff_count":0,
                                    "score_trend":[], "archetype":"unknown"},
            "contradiction_log":  [],
            "interview_phase":    "warmup",
            "main_question_index": 0,
            "followup_depth":     0,
            "max_followups_per_question": MAX_FOLLOWUPS,
            "asked_topic_fingerprints": [],
            "asked_competencies": [],
            "asked_skills":       [],
            "turns":              [],
            "questions_asked":    0,
            "topics_covered":     [],
            "weak_areas":         [],
            "soft_scores_history":  [],
            "audio_scores_history": [],
            "video_scores_history": [],
            "consecutive_followups": 0,
            "consecutive_low_scores": 0,
            "consecutive_high_scores": 0,
            "next_action":        "new_question",
            "end_reason":         "",
            "interview_complete": False,
            "session_locked":     False,
            "last_transition_note": "",
            "forced_question_category": "auto",
            "interview_briefing": interview_briefing,
            "dataset_entries":    dataset_entries,
            "error":              None,
        }
    except Exception as e:
        log.error(f"load_cv error: {e}", exc_info=True)
        return {"error": str(e), "session_locked": False}


def _safe_parse(raw: str, defaults: dict) -> dict:
    """Parse LLM JSON output safely, falling back to defaults."""
    try:
        result = parse_json_output(raw)
        return {**defaults, **result}
    except Exception:
        return defaults


# ── 2. Generate Question ──────────────────────────────────────────────────
def generate_question(state):
    """
    Generate main question using blueprint slot for phase/category/competency.
    Validates with question_validator before accepting. Retries up to 3x.
    """
    if state.get("session_locked"):
        return {"error": "Session locked"}

    plan = state.get("competency_plan", [])
    main_q_index = state.get("main_question_index", 0)
    level = state.get("level", "mid")
    role_label = state.get("role_label", "Professional")
    fingerprints = list(state.get("asked_topic_fingerprints", []))
    topics = list(state.get("topics_covered", []))
    asked_questions = [t.get("question", "") for t in state.get("turns", [])]
    asked_competencies = list(state.get("asked_competencies", []))
    profile = state.get("candidate_profile", {})

    # ── Read phase/category/competency from blueprint slot ────────────────
    blueprint_dicts = state.get("interview_blueprint", [])
    if blueprint_dicts and main_q_index < len(blueprint_dicts):
        slot = blueprint_dicts[main_q_index]
        phase        = slot.get("phase", "technical")
        category     = slot.get("category", "technical")
        current_comp = slot.get("competency", plan[0] if plan else "general")
        max_fu       = slot.get("max_followups", MAX_FOLLOWUPS)
        jd_term      = slot.get("jd_term", "")
    else:
        current_comp = state.get("current_competency", plan[0] if plan else "general")
        phase        = state.get("interview_phase", "technical")
        # Rotate category when falling back so questions are not all "scenario"
        _rotation = ["technical", "definition", "scenario", "comparison",
                     "implementation", "trade_off", "debug"]
        category = _rotation[main_q_index % len(_rotation)]
        if phase == "behavioral": category = "behavioral"
        if phase == "warmup":     category = "project"
        max_fu   = MAX_FOLLOWUPS
        jd_term  = ""

    # Respect forced category override from decide() node
    forced_cat = state.get("forced_question_category", "auto")
    if forced_cat and forced_cat != "auto":
        category = forced_cat
    diff_hint = get_difficulty_hint(level, profile)
    asked_str = ", ".join(fingerprints[-20:]) or "none"
    tc = state.get("topics_covered", [])
    # Extract key concepts from topics to prevent semantic repetition
    import re as _re
    key_concepts = []
    for t in tc[-15:]:
        # Extract nouns/concepts from topic fingerprints
        concepts = _re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|(?:RAG|LLM|API|ML|AI|NLP|CNN|RNN|BERT|GPT)', t)
        key_concepts.extend(concepts[:2])
    asked_concepts_str = "; ".join(dict.fromkeys(key_concepts[:20])) if key_concepts else "; ".join(tc[-10:]) if tc else "none"

    # ── Domain lock: prevent off-domain questions ─────────────────────────
    primary = state.get("primary_domain", "")
    detected_techs = state.get("detected_technologies", [])
    jd_text = state.get("job_description", "")
    web_terms = ("django", "flask", "rails", "spring", "laravel", "express", "web framework")
    jd_mentions_web = any(t in jd_text.lower() for t in web_terms)
    if primary and primary.lower() not in ("web", "web_development", "backend", "fullstack") and not jd_mentions_web:
        domain_lock_str = (
            f"DOMAIN LOCK — {primary.upper()} ROLE: Do NOT ask about web frameworks "
            f"(Django, Flask, Rails) — these appear as background in the CV but are NOT relevant to this role. "
            f"Focus exclusively on: {', '.join(detected_techs[:8]) if detected_techs else primary}."
        )
    else:
        domain_lock_str = state.get("domain_lock_instruction", "")

    # ── Try up to 3× to get a valid novel question ────────────────────────
    for attempt in range(3):
        try:
            raw = generate_question_chain(state["retriever"]).invoke({
                "role_label":            role_label,
                "role_description":      state.get("role_description", ""),
                "primary_domain":        state.get("primary_domain", "technology"),
                "detected_technologies": ", ".join(state.get("detected_technologies", [])) or "not specified",
                "level":                 level,
                "current_competency":    current_comp,
                "question_category":     category,
                "interview_phase":       phase,
                "topics_covered":        asked_str,
                "difficulty_hint":       diff_hint,
                "candidate_strengths":   ", ".join(profile.get("strengths", [])) or "none observed",
                "candidate_weaknesses":  ", ".join(profile.get("weaknesses", [])) or "none observed",
                "unverified_claims":     ", ".join(state.get("unverified_claims", [])[-2:]) or "none",
                "last_transition_note":  state.get("last_transition_note", ""),
                "job_description":       state.get("job_description", "") or "Not provided",
                "role_guidelines":       state.get("role_guidelines", ""),
                "jd_term":               jd_term,
                "domain_lock":           domain_lock_str,
            })
            q = raw.strip().strip('"').strip("'")
            # Strip preamble the LLM sometimes adds
            for _pre in ["Here's a question:", "Question:", "Here is a question:", "Interview question:", "Here's your question:"]:
                if q.lower().startswith(_pre.lower()):
                    q = q[len(_pre):].strip()
            if not q or len(q) < 15:
                continue

            # ── Enforce question format — never let a statement through ──────
            if not q.rstrip().endswith('?'):
                # Common statement starters → convert to question form
                _stmt_map = [
                    ("Tell me about your experience with ", "Can you walk me through your experience with "),
                    ("Tell me about ", "Can you tell me about "),
                    ("Describe your experience with ", "How would you describe your experience with "),
                    ("Describe ", "How would you describe "),
                    ("Explain ", "Can you explain "),
                    ("Walk me through ", "Can you walk me through "),
                    ("Discuss ", "Can you discuss "),
                ]
                _converted = False
                for _stmt, _repl in _stmt_map:
                    if q.startswith(_stmt):
                        q = _repl + q[len(_stmt):]
                        if not q.endswith('?'):
                            q = q.rstrip('.') + '?'
                        _converted = True
                        break
                if not _converted:
                    # Just append a question mark if it ends like a sentence
                    q = q.rstrip('.') + '?'


            # Python-level semantic dedup — prevent asking same concept twice
            q_words = set(q.lower().split()[:10])
            for prev_topic in (topics or []):
                prev_words = set(prev_topic.lower().split()[:10])
                overlap = len(q_words & prev_words)
                if overlap >= 4 and attempt < 2:
                    log.warning(f"Semantic duplicate detected ({overlap} words overlap), retrying")
                    q = None
                    break
            if q is None:
                continue

            # Run validator
            is_valid, reason = validate_question(
                question=q, asked_questions=asked_questions,
                expected_category=category, expected_phase=phase,
                competency=current_comp, asked_competencies=asked_competencies,
                followup_depth=0, max_followups=max_fu, is_followup=False,
            )
            if not is_valid:
                log.info(f"Q rejected attempt {attempt+1}: {reason}")
                continue

            # Accept
            fp = make_topic_fingerprint(q)
            if fp not in fingerprints: fingerprints.append(fp)
            # Store a clean, human-readable topic label (not the full question text)
            tag = current_comp.replace("_", " ").title() if current_comp else q[:40].rstrip("?").strip()
            if tag not in topics: topics.append(tag)
            if current_comp not in asked_competencies: asked_competencies.append(current_comp)

            log.info(f"Q{main_q_index+1} [{phase}/{category}] {current_comp}: {q[:60]}...")
            return {
                "current_question": q, "current_question_category": category,
                "current_competency_tag": current_comp, "current_competency": current_comp,
                "interview_phase": phase, "current_answer": "", "current_score": None,
                "current_feedback": "", "current_improvements": [],
                "current_transcription": None, "current_soft_skill_notes": "",
                "current_audio_analysis": None, "current_video_analysis": None,
                "consecutive_followups": 0, "followup_depth": 0,
                "current_correctness_note": "", "current_clarity_note": "",
                "current_depth_note": "", "current_confidence_note": "",
                "topics_covered": topics, "asked_topic_fingerprints": fingerprints,
                "asked_competencies": asked_competencies, "error": None,
            }
        except Exception as e:
            log.warning(f"generate_question attempt {attempt+1}: {e}")

    # ── Failsafe fallback — drive from JD, never generic ─────────────────
    jd_text  = state.get("job_description", "").strip()
    role_label = state.get("role_label", "Professional")
    level_label = state.get("level", "mid")
    asked_str_fb = ", ".join(topics[-10:]) if topics else "none"

    if jd_text:
        try:
            from chains.llm_factory import get_llm as _get_llm
            _fb_llm = _get_llm(temperature=0.5, max_tokens=120, tier="fast")
            _fb_prompt = (
                f"You are a technical interviewer for a {role_label} role ({level_label} level).\n"
                f"Job description:\n{jd_text[:1200]}\n\n"
                f"Topics already covered (DO NOT repeat): {asked_str_fb}\n\n"
                f"Write ONE specific interview question drawn directly from a requirement in the job description above.\n"
                f"The question must end with a question mark. Output only the question, nothing else."
            )
            _fb_raw = _fb_llm.invoke(_fb_prompt).content.strip().strip('"').strip("'")
            if _fb_raw and len(_fb_raw) > 15 and "?" in _fb_raw:
                fallback = _fb_raw
            else:
                raise ValueError("bad jd fallback output")
        except Exception as _fe:
            log.warning(f"JD fallback LLM failed: {_fe}")
            # Last-resort: pull a concrete requirement phrase from the JD
            import re as _re
            _reqs = _re.findall(r'(?:experience|knowledge|proficiency|familiarity) (?:with|in) ([A-Za-z0-9\+\#\. ]{3,40}?)(?:[,\.\n]|$)', jd_text)
            if _reqs:
                _req = _reqs[0].strip()
                fallback = f"The role requires {_req} — can you describe a specific situation where you applied that?"
            else:
                fallback = f"Based on this role's requirements, what's the most relevant technical project you've worked on and what was your contribution?"
    else:
        # No JD at all — use competency if it's meaningful, otherwise role-based
        comp_label = current_comp.replace('_', ' ').strip()
        _generic = {"general","background","candidate_background","core_domain_knowledge","core knowledge","experience","intro","other"}
        if comp_label.lower() not in _generic and len(comp_label) > 4:
            fallback = f"What's the most challenging problem you've encountered with {comp_label}, and how did you resolve it?"
        else:
            fallback = f"What's the most technically complex project you've worked on as a {role_label}, and what was your specific role?"

    log.warning(f"Using fallback question for {current_comp}")
    fp = make_topic_fingerprint(fallback)
    if fp not in fingerprints: fingerprints.append(fp)
    if current_comp not in asked_competencies: asked_competencies.append(current_comp)
    return {
        "current_question": fallback, "current_question_category": category,
        "current_competency_tag": current_comp, "current_competency": current_comp,
        "interview_phase": phase, "current_answer": "", "current_score": None,
        "current_feedback": "", "current_improvements": [],
        "current_transcription": None, "current_soft_skill_notes": "",
        "current_audio_analysis": None, "current_video_analysis": None,
        "consecutive_followups": 0, "followup_depth": 0,
        "current_correctness_note": "", "current_clarity_note": "",
        "current_depth_note": "", "current_confidence_note": "",
        "topics_covered": topics, "asked_topic_fingerprints": fingerprints,
        "asked_competencies": asked_competencies, "error": None,
    }


# ── 3. Process Answer (transcription + audio/video) ───────────────────────
def process_answer(state):
    if state.get("session_locked"):
        return {}
    mode = state.get("interview_mode", state.get("current_mode", "text"))
    media_path = state.get("media_file_path")
    updates = {"current_mode": mode}

    if mode == "audio" and media_path:
        try:
            from audio.speech_to_text import transcribe_audio
            from audio.audio_analysis import analyse_audio as analyze_audio, interpret_audio_metrics
            from audio.speech_to_text import correct_technical_terms
            transcript_raw = transcribe_audio(media_path)
            transcript = transcript_raw.strip() if isinstance(transcript_raw, str) else (transcript_raw.get("text","") if isinstance(transcript_raw, dict) else "")
            # Correct technical term mishearings using CV/JD context
            if transcript:
                cv_context = (state.get("cv_text", "") or "") + " " + (state.get("job_description", "") or "")
                competencies = " ".join(state.get("competency_plan", []) or [])
                transcript = correct_technical_terms(transcript, cv_context + " " + competencies)
            updates["current_answer"] = transcript if transcript else "[Audio received — no speech detected]"
            updates["current_transcription"] = transcript
            try:
                transcript_for_analysis = updates.get("current_answer", state.get("current_answer",""))
                raw_aa = analyze_audio(media_path, transcript_for_analysis)
                aa = interpret_audio_metrics(raw_aa)
                aa["raw"] = raw_aa
                updates["current_audio_analysis"] = aa
            except Exception as ae:
                log.warning(f"Audio analysis failed: {ae}")
        except Exception as e:
            log.warning(f"Audio processing error: {e}")

    elif mode == "video" and media_path:
        # ── Non-verbal video analysis (eye contact / expression / posture) ──
        # Runs independently of audio: it only needs the recorded frames, so a
        # missing/failed audio track (e.g. denied mic permission, muted input,
        # or an ffmpeg failure) must NEVER prevent this from running.
        try:
            from video.video_analysis import analyse_video as analyze_video_nonverbal, interpret_video_metrics
            import threading, tempfile, subprocess as _sp, os as _os

            # Pre-transcode browser WebM → MP4 so OpenCV can seek/decode reliably.
            # Browser MediaRecorder WebM blobs often lack a finalized Cues index,
            # which causes OpenCV's VideoCapture to report frame_count=0 or garbage.
            # ffmpeg remux fixes this without re-encoding (fast, lossless copy).
            _analysis_path = media_path
            _tmp_mp4 = None
            try:
                _tmp_mp4_f = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
                _tmp_mp4_f.close()
                _tmp_mp4 = _tmp_mp4_f.name
                # Re-encode VP8/VP9 → H.264: VP8 codec is not valid in MP4 container,
                # so -c:v copy fails. Always re-encode with ultrafast preset (fast, small).
                r = _sp.run(
                    ["ffmpeg", "-y", "-loglevel", "error",
                     "-i", media_path,
                     "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
                     "-c:a", "aac", "-b:a", "64k",
                     "-movflags", "+faststart",
                     _tmp_mp4],
                    capture_output=True, text=True, timeout=60
                )
                if r.returncode == 0 and _os.path.exists(_tmp_mp4) and _os.path.getsize(_tmp_mp4) > 1000:
                    _analysis_path = _tmp_mp4
                    log.info(f"Pre-transcoded WebM VP8 → MP4 H.264 for video analysis: {_tmp_mp4}")
                else:
                    log.warning(f"WebM→MP4 transcode failed (rc={r.returncode}), using original WebM: {r.stderr.strip()[:200]}")
                    if _os.path.exists(_tmp_mp4): _os.remove(_tmp_mp4)
                    _tmp_mp4 = None
            except Exception as _te:
                log.warning(f"WebM pre-transcode skipped: {_te}")
                if _tmp_mp4 and _os.path.exists(_tmp_mp4):
                    try: _os.remove(_tmp_mp4)
                    except: pass
                _tmp_mp4 = None

            vr = [None]
            def do_video():
                try:
                    vr[0] = analyze_video_nonverbal(_analysis_path)
                except Exception as ve:
                    log.warning(f"Video non-verbal analysis failed: {ve}")
                    vr[0] = {"overall_score": None, "analysis_available": False}
                finally:
                    # Clean up temp MP4 after analysis
                    if _tmp_mp4 and _os.path.exists(_tmp_mp4):
                        try: _os.remove(_tmp_mp4)
                        except: pass
            t = threading.Thread(target=do_video); t.start(); t.join(timeout=60)
            if vr[0] is None:
                vr[0] = {"overall_score": None, "analysis_available": False, "method": "timeout"}
                if _tmp_mp4 and _os.path.exists(_tmp_mp4):
                    try: _os.remove(_tmp_mp4)
                    except: pass
            # Normalise keys: analyse_video returns "score", but the rest of the
            # pipeline expects "overall_score". Call interpret_video_metrics to map them.
            raw_va = vr[0]
            try:
                va_interpreted = interpret_video_metrics(raw_va)
            except Exception:
                # Fallback: manually alias "score" → "overall_score"
                va_interpreted = dict(raw_va)
                if "overall_score" not in va_interpreted:
                    va_interpreted["overall_score"] = raw_va.get("score")
            updates["current_video_analysis"] = va_interpreted
        except Exception as e:
            log.warning(f"Video frame processing error: {e}", exc_info=True)

        # ── Audio track: transcription + delivery (pace/fluency/etc) ────────
        # Independent try/except — if there's no usable audio track, the
        # candidate still gets credit for the video-only metrics above.
        try:
            from audio.speech_to_text import transcribe_audio, correct_technical_terms
            from audio.audio_analysis import analyse_audio as analyze_audio, interpret_audio_metrics
            from video.video_processor import extract_audio_from_video
            audio_path = extract_audio_from_video(media_path)
            transcript_raw = transcribe_audio(audio_path)
            transcript = transcript_raw.strip() if isinstance(transcript_raw, str) else (transcript_raw.get("text","") if isinstance(transcript_raw, dict) else "")
            if transcript:
                cv_context = (state.get("cv_text", "") or "") + " " + (state.get("job_description", "") or "")
                competencies = " ".join(state.get("competency_plan", []) or [])
                transcript = correct_technical_terms(transcript, cv_context + " " + competencies)
            updates["current_answer"] = transcript if transcript else "[Video received — no speech detected]"
            updates["current_transcription"] = transcript
            try:
                transcript_for_va = updates.get("current_answer", state.get("current_answer",""))
                raw_vaa = analyze_audio(audio_path, transcript_for_va)
                vaa = interpret_audio_metrics(raw_vaa)
                vaa["raw"] = raw_vaa
                updates["current_audio_analysis"] = vaa
            except Exception as ae:
                log.warning(f"Video audio analysis failed: {ae}")
        except Exception as e:
            log.warning(f"Video audio extraction/transcription failed: {e}", exc_info=True)
            # No usable audio track — still let the candidate get scored on
            # whatever spoken answer (if any) was captured earlier, otherwise
            # fall back to a placeholder so evaluation can still run.
            updates.setdefault("current_answer", state.get("current_answer", "") or "[Video received — no audio track detected]")
            updates.setdefault("current_transcription", state.get("current_transcription", ""))

    return updates


# ── 4. Evaluate ───────────────────────────────────────────────────────────

# Uncertainty signals for pre-LLM score capping
_HARD_CAP_PHRASES = [
    "i don't know", "i do not know", "i have no idea", "no idea",
    "i'm not sure", "i am not sure", "i never learned", "i have no experience",
    "i haven't used", "i have not used", "i can't answer", "i cannot answer",
    "never heard of", "not familiar with", "no knowledge of",
    # Additional honest ignorance patterns
    "i have not faced", "i haven't faced", "i have never faced",
    "i don't have experience", "i do not have experience",
    "i have not done", "i haven't done", "i have never done",
    "i have not worked", "i haven't worked", "i have never worked",
    "i have not dealt", "i haven't dealt",
    "i have no knowledge", "i have no background",
    "i am not familiar", "i'm not familiar",
    "i don't have knowledge", "i do not have knowledge",
    "i don't understand", "i do not understand this",
    "i have not encountered", "i haven't encountered",
    "i cannot answer this", "i can not answer this",
    "i don't know the answer", "i do not know the answer",
]
_SOFT_CAP_PHRASES = [
    "i think maybe", "i'm not certain", "i am not certain",
    "i would probably just google", "i'm not sure but", "not really sure",
    "i have limited experience", "i've never done this before",
    "i'm guessing", "i am guessing",
]
_HONEST_GAP_PHRASES = [
    "haven't used", "but i would approach", "but i would learn",
    "transferable", "similar to", "i would research", "based on my knowledge of",
]


def _detect_uncertainty(answer: str):
    """
    Returns (uncertainty_type, score_cap).
    uncertainty_type: none | honest_gap | soft_ignorance | hard_ignorance
    score_cap: None = no cap, float = maximum allowed technical score
    """
    al = answer.lower().strip()

    # Hard cap: blank or near-blank
    if len(al.split()) < 5:
        return "hard_ignorance", 1.0

    # Check for honest gap (no cap — they tried)
    has_honest = any(p in al for p in _HONEST_GAP_PHRASES)
    has_hard = any(p in al for p in _HARD_CAP_PHRASES)
    has_soft = any(p in al for p in _SOFT_CAP_PHRASES)

    if has_hard and not has_honest:
        return "hard_ignorance", 2.0
    if has_soft and not has_honest:
        return "soft_ignorance", 4.0
    if has_hard and has_honest:
        # "I don't know X but I would approach it by..." — honest gap
        return "honest_gap", None

    return "none", None


def _weighted_score(technical: float, soft_scores: dict, question_category: str) -> float:
    """
    Compute final score. Technical score is the primary signal.
    Soft skills slightly adjust but never tank a correct answer.
    """
    comm = _safe_float(soft_scores.get("communication"), 5.0)
    prob = _safe_float(soft_scores.get("problem_solving"), 5.0)
    hon  = _safe_float(soft_scores.get("honesty"), 5.0)

    if question_category in ("technical", "scenario", "problem_solving"):
        # Technical-heavy: 85% technical, soft skills as minor adjustment (never more than ±0.5)
        soft_adj = (prob - 5) * 0.05 + (comm - 5) * 0.03  # max ±0.5 adjustment
        weighted = technical * 0.85 + prob * 0.10 + comm * 0.05
        # Clamp so soft skills don't tank a technically correct answer
        weighted = max(weighted, technical * 0.80)
    elif question_category == "behavioral":
        # Behavioral: 25% technical, 35% communication, 30% problem-solving, 10% honesty
        weighted = technical * 0.25 + comm * 0.35 + prob * 0.30 + hon * 0.10
    else:
        # Default / project / followup: 45% technical, 30% communication, 20% problem-solving, 5% honesty
        weighted = technical * 0.45 + comm * 0.30 + prob * 0.20 + hon * 0.05

    return round(min(max(weighted, 0.0), 10.0), 1)


def evaluate(state):
    """Score the current answer. NEVER returns None for current_score."""
    if state.get("session_locked"):
        return {"current_score": 5.0}

    answer = state.get("current_answer", "").strip()
    # Detect placeholder/empty answers (no actual speech or text)
    _placeholder_markers = ["[no speech detected", "[audio received", "[video received",
                             "no speech detected", "transcription unavailable", "[no speech"]
    _is_placeholder = any(m in answer.lower() for m in _placeholder_markers) or len(answer) < 8
    _empty_answer = not answer or _is_placeholder

    if _empty_answer:
        profile = dict(state.get("candidate_profile", {}))
        comp_status_empty = dict(state.get("competency_status", {}))
        comp_tag_e = state.get("current_competency_tag", "")
        if comp_tag_e and not state.get("is_practice_turn"):
            cs_empty = dict(comp_status_empty.get(comp_tag_e, {}))
            prev_e = list(cs_empty.get("all_scores", []))
            prev_e.append(0.0)
            cs_empty["tested"] = True
            cs_empty["score"] = round(sum(prev_e)/len(prev_e), 1)
            cs_empty["all_scores"] = prev_e
            comp_status_empty[comp_tag_e] = cs_empty
        return {
            "current_score": 0.0,
            "current_soft_scores": {"communication":0,"confidence":0,"problem_solving":0,"honesty":0},
            "competency_status": comp_status_empty,
            "current_feedback": "No answer was detected — the recording was empty or silent.",
            "current_improvements": [
                "Ensure your microphone is working before starting.",
                "Speak clearly and at a natural pace during recording.",
            ],
            "current_soft_skill_notes": "No answer provided.",
            "current_correctness_note": "No answer.",
            "current_clarity_note": "No answer.",
            "current_depth_note": "No answer.",
            "current_confidence_note": "No answer.",
            "soft_scores_history": list(state.get("soft_scores_history", [])),
            "audio_scores_history": list(state.get("audio_scores_history", [])),
            "video_scores_history": list(state.get("video_scores_history", [])),
            "consecutive_low_scores": state.get("consecutive_low_scores", 0) + 1,
            "consecutive_high_scores": 0,
            "candidate_profile": profile,
            "error": None,
        }

    try:
        # ── Pre-LLM uncertainty detection ────────────────────────────────
        uncertainty_type, score_cap = _detect_uncertainty(answer)
        q_category = state.get("current_question_category", "technical")

        context = _get_cv_context(state.get("retriever"), state.get("user_id", ""),
                                   state.get("current_question", ""))

        # If hard ignorance ("I don't know") → score 0, skip LLM entirely
        if uncertainty_type == "hard_ignorance" and score_cap is not None and score_cap <= 2.0:
            log.info(f"Hard ignorance detected — scoring 0")
            final_score = 0.0
            soft = {"communication": 2.0, "confidence": 1.0, "problem_solving": 1.0, "honesty": 8.0}
            sh = list(state.get("soft_scores_history", []))
            if not state.get("is_practice_turn"):
                sh.append(soft)
            cls = state.get("consecutive_low_scores", 0) + 1
            profile = dict(state.get("candidate_profile", {}))
            weaknesses = list(profile.get("weaknesses", []))
            comp = state.get("current_competency_tag", "general")
            if comp not in weaknesses: weaknesses.append(comp)
            profile["weaknesses"] = weaknesses[:6]
            score_trend = [float(s) for s in profile.get("score_trend", []) if s is not None]
            score_trend.append(final_score)
            profile["score_trend"] = score_trend[-8:]
            # Update competency status
            comp_status_ign = dict(state.get("competency_status", {}))
            if comp and not state.get("is_practice_turn"):
                cs_ign = dict(comp_status_ign.get(comp, {}))
                prev_ign = list(cs_ign.get("all_scores", []))
                prev_ign.append(0.0)
                cs_ign["tested"] = True
                cs_ign["score"] = round(sum(prev_ign)/len(prev_ign), 1)
                cs_ign["all_scores"] = prev_ign
                comp_status_ign[comp] = cs_ign
            return {
                "current_score": final_score,
                "current_feedback": f"The candidate stated they do not know this topic. No technical content was demonstrated on {comp.replace('_',' ')}.",
                "current_improvements": [
                    f"Review the fundamentals of {comp.replace('_',' ')} — focus on core concepts you can explain clearly.",
                    "When uncertain, try to describe related concepts you do know and how you would approach learning this topic.",
                ],
                "current_soft_skill_notes": "Candidate admitted lack of knowledge — honesty noted but no technical depth shown.",
                "current_correctness_note": "No technical content provided.",
                "current_clarity_note": "N/A — no substantive answer given.",
                "current_depth_note": "No depth — candidate stated lack of knowledge.",
                "current_confidence_note": "Low confidence — admitted ignorance.",
                "soft_scores_history": sh,
                "competency_status": comp_status_ign,
                "consecutive_low_scores": cls,
                "consecutive_high_scores": 0,
                "candidate_profile": profile,
                "error": None,
            }

        raw = evaluate_answer_chain(state["retriever"]).invoke({
            "question":          state.get("current_question", ""),
            "answer":            answer,
            "role_label":        state.get("role_label", "Professional"),
            "level":             state.get("level", "mid"),
            "question_category": q_category,
            "context":           context[:500],
            "job_description":   state.get("job_description", ""),
        })
        log.info(f"[eval] raw LLM output ({len(raw)} chars): {raw[:200]}")
        parsed = parse_json_output(raw)
        log.info(f"[eval] parsed score={parsed.get('score')} tech={parsed.get('technical_accuracy')} comm={parsed.get('soft_scores',{}).get('communication')}")

        # ── Extract and validate technical score ──────────────────────────
        # Prefer technical_accuracy if available (new prompt field)
        technical_raw = parsed.get("technical_accuracy") or parsed.get("score")
        technical_score = _safe_float(technical_raw, 5.0)
        technical_score = max(0.0, min(10.0, technical_score))

        # Apply pre-LLM cap if uncertainty detected
        if score_cap is not None:
            technical_score = min(technical_score, score_cap)
            log.info(f"Uncertainty cap applied ({uncertainty_type}): capped at {score_cap}")

        # Soft scores from LLM
        rs = parsed.get("soft_scores", {})
        soft = {k: _safe_float(rs.get(k), 5.0) for k in ("communication", "confidence", "problem_solving", "honesty")}

        # ── Weighted final score (LLM) ────────────────────────────────────
        llm_score = _weighted_score(technical_score, soft, q_category)
        llm_score = max(0.0, min(10.0, llm_score))

        # ── Dataset scoring ───────────────────────────────────────────────
        dataset_entries = state.get("dataset_entries", [])
        dataset_result  = {"available": False, "dataset_score": None,
                           "matched_concepts": [], "missing_concepts": [],
                           "scoring_method": "none", "similarity": 0.0,
                           "best_match_competency": ""}
        if dataset_entries:
            try:
                ollama_url = getattr(Config, "OLLAMA_BASE_URL", "http://localhost:11434")
                dataset_result = score_against_dataset(
                    answer      = answer,
                    question    = state.get("current_question", ""),
                    competency  = state.get("current_competency_tag", ""),
                    dataset_entries = dataset_entries,
                    ollama_url  = ollama_url,
                )
            except Exception as _dse:
                log.warning(f"Dataset scoring failed: {_dse}")

        # ── Blend LLM + dataset ───────────────────────────────────────────
        score, score_explanation = blend_scores(llm_score, dataset_result)
        score = max(0.0, min(10.0, score))
        log.info(f"[eval] Score: {score_explanation}")

        # Soft scores history — skip practice turns so Q0 doesn't pollute averages
        sh = list(state.get("soft_scores_history", []))
        if not state.get("is_practice_turn"):
            sh.append(soft)

        # Audio/video history
        ah = list(state.get("audio_scores_history", []))
        aa = state.get("current_audio_analysis")
        if aa:
            ah.append({
                "pace":        _safe_float(aa.get("pace_score"),       0.0),
                "fluency":     _safe_float(aa.get("fluency_score"),    0.0),
                "confidence":  _safe_float(aa.get("confidence_score"), 0.0),
                "engagement":  _safe_float(aa.get("engagement_score"), 0.0),
                "hesitation":  int(aa.get("hesitation_level", 0)),
                "observations": aa.get("observations", []),
                "summary":     aa.get("summary", ""),
            })

        vh = list(state.get("video_scores_history", []))
        va = state.get("current_video_analysis")
        if va and va.get("overall_score") is not None:
            vh.append({
                "overall":     _safe_float(va.get("overall_score"),       0.0),
                "eye_contact": _safe_float(va.get("eye_contact_score"),   0.0),
                "expression":  _safe_float(va.get("expression_score"),    0.0),
                "posture":     _safe_float(va.get("posture_score"),       0.0),
                "observations": va.get("observations", []),
                "method":      va.get("method", "basic_cv"),
            })

        # Competency status update
        comp = state.get("current_competency_tag", state.get("current_competency", "general"))
        comp_status = dict(state.get("competency_status", {}))
        existing = comp_status.get(comp, {"name": comp, "depth": 0, "confidence": 0.0, "score": 0.0, "tested": False})
        new_depth = min(existing["depth"] + 1, 3)
        comp_conf = _safe_float(parsed.get("competency_confidence"), min(score + 1, 10.0))
        new_score = round((_safe_float(existing.get("score")) + score) / 2, 1) if existing["tested"] else score
        comp_status[comp] = {"name": comp, "depth": new_depth, "confidence": comp_conf,
                              "score": new_score, "tested": True}

        # Candidate profile update
        profile = dict(state.get("candidate_profile", {}))
        score_trend = [float(s) for s in profile.get("score_trend", []) if s is not None]
        score_trend.append(score)
        strengths = list(profile.get("strengths", []))
        weaknesses = list(profile.get("weaknesses", []))
        bluff_count = profile.get("bluff_count", 0)
        if score >= 7.5 and comp not in strengths: strengths.append(comp)
        if score < 5.0 and comp not in weaknesses: weaknesses.append(comp)
        if parsed.get("bluff_detected"): bluff_count += 1

        archetype = "unknown"
        if bluff_count >= 2:
            archetype = "buzzword_heavy"
        elif len(score_trend) >= 3:
            avg = sum(score_trend) / len(score_trend)
            improving = score_trend[-1] > score_trend[0] + 1
            if avg >= 7.5: archetype = "strong_performer"
            elif improving: archetype = "fast_learner"
            elif avg >= 6.0: archetype = "solid_mid"
            elif avg < 4.5: archetype = "needs_fundamentals"
            else: archetype = "average"

        profile.update({"strengths": strengths[:6], "weaknesses": weaknesses[:6],
                         "bluff_count": bluff_count, "score_trend": score_trend[-8:],
                         "archetype": archetype})

        unverified = list(state.get("unverified_claims", []))
        for claim in parsed.get("unverified_claims", []):
            if claim and claim not in unverified:
                unverified.append(claim)
        unverified = unverified[-5:]

        contradiction_log = list(state.get("contradiction_log", []))
        if existing.get("tested") and _safe_float(existing.get("score"), 5.0) >= 7 and score < 4:
            contradiction_log.append(f"Score drop on '{comp}': was {existing['score']}/10, now {score}/10")

        wa = list(state.get("weak_areas", []))
        if score < Config.WEAK_SCORE_THRESHOLD:
            entry = f"'{comp}' — {state.get('current_question','')[:65]}... ({score}/10)"
            if entry not in wa: wa.append(entry)

        cls = state.get("consecutive_low_scores", 0)
        chs = state.get("consecutive_high_scores", 0)
        if score < Config.EARLY_STOP_SCORE: cls += 1; chs = 0
        else: cls = 0; chs = (chs + 1) if score >= 7.0 else 0

        # Update competency_status with this turn's score
        comp_status_upd = dict(state.get("competency_status", {}))
        comp_tag_eval = state.get("current_competency_tag", "")
        if comp_tag_eval and not state.get("is_practice_turn"):
            cs_e = dict(comp_status_upd.get(comp_tag_eval, {}))
            prev_scores = list(cs_e.get("all_scores", []))
            prev_scores.append(score)
            cs_e["tested"] = True
            cs_e["score"] = round(sum(prev_scores)/len(prev_scores), 1)
            cs_e["all_scores"] = prev_scores
            comp_status_upd[comp_tag_eval] = cs_e

        # Merge both competency tracking dicts: comp_status has depth/confidence,
        # comp_status_upd has all_scores. Merge them so we keep everything.
        for k, v in comp_status.items():
            if k not in comp_status_upd:
                comp_status_upd[k] = v
            else:
                merged = dict(comp_status_upd[k])
                merged["depth"]      = v.get("depth", merged.get("depth", 0))
                merged["confidence"] = v.get("confidence", merged.get("confidence", 0.0))
                merged["tested"]     = merged.get("tested") or v.get("tested", False)
                comp_status_upd[k]   = merged

        return {
            "current_score":       score,
            "current_llm_score":   llm_score,
            "current_dataset_score": dataset_result.get("dataset_score"),
            "current_dataset_result": {
                "available":             dataset_result.get("available", False),
                "similarity":            dataset_result.get("similarity", 0.0),
                "matched_concepts":      dataset_result.get("matched_concepts", []),
                "missing_concepts":      dataset_result.get("missing_concepts", []),
                "scoring_method":        dataset_result.get("scoring_method", "none"),
                "best_match_competency": dataset_result.get("best_match_competency", ""),
                "score_explanation":     score_explanation,
            },
            "current_soft_scores":    soft,
            "competency_status":      comp_status_upd,
            "current_feedback":       parsed.get("feedback", ""),
            "current_improvements":   parsed.get("improvements", []),
            "current_soft_skill_notes": parsed.get("soft_skill_notes", ""),
            "current_correctness_note": parsed.get("correctness_note", ""),
            "current_clarity_note":   parsed.get("clarity_note", ""),
            "current_depth_note":     parsed.get("depth_note", ""),
            "current_confidence_note": parsed.get("confidence_note", ""),
            "soft_scores_history":    sh,
            "audio_scores_history":   ah,
            "video_scores_history":   vh,
            "weak_areas":             wa,
            "consecutive_low_scores": cls,
            "consecutive_high_scores": chs,
            "candidate_profile":      profile,
            "unverified_claims":      unverified,
            "contradiction_log":      contradiction_log,
            "error":                  None,
        }

    except Exception as e:
        log.error(f"evaluate error: {e}", exc_info=True)
        # RETRY with minimal prompt to get at least a real score
        try:
            from langchain_groq import ChatGroq
            retry_llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                temperature=0.3, max_tokens=512,
                api_key=Config.GROQ_API_KEY,
            )
            q_text = state.get('current_question', '')[:200]
            a_text = state.get('current_answer', '')[:600]
            retry_prompt = (
                f"Score this interview answer strictly from 1-10.\n"
                f"Question: {q_text}\n"
                f"Answer: {a_text}\n"
                "Rules: 0-2=no knowledge, 3-4=wrong/vague, 5-6=partial, 7-8=strong with examples, 9-10=exceptional.\n"
                'Respond ONLY with JSON: {"score":<1-10>,"feedback":"<2 sentences>","improvements":["<action>"],"soft_scores":{"communication":5,"confidence":5,"problem_solving":5,"honesty":5}}'
            )
            from langchain_core.messages import HumanMessage
            retry_raw = retry_llm.invoke([HumanMessage(content=retry_prompt)]).content
            log.info(f"[eval] retry raw: {retry_raw[:150]}")
            retry_parsed = parse_json_output(retry_raw)
            retry_score = _safe_float(retry_parsed.get("score"), 5.0)
            return {
                "current_score": retry_score,
                "current_feedback": retry_parsed.get("feedback", "Evaluation completed."),
                "current_improvements": retry_parsed.get("improvements", []),
                "current_soft_skill_notes": "",
                "current_correctness_note": "", "current_clarity_note": "",
                "current_depth_note": "", "current_confidence_note": "",
                "consecutive_low_scores": state.get("consecutive_low_scores", 0),
                "consecutive_high_scores": state.get("consecutive_high_scores", 0),
                "error": None,
            }
        except Exception as e2:
            log.error(f"evaluate RETRY also failed: {e2}")
            return {
                "current_score": 5.0,
                "current_feedback": f"Evaluation error: {str(e)[:80]}",
                "current_improvements": [],
                "current_soft_skill_notes": "",
                "current_correctness_note": "", "current_clarity_note": "",
                "current_depth_note": "", "current_confidence_note": "",
                "consecutive_low_scores": state.get("consecutive_low_scores", 0),
                "consecutive_high_scores": state.get("consecutive_high_scores", 0),
                "error": str(e),
            }


# ── 5. Record Turn ────────────────────────────────────────────────────────
def record_turn(state):
    if state.get("session_locked"):
        return {}

    turns = list(state.get("turns", []))
    aa = state.get("current_audio_analysis") or {}
    va = state.get("current_video_analysis") or {}
    main_q_index = state.get("main_question_index", 0)
    followup_depth = state.get("followup_depth", 0)

    turn = {
        "turn": len(turns) + 1,
        "main_q_index": main_q_index,
        "followup_index": followup_depth,
        "question": state.get("current_question", ""),
        "question_category": state.get("current_question_category", "technical"),
        "answer": state.get("current_answer", ""),
        "mode": state.get("current_mode", "text"),
        "score": _safe_float(state.get("current_score"), 0.0),  # 0 if eval didn't run (not 5)
        "feedback": state.get("current_feedback", ""),
        "improvements": state.get("current_improvements", []),
        "transcription": state.get("current_transcription"),
        "is_followup": followup_depth > 0,
        "is_practice": state.get("is_practice_turn", False),
        "soft_skill_notes": state.get("current_soft_skill_notes", ""),
        "correctness_note": state.get("current_correctness_note", ""),
        "clarity_note": state.get("current_clarity_note", ""),
        "depth_note": state.get("current_depth_note", ""),
        "confidence_note": state.get("current_confidence_note", ""),
        "competency_tag": state.get("current_competency_tag", ""),
        "bluff_detected": False,
        # Dataset scoring
        "llm_score":             state.get("current_llm_score"),
        "dataset_score":         state.get("current_dataset_score"),
        "dataset_similarity":    (state.get("current_dataset_result") or {}).get("similarity"),
        "matched_concepts":      (state.get("current_dataset_result") or {}).get("matched_concepts", []),
        "missing_concepts":      (state.get("current_dataset_result") or {}).get("missing_concepts", []),
        "dataset_scoring_method":(state.get("current_dataset_result") or {}).get("scoring_method", "none"),
        "score_explanation":     (state.get("current_dataset_result") or {}).get("score_explanation", ""),
        "audio_pace_score": _safe_float(aa.get("pace_score")) if aa.get("pace_score") is not None else None,
        "audio_fluency_score": _safe_float(aa.get("fluency_score")) if aa.get("fluency_score") is not None else None,
        "audio_confidence_score": _safe_float(aa.get("confidence_score")) if aa.get("confidence_score") is not None else None,
        "audio_observations": aa.get("observations", []),
        "audio_summary": aa.get("summary", ""),
        "video_score": _safe_float(va.get("overall_score")) if va.get("overall_score") is not None else None,
        "video_eye_contact": _safe_float(va.get("eye_contact_score")) if va.get("eye_contact_score") is not None else None,
        "video_expression": _safe_float(va.get("expression_score")) if va.get("expression_score") is not None else None,
        "video_posture": _safe_float(va.get("posture_score")) if va.get("posture_score") is not None else None,
        "video_observations": va.get("observations", []),
        "video_method": va.get("method", "none"),
    }
    turns.append(turn)
    return {"turns": turns, "questions_asked": len(turns)}


# ── 6. Decide Next Action ─────────────────────────────────────────────────
def decide(state):
    """
    Central routing decision. Uses MAIN question index for completion checks.
    Enforces follow-up depth limit. Locks session on completion.
    """
    if state.get("session_locked"):
        return {"next_action": "end", "end_reason": "Session locked.", "interview_complete": True}

    main_qi = state.get("main_question_index", 0)
    followup_depth = state.get("followup_depth", 0)
    consec_fu = state.get("consecutive_followups", 0)
    total_fu = state.get("total_followups_asked", 0)
    # Session-level follow-up budget: 3–5 total
    session_fu_budget = MAX_SESSION_FOLLOWUPS
    session_fu_exhausted = total_fu >= session_fu_budget
    # How many questions remain (so we can force follow-ups if under minimum)
    session_max = min(state.get("session_max_questions", Config.MAX_QUESTIONS), Config.MAX_QUESTIONS)
    questions_remaining = session_max - (main_qi + 1)  # questions left after this one
    fu_deficit = max(0, MIN_SESSION_FOLLOWUPS - total_fu)  # how many more we must still do
    # Force a follow-up if we're under minimum AND questions remain AND slot allows
    must_followup = (fu_deficit > 0 and questions_remaining > 0
                     and consec_fu < MAX_FOLLOWUPS and not session_fu_exhausted)
    cls = state.get("consecutive_low_scores", 0)
    topics = list(state.get("topics_covered", []))
    plan = state.get("competency_plan", [])
    comp_status = state.get("competency_status", {})
    profile = state.get("candidate_profile", {})
    current_comp = state.get("current_competency", plan[0] if plan else "general")
    score = _safe_float(state.get("current_score"), 5.0)
    fingerprints = state.get("asked_topic_fingerprints", [])

    # ── HARD STOP: max questions reached ──────────────────────────────────
    session_max = min(state.get("session_max_questions", Config.MAX_QUESTIONS), Config.MAX_QUESTIONS)
    blueprint = state.get("interview_blueprint", [])
    # main_qi is the 0-based index of the question just answered.
    # We end when we've answered all slots: (main_qi + 1) >= session_max
    blueprint_exhausted = bool(blueprint) and (main_qi + 1) >= len(blueprint)
    if (main_qi + 1) >= session_max or blueprint_exhausted:
        return _lock_and_end(state, topics,
            f"Completed {main_qi + 1} questions." if blueprint_exhausted
            else f"Reached session limit of {session_max} questions.")

    # ── HARD STOP: dynamic early end (uses MAIN index) ────────────────────
    should_end, end_reason = should_end_early(
        comp_status, plan, main_qi, Config.MIN_QUESTIONS, cls, Config.EARLY_STOP_COUNT
    )
    if should_end:
        return _lock_and_end(state, topics, end_reason)

    # ── FORCE NEW QUESTION if follow-up depth maxed or comp saturated ─────
    # Compute slot limit here so it's available for all subsequent checks
    _bp = state.get("interview_blueprint", [])
    slot_max_fu_global = min(
        _bp[main_qi].get("max_followups", MAX_FOLLOWUPS)
        if _bp and main_qi < len(_bp) else MAX_FOLLOWUPS,
        3
    )
    if should_force_new_question(followup_depth, slot_max_fu_global, comp_status, current_comp):
        next_comp = get_next_competency(plan, comp_status, current_comp)
        new_phase = get_next_phase(main_qi + 1, state.get("level", "mid"))
        return {
            "next_action": "new_question",
            "end_reason": "",
            "topics_covered": topics,
            "current_competency": next_comp,
            "interview_phase": new_phase,
            "forced_question_category": "auto",
            "main_question_index": main_qi + 1,  # increment MAIN index
            "followup_depth": 0,                  # reset follow-up depth
            "consecutive_followups": 0,
        }

    # ── Under minimum: simple heuristic ──────────────────────────────────
    if main_qi < Config.MIN_QUESTIONS:
        saturated = compute_saturation(comp_status, current_comp)
        bluff = profile.get("bluff_count", 0) > 0
        slot_max_fu = slot_max_fu_global  # already computed above

        if saturated or consec_fu >= slot_max_fu:
            next_comp = get_next_competency(plan, comp_status, current_comp)
            new_phase = get_next_phase(main_qi + 1, state.get("level", "mid"))
            return {
                "next_action": "new_question",
                "end_reason": "",
                "topics_covered": topics,
                "current_competency": next_comp,
                "interview_phase": new_phase,
                "forced_question_category": "auto",
                "main_question_index": main_qi + 1,
                "followup_depth": 0,
                "consecutive_followups": 0,
            }

        # ── Follow-up gating: targeted probing, not automatic ──────────
        has_unverified = bool(state.get("unverified_claims", []))
        needs_followup = (
            must_followup                          # guaranteed minimum not yet reached
            or (
                not session_fu_exhausted           # respect session budget (max 5 total)
                and score < 8.0                    # probe any non-perfect answer
                and score >= 1.5                   # don't probe truly blank answers
                and not saturated
                and consec_fu < MAX_FOLLOWUPS      # respect per-slot limit (max 2)
                and not bluff                      # bluff handled separately
            ) or (
                not session_fu_exhausted
                and bluff                          # always probe bluff/contradiction
                and consec_fu < MAX_FOLLOWUPS
                and not saturated
            )
        )
        if needs_followup:
            return {
                "next_action": "followup",
                "end_reason": "",
                "topics_covered": topics,
                "followup_depth": followup_depth + 1,
                "consecutive_followups": consec_fu + 1,
                "total_followups_asked": total_fu + 1,
            }

        next_comp = get_next_competency(plan, comp_status, current_comp)
        new_phase = get_next_phase(main_qi + 1, state.get("level", "mid"))
        return {
            "next_action": "new_question",
            "end_reason": "",
            "topics_covered": topics,
            "current_competency": next_comp,
            "interview_phase": new_phase,
            "forced_question_category": "auto",
            "main_question_index": main_qi + 1,
            "followup_depth": 0,
            "consecutive_followups": 0,
        }

    # ── LLM strategic decision ─────────────────────────────────────────────
    turns = state.get("turns", [])
    history = "\n".join(
        f"Q{t['turn']}[{t.get('competency_tag','?')}][{'FU' if t['is_followup'] else 'New'}]"
        f"({_safe_float(t.get('score'), 0)}/10): {t['question'][:55]}"
        for t in turns[-5:]
    ) or "No turns."
    cov_str = _build_coverage_str(plan, comp_status)
    saturated = compute_saturation(comp_status, current_comp)
    sat_str = f"'{current_comp}' is {'SATURATED — must transition' if saturated else 'not saturated'}."
    diff_hint = get_difficulty_hint(state.get("level", "mid"), profile)
    bluff_detected = score < 5 and profile.get("bluff_count", 0) > 0

    try:
        raw = decide_next_action_chain(state["retriever"]).invoke({
            "role_label": state.get("role_label", "Professional"),
            "level": state.get("level", "mid"),
            "interview_phase": state.get("interview_phase", "technical"),
            "questions_asked": str(main_qi),
            "min_q": str(Config.MIN_QUESTIONS),
            "max_q": str(Config.MAX_QUESTIONS),
            "difficulty_hint": diff_hint,
            "competency_coverage": cov_str,
            "saturation_status": sat_str,
            "history": history,
            "question": state.get("current_question", ""),
            "answer": state.get("current_answer", "")[:150],
            "score": str(score),
            "bluff_detected": str(bluff_detected),
            "consecutive_followups": str(consec_fu),
            "unverified_claims": ", ".join(state.get("unverified_claims", [])[-3:]) or "none",
            "candidate_strengths": ", ".join(profile.get("strengths", [])) or "none",
            "candidate_weaknesses": ", ".join(profile.get("weaknesses", [])) or "none",
        })
        parsed = parse_json_output(raw)
        action = parsed.get("action", "new_question").lower()
        topic_tag = parsed.get("topic_tag", "")
        end_reason = parsed.get("end_reason", "")
        transition_note = parsed.get("transition_note", "")
        next_comp = parsed.get("next_competency") or get_next_competency(plan, comp_status, current_comp)
        force_cat = parsed.get("force_category", "auto")

        # Safety overrides
        if action not in ("followup", "new_question", "end"):
            action = "new_question"
        if action == "followup" and (consec_fu >= MAX_FOLLOWUPS or saturated or session_fu_exhausted):
            action = "new_question"
        if topic_tag and topic_tag not in topics:
            topics.append(topic_tag)

        if action == "end":
            return _lock_and_end(state, topics, end_reason or "Interview complete.")

        result = {"next_action": action, "end_reason": end_reason, "topics_covered": topics}
        if action == "new_question":
            new_phase = get_next_phase(main_qi + 1, state.get("level", "mid"))
            result.update({
                "current_competency": next_comp,
                "interview_phase": new_phase,
                "forced_question_category": force_cat,
                "main_question_index": main_qi + 1,
                "followup_depth": 0,
                "consecutive_followups": 0,
            })
        elif action == "followup":
            result.update({
                "followup_depth": followup_depth + 1,
                "consecutive_followups": consec_fu + 1,
            })
        if transition_note:
            result["last_transition_note"] = transition_note
        return result

    except Exception as e:
        log.error(f"decide LLM error: {e}")
        # Fallback: follow-up if low score, else advance
        action = "followup" if (score < Config.FOLLOWUP_SCORE_THRESHOLD
                                 and consec_fu < MAX_FOLLOWUPS and not saturated
                                 and not session_fu_exhausted) else "new_question"
        if action == "new_question":
            next_comp = get_next_competency(plan, comp_status, current_comp)
            new_phase = get_next_phase(main_qi + 1, state.get("level", "mid"))
            return {"next_action": action, "end_reason": "", "topics_covered": topics,
                    "current_competency": next_comp, "interview_phase": new_phase,
                    "forced_question_category": "auto",
                    "main_question_index": main_qi + 1, "followup_depth": 0,
                    "consecutive_followups": 0}
        return {"next_action": action, "end_reason": "", "topics_covered": topics,
                "followup_depth": followup_depth + 1, "consecutive_followups": consec_fu + 1}


def _lock_and_end(state, topics, end_reason):
    """Lock session and signal completion. Called from decide()."""
    log.info(f"Interview complete: {end_reason}")
    return {
        "next_action": "end",
        "end_reason": end_reason,
        "topics_covered": topics,
        "interview_complete": True,
        "session_locked": True,   # ← hard lock: no more generation
    }


# ── 7. Generate Follow-up ─────────────────────────────────────────────────
def generate_followup(state):
    if state.get("session_locked"):
        return {"error": "Session locked"}

    fingerprints = list(state.get("asked_topic_fingerprints", []))
    topics = list(state.get("topics_covered", []))
    profile = state.get("candidate_profile", {})
    unverified = state.get("unverified_claims", [])
    bluff_signals = "Possible bluffing — probe for specifics." if profile.get("bluff_count", 0) > 0 else "None."

    try:
        fu = generate_followup_chain(state["retriever"]).invoke({
            "question": state.get("current_question", ""),
            "answer": state.get("current_answer", ""),
            "role_label": state.get("role_label", "Professional"),
            "level": state.get("level", "mid"),
            "bluff_signals": bluff_signals,
            "unverified_claims": ", ".join(unverified[-2:]) if unverified else "none",
        })
        fu = fu.strip()
        fp = make_topic_fingerprint(fu)
        if fp not in fingerprints:
            fingerprints.append(fp)
        # Use current_competency as topic label — not the follow-up question text
        comp_tag = state.get("current_competency_tag") or state.get("current_competency", "")
        tag = comp_tag.replace("_", " ").title() if comp_tag else ""
        # Only add if this topic isn't already in the list
        if tag and tag not in topics:
            topics.append(tag)
        return {
            "current_question": fu,
            "current_question_category": "followup",
            "current_answer": "",
            "current_score": None,
            "current_feedback": "",
            "current_improvements": [],
            "current_transcription": None,
            "current_soft_skill_notes": "",
            "current_audio_analysis": None,
            "current_video_analysis": None,
            "topics_covered": topics,
            "asked_topic_fingerprints": fingerprints,
            "current_correctness_note": "",
            "current_clarity_note": "",
            "current_depth_note": "",
            "current_confidence_note": "",
            "error": None,
        }
    except Exception:
        return generate_question(state)


# ── 8. Final Evaluation ───────────────────────────────────────────────────
def _build_mode_soft(mode, comm, conf_s, prob, hon, avg_pace=0.0, avg_flu=0.0, avg_nv=0.0,
                     avg_conf_del=0.0, avg_eng=0.0, avg_eye=0.0, avg_expr=0.0, avg_posture=0.0):
    """Build soft_skills dict based on interview mode."""
    base = {
        "communication": round(comm, 1),
        "confidence": round(conf_s, 1),
        "problem_solving": round(prob, 1),
        "honesty": round(hon, 1),
    }
    if mode in ("audio", "video") and avg_pace > 0:
        base["speaking_pace"] = round(avg_pace, 1)
        if avg_flu > 0: base["voice_fluency"] = round(avg_flu, 1)
        if avg_conf_del > 0: base["delivery_confidence"] = round(avg_conf_del, 1)
        if avg_eng > 0: base["engagement"] = round(avg_eng, 1)
    if mode == "video" and avg_nv > 0:
        base["non_verbal"] = round(avg_nv, 1)
        if avg_eye > 0: base["eye_contact"] = round(avg_eye, 1)
        if avg_expr > 0: base["expression"] = round(avg_expr, 1)
        if avg_posture > 0: base["posture"] = round(avg_posture, 1)
    return base


def generate_final_eval(state):
    turns = state.get("turns", [])
    # Exclude practice turns AND all turns from Q0 (main_q_index=0) — the warmup phase
    scored_turns = [t for t in turns if not t.get("is_practice", False) and t.get("main_q_index", 0) > 0]
    # If session ended early, unanswered questions beyond blueprint already have score=0 via not being in turns
    # But we note the early_finish for context
    early_finished = state.get("early_finished", False)
    total_planned  = len(state.get("blueprint", state.get("interview_blueprint", [])))
    if not scored_turns:
        # Even with no scored turns, return a minimal eval so the UI doesn't show the error placeholder
        return {"final_evaluation": {
            "role_label": state.get("role_label", "Professional"),
            "technical_average": 0.0,
            "competency_scores": {},
            "soft_skills": {"communication": 5, "confidence": 5, "problem_solving": 5, "honesty": 5},
            "overall_score": 0.0,
            "confidence_in_evaluation": 3.0,
            "interview_consistency": "stable",
            "growth_potential": "medium",
            "mentorship_need": "",
            "strengths": [],
            "weak_areas": [],
            "bluff_assessment": "No answers recorded.",
            "soft_skill_summary": "No answers were provided.",
            "delivery_summary": "",
            "hiring_recommendation": "No",
            "summary_paragraph": "No answers were recorded during this session.",
            "improvement_plan": [],
            "topics_covered": state.get("topics_covered", []),
            "role_fit_score": 0,
            "readiness": "needs_6_months",
            "hiring_rationale": "Session had no scored answers.",
        }}

    transcript = "\n".join(
        f"Q{t['turn']}[{t.get('competency_tag','?')}][{'FU' if t['is_followup'] else 'New'},"
        f"{_safe_float(t.get('score'), 0)}/10]:\n"
        f"Q: {t['question'][:100]}\nA: {t['answer'][:250]}"
        for t in scored_turns
    )
    tech_scores_str = "\n".join(
        f"Q{t.get('main_q_index', t['turn'])}{'(FU)' if t['is_followup'] else ''}"
        f"[{t.get('competency_tag','?')}] {_safe_float(t.get('score'), 0)}/10: "
        f"{t.get('feedback','')[:120]} | depth: {t.get('depth_note','')[:60]}"
        for t in scored_turns
    )
    plan = state.get("competency_plan", [])
    comp_status = state.get("competency_status", {})
    cov_str = _build_coverage_str(plan, comp_status)
    profile = state.get("candidate_profile", {})
    bluff_incidents = f"{profile.get('bluff_count',0)} suspected bluffing incident(s)." if profile.get("bluff_count") else "None."
    contradiction_log = state.get("contradiction_log", [])
    soft_obs = "\n".join(f"Q{t['turn']}: {t.get('soft_skill_notes','')}"
                          for t in scored_turns if t.get("soft_skill_notes"))
    audio_sum = "\n".join(f"Q{t['turn']}: {t.get('audio_summary','')}"
                           for t in scored_turns if t.get("audio_summary"))
    video_sum = "\n".join(
        f"Q{t['turn']}: eye={t.get('video_eye_contact','?')} expr={t.get('video_expression','?')}"
        for t in scored_turns if t.get("video_score") is not None
    ) or "Video analysis not available."

    # Weight JD-related questions higher in tech_avg calculation
    job_desc = state.get("job_description", "").strip()
    scores_weighted = []
    for t in scored_turns:
        s = _safe_float(t.get("score"), 0.0)  # 0 not 5 for unanswered
        if job_desc and not t.get("jd_related", True):
            scores_weighted.append(s * 0.85)
        else:
            scores_weighted.append(s * 1.0)
    scores = [_safe_float(t.get("score"), 0.0) for t in scored_turns]

    # Early finish: unanswered questions count as 0 in the denominator
    # Total planned = blueprint questions + expected follow-ups (approx 1 per question)
    blueprint = state.get("blueprint", state.get("interview_blueprint", []))
    total_planned = max(len(blueprint), len(scored_turns), 6)  # at least 6 questions expected
    if early_finished and total_planned > len(scored_turns):
        # Add zero scores for each unanswered question
        unanswered_count = total_planned - len(scored_turns)
        scores_weighted += [0.0] * unanswered_count
        scores += [0.0] * unanswered_count
        log.info(f"Early finish: {len(scored_turns)} answered, {unanswered_count} unanswered → scores padded with 0s")

    tech_avg = round(sum(scores_weighted) / len(scores_weighted), 1) if scores_weighted else 0

    actual_weak = []
    for t in scored_turns:
        if _safe_float(t.get("score"), 5.0) < Config.WEAK_SCORE_THRESHOLD:
            ans_snip = (t.get("answer") or "").strip()[:100]
            ans_quote = f' Candidate answered: "{ans_snip}..."' if len(ans_snip) > 20 else ""
            actual_weak.append({
                "area": t.get("competency_tag", "?"),
                "score": _safe_float(t.get("score"), 0),
                "feedback": (t.get("feedback", "") or "")[:150] + ans_quote,
                "reason": t.get("depth_note", t.get("clarity_note", ""))[:80],
                "question": t.get("question", "")[:70],
            })
            if len(actual_weak) >= 8:
                break

    # Initialize ALL variables before try so except block never hits UnboundLocalError
    consistency    = "stable"
    interview_mode = state.get("interview_mode", "text")
    avg_pace  = 0.0; avg_flu   = 0.0; avg_conf_del = 0.0
    avg_eng   = 0.0; avg_nv    = 0.0; avg_eye      = 0.0
    avg_expr  = 0.0; avg_posture = 0.0
    actual_comm = 5.0; actual_conf = 5.0
    actual_prob = 5.0; actual_hon  = 5.0
    parsed = {}
    try:
        trend_pre = [float(s) for s in profile.get("score_trend", []) if s is not None]
        if len(trend_pre) >= 3:
            fh = sum(trend_pre[:len(trend_pre)//2]) / max(len(trend_pre)//2, 1)
            sh = sum(trend_pre[len(trend_pre)//2:]) / max(len(trend_pre) - len(trend_pre)//2, 1)
            if sh > fh + 1: consistency = "improving"
            elif sh < fh - 1: consistency = "declining"

        # Compute actual soft averages from per-answer history
        ssh2 = [e for e in state.get("soft_scores_history", []) if e]

        def _avg_ssh(key):
            vals = [_safe_float(s.get(key)) for s in ssh2
                    if s.get(key) is not None and _safe_float(s.get(key)) > 0]
            return round(sum(vals)/len(vals), 1) if vals else None  # None means "not measured"

        actual_comm = _avg_ssh("communication")
        actual_conf = _avg_ssh("confidence")
        actual_prob = _avg_ssh("problem_solving")
        actual_hon  = _avg_ssh("honesty")

        # TEXT MODE: compute soft skills from actual answer content if history empty/all-zero
        if interview_mode == "text" and scored_turns:
            def _compute_text_soft():
                comm_vals, conf_vals, ps_vals, hon_vals = [], [], [], []
                for t in scored_turns:
                    ans = (t.get("answer") or "").strip()
                    wc  = len(ans.split())
                    sc  = _safe_float(t.get("score"), 0)
                    # Communication: word count, sentence variety, structure markers
                    struct_words = sum(1 for w in ("first","then","because","however","therefore",
                                                    "for example","additionally","in summary") if w in ans.lower())
                    comm = min(9.0, 3.0 + (wc / 30) + struct_words * 0.5)
                    comm_vals.append(round(min(comm, sc + 1.5), 1))  # cap near actual score
                    # Confidence: definitive language vs hedging
                    hedges = sum(1 for w in ("maybe","perhaps","i think","i guess","not sure","possibly") if w in ans.lower())
                    strong = sum(1 for w in ("i implemented","i built","i used","i designed","specifically","exactly") if w in ans.lower())
                    conf = min(9.0, max(3.0, 5.0 + strong * 0.6 - hedges * 0.7))
                    conf_vals.append(round(conf, 1))
                    # Problem solving: mirrors technical score
                    ps_vals.append(round(min(9.0, max(2.0, sc * 0.9)), 1))
                    # Honesty: explicit admission of uncertainty is honest; bluffing is not
                    bluff_sig = any(p in ans.lower() for p in ("i don't know","not sure","haven't","i would assume"))
                    hon_vals.append(round(8.5 if bluff_sig else min(8.0, max(4.0, sc * 0.85 + 1)), 1))
                return (
                    round(sum(comm_vals)/len(comm_vals), 1),
                    round(sum(conf_vals)/len(conf_vals), 1),
                    round(sum(ps_vals)/len(ps_vals), 1),
                    round(sum(hon_vals)/len(hon_vals), 1),
                )
            tc, tf, tp, th = _compute_text_soft()
            if actual_comm is None: actual_comm = tc
            if actual_conf is None: actual_conf = tf
            if actual_prob is None: actual_prob = tp
            if actual_hon  is None: actual_hon  = th

        # Final fallback: derive from tech_avg (still better than hardcoded 5)
        if actual_comm is None: actual_comm = round(min(8, max(3, tech_avg * 0.85)), 1)
        if actual_conf is None: actual_conf = round(min(8, max(3, tech_avg * 0.80)), 1)
        if actual_prob is None: actual_prob = round(min(9, max(2, tech_avg * 0.90)), 1)
        if actual_hon  is None: actual_hon  = round(min(8, max(4, 6.0)), 1)

        # Compute audio/video averages BEFORE LLM call so except block can use them
        ah = state.get("audio_scores_history", [])
        vh = state.get("video_scores_history", [])
        avg_pace     = _avg(ah, "pace");    avg_flu     = _avg(ah, "fluency")
        avg_conf_del = _avg(ah, "confidence"); avg_eng  = _avg(ah, "engagement")
        avg_nv       = _avg(vh, "overall"); avg_eye     = _avg(vh, "eye_contact")
        avg_expr     = _avg(vh, "expression"); avg_posture = _avg(vh, "posture")

        raw = final_evaluation_chain(state["retriever"]).invoke({
            "role_label": state.get("role_label", "Professional"),
            "level": state.get("level", "mid"),
            "transcript": transcript[:3000],
            "technical_scores": tech_scores_str,
            "competency_coverage": cov_str,
            "bluff_incidents": bluff_incidents,
            "contradiction_log": "; ".join(contradiction_log) if contradiction_log else "None.",
            "soft_observations": soft_obs or "No observations.",
            "audio_analysis": audio_sum or "Text mode.",
            "video_analysis": video_sum,
            "actual_comm": str(actual_comm),
            "actual_conf": str(actual_conf),
            "actual_prob": str(actual_prob),
            "actual_hon": str(actual_hon),
        })
        parsed = parse_json_output(raw)
        # Use computed averages — more accurate than LLM regeneration
        soft = parsed.get("soft_skills", {})
        soft["communication"]   = actual_comm
        soft["confidence"]      = actual_conf
        soft["problem_solving"] = actual_prob
        soft["honesty"]         = actual_hon
        # Delivery metrics — ONLY from real computed audio/video analysis
        # First, purge any LLM-guessed delivery values (they default to 5 when no audio)
        for _dk in ("speaking_pace","voice_fluency","delivery_confidence","engagement",
                    "non_verbal","eye_contact","expression","posture"):
            soft.pop(_dk, None)
        # Now insert only values we actually measured
        if interview_mode in ("audio", "video") and ah:
            if avg_pace > 0:     soft["speaking_pace"]       = round(avg_pace, 1)
            if avg_flu > 0:      soft["voice_fluency"]        = round(avg_flu, 1)
            if avg_conf_del > 0: soft["delivery_confidence"]  = round(avg_conf_del, 1)
            if avg_eng > 0:      soft["engagement"]           = round(avg_eng, 1)
        if interview_mode == "video" and vh:
            if avg_nv > 0:      soft["non_verbal"]    = round(avg_nv, 1)
            if avg_eye > 0:     soft["eye_contact"]   = round(avg_eye, 1)
            if avg_expr > 0:    soft["expression"]    = round(avg_expr, 1)
            if avg_posture > 0: soft["posture"]       = round(avg_posture, 1)
        # Remove None values
        soft = {k: v for k, v in soft.items() if v is not None}

        # Build strengths: LLM strings first (they reference transcript), fallback to turns
        llm_strengths = [s for s in parsed.get("strengths", []) if isinstance(s, str) and len(s) > 8]
        if not llm_strengths:
            llm_strengths = []
            for t in scored_turns:
                if _safe_float(t.get("score"), 0) >= 6.5 and t.get("feedback"):
                    ans_snippet = (t.get("answer") or "")[:90].strip()
                    quote = f' ("{ans_snippet}...")' if len(ans_snippet) > 20 else ""
                    llm_strengths.append(
                        f"{t.get('competency_tag','General').replace('_',' ').title()}: "
                        f"{t.get('feedback','')[:120]}{quote}"
                    )
                    if len(llm_strengths) >= 4:
                        break

        # Build weak_areas: always computed from real turn data, LLM supplements
        llm_weak = parsed.get("weak_areas") or []
        # Build from turns with low scores
        computed_weak_turns = [w for w in actual_weak if _safe_float(w.get("score"), 10) < 6.5]
        # Also flag competencies that were never tested
        untested = [c for c in plan if not comp_status.get(c, {}).get("tested")]
        untested_items = [
            {"area": c, "score": 0, "feedback": f"This topic was not covered in the interview — study {c.replace('_',' ')} before your next session."}
            for c in untested[:3]
        ]
        # Merge: LLM + computed turns + untested (deduplicated by area)
        seen_areas = set()
        llm_weak_merged = []
        for item in (llm_weak + computed_weak_turns + untested_items):
            area = item.get("area", "") if isinstance(item, dict) else item.split(":")[0][:30]
            if area not in seen_areas:
                seen_areas.add(area)
                llm_weak_merged.append(item)
        llm_weak = llm_weak_merged[:6]

        # Soft skills: if all exactly 5 (fallback default), try to infer from answers
        soft_vals = [soft.get(k, 5.0) for k in ("communication", "confidence", "problem_solving", "honesty")]
        all_default = all(abs(v - 5.0) < 0.05 for v in soft_vals)
        if all_default and scored_turns:
            # Infer communication from average answer length / clarity
            avg_ans_len = sum(len(t.get("answer","")) for t in scored_turns) / len(scored_turns)
            comm_infer = min(9.0, 5.0 + (avg_ans_len - 100) / 120)  # longer answers → better comm
            # Problem solving from avg score on technical turns
            tech_turns = [t for t in scored_turns if t.get("question_category") not in ("behavioral",)]
            ps_infer = round(sum(_safe_float(t.get("score"), 5) for t in tech_turns) / max(len(tech_turns), 1), 1) if tech_turns else 5.0
            # Honesty from bluff count
            bluff_n = state.get("candidate_profile", {}).get("bluff_count", 0)
            hon_infer = max(4.0, 8.0 - bluff_n * 1.5)
            conf_infer = min(9.0, max(3.0, ps_infer - 0.5 + (1 if bluff_n == 0 else -0.5)))
            soft["communication"]   = round(min(9.0, max(3.0, comm_infer)), 1)
            soft["problem_solving"] = round(min(9.0, max(3.0, ps_infer)), 1)
            soft["honesty"]         = round(hon_infer, 1)
            soft["confidence"]      = round(conf_infer, 1)

        return {"final_evaluation": {
            "role_label": state.get("role_label", "Professional"),
            "technical_average": _safe_float(parsed.get("technical_average") or tech_avg),
            "competency_scores": (lambda llm_scores, fallback: {
                **fallback,  # start with computed scores
                **{k: v for k, v in llm_scores.items() if v > 0}  # override with LLM scores where available
            })(
                parsed.get("competency_scores") or {},
                {c: round(_safe_float(comp_status.get(c, {}).get("score"), 0), 1) for c in plan}
            ),
            "soft_skills": soft,
            "overall_score": _safe_float(parsed.get("overall_score") or round(tech_avg*0.6 + 5*0.4, 1)),
            "confidence_in_evaluation": _safe_float(parsed.get("confidence_in_evaluation") or 7.0),
            "interview_consistency": parsed.get("interview_consistency", consistency),
            "growth_potential": parsed.get("growth_potential", "medium"),
            "mentorship_need": parsed.get("mentorship_need", ""),
            "strengths": llm_strengths,
            "weak_areas": llm_weak,
            "bluff_assessment": parsed.get("bluff_assessment", bluff_incidents),
            "soft_skill_summary": parsed.get("soft_skill_summary", ""),
            "delivery_summary": parsed.get("delivery_summary", ""),
            "hiring_recommendation": parsed.get("hiring_recommendation", "Maybe"),
            "summary_paragraph": parsed.get("summary_paragraph", ""),
            "improvement_plan": parsed.get("improvement_plan", []),
            "topics_covered": state.get("topics_covered", []),
            "role_fit_score": _safe_float(parsed.get("role_fit_score") or 0),
            "readiness": parsed.get("readiness", "needs_3_months"),
            "hiring_rationale": parsed.get("hiring_rationale", ""),
        }}

    except Exception as e:
        log.error(f"final_eval error: {e}", exc_info=True)
        # Use the pre-initialized actual_* values (computed before LLM call if possible)
        comm = actual_comm; conf_s = actual_conf
        prob = actual_prob; hon = actual_hon
        # Weighted fallback score: 55% technical, 20% problem-solving, 15% communication, 10% honesty
        overall = round(tech_avg * 0.55 + prob * 0.20 + comm * 0.15 + hon * 0.10, 1)
        if tech_avg < 4.0:
            overall = min(overall, 5.5)
        overall = max(0.0, min(10.0, overall))
        rec = "Yes" if overall >= 6.5 else "Maybe" if overall >= 5 else "No"
        return {"final_evaluation": {
            "role_label": state.get("role_label", "Professional"),
            "technical_average": tech_avg,
            "competency_scores": {
                c: round(_safe_float(comp_status.get(c, {}).get("score"), 0), 1)
                for c in plan
            },
            "soft_skills": _build_mode_soft(interview_mode, comm, conf_s, prob, hon, avg_pace, avg_flu, avg_nv, avg_conf_del, avg_eng, avg_eye, avg_expr, avg_posture),
            "overall_score": overall, "confidence_in_evaluation": 6.0,
            "interview_consistency": consistency, "growth_potential": "medium",
            "strengths": [
                (lambda t: (
                    f"{t.get('competency_tag','General').replace('_',' ').title()}: "
                    f"{(t.get('feedback') or '')[:120]}"
                    + (f' ("{(t.get("answer") or "")[:80].strip()}...")'
                       if len((t.get("answer") or "").strip()) > 20 else "")
                ))(t)
                for t in scored_turns
                if _safe_float(t.get("score"), 0) >= 6.5
            ][:4] or [
                f"{s.replace('_',' ').title()}: Demonstrated competency in this area."
                for s in profile.get("strengths", [])
                if isinstance(s, str)
            ],
            "weak_areas": actual_weak, "bluff_assessment": bluff_incidents,
            "soft_skill_summary": (
                f"Communication averaged {comm}/10 across {len(scored_turns)} answered question(s)"
                + (" — answers were well-structured, clear, and detailed." if comm >= 7
                   else " — answers were adequate but could use more structure." if comm >= 5
                   else " — answers tended to be brief, vague, or lacked clear reasoning.")
                + f" Problem-solving scored {prob}/10"
                + (" — demonstrated strong, structured analytical thinking." if prob >= 7
                   else " — showed some analytical depth but reasoning was inconsistent." if prob >= 5
                   else " — reasoning steps were often implicit or missing.")
                + (f" Honesty: {hon}/10." if hon else "")
            ),
            "delivery_summary": (
                "" if interview_mode == "text"
                else (
                    " | ".join(filter(None, [
                        f"Speaking pace: {round(avg_pace,1)}/10" if avg_pace > 0 else None,
                        f"Fluency: {round(avg_flu,1)}/10" if avg_flu > 0 else None,
                        f"Delivery confidence: {round(avg_conf_del,1)}/10" if avg_conf_del > 0 else None,
                        f"Engagement: {round(avg_eng,1)}/10" if avg_eng > 0 else None,
                    ])) + "."
                ) if avg_pace > 0
                else "Audio delivery analysis not available for this session."
            ),
            "hiring_recommendation": rec,
            "summary_paragraph": (
                f"Candidate completed {len(scored_turns)} of {total_planned} planned questions"
                f" for {state.get('role_label','Professional')} ({state.get('level','mid')})"
                + (" — session ended early." if early_finished else ".")
                + f" Technical average: {tech_avg}/10."
            ),
            "improvement_plan": [
                {"area": c,
                 "priority": "High" if _safe_float(comp_status.get(c, {}).get("score"), 5) < 4.5 else "Medium",
                 "issue": next(
                     (t.get("feedback","")[:200] for t in scored_turns
                      if t.get("competency_tag") == c and t.get("feedback")
                      and _safe_float(t.get("score"), 5) < 7),
                     f"Answers on {c.replace('_',' ')} lacked sufficient depth or specific examples."
                 ),
                 "actions": list(dict.fromkeys([  # deduplicate while preserving order
                     imp for t in scored_turns if t.get("competency_tag") == c
                     for imp in (t.get("improvements") or [])
                     if imp and len(imp) > 15
                 ]))[:3] or [
                     f"Study {c.replace('_',' ')} concepts and be ready to explain them with examples",
                     f"Practice articulating trade-offs and decision-making in {c.replace('_',' ')}",
                     "Review your session answers and identify where you lacked specificity"
                 ]
                }
                for c in plan if _safe_float(comp_status.get(c, {}).get("score"), 5) < 6
            ][:5],
            "topics_covered": state.get("topics_covered", []),
        }}


# ── 9. End ────────────────────────────────────────────────────────────────
def end_interview(state):
    """Final node. Ensures session_locked=True and interview_complete=True."""
    return {
        "interview_complete": True,
        "session_locked": True,
        "error": None,
    }
