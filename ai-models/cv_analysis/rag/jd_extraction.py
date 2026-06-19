"""
cv_agent.rag
============
RAG Module — FAISS embedding retrieval + TF-IDF fallback + regex keyword extraction.
"""

from __future__ import annotations

import json
import re
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from cv_agent.app.config import logger, _SKLEARN_AVAILABLE, _FAISS_AVAILABLE, _SENTENCE_AVAILABLE
from cv_analysis.config import CVAnalysisConfig, get_cv_analysis_config
from cv_analysis.judges.schemas import JDContext
from cv_analysis.judges.utils import jd_hash as _jd_hash


class RAGModule:
    """Retrieval-Augmented Generation module with FAISS + TF-IDF + regex fallback."""

    REQUIREMENT_PATTERNS = [
        r"(?:required|must have|mandatory)[:\s]+([^\.\n]{10,80})",
        r"(\d+\+?\s+years?[^\.\n]{0,50})",
        r"(?:bachelor|master|phd|degree)[^\.\n]{0,60}",
    ]

    def __init__(self, ontology_path: str = "") -> None:
        self.ontology: Dict[str, List[str]] = {}
        if ontology_path and Path(ontology_path).exists():
            with open(ontology_path) as f:
                self.ontology = json.load(f)

        self._embed_model: Any = None
        self._embed_lock = threading.Lock()
        self._index_cache: Dict[str, Any] = {}
        self._chunk_cache: Dict[str, List[str]] = {}

    def _get_embed_model(self, cfg_model: str = "all-MiniLM-L6-v2") -> Optional[Any]:
        if not _SENTENCE_AVAILABLE or not _FAISS_AVAILABLE:
            return None
        if self._embed_model is None:
            with self._embed_lock:
                if self._embed_model is None:
                    try:
                        from sentence_transformers import SentenceTransformer
                        self._embed_model = SentenceTransformer(cfg_model)
                        logger.info("RAG: SentenceTransformer loaded (%s)", cfg_model)
                    except Exception as e:
                        logger.warning("RAG: embedding model load failed: %s", e)
        return self._embed_model

    def _build_faiss_index(self, chunks: List[str], model: Any, jd_h: str) -> Any:
        import faiss
        import numpy as np
        vecs = model.encode(chunks, normalize_embeddings=True, show_progress_bar=False)
        dim = vecs.shape[1]
        idx = faiss.IndexFlatIP(dim)
        idx.add(vecs.astype(np.float32))
        self._index_cache[jd_h] = idx
        self._chunk_cache[jd_h] = chunks
        return idx

    def extract(self, jd_text: str, target_role: str, cfg: Optional[CVAnalysisConfig] = None) -> JDContext:
        if not jd_text.strip():
            return JDContext()
        keywords = self._extract_keywords(jd_text, cfg)
        requirements = self._extract_requirements(jd_text)
        canonical = self._ontology_align(keywords, target_role)
        return JDContext(keywords=keywords, requirements=requirements, canonical_skills=canonical)

    def semantic_search(
        self, query: str, jd_text: str, top_k: int = 5,
        cfg: Optional[CVAnalysisConfig] = None,
    ) -> List[str]:
        model = self._get_embed_model(cfg.embedding_model if cfg else "all-MiniLM-L6-v2")
        if model is None:
            return []
        import numpy as np
        h = _jd_hash(jd_text)
        if h not in self._index_cache:
            sentences = [s.strip() for s in re.split(r'[.\n]+', jd_text) if len(s.strip()) > 20]
            if not sentences:
                return []
            try:
                self._build_faiss_index(sentences, model, h)
            except Exception as e:
                logger.warning("FAISS index build failed: %s", e)
                return []
        try:
            q_vec = model.encode([query], normalize_embeddings=True, show_progress_bar=False)
            idx = self._index_cache[h]
            chunks = self._chunk_cache[h]
            _, ids = idx.search(q_vec.astype(np.float32), min(top_k, len(chunks)))
            return [chunks[i] for i in ids[0] if 0 <= i < len(chunks)]
        except Exception as e:
            logger.warning("FAISS search failed: %s", e)
            return []

    def _extract_keywords(self, text: str, cfg: Optional[CVAnalysisConfig] = None) -> List[str]:
        # TF-IDF first — do not load SentenceTransformer unless semantic_search needs it.
        if _SKLEARN_AVAILABLE:
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer
                vec = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", max_features=40)
                mat = vec.fit_transform([text])
                scores = zip(vec.get_feature_names_out(), mat.toarray()[0])
                return [w for w, _ in sorted(scores, key=lambda x: -x[1])[:30]]
            except Exception:
                pass

        logger.info("RAG: falling back to regex keyword extraction")
        tokens = re.findall(r'\b[A-Z][a-zA-Z+#]{2,}\b|\b(?:python|sql|aws|ml|ai|api)\b', text)
        seen: Dict[str, int] = {}
        for t in tokens:
            seen[t.lower()] = seen.get(t.lower(), 0) + 1
        return [k for k, _ in sorted(seen.items(), key=lambda x: -x[1])[:30]]

    def _extract_requirements(self, text: str) -> List[str]:
        reqs: List[str] = []
        for pat in self.REQUIREMENT_PATTERNS:
            reqs.extend(re.findall(pat, text, re.IGNORECASE))
        return [r.strip() for r in reqs[:10]]

    def _ontology_align(self, keywords: List[str], role: str) -> List[str]:
        canonical: List[str] = []
        role_key = role.lower()
        for k, skills in self.ontology.items():
            if k.lower() in role_key or role_key in k.lower():
                canonical.extend(skills)
        kw_lower = {k.lower() for k in keywords}
        return [s for s in canonical if any(s.lower() in kw for kw in kw_lower)][:15]
