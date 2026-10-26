"""Build the DuckDB file and context cache of every business in a split.

uv run python -m scripts.ingest --split train
"""

import argparse

from src.config import settings
from src.data.layout import calendar_file, list_businesses, split_dir
from src.services.ingest import IngestService
from src.utils import get_logger

logger = get_logger("scripts.ingest")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--split", default="train")
    args = parser.parse_args(argv)
    root = split_dir(settings.data_dir, args.split)
    service = IngestService(settings.work_dir, calendar=calendar_file(root))
    failed = 0
    for package in list_businesses(root):
        try:
            context = service.load(package.name, package)
            logger.info(
                "%s: %d tables -> %s",
                package.name,
                len(context.card.tables),
                context.db_path.parent,
            )
        except Exception:
            failed += 1
            logger.exception("could not ingest %s", package.name)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
