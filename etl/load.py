"""
ETL — Load
Сохраняет очищенные таблицы в SQLite-хранилище.
SQLite выбран как промежуточное хранилище: быстрые запросы без лишней инфраструктуры.
"""

import sys
import sqlite3
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import WAREHOUSE_DB, DATA_DIR


class Loader:
    """Загрузка в SQLite."""

    def __init__(self, db_path: Path = WAREHOUSE_DB):
        self.db_path = db_path
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def load(self, tables: dict):
        """Пишет каждую DataFrame в одноимённую таблицу. replace mode."""
        print(f"Загрузка в warehouse: {self.db_path}")
        with sqlite3.connect(self.db_path) as conn:
            for name, df in tables.items():
                if df is None:
                    print(f"  - {name}: пусто, пропуск")
                    continue

                df_to_save = df.copy()
                for col in df_to_save.columns:
                    if pd.api.types.is_datetime64_any_dtype(df_to_save[col]):
                        df_to_save[col] = df_to_save[col].dt.strftime("%Y-%m-%d %H:%M:%S")

                if df_to_save.empty:
                    if len(df_to_save.columns) == 0:
                        print(f"  - {name}: нет схемы, пропуск")
                        continue
                    conn.execute(f"DROP TABLE IF EXISTS \"{name}\"")
                    cols_sql = ", ".join(f'"{c}" TEXT' for c in df_to_save.columns)
                    conn.execute(f'CREATE TABLE "{name}" ({cols_sql})')
                    print(f"  ○ {name}: пусто (таблица создана без строк)")
                else:
                    df_to_save.to_sql(name, conn, if_exists="replace", index=False)
                    print(f"  ✓ {name}: {len(df_to_save)} записей")

            self._create_indexes(conn)
            self._record_run(conn)

    def _create_indexes(self, conn):
        """Индексы для быстрых запросов аналитики."""
        indexes = [
            ("idx_logs_user", "fact_logs(user_id)"),
            ("idx_logs_course", "fact_logs(course_id)"),
            ("idx_logs_event", "fact_logs(event_at)"),
            ("idx_enrol_user", "fact_enrolments(user_id)"),
            ("idx_enrol_course", "fact_enrolments(course_id)"),
            ("idx_comp_user", "fact_completions(user_id)"),
            ("idx_comp_course", "fact_completions(course_id)"),
            ("idx_grades_user", "fact_grades(user_id)"),
            ("idx_grades_course", "fact_grades(course_id)"),
            ("idx_qa_user", "fact_quiz_attempts(user_id)"),
            ("idx_qa_quiz", "fact_quiz_attempts(quiz_id)"),
            ("idx_qna_question", "fact_question_attempts(questionid)"),
            ("idx_qna_user", "fact_question_attempts(user_id)"),
            ("idx_cert_user", "fact_certificates(user_id)"),
            ("idx_cert_course", "fact_certificates(course_id)"),
        ]
        for name, spec in indexes:
            try:
                conn.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {spec}")
            except sqlite3.OperationalError:
                pass 

    def _record_run(self, conn):
        """Метка последнего успешного ETL-запуска."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS etl_runs (
                run_at TEXT PRIMARY KEY,
                status TEXT
            )
        """)
        from datetime import datetime
        conn.execute(
            "INSERT OR REPLACE INTO etl_runs (run_at, status) VALUES (?, ?)",
            (datetime.now().isoformat(timespec="seconds"), "success"),
        )

    def query(self, sql: str) -> pd.DataFrame:
        """Произвольный SQL-запрос к хранилищу."""
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql(sql, conn)
