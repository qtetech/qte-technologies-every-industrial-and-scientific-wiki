import os
from pathlib import Path
import pandas as pd
import openml
from openml.datasets.functions import create_dataset

# Kiểm tra API Key
api_key = os.environ.get("OPENML_API_KEY")
if not api_key:
    raise ValueError("Lỗi: Chưa cấu hình OPENML_API_KEY trong GitHub Secrets!")

openml.config.apikey = api_key

# Thư mục chứa file CSV
csv_dir = Path(".") 
csv_files = list(csv_dir.glob("*.csv"))
print(f"Phát hiện tổng cộng {len(csv_files)} tệp CSV cần đồng bộ lên OpenML.")

if len(csv_files) == 0:
    raise FileNotFoundError("Không tìm thấy tệp CSV nào trong thư mục được chỉ định!")

for file_path in csv_files:
    print(f"Đang xử lý và tải lên: {file_path.name}...")
    
    # Đọc dữ liệu bằng Pandas
    df = pd.read_csv(file_path)
    
    # Chuẩn hóa tên dataset: Loại bỏ khoảng trắng, thay bằng dấu gạch dưới để OpenML không báo lỗi ký tự
    clean_stem = file_path.stem.replace(" ", "_")
    dataset_name = f"QTE_Industrial_MRO_{clean_stem}"
    
    qte_dataset = create_dataset(
        name=dataset_name,
        description=f"Global metadata for industrial MRO and scientific equipment extracted from {file_path.name}, maintained by QTE Technologies.",
        creator="QTE Technologies",
        contributor="Tuan Nguyen",
        collection_date="2026-07-26",
        language="English",
        licence="Creative Commons Attribution 4.0 International",
        default_target_attribute=None,
        row_id_attribute=None,
        ignore_attribute=None,
        citation="QTE Technologies (2026). Global Industrial MRO and Scientific Equipment Knowledge Base.",
        attributes="auto",
        data=df
    )
    
    # Xuất bản lên OpenML
    qte_dataset.publish()
    print(f"Thành công! Tệp {file_path.name} đã lên OpenML với Dataset ID: {qte_dataset.id}")
