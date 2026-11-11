"""Column roles: which column is the order code, the date, the status, the money, ... .

The semantic views (`bind.py`) need to be written once and work on 30 different export
templates. The names differ (`Mã hóa đơn`, `ma_bill`, `Số phiếu`, `mahoadon`); the role does
not. This module guesses the role of each column from its folded name, its type and the name of
its table, with a score, and classifies each table (sales, products, stock, purchases).

Deterministic, no LLM. A guess is only used above a threshold; a table whose kind is unclear
gets no view, and the old prompt-only path still applies.
"""

import re
from dataclasses import dataclass, field

from src.models import SchemaCard, TableCard
from src.utils.text import fold

DATE, NUM, TEXT = "date", "num", "text"


@dataclass(frozen=True)
class RoleSpec:
    patterns: tuple[tuple[str, float], ...]
    kind: str | None = None  # dtype family the column must belong to
    exclude: tuple[str, ...] = ()


# weights add up when several patterns match; 3 is a strong name, 1.5 a weak one
SPECS: dict[str, RoleSpec] = {
    "order_code": RoleSpec(
        (
            (r"(^|_)(ma|so|id)_?(don|hoa_don|hd|bill|phieu|order)(_|$)", 2.5),
            (r"^(ma_don_hang|ma_hoa_don|ma_hd|ma_bill|so_hoa_don|so_ct|so_phieu|mahoadon)$", 2.5),
            (r"(^|_)(ma|so)_(chung_tu|ct)(_|$)", 1.5),
            (r"^(hd)$", 2.0),
        ),
        TEXT,
        (r"nhap", r"giao", r"tra"),
    ),
    "order_date": RoleSpec(
        (
            (r"^(ngay_dat_hang|ngay_ban|ngay|thoi_gian)$", 3.0),
            (r"^(ngay|thoi_gian)_(dat|ban|lap|tao_don|mua)(_|$)", 2.5),
            (r"^(ngay|thoi_gian)(_|$)", 1.0),
        ),
        DATE,
        (r"sinh", r"han", r"giao_hang", r"nhap", r"tao", r"thanh_toan", r"hen"),
    ),
    "status": RoleSpec(
        ((r"(trang_thai|status|tinh_trang)", 3.0), (r"(^|_)tt(_|$)", 1.0)),
        TEXT,
        (r"hoa_don_dien_tu", r"hdđt"),
    ),
    "customer_code": RoleSpec(
        (
            (r"^(ma_kh|ma_khach|ma_khach_hang|makh|id_khach|ma_nguoi_mua)$", 3.0),
            (r"(^|_)ma_(kh|khach)(_|$)", 2.5),
        ),
        TEXT,
    ),
    "customer_name": RoleSpec(
        (
            (r"^(ten_khach_hang|ten_khach|ten_kh|khach_hang|khach|ten_nguoi_mua)$", 3.0),
            (r"(^|_)ten_(khach|kh)(_|$)", 2.5),
            (r"^(ho_ten|ten)$", 1.0),
        ),
        TEXT,
        (r"nha_cung_cap", r"nhan_vien", r"nguoi_tao", r"nguoi_ban", r"ghi_chu"),
    ),
    "item_code": RoleSpec(
        (
            (r"^(ma_hang|ma_hang_hoa|ma_san_pham|ma_sp|ma_sku|ma_barcode|ma_vach_ean)$", 3.0),
            (r"^(mahanghoa|ma_hh|ma_thuoc|ma_lo|id_sp|ma_hh_lien_quan|ma_mat_hang)$", 2.5),
            (r"(^|_)ma_(hang|sp|san_pham|sku|thuoc)(_|$)", 2.0),
        ),
        TEXT,
    ),
    "item_name": RoleSpec(
        (
            (
                r"^(ten_hang|ten_hang_hoa|ten_san_pham|ten_sp|ten_thuoc|hang_hoa|san_pham|hang)$",
                3.0,
            ),
            (r"^(ten|tengoi|product|noi_dung)$", 1.5),
            (r"^(hang_ban)$", 2.5),
            (r"(^|_)ten_(hang|sp|san_pham|thuoc)(_|$)", 2.5),
        ),
        TEXT,
        (r"khach", r"nhan_vien", r"nha_cung_cap", r"cong_ty", r"ghi_chu", r"mo_ta", r"hinh"),
    ),
    "quantity": RoleSpec(
        (
            (r"^(so_luong|sl|qty|quantity|sl_ban|so_luong_ban|sl_nhap|so_luong_san_pham)$", 3.0),
            (r"(^|_)(so_luong|sl)(_|$)", 1.5),
            (r"^(sl)$", 2.0),
        ),
        NUM,
        (r"quy_doi", r"le", r"giao", r"nhap", r"ton", r"dvt_co_ban"),
    ),
    "base_quantity": RoleSpec(
        (
            (r"^(so_luong_quy_doi|quy_ra_dv_le|slquydoi|so_luong_le|sl_le)$", 3.0),
            (r"(^|_)(quy_doi|quy_ra)(_|$)", 2.0),
            (r"^so_luong_dvt_co_ban$", 2.5),
        ),
        NUM,
    ),
    "unit": RoleSpec(
        ((r"^(don_vi_tinh|dvt|don_vi|donvitinh|unit|don_vi_ban)$", 2.5),),
        TEXT,
        (r"quy_doi", r"co_ban", r"goc", r"nhap"),
    ),
    "unit_factor": RoleSpec(
        (
            (r"^(ti_le_quy_doi|he_so_quy_doi|he_so|ty_le|factor|quy_doi)$", 3.0),
            (r"(^|_)(he_so|ti_le|ty_le)(_|$)", 1.5),
        ),
        NUM,
    ),
    "line_total": RoleSpec(
        (
            (r"^(thanh_tien|tri_gia|thanh_tien_d|line_total|tong_cong)$", 3.0),
            (r"^(tong_tien_hang|tien_hang|tong_tien|gia_tri|tong_don)$", 2.5),
            (r"^(tien|so_tien|amount|tong|tong_don)$", 3.0),
            (r"^(tt)$", 2.5),
            (r"(^|_)(thanh_tien|tri_gia)(_|$)", 2.0),
        ),
        NUM,
        (
            r"sau_giam",
            r"khach_phai_tra",
            r"con_no",
            r"da_tra",
            r"khach_da_tra",
            r"giam_gia",
            r"chiet_khau",
            r"von",
            r"nhap",
        ),
    ),
    "unit_price": RoleSpec(
        (
            (r"^(don_gia|don_gia_ban|gia_ban|gia_le|gia_san_pham|price|gia)$", 3.0),
            (r"(^|_)don_gia(_|$)", 2.0),
            (r"^(gia_1_dv|gia_ban_le|dg)$", 2.0),
        ),
        NUM,
        (r"nhap", r"von", r"goc", r"moi", r"cu", r"tri_gia"),
    ),
    "discount": RoleSpec(
        ((r"(giam_gia|chiet_khau|discount)", 3.0),),
        NUM,
    ),
    "order_total": RoleSpec(
        (
            (r"^(tong_tien_hang|tien_hang|tam_tinh|tong_truoc_giam|tong_tien|tong_cong)$", 3.0),
            (r"^(tong_sau_giam_gia|tong_thanh_toan|khach_phai_tra)$", 2.0),
        ),
        NUM,
        (r"nhap", r"von", r"con_no", r"da_tra"),
    ),
    "paid": RoleSpec(
        ((r"^(khach_da_tra|da_tra|tien_da_tra|da_thanh_toan|paid)$", 3.0),),
        NUM,
    ),
    "debt": RoleSpec(
        ((r"^(con_no|cong_no|no|no_con_lai|du_no)$", 3.0), (r"(^|_)con_no(_|$)", 2.5)),
        NUM,
    ),
    "payment_method": RoleSpec(
        (
            (r"(phuong_thuc_thanh_toan|hinh_thuc_thanh_toan|pttt|payment_method)", 3.0),
            (r"^(thanh_toan|payment)$", 1.5),
        ),
        TEXT,
    ),
    "channel": RoleSpec(
        ((r"(kenh_ban|kenh|channel|nguon_don|hinh_thuc_ban)", 3.0),),
        TEXT,
        (r"thanh_toan",),
    ),
    "staff": RoleSpec(
        ((r"(nhan_vien|nguoi_ban|nguoi_tao|staff|sales|ma_nv)", 2.5),),
        TEXT,
    ),
    "supplier": RoleSpec(
        ((r"(nha_cung_cap|ten_ncc|ncc|supplier|cong_ty)$", 3.0), (r"(^|_)ncc(_|$)", 2.5)),
        TEXT,
    ),
    "purchase_date": RoleSpec(
        (
            (r"^(ngay_nhap|ngay_phieu|thoi_gian_nhap|ngay_lap_phieu|ngay_nhap_hang)$", 3.0),
            (r"^(ngay|thoi_gian)$", 1.0),
        ),
        DATE,
        (r"sinh", r"han", r"giao", r"tao", r"thanh_toan"),
    ),
    "purchase_total": RoleSpec(
        ((r"^(can_tra_ncc|tien_nhap|tong_tien_nhap|thanh_tien|tong_tien)$", 2.5),),
        NUM,
        (r"khach", r"con_no", r"da_tra"),
    ),
    "stock_qty": RoleSpec(
        (
            (r"^(ton_cuoi|ton_cuoi_ky|ton_kho|ton|so_luong_ton|stock|ton_thuc_te)$", 3.0),
            (r"(^|_)ton(_|$)", 1.5),
        ),
        NUM,
        (r"lon_nhat", r"nho_nhat", r"toi_thieu", r"toi_da", r"dinh_muc"),
    ),
    "cost_price": RoleSpec(
        ((r"^(gia_von|gia_nhap|gia_goc|cost|cost_price|gia_von_don_vi)$", 3.0),),
        NUM,
    ),
    "category": RoleSpec(
        (
            (
                r"^(nhom_hang|nhom_hang_hoa|nhom_hang_3_cap|loai_hang|loai_hang_hoa|nhom|category)$",
                2.5,
            ),
            (r"(^|_)nhom(_|$)", 1.5),
        ),
        TEXT,
    ),
    "base_unit": RoleSpec(
        ((r"^(don_vi_co_ban|don_vi_goc|dvt_co_ban|base_unit|don_vi_le)$", 3.0),),
        TEXT,
    ),
}

