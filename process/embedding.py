from sentence_transformers import SentenceTransformer as st

# Sentence transformers model

model = st("intfloat/multilingual-e5-small")

def generate_embedding(text, is_query = False):
    if not text or not text.strip():
        return None

    # Prefix
    if is_query:
        text = "query: " + text
    else:
        text = "passage: " + text

    # Convert to vector
    embedding = model.encode(
        text,
        normalize_embeddings = True
    )

    return embedding