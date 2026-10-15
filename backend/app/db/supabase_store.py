from __future__ import annotations

from dataclasses import fields
from datetime import date, datetime
from typing import Any

from app.db.store import TABLES, _coerce, _key, _model_from_row, _pk_column, _values

PAGE = 1000


def _encode(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def _encode_row(obj: Any) -> dict:
    return {name: _encode(value) for name, value in _values(obj).items()}


class SupabaseStore:
    """Data API unit of work. Writes go out on flush. rollback deletes those rows."""

    def __init__(self, client) -> None:
        self.client = client
        self.identity: dict[tuple[type, Any], Any] = {}
        self.snapshots: dict[tuple[type, Any], dict] = {}
        self.pending: list[Any] = []
        self.undo_inserts: list[tuple[type, Any]] = []

    def add(self, obj: Any) -> None:
        self.identity[(type(obj), _key(obj))] = obj
        self.pending.append(obj)

    def get(self, model: type, identifier: Any) -> Any:
        cached = self.identity.get((model, identifier))
        if cached is not None:
            return cached
        rows = self._select(model, {_pk_column(model): identifier})
        return self._hydrate(model, rows[0] if rows else None)

    def find(self, model: type, filt: dict | None = None, sort: list | None = None) -> list:
        self._flush_inserts()
        return [self._hydrate(model, row) for row in self._select(model, filt or {}, sort)]

    def find_one(self, model: type, filt: dict | None = None, sort: list | None = None) -> Any:
        rows = self.find(model, filt, sort)
        return rows[0] if rows else None

    def ids(self, model: type, filt: dict) -> list:
        self._flush_inserts()
        column = _pk_column(model)
        return [row[column] for row in self._select(model, filt, columns=column)]

    def maximum(self, model: type, field_name: str, filt: dict) -> Any:
        self._flush_inserts()
        rows = self._select(model, filt, sort=[(field_name, -1)], columns=field_name, limit=1)
        if not rows:
            return None
        return _coerce(field_name, rows[0].get(field_name))

    def delete(self, obj: Any) -> None:
        self._flush_updates()
        model = type(obj)
        identifier = _key(obj)
        self._delete_ids(model, [identifier])
        self.pending = [item for item in self.pending if item is not obj]
        key = (model, identifier)
        self.identity.pop(key, None)
        self.snapshots.pop(key, None)
        self.undo_inserts = [item for item in self.undo_inserts if item != (model, identifier)]

    def delete_many(self, model: type, filt: dict) -> None:
        self._flush_inserts()
        identifiers = self.ids(model, filt)
        self._delete_ids(model, identifiers)
        for identifier in identifiers:
            key = (model, identifier)
            self.identity.pop(key, None)
            self.snapshots.pop(key, None)
            self.undo_inserts = [item for item in self.undo_inserts if item != (model, identifier)]

    def flush(self) -> None:
        self._flush_inserts()
        self._flush_updates()

    def commit(self) -> None:
        self.flush()
        self.undo_inserts.clear()
        self.snapshots = {key: _values(obj) for key, obj in self.identity.items()}

    def rollback(self) -> None:
        self.pending.clear()
        for model, identifier in self.undo_inserts:
            self._delete_ids(model, [identifier])
            key = (model, identifier)
            self.identity.pop(key, None)
            self.snapshots.pop(key, None)
        self.undo_inserts.clear()
        for key, snap in list(self.snapshots.items()):
            model, identifier = key
            self._update(model, identifier, {name: _encode(value) for name, value in snap.items()})
            obj = self.identity.get(key)
            if obj is None:
                continue
            restored = _model_from_row(model, snap)
            for item in fields(model):
                setattr(obj, item.name, getattr(restored, item.name))

    def refresh(self, obj: Any) -> None:
        model = type(obj)
        identifier = _key(obj)
        rows = self._select(model, {_pk_column(model): identifier})
        if not rows:
            return
        fresh = _model_from_row(model, rows[0])
        for item in fields(model):
            setattr(obj, item.name, getattr(fresh, item.name))
        key = (model, identifier)
        self.identity[key] = obj
        self.snapshots[key] = _values(obj)

    def close(self) -> None:
        if self.pending or self.undo_inserts or self._dirty():
            self.rollback()

    def _dirty(self) -> bool:
        return any(self.snapshots.get(key) != _values(obj) for key, obj in self.identity.items())

    def _table(self, model: type) -> str:
        return TABLES[model].name

    def _select(
        self,
        model: type,
        filt: dict | None = None,
        sort: list | None = None,
        columns: str = "*",
        limit: int | None = None,
    ) -> list[dict]:
        rows: list[dict] = []
        start = 0
        while True:
            query = self.client.table(self._table(model)).select(columns)
            query = _filters(query, filt or {})
            for name, direction in sort or []:
                query = query.order(name, desc=direction < 0)
            size = PAGE if limit is None else min(PAGE, limit - len(rows))
            if size <= 0:
                break
            chunk = query.range(start, start + size - 1).execute().data or []
            rows.extend(chunk)
            if limit is not None or len(chunk) < size:
                break
            start += size
        return rows

    def _insert(self, model: type, obj: Any) -> None:
        self.client.table(self._table(model)).insert(_encode_row(obj)).execute()

    def _update(self, model: type, identifier: Any, values: dict) -> None:
        column = _pk_column(model)
        self.client.table(self._table(model)).update(values).eq(column, _encode(identifier)).execute()

    def _delete_ids(self, model: type, identifiers: list) -> None:
        if not identifiers:
            return
        column = _pk_column(model)
        encoded = [_encode(item) for item in identifiers]
        self.client.table(self._table(model)).delete().in_(column, encoded).execute()

    def _hydrate(self, model: type, row: dict | None) -> Any:
        if row is None:
            return None
        identifier = row[_pk_column(model)]
        key = (model, identifier)
        cached = self.identity.get(key)
        if cached is not None:
            return cached
        payload = {name: _coerce(name, value) for name, value in row.items()}
        obj = _model_from_row(model, payload)
        self.identity[key] = obj
        self.snapshots[key] = _values(obj)
        return obj

    def _flush_inserts(self) -> None:
        ready = list(self.pending)
        self.pending.clear()
        grouped: dict[type, list] = {}
        for obj in ready:
            grouped.setdefault(type(obj), []).append(obj)
        for model, objects in grouped.items():
            rows = [_encode_row(obj) for obj in objects]
            for start in range(0, len(rows), 200):
                self.client.table(self._table(model)).insert(rows[start : start + 200]).execute()
            for obj in objects:
                key = (model, _key(obj))
                self.undo_inserts.append(key)
                self.snapshots[key] = _values(obj)

    def _flush_updates(self) -> None:
        for key, obj in list(self.identity.items()):
            current = _values(obj)
            if self.snapshots.get(key) == current:
                continue
            model, identifier = key
            self._update(model, identifier, _encode_row(obj))


def _filters(query, filt: dict):
    for name, value in filt.items():
        if isinstance(value, dict):
            if "$in" in value:
                query = query.in_(name, [_encode(item) for item in value["$in"]])
            if "$gte" in value:
                query = query.gte(name, _encode(value["$gte"]))
            if "$lte" in value:
                query = query.lte(name, _encode(value["$lte"]))
            continue
        query = query.eq(name, _encode(value))
    return query
