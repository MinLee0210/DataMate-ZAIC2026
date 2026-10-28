import duckdb
import pandas as pd
import pytest

from src.modules.ingest import Table, merge_split_tables, parse_number, read_tables, to_identifier
from src.modules.ingest.clean import detect_header_row, number_locale
from src.services.ingest import IngestService


@pytest.mark.parametrize(
    "text, expected",
    [
        ("1.200.000", 1200000),
        ("1,200,000", 1200000),
        ("12,5", 12.5),
        ("12.5", 12.5),
        ("350.000 đ", 350000),  # VND has no decimals
        ("50.000đ", 50000),
        ("9.999đ", 9999),
        ("25k", 25000),
        ("1,5tr", 1500000),
        ("2 triệu", 2000000),
        ("30 nghìn", 30000),
        ("12.500", 12.5),  # no currency, ambiguous: read as a decimal
        ("1.234,5 VNĐ", 1234.5),
        ("15%", 0.15),
        ("-3", -3),
        ("abc", None),
        ("SP01", None),
    ],
)
def test_parse_number(text, expected):
    assert parse_number(text) == expected


def test_ambiguous_thousands_follow_the_column_locale():
    assert parse_number("350.000 đ", "vi") == 350000
    assert number_locale(pd.Series(["1.200.000", "350.000"])) == "vi"
    assert number_locale(pd.Series(["1,200,000", "350.5"])) == "en"
    assert number_locale(pd.Series(["350.000", "12.5"])) is None


def test_to_identifier():
    assert to_identifier("Thành tiền (VNĐ)") == "thanh_tien_vnd"
    assert to_identifier("Đơn giá") == "don_gia"
    assert to_identifier("2024") == "c_2024"
    assert to_identifier("!!!") == "col"


def test_detect_header_skips_title_rows():
    raw = pd.DataFrame([["BÁO CÁO", None, None], ["Mã", "Tên", "Giá"], ["A", "x", "1"]])
    assert detect_header_row(raw) == 1


def test_read_csv_with_title_rows_and_vietnamese_numbers(toy_split):
    (table,) = read_tables(toy_split / "businesses/shop1/orders.csv")
    assert table.name == "orders"
    assert list(table.frame.columns) == ["ma_don", "ngay", "ma_sp", "so_luong", "thanh_tien_vnd"]
    assert table.originals[4] == "Thành tiền (VNĐ)"
    assert table.frame["thanh_tien_vnd"].tolist() == [1200000, 350000, 600000, 1050000]
    assert str(table.frame["ngay"].iloc[0].date()) == "2026-10-20"  # day first


def test_read_xlsx_merged_cells_and_sheets(toy_split):
    tables = {t.name: t for t in read_tables(toy_split / "businesses/shop1/products.xlsx")}
    assert set(tables) == {"products__san_pham", "products__ghi_chu"}
    products = tables["products__san_pham"].frame
    assert products["nhom"].tolist() == ["Đồ uống", "Đồ uống"]
    assert products["ten_san_pham"].tolist() == ["Cà phê sữa", "Bánh mì"]


def test_ingest_service_builds_and_caches(toy_split, tmp_path):
    service = IngestService(tmp_path / "work")
    ctx = service.load("shop1", toy_split / "businesses/shop1")
    names = {t.name for t in ctx.card.tables}
    assert names == {"orders", "products__san_pham", "products__ghi_chu", "nhan_vien"}
    assert any(e.value == "Cà phê sữa" for e in ctx.entities)
    conn = duckdb.connect(str(ctx.db_path), read_only=True)
    assert conn.execute("SELECT sum(thanh_tien_vnd) FROM orders").fetchall()[0][0] == 3200000
    conn.close()
    # a second service reuses the on-disk cache
    again = IngestService(tmp_path / "work").load("shop1", toy_split / "businesses/shop1")
    assert again.db_path == ctx.db_path


