"""A tiny messy business package (title rows, Vietnamese numbers, merged cells, SQLite).

Used by the tests and by scripts/devfree/smoke.py; it is synthetic, not competition data.
"""

import json
import sqlite3
from pathlib import Path

import openpyxl

ORDERS_CSV = """BÁO CÁO ĐƠN HÀNG;;;;
Cửa hàng: Shop 1;;;;
Mã đơn;Ngày;Mã SP;Số lượng;Thành tiền (VNĐ)
D1;20/10/2026;SP01;2;1.200.000
D2;21/10/2026;SP02;1;350.000
D3;22/10/2026;SP01;1;600.000
D4;27/10/2026;SP02;3;1.050.000
"""


def _write_products_xlsx(path):
    book = openpyxl.Workbook()
    sheet = book.active
    sheet.title = "Sản phẩm"
    sheet.append(["DANH MỤC SẢN PHẨM", None, None])
    sheet.merge_cells("A1:C1")
    sheet.append(["Mã SP", "Tên sản phẩm", "Nhóm"])
    sheet.append(["SP01", "Cà phê sữa", "Đồ uống"])
    sheet.append(["SP02", "Bánh mì", None])
    sheet.merge_cells("C3:C4")  # both products are in the "Đồ uống" group
    other = book.create_sheet("Ghi chú")
    other.append(["Ghi chú"])
    other.append(["mở cửa 7h"])
    book.save(path)


def write_toy_split(root: Path) -> Path:
    """Write a split with one business `shop1` and two labelled questions under `root`."""
    shop = root / "businesses" / "shop1"
    shop.mkdir(parents=True)
    (shop / "README.md").write_text("Quán cà phê nhỏ. Doanh thu = thành tiền.")
    (shop / "orders.csv").write_text(ORDERS_CSV, encoding="utf-8")
    _write_products_xlsx(shop / "products.xlsx")
    conn = sqlite3.connect(shop / "staff.sqlite")
    conn.execute("CREATE TABLE nhan_vien (id INTEGER, ten TEXT)")
    conn.execute("INSERT INTO nhan_vien VALUES (1, 'Lan'), (2, 'Minh')")
    conn.commit()
    conn.close()
    questions = [
        {
            "id": "q1",
            "business_id": "shop1",
            "question": "doanh thu tuần rồi",
            "as_of_date": "2026-10-28",
            "type": "number",
            "answer": 2150000,
        },
        {
            "id": "q2",
            "business_id": "shop1",
            "question": "cà fê sữa bán bao nhiêu ly",
            "as_of_date": "2026-10-28",
            "type": "number",
            "answer": 3,
        },
    ]
    (root / "questions.jsonl").write_text(
        "\n".join(json.dumps(q, ensure_ascii=False) for q in questions)
    )
    return root
