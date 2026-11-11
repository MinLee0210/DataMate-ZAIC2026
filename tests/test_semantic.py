import duckdb
import pandas as pd

from src.models import SchemaCard
from src.modules.context import build_table_card
from src.modules.ingest import infer_types
from src.modules.semantic import apply_semantic_layer
from src.modules.semantic.roles import detect_roles


def build(frames: dict[str, pd.DataFrame]) -> tuple[duckdb.DuckDBPyConnection, SchemaCard]:
    """A throwaway business database with a schema card, as ingest builds one."""
    conn = duckdb.connect()
    card = SchemaCard(business_id="test")
    for name, frame in frames.items():
        frame = infer_types(frame)
        conn.register("_frame", frame)
        conn.execute(f'CREATE TABLE "{name}" AS SELECT * FROM _frame')
        conn.unregister("_frame")
        card.tables.append(build_table_card(conn, name, name, list(frame.columns)))
    return conn, card


def shop() -> dict[str, pd.DataFrame]:
    orders = pd.DataFrame(
        {
            "ma_hoa_don": ["H1", "H2", "H3"],
            "thoi_gian": ["2025-03-01", "2025-03-02", "2025-03-03"],
            "ma_kh": ["K1", "K2", None],
            "khach_hang": ["An", "Bình", "Khách lẻ"],
            "tong_tien_hang": [100, 200, 300],
            "khach_da_tra": [100, 0, 300],
            "trang_thai": ["Hoàn thành", "Đã hủy", "Hoàn thành"],
            "kenh_ban": ["store", "phone", "store"],
            "nguoi_ban": ["NV1", "NV2", "NV1"],
        }
    )
    lines = pd.DataFrame(
        {
            "ma_hoa_don": ["H1", "H1", "H2", "H3"],
            "ma_hang": ["SP1", "SP2", "SP1", "SP3"],
            "ten_hang": ["Cà phê", "Bánh", "Cà phê", "Trà"],
            "so_luong": [2, 1, 4, 3],
            "don_gia": [20, 60, 50, 100],
            "thanh_tien": [40, 60, 200, 300],
            "don_vi_tinh": ["ly", "cái", "ly", "ly"],
        }
    )
    products = pd.DataFrame(
        {
            "ma_hang": ["SP1", "SP2", "SP3"],
            "ten_hang": ["Cà phê", "Bánh", "Trà"],
            "don_vi_tinh": ["ly", "cái", "ly"],
            "gia_von": [5, 20, 30],
            "nhom_hang": ["đồ uống", "bánh", "đồ uống"],
        }
    )
    stock = pd.DataFrame(
        {"ma_hang": ["SP1", "SP2"], "ten_hang": ["Cà phê", "Bánh"], "ton_cuoi_ky": [9, 4]}
    )
    return {"danhsachhoadon": orders, "danhsachhoadonchitiet": lines, "danhsachsanpham": products,
            "baocaotonkho": stock}  # fmt: skip


def test_roles_are_detected_from_names_and_types():
    conn, card = build(shop())
    kinds = {roles.table.name: roles.kind for roles in detect_roles(card)}
    assert kinds["danhsachhoadon"] == "sales"
    assert kinds["danhsachhoadonchitiet"] == "sales"
    assert kinds["danhsachsanpham"] == "products"
    assert kinds["baocaotonkho"] == "stock"
    conn.close()


def test_valid_orders_revenue_and_walk_in():
    conn, card = build(shop())
    apply_semantic_layer(conn, card)
    # 100 (H1) + 300 (H3); H2 is cancelled and its lines never count
    total = conn.execute("SELECT sum(line_total) FROM v_sales WHERE is_valid").fetchone()[0]
    assert total == 400
    # a customer is a code: the walk-in row is not a customer
    rows = conn.execute(
        "SELECT customer_code, sum(line_total) FROM v_sales "
        "WHERE is_valid AND NOT is_walk_in GROUP BY 1 ORDER BY 2 DESC"
    ).fetchall()
    assert rows == [("K1", 100.0)]
    conn.close()


def test_orders_one_row_per_code_and_line_totals():
    conn, card = build(shop())
    apply_semantic_layer(conn, card)
    rows = conn.execute(
        "SELECT order_code, order_total, is_valid FROM v_orders ORDER BY order_code"
    ).fetchall()
    assert rows == [("H1", 100.0, True), ("H2", 200.0, False), ("H3", 300.0, True)]
    conn.close()


def test_products_and_stock_views():
    conn, card = build(shop())
    apply_semantic_layer(conn, card)
    assert conn.execute("SELECT count(*) FROM v_products").fetchone()[0] == 3
    assert (
        conn.execute("SELECT quantity FROM v_stock WHERE item_name = 'Cà phê'").fetchone()[0] == 9
    )
    conn.close()


def test_a_shop_without_order_codes_gets_sales_but_not_orders():
    flat = pd.DataFrame(
        {
            "ngay_ban": ["2025-03-01", "2025-03-02"],
            "noi_dung": ["Cà phê", "Trà"],
            "so_luong": [2, 1],
            "don_gia": [20, 30],
            "thanh_tien": [40, 30],
            "trang_thai_xu_ly": ["Hoàn thành", "Hoàn thành"],
        }
    )
    conn, card = build({"sobanhang": flat})
    described = apply_semantic_layer(conn, card)
    assert any(item.startswith("v_sales(") for item in described)
    assert not any(item.startswith("v_orders(") for item in described)
    assert conn.execute("SELECT sum(line_total) FROM v_sales WHERE is_valid").fetchone()[0] == 70
    conn.close()


def test_a_negative_line_invalidates_the_whole_order():
    orders = pd.DataFrame(
        {
            "ma_hoa_don": ["H1", "H2"],
            "thoi_gian": ["2025-03-01", "2025-03-02"],
            "ma_kh": ["K1", "K1"],
            "khach_hang": ["An", "An"],
            "trang_thai": ["Hoàn thành", "Hoàn thành"],  # the status does not say "returned"
        }
    )
    lines = pd.DataFrame(
        {
            "ma_hoa_don": ["H1", "H2", "H2"],
            "ma_hang": ["SP1", "SP1", "SP1"],
            "ten_hang": ["Cà phê", "Cà phê", "Cà phê"],
            "so_luong": [1, 3, -1],  # a return written as a negative line, same order code
            "don_gia": [40, 40, 40],
            "thanh_tien": [40, 120, -40],
        }
    )
    conn, card = build({"danhsachhoadon": orders, "danhsachhoadonchitiet": lines})
    apply_semantic_layer(conn, card)
    # rulebook §1: a partly returned order is dropped as a whole, so only H1 counts
    assert conn.execute("SELECT sum(line_total) FROM v_sales WHERE is_valid").fetchone()[0] == 40
    assert (
        conn.execute("SELECT is_valid FROM v_orders WHERE order_code = 'H2'").fetchone()[0] is False
    )
    conn.close()
