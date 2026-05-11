"""
ETL Pipeline — оркестратор Extract → Transform → Load.

Использование:
    python -m etl.pipeline              # обычный запуск (incremental в MariaDB-режиме)
    python -m etl.pipeline --full       # полная перезагрузка (сброс watermarks)

В CSV-режиме всегда идёт полная загрузка (нет смысла делать инкремент на снапшоте).
"""

import sys
import time
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from etl.extract import get_extractor
from etl.transform import Transformer
from etl.load import Loader
from etl.watermarks import WatermarkStore
from config import TABLE_SCHEMAS, SOURCE_MODE, INCREMENTAL_TABLES, WAREHOUSE_DB


def run(full_reload: bool = False):
    t0 = time.time()
    print("═" * 60)
    print(f"  CmtisEdu ETL Pipeline · источник: {SOURCE_MODE}")
    if full_reload and SOURCE_MODE == "mariadb":
        print("  Режим: ПОЛНАЯ ПЕРЕЗАГРУЗКА (сброс watermarks)")
    elif SOURCE_MODE == "mariadb":
        print("  Режим: ИНКРЕМЕНТАЛЬНАЯ ЗАГРУЗКА")
    print("═" * 60)

    if full_reload and SOURCE_MODE == "mariadb":
        WatermarkStore(WAREHOUSE_DB).reset()
        print("  ✓ Watermarks сброшены")

    print("\n[1/3] EXTRACT")
    incremental = (SOURCE_MODE == "mariadb" and not full_reload)
    extractor = get_extractor(incremental=incremental)

    raw = {}
    for table in TABLE_SCHEMAS.keys():
        try:
            df = extractor.extract(table)
            raw[table] = df
            # Помечаем инкрементальные загрузки в выводе
            tag = ""
            if SOURCE_MODE == "mariadb" and incremental and table in INCREMENTAL_TABLES:
                tag = " [incremental]"
            print(f"  ✓ {table}: {len(df):,} записей{tag}")
        except Exception as e:
            print(f"  ✗ {table}: {e}")
            raw[table] = None

    # Закрываем соединение сразу после EXTRACT чтобы не держать коннект
    extractor.close()

    # ─── TRANSFORM ───
    print("\n[2/3] TRANSFORM")
    transformer = Transformer(raw)
    clean = transformer.transform_all()

    # ─── LOAD ───
    print("\n[3/3] LOAD")
    loader = Loader()
    loader.load(clean)

    elapsed = time.time() - t0
    print(f"\n✅ ETL завершён за {elapsed:.1f} сек\n")
    return clean


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true",
                        help="Полная перезагрузка (сброс watermarks)")
    args = parser.parse_args()
    run(full_reload=args.full)
