from pathlib import Path
import fitz
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
        with fitz.open(file_path) as pdf:
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