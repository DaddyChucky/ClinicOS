from __future__ import annotations

import argparse
import sys
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy import func, select
from sqlalchemy.engine import Engine

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings, is_postgres_url, is_sqlite_url, normalize_database_url

TABLE_COPY_ORDER = [
    "users",
    "conversations",
    "messages",
    "agent_runs",
    "escalations",
    "prospects",
    "outreach_drafts",
    "campaign_drafts",
    "review_decisions",
    "conversation_controls",
    "conversation_profile_overrides",
    "system_controls",
    "conversation_event_logs",
    "conversation_deletions",
]


def _load_table(engine: Engine, table_name: str) -> sa.Table:
    metadata = sa.MetaData()
    return sa.Table(table_name, metadata, autoload_with=engine)


def _target_default_url() -> str | None:
    settings = get_settings()
    if not settings.database_url:
        return None
    return normalize_database_url(settings.database_url)


def _source_default_url() -> str:
    return get_settings().sqlite_fallback_url


def _shared_columns(source_table: sa.Table, target_table: sa.Table) -> list[str]:
    source_column_names = set(source_table.c.keys())
    return [column.name for column in target_table.columns if column.name in source_column_names]


def _assert_target_tables_exist(source_engine: Engine, target_engine: Engine) -> None:
    source_tables = set(sa.inspect(source_engine).get_table_names())
    target_tables = set(sa.inspect(target_engine).get_table_names())

    missing_targets = [table_name for table_name in TABLE_COPY_ORDER if table_name in source_tables and table_name not in target_tables]
    if missing_targets:
        raise ValueError(
            "Target database is missing required tables. Run migrations first. Missing: "
            + ", ".join(missing_targets)
        )


def _assert_target_is_empty(target_engine: Engine) -> None:
    with target_engine.connect() as connection:
        for table_name in TABLE_COPY_ORDER:
            if table_name not in sa.inspect(target_engine).get_table_names():
                continue
            table = _load_table(target_engine, table_name)
            row_count = connection.execute(select(func.count()).select_from(table)).scalar_one()
            if row_count:
                raise ValueError(
                    f"Target table '{table_name}' already contains {row_count} rows. "
                    "Use an empty target database to avoid accidental overwrites."
                )


def _copy_table_rows(source_engine: Engine, target_engine: Engine, table_name: str) -> int:
    source_tables = set(sa.inspect(source_engine).get_table_names())
    if table_name not in source_tables:
        return 0

    source_table = _load_table(source_engine, table_name)
    target_table = _load_table(target_engine, table_name)
    shared_columns = _shared_columns(source_table, target_table)
    if not shared_columns:
        return 0

    with source_engine.connect() as source_connection:
        rows = [
            dict(row)
            for row in source_connection.execute(
                select(*(source_table.c[column_name] for column_name in shared_columns))
            ).mappings()
        ]

    if not rows:
        return 0

    with target_engine.begin() as target_connection:
        target_connection.execute(
            target_table.insert(),
            [{column_name: row[column_name] for column_name in shared_columns} for row in rows],
        )
    return len(rows)


def _reset_postgres_sequences(target_engine: Engine) -> None:
    if not is_postgres_url(str(target_engine.url)):
        return

    with target_engine.begin() as connection:
        for table_name in TABLE_COPY_ORDER:
            if table_name not in sa.inspect(target_engine).get_table_names():
                continue
            table = _load_table(target_engine, table_name)
            if "id" not in table.c:
                continue
            max_id = connection.execute(select(func.max(table.c.id))).scalar_one()
            if max_id is None:
                continue
            connection.execute(
                sa.text(
                    f"""
                    SELECT setval(
                        pg_get_serial_sequence('{table_name}', 'id'),
                        :max_id,
                        true
                    )
                    """
                ),
                {"max_id": int(max_id)},
            )


def copy_sqlite_to_database(source_url: str, target_url: str) -> dict[str, int]:
    normalized_source = normalize_database_url(source_url)
    normalized_target = normalize_database_url(target_url)

    if not is_sqlite_url(normalized_source):
        raise ValueError("Source URL must point to a SQLite database.")
    if normalized_source == normalized_target:
        raise ValueError("Source and target databases must be different.")

    source_engine = sa.create_engine(normalized_source, future=True)
    target_engine = sa.create_engine(normalized_target, future=True)

    _assert_target_tables_exist(source_engine, target_engine)
    _assert_target_is_empty(target_engine)

    copied_rows: dict[str, int] = {}
    for table_name in TABLE_COPY_ORDER:
        copied_rows[table_name] = _copy_table_rows(source_engine, target_engine, table_name)

    _reset_postgres_sequences(target_engine)
    return copied_rows


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Copy an existing ClinicOS SQLite database into a migrated target database. "
            "Run Alembic migrations on the target first."
        )
    )
    parser.add_argument(
        "--source-url",
        default=None,
        help=f"SQLite source database URL. Defaults to { _source_default_url() }",
    )
    parser.add_argument(
        "--target-url",
        default=None,
        help="Target database URL. Defaults to DATABASE_URL when it is set.",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    source_url = args.source_url or _source_default_url()
    target_url = args.target_url or _target_default_url()
    if not target_url:
        parser.error("Provide --target-url or set DATABASE_URL to the target database.")

    copied_rows = copy_sqlite_to_database(source_url=source_url, target_url=target_url)
    print("SQLite data copy complete.")
    for table_name, row_count in copied_rows.items():
        print(f"- {table_name}: {row_count}")


if __name__ == "__main__":
    main()
