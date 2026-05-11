import os
import csv
import sys
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    TABLE_SCHEMAS, CSV_DIR, SOURCE_MODE, MARIADB_CONFIG,
    INCREMENTAL_TABLES, CHUNK_SIZE, BATCH_THRESHOLD, LARGE_TABLES,
    DB_SECURITY, WAREHOUSE_DB, DATA_DIR,
)
from etl.watermarks import WatermarkStore

csv.field_size_limit(10_000_000)


class Extractor:
    """Базовый интерфейс извлечения."""

    def extract(self, table_name: str) -> pd.DataFrame:
        raise NotImplementedError

    def list_tables(self) -> list:
        raise NotImplementedError

    def close(self):
        pass



# CSV EXTRACTOR

class CSVExtractor(Extractor):
    """
    Извлечение из CSV/TXT-файлов Moodle. Всегда читает весь файл целиком
    (инкрементальность для снапшота не имеет смысла).
    """

    def __init__(self, data_dir: str = CSV_DIR):
        self.data_dir = data_dir

    def extract(self, table_name: str) -> pd.DataFrame:
        schema = TABLE_SCHEMAS.get(table_name)
        if not schema:
            raise ValueError(f"Нет схемы для таблицы {table_name}")

        path = os.path.join(self.data_dir, f"{table_name}.txt")
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            return pd.DataFrame(columns=schema["columns"])

        expected_cols = len(schema["columns"])
        rows = []

        with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
            reader = csv.reader(f, quotechar='"', escapechar='\\')
            for row in reader:
                if len(row) > expected_cols:
                    rows.append(row[:expected_cols])
                elif len(row) < expected_cols:
                    row.extend([None] * (expected_cols - len(row)))
                    rows.append(row)
                else:
                    rows.append(row)

        df = pd.DataFrame(rows, columns=schema["columns"])
        df = df.replace({"\\N": None, "NULL": None, "": None})
        return df

    def list_tables(self) -> list:
        return [
            name for name in TABLE_SCHEMAS.keys()
            if os.path.exists(os.path.join(self.data_dir, f"{name}.txt"))
        ]


# MARIADB EXTRACTOR

