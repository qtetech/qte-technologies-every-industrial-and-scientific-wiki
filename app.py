import glob
import math
import os
import re
import urllib.parse
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="QTE Technologies — Industrial MRO & Scientific Catalog Explorer",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

MAIN_DOMAIN = "https://qtetech.com"
WIKIDATA_URL = "https://www.wikidata.org/wiki/Q138411149"
ORCID_URL = "https://orcid.org/0009-0002-1648-9536"
DATAVERSE_DOI = "https://doi.org/10.7910/DVN/VEVXRV"
ZENODO_DOI = "https://doi.org/10.5281/zenodo.18722002"
KAGGLE_URL = "https://www.kaggle.com/datasets/nguyenhuutuan1982/qte-technologies-industrial-scientific-archive"
HF_URL = "https://huggingface.co/datasets/QTE-Technologies/industrial-technical-archive"
ProductHunt_URL = "https://www.producthunt.com/products/qte-technologies"

COL_ALIASES = {
    "url": {"url", "link", "product_url", "duong_dan", "loc"},
    "name": {"title", "name", "product_name", "ten_san_pham", "ten", "heading"},
    "sku": {"sku", "mpn", "model", "code", "ma_san_pham", "ma_hang", "id", "part_number"},
    "brand": {"brand", "manufacturer", "hang", "thuong_hieu", "nha_san_xuat"},
    "category": {"category", "danh_muc", "type", "nhom_hang"},
    "price": {"price", "gia", "gia_ban", "amount"},
    "description": {"description", "mo_ta", "specs", "thong_so", "summary", "detail"},
}


def parse_date_from_filename(filepath: str):
    name = os.path.basename(filepath)
    match = re.search(r"product-[EV]-(\d{2})-(\d{2})-(\d{4})", name, re.IGNORECASE)
    if match:
        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
        return (year, month, day), f"{year:04d}-{month:02d}-{day:02d}"
    return (0, 0, 0), "Latest"


def find_latest_csv(prefix: str):
    candidates = glob.glob(f"{prefix}-*.csv") + glob.glob(f"**/{prefix}-*.csv", recursive=True)
    unique_files = list(dict.fromkeys(candidates))
    if not unique_files:
        return None, None
    ranked = sorted(
        unique_files,
        key=lambda p: parse_date_from_filename(p)[0],
        reverse=True,
    )
    best_file = ranked[0]
    _, date_label = parse_date_from_filename(best_file)
    return best_file, date_label


def slug_to_title(url: str) -> str:
    path = urllib.parse.urlparse(url).path.rstrip("/")
    slug = path.split("/")[-1] if path else ""
    slug = re.sub(r"-pr\d+$", "", slug, flags=re.IGNORECASE)
    words = [w for w in slug.split("-") if w]
    return " ".join(words).capitalize() if words else url


def extract_sku_from_url(url: str) -> str:
    path = urllib.parse.urlparse(url).path
    match = re.search(r"-(pr\d+)$", path, re.IGNORECASE)
    return match.group(1).upper() if match else ""


@st.cache_data(ttl=86400, show_spinner=False)
def load_catalog(filepath: str) -> pd.DataFrame:
    raw_df = pd.read_csv(
        filepath,
        dtype=str,
        encoding="utf-8-sig",
        on_bad_lines="skip",
    ).fillna("")

    if raw_df.empty:
        return pd.DataFrame()

    lower_cols = {col: col.strip().lower() for col in raw_df.columns}
    mapped = {}
    for canonical, aliases in COL_ALIASES.items():
        for orig_col, low_col in lower_cols.items():
            if low_col in aliases:
                mapped[canonical] = orig_col
                break

    if "url" not in mapped:
        for orig_col in raw_df.columns:
            sample = raw_df[orig_col].astype(str).str.strip()
            if sample.str.startswith(("http://", "https://")).mean() > 0.5:
                mapped["url"] = orig_col
                break

    if "url" not in mapped:
        return pd.DataFrame()

    df = pd.DataFrame()
    df["url"] = raw_df[mapped["url"]].str.strip()
    df = df[df["url"].str.startswith(("http://", "https://"))].copy()
    raw_df = raw_df.loc[df.index]

    if "name" in mapped:
        df["name"] = raw_df[mapped["name"]].str.strip()
        empty_name = df["name"] == ""
        if empty_name.any():
            df.loc[empty_name, "name"] = df.loc[empty_name, "url"].map(slug_to_title)
    else:
        df["name"] = df["url"].map(slug_to_title)

    if "sku" in mapped:
        df["sku"] = raw_df[mapped["sku"]].str.strip()
        empty_sku = df["sku"] == ""
        if empty_sku.any():
            df.loc[empty_sku, "sku"] = df.loc[empty_sku, "url"].map(extract_sku_from_url)
    else:
        df["sku"] = df["url"].map(extract_sku_from_url)

    for optional_field in ["brand", "category", "price", "description"]:
        if optional_field in mapped:
            df[optional_field] = raw_df[mapped[optional_field]].str.strip()
        else:
            df[optional_field] = ""

    df["_search_blob"] = (
        df["name"]
        + " "
        + df["sku"]
        + " "
        + df["brand"]
        + " "
        + df["category"]
        + " "
        + df["description"]
        + " "
        + df["url"]
    ).str.lower()

    df.reset_index(drop=True, inplace=True)
    return df


