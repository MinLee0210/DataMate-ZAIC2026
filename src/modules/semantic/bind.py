"""The rulebook as executable views, bound to whatever columns a shop has.

`roles.py` says which column plays which part. This module writes the views once:

    v_sales       one row per order line (or per order when the shop has no line table):
                  order_code, sale_date, status, is_cancelled/is_returned/is_valid,
                  customer_code/name, item_code/name, quantity, base_quantity, unit,
                  unit_price, line_total, order_paid, payment_method, channel, staff
    v_orders      one row per order, derived from v_sales: min date, bool_and(valid),
                  sum(line_total), any customer
    v_products    item_code, item_name, base_unit, big_unit, factor, cost_price, category
    v_stock       item_code, item_name, quantity, unit
    v_purchases   purchase_code, purchase_date, status, supplier, item_name, quantity,
                  unit, amount

This is what the old semantic layer did not have: rulebook §1 (valid orders, revenue by order
date, line totals before the order discount) and §3 (a customer is a code, walk-in is nobody)
now happen in SQL, not in a 9B model's reading of a prompt.

Every statement is best-effort: a view that cannot be built is skipped and the generic prompt
path still works. No view is ever keyed on a business id.
"""

import duckdb

from src.models import SchemaCard
from src.modules.semantic.roles import TableRoles, detect_roles
from src.utils import get_logger

logger = get_logger(__name__)

# the standardized columns of v_sales: (role, type, name in the view)
STANDARD = (
    ("order_code", "text", "order_code"),
    ("order_date", "date", "sale_date"),
    ("status", "text", "status"),
    ("customer_code", "text", "customer_code"),
    ("customer_name", "text", "customer_name"),
    ("item_code", "text", "item_code"),
    ("item_name", "text", "item_name"),
    ("quantity", "num", "quantity"),
    ("base_quantity", "num", "base_quantity"),
    ("unit", "text", "unit"),
    ("unit_price", "num", "unit_price"),
    ("line_total", "num", "line_total"),
    ("paid", "num", "order_paid"),
    ("payment_method", "text", "payment_method"),
    ("channel", "text", "channel"),
    ("staff", "text", "staff"),
)
_NULL = {
    "date": "CAST(NULL AS DATE)",
    "num": "CAST(NULL AS DOUBLE)",
    "text": "CAST(NULL AS VARCHAR)",
}


class SalesSource:
    """The tables that make up the sales fact: an order header, its lines, or a flat book."""

    def __init__(
        self,
        header: TableRoles | None = None,
        detail: TableRoles | None = None,
        flat: TableRoles | None = None,
    ) -> None:
        self.header = header
        self.detail = detail
        self.flat = flat


def _q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _cast(roles: TableRoles, role: str, kind: str, alias: str) -> str:
    """`alias."column"` cast to the view's type, or NULL when the role is missing."""
    column = roles.column(role)
    if column is None:
        return _NULL[kind]
    expr = f"{alias}.{_q(column)}"
    if kind == "date":
        return f"TRY_CAST({expr} AS DATE)"
    if kind == "num":
        return f"TRY_CAST({expr} AS DOUBLE)"
    return f"TRY_CAST({expr} AS VARCHAR)"


def _line_total(roles: TableRoles, alias: str) -> str:
    """The line's money: its own line total, else the order total, else qty x price - discount."""
    if roles.column("line_total") or roles.column("order_total"):
        role = "line_total" if roles.column("line_total") else "order_total"
        return _cast(roles, role, "num", alias)
    if roles.column("quantity") and roles.column("unit_price"):
        expr = (
            f"{_cast(roles, 'quantity', 'num', alias)} * {_cast(roles, 'unit_price', 'num', alias)}"
        )
        if roles.column("discount"):
            expr += f" - COALESCE({_cast(roles, 'discount', 'num', alias)}, 0)"
        return expr
    return _NULL["num"]


