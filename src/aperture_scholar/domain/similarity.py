"""Deterministic vector operations independent of embedding providers."""

import math
from collections.abc import Sequence


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    """Reject invalid vectors rather than silently accepting dimension mismatches."""
    if not left or len(left) != len(right):
        raise ValueError("vectors must have equal, nonzero dimensions")
    if not all(math.isfinite(x) for x in (*left, *right)):
        raise ValueError("vector components must be finite")
    # Normalize separately to avoid overflow from a product of large norms.
    left_norm, right_norm = math.hypot(*left), math.hypot(*right)
    if left_norm == 0 or right_norm == 0:
        raise ValueError("zero vectors do not have cosine similarity")
    value = sum((a / left_norm) * (b / right_norm) for a, b in zip(left, right, strict=True))
    return max(-1.0, min(1.0, value))


def deduplicate_vectors(vectors: Sequence[Sequence[float]], threshold: float) -> list[int]:
    """Stable greedy selection; return indices into the original input."""
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between zero and one")
    kept: list[int] = []
    for index, vector in enumerate(vectors):
        cosine_similarity(vector, vector)
        if not any(cosine_similarity(vector, vectors[k]) >= threshold for k in kept):
            kept.append(index)
    return kept
