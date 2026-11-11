from src.modules.context.readme import readme_excerpt


def test_a_short_readme_is_unchanged():
    text = "# Dữ liệu\n\nSổ bán hàng."
    assert readme_excerpt(text) == text


def test_a_long_readme_keeps_its_conventions_section():
    head = "# Dữ liệu shop\n\n" + ("## Cột trong `orders`\n- **Ngày**: ngày bán\n" * 200)
    tail = "## Quy ước\n- Dữ liệu có đến hết 24/06/2026.\n- Trả hàng ghi số lượng âm."
    out = readme_excerpt(head + tail, limit=1500)
    assert len(out) <= 1500
    assert "## Quy ước" in out and "số lượng âm" in out
    assert out.startswith("# Dữ liệu shop")


def test_a_long_readme_without_conventions_is_cut():
    text = "## Cột\n" + ("- cột dài\n" * 500)
    out = readme_excerpt(text, limit=200)
    assert len(out) <= 200 and "Quy ước" not in out