SALES_HINT = re.compile(r"(hoadon|hoa_don|donhang|don_hang|banhang|ban_hang|sobanhang|chi_tiet)")
PURCHASE_HINT = re.compile(r"(nhap)")
STOCK_HINT = re.compile(r"(ton)")
CATALOG_HINT = re.compile(
    r"(sanpham|san_pham|hanghoa|hang_hoa|danhmuc|danh_muc|thuoc|banggia|quydoi|quy_doi|lo_hang)"
)
CUSTOMER_HINT = re.compile(r"(khach)")
STAFF_HINT = re.compile(r"(nhan_vien)")
KIND_THRESHOLD = 3.0


@dataclass(frozen=True)
class ColumnRole:
    table: str
    column: str
    dtype: str
    score: float


@dataclass
class TableRoles:
    table: TableCard
    kind: str = "other"  # sales | products | stock | purchases | customers | staff | other
    roles: dict[str, ColumnRole] = field(default_factory=dict)

    def column(self, role: str) -> str | None:
        hit = self.roles.get(role)
        return hit.column if hit else None


def _is_date(dtype: str) -> bool:
    return dtype.startswith(("DATE", "TIMESTAMP"))


def _is_num(dtype: str) -> bool:
    return dtype.startswith(
        ("BIGINT", "INTEGER", "INT", "SMALLINT", "TINYINT", "DOUBLE", "FLOAT", "REAL", "DECIMAL")
    )


