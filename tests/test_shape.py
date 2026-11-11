import pandas as pd
import pytest

from src.modules.questions.shape import Shape, coerce, infer_shape


@pytest.mark.parametrize(
    "question, answer_type",
    [
        ("doanh thu tháng 7/2025 là bao nhiêu", "number"),
        ("tháng này cửa hàng bán được bao nhiêu đơn", "number"),
        ("tỉ lệ huỷ đơn tháng 2/2025 là bao nhiêu %", "percent"),
        ("doanh thu tháng 5/2026 tăng bao nhiêu % so với tháng trước", "percent"),
        ("doanh thu 3 tháng 4/2026, 5/2026, 6/2026 có tăng liên tục không", "boolean"),
        ("lô thuốc gần hết hạn nhất có hạn dùng ngày nào", "date"),
        ("liệt kê 5 mặt hàng bán chạy nhất tuần rồi", "list"),
        ("top 3 khách hàng mua nhiều tiền nhất tháng 5/2026 là ai", "list"),
        ("khách nào mua nhiều tiền nhất tháng 6/2025", "string"),
        ("tháng 5/2025 hàng nào bán chạy nhất", "string"),
    ],
)
def test_answer_type_from_the_wording(question, answer_type):
    shape = infer_shape(question)
    assert shape.answer_type == answer_type and shape.strong


@pytest.mark.parametrize(
    "question, answer_type",
    [
        # a concentration in a product name is not a percentage question
        ("tháng 7/2025 Otrivin 0,1% xịt mũi bán được bao nhiêu chai", "number"),
        # "mọi loại" (all) is a scope, not "mỗi loại" (each): one total, not a list
        ("số ly size L bán được là bao nhiêu, tính mọi loại đồ uống", "number"),
        # "ít nhất 4 đơn" is a filter, not the superlative "fewest"
        ("số khách mua ít nhất 4 đơn trong tháng 12/2025 là bao nhiêu", "number"),
        # "không ai mua" is not a question about a person
        ("7 ngày gần nhất có mấy mặt hàng ế, không ai mua cái nào", "number"),
        # "kém" (lower) folds to "kem" like "kèm", but it is not a request for two columns
        ("doanh thu tháng 5/2026 hơn hay kém tháng trước bao nhiêu %", "percent"),
    ],
)
def test_the_wording_traps(question, answer_type):
    assert infer_shape(question).answer_type == answer_type


def test_list_of_names_vs_measures():
    assert infer_shape("liệt kê 3 khách chi tiêu nhiều nhất tháng 5/2026").list_of == "names"
    assert infer_shape(
        "doanh thu 3 tháng 1/2026, 2/2026, 3/2026 lần lượt là bao nhiêu"
    ).list_of == ("measures")
    assert infer_shape("dthu các đơn trả bằng cod và tiền mặt mỗi loại bao nhiêu").list_of == (
        "measures"
    )


def test_a_debt_table_is_still_a_table():
    shape = infer_shape(
        "tính đến hết ngày 28/07/2026, 3 khách nào đang nợ nhiều nhất, mỗi người còn nợ bao nhiêu"
    )
    assert shape.answer_type == "table"


def test_table_narrowed_to_the_names_the_question_lists():
    frame = pd.DataFrame({"khach_hang": ["Lan", "Hùng"], "tong": [900, 700]})
    shape = infer_shape("liệt kê 2 khách chi tiêu nhiều nhất tháng 5/2026")
    answer_type, out = coerce("table", frame, shape)
    assert answer_type == "list" and out.iloc[:, 0].tolist() == ["Lan", "Hùng"]


def test_table_narrowed_to_the_one_measure():
    frame = pd.DataFrame({"thang": ["2026-01", "2026-02"], "doanh_thu": [900, 700]})
    shape = infer_shape("doanh thu 2 tháng 1/2026, 2/2026 lần lượt là bao nhiêu")
    answer_type, out = coerce("table", frame, shape)
    assert answer_type == "list" and out.iloc[:, 0].tolist() == [900, 700]


def test_two_measure_columns_are_flattened_in_row_order():
    frame = pd.DataFrame({"no_them": [921000], "da_tra": [311500]})
    shape = infer_shape("khách A tháng này nợ thêm bao nhiêu, trả được bao nhiêu")
    answer_type, out = coerce("table", frame, shape)
    assert answer_type == "list" and out.iloc[:, 0].tolist() == [921000, 311500]


def test_a_single_cell_list_becomes_the_scalar():
    shape = infer_shape("doanh thu tháng 7 là bao nhiêu")
    answer_type, _ = coerce("list", pd.DataFrame({"v": [42]}), shape)
    assert answer_type == "number"


def test_nothing_is_coerced_without_a_strong_cue():
    shape = Shape()
    frame = pd.DataFrame({"a": [1], "b": [2]})
    assert coerce("table", frame, shape)[0] == "table"
