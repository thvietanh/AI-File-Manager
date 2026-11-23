import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from process.doc_extract import extract
from process.chunking import split_text
from process.embedding import generate_embedding, generate_embeddings

FOLDER = sys.argv[1]

QUERIES = [
    "quy định nghỉ phép",
    "tiền đặt cọc thuê nhà",
    "sân bay Long Thành",
    "mức thu tiền sử dụng khu vực biển",
    "công báo điện tử",
    "thủ tục hành chính",
    "hôm nay trời đẹp",
]

names, vectors = [], []
for name in sorted(os.listdir(FOLDER)):
    try:
        text = extract(os.path.join(FOLDER, name))
    except Exception:
        continue
    chunks = split_text(text)
    for vec in generate_embeddings(chunks):
        names.append(name)
        vectors.append(vec)

matrix = np.vstack(vectors)

for query in QUERIES:
    scores = matrix @ generate_embedding(query, is_query=True)
    best = {}
    for name, score in zip(names, scores):
        best[name] = max(best.get(name, 0.0), float(score))

    print(f"\n[{query}]")
    for name, score in sorted(best.items(), key=lambda x: -x[1])[:5]:
        print(f"  {score:.3f}  {name}")