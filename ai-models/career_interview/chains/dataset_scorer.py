"""
dataset_scorer.py
=================
Scores a candidate's answer against a dataset of ideal answers using
semantic similarity (cosine similarity on embeddings).

Architecture:
- Built-in datasets live in dataset/{role}.json and dataset/general.json
- Custom datasets uploaded by the user live in dataset/custom/{user_id}.json
- At session start, the relevant datasets are loaded and embeddings pre-computed
- At evaluation time, the best matching ideal answer is found via cosine similarity
- The dataset score (0–10) blends with the LLM score: final = LLM*0.65 + dataset*0.35

Similarity → dataset score mapping:
  >= 0.85  → 9–10  (near-identical coverage)
  >= 0.70  → 7–8   (strong conceptual overlap)
  >= 0.55  → 5–6   (partial overlap)
  >= 0.40  → 3–4   (some relevant concepts)
  <  0.40  → 1–2   (little to no overlap)
"""

import os
import json
import logging
import numpy as np
from typing import List, Dict, Optional, Tuple

log = logging.getLogger("dataset_scorer")

DATASET_DIR  = os.path.join(os.path.dirname(__file__), "..", "dataset")
CUSTOM_DIR   = os.path.join(DATASET_DIR, "custom")
os.makedirs(CUSTOM_DIR, exist_ok=True)

# Role key → dataset file mapping
ROLE_DATASET_MAP = {
    "ml_engineer":         "ml_engineer.json",
    "data_scientist":      "data_scientist.json",
    "backend_developer":   "backend_developer.json",
    "fullstack_developer": "backend_developer.json",  # reuse backend
    "frontend_developer":  "general.json",
    "devops_engineer":     "general.json",
    "data_analyst":        "data_scientist.json",
    "other":               "general.json",
}


# ── Embedding ──────────────────────────────────────────────────────────────