def _is_text(dtype: str) -> bool:
    return dtype.startswith(("VARCHAR", "CHAR", "TEXT", "STRING", "BLOB"))


def _fits(kind: str | None, dtype: str) -> bool:
    if kind is None:
        return True
    if kind == DATE:
        return _is_date(dtype)
    if kind == NUM:
        return _is_num(dtype)
    return _is_text(dtype)


# some exports write the whole name without separators ("mahoadon", "tongtienhang"); map the
# common ones to their snake_case form before matching
ALIASES = {
    "mahoadon": "ma_hoa_don",
    "maphieu": "ma_phieu",
    "makhachhang": "ma_khach_hang",
    "makh": "ma_kh",
    "manhanvien": "ma_nhan_vien",
    "tenkhachhang": "ten_khach_hang",
    "tenkhach": "ten_khach",
    "tenhang": "ten_hang",
    "tenhanghoa": "ten_hang_hoa",
    "tensanpham": "ten_san_pham",
    "tensp": "ten_sp",
    "mahanghoa": "ma_hang_hoa",
    "mahang": "ma_hang",
    "masanpham": "ma_san_pham",
    "masp": "ma_sp",
    "tongtienhang": "tong_tien_hang",
    "tongtien": "tong_tien",
    "tienhang": "tien_hang",
    "thanhtien": "thanh_tien",
    "soluong": "so_luong",
    "soluongban": "so_luong_ban",
    "tongdon": "tong_don",
    "mamathang": "ma_mat_hang",
    "sluong": "so_luong",
    "soluongsanpham": "so_luong_san_pham",
    "slban": "sl_ban",
    "slnhap": "sl_nhap",
    "donvitinh": "don_vi_tinh",
    "kenhbanhang": "kenh_ban_hang",
    "kenhban": "kenh_ban",
    "ngaylap": "ngay_lap",
    "thoigianlap": "thoi_gian_lap",
    "ngaydat": "ngay_dat",
    "ngayban": "ngay_ban",
    "ngaynhap": "ngay_nhap",
    "thoigian": "thoi_gian",
    "tinhtrang": "tinh_trang",
    "trangthai": "trang_thai",
    "nhanvien": "nhan_vien",
    "nguoiban": "nguoi_ban",
    "nhacungcap": "nha_cung_cap",
    "tenncc": "ten_ncc",
    "toncuoi": "ton_cuoi",
    "toncuoiky": "ton_cuoi_ky",
    "tonkho": "ton_kho",
    "giavon": "gia_von",
    "gianhap": "gia_nhap",
    "giaban": "gia_ban",
    "giale": "gia_le",
    "dongia": "don_gia",
    "giamgia": "giam_gia",
    "chietkhau": "chiet_khau",
    "phuongthucthanhtoan": "phuong_thuc_thanh_toan",
    "hinhthucthanhtoan": "hinh_thuc_thanh_toan",
    "khachdatra": "khach_da_tra",
    "datra": "da_tra",
    "conno": "con_no",
    "congno": "cong_no",
    "donvicoban": "don_vi_co_ban",
    "donvigoc": "don_vi_goc",
    "tilequydoi": "ti_le_quy_doi",
    "hesosquydoi": "he_so_quy_doi",
    "heso": "he_so",
    "nhomhang": "nhom_hang",
    "nhomhanghoa": "nhom_hang_hoa",
    "loaihang": "loai_hang",
    "loaihanghoa": "loai_hang_hoa",
    "sotien": "so_tien",
    "hangban": "hang_ban",
}


