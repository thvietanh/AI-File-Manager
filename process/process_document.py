from process.chunking import split_text
from process.embedding import generate_embeddings

def process_document(text):
    chunks = split_text(text, chunk_size=800, overlap=100)

    if not chunks:
        return []

    embeddings = generate_embeddings(chunks)

    return [
        {
            "chunk_index": index,
            "content": chunk,
            "embedding": embedding
        }
        for index, (chunk, embedding) in enumerate(zip(chunks, embeddings))
    ]