# --- Sidebar: Language & Verified Entity Hub ---
with st.sidebar:
    st.markdown("### ⚙️ QTE Technologies Co., Ltd")
    st.caption("CÔNG TY TNHH KỸ THUẬT QTE • Est. 2010 • Hanoi, Vietnam")

    en_file, en_date = find_latest_csv("product-E")
    vi_file, vi_date = find_latest_csv("product-V")

    lang_options = []
    if en_file:
        lang_options.append("English Catalog (EN)")
    if vi_file:
        lang_options.append("Danh mục Tiếng Việt (VI)")

    if not lang_options:
        st.error("Không tìm thấy tệp product-E-*.csv hoặc product-V-*.csv trong kho lưu trữ.")
        st.stop()

    selected_lang = st.radio(
        "Catalog Language / Ngôn ngữ danh mục",
        options=lang_options,
        index=0,
    )
    is_en = selected_lang.startswith("English")
    active_file = en_file if is_en else vi_file
    active_date = en_date if is_en else vi_date

    st.divider()
    st.markdown(
        "**Verified Entity & Open Data Hub**"
        if is_en
        else "**Hệ thống Định danh & Dữ liệu Mở**"
    )
    st.markdown(
        f"""
- 🌐 [Official B2B Portal (qtetech.com)]({MAIN_DOMAIN})
- 🆔 [Wikidata Canonical ID: Q138411149]({WIKIDATA_URL})
- 👨‍🔬 [Founder ORCID: 0009-0002-1648-9536]({ORCID_URL})
- 📚 [Harvard Dataverse DOI]({DATAVERSE_DOI})
- 🔬 [Zenodo Archive DOI]({ZENODO_DOI})
- 🤗 [Hugging Face Dataset]({HF_URL})
- 📊 [Kaggle Scientific Archive]({KAGGLE_URL})
- [Product Hunt]({ProductHunt_URL})
"""
    )

# --- Main Header ---
st.title(
    "QTE Technologies — Industrial MRO & Scientific Equipment Explorer"
    if is_en
    else "QTE Technologies — Cổng Tra Cứu Thiết Bị Công Nghiệp & Khoa Học"
)
st.markdown(
    f"Interactive B2B catalog explorer synced automatically from official QTE Technologies open datasets (`{os.path.basename(active_file)}`). Click any product link to view full technical specifications and request a B2B quotation on **[qtetech.com]({MAIN_DOMAIN})**."
    if is_en
    else f"Hệ thống tra cứu tương tác đồng bộ tự động từ kho dữ liệu mở của Công ty TNHH Kỹ thuật QTE (`{os.path.basename(active_file)}`). Bấm vào liên kết sản phẩm để xem thông số kỹ thuật chi tiết và gửi yêu cầu báo giá B2B tại **[qtetech.com]({MAIN_DOMAIN})**."
)

with st.spinner("Loading catalog index..." if is_en else "Đang nạp chỉ mục danh mục..."):
    df = load_catalog(active_file)

if df.empty:
    st.warning("Dataset is empty or missing valid product URLs.")
    st.stop()

# --- Filters ---
has_brand = (df["brand"] != "").any()
has_category = (df["category"] != "").any()

col_search, col_brand, col_cat = st.columns([2.4, 1.3, 1.3])

with col_search:
    query = st.text_input(
        "🔍 Search by Product Name, Model / SKU, or Keyword"
        if is_en
        else "🔍 Tìm theo Tên thiết bị, Mã hàng / Model hoặc Từ khóa",
        placeholder="e.g. V-301, vacuum pump, sensor, AS ONE..."
        if is_en
        else "VD: V-301, bơm chân không, cảm biến, AS ONE...",
    ).strip()

selected_brand = "All"
if has_brand:
    top_brands = df.loc[df["brand"] != "", "brand"].value_counts().index.tolist()
    with col_brand:
        selected_brand = st.selectbox(
            "Manufacturer / Brand" if is_en else "Hãng sản xuất",
            options=["All"] + top_brands,
        )

selected_cat = "All"
if has_category:
    top_cats = df.loc[df["category"] != "", "category"].value_counts().index.tolist()
    with col_cat:
        selected_cat = st.selectbox(
            "Technical Category" if is_en else "Nhóm ngành hàng",
            options=["All"] + top_cats,
        )

filtered = df
if selected_brand != "All":
    filtered = filtered[filtered["brand"] == selected_brand]
