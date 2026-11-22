import re

def split_text(text, chunk_size=800, overlap=100):
    if not text or not text.strip():
        return []

    if overlap >= chunk_size:
        raise ValueError("overlap must be lower than chunk_size")

    units = []
    for line in re.split(r"\n+", text):
        line = line.strip()
        while len(line) > chunk_size:
            units.append(line[:chunk_size])
            line = line[chunk_size:]
        if line:
            units.append(line)

    chunks = []
    current = ""

    for unit in units:
        if current and len(current) + len(unit) + 1 > chunk_size:
            chunks.append(current)
            tail = current[-overlap:]
            tail = tail[tail.find(" ") + 1:] if " " in tail else ""
            current = (tail + " " + unit).strip()
        else:
            current = (current + " " + unit) if current else unit

    if current:
        chunks.append(current)

    return chunks