import pandas as pd

from src.models import ColumnCard, SchemaCard, TableCard
from src.modules.context.literals import ValueIndex, literal_warnings, sql_literals


def _index():
    card = SchemaCard(
        business_id="b",
        tables=[
            TableCard(
                name="don",
                source="x",
                rows=3,
                columns=[
                    ColumnCard(name="trang_thai", original="Trạng thái", dtype="VARCHAR"),
                    ColumnCard(name="tien", original="Tiền", dtype="BIGINT"),
                ],
            )
        ],
    )
    frame = pd.DataFrame({"trang_thai": ["Đã huỷ", "Hoàn thành", "Trả hàng"]})
    return ValueIndex.build(card, lambda sql: frame if "trang_thai" in sql else pd.DataFrame())


def test_sql_literals_reads_equality_in_and_like():
    code = (
        "SELECT 1 FROM don WHERE a = 'x' AND b IN ('y', 'it''s') AND c ILIKE '%z%' "
        "AND strftime(d, '%Y') = '2025' AND date_trunc('month', e) = DATE '2025-01-01'"
    )
    assert sql_literals(code) == [
        ("x", False),
        ("y", False),
        ("it's", False),
        ("%z%", True),
        ("2025", False),
    ]


def test_a_value_that_exists_matches_without_accents_or_case():
    index = _index()
    assert index.has("da huy", False) and index.has("HOÀN THÀNH", False)
    assert index.has("huy", True)  # LIKE '%huy%'


def test_a_missing_value_is_reported_with_the_closest_real_ones():
    warnings = literal_warnings(
        "SELECT COUNT(*) FROM don WHERE trang_thai IN ('Đã huỷ', 'khách hủy', 'Hủy đơn')", _index()
    )
    assert len(warnings) == 2
    assert "'khách hủy'" in warnings[0] and "'Đã huỷ'" in warnings[0]


def test_dates_and_non_string_columns_are_ignored():
    assert literal_warnings("SELECT 1 WHERE d >= '2025-03-01'", _index()) == []