if selected_cat != "All":
    filtered = filtered[filtered["category"] == selected_cat]
if query:
    tokens = [t for t in query.lower().split() if t]
    mask = pd.Series(True, index=filtered.index)
    for token in tokens:
        mask &= filtered["_search_blob"].str.contains(token, regex=False)
    filtered = filtered[mask]

# --- KPI Metrics ---
m1, m2, m3, m4 = st.columns(4)
m1.metric(
    "Total Catalog Items" if is_en else "Tổng số sản phẩm",
    f"{len(df):,}",
)
m2.metric(
    "Matching Results" if is_en else "Kết quả phù hợp",
    f"{len(filtered):,}",
)
m3.metric(
    "Verified Brands" if is_en else "Thương hiệu",
    f"{df.loc[df['brand'] != '', 'brand'].nunique():,}" if has_brand else "B2B MRO",
)
m4.metric(
    "Dataset Snapshot" if is_en else "Cập nhật dữ liệu",
    active_date,
)

st.divider()

# --- Pagination Controls ---
total_rows = len(filtered)
if total_rows == 0:
    st.info(
        "No matching products found. Try broadening your keywords or resetting filters."
        if is_en
        else "Không tìm thấy thiết bị phù hợp. Vui lòng thử từ khóa ngắn gọn hơn hoặc xóa bộ lọc."
    )
    st.stop()

p_col1, p_col2, p_col3 = st.columns([1.2, 1.2, 2.6])
with p_col1:
    page_size = st.selectbox(
        "Rows per page" if is_en else "Số dòng / trang",
        options=[25, 50, 100],
        index=1,
    )
total_pages = max(1, math.ceil(total_rows / page_size))
with p_col2:
    current_page = st.number_input(
        f"Page (1–{total_pages:,})" if is_en else f"Trang (1–{total_pages:,})",
        min_value=1,
        max_value=total_pages,
        value=1,
        step=1,
    )

start_idx = (current_page - 1) * page_size
end_idx = min(start_idx + page_size, total_rows)
page_slice = filtered.iloc[start_idx:end_idx].copy()

with p_col3:
    st.caption(
        f"Showing items **{start_idx + 1:,} – {end_idx:,}** of **{total_rows:,}** matching products."
        if is_en
        else f"Đang hiển thị sản phẩm **{start_idx + 1:,} – {end_idx:,}** trong tổng số **{total_rows:,}** kết quả."
    )

# --- Build Clean Display Table ---
display_cols = ["sku", "name"]
if has_brand:
    display_cols.append("brand")
if has_category:
    display_cols.append("category")
if (df["price"] != "").any():
    display_cols.append("price")
if (df["description"] != "").any():
    display_cols.append("description")
display_cols.append("url")

rename_map = (
    {
        "sku": "SKU / Ref",
        "name": "Product Name",
        "brand": "Brand",
        "category": "Category",
        "price": "Reference Price",
        "description": "Technical Summary",
        "url": "Official Page & RFQ",
    }
    if is_en
    else {
        "sku": "Mã SP",
        "name": "Tên thiết bị",
        "brand": "Hãng SX",
        "category": "Danh mục",
        "price": "Giá tham khảo",
        "description": "Mô tả kỹ thuật",
        "url": "Trang SP & Báo giá",
    }
)

table_df = page_slice[display_cols].rename(columns=rename_map)
url_col_label = rename_map["url"]

st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True,
    height=620,
    column_config={
        url_col_label: st.column_config.LinkColumn(
            url_col_label,
            display_text="View & Quote →" if is_en else "Xem & Báo giá →",
        ),
    },
)

# --- Export Shortlist for Engineers / Buyers ---
export_limit = min(total_rows, 5000)
export_csv = filtered.iloc[:export_limit][display_cols].to_csv(index=False).encode("utf-8-sig")
st.download_button(
    label=(
        f"⬇️ Download Filtered Shortlist CSV (Top {export_limit:,} items)"
        if is_en
        else f"⬇️ Tải danh sách lọc CSV ({export_limit:,} sản phẩm đầu)"
    ),
    data=export_csv,
    file_name=f"qte-filtered-catalog-{active_date}.csv",
    mime="text/csv",
)

# --- Optional Analytics Expander ---
if has_brand or has_category:
    with st.expander("📊 Catalog Distribution Analytics / Thống kê phân bổ danh mục"):
        c1, c2 = st.columns(2)
        if has_brand:
            with c1:
                st.subheader("Top 15 Brands" if is_en else "Top 15 Thương hiệu")
                brand_counts = df.loc[df["brand"] != "", "brand"].value_counts().head(15)
                st.bar_chart(brand_counts)
        if has_category:
            with c2:
                st.subheader("Top 15 Categories" if is_en else "Top 15 Nhóm hàng")
                cat_counts = df.loc[df["category"] != "", "category"].value_counts().head(15)
                st.bar_chart(cat_counts)
