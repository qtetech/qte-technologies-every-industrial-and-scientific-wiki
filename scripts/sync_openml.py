import os
from pathlib import Path
import pandas as pd
import openml
from openml.exceptions import OpenMLServerError
from openml.datasets.functions import create_dataset

api_key = os.environ.get("OPENML_API_KEY")
if not api_key:
    raise ValueError("Lỗi: Chưa cấu hình OPENML_API_KEY trong GitHub Secrets!")

openml.config.apikey = api_key

csv_dir = Path(".") 
csv_files = list(csv_dir.glob("*.csv"))
print(f"Phát hiện tổng cộng {len(csv_files)} tệp CSV cần đồng bộ lên OpenML.")

for file_path in csv_files:
    print(f"Đang xử lý: {file_path.name}...")
    try:
        # Đọc dữ liệu
        df = pd.read_csv(file_path)
        
        # Nếu tệp quá lớn (>50,000 dòng), chỉ lấy mẫu 10,000 dòng đầu tiên để tránh lỗi 504 Timeout trên OpenML
        if len(df) > 50000:
            print(f"-> Tệp lớn ({len(df)} dòng), tiến hành lấy mẫu 10,000 dòng cho OpenML...")
            df = df.head(10000)
            
        clean_stem = file_path.stem.replace(" ", "_")
        dataset_name = f"QTE_Industrial_MRO_{clean_stem}"
        
        qte_dataset = create_dataset(
            name=dataset_name,
            description=f"Metadata sample extracted from {file_path.name}, maintained by QTE Technologies.",
            creator="QTE Technologies",
            contributor="Tuan Nguyen",
            collection_date="2026-07-26",
            language="English",
            licence="Creative Commons Attribution 4.0 International",
            default_target_attribute=None,
            row_id_attribute=None,
            ignore_attribute=None,
            citation="QTE Technologies (2026). Global Industrial and Scientific Knowledge Base.",
            attributes="auto",
            data=df
        )
        
        qte_dataset.publish()
        print(f"-> Thành công! Dataset ID: {qte_dataset.id}")
        
    except OpenMLServerError as e:
        print(f"-> Bỏ qua lỗi OpenML Server (504/Timeout) đối với {file_path.name}: {str(e)}")
        continue
    except Exception as e:
        print(f"-> Lỗi không mong muốn với {file_path.name}: {str(e)}")
        continue

print("Hoàn tất quy trình xử lý đồng bộ OpenML.")
