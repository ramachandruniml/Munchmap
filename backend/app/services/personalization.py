def _mean(vectors: list[list[float]], dim: int) -> list[float]:
    if not vectors:
        return [0.0] * dim
    return [sum(v[i] for v in vectors) / len(vectors) for i in range(dim)]


def build_preference_vector(
    liked: list[list[float]], disliked: list[list[float]]
) -> list[float] | None:
    """Mean of liked embeddings minus mean of disliked embeddings.

    Returns None when there are no ratings to build a preference from.
    """
    if not liked and not disliked:
        return None
    dim = len(liked[0]) if liked else len(disliked[0])
    liked_mean = _mean(liked, dim)
    disliked_mean = _mean(disliked, dim)
    return [liked_v - disliked_v for liked_v, disliked_v in zip(liked_mean, disliked_mean)]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
