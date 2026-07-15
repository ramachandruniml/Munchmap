import math

from app.services.personalization import build_preference_vector, cosine_similarity


def test_build_preference_vector_returns_none_with_no_ratings() -> None:
    assert build_preference_vector([], []) is None


def test_build_preference_vector_liked_only() -> None:
    vector = build_preference_vector([[1.0, 0.0], [0.0, 1.0]], [])

    assert vector == [0.5, 0.5]


def test_build_preference_vector_subtracts_disliked() -> None:
    vector = build_preference_vector([[1.0, 0.0]], [[0.0, 1.0]])

    assert vector == [1.0, -1.0]


def test_cosine_similarity_identical_vectors() -> None:
    assert math.isclose(cosine_similarity([1.0, 0.0], [1.0, 0.0]), 1.0)


def test_cosine_similarity_orthogonal_vectors() -> None:
    assert math.isclose(cosine_similarity([1.0, 0.0], [0.0, 1.0]), 0.0)


def test_cosine_similarity_zero_vector_is_zero() -> None:
    assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0