def _row(roles: TableRoles, alias: str, with_order_paid: bool) -> str:
    """The standardized SELECT list for one table."""
    parts = []
    for role, kind, name in STANDARD:
        if role == "paid" and not with_order_paid:
            parts.append(f"{_NULL['num']} AS order_paid")
            continue
        if role == "line_total":
            parts.append(f"{_line_total(roles, alias)} AS line_total")
            continue
        parts.append(f"{_cast(roles, role, kind, alias)} AS {name}")
    return ",\n         ".join(parts)


def _grain(roles: TableRoles) -> float:
    """Rows per order code: ~1 for a header table, small for a line table."""
    column = roles.roles.get("order_code")
    if column is None or not roles.table.rows:
        return 0.0
    distinct = next((c.distinct for c in roles.table.columns if c.name == column.column), 0)
    return distinct / roles.table.rows


def _pick_sales(detected: list[TableRoles]) -> SalesSource:
    """Header = one row per order; detail = one row per line; flat = no order code at all."""
    candidates = [r for r in detected if r.kind == "sales"]
    headers = [
        r
        for r in candidates
        if r.column("order_code") and r.column("order_date") and _grain(r) >= 0.8
    ]
    details = [
        r
        for r in candidates
        if r.column("order_code")
        and (r.column("item_name") or r.column("item_code"))
        and (r.column("line_total") or (r.column("quantity") and r.column("unit_price")))
        and _grain(r) < 0.8
    ]
    flats = [
        r
        for r in candidates
        if not r.column("order_code")
        and r.column("order_date")
        and (r.column("line_total") or (r.column("quantity") and r.column("unit_price")))
    ]

    def header_score(roles: TableRoles) -> float:
        """A sales header carries the order's status/customer, not just a payment amount.

        A cash book has an order code, a date and an amount too, and often more rows than the
        invoice table; picking it as the header leaves every order without a status."""
        score = 0.0
        if roles.column("status"):
            score += 2
        if roles.column("customer_code") or roles.column("customer_name"):
            score += 1
        if roles.column("order_total") or roles.column("line_total"):
            score += 1
        if roles.column("payment_method") and not roles.column("status"):
            score -= 2
        return score

    return SalesSource(
        header=max(
            headers, key=lambda r: (header_score(r), r.table.rows, r.table.name), default=None
        ),
        detail=max(details, key=lambda r: (r.table.rows, r.table.name), default=None),
        flat=max(flats, key=lambda r: (r.table.rows, r.table.name), default=None),
    )


def _flags(inner: str, has_customer: bool) -> str:
    """Wrap a SELECT that has `status` and add the rulebook §1 and §3 flags."""
    walk_in = (
        "CASE WHEN customer_code IS NOT NULL THEN false ELSE is_walk_in(customer_name) END"
        if has_customer
        else "false"
    )
    # rulebook §1: an order with any returned line is a returned order, so one negative quantity
    # invalidates every line of that order (a return written as a negative line, no status)
    returned_line = (
        "CASE WHEN order_code IS NULL THEN COALESCE(quantity, 0) < 0"
        " ELSE BOOL_OR(COALESCE(quantity, 0) < 0) OVER (PARTITION BY order_code) END"
    )
    return (
        "SELECT *, is_cancelled(status) AS is_cancelled,"
        " is_returned(status) AS is_returned,"
        f" (NOT is_cancelled(status) AND NOT is_returned(status) AND NOT {returned_line})"
        " AS is_valid,"
        f" {walk_in} AS is_walk_in\n"
        f"     FROM (\n       SELECT {inner}\n     ) s"
    )


def _has_customer(*tables: TableRoles | None) -> bool:
    return any(
        t is not None and (t.column("customer_code") or t.column("customer_name")) for t in tables
    )


