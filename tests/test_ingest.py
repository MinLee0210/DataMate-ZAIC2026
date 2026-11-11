import duckdb
import pandas as pd
import pytest

from src.modules.ingest import (
    Table,
    infer_types,
    merge_split_tables,
    parse_number,
    read_tables,
    to_identifier,
)
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
        ("1tr440", 1440000),  # the "1tr440" / "2tr950" shorthand: fraction of a million
        ("2tr950", 2950000),
        ("12tr500", 12500000),
        ("1tr5", 1500000),
        ("1tr44", 1440000),
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


def test_semantic_status_and_walk_in_macros():
    from src.modules.semantic import apply_semantic_layer

    conn = duckdb.connect()
    described = apply_semantic_layer(conn)
    assert {"fold", "is_cancelled", "is_returned", "is_walk_in"} <= {
        item.split("(")[0] for item in described
    }

    def ask(sql, value):
        return conn.execute(sql, [value]).fetchone()[0]

    assert all(ask("select is_cancelled(?)", s) for s in ["Huỷ đơn", "hủy đơn", "khách hủy"])
    assert all(ask("select is_returned(?)", s) for s in ["Đổi trả", "hàng trả về", "Đã hoàn hàng"])
    assert not ask("select is_returned(?)", "Đã hoàn thành")
    assert ask("select is_cancelled(?)", None) is False
    assert ask("select is_returned(?)", None) is False
    conn.execute("create table order_status(status varchar)")
    conn.executemany("insert into order_status values (?)", [(None,), ("Xong",), ("Đã hủy",)])
    assert (
        conn.execute(
            "select count(*) from order_status "
            "where not is_cancelled(status) and not is_returned(status)"
        ).fetchone()[0]
        == 2
    )
    assert all(ask("select is_walk_in(?)", s) for s in ["khách lẻ", "kl", "lẻ", None])
    assert not ask("select is_walk_in(?)", "Lê Văn Kl")


def test_monthly_tables_merge_into_one_base_name():
    from src.modules.ingest.readers import _base_name

    names = ["banhang_t10_2025", "banhang_t1", "banhang_thang05", "banhang_thang06_2025"]
    assert {_base_name(n) for n in names} == {"banhang"}
    assert _base_name("donhang_chitiet_2026__t06_2026") == "donhang_chitiet"


def test_grouped_export_does_not_fill_order_money_down():
    from src.modules.ingest.clean import fill_grouped_rows

    frame = pd.DataFrame(
        {
            "ma_don": ["D1", None, None, "D2"],
            "thoi_gian": ["01/05/2025", None, None, "02/05/2025"],
            "tong_phieu": ["300000", None, None, "50000"],  # order total, first line only
            "ten_hang": ["A", "B", "C", "D"],
        }
    )
    out = fill_grouped_rows(frame)
    assert out["ma_don"].tolist() == ["D1", "D1", "D1", "D2"]
    assert out["tong_phieu"].isna().tolist() == [False, True, True, False]


def test_excel_serial_dates_in_a_date_column_become_dates():
    # a date column exported as day numbers, the case that stopped every date filter in biz_107
    frame = pd.DataFrame({"ngay_ban": [45717, 45718, 45719, 45720, 45721]})
    typed = infer_types(frame)
    assert pd.api.types.is_datetime64_any_dtype(typed["ngay_ban"])
    assert [d.strftime("%Y-%m-%d") for d in typed["ngay_ban"]] == [
        "2025-03-01",
        "2025-03-02",
        "2025-03-03",
        "2025-03-04",
        "2025-03-05",
    ]


def test_serial_day_numbers_outside_a_date_column_stay_numbers():
    frame = pd.DataFrame(
        {"so_ngay": [1, 2, 3, 4, 5], "ngay_sinh": [24000, 24001, 24002, 24003, 24004]}
    )
    typed = infer_types(frame)
    assert typed["so_ngay"].tolist() == [1, 2, 3, 4, 5]
    assert typed["ngay_sinh"].tolist() == [24000, 24001, 24002, 24003, 24004]


def test_the_schema_card_records_the_data_window(toy_split):
    ctx = IngestService(toy_split / "work").load("shop1", toy_split / "businesses/shop1")
    assert ctx.card.data_start and ctx.card.data_end
    assert ctx.card.data_start.startswith("2026-10") and ctx.card.data_end.startswith("2026-10")
    from src.modules.context import render_schema_card

    assert "data_window" in render_schema_card(ctx.card)


def test_the_data_window_ignores_expiry_birth_and_creation_dates():
    from src.models import ColumnCard, SchemaCard, TableCard
    from src.modules.context import data_window

    def col(name, lo, hi):
        return ColumnCard(name=name, original=name, dtype="TIMESTAMP", min=lo, max=hi)

    card = SchemaCard(
        business_id="b",
        tables=[
            TableCard(
                name="orders",
                source="x",
                rows=1,
                columns=[
                    col("ngay_dat_hang", "2025-04-01", "2026-07-09"),
                    col("han_su_dung", "2024-01-01", "2029-01-01"),
                    col("ngay_sinh", "1965-01-01", "2004-01-01"),
                    col("thoi_gian_tao", "2023-01-01", "2023-06-01"),
                ],
            )
        ],
    )
    # "hang" in ngay_dat_hang is not "han" (expiry); expiry, birth and creation dates are metadata
    assert data_window(card) == ("2025-04-01", "2026-07-09")


def test_serial_dates_in_an_order_date_column():
    frame = pd.DataFrame({"ngay_dat_hang": [45717, 45718, 45719, 45720, 45721]})
    typed = infer_types(frame)
    assert pd.api.types.is_datetime64_any_dtype(typed["ngay_dat_hang"])


@pytest.mark.parametrize(
    "text, expected",
    [
        ("1 ly", 1),
        ("2 phần", 2),
        ("1 m3", 1),
        ("2", 2),
        ("1,5 ly", 1.5),
        ("1/2", None),
        ("SP01", None),
    ],
)
def test_parse_quantity(text, expected):
    from src.modules.ingest.clean import parse_quantity

    assert parse_quantity(text) == expected


def test_a_quantity_written_with_its_unit_becomes_a_number():
    frame = pd.DataFrame({"so_luong_san_pham": ["1", "1 ly", "2", "2 ly", "1 phần"]})
    assert infer_types(frame)["so_luong_san_pham"].tolist() == [1, 1, 2, 2, 1]
