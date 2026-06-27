import json, re, logging

log = logging.getLogger("parser")


def parse_json_output(text: str) -> dict:
    if not text or not text.strip():
        log.error("[parser] Empty output from LLM")
        raise ValueError("Empty output from LLM.")

    cleaned = text.strip()

    # Strip markdown fences
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    # Extract first {...} block
    match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)

    # Remove trailing commas
    cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)

    try:
        result = json.loads(cleaned)
        log.debug(f"[parser] Parsed OK, keys: {list(result.keys())[:8]}")
        return result
    except json.JSONDecodeError as e1:
        log.warning(f"[parser] First parse failed: {e1} — trying newline fix")
        cleaned2 = re.sub(r'(?<!\\)\n', ' ', cleaned)
        try:
            result = json.loads(cleaned2)
            log.info("[parser] Parsed after newline fix")
            return result
        except json.JSONDecodeError as e2:
            log.warning(f"[parser] Second parse failed: {e2} — trying truncated JSON fix")
            cleaned3 = _close_truncated_json(cleaned2)
            try:
                result = json.loads(cleaned3)
                log.info("[parser] Parsed after truncation fix")
                return result
            except json.JSONDecodeError as e3:
                # Last resort: regex extraction — LOG the raw response for debugging
                log.error(f"[parser] ALL JSON parses failed. Raw LLM output:\n{text[:500]}")
                score_m = re.search(r'"score"\s*:\s*([\d.]+)', cleaned)
                feedback_m = re.search(r'"feedback"\s*:\s*"([^"]{5,})"', cleaned)
                if score_m:
                    log.warning(f"[parser] Regex fallback — score={score_m.group(1)}")
                    return {
                        "score": float(score_m.group(1)),
                        "technical_accuracy": float(score_m.group(1)),
                        "feedback": feedback_m.group(1) if feedback_m else "Evaluation completed.",
                        "improvements": [],
                        "correctness_note": "", "clarity_note": "",
                        "depth_note": "", "confidence_note": "",
                        "soft_skill_notes": "",
                        "soft_scores": {"communication":5,"confidence":5,"problem_solving":5,"honesty":5},
                        "bluff_detected": False,
                        "uncertainty_detected": False,
                        "uncertainty_type": "none",
                        "unverified_claims": [],
                    }
                log.error(f"[parser] Cannot extract any score. Full raw:\n{text}")
                raise ValueError(f"Cannot parse JSON from LLM output. Raw: {text[:300]}")


def _close_truncated_json(s: str) -> str:
    depth_brace   = s.count('{') - s.count('}')
    depth_bracket = s.count('[') - s.count(']')
    in_string = False
    escape_next = False
    for ch in s:
        if escape_next: escape_next = False; continue
        if ch == '\\': escape_next = True; continue
        if ch == '"' and not escape_next: in_string = not in_string
    if in_string: s += '"'
    s += ']' * max(0, depth_bracket)
    s += '}' * max(0, depth_brace)
    return s
