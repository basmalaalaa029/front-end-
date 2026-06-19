"""Instant template fill — no AI."""

from __future__ import annotations

from cv_generator.markdown import cv_data_to_markdown
from cv_generator.models.cv_schema import CVData


def fill_template(cv_data: CVData) -> dict:
    """Instantly fill template with raw user data. No AI — returns immediately."""
    markdown = cv_data_to_markdown(cv_data)
    return {
        "status": "success",
        "data": cv_data.model_dump(),
        "markdown": markdown,
        "version": "template",
    }
