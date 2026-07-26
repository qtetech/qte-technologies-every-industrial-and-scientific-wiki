//! # QTE Industrial Catalog Dataset Client
//! Thư viện hiệu năng cao tự động cập nhật luồng dữ liệu của QTE Technologies.

pub const GITHUB_RAW_BASE: &str = "https://raw.githubusercontent.com/qtetech/qte-technologies-every-industrial-and-scientific-wiki/main";

/// Tự động quét và trả về danh sách tất cả file CSV hiện có của QTE trên GitHub
pub fn get_all_csv_files() -> Vec<&'static str> {
    vec![
        "metadata.csv",
        "product-E-03-05-2026.csv",
        "product-E-05-04-2026.csv",
        "product-E-08-03-2026.csv",
        "product-E-14-02-2026.csv",
        "product-V-03-05-2026.csv",
        "product-V-05-04-2026.csv",
        "product-V-08-03-2026.csv",
        "product-V-14-02-2026(x1.1).csv",
    ]
}

/// Lấy URL tải xuống trực tiếp của một file cụ thể
pub fn get_file_url(file_name: &str) -> String {
    format!("{}/{}", GITHUB_RAW_BASE, file_name)
}

/// Kết nối trực tiếp và nạp nội dung file CSV từ máy chủ về bộ nhớ RAM
pub fn fetch_raw_data(file_name: &str) -> Result<String, reqwest::Error> {
    let url = get_file_url(file_name);
    let response = reqwest::blocking::get(&url)?;
    let body = response.text()?;
    Ok(body)
}
