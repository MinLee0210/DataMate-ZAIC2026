import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import duckdb

from src.config import settings
from src.models import SchemaCard
from src.modules.context import Entity, build_entity_dict, build_table_card, data_window
from src.modules.ingest import TABLE_SUFFIXES, merge_split_tables, read_tables
from src.modules.semantic import apply_semantic_layer
from src.utils import get_logger

logger = get_logger(__name__)

CALENDAR_TABLE = "lunar_calendar"
# part of the cache key: bump it when ingest output changes, so old caches are rebuilt
INGEST_VERSION = "15"


@dataclass
class BusinessContext:
    """Everything the QA graph needs about one business, built once and cached on disk."""

    business_id: str
    db_path: Path
    card: SchemaCard
    entities: list[Entity]
    semantic: list[str]


def _fingerprint(paths: list[Path]) -> str:
    digest = hashlib.sha256(INGEST_VERSION.encode())
    for path in sorted(paths):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


class IngestService:
    """Business package -> DuckDB file + schema card + entity dict, cached per content hash."""

    def __init__(self, work_dir: Path | None = None, calendar: Path | None = None) -> None:
        self.work_dir = work_dir or settings.work_dir
        self.calendar = calendar
        self._loaded: dict[str, BusinessContext] = {}

    def load(self, business_id: str, package_dir: Path) -> BusinessContext:
        if business_id in self._loaded:
            return self._loaded[business_id]
        files = sorted(p for p in package_dir.iterdir() if p.suffix.lower() in TABLE_SUFFIXES)
        if not files:
            raise FileNotFoundError(f"no data files in {package_dir}")
        inputs = files + [package_dir / "README.md"] * (package_dir / "README.md").is_file()
        if self.calendar:
            inputs.append(self.calendar)
        out = self.work_dir / "ingest" / f"{business_id}-{_fingerprint(inputs)}"
        if not (out / "context.json").is_file():
            self._build(business_id, package_dir, files, out)
        context = self._read(business_id, out)
        self._loaded[business_id] = context
        return context

    def _build(self, business_id: str, package_dir: Path, files: list[Path], out: Path) -> None:
        out.mkdir(parents=True, exist_ok=True)
        db_path = out / "db.duckdb"
        db_path.unlink(missing_ok=True)
        readme = package_dir / "README.md"
        card = SchemaCard(
            business_id=business_id, readme=readme.read_text().strip() if readme.is_file() else ""
        )
        conn = duckdb.connect(str(db_path))
        try:
            tables = merge_split_tables([t for f in files for t in read_tables(f, infer=False)])
            if self.calendar:
                for table in read_tables(self.calendar):
                    table.name = CALENDAR_TABLE
                    tables.append(table)
            names: set[str] = set()
            for table in tables:
                while table.name in names:
                    table.name += "_2"
                names.add(table.name)
                conn.register("_frame", table.frame)
                conn.execute(f'CREATE TABLE "{table.name}" AS SELECT * FROM _frame')
                conn.unregister("_frame")
                card.tables.append(
                    build_table_card(conn, table.name, table.source, table.originals)
                )
            card.data_start, card.data_end = data_window(card)
            semantic = apply_semantic_layer(conn, card)
            entities = build_entity_dict(conn, card)
        finally:
            conn.close()
        payload = {
            "card": card.model_dump(),
            "entities": [e.__dict__ for e in entities],
            "semantic": semantic,
        }
        # written last: its presence marks a complete build
        (out / "context.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1))
        logger.info(
            "ingested %s: %d tables, %d entities", business_id, len(card.tables), len(entities)
        )

    def _read(self, business_id: str, out: Path) -> BusinessContext:
        payload = json.loads((out / "context.json").read_text())
        return BusinessContext(
            business_id=business_id,
            db_path=out / "db.duckdb",
            card=SchemaCard.model_validate(payload["card"]),
            entities=[Entity(**e) for e in payload["entities"]],
            semantic=payload["semantic"],
        )
