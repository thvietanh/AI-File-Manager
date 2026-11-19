from process.chunking import split_text
from process.embedding import generate_embedding

def process_document(text):
    # Chunking
    chunks = split_text(
        text,
        chunk_size = 1500,
        overlap = 200
    )

    results = []

    # Embedding
    for index, chunk in enumerate(chunks):
        embedding = generate_embedding(chunk)

        results.append({
            "chunk_index": index,
            "content": chunk,
            "embedding": embedding
        })

    return results
