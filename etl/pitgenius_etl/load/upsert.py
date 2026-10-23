"""Idempotent Postgres upserts, keyed on each table's unique constraint.

Every ETL write goes through here so re-running a season/round is always
safe — the second run produces identical row counts and just refreshes
values that changed (e.g. a post-race time penalty updating points).
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import Table
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session as OrmSession


def upsert_rows(
    session: OrmSession,
    table: Table,
    rows: list[dict[str, Any]],
    conflict_cols: list[str],
    update_cols: list[str] | None = None,
) -> None:
    """Bulk upsert `rows` into `table`, returning nothing.

    `conflict_cols` must match an existing unique constraint on the table.
    `update_cols` defaults to the columns actually present in `rows`, minus the
    conflict columns and `id`/`created_at`.

    Deriving this from the rows rather than from the full table definition is
    load-bearing: for a column the rows omit, `excluded.<col>` is that column's
    default (NULL), so including it here would blank out data written by some
    other process. That is exactly how a circuits upsert carrying only the
    Jolpica reference fields silently wiped every circuit's `track_outline`
    and 3D normalization params on each ETL run.
    """
    if not rows:
        return

    if update_cols is None:
        present = {key for row in rows for key in row}
        skip = set(conflict_cols) | {"id", "created_at"}
        update_cols = [c.name for c in table.columns if c.name in present and c.name not in skip]

    stmt = insert(table).values(rows)
    if update_cols:
        update_dict = {col: getattr(stmt.excluded, col) for col in update_cols}
        stmt = stmt.on_conflict_do_update(index_elements=conflict_cols, set_=update_dict)
    else:
        # Nothing to refresh (e.g. sessions, whose rows carry only the conflict
        # columns) — an empty DO UPDATE SET is invalid SQL.
        stmt = stmt.on_conflict_do_nothing(index_elements=conflict_cols)
    session.execute(stmt)


def fetch_ref_id_map(session: OrmSession, table: Table, ref_col: str, id_col: str = "id") -> dict[str, int]:
    """e.g. fetch_ref_id_map(session, Driver.__table__, 'driver_ref') -> {'max_verstappen': 1, ...}"""
    result = session.execute(table.select().with_only_columns(table.c[ref_col], table.c[id_col]))
    return {row[0]: row[1] for row in result}
