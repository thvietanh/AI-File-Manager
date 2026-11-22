from sentence_transformers import SentenceTransformer
import threading

MODEL_NAME = "intfloat/multilingual-e5-base"
_model = None
_lock = threading.Lock()

def get_model():
    global _model
    with _lock:
        if _model is None:
                _model = SentenceTransformer(MODEL_NAME)
    return _model

def generate_embedding(text, is_query=False):
    if not text or not text.strip():
        return None

    prefix = "query: " if is_query else "passage: "

    return get_model().encode(
        prefix + text,
        normalize_embeddings=True
    )

def generate_embeddings(texts, is_query=False, batch_size=32):
    if not texts:
        return []

    prefix = "query: " if is_query else "passage: "

    return get_model().encode(
        [prefix + t for t in texts],
        batch_size=batch_size,
        normalize_embeddings=True
    )