from doc_extract import extract

# Docx
print("\033[1m" + "File docx:" + "\033[0m")
file_path = "C:\\Users\\thvie\\Documents\\VSCode\\Test Folder\\cv_ung_vien.docx"

try:
    content = extract(file_path)
    print(content)
except ValueError as e:
    print(f"Error: {e}")

# PDF
print("\n")
print("\033[1m" + "File PDF:" + "\033[0m")
file_path = "C:\\Users\\thvie\\Documents\\VSCode\\Test Folder\\chinh_sach_nghi_phep.pdf"

try:
    content = extract(file_path)
    print(content)
except ValueError as e:
    print(f"Error: {e}")

# TXT
print("\n")
print("\033[1m" + "File txt:" + "\033[0m")
file_path = "C:\\Users\\thvie\\Documents\\VSCode\\Test Folder\\bien_ban_hop_du_an.txt"

try:
    content = extract(file_path)
    print(content)
except ValueError as e:
    print(f"Error: {e}")