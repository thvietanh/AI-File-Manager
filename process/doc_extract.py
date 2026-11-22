from pathlib import Path
import pymupdf
import re
from docx import Document


def extract(file_path):
    path = Path(file_path)
    extension = path.suffix.lower()

    if extension == ".txt":
        return path.read_text(
            encoding="utf-8",
            errors="replace"
        )

    elif extension == ".pdf":
        with pymupdf.open(file_path) as pdf:
            return "\n".join(
                page.get_text() for page in pdf
            )

    elif extension == ".docx":
        doc = Document(file_path)

        paragraphs = [
            p.text for p in doc.paragraphs
        ]

        return "\n".join(paragraphs)

    else:
        raise ValueError("Định dạng file không được hỗ trợ")

DATE = (
    r"(\d{1,2}\s*[/-]\s*\d{1,2}\s*[/-]\s*\d{4}"
    r"|\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4})"
)


def to_ddmmyyyy(text):
    match = (
        re.search(r"(\d{1,2})\s*[/-]\s*(\d{1,2})\s*[/-]\s*(\d{4})", text)
        or re.search(r"(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})", text)
    )
    if not match:
        return None

    day, month, year = match.groups()
    if not (1 <= int(day) <= 31 and 1 <= int(month) <= 12):
        return None

    return f"{day.zfill(2)}/{month.zfill(2)}/{year}"


def official_extract(content):
    if not content:
        return None

    # Chuẩn hóa khoảng trắng và cách viết "HOÀ" / "HÒA"
    header = re.sub(r"\s+", " ", content.upper()).replace("HOÀ", "HÒA")
    if "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM" not in header:
        return None

    metadata = {
        "document_number": None,
        "signing_date": None,
        "effective_date": None,
        "deadline_date": None,
    }

    patterns = {
        "document_number": r"Số\s*:\s*([0-9]+(?:/[A-ZĐ0-9-]+)+)",
        "signing_date": r"ngày\s+(\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4})",
        "effective_date": (
            r"có hiệu lực(?: thi hành)?\s+(?:kể từ ngày|từ ngày)\s+" + DATE
        ),
        "deadline_date": (
            r"(?:hạn cuối|chậm nhất|trước ngày)\s+" + DATE
        ),
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, content, re.IGNORECASE)
        if not match:
            continue

        if key == "document_number":
            metadata[key] = match.group(1)
        else:
            metadata[key] = to_ddmmyyyy(match.group(1))

    # Văn bản không có số hiệu (hợp đồng, đơn từ...) thì không coi là công văn
    if not metadata["document_number"]:
        return None

    return metadata 