def test_split_sheets_and_files_are_merged_with_a_source_column():
    def raw(rows):
        return pd.DataFrame(rows, columns=["ma_don", "tong_tien"])

    tables = [
        Table(
            "donhang_chitiet_1__t01_2025",
            "DonHang_ChiTiet_1.xlsx#T01",
            raw([["A", "25k"]]),
            ["Mã", "Tổng"],
        ),
        Table(
            "donhang_chitiet_1__t02_2025",
            "DonHang_ChiTiet_1.xlsx#T02",
            raw([["B", "9.999đ"]]),
            ["Mã", "Tổng"],
        ),
        Table(
            "donhang_chitiet_2026__t01_2026",
            "DonHang_ChiTiet_2026.xlsx#T01",
            raw([["C", "18000"]]),
            ["Mã", "Tổng"],
        ),
        Table("khach_hang", "KhachHang.xlsx", pd.DataFrame({"ma_kh": ["K1"]}), ["Mã KH"]),
    ]
    out = {t.name: t for t in merge_split_tables(tables)}
    assert set(out) == {"donhang_chitiet", "khach_hang"}
    merged = out["donhang_chitiet"]
    assert merged.frame["tong_tien"].tolist() == [25000, 9999, 18000]
    assert merged.frame["nguon"].tolist()[0] == "DonHang_ChiTiet_1.xlsx#T01"
    assert merged.originals[-1] == "Nguồn (file#sheet)"


def test_grouped_export_fills_parent_cells_only():
    from src.modules.ingest.clean import fill_grouped_rows

    frame = pd.DataFrame(
        {
            "ma_don_hang": ["D1", None, "D2", "D3", None],
            "ngay_dat_hang": ["01/05/2025", None, "01/05/2025", "02/05/2025", None],
            "ten_khach_hang": ["An", None, "Khách lẻ", "Bình", None],
            "ma_khach": ["K1", "K1", None, "K3", "K3"],  # blank for a walk-in: kept blank
            "ten_san_pham": ["A", "B", "C", "D", "E"],
        }
    )
    out = fill_grouped_rows(frame)
    assert out["ma_don_hang"].tolist() == ["D1", "D1", "D2", "D3", "D3"]
    assert out["ngay_dat_hang"].tolist()[1] == "01/05/2025"
    assert out["ma_khach"].isna().tolist() == [False, False, True, False, False]


def test_duplicate_lines_of_an_order_count_once():
    from src.modules.ingest.clean import drop_duplicate_order_lines

    lines = pd.DataFrame(
        {"ma_hoa_don": ["H1", "H1", "H2"], "ten_hang": ["A", "A", "A"], "thanh_tien": [5, 5, 5]}
    )
    assert drop_duplicate_order_lines(lines)["ma_hoa_don"].tolist() == ["H1", "H2"]
    log = pd.DataFrame({"ngay": ["01/05", "01/05"], "so_tien": [5, 5]})  # no order code: keep both
    assert len(drop_duplicate_order_lines(log)) == 2


def test_mixed_date_formats_become_one_date_column():
    from src.modules.ingest.clean import add_sheet_year, infer_column

    col = pd.Series(["30 thg 5 2026", "45678", "29/11/2025", "ngày 3 tháng 12 năm 2025", "12/5"])
    typed = infer_column(add_sheet_year(col.to_frame("ngay"), 2026)["ngay"])
    assert pd.api.types.is_datetime64_any_dtype(typed)
    assert [d.strftime("%Y-%m-%d") for d in typed] == [
        "2026-05-30",
        "2025-01-21",
        "2025-11-29",
        "2025-12-03",
        "2026-05-12",
    ]


def test_subtotal_and_repeated_header_rows_are_dropped():
    from src.modules.ingest.clean import drop_repeated_headers, drop_subtotal_rows

    frame = pd.DataFrame(
        {
            "khach": ["Tong Ngoc Chi", "Tổng ngày 30/05", "Mã đơn", "Cộng", "An"],
            "ma_don": ["D1", None, "Mã đơn", None, "D2"],
            "tien": ["5", "5", "Tiền", "10", "7"],
        }
    )
    out = drop_subtotal_rows(drop_repeated_headers(frame, ["Khách", "Mã đơn", "Tiền"]))
    assert out["khach"].tolist() == ["Tong Ngoc Chi", "An"]
