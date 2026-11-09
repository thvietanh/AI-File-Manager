import os
from pathlib import Path


def get_files(folder_path):
    """Lấy danh sách file trong thư mục và các thư mục con."""
    files = []

    for root, dirs, filenames in os.walk(folder_path):
        for filename in filenames:
            path = Path(root) / filename

            try:
                files.append({
                    "name": filename,
                    "extension": path.suffix.lower(),
                    "size": path.stat().st_size,
                    "path": str(path)
                })
            except OSError:
                continue

    return files


def open_file(file_path):
    """Mở file bằng ứng dụng mặc định của Windows."""
    if os.path.isfile(file_path):
        os.startfile(file_path)