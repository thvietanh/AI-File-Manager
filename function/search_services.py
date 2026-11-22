import numpy as np

from process.embedding import generate_embedding
from database.embedded_data import get_all_chunks

MIN_SCORE = 0.8

def semantic_search(query, top_k=20, min_score=MIN_SCORE):

    query_vec = generate_embedding(query, is_query=True)
    if query_vec is None:
        return []

    rows = get_all_chunks()
    if not rows:
        return []

    matrix = np.vstack([
        np.frombuffer(row[3], dtype=np.float32) for row in rows
    ])

    scores = matrix @ query_vec

    best = {}
    for row, score in zip(rows, scores):
        doc_id = row[0]
        if doc_id not in best or score > best[doc_id]["score"]:
            best[doc_id] = {
                "document_id": doc_id,
                "score": float(score),
                "snippet": row[2][:200],
            }

    results = sorted(best.values(), key=lambda r: r["score"], reverse=True)
    results = [r for r in results if r["score"] >= min_score]
    return results[:top_k]