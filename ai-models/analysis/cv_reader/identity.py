"""Lightweight regex-based metadata extraction from CV text (display only)."""

import re

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(\+?\d[\d\s().-]{7,}\d)")


def extract_identity(cv_text: str) -> dict:
    lines = [l.strip() for l in cv_text.splitlines() if l.strip()]

    name = _guess_name(lines)
    email_match = EMAIL_RE.search(cv_text)
    phone_match = PHONE_RE.search(cv_text)

    return {
        "name": name,
        "email": email_match.group(0) if email_match else "",
        "phone": phone_match.group(0).strip() if phone_match else "",
    }


def _guess_name(lines: list) -> str:
    for line in lines[:5]:
        words = line.split()
        if 1 < len(words) <= 4 and all(w.replace("-", "").isalpha() for w in words):
            return line
    return ""
