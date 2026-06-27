"""Tests for job_match feature."""

import time

from job_matcher.api.schemas import MatchRequest
from job_matcher.api.service import get_match_results, get_match_status, start_job_match

CV_SAMPLE = """
John Doe
Software Engineer

## Experience
Built React and TypeScript apps at Stripe for 5 years. Led payments UI team.

## Skills
React, TypeScript, Node.js, Python, AWS, Docker, GraphQL, PostgreSQL
""".strip()


def _wait_for_results(session_id: str, timeout_s: float = 30.0):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        status = get_match_status(session_id)
        if status and status.status == "ready":
            return get_match_results(session_id)
        if status and status.status == "failed":
            raise AssertionError(status.error or "job match failed")
        time.sleep(0.1)
    raise TimeoutError(f"job match {session_id} did not complete in {timeout_s}s")


def test_start_job_match_returns_ranked_jobs():
    start = start_job_match(MatchRequest(cv_text=CV_SAMPLE, target_role="Senior Engineer"))
    result = _wait_for_results(start.session_id)
    assert result is not None
    assert result.session_id == start.session_id
    assert len(result.jobs) >= 3
    assert result.jobs[0].match_score >= result.jobs[-1].match_score
    assert result.jobs[0].why


def test_get_match_results_by_session():
    start = start_job_match(MatchRequest(cv_text=CV_SAMPLE))
    fetched = _wait_for_results(start.session_id)
    assert fetched is not None
    again = get_match_results(start.session_id)
    assert again is not None
    assert again.session_id == fetched.session_id
    assert len(again.jobs) == len(fetched.jobs)
