from functools import lru_cache

MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache
def _model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


def embed_text(text: str) -> list[float]:
    return _model().encode(text, normalize_embeddings=True).tolist()


def recipe_embedding_text(name: str, diet_tags: list[str], ingredient_names: list[str]) -> str:
    return ", ".join([name, *diet_tags, *ingredient_names])