class MariaDBExtractor(Extractor):
    """
    Чтение из MariaDB:
      - read-only сессия
      - инкрементальная загрузка с raw-буфером в warehouse
      - батчинг больших таблиц через keyset pagination

    Для инкрементальных таблиц:
      1. Читаем из БД только строки с watermark_col > last_value.
      2. Дописываем в raw-таблицу `raw_<table_name>` в warehouse.
      3. Обновляем watermark.
      4. Возвращаем Transformer'у полное содержимое raw-таблицы.

    Для НЕ инкрементальных таблиц (пользователи, курсы и т.п.):
      Читаем полностью каждый раз — они маленькие и могут меняться
      в существующих строках (UPDATE), а не только добавляться.
    """

    def __init__(self, config: dict = None, incremental: bool = True):
        self.config = config or MARIADB_CONFIG
        self.incremental = incremental
        self._conn = None
        self.watermarks = WatermarkStore(WAREHOUSE_DB)
        DATA_DIR.mkdir(parents=True, exist_ok=True)


    def _connect(self):
        if self._conn is not None:
            return self._conn

        try:
            import pymysql
        except ImportError:
            raise RuntimeError(
                "Для режима mariadb установите драйвер: pip install pymysql"
            )

        self._conn = pymysql.connect(
            host=self.config["host"],
            port=self.config["port"],
            user=self.config["user"],
            password=self.config["password"],
            database=self.config["database"],
            charset=self.config.get("charset", "utf8mb4"),
            connect_timeout=DB_SECURITY.get("connect_timeout", 10),
            read_timeout=DB_SECURITY.get("read_timeout", 300),
            write_timeout=DB_SECURITY.get("write_timeout", 10),
            autocommit=True,
        )

        # Session-level защита от записи
        with self._conn.cursor() as cur:
            for stmt in DB_SECURITY.get("session_sql", []):
                try:
                    cur.execute(stmt)
                except Exception as e:
                    print(f"  ! Не удалось применить '{stmt[:40]}…': {e}")

        self._verify_readonly()
        return self._conn

    def _verify_readonly(self):
        try:
            with self._conn.cursor() as cur:
                cur.execute("SELECT @@SESSION.transaction_read_only")
                row = cur.fetchone()
                if row and int(row[0]) == 1:
                    print("  ✓ Сессия в режиме READ ONLY")
                else:
                    print("  ! Сессия не в READ ONLY — полагаемся на GRANT SELECT пользователя")
        except Exception:
            pass

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    

    def _count_rows(self, table_name: str, where_clause: str = "") -> int:
        conn = self._connect()
        query = f"SELECT COUNT(*) FROM `{table_name}`"
        if where_clause:
            query += f" WHERE {where_clause}"
        with conn.cursor() as cur:
            cur.execute(query)
            return int(cur.fetchone()[0])

    def _raw_table_name(self, table_name: str) -> str:
        """Имя raw-буфера в warehouse."""
        return f"raw_{table_name}"

    def _read_raw_buffer(self, table_name: str) -> pd.DataFrame:
        """Читает полный raw-буфер из warehouse."""
        raw_name = self._raw_table_name(table_name)
        with sqlite3.connect(WAREHOUSE_DB) as conn:
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (raw_name,),
            )
            if not cur.fetchone():
                # Таблицы ещё нет — первый запуск
                schema = TABLE_SCHEMAS[table_name]
                return pd.DataFrame(columns=schema["columns"])
            return pd.read_sql(f"SELECT * FROM `{raw_name}`", conn)

    def _append_to_raw_buffer(self, table_name: str, new_df: pd.DataFrame):
        """Дописывает новые строки в raw-буфер."""
        if new_df.empty:
            return
        raw_name = self._raw_table_name(table_name)
        with sqlite3.connect(WAREHOUSE_DB) as conn:
            new_df.to_sql(raw_name, conn, if_exists="append", index=False)

    def _replace_raw_buffer(self, table_name: str, df: pd.DataFrame):
        """Заменяет raw-буфер целиком (для НЕ инкрементальных таблиц)."""
        raw_name = self._raw_table_name(table_name)
        with sqlite3.connect(WAREHOUSE_DB) as conn:
            df.to_sql(raw_name, conn, if_exists="replace", index=False)


    # Публичный API

    def extract(self, table_name: str) -> pd.DataFrame:
        """
        Возвращает полный набор сырых данных таблицы для Transformer'а.
        Внутри выбирает стратегию:
          - инкремент + буфер в warehouse (для INCREMENTAL_TABLES)
          - полное чтение из БД каждый раз (для остальных)
          - чанки (для LARGE_TABLES и больших объёмов)
        """
        schema = TABLE_SCHEMAS.get(table_name)
        if not schema:
            raise ValueError(f"Нет схемы для таблицы {table_name}")

        is_incremental = (
            self.incremental
            and table_name in INCREMENTAL_TABLES
        )

        if is_incremental:
            return self._extract_incremental(table_name, schema)
        else:
            return self._extract_full_table(table_name, schema)

    def _extract_incremental(self, table_name: str, schema: dict) -> pd.DataFrame:
        """Инкремент: только новые строки из БД + дозапись в raw-буфер."""
        watermark_col = INCREMENTAL_TABLES[table_name]
        last_value = self.watermarks.get(table_name)

        cols_sql = ", ".join(f"`{c}`" for c in schema["columns"])
        where_sql = f"`{watermark_col}` > {int(last_value)}"

        new_count = self._count_rows(table_name, where_sql)

        if new_count == 0:
            # Ничего нового — просто возвращаем содержимое буфера
            return self._read_raw_buffer(table_name)

        # Решаем: читать целиком или чанками
        use_batching = (
            table_name in LARGE_TABLES
            or new_count > BATCH_THRESHOLD
        )

        if use_batching:
            print(f"    ↓ {table_name}: +{new_count:,} строк · chunked (по {CHUNK_SIZE:,})")
            new_df = self._read_chunked(table_name, cols_sql, where_sql, watermark_col)
        else:
            print(f"    ↓ {table_name}: +{new_count:,} новых строк")
            new_df = self._read_full(table_name, cols_sql, where_sql)

        # Дописываем в raw-буфер
        self._append_to_raw_buffer(table_name, new_df)

        # Обновляем watermark
        if not new_df.empty:
            new_max = pd.to_numeric(new_df[watermark_col], errors="coerce").dropna().max()
            if pd.notna(new_max) and int(new_max) > last_value:
                self.watermarks.set(
                    table_name, watermark_col,
                    int(new_max), rows_loaded=len(new_df),
                )

        # Возвращаем Transformer'у полное содержимое буфера
        return self._read_raw_buffer(table_name)

    def _extract_full_table(self, table_name: str, schema: dict) -> pd.DataFrame:
        """Полное чтение: таблица не инкрементальная или форс-режим."""
        cols_sql = ", ".join(f"`{c}`" for c in schema["columns"])
        row_count = self._count_rows(table_name)

        if row_count == 0:
            return pd.DataFrame(columns=schema["columns"])

        use_batching = (
            table_name in LARGE_TABLES
            or row_count > BATCH_THRESHOLD
        )

        if use_batching:
            print(f"    ↓ {table_name}: {row_count:,} строк · chunked (по {CHUNK_SIZE:,})")
            df = self._read_chunked(table_name, cols_sql, "", "id")
        else:
            df = self._read_full(table_name, cols_sql, "")

        # Для НЕ инкрементальных таблиц обновляем raw-буфер целиком
        # (чтобы он всегда был актуальным на случай миграции режима)
        self._replace_raw_buffer(table_name, df)

        return df

    


    # Режимы чтения: полный и чанки

    def _read_full(self, table_name: str, cols_sql: str, where_sql: str) -> pd.DataFrame:
        """SELECT * в один заход."""
        conn = self._connect()
        query = f"SELECT {cols_sql} FROM `{table_name}`"
        if where_sql:
            query += f" WHERE {where_sql}"
        return pd.read_sql(query, conn)

    def _read_chunked(
        self, table_name: str, cols_sql: str, where_sql: str, key_col: str,
    ) -> pd.DataFrame:
        """
        Keyset pagination по key_col.
        Лучше OFFSET — O(1) на чанк и нет проблем с дубликатами при вставках в БД
        между чанками.
        """
        conn = self._connect()
        parts = []
        last_key = None

        while True:
            clauses = []
            if where_sql:
                clauses.append(where_sql)
            if last_key is not None:
                clauses.append(f"`{key_col}` > {int(last_key)}")

            query = f"SELECT {cols_sql} FROM `{table_name}`"
            if clauses:
                query += " WHERE " + " AND ".join(clauses)
            query += f" ORDER BY `{key_col}` ASC LIMIT {CHUNK_SIZE}"

            chunk = pd.read_sql(query, conn)
            if chunk.empty:
                break

            parts.append(chunk)
            try:
                last_key = int(
                    pd.to_numeric(chunk[key_col], errors="coerce").dropna().iloc[-1]
                )
            except (ValueError, KeyError, IndexError):
                break

            if len(chunk) < CHUNK_SIZE:
                break

        if not parts:
            schema = TABLE_SCHEMAS[table_name]
            return pd.DataFrame(columns=schema["columns"])

        return pd.concat(parts, ignore_index=True)

    def list_tables(self) -> list:
        return list(TABLE_SCHEMAS.keys())



def get_extractor(incremental=True):
    from config import SOURCE_MODE
    if SOURCE_MODE == "csv":
        return CSVExtractor()
    return MariaDBExtractor(incremental=incremental)
