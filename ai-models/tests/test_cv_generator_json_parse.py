"""Tests for CV generation JSON parsing."""

import pytest

from cv_generator.json_parse import parse_cv_json


def test_parse_cv_json_strips_fences():
    raw = '```json\n{"summary": "Hello", "skills": {"backend": ["Python"]}}\n```'
    data = parse_cv_json(raw)
    assert data["summary"] == "Hello"


def test_parse_cv_json_repairs_trailing_comma():
    raw = '{"summary": "Hi", "skills": [],}'
    data = parse_cv_json(raw)
    assert data["summary"] == "Hi"


def test_parse_cv_json_raises_on_empty():
    with pytest.raises(Exception):
        parse_cv_json("")
