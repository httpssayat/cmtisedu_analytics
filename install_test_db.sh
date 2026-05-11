#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
#   УСТАНОВКА ТЕСТОВОЙ БАЗЫ ДАННЫХ MOODLE
# ═══════════════════════════════════════════════════════════════════
#
# Этот скрипт создаёт локальную базу MariaDB с данными из CSV
# и пользователя analytics_ro для подключения системы аналитики.
#
# Использование:
#   sudo bash install_test_db.sh
#
# После установки:
#   1. Запустите: python test_mariadb.py — проверка подключения
#   2. Если всё ОК — переключите SOURCE_MODE на "mariadb" в config.py
#   3. Запустите: python run.py
#
# ═══════════════════════════════════════════════════════════════════

set -e  # остановиться при первой ошибке

# Цвета
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

DB_NAME="moodle"
DB_USER="analytics_ro"
DB_PASS="test_password_123"   # измените на свой при желании
DUMP_FILE="moodle_dump.sql.gz"

echo
echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  УСТАНОВКА ТЕСТОВОЙ БАЗЫ MOODLE${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo

# ─── ПРОВЕРКА: запущено ли с правами root? ─────────────────────────
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}✗ Запустите с sudo:${NC}"
    echo "  sudo bash install_test_db.sh"
    exit 1
fi

# ─── ПРОВЕРКА: дамп лежит рядом? ───────────────────────────────────
if [ ! -f "$DUMP_FILE" ]; then
    echo -e "${RED}✗ Файл $DUMP_FILE не найден${NC}"
    echo "  Положите $DUMP_FILE в ту же папку что и этот скрипт"
    exit 1
fi
echo -e "${GREEN}✓${NC} Найден файл дампа: $(ls -lh $DUMP_FILE | awk '{print $5}')"

# ─── ШАГ 1: Установка MariaDB если её нет ──────────────────────────
echo
echo -e "${BLUE}${BOLD}[1/4] Проверка MariaDB${NC}"

if ! command -v mariadb &> /dev/null && ! command -v mysql &> /dev/null; then
    echo -e "${YELLOW}⚠${NC} MariaDB не установлена — устанавливаем..."
    apt-get update -qq
    DEBIAN_FRONTEND=noninteractive apt-get install -y mariadb-server mariadb-client > /dev/null 2>&1
    echo -e "${GREEN}✓${NC} MariaDB установлена"
else
    echo -e "${GREEN}✓${NC} MariaDB уже установлена"
fi

# Запуск службы
if ! systemctl is-active --quiet mariadb 2>/dev/null && ! systemctl is-active --quiet mysql 2>/dev/null; then
    systemctl start mariadb 2>/dev/null || systemctl start mysql 2>/dev/null || {
        # Если systemd недоступен (например, в Docker), запускаем вручную
        mkdir -p /run/mysqld && chown mysql:mysql /run/mysqld
        nohup su -s /bin/bash mysql -c "mysqld --bind-address=127.0.0.1" > /tmp/mysqld.log 2>&1 &
        sleep 5
    }
fi

# Проверка подключения
if ! mysql -u root -e "SELECT 1" > /dev/null 2>&1; then
    echo -e "${RED}✗ Не удалось подключиться к MariaDB как root${NC}"
    echo "  Попробуйте: sudo mysql -u root"
    exit 1
fi
echo -e "${GREEN}✓${NC} MariaDB запущена и доступна"

# ─── ШАГ 2: Создание базы и пользователя ───────────────────────────
echo
echo -e "${BLUE}${BOLD}[2/4] Создание базы и пользователя${NC}"

mysql -u root <<EOF
DROP DATABASE IF EXISTS $DB_NAME;
CREATE DATABASE $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

DROP USER IF EXISTS '$DB_USER'@'localhost';
DROP USER IF EXISTS '$DB_USER'@'127.0.0.1';

CREATE USER '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS';
CREATE USER '$DB_USER'@'127.0.0.1' IDENTIFIED BY '$DB_PASS';

GRANT SELECT ON $DB_NAME.* TO '$DB_USER'@'localhost';
GRANT SELECT ON $DB_NAME.* TO '$DB_USER'@'127.0.0.1';
FLUSH PRIVILEGES;
EOF

echo -e "${GREEN}✓${NC} База '$DB_NAME' создана"
echo -e "${GREEN}✓${NC} Пользователь '$DB_USER' создан с правами READ-ONLY"

# ─── ШАГ 3: Импорт дампа ───────────────────────────────────────────
echo
echo -e "${BLUE}${BOLD}[3/4] Импорт данных (это может занять 1-2 минуты)${NC}"

START=$(date +%s)
gunzip -c "$DUMP_FILE" | mysql -u root
END=$(date +%s)
DURATION=$((END - START))

echo -e "${GREEN}✓${NC} Импорт завершён за ${DURATION} секунд"

# ─── ШАГ 4: Проверка данных ────────────────────────────────────────
echo
echo -e "${BLUE}${BOLD}[4/4] Проверка загруженных данных${NC}"

mysql -u root -D $DB_NAME -t <<EOF
SELECT 'mdl_user'                      as table_name, COUNT(*) as rows FROM mdl_user
UNION ALL SELECT 'mdl_course',                      COUNT(*) FROM mdl_course
UNION ALL SELECT 'mdl_user_enrolments',             COUNT(*) FROM mdl_user_enrolments
UNION ALL SELECT 'mdl_logstore_standard_log',       COUNT(*) FROM mdl_logstore_standard_log
UNION ALL SELECT 'mdl_customcert_issues',           COUNT(*) FROM mdl_customcert_issues
UNION ALL SELECT 'mdl_grade_grades',                COUNT(*) FROM mdl_grade_grades
UNION ALL SELECT 'mdl_quiz_attempts',               COUNT(*) FROM mdl_quiz_attempts
UNION ALL SELECT 'mdl_course_modules_completion',   COUNT(*) FROM mdl_course_modules_completion;
EOF

echo
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  ✅ УСТАНОВКА ЗАВЕРШЕНА${NC}"
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo
echo -e "${BOLD}Параметры подключения:${NC}"
echo "  CMTIS_DB_HOST=127.0.0.1"
echo "  CMTIS_DB_PORT=3306"
echo "  CMTIS_DB_USER=$DB_USER"
echo "  CMTIS_DB_PASSWORD=$DB_PASS"
echo "  CMTIS_DB_NAME=$DB_NAME"
echo
echo -e "${BOLD}Что делать дальше:${NC}"
echo
echo "  1. Запустите тест подключения:"
echo "     ${BLUE}export CMTIS_DB_HOST=127.0.0.1${NC}"
echo "     ${BLUE}export CMTIS_DB_USER=$DB_USER${NC}"
echo "     ${BLUE}export CMTIS_DB_PASSWORD=$DB_PASS${NC}"
echo "     ${BLUE}export CMTIS_DB_NAME=$DB_NAME${NC}"
echo "     ${BLUE}python test_mariadb.py${NC}"
echo
echo "  2. Если все 5 проверок зелёные — переключите режим в config.py:"
echo "     ${BLUE}SOURCE_MODE = \"mariadb\"${NC}"
echo
echo "  3. Запустите полный пайплайн:"
echo "     ${BLUE}python run.py${NC}"
echo
echo "  4. Откройте dashboard/index.html и сравните цифры с CSV-режимом."
echo
