import csv
import glob
import json
import os
import re
import sys
import urllib.error
import urllib.request

WORKER_URL = os.environ.get("DIFFBOT_WORKER_URL", "").rstrip("/")
DIFFBOT_TOKEN = os.environ.get("DIFFBOT_TOKEN", "").strip()

URL_COLUMN_ALIASES = {"url", "link", "product_url", "duong_dan", "loc"}

# Chỉ giữ lại các đường dẫn thực tế đang hoạt động trên qtetech.com
ANCHOR_URLS = [
    "https://qtetech.com/",
    "https://qtetech.com/en",
]


def parse_date_from_filename(filepath):
    """Trích xuất (YYYY, MM, DD) từ tên file dạng product-E-15-11-2026.csv."""
    name = os.path.basename(filepath)
    match = re.search(r"product-[EV]-(\d{2})-(\d{2})-(\d{4})", name, re.IGNORECASE)
    if match:
        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
        return (year, month, day)
    return (0, 0, 0)


def extract_urls(filepath):
    """Đọc file CSV và trả về danh sách URL hợp lệ."""
    urls = []
    with open(filepath, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header:
            return urls

        lower_header = [h.strip().lower() for h in header]
        col_idx = -1
        for idx, col in enumerate(lower_header):
            if col in URL_COLUMN_ALIASES:
                col_idx = idx
                break

        first_data_row = next(reader, None)
        if not first_data_row:
            return urls

        if col_idx == -1:
            for idx, val in enumerate(first_data_row):
                if val.strip().startswith(("http://", "https://")):
                    col_idx = idx
                    break

        if col_idx == -1:
            print(f"[Cảnh báo] Không tìm thấy cột URL trong {filepath}")
            return urls

        for row in [first_data_row] + list(reader):
            if len(row) > col_idx:
                val = row[col_idx].strip()
                if val.startswith(("http://", "https://")):
                    urls.append(val)
    return urls


def main():
    if not WORKER_URL or not DIFFBOT_TOKEN:
        print("[Lỗi] Thiếu biến môi trường DIFFBOT_WORKER_URL hoặc DIFFBOT_TOKEN.")
        sys.exit(1)

    en_files = sorted(glob.glob("product-E-*.csv"), key=parse_date_from_filename, reverse=True)
    vi_files = sorted(glob.glob("product-V-*.csv"), key=parse_date_from_filename, reverse=True)

    if not en_files and not vi_files:
        print("Không tìm thấy tệp product-E-*.csv hoặc product-V-*.csv nào.")
        sys.exit(0)

    latest_en = en_files[0] if en_files else None
    latest_vi = vi_files[0] if vi_files else None
    print(f"Tệp mới nhất được chọn: EN={latest_en} | VI={latest_vi}")

    latest_en_urls = extract_urls(latest_en) if latest_en else []
    latest_vi_urls = extract_urls(latest_vi) if latest_vi else []

    historical_urls = set()
    for old_file in en_files[1:] + vi_files[1:]:
        historical_urls.update(extract_urls(old_file))

    final_queue = []
    seen = set()

    def add_url(u):
        if u and u not in seen:
            seen.add(u)
            final_queue.append(u)

    # 1. Trang chủ tiếng Việt và tiếng Anh
    for u in ANCHOR_URLS:
        add_url(u)

    # 2. Ưu tiên đẩy các sản phẩm MỚI xuất hiện trong lần cập nhật gần nhất
    new_en = [u for u in latest_en_urls if u not in historical_urls]
    new_vi = [u for u in latest_vi_urls if u not in historical_urls]
    print(f"Phát hiện {len(new_en):,} URL tiếng Anh mới và {len(new_vi):,} URL tiếng Việt mới.")

    for i in range(max(len(new_en), len(new_vi))):
        if i < len(new_en):
            add_url(new_en[i])
        if i < len(new_vi):
            add_url(new_vi[i])

    # 3. Toàn bộ các URL sản phẩm còn lại trong 2 file CSV mới nhất
    for i in range(max(len(latest_en_urls), len(latest_vi_urls))):
        if i < len(latest_en_urls):
            add_url(latest_en_urls[i])
        if i < len(latest_vi_urls):
            add_url(latest_vi_urls[i])

    print(f"Tổng số URL sạch chuẩn bị gửi sang Worker: {len(final_queue):,}")

    payload = ("\n".join(final_queue) + "\n").encode("utf-8")
    req = urllib.request.Request(
        f"{WORKER_URL}/api/upload",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {DIFFBOT_TOKEN}",
            "Content-Type": "text/plain; charset=utf-8",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            print("Thành công! Phản hồi từ Cloudflare Worker:", result)
    except urllib.error.HTTPError as e:
        print(f"[Lỗi HTTP {e.code}] {e.read().decode('utf-8', errors='replace')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
