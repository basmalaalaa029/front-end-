"""Job matching — orchestrates the job_matcher engine pipeline."""

from __future__ import annotations

import logging
import time
import uuid
from typing import List, Optional

from cv_agent.app.config import PipelineConfig
from job_matcher.api.schemas import MatchRequest, MatchResultsResponse, MatchedJob
from job_matcher.api.session import MatchSession, get_match_session_manager

log = logging.getLogger(__name__)

JOB_MATCH_TOP_N = 10


def _why_summary(score: int, title: str, company: str,
                  matched_skills: List[str], missing_skills: List[str]) -> str:
    kw = ", ".join(matched_skills[:4]) if matched_skills else "core skills"
    gap = ", ".join(missing_skills[:2]) if missing_skills else ""

    if score >= 85:
        return f"Strong overlap on {kw} — your CV aligns well with {title} at {company}."
    if score >= 70:
        msg = f"Good fit for {title} at {company}. Highlight {kw} in your application."
        if gap:
            msg += f" Consider strengthening {gap}."
        return msg
    if score >= 55:
        msg = f"Moderate match for {title} at {company}."
        if gap:
            msg += f" Strengthen {gap} to improve odds."
        return msg
    return f"Limited overlap for {title} at {company}. Consider tailoring CV for {kw}."


def _run_full_pipeline(req: MatchRequest, cfg: PipelineConfig) -> List[MatchedJob]:
    from job_matcher.cv_reader.parser import parse_cv
    from job_matcher.cv_reader.identity import extract_identity
    from job_matcher.jobs.fetcher import fetch_jobs
    from job_matcher.matching.engine import pre_filter, rank_jobs
    from job_matcher.matching.reranker import CrossEncoderReranker
    from job_matcher.rag.vector_store import JobVectorStore, generate_query
    from job_matcher.rag.explainer import RAGExplainer

    profile = parse_cv(req.cv_text)

    if req.target_role:
        profile.setdefault("preferred_roles", [])
        if req.target_role not in profile["preferred_roles"]:
            profile["preferred_roles"].insert(0, req.target_role)
        profile["_llm_query"] = req.target_role

    try:
        profile["_identity"] = extract_identity(profile, req.cv_text)
    except Exception:
        pass

    try:
        if not profile.get("_llm_query"):
            profile["_llm_query"] = generate_query(profile)
    except Exception:
        pass

    jobs = fetch_jobs(
        profile,
        country="us",
        remote_only=False,
        max_jobs=getattr(cfg, "max_jobs", 500),
    )

    if not jobs:
        log.warning("No jobs fetched from live sources")
        return []

    jobs = pre_filter(profile, jobs)

    rag_top_k = min(200, len(jobs))
    try:
        store = JobVectorStore()
        built = store.build(jobs)
        if built:
            jobs = store.retrieve(profile, k=rag_top_k)
    except Exception as exc:
        log.warning("RAG retrieval failed (%s), using pre-filtered pool", exc)

    ranked = rank_jobs(profile, jobs, diversify=True)

    try:
        reranker = CrossEncoderReranker()
        if reranker.is_available():
            ranked = reranker.rerank(profile, ranked, top_n=50)
    except Exception as exc:
        log.warning("Cross-encoder rerank failed (%s), using scored order", exc)

    try:
        explainer = RAGExplainer()
        explainer.explain_batch(profile, ranked, top_n=JOB_MATCH_TOP_N)
    except Exception as exc:
        log.warning("RAG explanations failed (%s)", exc)

    results: List[MatchedJob] = []
    for r in ranked[:JOB_MATCH_TOP_N]:
        score = int(r.get("score", 0))
        title = r.get("title", "")
        company = r.get("company", "")
        matched = r.get("matched_skills", [])
        missing = r.get("missing_skills", [])

        rag_data = r.get("rag", {})
        if rag_data.get("match_summary"):
            why = rag_data["match_summary"]
        else:
            why = _why_summary(score, title, company, matched, missing)

        results.append(MatchedJob(
            id=r.get("url") or f"{company}-{title}".replace(" ", "-").lower(),
            brand=company.lower().replace(" ", "-")[:20],
            logo=company[0].upper() if company else "?",
            title=title,
            company=company,
            location=r.get("location", ""),
            salary=r.get("salary", ""),
            match_score=score,
            why=why,
            source=r.get("source", ""),
            url=r.get("url", ""),
            posted=r.get("posted", ""),
            score_breakdown={
                "semantic": r.get("score_semantic", 0),
                "hard_skills": r.get("score_skills", 0),
                "seniority": r.get("score_seniority", 0),
                "role_title": r.get("score_title", 0),
                "soft_certs": r.get("score_extra", 0),
            },
            tags=r.get("tags", []) or [],
            matched_skills=matched,
            missing_skills=missing,
        ))

    return results


def run_job_match(
    req: MatchRequest,
    config: Optional[PipelineConfig] = None,
) -> MatchResultsResponse:
    cfg = config or PipelineConfig()
    t0 = time.perf_counter()
    session_id = str(uuid.uuid4())[:12]

    text = req.cv_text.strip()
    if len(text) < 50:
        raise ValueError("CV text is too short — provide at least 50 characters.")

    try:
        matched = _run_full_pipeline(req, cfg)
    except Exception:
        log.exception("Job match pipeline failed")
        matched = []

    latency = int((time.perf_counter() - t0) * 1000)

    session = MatchSession(
        session_id=session_id,
        status="completed",
        jobs=matched,
        target_role=req.target_role,
        latency_ms=latency,
    )
    get_match_session_manager().create(session_id, session)

    return MatchResultsResponse(
        session_id=session_id,
        status="completed",
        jobs=matched,
        target_role=req.target_role,
        latency_ms=latency,
    )


def get_match_results(session_id: str) -> MatchResultsResponse:
    rec = get_match_session_manager().get(session_id)
    if rec is None:
        raise ValueError(f"Session '{session_id}' not found.")
    return MatchResultsResponse(
        session_id=rec.session_id,
        status=rec.status,
        jobs=rec.jobs,
        target_role=rec.target_role,
        latency_ms=rec.latency_ms,
        error=rec.error,
    )