def _sales_sql(source: SalesSource) -> str | None:
    """CREATE VIEW v_sales, or None when no sales table has a usable date."""
    if source.detail is not None:
        detail = source.detail
        detail_date = detail.column("order_date")
        header = source.header
        if header is not None and (header.column("order_date") or detail_date):
            header_rows = _row(header, "h", with_order_paid=False)
            code = _q(detail.column("order_code") or "order_code")
            select = []
            for role, kind, name in STANDARD:
                if role == "paid":
                    # a header amount repeated on every line must not be summed once per line
                    select.append(f"{_NULL['num']} AS order_paid")
                    continue
                left = (
                    _line_total(detail, "d")
                    if role == "line_total"
                    else _cast(detail, role, kind, "d")
                )
                select.append(f"COALESCE({left}, hdr.{name}) AS {name}")
            join = (
                "WITH h AS (\n"
                f"         SELECT {header_rows} FROM {_q(header.table.name)} h\n"
                "       ),\n"
                "       h1 AS (\n"
                "         SELECT * FROM (SELECT h.*,"
                " ROW_NUMBER() OVER (PARTITION BY order_code) AS rn FROM h) WHERE rn = 1\n"
                "       )\n"
                "     "
            )
            inner = (
                ",\n         ".join(select)
                + f"\n       FROM {_q(detail.table.name)} d"
                + f" LEFT JOIN h1 hdr ON TRY_CAST(d.{code} AS VARCHAR) = hdr.order_code"
            )
            flags = _flags(inner, _has_customer(header, detail))
            return f"CREATE OR REPLACE VIEW v_sales AS\n{join}{flags}"
        if detail_date:
            inner = f"{_row(detail, 'd', with_order_paid=False)} FROM {_q(detail.table.name)} d"
            return f"CREATE OR REPLACE VIEW v_sales AS\n{_flags(inner, _has_customer(detail))}"
    if source.header is not None:
        header = source.header
        if not header.column("order_date"):
            return None
        inner = f"{_row(header, 'h', with_order_paid=True)} FROM {_q(header.table.name)} h"
        return f"CREATE OR REPLACE VIEW v_sales AS\n{_flags(inner, _has_customer(header))}"
    if source.flat is not None:
        flat = source.flat
        inner = f"{_row(flat, 'f', with_order_paid=False)} FROM {_q(flat.table.name)} f"
        return f"CREATE OR REPLACE VIEW v_sales AS\n{_flags(inner, _has_customer(flat))}"
    return None


def _orders_sql() -> str:
    return (
        "CREATE OR REPLACE VIEW v_orders AS\n"
        "SELECT order_code,\n"
        "       MIN(sale_date) AS order_date,\n"
        "       MIN(status) AS status,\n"
        "       BOOL_AND(is_valid) AS is_valid,\n"
        "       BOOL_AND(is_walk_in) AS is_walk_in,\n"
        "       ANY_VALUE(customer_code) AS customer_code,\n"
        "       ANY_VALUE(customer_name) AS customer_name,\n"
        "       SUM(line_total) AS order_total,\n"
        "       ANY_VALUE(payment_method) AS payment_method,\n"
        "       ANY_VALUE(channel) AS channel,\n"
        "       ANY_VALUE(staff) AS staff\n"
        "FROM v_sales WHERE order_code IS NOT NULL GROUP BY order_code"
    )


def _products_sql(roles: TableRoles) -> str | None:
    if not (roles.column("item_code") or roles.column("item_name")):
        return None
    body = ",\n         ".join(
        (
            f"{_cast(roles, 'item_code', 'text', 't')} AS item_code",
            f"{_cast(roles, 'item_name', 'text', 't')} AS item_name",
            f"{_cast(roles, 'base_unit', 'text', 't')} AS base_unit",
            f"{_cast(roles, 'unit', 'text', 't')} AS big_unit",
            f"{_cast(roles, 'unit_factor', 'num', 't')} AS factor",
            f"{_cast(roles, 'cost_price', 'num', 't')} AS cost_price",
            f"{_cast(roles, 'category', 'text', 't')} AS category",
        )
    )
    return (
        "CREATE OR REPLACE VIEW v_products AS\n"
        "SELECT item_code, item_name, base_unit, big_unit, factor, cost_price, category\n"
        f"FROM (SELECT {body}, ROW_NUMBER() OVER"
        " (PARTITION BY COALESCE(item_code, item_name)) AS rn"
        f" FROM {_q(roles.table.name)} t) WHERE rn = 1"
    )


