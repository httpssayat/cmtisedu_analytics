#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════
  ТЕСТ ПОДКЛЮЧЕНИЯ К MARIADB
═══════════════════════════════════════════════════════════════════

Этот скрипт проверяет что система корректно работает с MariaDB.
Запускает 5 проверок по очереди — если все зелёные, всё работает.

Запуск:
    cd /opt/cmtis_analytics
    python test_mariadb.py

Перед запуском убедитесь что:
  1. MariaDB запущен и доступен
  2. Создан пользователь analytics_ro с правами SELECT на базу moodle
  3. Заполнен файл /etc/cmtis-analytics.env (или переменные окружения)
"""

import sys
import os
import time
from pathlib import Path

# ─── Цвета для терминала ──────────────────────────────────────────
class C:
    OK    = '\033[92m'  # зелёный
    FAIL  = '\033[91m'  # красный
    WARN  = '\033[93m'  # жёлтый
    INFO  = '\033[94m'  # синий
    BOLD  = '\033[1m'
    END   = '\033[0m'

def header(text):
    print(f"\n{C.BOLD}{'═' * 65}{C.END}")
    print(f"{C.BOLD}  {text}{C.END}")
    print(f"{C.BOLD}{'═' * 65}{C.END}")

def step(num, text):
    print(f"\n{C.INFO}{C.BOLD}[{num}/5] {text}{C.END}")

def ok(text):
    print(f"  {C.OK}✓{C.END} {text}")

def fail(text):
    print(f"  {C.FAIL}✗{C.END} {text}")

def warn(text):
    print(f"  {C.WARN}⚠{C.END} {text}")

def info(text):
    print(f"    {text}")

# ─── Загружаем .env если есть ─────────────────────────────────────
def load_env_file():
    """Читаем /etc/cmtis-analytics.env если существует."""
    env_paths = [
        Path("/etc/cmtis-analytics.env"),
        Path(__file__).parent / "webapp" / "cmtis-analytics.env",
        Path(__file__).parent / ".env",
    ]
    for p in env_paths:
        if p.exists():
            with open(p) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, val = line.split("=", 1)
                        os.environ.setdefault(key.strip(), val.strip())
            print(f"  Загружен env-файл: {p}")
            return True
    return False

# ═══════════════════════════════════════════════════════════════════
header("ТЕСТ ПОДКЛЮЧЕНИЯ К MARIADB · CmtisEdu Analytics")

load_env_file()

# Принудительно ставим режим mariadb для теста (НЕ меняет config.py)
os.environ["CMTIS_SOURCE_MODE_OVERRIDE"] = "mariadb"

# ─── ПРОВЕРКА 1: pymysql установлен? ─────────────────────────────
step(1, "Проверка драйвера pymysql")
try:
    import pymysql
    ok(f"pymysql установлен (версия {pymysql.__version__})")
except ImportError:
    fail("pymysql НЕ установлен")
    info("Установите: pip install pymysql>=1.1.0 --break-system-packages")
    sys.exit(1)

# ─── ПРОВЕРКА 2: env-переменные заполнены? ───────────────────────
step(2, "Проверка переменных окружения")

required_vars = {
    "CMTIS_DB_HOST":     "хост MariaDB",
    "CMTIS_DB_PORT":     "порт MariaDB",
    "CMTIS_DB_USER":     "имя пользователя",
    "CMTIS_DB_PASSWORD": "пароль",
    "CMTIS_DB_NAME":     "имя базы данных",
}

missing = []
for var, desc in required_vars.items():
    val = os.environ.get(var, "")
    if not val:
        missing.append(var)
        fail(f"{var} ({desc}) — НЕ ЗАПОЛНЕНО")
    else:
        # Маскируем пароль
        display = "***" if "PASSWORD" in var else val
        ok(f"{var} = {display}")

if missing:
    print()
    fail(f"Не заполнены переменные: {', '.join(missing)}")
    info("Заполните /etc/cmtis-analytics.env или экспортируйте их вручную:")
    info("  export CMTIS_DB_HOST=127.0.0.1")
    info("  export CMTIS_DB_USER=analytics_ro")
    info("  export CMTIS_DB_PASSWORD=ваш_пароль")
    info("  export CMTIS_DB_NAME=moodle")
    sys.exit(1)

# ─── ПРОВЕРКА 3: TCP-подключение работает? ───────────────────────
step(3, "Проверка сетевого подключения к MariaDB")

try:
    conn = pymysql.connect(
        host=os.environ["CMTIS_DB_HOST"],
        port=int(os.environ["CMTIS_DB_PORT"]),
        user=os.environ["CMTIS_DB_USER"],
        password=os.environ["CMTIS_DB_PASSWORD"],
        database=os.environ["CMTIS_DB_NAME"],
        charset="utf8mb4",
        connect_timeout=10,
    )
    ok(f"Подключение успешно (host={os.environ['CMTIS_DB_HOST']})")

    with conn.cursor() as cur:
        cur.execute("SELECT VERSION()")
        version = cur.fetchone()[0]
        ok(f"MariaDB version: {version}")

        cur.execute("SELECT DATABASE()")
        db = cur.fetchone()[0]
        ok(f"Активная база: {db}")
except pymysql.err.OperationalError as e:
    fail(f"Не удалось подключиться: {e}")
    info("Возможные причины:")
    info("  • MariaDB не запущен")
    info("  • Неверный хост/порт/пользователь/пароль")
    info("  • Файрвол блокирует соединение")
    info("  • Пользователь analytics_ro не создан или не имеет доступа")
    info("")
    info("Проверьте на сервере MariaDB:")
    info(f"  mysql -u {os.environ['CMTIS_DB_USER']} -p {os.environ['CMTIS_DB_NAME']}")
    sys.exit(1)
except Exception as e:
    fail(f"Ошибка: {e}")
    sys.exit(1)

# ─── ПРОВЕРКА 4: ключевые таблицы существуют и не пустые? ────────
step(4, "Проверка таблиц Moodle в базе данных")

required_tables = [
    ("mdl_user",                       "пользователи Moodle",         True),
    ("mdl_course",                     "курсы",                       True),
    ("mdl_user_enrolments",            "записи на курсы",             True),
    ("mdl_logstore_standard_log",      "журнал событий",              True),
    ("mdl_customcert_issues",          "выданные сертификаты",        False),
    ("mdl_grade_grades",               "оценки",                      False),
    ("mdl_quiz_attempts",              "попытки тестов",              False),
    ("mdl_course_modules_completion",  "завершение модулей",          False),
    ("mdl_role_assignments",           "роли пользователей",          False),
]

all_ok = True
empty_critical = False
with conn.cursor() as cur:
    for table, desc, critical in required_tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM `{table}`")
            n = cur.fetchone()[0]
            if n > 0:
                ok(f"{table:35s} {n:>10,} строк  ({desc})")
            elif critical:
                fail(f"{table:35s} {'пусто':>10}  ({desc}) — КРИТИЧНО")
                empty_critical = True
                all_ok = False
            else:
                warn(f"{table:35s} {'пусто':>10}  ({desc}) — допустимо")
        except pymysql.err.ProgrammingError as e:
            if critical:
                fail(f"{table:35s} НЕ СУЩЕСТВУЕТ — {e.args[1][:50]}")
                all_ok = False
            else:
                warn(f"{table:35s} НЕ СУЩЕСТВУЕТ — допустимо")

if empty_critical:
    print()
    fail("Критические таблицы пустые — пайплайн не сможет работать")
    info("Возможно вы подключились не к той базе. Проверьте CMTIS_DB_NAME.")
    sys.exit(1)

# ─── ПРОВЕРКА 5: пробный extract из MariaDB через MariaDBExtractor ─
step(5, "Тестовый запуск MariaDBExtractor")

# Подмена SOURCE_MODE чтобы не править config.py
sys.path.insert(0, str(Path(__file__).parent))

import config as cfg
original_mode = cfg.SOURCE_MODE
cfg.SOURCE_MODE = "mariadb"

try:
    from etl.extract import MariaDBExtractor

    extractor = MariaDBExtractor()
    test_conn = extractor._connect()
    ok("MariaDBExtractor.connect() — успешно")

    # Пробуем читать одну небольшую таблицу
    with test_conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM mdl_user WHERE deleted = 0 AND suspended = 0")
        active_users = cur.fetchone()[0]
        ok(f"Чтение mdl_user: {active_users} активных пользователей")

    test_conn.close()
    ok("Соединение корректно закрыто")

except Exception as e:
    fail(f"Ошибка extract: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    cfg.SOURCE_MODE = original_mode

conn.close()

# ─── ИТОГ ─────────────────────────────────────────────────────────
print()
header("РЕЗУЛЬТАТ")
print()
if all_ok:
    print(f"  {C.OK}{C.BOLD}✅ ВСЕ 5 ПРОВЕРОК ПРОЙДЕНЫ{C.END}")
    print()
    print(f"  Система готова работать с MariaDB.")
    print()
    print(f"  Следующий шаг — запустить полный пайплайн:")
    print(f"    {C.BOLD}1.{C.END} Откройте config.py")
    print(f"    {C.BOLD}2.{C.END} Замените строку:")
    print(f"         SOURCE_MODE = \"csv\"")
    print(f"       на:")
    print(f"         SOURCE_MODE = \"mariadb\"")
    print(f"    {C.BOLD}3.{C.END} Запустите: python run.py")
    print()
    print(f"  После этого откройте dashboard/index.html и сравните")
    print(f"  цифры с теми, что были в CSV-режиме.")
    print()
    sys.exit(0)
else:
    print(f"  {C.FAIL}{C.BOLD}❌ ЕСТЬ ПРОБЛЕМЫ{C.END}")
    print()
    print(f"  Исправьте ошибки выше и запустите тест снова.")
    print()
    sys.exit(1)
