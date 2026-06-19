"""Tests for job_match feature."""

from job_matcher.api.schemas import MatchRequest
from job_matcher.api.service import get_match_results, run_job_match

CV_SAMPLE = """
John Doe
Software Engineer

## Experience
Built React and TypeScript apps at Stripe for 5 years. Led payments UI team.

## Skills
React, TypeScript, Node.js, Python, AWS, Docker, GraphQL, PostgreSQL
""".strip()


def test_run_job_match_returns_ranked_jobs():
    result = run_job_match(MatchRequest(cv_text=CV_SAMPLE, target_role="Senior Engineer"))
    assert result.session_id
    assert len(result.jobs) >= 3
    assert result.jobs[0].match_score >= result.jobs[-1].match_score
    assert result.jobs[0].why


def test_get_match_results_by_session():
    created = run_job_match(MatchRequest(cv_text=CV_SAMPLE))
    fetched = get_match_results(created.session_id)
    assert fetched.session_id == created.session_id
    assert len(fetched.jobs) == len(created.jobs)
