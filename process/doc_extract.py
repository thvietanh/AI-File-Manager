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

def official_extract(content):
    if not content:
        return None

    content_upper = content.upper()
    if "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM" not in content_upper:
        return None

    metadata = {
        "document_number": None,
        "signing_date": None,
        "effective_date": None,
        "deadline_date": None
    }


    # 123/QĐ-UBND, 45/2026/NĐ-CP
    patterns = {
        "document_number": r"Số\s*:\s*([0-9]+(?:/[A-ZĐ0-9-]+)+)",

        # Signing date
        "signing_date": (
            r"(?:Hà Nội,\s*)?"
            r"ngày\s+(\d{1,2})\s+tháng\s+"
            r"(\d{1,2})\s+năm\s+(\d{4})"
        ),

        # Effective date
        "effective_date": (
            r"có hiệu lực(?: thi hành)?\s+"
            r"(?:kể từ ngày|từ ngày)\s+"
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})"
        ),

        # Deadline
        "deadline_date": (
            r"(?:hạn cuối|chậm nhất|trước ngày)\s+"
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})"
        )
    }

    # number
    match = re.search(
        patterns["document_number"],
        content,
        re.IGNORECASE
    )
    if match:
        metadata["document_number"] = match.group(1)

    # Sign
    match = re.search(
        patterns["signing_date"],
        content,
        re.IGNORECASE
    )
    if match:
        day, month, year = match.groups()
        metadata["signing_date"] = (
            f"{day.zfill(2)}/{month.zfill(2)}/{year}"
        )

    # Effective
    match = re.search(
        patterns["effective_date"],
        content,
        re.IGNORECASE
    )
    if match:
        day, month, year = re.split(r"[/-]", match.group(1))
        metadata["effective_date"] = (
            f"{day.zfill(2)}/{month.zfill(2)}/{year}"
        )

    # Deadline
    match = re.search(
        patterns["deadline_date"],
        content,
        re.IGNORECASE
    )
    if match:
        day, month, year = re.split(r"[/-]", match.group(1))
        metadata["deadline_date"] = (
            f"{day.zfill(2)}/{month.zfill(2)}/{year}"
        )

    # No info
    if not any(metadata.values()):
        return None

    return metadata 