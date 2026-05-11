"""
ETL — Watermarks
Хранилище меток "до какого момента мы уже загрузили каждую таблицу".
Используется для инкрементальной загрузки.

Таблица в SQLite: etl_watermarks (table_name, watermark_col, last_value, updated_at)
"""

import sqlite3
from pathlib import Path
from datetime import datetime


class WatermarkStore:
    """Управление метками инкрементальной загрузки."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS etl_watermarks (
                    table_name TEXT PRIMARY KEY,
                    watermark_col TEXT NOT NULL,
                    last_value INTEGER NOT NULL,
                    last_rows INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL
                )
            """)

    def get(self, table_name: str) -> int:
        """Возвращает последнее загруженное значение (0 если таблица ещё не грузилась)."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT last_value FROM etl_watermarks WHERE table_name = ?",
                (table_name,),
            )
            row = cur.fetchone()
            return int(row[0]) if row else 0

    def set(self, table_name: str, watermark_col: str, last_value: int, rows_loaded: int = 0):
        """Обновляет watermark после успешной загрузки."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO etl_watermarks (table_name, watermark_col, last_value, last_rows, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(table_name) DO UPDATE SET
                    watermark_col = excluded.watermark_col,
                    last_value = excluded.last_value,
                    last_rows = excluded.last_rows,
                    updated_at = excluded.updated_at
            """, (table_name, watermark_col, int(last_value), int(rows_loaded),
                  datetime.now().isoformat(timespec="seconds")))

    def reset(self, table_name: str = None):
        """Сбрасывает watermark (полезно для форс-перезагрузки).
        Без аргумента — сбрасывает все."""
        with sqlite3.connect(self.db_path) as conn:
            if table_name:
                conn.execute("DELETE FROM etl_watermarks WHERE table_name = ?", (table_name,))
            else:
                conn.execute("DELETE FROM etl_watermarks")

    def list_all(self) -> list:
        """Возвращает все watermarks для отладки/мониторинга."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("""
                SELECT table_name, watermark_col, last_value, last_rows, updated_at
                FROM etl_watermarks
                ORDER BY updated_at DESC
            """)
            return [dict(zip([d[0] for d in cur.description], row)) for row in cur.fetchall()]
