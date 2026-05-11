import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

from flask import Flask, Response, jsonify, send_file

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import OUTPUT_HTML, DATA_DIR, WAREHOUSE_DB

app = Flask(__name__)

DASHBOARD_HTML = Path(OUTPUT_HTML)
REPORT_JSON = Path(DATA_DIR) / "report.json"




@app.route("/")
def dashboard():
    """Главная: отдаём сгенерированный HTML-дашборд."""
    if not DASHBOARD_HTML.exists():
        return _render_empty_state(), 503

    # Отключаем кэш браузера, чтобы после ночного ETL
    # пользователи сразу видели свежие данные
    response = send_file(DASHBOARD_HTML, mimetype="text/html")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/health")
def health():
    """Health check для мониторинга (Zabbix, Prometheus, cron-проверки)."""
    checks = {
        "dashboard_exists": DASHBOARD_HTML.exists(),
        "warehouse_exists": Path(WAREHOUSE_DB).exists(),
        "report_exists": REPORT_JSON.exists(),
    }

    # Проверяем, что последний ETL был не слишком давно (>36 часов — проблема)
    if DASHBOARD_HTML.exists():
        age_hours = (datetime.now().timestamp() - DASHBOARD_HTML.stat().st_mtime) / 3600
        checks["data_fresh"] = age_hours < 36
        checks["data_age_hours"] = round(age_hours, 1)

    all_ok = all(v for k, v in checks.items() if isinstance(v, bool))
    return jsonify({
        "status": "ok" if all_ok else "degraded",
        "checks": checks,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }), 200 if all_ok else 503


@app.route("/status")
def status():
    """Статус последнего ETL-запуска и watermarks."""
    info = {}

    if DASHBOARD_HTML.exists():
        mtime = datetime.fromtimestamp(DASHBOARD_HTML.stat().st_mtime)
        info["dashboard_generated_at"] = mtime.isoformat(timespec="seconds")

    if Path(WAREHOUSE_DB).exists():
        try:
            with sqlite3.connect(WAREHOUSE_DB) as conn:
                # Последний успешный ETL-запуск
                cur = conn.execute(
                    "SELECT run_at, status FROM etl_runs "
                    "ORDER BY run_at DESC LIMIT 1"
                )
                row = cur.fetchone()
                if row:
                    info["last_etl_at"] = row[0]
                    info["last_etl_status"] = row[1]

                # Watermarks инкрементальной загрузки
                cur = conn.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name='etl_watermarks'
                """)
                if cur.fetchone():
                    cur = conn.execute("""
                        SELECT table_name, last_value, last_rows, updated_at
                        FROM etl_watermarks ORDER BY updated_at DESC
                    """)
                    info["watermarks"] = [
                        dict(zip(["table", "last_value", "rows", "updated_at"], r))
                        for r in cur.fetchall()
                    ]
                else:
                    info["watermarks"] = []
        except Exception as e:
            info["warehouse_error"] = str(e)

    return jsonify(info)


@app.route("/api/report")
def api_report():
    """Сырой JSON-отчёт для интеграций (BI-системы, экспорт в Excel)."""
    if not REPORT_JSON.exists():
        return jsonify({"error": "Отчёт ещё не сгенерирован"}), 503
    return send_file(REPORT_JSON, mimetype="application/json")



def _render_empty_state() -> str:
    """Страница-заглушка когда дашборд ещё не собран."""
    return """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>CmtisEdu · Инициализация</title>
<style>
  body { font-family: 'IBM Plex Sans', system-ui, sans-serif; background: #0A0A0B;
         color: #E4E4E7; display: flex; align-items: center; justify-content: center;
         min-height: 100vh; margin: 0; text-align: center; padding: 40px; }
  h1 { font-size: 28px; font-weight: 300; letter-spacing: -0.02em; margin-bottom: 8px; }
  p { color: #8A8A92; max-width: 560px; margin: 16px auto; line-height: 1.6; }
  code { background: #1A1A1D; padding: 4px 10px; border: 1px solid #3A3A40;
         font-family: 'IBM Plex Mono', monospace; font-size: 13px; }
  .mark { font-family: 'IBM Plex Mono', monospace; font-size: 10px;
          letter-spacing: 0.15em; color: #5A5A62; text-transform: uppercase; }
</style>
</head>
<body>
<div>
  <div class="mark">CMTIS · АНАЛИТИКА</div>
  <h1>Дашборд готовится</h1>
  <p>Данные ещё не загружены. Запустите ETL на сервере:</p>
  <p><code>python run.py</code></p>
  <p>После этого обновите страницу.</p>
</div>
</body>
</html>"""




# ЗАПУСК DEV-СЕРВЕРА
if __name__ == "__main__":
    port = int(os.getenv("CMTIS_APP_PORT", 8000))
    debug = os.getenv("CMTIS_APP_DEBUG", "false").lower() == "true"

    print(f" CmtisEdu Analytics запускается на порту {port}")
    print(f"   URL: http://localhost:{port}/")
    print()

    app.run(host="0.0.0.0", port=port, debug=debug)