def _get_embedding(text: str, ollama_url: str = "http://localhost:11434") -> Optional[np.ndarray]:
    """
    Get a single embedding via Ollama's /api/embeddings endpoint.
    Returns None on failure.
    """
    try:
        import requests
        resp = requests.post(
            f"{ollama_url}/api/embeddings",
            json={"model": "nomic-embed-text", "prompt": text[:1000]},
            timeout=10,
        )
        if resp.status_code == 200:
            vec = resp.json().get("embedding", [])
            if vec:
                return np.array(vec, dtype=np.float32)
        log.warning(f"Ollama embedding returned status {resp.status_code}")
        return None
    except Exception as e:
        log.warning(f"Embedding failed: {e}")
        return None


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors. Returns 0.0 on error."""
    try:
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
    except Exception:
        return 0.0


# ── Keyword fallback scorer (no Ollama needed) ─────────────────────────────

def _keyword_overlap_score(answer: str, entry: dict) -> float:
    """
    Fast keyword-based fallback when embeddings are unavailable.
    Checks how many key_concepts appear in the answer.
    Returns 0.0–1.0.
    """
    concepts = entry.get("key_concepts", [])
    if not concepts:
        # Fall back to word overlap with ideal answer
        ideal_words = set(entry.get("ideal_answer", "").lower().split())
        answer_words = set(answer.lower().split())
        if not ideal_words:
            return 0.0
        return len(ideal_words & answer_words) / max(len(ideal_words), 1)

    answer_lower = answer.lower()
    matched = sum(1 for c in concepts if c.lower() in answer_lower)
    return matched / len(concepts)


def _overlap_to_score(overlap: float) -> float:
    """Map keyword overlap (0–1) to a 0–10 score."""
    if overlap >= 0.75: return 9.0
    if overlap >= 0.55: return 7.5
    if overlap >= 0.35: return 5.5
    if overlap >= 0.20: return 3.5
    return 2.0


def _similarity_to_score(similarity: float) -> float:
    """Map cosine similarity (0–1) to a 0–10 dataset score."""
    if similarity >= 0.88: return 9.5
    if similarity >= 0.80: return 8.5
    if similarity >= 0.70: return 7.0
    if similarity >= 0.58: return 5.5
    if similarity >= 0.45: return 3.5
    if similarity >= 0.30: return 2.0
    return 1.0


# ── Dataset loading ────────────────────────────────────────────────────────

def load_dataset(role: str, user_id: str = "") -> List[dict]:
    """
    Load the relevant dataset entries for a role.
    Merges: role-specific built-in + general + custom (if uploaded).
    """
    entries = []

    # 1. Role-specific built-in
    role_file = ROLE_DATASET_MAP.get(role, "general.json")
    role_path = os.path.join(DATASET_DIR, role_file)
    if os.path.exists(role_path):
        try:
            with open(role_path, encoding="utf-8") as f:
                entries.extend(json.load(f))
        except Exception as e:
            log.warning(f"Could not load built-in dataset {role_path}: {e}")

    # 2. General (always included, avoid duplicating if same file)
    general_path = os.path.join(DATASET_DIR, "general.json")
    if os.path.exists(general_path) and role_file != "general.json":
        try:
            with open(general_path, encoding="utf-8") as f:
                entries.extend(json.load(f))
        except Exception as e:
            log.warning(f"Could not load general dataset: {e}")

    # 3. Custom dataset for this user
    if user_id:
        custom_path = os.path.join(CUSTOM_DIR, f"{user_id}.json")
        if os.path.exists(custom_path):
            try:
                with open(custom_path, encoding="utf-8") as f:
                    custom = json.load(f)
                    entries.extend(custom)
                    log.info(f"Loaded {len(custom)} custom entries for user {user_id}")
            except Exception as e:
                log.warning(f"Could not load custom dataset for {user_id}: {e}")

    log.info(f"Dataset loaded: {len(entries)} entries for role={role}, user={user_id}")
    return entries


def save_custom_dataset(user_id: str, entries: List[dict]) -> Tuple[bool, str]:
    """
    Validate and save a custom dataset for a user.
    Returns (success, message).
    """
    if not entries:
        return False, "Dataset is empty."
    if len(entries) > 500:
        return False, "Dataset too large (max 500 entries)."

    validated = []
    for i, e in enumerate(entries):
        if not isinstance(e, dict):
            return False, f"Entry {i}: must be a JSON object."
        if "ideal_answer" not in e:
            return False, f"Entry {i}: missing required field 'ideal_answer'."
        if len(e.get("ideal_answer", "")) < 20:
            return False, f"Entry {i}: 'ideal_answer' is too short (min 20 chars)."
        validated.append({
            "competency":       e.get("competency", "general"),
            "question_keywords": e.get("question_keywords", []),
            "ideal_answer":     e["ideal_answer"][:2000],
            "key_concepts":     e.get("key_concepts", []),
            "source":           "custom",
        })

    path = os.path.join(CUSTOM_DIR, f"{user_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(validated, f, indent=2)

    return True, f"Saved {len(validated)} entries."


# ── Pre-compute embeddings for a dataset ──────────────────────────────────

def precompute_dataset_embeddings(
    entries: List[dict],
    ollama_url: str = "http://localhost:11434",
) -> List[dict]:
    """
    Embed the ideal_answer of each entry.
    Adds 'embedding' key (np.ndarray or None) to each entry dict.
    Entries where embedding fails keep embedding=None and fall back to keyword scoring.
    """
    log.info(f"Pre-computing embeddings for {len(entries)} dataset entries...")
    enriched = []
    for entry in entries:
        e = dict(entry)
        text = e.get("ideal_answer", "")
        if text:
            e["embedding"] = _get_embedding(text, ollama_url)
        else:
            e["embedding"] = None
        enriched.append(e)

    embedded_count = sum(1 for e in enriched if e["embedding"] is not None)
    log.info(f"Embeddings computed: {embedded_count}/{len(entries)} succeeded")
    return enriched


# ── Core scoring function ──────────────────────────────────────────────────

def score_against_dataset(
    answer: str,
    question: str,
    competency: str,
    dataset_entries: List[dict],
    ollama_url: str = "http://localhost:11434",
) -> Dict:
    """
    Score a candidate's answer against the dataset.

    Returns:
    {
        "dataset_score":     float (0–10),
        "similarity":        float (0–1),
        "best_match_competency": str,
        "matched_concepts":  list[str],
        "missing_concepts":  list[str],
        "scoring_method":    "embedding" | "keyword",
        "available":         bool,
    }
    """
    if not dataset_entries or not answer.strip():
        return {
            "dataset_score": None,
            "similarity": 0.0,
            "best_match_competency": "",
            "matched_concepts": [],
            "missing_concepts": [],
            "scoring_method": "none",
            "available": False,
        }

    # Filter to competency-relevant entries first, fall back to all if none match
    def _competency_match(entry):
        ec = entry.get("competency", "").lower()
        comp = competency.lower()
        return ec == comp or ec in comp or comp in ec

    relevant = [e for e in dataset_entries if _competency_match(e)]
    if not relevant:
        # Try keyword match on the question
        q_lower = question.lower()
        relevant = [
            e for e in dataset_entries
            if any(kw.lower() in q_lower for kw in e.get("question_keywords", []))
        ]
    if not relevant:
        relevant = dataset_entries  # no filter — compare against everything

    # Get answer embedding
    answer_emb = _get_embedding(answer[:1200], ollama_url)

    best_score   = 0.0
    best_sim     = 0.0
    best_entry   = relevant[0]
    method       = "keyword"

    if answer_emb is not None:
        # Embedding path
        method = "embedding"
        for entry in relevant:
            ideal_emb = entry.get("embedding")
            if ideal_emb is None:
                # Embed on-demand if not pre-computed
                ideal_emb = _get_embedding(entry.get("ideal_answer", "")[:1200], ollama_url)
                entry["embedding"] = ideal_emb

            if ideal_emb is not None:
                sim = _cosine_similarity(answer_emb, ideal_emb)
                if sim > best_sim:
                    best_sim = sim
                    best_entry = entry
                    best_score = _similarity_to_score(sim)
    else:
        # Keyword fallback
        for entry in relevant:
            overlap = _keyword_overlap_score(answer, entry)
            if overlap > best_sim:
                best_sim = overlap
                best_entry = entry
                best_score = _overlap_to_score(overlap)

    # Concept coverage analysis
    concepts = best_entry.get("key_concepts", [])
    answer_lower = answer.lower()
    matched = [c for c in concepts if c.lower() in answer_lower]
    missing = [c for c in concepts if c.lower() not in answer_lower]

    return {
        "dataset_score":         round(best_score, 1),
        "similarity":            round(best_sim, 3),
        "best_match_competency": best_entry.get("competency", ""),
        "matched_concepts":      matched,
        "missing_concepts":      missing[:5],  # top 5 missing for feedback
        "scoring_method":        method,
        "available":             True,
    }


# ── Blended score ──────────────────────────────────────────────────────────

LLM_WEIGHT     = 0.65
DATASET_WEIGHT = 0.35

def blend_scores(llm_score: float, dataset_result: dict) -> Tuple[float, str]:
    """
    Blend LLM score with dataset score.
    Returns (blended_score, explanation_string).

    If dataset scoring is unavailable, returns the LLM score unchanged.
    """
    if not dataset_result.get("available") or dataset_result.get("dataset_score") is None:
        return llm_score, "LLM only (no dataset match found)"

    dataset_score = dataset_result["dataset_score"]
    blended = round(
        (llm_score * LLM_WEIGHT) + (dataset_score * DATASET_WEIGHT),
        1
    )
    blended = max(0.0, min(10.0, blended))

    method  = dataset_result.get("scoring_method", "keyword")
    sim_pct = int(dataset_result.get("similarity", 0) * 100)
    missing = dataset_result.get("missing_concepts", [])

    explanation = (
        f"LLM score: {llm_score}/10 ({int(LLM_WEIGHT*100)}%) + "
        f"Dataset score: {dataset_score}/10 ({int(DATASET_WEIGHT*100)}%, "
        f"{sim_pct}% similarity via {method}) = {blended}/10"
    )
    if missing:
        explanation += f". Missing concepts: {', '.join(missing)}"

    return blended, explanation
