"""
CmtisEdu Analytics — Configuration
Центральная конфигурация системы.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
#CSV_DIR = "/opt/cmtis_analytics/data/csv_export"
#CSV_DIR = "CSV"
WAREHOUSE_DB = DATA_DIR / "warehouse.db"
DASHBOARD_DIR = BASE_DIR / "dashboard"
OUTPUT_HTML = DASHBOARD_DIR / "index.html"

#SOURCE_MODE = "csv"
#SOURCE_MODE = "mariadb" 

MARIADB_CONFIG = {
    "host": os.getenv("CMTIS_DB_HOST", "localhost"),
    "port": int(os.getenv("CMTIS_DB_PORT", 3306)),
    "user": os.getenv("CMTIS_DB_USER", "analytics"),
    "password": os.getenv("CMTIS_DB_PASSWORD", ""),
    "database": os.getenv("CMTIS_DB_NAME", "moodle"),
    "charset": "utf8mb4",
}




















# cхемы таблиц

TABLE_SCHEMAS = {
    "mdl_user": {
        "columns": [
            "id", "auth", "confirmed", "policyagreed", "deleted", "suspended",
            "mnethostid", "username", "password", "idnumber", "firstname",
            "lastname", "email", "emailstop", "phone1", "phone2", "institution",
            "department", "address", "city", "country", "lang", "calendartype",
            "theme", "timezone", "firstaccess", "lastaccess", "lastlogin",
            "currentlogin", "lastip", "secret", "picture", "description",
            "descriptionformat", "mailformat", "maildigest", "maildisplay",
            "autosubscribe", "trackforums", "timecreated", "timemodified",
            "trustbitmask", "imagealt", "lastnamephonetic", "firstnamephonetic",
            "middlename", "alternatename", "moodlenetprofileid",
        ],
        "keep": ["id", "username", "firstname", "lastname", "email",
                 "deleted", "suspended", "firstaccess", "lastaccess",
                 "lastlogin", "timecreated", "timemodified", "country", "city"],
        "numeric": ["id", "deleted", "suspended", "firstaccess", "lastaccess",
                    "lastlogin", "timecreated", "timemodified"],
    },
    "mdl_course": {
        "columns": [
            "id", "category", "sortorder", "fullname", "shortname", "idnumber",
            "summary", "summaryformat", "format", "showgrades", "newsitems",
            "startdate", "enddate", "relativedatesmode", "marker", "maxbytes",
            "legacyfiles", "showreports", "visible", "visibleold",
            "downloadcontent", "groupmode", "groupmodeforce", "defaultgroupingid",
            "lang", "calendartype", "theme", "timecreated", "timemodified",
            "requested", "enablecompletion", "completionnotify", "cacherev",
            "originalcourseid", "showactivitydates", "showcompletionconditions",
            "pdfexportfont",
        ],
        "keep": ["id", "category", "fullname", "shortname", "visible",
                 "timecreated", "startdate"],
        "numeric": ["id", "category", "visible", "timecreated", "startdate"],
    },
    "mdl_course_categories": {
        "columns": ["id", "name", "idnumber", "description", "descriptionformat",
                    "parent", "sortorder", "coursecount", "visible", "visibleold",
                    "timemodified", "depth", "path", "theme"],
        "keep": ["id", "name", "parent", "coursecount", "visible"],
        "numeric": ["id", "parent", "coursecount", "visible"],
    },
    "mdl_enrol": {
        "columns": [
            "id", "enrol", "status", "courseid", "sortorder", "name",
            "enrolperiod", "enrolstartdate", "enrolenddate", "expirynotify",
            "expirythreshold", "notifyall", "password", "cost", "currency",
            "roleid", "customint1", "customint2", "customint3", "customint4",
            "customint5", "customint6", "customint7", "customint8",
            "customchar1", "customchar2", "customchar3", "customdec1",
            "customdec2", "customtext1", "customtext2", "customtext3",
            "customtext4", "timecreated", "timemodified"
        ],
        "keep": ["id", "enrol", "status", "courseid", "roleid", "timecreated"],
        "numeric": ["id", "status", "courseid", "roleid", "timecreated"],
    },
    "mdl_user_enrolments": {
        "columns": ["id", "status", "enrolid", "userid", "timestart", "timeend",
                    "modifierid", "timecreated", "timemodified"],
        "keep": ["id", "status", "enrolid", "userid", "timestart", "timeend",
                 "timecreated", "timemodified"],
        "numeric": ["id", "status", "enrolid", "userid", "timestart", "timeend",
                    "timecreated", "timemodified"],
    },
    "mdl_role_assignments": {
        "columns": ["id", "roleid", "contextid", "userid", "timemodified",
                    "modifierid", "component", "sortorder", "itemid"],
        "keep": ["id", "roleid", "contextid", "userid", "timemodified"],
        "numeric": ["id", "roleid", "contextid", "userid", "timemodified"],
    },
    "mdl_course_modules": {
        "columns": ["id", "course", "module", "instance", "section", "idnumber",
                    "added", "score", "indent", "visible", "visibleoncoursepage",
                    "visibleold", "groupmode", "groupingid", "completion",
                    "completiongradeitemnumber", "completionview",
                    "completionexpected", "completionpassgrade", "showdescription",
                    "availability", "deletioninprogress", "downloadcontent", "lang"],
        "keep": ["id", "course", "module", "instance", "section", "completion", "added"],
        "numeric": ["id", "course", "module", "instance", "completion", "added"],
    },
    "mdl_modules": {
        "columns": ["id", "name", "cron", "lastcron", "search", "visible"],
        "keep": ["id", "name"],
        "numeric": ["id"],
    },
    "mdl_course_modules_completion": {
        "columns": ["id", "coursemoduleid", "userid", "completionstate",
                    "overrideby", "timemodified"],
        "keep": ["id", "coursemoduleid", "userid", "completionstate", "timemodified"],
        "numeric": ["id", "coursemoduleid", "userid", "completionstate", "timemodified"],
    },
    "mdl_grade_items": {
        "columns": ["id", "courseid", "categoryid", "itemname", "itemtype",
                    "itemmodule", "iteminstance", "itemnumber", "iteminfo",
                    "idnumber", "calculation", "gradetype", "grademax", "grademin",
                    "scaleid", "outcomeid", "gradepass", "multfactor", "plusfactor",
                    "aggregationcoef", "aggregationcoef2", "sortorder", "display",
                    "decimals", "hidden", "locked", "locktime", "needsupdate",
                    "weightoverride", "timecreated", "timemodified"],
        "keep": ["id", "courseid", "itemname", "itemtype", "itemmodule",
                 "iteminstance", "grademax", "grademin", "gradepass"],
        "numeric": ["id", "courseid", "grademax", "grademin", "gradepass"],
    },
    "mdl_grade_grades": {
        "columns": ["id", "itemid", "userid", "rawgrade", "rawgrademax",
                    "rawgrademin", "rawscaleid", "usermodified", "finalgrade",
                    "hidden", "locked", "locktime", "exported", "overridden",
                    "excluded", "feedback", "feedbackformat", "information",
                    "informationformat", "timecreated", "timemodified",
                    "aggregationstatus", "aggregationweight", "aggregationcoef"],
        "keep": ["id", "itemid", "userid", "rawgrade", "rawgrademax",
                 "rawgrademin", "finalgrade", "timecreated", "timemodified"],
        "numeric": ["id", "itemid", "userid", "rawgrade", "rawgrademax",
                    "rawgrademin", "finalgrade", "timecreated", "timemodified"],
    },
    "mdl_quiz": {
        "columns": [
            "id", "course", "name", "intro", "introformat", "timeopen",
            "timeclose", "timelimit", "overduehandling", "graceperiod",
            "preferredbehaviour", "canredoquestions", "attempts",
            "attemptonlast", "grademethod", "decimalpoints",
            "questiondecimalpoints", "reviewattempt", "reviewcorrectness",
            "reviewmarks", "reviewspecificfeedback", "reviewgeneralfeedback",
            "reviewrightanswer", "reviewoverallfeedback", "questionsperpage",
            "navmethod", "shuffleanswers", "sumgrades", "grade",
            "timecreated", "timemodified", "password", "subnet",
            "browsersecurity", "delay1", "delay2", "showuserpicture",
            "showblocks", "completionattemptsexhausted", "completionminattempts",
            "allowofflineattempts", "completionpass", "timelimiten",
        ],
        "keep": ["id", "course", "name", "timeopen", "timeclose", "timelimit",
                 "attempts", "sumgrades", "grade", "timecreated"],
        "numeric": ["id", "course", "timeopen", "timeclose", "timelimit",
                    "attempts", "sumgrades", "grade", "timecreated"],
    },
    "mdl_quiz_attempts": {
        "columns": ["id", "quiz", "userid", "attempt", "uniqueid", "layout",
                    "currentpage", "preview", "state", "timestart", "timefinish",
                    "timemodified", "timecheckstate", "sumgrades",
                    "gradednotificationsenttime", "extra"],
        "keep": ["id", "quiz", "userid", "attempt", "state", "timestart",
                 "timefinish", "timemodified", "sumgrades"],
        "numeric": ["id", "quiz", "userid", "attempt", "timestart",
                    "timefinish", "timemodified", "sumgrades"],
    },
    "mdl_quiz_grades": {
        "columns": ["id", "quiz", "userid", "grade", "timemodified"],
        "keep": ["id", "quiz", "userid", "grade", "timemodified"],
        "numeric": ["id", "quiz", "userid", "grade", "timemodified"],
    },
    "mdl_question": {
        "columns": ["id", "category", "parent", "name", "questiontext",
                    "questiontextformat", "generalfeedback", "generalfeedbackformat",
                    "defaultmark", "penalty", "qtype", "length", "stamp",
                    "version", "hidden", "timecreated"],
        "keep": ["id", "name", "qtype", "defaultmark", "timecreated"],
        "numeric": ["id", "defaultmark", "timecreated"],
    },
    "mdl_question_attempts": {
        "columns": ["id", "questionusageid", "slot", "behaviour", "questionid",
                    "variant", "maxmark", "minfraction", "maxfraction", "flagged",
                    "questionsummary", "rightanswer", "responsesummary",
                    "timemodified"],
        "keep": ["id", "questionusageid", "questionid", "maxmark",
                 "minfraction", "maxfraction", "timemodified"],
        "numeric": ["id", "questionusageid", "questionid", "maxmark",
                    "minfraction", "maxfraction", "timemodified"],
    },
    "mdl_question_attempt_steps": {
        "columns": ["id", "questionattemptid", "sequencenumber", "state",
                    "fraction", "timecreated", "userid"],
        "keep": ["id", "questionattemptid", "sequencenumber", "state",
                 "fraction", "timecreated", "userid"],
        "numeric": ["id", "questionattemptid", "sequencenumber", "fraction",
                    "timecreated", "userid"],
    },
    "mdl_lesson": {
        # 42 колонки — нам интересны только первые 4
        "columns": [
            "id", "course", "name", "intro"
        ] + [f"_extra_{i}" for i in range(42 - 4)],
        "keep": ["id", "course", "name"],
        "numeric": ["id", "course"],
    },
    "mdl_lesson_grades": {
        "columns": ["id", "lesson", "userid", "grade", "late", "completed"],
        "keep": ["id", "lesson", "userid", "grade", "completed"],
        "numeric": ["id", "lesson", "userid", "grade", "completed"],
    },
    "mdl_lesson_timer": {
        "columns": ["id", "lessonid", "userid", "starttime", "lessontime",
                    "completed", "timemodifiedoffline"],
        "keep": ["id", "lessonid", "userid", "starttime", "lessontime", "completed"],
        "numeric": ["id", "lessonid", "userid", "starttime", "lessontime", "completed"],
    },
    "mdl_logstore_standard_log": {
        "columns": ["id", "eventname", "component", "action", "target",
                    "objecttable", "objectid", "crud", "edulevel", "contextid",
                    "contextlevel", "contextinstanceid", "userid", "courseid",
                    "relateduserid", "anonymous", "other", "timecreated",
                    "origin", "ip", "realuserid"],
        "keep": ["id", "eventname", "component", "action", "target",
                 "crud", "contextinstanceid", "userid", "courseid",
                 "timecreated", "origin"],
        "numeric": ["id", "contextinstanceid", "userid", "courseid", "timecreated"],
    },
    "mdl_assign": {
        # 36 колонок — берём первые 4
        "columns": [
            "id", "course", "name", "intro"
        ] + [f"_extra_{i}" for i in range(36 - 4)],
        "keep": ["id", "course", "name"],
        "numeric": ["id", "course"],
    },
    "mdl_assign_submission": {
        "columns": ["id", "assignment", "userid", "timecreated", "timemodified",
                    "timestarted", "status", "groupid", "attemptnumber", "latest"],
        "keep": ["id", "assignment", "userid", "timecreated", "timemodified",
                 "status", "attemptnumber"],
        "numeric": ["id", "assignment", "userid", "timecreated", "timemodified"],
    },
    "mdl_assign_grades": {
        "columns": ["id", "assignment", "userid", "timecreated", "timemodified",
                    "grader", "grade", "attemptnumber", "extra"],
        "keep": ["id", "assignment", "userid", "grade", "timecreated", "timemodified"],
        "numeric": ["id", "assignment", "userid", "grade", "timecreated", "timemodified"],
    },
    # Custom Certificate plugin - факт выдачи сертификата
    "mdl_customcert": {
        "columns": ["id", "course", "templateid", "name", "intro", "introformat",
                    "requiredtime", "verifyany", "deliveryoption", "protection",
                    "emailstudents", "emailteachers", "emailothers", "language",
                    "fonttype", "fontsize", "timecreated", "timemodified"],
        "keep": ["id", "course", "name"],
        "numeric": ["id", "course"],
    },
    "mdl_customcert_issues": {
        "columns": ["id", "userid", "customcertid", "code", "emailed", "timecreated"],
        "keep": ["id", "userid", "customcertid", "timecreated"],
        "numeric": ["id", "userid", "customcertid", "timecreated"],
    },
    # Профильные поля пользователя (для организации)
    "mdl_user_info_field": {
        "columns": ["id", "shortname", "name", "datatype", "description",
                    "descriptionformat", "categoryid", "sortorder", "required",
                    "locked", "visible", "forceunique", "signup", "defaultdata",
                    "defaultdataformat", "param1", "param2", "param3", "param4", "param5"],
        "keep": ["id", "shortname", "name"],
        "numeric": ["id"],
    },
    "mdl_user_info_data": {
        "columns": ["id", "userid", "fieldid", "data", "dataformat"],
        "keep": ["id", "userid", "fieldid", "data"],
        "numeric": ["id", "userid", "fieldid"],
    },
}



AT_RISK_THRESHOLDS = {
    "critical_days": 30,
    "warning_days": 14,
}

GRADE_THRESHOLDS = {
    "excellent": 85,
    "good": 70,
    "satisfactory": 50,
    "fail": 0,
}

ROLES = {
    1: "manager", 2: "coursecreator", 3: "editingteacher",
    4: "teacher", 5: "student", 11: "enrolled_student",
}


ADMIN_USER_ID = 2

# Дополнительные админ/тестовые аккаунты для исключения
# Их активность искажает статистику (сотрудники CmtisEdu тестируют платформу)
EXCLUDED_USER_IDS = [
    2,     # admin (системный)
    227,   # Assyl Faizullin
    229,   # Тестовый Участник
    355,   # Assyl Test
    359,   # Askarr Abubakirovvvvv
    377,   # Proverka 102
]

# Готовый SQL-фрагмент для использования в WHERE-условиях.
# Использовать как: "WHERE user_id IS NOT NULL " + EXCLUDE_USERS_SQL
EXCLUDE_USERS_SQL = "AND user_id NOT IN (" + ",".join(str(u) for u in EXCLUDED_USER_IDS) + ")"





# ИНКРЕМЕНТАЛЬНАЯ ЗАГРУЗКА
# Ключ — таблица Moodle, значение — колонка для "водяного знака".
# ETL будет грузить только строки, где watermark_col > last_run_value.
# Остальные таблицы (пользователи, курсы и т.п.) грузятся целиком.
INCREMENTAL_TABLES = {
    "mdl_logstore_standard_log": "timecreated",      # самая большая таблица
    "mdl_course_modules_completion": "timemodified",
    "mdl_grade_grades": "timemodified",
    "mdl_quiz_attempts": "timemodified",
    "mdl_quiz_grades": "timemodified",
    "mdl_question_attempt_steps": "timecreated",
    "mdl_lesson_grades": "completed",
    "mdl_lesson_timer": "lessontime",
    "mdl_assign_submission": "timemodified",
    "mdl_assign_grades": "timemodified",
}

# БАТЧИНГ
# Для MariaDB при чтении больших таблиц читаем чанками.
# CHUNK_SIZE — сколько строк за один запрос.
# BATCH_THRESHOLD — при числе строк > порога используем chunked чтение.

CHUNK_SIZE = 50_000
BATCH_THRESHOLD = 100_000

# Таблицы, для которых всегда используем батчинг (ожидаем > миллиона строк)
LARGE_TABLES = {
    "mdl_logstore_standard_log",
    "mdl_question_attempt_steps",
    "mdl_question_attempts",
}

# БЕЗОПАСНОСТЬ ПОДКЛЮЧЕНИЯ К БД
# Read-only гарантии на уровне драйвера и сессии.
DB_SECURITY = {
    # Session-level настройки MariaDB для гарантии read-only поведения
    "session_sql": [
        "SET SESSION TRANSACTION READ ONLY",           # только READ-транзакции
        "SET SESSION autocommit = 1",                  # чтобы каждый SELECT не висел в транзакции
        "SET SESSION wait_timeout = 600",              # таймаут простоя
        "SET SESSION max_execution_time = 300000",     # макс. время запроса 5 минут (в мс)
    ],
    # Таймауты соединения
    "connect_timeout": 10,
    "read_timeout": 300,
    "write_timeout": 10,
}