def _excluded(folded: str, patterns: tuple[str, ...]) -> bool:
    """Word-bounded exclusion: "han" (expiry) must not match "thang" in "ngay_thang"."""
    return any(re.search(rf"(^|_){pattern}($|_)", folded) for pattern in patterns)


def _score_column(name: str, dtype: str) -> dict[str, float]:
    """Role -> score for one column (0 when a role's type or exclusion does not fit)."""
    # keep "_": identifiers are snake_case and the patterns are written that way
    folded = fold(name, keep="_")
    folded = ALIASES.get(folded, folded)
    scores: dict[str, float] = {}
    for role, spec in SPECS.items():
        if not _fits(spec.kind, dtype):
            continue
        if _excluded(folded, spec.exclude):
            continue
        score = sum(weight for pattern, weight in spec.patterns if re.search(pattern, folded))
        if score:
            scores[role] = score
    return scores


def detect_table(table: TableCard) -> TableRoles:
    """Best column per role in one table, and the table's kind."""
    found: TableRoles = TableRoles(table)
    for column in table.columns:
        for role, score in _score_column(column.name, column.dtype).items():
            current = found.roles.get(role)
            if current is None or score > current.score:
                found.roles[role] = ColumnRole(table.name, column.name, column.dtype, score)
    found.kind = _kind(table, found.roles, table.name)
    return found


