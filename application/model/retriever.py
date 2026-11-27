"""Dynamic semantic retriever for the Interface Library.

Encodes all interface descriptions into FAISS and retrieves the most
relevant existing interfaces for a given query. Rebuilt whenever a new
interface is added to the library.
"""

from __future__ import annotations

import time
from typing import Any

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from logger import get_logger, truncate_payload

logger = get_logger(__name__)


class ToolRetriever:
    """FAISS-backed semantic search over the dynamic interface library."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.encoder = SentenceTransformer(model_name)
        self._tools: list[dict[str, str]] = []
        self._embeddings: np.ndarray | None = None
        self._index: faiss.IndexFlatIP | None = None
        logger.info("ToolRetriever initialized")

    def rebuild(self, tools: list[dict[str, str]]) -> None:
        """Rebuild the FAISS index from current interface descriptions."""
        if not tools:
            self._tools = []
            self._index = None
            return

        self._tools = tools
        descriptions = [t["description"] for t in tools]
        self._embeddings = self.encoder.encode(
            descriptions,
            normalize_embeddings=True,
            convert_to_numpy=True,
        ).astype(np.float32)

        dim = self._embeddings.shape[1]
        self._index = faiss.IndexFlatIP(dim)
        self._index.add(self._embeddings)
        logger.info("FAISS index rebuilt | interfaces=%d", len(tools))

    def retrieve(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Return top-k most relevant interfaces for the query."""
        if self._index is None or not self._tools:
            logger.warning("Retriever index is empty; returning 0 matches for query=%s", truncate_payload(query, 200))
            return []

        start = time.perf_counter()
        query_vec = self.encoder.encode(
            [query], normalize_embeddings=True, convert_to_numpy=True
        ).astype(np.float32)

        k = min(top_k, len(self._tools))
        scores, indices = self._index.search(query_vec, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0:
                results.append({
                    "tool": self._tools[idx],
                    "score": float(score),
                })

        duration_ms = (time.perf_counter() - start) * 1000
        top_summary = [(r["tool"]["name"], round(r["score"], 4)) for r in results]
        logger.info(
            "Retrieval complete | matches=%d | top=%s | duration=%.1fms | query=%s",
            len(results),
            top_summary,
            duration_ms,
            truncate_payload(query, 200),
        )
        return results

    def best_match(self, query: str, threshold: float = 0.55) -> dict[str, str] | None:
        """Return the single best matching interface if above similarity threshold."""
        results = self.retrieve(query, top_k=1)
        if results and results[0]["score"] >= threshold:
            logger.debug(
                "Best match accepted | tool=%s | score=%.4f >= threshold=%.2f",
                results[0]["tool"]["name"],
                results[0]["score"],
                threshold,
            )
            return results[0]["tool"]
        logger.debug(
            "No match above threshold=%.2f (top_score=%.4f)",
            threshold,
            results[0]["score"] if results else 0.0,
        )
        return None