def _stock_sql(roles: TableRoles) -> str | None:
    if not roles.column("stock_qty"):
        return None
    body = ",\n         ".join(
        (
            f"{_cast(roles, 'item_code', 'text', 't')} AS item_code",
            f"{_cast(roles, 'item_name', 'text', 't')} AS item_name",
            f"{_cast(roles, 'stock_qty', 'num', 't')} AS quantity",
            f"{_cast(roles, 'unit', 'text', 't')} AS unit",
        )
    )
    return f"CREATE OR REPLACE VIEW v_stock AS\nSELECT {body} FROM {_q(roles.table.name)} t"


def _purchases_sql(roles: TableRoles) -> str | None:
    if not roles.column("purchase_date"):
        return None
    body = ",\n         ".join(
        (
            f"{_cast(roles, 'order_code', 'text', 't')} AS purchase_code",
            f"{_cast(roles, 'purchase_date', 'date', 't')} AS purchase_date",
            f"{_cast(roles, 'status', 'text', 't')} AS status",
            f"{_cast(roles, 'supplier', 'text', 't')} AS supplier",
            f"{_cast(roles, 'item_name', 'text', 't')} AS item_name",
            f"{_cast(roles, 'quantity', 'num', 't')} AS quantity",
            f"{_cast(roles, 'unit', 'text', 't')} AS unit",
            f"{_cast(roles, 'purchase_total', 'num', 't')} AS amount",
        )
    )
    return f"CREATE OR REPLACE VIEW v_purchases AS\nSELECT {body} FROM {_q(roles.table.name)} t"


def describe_views(conn: duckdb.DuckDBPyConnection, names: list[str]) -> list[str]:
    """`v_sales(order_code, sale_date, ...)`, the block the prompt shows."""
    described = []
    for name in names:
        try:
            cursor = conn.execute(f"SELECT * FROM {_q(name)} LIMIT 0")
            columns = [item[0] for item in cursor.description]
            described.append(f"{name}({', '.join(columns)})")
        except duckdb.Error:  # a view that disappeared must not break the context
            continue
    return described


def build_semantic_views(conn: duckdb.DuckDBPyConnection, card: SchemaCard) -> list[str]:
    """Create the rulebook views this business supports; return their descriptions."""
    detected = detect_roles(card)
    source = _pick_sales(detected)
    sales = _sales_sql(source)
    statements: list[tuple[str, str]] = []
    if sales:
        statements.append(("v_sales", sales))
        if source.detail is not None or source.header is not None:
            statements.append(("v_orders", _orders_sql()))
    # a shop often has both a catalogue and a conversion table: prefer the richer one
    catalogues = [r for r in detected if r.kind == "products"]
    products = max(catalogues, key=lambda r: (len(r.roles), r.table.rows), default=None)
    if products is not None and (sql := _products_sql(products)):
        statements.append(("v_products", sql))
    stock = next((r for r in detected if r.kind == "stock"), None)
    if stock is not None and (sql := _stock_sql(stock)):
        statements.append(("v_stock", sql))
    purchase = next((r for r in detected if r.kind == "purchases"), None)
    if purchase is not None and (sql := _purchases_sql(purchase)):
        statements.append(("v_purchases", sql))

    created = []
    for name, sql in statements:
        try:
            conn.execute(sql)
            created.append(name)
        except duckdb.Error as e:
            logger.info("semantic view %s: skipped (%s)", name, str(e)[:160])
    return describe_views(conn, created)


def sales_source_table(card: SchemaCard) -> str | None:
    """The table v_sales is built from, for the log line at ingest."""
    source = _pick_sales(detect_roles(card))
    roles = source.detail or source.header or source.flat
    return roles.table.name if roles is not None else None