def _kind(table: TableCard, roles: dict[str, ColumnRole], name: str) -> str:
    """Classify a table from its roles and its name. Score-based, one winner."""
    folded = fold(name, keep="_")
    dates = _is_date(roles["order_date"].dtype) if "order_date" in roles else False
    sales = 0.0
    if "order_code" in roles:
        sales += 2.0
    if "order_date" in roles or dates:
        sales += 2.5
    if "status" in roles:
        sales += 1.0
    if "line_total" in roles:
        sales += 1.5
    if "order_total" in roles:
        sales += 1.0
    if "quantity" in roles or "base_quantity" in roles:
        sales += 1.0
    if "customer_code" in roles or "customer_name" in roles:
        sales += 0.5
    if SALES_HINT.search(folded):
        sales += 1.0
    if PURCHASE_HINT.search(folded):
        sales -= 3.0
    if STOCK_HINT.search(folded):
        sales -= 3.0
    if CATALOG_HINT.search(folded) and "order_date" not in roles:
        sales -= 2.0

    products = 0.0
    if "item_code" in roles or "item_name" in roles:
        products += 2.0
    for role in ("unit_factor", "cost_price", "base_unit", "category"):
        if role in roles:
            products += 1.0
    if CATALOG_HINT.search(folded):
        products += 1.5
    if "order_date" in roles or "order_code" in roles:
        products -= 3.0

    stock = 0.0
    if "stock_qty" in roles:
        stock += 3.0
    if "item_code" in roles or "item_name" in roles:
        stock += 1.0
    if STOCK_HINT.search(folded):
        stock += 1.5

    purchases = 0.0
    if "purchase_date" in roles:
        purchases += 3.0
    if "supplier" in roles:
        purchases += 2.0
    if "purchase_total" in roles:
        purchases += 1.0
    if PURCHASE_HINT.search(folded):
        purchases += 1.5

    customers = 0.0
    if ("customer_code" in roles or "customer_name" in roles) and "order_code" not in roles:
        customers += 2.0
    if CUSTOMER_HINT.search(folded):
        customers += 2.0
    staff = 2.0 if STAFF_HINT.search(folded) and "order_code" not in roles else 0.0

    scored = {
        "sales": sales,
        "products": products,
        "stock": stock,
        "purchases": purchases,
        "customers": customers,
        "staff": staff,
    }
    kind, best = max(scored.items(), key=lambda kv: kv[1])
    return kind if best >= KIND_THRESHOLD else "other"


def detect_roles(card: SchemaCard) -> list[TableRoles]:
    """Every table of a business with its roles and kind (deterministic order)."""
    return [detect_table(table) for table in card.tables]
