# CmtisEdu Analytics

Аналитическая система для образовательной платформы [cmtisedu.kz](https://cmtisedu.kz) (АО «Центр медицинских технологий и информационных систем» УДП РК).
Читает данные из Moodle, считает метрики, генерирует автономный HTML-дашборд и раздаёт его через Flask.


---

## Содержание

1. [Структура проекта](#структура-проекта)
2. [Быстрый старт](#быстрый-старт)
3. [Конфигурация](#конфигурация)
4. [ETL: загрузка данных](#etl-загрузка-данных)
5. [Аналитика и метрики](#аналитика-и-метрики)
6. [Дашборд](#дашборд)
7. [Flask веб-приложение](#flask-веб-приложение)
8. [Деплой на сервер](#деплой-на-сервер)
9. [Переключение на MariaDB](#переключение-на-mariadb)
10. [Мониторинг и диагностика](#мониторинг-и-диагностика)
11. [Архитектурные решения и нюансы](#архитектурные-решения-и-нюансы)

---

## Структура проекта

```
cmtis_analytics/
├── config.py                       # Центральная конфигурация: схемы 28 таблиц, бизнес-пороги
├── run.py                          # Точка входа: ETL → Analytics → Dashboard
├── requirements.txt
│
├── etl/
│   ├── extract.py                  # CSVExtractor + MariaDBExtractor (read-only, инкремент)
│   ├── transform.py                # Строит 12 dim/fact таблиц из 28 сырых
│   ├── load.py                     # Сохраняет в SQLite warehouse + индексы
│   ├── pipeline.py                 # Оркестратор ETL
│   └── watermarks.py               # Метки инкрементальной загрузки
│
├── analytics/
│   ├── core_metrics.py             # KPI, воронка, активность, сертификация
│   ├── course_analytics.py         # Метрики курсов + health score (на основе сертификатов)
│   ├── cohort_analytics.py         # Когортный анализ, retention matrix
│   ├── advanced_analytics.py       # CTT-сложность вопросов, engagement, at-risk
│   ├── assessment_analytics.py     # Тесты, оценки, длительность
│   └── report.py                   # Агрегатор → report.json
│
├── dashboard/
│   ├── builder.py                  # Генератор HTML из report.json
│   └── index.html                  # Готовый дашборд (создаётся при запуске)
│
├── webapp/
│   ├── app.py                      # Flask: /, /health, /status, /api/report
│   ├── cmtis-analytics.service     # systemd unit
│   └── cmtis-analytics.env.example # Шаблон переменных окружения
│
└── data/                           # Создаётся при запуске
    ├── warehouse.db                # SQLite хранилище
    └── report.json                 # Агрегированный отчёт
```

---

## Быстрый старт

```bash
# 1. Установить зависимости
pip install -r requirements.txt

# 2. В config.py убедиться:
#    SOURCE_MODE = "csv"
#    CSV_DIR = "/путь/к/папке/с/txt-файлами"

# 3. Полный пайплайн
python run.py

# 4. Открыть результат
open dashboard/index.html
# или запустить веб-сервер:
python -m webapp.app   # → http://localhost:8000
```

### Частичный запуск

```bash
python run.py --skip-etl        # Пересчитать аналитику без перезагрузки данных
python run.py --skip-dashboard  # ETL + аналитика без генерации HTML
python -m etl.pipeline          # Только ETL
python -m etl.pipeline --full   # ETL с полным сбросом watermarks (MariaDB)
```

---

## Конфигурация

Весь конфиг — `config.py`.

### Источник данных

```python
SOURCE_MODE = "csv"        # "csv" или "mariadb"
CSV_DIR = "/opt/cmtis_analytics/data/csv_export"
```

### MariaDB через переменные окружения

```bash
export CMTIS_DB_HOST=db.cmtisedu.kz
export CMTIS_DB_PORT=3306
export CMTIS_DB_USER=analytics_ro
export CMTIS_DB_PASSWORD=ваш_пароль
export CMTIS_DB_NAME=moodle
```

Или через файл `/etc/cmtis-analytics.env` (шаблон в `webapp/cmtis-analytics.env.example`).

### Исключение админов и тест-аккаунтов

Активность сотрудников CmtisEdu, тестировавших платформу, искажает статистику. Их ID жёстко прописаны в `config.py`:

```python
EXCLUDED_USER_IDS = [
    2,     # admin (системный)
    227,   # Assyl Faizullin
    229,   # Тестовый Участник
    355,   # Assyl Test
    359,   # Askarr Abubakirovvvvv
    377,   # Proverka 102
]
```

Исключение работает на двух уровнях:
1. В `dim_users` им проставляется `is_active = 0` — фильтр `WHERE is_active=1` автоматически их пропускает
2. В прямых SQL-запросах к `fact_logs` используется `WHERE user_id NOT IN (2,227,229,355,359,377)`

Чтобы добавить нового админа — просто допиши его ID в массив. После следующего ETL он исчезнет из всех отчётов.

### Бизнес-пороги

```python
AT_RISK_THRESHOLDS = {
    "critical_days": 30,   # не заходил > 30 дней → критический риск
    "warning_days": 14,    # 14–30 дней → предупреждение
}

GRADE_THRESHOLDS = {
    "excellent": 85, "good": 70, "satisfactory": 50, "fail": 0,
}
```

### Схемы 28 таблиц Moodle

В `config.py` прописаны схемы всех таблиц (`TABLE_SCHEMAS`). Каждая содержит:
- `columns` — все колонки в порядке как идут в CSV/БД
- `keep` — нужные для аналитики
- `numeric` — приводятся к числовому типу

Если схема Moodle поменяется (обновление версии) — править здесь.

---

## ETL: загрузка данных

### CSV

- Файлы `mdl_*.txt` из папки `CSV_DIR`
- `csv.reader` с `escapechar='\\'` — **не** `pandas.read_csv`
- Причина: Moodle экспортирует HTML-поля с переносами строк внутри, pandas их ломает
- При каждом запуске `warehouse.db` пересоздаётся с нуля

### MariaDB

- Подключение через `pymysql` (`pip install pymysql`)
- При каждой сессии: `SET SESSION TRANSACTION READ ONLY`
- Таймауты: connect=10с, read=300с, write=10с

#### Инкрементальная загрузка

10 больших таблиц-фактов грузятся инкрементально через `etl_watermarks`:

| Таблица | Watermark-колонка |
|---|---|
| `mdl_logstore_standard_log` | `timecreated` |
| `mdl_course_modules_completion` | `timemodified` |
| `mdl_grade_grades` | `timemodified` |
| `mdl_quiz_attempts` | `timemodified` |
| `mdl_quiz_grades` | `timemodified` |
| `mdl_question_attempt_steps` | `timecreated` |
| `mdl_lesson_grades` | `completed` |
| `mdl_lesson_timer` | `lessontime` |
| `mdl_assign_submission` | `timemodified` |
| `mdl_assign_grades` | `timemodified` |

Логика: `SELECT ... WHERE timecreated > <last_watermark>`. Маленькие таблицы (`mdl_user`, `mdl_course`, `mdl_customcert`, `mdl_user_info_data`) читаются целиком.

#### Батчинг

Большие таблицы (> 100 000 строк) читаются чанками по 50 000 через **keyset pagination**:

```sql
WHERE id > <last_seen_id> ORDER BY id ASC LIMIT 50000
```

O(1) на чанк, нет дубликатов при параллельных вставках.

### Что строит TRANSFORM

12 чистых таблиц из 28 сырых:

**Dimensions:**
- `dim_users` — пользователи + поле `organization` из custom field
- `dim_courses` — курсы с категориями, флаг `is_system`
- `dim_modules` — типы модулей Moodle

**Facts:**
- `fact_enrolments` — записи на курсы
- `fact_completions` — завершения модулей (`is_completed`, `is_passed`, `is_failed`)
- `fact_grades` — оценки с нормализацией: `grade_percent = finalgrade / grademax * 100`
- `fact_quiz_attempts` — попытки тестов с длительностью
- `fact_question_attempts` — ответы на вопросы (только финальные состояния)
- `fact_logs` — события из логов
- `fact_lesson_grades` / `fact_lesson_timer` — оценки и время прохождения уроков
- **`fact_certificates`** — выданные сертификаты (плагин customcert)

---

## Аналитика и метрики

### Главная страница

**Hero-карточки** — 4 главные метрики крупно:
- **Активных пользователей** — `users_with_activity` + DAU за 30 дней + % вовлечённости
- **Активных курсов** — `total_courses` + общее число записей + сколько курсов с сертификатами
- **Получили сертификат** — уникальные пользователи с хотя бы одним сертификатом + прирост за 7 дней
- **Сертификатов выдано** — общее число выдач (одна выдача = один сертификат) + прирост за 7 дней

**Вторичные метрики (kpi-grid):**
- DAU за 7 дней / DAU за 30 дней (от последнего события в логах)
- Средняя оценка + доля сдачи
- Всего событий, попыток тестов, ср. длительность
- Завершено модулей

**Главные блоки:**
- **Динамика DAU за 90 дней** (`dau_90d`) — линейный график активности по дням за последние 90 дней относительно `MAX(event_at)`. Tooltip содержит полную дату.
- **Коэффициент эффективности всех курсов** (`overall_effectiveness`) — gauge-индикатор 0–100 с разложением на компоненты: активность (макс 30), сертификация (макс 40), успеваемость (макс 30). Категория: высокая (≥70), средняя (40–70), низкая (<40).
- **Воронка вовлечения** (7 этапов) — каждый этап с тремя метриками: «Шаг» (конверсия с предыдущего), «От топа» (от вершины), «Потери» (сколько ушло на этом шаге).
- **Интерактивный фильтр сертификатов** — см. отдельный раздел ниже.
- Топ-5 курсов по числу сертификатов
- Топ-5 организаций по числу пользователей
- Активность по месяцам (формат `MM/YY` — года не наезжают друг на друга)

### Интерактивный фильтр сертификатов

Блок `Динамика выдачи сертификатов · интерактивный фильтр` — для админа/методиста.

Управление:
- **Период** — два инпута даты (от/до) + быстрые пресеты «7д», «30д», «90д», «Весь период». Значения дат ограничены реальным диапазоном (`min_date`–`max_date` из `fact_certificates.issued_at`).
- **Курсы** — multi-select с поиском по названию. Чекбокс «Все курсы» массово включает/выключает. Рядом с каждым курсом — общее число его сертификатов.
- **Минимум сертификатов на курс** — порог, чтобы скрыть курсы с малым числом выдач в выбранный период.

Что показывается после применения:
- 4 агрегата: сертификатов выдано, уникальных пользователей, активных курсов (которые попали в фильтр), дней с активностью.
- График динамики по дням (зелёная линия, заполненная пустыми днями).
- Таблица «По курсам · топ N» с сертификатами / уникальными пользователями / днями активности.

Все вычисления — на стороне браузера (агрегация по `filter.issues`), запросы к серверу не делаются. Это позволяет отзывчиво менять параметры без перезагрузки.

### Корректность данных при переходе через год

Чтобы при многолетней работе платформы данные не накладывались:
- В `fact_logs` группировка по `substr(event_at, 1, 7)` даёт `YYYY-MM` — год сохраняется.
- В когортах `dt.to_period("M")` → строка вида `2025-07`, `2026-07` — это разные когорты.
- В weekly_retention неделя номеруется как `year * 100 + week`, что исключает наложение недель.
- На дашборде месяцы рендерятся как `MM/YY` (`07/25` ≠ `07/26`), даты — как `YYYY-MM-DD` или `MM-DD` с полной датой в tooltip.
- ETL в CSV-режиме каждый запуск **полностью пересоздаёт** warehouse (`if_exists="replace"`) — старые данные не накапливаются.
- Деактивированные/удалённые/тестовые аккаунты помечаются `is_active=0` ещё в `dim_users` и автоматически исключаются из всех аналитик и из воронки/KPI.

### Воронка

7 шагов с тремя видами конверсии:

| Этап | Формула |
|---|---|
| 1. Зарегистрированы | `COUNT(*) WHERE is_active=1` в dim_users |
| 2. Записались на курс | `COUNT(DISTINCT user_id)` в fact_enrolments |
| 3. Были активны | `COUNT(DISTINCT user_id)` в fact_logs |
| 4. Начали тесты | `COUNT(DISTINCT user_id)` в fact_quiz_attempts |
| 5. Завершили модули | `COUNT(DISTINCT user_id) WHERE is_completed=1` |
| 6. Сдали с оценкой ≥60% | `COUNT(DISTINCT user_id) WHERE grade_percent >= 60` |
| 7. Получили сертификат | `COUNT(DISTINCT user_id)` в fact_certificates |

Для каждого шага считаются:
- `conversion_step` — % перешедших с предыдущего шага
- `conversion_total` — % от вершины (всего зарегистрированных)
- `drop_off` — абсолютное число потерянных пользователей

### Активность

- По месяцам: события и уникальные пользователи
- По дням: DAU
- По дням недели и часам суток
- Тепловая карта 7×24 (день недели × час)

### Курсы

| Колонка | Что считается |
|---|---|
| **Записано** | `COUNT(DISTINCT user_id)` в `fact_enrolments` |
| **Активных** | `COUNT(DISTINCT user_id)` в `fact_logs` для курса |
| **События** | `COUNT(*)` событий в логах для курса |
| **Сертификаты** | `COUNT(DISTINCT user_id)` в `fact_certificates` + % от записанных |
| **Ср. оценка** | `AVG(grade_percent)` |
| **Доля сдачи** | % студентов с `grade_percent ≥ 70` |
| **Здоровье** | Композит 0–100 (см. ниже) |

**Health Score курса:**
```
health = (active_users / students) * 30          # активность (макс 30)
       + min(certification_rate, 100) * 0.4       # сертификация (макс 40)
       + pass_rate * 0.3                          # успеваемость (макс 30)
```

Здоровье основано на проценте сертификации (а не на проценте завершённых модулей), потому что **сертификат — это конечная цель платформы**.

- **> 70** — курс живой и успешный
- **40–70** — есть проблемы
- **< 40** — курс мёртвый или очень новый

### Сертификаты — как они работают

В Moodle используется плагин **customcert** (Custom Certificate). Он:

1. Привязан к курсу через `mdl_customcert.course = course_id`
2. Выдаёт сертификат пользователю когда тот выполняет условие, заданное в настройках (обычно — успешная сдача обязательного теста с проходным баллом)
3. Каждая выдача фиксируется в `mdl_customcert_issues` с timestamp

Метрика "получил сертификат" = есть хотя бы одна запись в `mdl_customcert_issues` для пары (user, course). Это объективный факт от Moodle, а не наш расчёт.

### Вовлечённость (Engagement Score)

Перцентильный рейтинг 0–100:

```
score = percentile_rank(events)        * 0.20
      + percentile_rank(active_days)   * 0.25
      + percentile_rank(completions)   * 0.20
      + avg_grade                      * 0.25   ← прямое значение 0-100, не ранг
      + percentile_rank(quizzes_done)  * 0.10
```

`percentile_rank` — позиция студента среди всех (топ 85% = лучше 85% коллег), не абсолютный балл.

| Колонка таблицы | Что это |
|---|---|
| Студент | `full_name` |
| Организация | Из custom field "org" Moodle, "—" если не заполнено или "Физ. лицо" |
| События | Всего действий в логах |
| Акт. дней | Уникальные календарные дни с активностью |
| Завершено | `SUM(is_completed)` модулей |
| Тестов | `SUM(is_finished)` пройденных до конца тестов |
| Ср. оценка | `AVG(grade_percent)` |
| Индекс | Engagement score 0–100 |

Классы:  высокая (≥70),  средняя (40–70),  низкая (20–40),  пассивная (<20).

### Риск отсева

Точкой отсчёта берётся `MAX(event_at)` из логов (последнее известное событие в данных), не текущая дата — корректно работает и в CSV-режиме.

| Статус | Условие |
|---|---|
| `active` | Последний вход ≤ 14 дней назад |
| `inactive_14d` | Не заходил 14–30 дней |
| `inactive_30d` | Не заходил > 30 дней |
| `never_active` | Записан, но ноль событий в логах |

В таблице — колонки: Студент, **Организация**, Email, Курсов, Статус, Дней без активности, Последний заход.

### Когорты

**Матрица удержания:**
- Когорта = месяц первой активности пользователя (`MIN(event_at)`)
- M0 = месяц прихода (всегда 100%)
- M1, M2... = % когорты, активных через N месяцев
- Значение = `active_in_month / cohort_size * 100`

Как читать:
- M0→M1 резко упало (100%→15%) → проблема с онбордингом
- Строки держатся выше 30–40% на M2-M3 → здоровая когорта
- Последние строки неполные → когорта молодая, это нормально

**Недельный retention** — % вернувшихся через 0, 1, 2... 12 недель.

### Сложность вопросов (CTT)

| Метрика | Формула |
|---|---|
| Индекс сложности | `AVG(fraction) * 100` — средняя доля правильности |
| % правильных | `SUM(is_correct) / COUNT(*) * 100` |
| % неправильных | `SUM(is_wrong) / COUNT(*) * 100` |
| % сдавшихся | `SUM(is_gaveup) / COUNT(*) * 100` |

`fraction` из `mdl_question_attempt_steps` учитывает partial credit. Вопросы с < 5 попытками исключаются.

Классификация:  <30% (очень сложный),  30–50%,  50–75%, 75–90%,  ≥90% (тривиальный).

---

## Дашборд

`dashboard/index.html` — **standalone HTML-файл** без CDN.

- Графики на чистом Canvas API (нет jQuery, Chart.js)
- Открывается в любом браузере без интернета
- Весь `report.json` вшивается в HTML как `const D = {...}` при генерации:
  ```python
  html.replace("__DATA_JSON__", data_json)
  ```
- **Не редактировать `index.html` вручную** — перезаписывается каждый запуск. Правки вносить в `dashboard/builder.py`.

### 9 разделов дашборда

1. **Главная** — hero-карточки (active users / active courses / users with cert / certificates issued, всё с +7д) + DAU за 90 дней + коэффициент эффективности (gauge) + воронка с 3 видами конверсии + интерактивный фильтр сертификатов + топ курсов и организаций + активность по месяцам
2. **Воронка** — детальная воронка с конверсией каждого шага
3. **Активность** — DAU, дни недели, часы, тепловая карта
4. **Курсы** — полная таблица с сертификатами и health score
5. **Тесты** — статистика попыток, распределение оценок и длительности
6. **Сложность вопросов** — CTT-анализ
7. **Когорты** — retention matrix (с полным форматом `YYYY-MM`) + недельный retention
8. **Вовлечённость** — таблица с организациями, индекс engagement
9. **Риск отсева** — at-risk студенты с организациями

---

## Flask веб-приложение

### Запуск

```bash
# Dev
python -m webapp.app                                  # → http://localhost:8000

# Production
gunicorn --workers 2 --bind 0.0.0.0:8000 webapp.app:app
```

### Endpoints

| URL | Метод | Что делает | Коды |
|---|---|---|---|
| `/` | GET | HTML-дашборд (`dashboard/index.html`) | 200 / 503 |
| `/health` | GET | Health check для мониторинга | 200 / 503 если данные старше 36ч |
| `/status` | GET | JSON: время ETL, watermarks | 200 |
| `/api/report` | GET | Сырой report.json для интеграций | 200 / 503 |

**Пример `/health`:**
```json
{
  "status": "ok",
  "checks": {
    "dashboard_exists": true,
    "warehouse_exists": true,
    "report_exists": true,
    "data_fresh": true,
    "data_age_hours": 5.2
  },
  "timestamp": "2026-04-29T03:00:00"
}
```

**Авторизации нет** — данные считаются не конфиденциальными. Если нужно — настроить Basic Auth или IP whitelist в Nginx.

---

## Деплой на сервер

### Требования

- Ubuntu 20.04+ / Debian 11+
- Python 3.8+
- Nginx + Certbot
- В MariaDB-режиме: `pip install pymysql`

### Установка

```bash
# 1. Создать пользователя и скопировать проект
sudo mkdir -p /opt/cmtis_analytics
sudo cp -r . /opt/cmtis_analytics/
sudo useradd --system --home /opt/cmtis_analytics analytics
sudo chown -R analytics:analytics /opt/cmtis_analytics
pip install -r /opt/cmtis_analytics/requirements.txt --break-system-packages

# 2. Секреты
sudo cp /opt/cmtis_analytics/webapp/cmtis-analytics.env.example /etc/cmtis-analytics.env
sudo chown root:root /etc/cmtis-analytics.env
sudo chmod 600 /etc/cmtis-analytics.env
sudo nano /etc/cmtis-analytics.env

# 3. Логи
sudo mkdir -p /var/log/cmtis-analytics
sudo chown analytics:analytics /var/log/cmtis-analytics

# 4. Systemd
sudo cp /opt/cmtis_analytics/webapp/cmtis-analytics.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now cmtis-analytics

# 5. Cron — ночной ETL
sudo crontab -u analytics -e
# Добавить:
0 3 * * * cd /opt/cmtis_analytics && /usr/bin/python3 run.py >> /var/log/cmtis-analytics/etl.log 2>&1

# 6. Первый запуск
sudo -u analytics python3 /opt/cmtis_analytics/run.py

# 7. Проверка
curl http://localhost:8000/health
```

### Nginx + HTTPS

```nginx
server {
    listen 443 ssl http2;
    server_name analytics.cmtisedu.kz;

    ssl_certificate     /etc/letsencrypt/live/analytics.cmtisedu.kz/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/analytics.cmtisedu.kz/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name analytics.cmtisedu.kz;
    return 301 https://$host$request_uri;
}
```

```bash
sudo certbot --nginx -d analytics.cmtisedu.kz
```

---

## Переключение на MariaDB

### 1. Read-only пользователь в Moodle БД

```sql
CREATE USER 'analytics_ro'@'%' IDENTIFIED BY 'ваш_пароль';
GRANT SELECT ON moodle.* TO 'analytics_ro'@'%';
FLUSH PRIVILEGES;
```

`GRANT SELECT` — пользователь физически не может изменить данные.

### 2. Переменные окружения

В `/etc/cmtis-analytics.env`:
```bash
CMTIS_DB_HOST=db.cmtisedu.kz
CMTIS_DB_PORT=3306
CMTIS_DB_USER=analytics_ro
CMTIS_DB_PASSWORD=ваш_пароль
CMTIS_DB_NAME=moodle
```

### 3. Одна строка в config.py

```python
SOURCE_MODE = "mariadb"   # было "csv"
```

### 4. Драйвер

```bash
pip install pymysql --break-system-packages
```

### 5. Первый запуск — полная загрузка

```bash
python run.py --full
```

Прочитает всю историю Moodle и создаст watermarks. Несколько минут.

### 6. Дальше — автоматически инкрементальные

```bash
python run.py   # только новые данные
```

---

## Мониторинг и диагностика

### Health check

```bash
curl http://analytics.cmtisedu.kz/health
```

200 если всё хорошо, 503 если нет файлов или данные старше 36 часов. Подключается к Zabbix, Uptime Robot, Prometheus.

### Статус ETL

```bash
curl http://analytics.cmtisedu.kz/status | python3 -m json.tool
```

Время последнего запуска и watermarks по каждой инкрементальной таблице.

### Логи

```bash
tail -f /var/log/cmtis-analytics/etl.log     # ETL (cron)
tail -f /var/log/cmtis-analytics/access.log  # Веб-приложение
tail -f /var/log/cmtis-analytics/error.log
journalctl -u cmtis-analytics -f             # Systemd
```

### Типичные проблемы

| Симптом | Причина | Решение |
|---|---|---|
| `data_age_hours > 36` в `/health` | Cron не отработал | `sudo crontab -u analytics -l`, смотреть `etl.log` |
| 503 на главной | ETL ещё не запускался | `sudo -u analytics python3 /opt/cmtis_analytics/run.py` |
| `Connection refused` (MariaDB) | Неверный хост/порт | Проверить `/etc/cmtis-analytics.env`, firewall |
| `Access denied` (MariaDB) | Неверный пароль или нет GRANT | Проверить пользователя на сервере БД |
| `ModuleNotFoundError: pymysql` | Не установлен драйвер | `pip install pymysql --break-system-packages` |
| Сертификатов 0 в дашборде | CSV не содержит `mdl_customcert*` | Проверить экспорт включает плагин customcert |
| Колонка "Организация" пустая | Поле `org` не заполнено в Moodle | Это нормально, у части пользователей не указано |
| Systemd: `failed` | Ошибка gunicorn | `journalctl -u cmtis-analytics --no-pager -n 50` |

### Полный сброс

```bash
# Удалить warehouse — пересоздастся
sudo -u analytics rm /opt/cmtis_analytics/data/warehouse.db
sudo -u analytics rm /opt/cmtis_analytics/data/report.json
sudo -u analytics python3 /opt/cmtis_analytics/run.py
```

В MariaDB-режиме для сброса watermarks:
```bash
sudo -u analytics python3 -m etl.pipeline --full
```

---

## Архитектурные решения и нюансы

### Почему csv.reader, а не pandas.read_csv

Moodle экспортирует поля типа `description`, `questiontext` с HTML внутри. HTML может содержать переносы строк `\n` которые буквальные, не экранированные. `pandas.read_csv` интерпретирует их как новую строку и ломает парсинг. `csv.reader` с `escapechar='\\'` справляется корректно.

### Почему SQLite, а не PostgreSQL

Аналитика раз в сутки, данных ~1.5 млн строк. SQLite справляется за секунды, не требует отдельного сервиса, файл копируется для отладки. При > 10 млн строк или нескольких параллельных процессах — переходить на PostgreSQL.

### Почему standalone HTML без CDN

Дашборд должен работать во внутренней сети без интернета. Все графики на Canvas без внешних библиотек — файл открывается офлайн в любом браузере.

### Почему index.html генерируется, а не шаблонизируется

Всё проще: `report.json` целиком вшивается как `const D = {...}`. Исключает API-запрос при открытии и делает файл автономным. Минус — при каждом запуске ETL файл перезаписывается. **Не редактировать `index.html` вручную** — правки вносить в `builder.py`.

### Почему данные раз в сутки

Аналитика образовательной платформы не требует реального времени. Ночной cron в 3:00 — вне пиковой нагрузки Moodle. Кнопки ручного обновления нет намеренно: исключает race condition между двумя одновременными запусками ETL.

### Сертификаты — почему customcert, а не grade_pass

Можно было считать "сертификат получен" как "финальная оценка курса ≥ проходной". Но это неточно: пороги разные у разных курсов, бывают ручные правки оценок, есть курсы без явного gradepass. **`mdl_customcert_issues` — это объективный факт выдачи**, который ведёт сама Moodle. Если плагин выдал сертификат — значит студент прошёл условие. Никаких эвристик.

### Организации — откуда берутся

В Moodle у пользователей есть кастомные поля профиля (`mdl_user_info_field`). У cmtisedu.kz есть поле `shortname='org'` (отображаемое имя "Организация"). Значения хранятся в `mdl_user_info_data`. ETL подмешивает их в `dim_users.organization`.

Возможные значения:
- Реальная организация — "ГЗ 2026г.", "KPI группа", "ДАЗ АП Сервис питание" и т.д. → отображается полностью с tooltip
- "Физ. лицо" — значение по умолчанию для большинства → отображается как "—"
- `NULL` (не заполнено) → отображается как "—"

### Исключение системного курса

В Moodle всегда существует курс с `id=1` (SITE — системный). Исключён через `is_system=1` в `dim_courses` и фильтруется во всех запросах.

### Период данных в дашборде

`Период: 2025-07-17 → 2026-03-13` — это `MIN(event_at)` и `MAX(event_at)` из логов, **не дата запуска ETL**. Левая граница фиксирована датой начала работы платформы, правая сдвигается при появлении новых событий.

### Двухслойное исключение админов

Через `is_active=0` + явные SQL-фильтры. Зачем дубликат?

- `is_active=0` работает в большинстве запросов которые джойнят `dim_users` (engagement, at_risk)
- Но многие SQL запросы идут напрямую к `fact_logs` без джойна (cohorts, daily activity) — там нужен явный `WHERE user_id NOT IN (...)`

Так надёжнее: даже если кто-то добавит новый запрос и забудет про фильтр — пользователь всё равно не появится в результатах джойна с `dim_users`.
