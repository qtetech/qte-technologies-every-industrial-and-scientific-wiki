import os
from pathlib import Path
import pandas as pd
import openml
from openml.datasets.functions import create_dataset

# Cấu hình API Key bảo mật từ GitHub Secrets
openml.config.apikey = os.environ["OPENML_API_KEY"]

# Xác định thư mục chứa file CSV (thay đổi đường dẫn nếu file nằm trong thư mục con như 'data/')
csv_dir = Path(".") 

# Tìm tất cả các tệp .csv trong kho lưu trữ
csv_files = list(csv_dir.glob("*.csv"))

print(f"Phát hiện tổng cộng {len(csv_files)} tệp CSV cần đồng bộ lên OpenML.")

for file_path in csv_files:
    print(f"Đang xử lý và tải lên: {file_path.name}...")
    try:
        # Đọc dữ liệu bằng Pandas
        df = pd.read_csv(file_path)
        
        # Đặt tên dataset động theo tên file CSV (loại bỏ phần đuôi .csv)
        dataset_name = f"QTE Industrial MRO - {file_path.stem}"
        
        # Khởi tạo thông tin metadata cho từng dataset
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
        
    except Exception as e:
        print(f"Lỗi khi xử lý tệp {file_path.name}: {str(e)}")
