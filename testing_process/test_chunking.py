from process.chunking import split_text

text = """
Trường Đại học Bách khoa Hà Nội thông báo
về việc tổ chức kỳ thi cuối kỳ.

Sinh viên cần hoàn thành các thủ tục
đăng ký dự thi theo đúng thời hạn.

Các đơn vị đào tạo có trách nhiệm
kiểm tra và tổng hợp danh sách sinh viên.
""" * 30

chunks = split_text(text)

print("Number of chunks", len(chunks))

for i, chunk in enumerate(chunks):
    print(f"\nChunk {i + 1}:")
    print(chunk[:100])
    print("Length:", len(chunk))