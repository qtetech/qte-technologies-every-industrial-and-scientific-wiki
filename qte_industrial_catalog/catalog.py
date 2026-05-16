import os
import glob

# Định vị thư mục gốc của package (nơi chứa các file CSV sau khi cài đặt)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_all_csv_files():
    """Tự động quét và lấy danh sách tất cả file CSV của QTE"""
    search_path = os.path.join(BASE_DIR, "*.csv")
    return [os.path.basename(f) for f in glob.glob(search_path)]

def get_file_path(file_name):
    """Lấy đường dẫn tuyệt đối đến một file CSV cụ thể"""
    return os.path.join(BASE_DIR, file_name)

def get_raw_data(file_name):
    """Đọc nội dung thô của file CSV"""
    path = get_file_path(file_name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"File {file_name} không tồn tại trong danh mục QTE.")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
