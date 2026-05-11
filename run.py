import sys
import time
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from etl.pipeline import run as run_etl
from analytics.report import AnalyticsReport
from dashboard.builder import generate as build_dashboard
from config import DATA_DIR, OUTPUT_HTML


def main():
    parser = argparse.ArgumentParser(description="CmtisEdu Analytics Pipeline")
    parser.add_argument("--skip-etl", action="store_true", help="Пропустить ETL (использовать существующий warehouse)")
    parser.add_argument("--skip-dashboard", action="store_true", help="Пропустить генерацию HTML")
    args = parser.parse_args()

    t0 = time.time()
    print("║  CMTIS EDU · ANALYTICS PIPELINE                          ║")
    print("║  Full build: ETL → Analytics → Dashboard                 ║")

    if not args.skip_etl:
        print("\n▸ ETL стартует..........................")
        run_etl()

    print("\n▸ Аналитика вычисляется...................")
    report_builder = AnalyticsReport()
    report = report_builder.generate()
    report_path = DATA_DIR / "report.json"
    report_builder.save_json(report, report_path)

    if not args.skip_dashboard:
        print("\n▸ Дашборды клепаются..........................")
        build_dashboard(report_path, OUTPUT_HTML)

    elapsed = time.time() - t0
    print(f"\nPipeline завершён за {elapsed:.1f} сек")
    print(f"   Warehouse:  {DATA_DIR / 'warehouse.db'}")
    print(f"   Report:     {report_path}")
    if not args.skip_dashboard:
        print(f"   Dashboard:  {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
