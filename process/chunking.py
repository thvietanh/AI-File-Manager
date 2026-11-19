def split_text(text, chunk_size = 1500, overlap = 200):
    if not text or not text.strip():
        return []

    if overlap >= chunk_size:
        raise ValueError("overlap must be lower than chunk_size")

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks