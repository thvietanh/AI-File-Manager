from process.embedding import generate_embedding

text = """
Công văn yêu cầu các đơn vị hoàn thành báo cáo
trước ngày 30 tháng 11 năm 2026.
"""

vector = generate_embedding(text)

if vector is not None:
    print("Embedding completed!")
    print("Dim", len(vector))
    print("Vector:")
    print(vector)
