import threading
from typing import NamedTuple

import numpy as np

from process.embedding import generate_embedding, get_model
from database.data import get_filtered_official_documents
from database.embedded_data import get_all_chunks

from process.query_understanding import understand_query

MIN_SCORE = 0.80
SCORE_MARGIN = 0.03

FILTER_KEYS = (
    "document_number",
    "signing_from", "signing_to",
    "effective_from", "effective_to",
    "deadline_from", "deadline_to",
)


class SearchResult(NamedTuple):
    files: list
    scores: dict
    snippets: dict
    semantic: bool

def warm_up_model():
    threading.Thread(target=get_model, daemon=True).start()


def has_official_filter(filters):
    return bool(filters) and any(filters.get(key) for key in FILTER_KEYS)


def semantic_search(query, top_k=20, min_score=MIN_SCORE,
                    margin=SCORE_MARGIN, allowed_ids=None):

    query_vec = generate_embedding(query, is_query=True)
    if query_vec is None:
        return []

    rows = get_all_chunks()

    if allowed_ids is not None:
        allowed = set(allowed_ids)
        rows = [row for row in rows if row[0] in allowed]

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

    # Threshold
    cutoff = max(min_score, results[0]["score"] - margin)
    results = [r for r in results if r["score"] >= cutoff]

    return results[:top_k]


def _official_ids(filters):
    rows = get_filtered_official_documents(
        **{key: filters.get(key) for key in FILTER_KEYS}
    )
    return {row[0] for row in rows}


def search_documents(files, query="", mode="name", file_type=None,
                     filters=None, top_k=20):
    query = (query or "").strip()

    if file_type:
        files = [f for f in files if f["extension"] == file_type]

    official_ids = None
    if has_official_filter(filters):
        official_ids = _official_ids(filters)

    if mode == "content" and query:
        allowed = {f["id"] for f in files}
        if official_ids is not None:
            allowed &= official_ids

        if not allowed:
            return SearchResult([], {}, {}, True)

        # Understand query
        query = understand_query(query)
        print("Processed query: ", query)
        
        hits = semantic_search(query, top_k=top_k, allowed_ids=allowed)

        files_by_id = {f["id"]: f for f in files}
        return SearchResult(
            [files_by_id[h["document_id"]] for h in hits],
            {h["document_id"]: h["score"] for h in hits},
            {h["document_id"]: h["snippet"] for h in hits},
            True
        )

    keyword = query.lower()
    results = [
        f for f in files
        if (not keyword or keyword in f["name"].lower())
        and (official_ids is None or f["id"] in official_ids)
    ]

    return SearchResult(results, {}, {}, False)