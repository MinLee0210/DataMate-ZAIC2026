import duckdb
import pandas as pd
import pytest

from src.modules.ingest import parse_number, read_tables, to_identifier
from src.modules.ingest.clean import detect_header_row, number_locale
from src.services.ingest import IngestService


@pytest.mark.parametrize(
    "text, expected",
    [
        ("1.200.000", 1200000),
        ("1,200,000", 1200000),
        ("12,5", 12.5),
        ("12.5", 12.5),
        ("350.000 đ", 350),
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
