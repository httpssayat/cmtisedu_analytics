"""
ETL — Transform
Очищает, типизирует и обогащает данные.
Создаёт производные таблицы (dimensions + facts) для аналитики.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import TABLE_SCHEMAS


class Transformer:
    """Преобразует сырые таблицы Moodle в чистые dimension/fact таблицы."""

    def __init__(self, raw_data: dict):
        """
        raw_data: dict[str, pd.DataFrame] — сырые таблицы из Extractor
        """
        self.raw = raw_data
        self.clean = {}

    # УТИЛИТЫ

    def _clean_table(self, table_name: str) -> pd.DataFrame:
        """Базовая очистка: оставляем только нужные колонки, типизируем."""
        if table_name not in self.raw or self.raw[table_name].empty:
            schema = TABLE_SCHEMAS.get(table_name, {})
            return pd.DataFrame(columns=schema.get("keep", []))

        df = self.raw[table_name].copy()
        schema = TABLE_SCHEMAS[table_name]

        # Оставляем только нужные колонки
        keep = [c for c in schema["keep"] if c in df.columns]
        df = df[keep]

        # Типизация числовых
        for col in schema.get("numeric", []):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        return df

    @staticmethod
    def _ts_to_datetime(series):
        """Unix timestamp → datetime."""
        return pd.to_datetime(series, unit="s", errors="coerce")






    # DIMENSIONS


    def build_dim_users(self) -> pd.DataFrame:
        """Измерение: пользователи."""
        df = self._clean_table("mdl_user")
        if df.empty:
            return df

        df["full_name"] = (
            df["firstname"].fillna("").str.strip() + " " +
            df["lastname"].fillna("").str.strip()
        ).str.strip()
        df["full_name"] = df["full_name"].replace("", None)

        df["is_active"] = ((df["deleted"] != 1) & (df["suspended"] != 1)).astype(int)

        # Исключаем известных админов/тест-аккаунтов из аналитики
        try:
            from config import EXCLUDED_USER_IDS
            df.loc[df["id"].isin(EXCLUDED_USER_IDS), "is_active"] = 0
        except Exception:
            pass

        df["created_at"] = self._ts_to_datetime(df["timecreated"])
        df["last_access_at"] = self._ts_to_datetime(df["lastaccess"])
        df["last_login_at"] = self._ts_to_datetime(df["lastlogin"])

        # Подмешиваем организацию из user_info_data (custom field "org")
        df["organization"] = self._build_organization_map(df["id"])

        return df[["id", "username", "full_name", "firstname", "lastname",
                   "email", "is_active", "country", "city", "organization",
                   "created_at", "last_access_at", "last_login_at"]]

    def _build_organization_map(self, user_ids):
        """Достаёт значение custom field 'org' (Организация) для каждого пользователя.
        Возвращает Series с организациями (None если не заполнено или = 'Физ. лицо')."""
        try:
            fields = self._clean_table("mdl_user_info_field")
            data = self._clean_table("mdl_user_info_data")
            if fields.empty or data.empty:
                return pd.Series([None] * len(user_ids), index=user_ids.index)

            # Находим field_id для shortname='org'
            org_field = fields[fields["shortname"] == "org"]
            if org_field.empty:
                return pd.Series([None] * len(user_ids), index=user_ids.index)
            org_field_id = int(org_field.iloc[0]["id"])

            # Собираем словарь user_id → organization
            org_data = data[data["fieldid"] == org_field_id].copy()
            org_data["data"] = org_data["data"].astype(str).str.strip()
            # "Физ. лицо" — это значение по умолчанию для физических лиц,
            # его обрабатываем отдельно: оставляем как организацию,
            # но в дашборде показываем как "—" если хотим скрыть
            org_map = dict(zip(org_data["userid"], org_data["data"]))

            return user_ids.map(org_map)
        except Exception:
            return pd.Series([None] * len(user_ids), index=user_ids.index)

    def build_dim_courses(self) -> pd.DataFrame:
        """Измерение: курсы."""
        df = self._clean_table("mdl_course")
        cats = self._clean_table("mdl_course_categories")

        if df.empty:
            return df

        df = df.rename(columns={
            "id": "course_id",
            "category": "category_id",
            "fullname": "course_name",
            "shortname": "course_code",
        })

        # Категории
        if not cats.empty:
            cats_map = cats.set_index("id")["name"].to_dict()
            df["category_name"] = df["category_id"].map(cats_map)
        else:
            df["category_name"] = None

        # Убираем системный курс id=1 (SITE) из аналитики
        df["is_system"] = (df["course_id"] == 1).astype(int)

        # Отсеиваем записи с NaN в course_id (битые строки)
        df = df[df["course_id"].notna()].copy()
        df["course_id"] = df["course_id"].astype(int)

        return df[["course_id", "course_name", "course_code",
                   "category_id", "category_name", "is_system"]]

    def build_dim_modules(self) -> pd.DataFrame:
        """Измерение: типы модулей Moodle."""
        df = self._clean_table("mdl_modules")
        return df.rename(columns={"id": "module_type_id", "name": "module_type_name"})

    



    # FACTS
    

    def build_fact_enrolments(self) -> pd.DataFrame:
        """Факт: записи пользователей на курсы."""
        ue = self._clean_table("mdl_user_enrolments")
        en = self._clean_table("mdl_enrol")

        if ue.empty or en.empty:
            return pd.DataFrame()

        # Джойн для получения course_id
        merged = ue.merge(
            en[["id", "courseid", "enrol"]].rename(
                columns={"id": "enrolid", "courseid": "course_id", "enrol": "enrol_method"}
            ),
            on="enrolid",
            how="left",
        )

        merged["enrolled_at"] = self._ts_to_datetime(merged["timecreated"])
        merged["start_at"] = self._ts_to_datetime(merged["timestart"])
        merged["end_at"] = self._ts_to_datetime(merged["timeend"])

        return merged.rename(columns={"userid": "user_id"})[[
            "id", "user_id", "course_id", "enrol_method", "status",
            "enrolled_at", "start_at", "end_at"
        ]]

    def build_fact_completions(self) -> pd.DataFrame:
        """Факт: завершения модулей."""
        comp = self._clean_table("mdl_course_modules_completion")
        cm = self._clean_table("mdl_course_modules")

        if comp.empty:
            return pd.DataFrame()

        # Присоединяем course_id и module_type
        if not cm.empty:
            comp = comp.merge(
                cm[["id", "course", "module"]].rename(
                    columns={"id": "coursemoduleid", "course": "course_id",
                             "module": "module_type_id"}
                ),
                on="coursemoduleid",
                how="left",
            )

        comp["completed_at"] = self._ts_to_datetime(comp["timemodified"])
        comp["is_completed"] = comp["completionstate"].isin([1, 2]).astype(int)
        comp["is_passed"] = (comp["completionstate"] == 2).astype(int)
        comp["is_failed"] = (comp["completionstate"] == 3).astype(int)

        cols = ["id", "userid", "coursemoduleid", "completionstate",
                "is_completed", "is_passed", "is_failed", "completed_at"]
        if "course_id" in comp.columns:
            cols.append("course_id")
        if "module_type_id" in comp.columns:
            cols.append("module_type_id")

        return comp[cols].rename(columns={"userid": "user_id"})

    def build_fact_grades(self) -> pd.DataFrame:
        """Факт: оценки (агрегированные по grade_items)."""
        gg = self._clean_table("mdl_grade_grades")
        gi = self._clean_table("mdl_grade_items")

        if gg.empty or gi.empty:
            return pd.DataFrame()

        # Присоединяем метаданные grade_item
        merged = gg.merge(
            gi[["id", "courseid", "itemname", "itemtype", "itemmodule", "grademax"]].rename(
                columns={"id": "itemid", "courseid": "course_id",
                         "grademax": "item_grademax"}
            ),
            on="itemid",
            how="left",
        )

        # Нормализация оценки (0-100%)
        merged["grade_percent"] = np.where(
            (merged["item_grademax"].notna()) & (merged["item_grademax"] > 0) &
            (merged["finalgrade"].notna()),
            merged["finalgrade"] / merged["item_grademax"] * 100,
            np.nan,
        )
        merged["grade_percent"] = merged["grade_percent"].clip(0, 100)

        merged["graded_at"] = self._ts_to_datetime(merged["timemodified"])

        return merged[[
            "id", "userid", "course_id", "itemid", "itemname", "itemtype",
            "itemmodule", "finalgrade", "item_grademax", "grade_percent",
            "graded_at"
        ]].rename(columns={"userid": "user_id"})

    def build_fact_quiz_attempts(self) -> pd.DataFrame:
        """Факт: попытки прохождения тестов."""
        qa = self._clean_table("mdl_quiz_attempts")
        q = self._clean_table("mdl_quiz")

        if qa.empty:
            return pd.DataFrame()

        # Присоединяем метаданные квиза
        if not q.empty:
            qa = qa.merge(
                q[["id", "course", "name"]].rename(
                    columns={"id": "quiz", "course": "course_id", "name": "quiz_name"}
                ),
                on="quiz",
                how="left",
            )

        qa["started_at"] = self._ts_to_datetime(qa["timestart"])
        qa["finished_at"] = self._ts_to_datetime(qa["timefinish"])
        qa["duration_sec"] = qa["timefinish"] - qa["timestart"]
        qa["duration_min"] = qa["duration_sec"] / 60
        # Отфильтровываем аномальные длительности (>5 часов — явно артефакт)
        qa.loc[qa["duration_min"] > 300, "duration_min"] = np.nan
        qa.loc[qa["duration_min"] < 0, "duration_min"] = np.nan

        qa["is_finished"] = (qa["state"] == "finished").astype(int)

        cols = ["id", "quiz", "userid", "attempt", "state",
                "started_at", "finished_at", "duration_min", "sumgrades",
                "is_finished"]
        if "course_id" in qa.columns:
            cols.append("course_id")
        if "quiz_name" in qa.columns:
            cols.append("quiz_name")

        return qa[cols].rename(columns={"userid": "user_id", "quiz": "quiz_id"})

    def build_fact_question_attempts(self) -> pd.DataFrame:
        """Факт: попытки ответов на вопросы (для анализа сложности)."""
        qas = self._clean_table("mdl_question_attempt_steps")
        if qas.empty:
            return pd.DataFrame()

        qa_meta = self._clean_table("mdl_question_attempts")
        q = self._clean_table("mdl_question")

        # Оставляем только финальные состояния (gradedright/gradedwrong/gradedpartial)
        graded_states = ["gradedright", "gradedwrong", "gradedpartial", "gaveup"]
        finals = qas[qas["state"].isin(graded_states)].copy()

        if finals.empty:
            return pd.DataFrame()

        # Берём последний шаг для каждой попытки
        finals = finals.sort_values("sequencenumber").groupby("questionattemptid").tail(1)

        # Присоединяем метаданные вопроса через qa_meta
        if not qa_meta.empty:
            finals = finals.merge(
                qa_meta[["id", "questionid", "maxmark"]].rename(
                    columns={"id": "questionattemptid"}
                ),
                on="questionattemptid",
                how="left",
            )

        # Присоединяем тип вопроса
        if not q.empty and "questionid" in finals.columns:
            finals = finals.merge(
                q[["id", "qtype", "name"]].rename(
                    columns={"id": "questionid", "name": "question_name"}
                ),
                on="questionid",
                how="left",
            )

        finals["answered_at"] = self._ts_to_datetime(finals["timecreated"])
        finals["is_correct"] = (finals["state"] == "gradedright").astype(int)
        finals["is_partial"] = (finals["state"] == "gradedpartial").astype(int)
        finals["is_wrong"] = (finals["state"] == "gradedwrong").astype(int)
        finals["is_gaveup"] = (finals["state"] == "gaveup").astype(int)

        cols = ["id", "questionattemptid", "userid", "state",
                "fraction", "answered_at", "is_correct", "is_partial",
                "is_wrong", "is_gaveup"]
        for c in ["questionid", "maxmark", "qtype", "question_name"]:
            if c in finals.columns:
                cols.append(c)

        return finals[cols].rename(columns={"userid": "user_id"})

    def build_fact_logs(self) -> pd.DataFrame:
        """Факт: события из логов (чистые, с датами)."""
        logs = self._clean_table("mdl_logstore_standard_log")
        if logs.empty:
            return pd.DataFrame()

        logs["event_at"] = self._ts_to_datetime(logs["timecreated"])
        # Отбрасываем строки с невалидной датой
        logs = logs[logs["event_at"].notna()]
        # Отбрасываем даты до 2020 года (артефакты)
        logs = logs[logs["event_at"] >= pd.Timestamp("2020-01-01")]

        # Упрощённое имя события
        logs["event_short"] = logs["eventname"].str.replace(r'\\+', '/', regex=True).str.split('/').str[-1]

        return logs.rename(columns={"userid": "user_id", "courseid": "course_id"})[[
            "id", "user_id", "course_id", "eventname", "event_short",
            "component", "action", "target", "crud", "event_at", "origin"
        ]]

    def build_fact_lesson_grades(self) -> pd.DataFrame:
        lg = self._clean_table("mdl_lesson_grades")
        if lg.empty:
            return pd.DataFrame()

        lg["graded_at"] = self._ts_to_datetime(lg["completed"])
        return lg.rename(columns={"userid": "user_id", "lesson": "lesson_id"})[[
            "id", "user_id", "lesson_id", "grade", "graded_at"
        ]]

    def build_fact_lesson_timer(self) -> pd.DataFrame:
        lt = self._clean_table("mdl_lesson_timer")
        if lt.empty:
            return pd.DataFrame()

        lt["started_at"] = self._ts_to_datetime(lt["starttime"])
        lt["finished_at"] = self._ts_to_datetime(lt["lessontime"])
        lt["duration_min"] = (lt["lessontime"] - lt["starttime"]) / 60
        lt.loc[lt["duration_min"] > 300, "duration_min"] = np.nan
        lt.loc[lt["duration_min"] < 0, "duration_min"] = np.nan

        return lt.rename(columns={"userid": "user_id", "lessonid": "lesson_id"})[[
            "id", "user_id", "lesson_id", "started_at", "finished_at",
            "duration_min", "completed"
        ]]

    def build_fact_certificates(self) -> pd.DataFrame:
        """Факт: выданные сертификаты (плагин customcert).

        Каждая запись = один сертификат, выданный конкретному пользователю по конкретному курсу.
        Сертификат выдаётся плагином customcert когда выполнены условия его получения
        (обычно — успешная сдача обязательного теста с проходным баллом)."""
        certs = self._clean_table("mdl_customcert")
        issues = self._clean_table("mdl_customcert_issues")

        if issues.empty or certs.empty:
            return pd.DataFrame(columns=[
                "id", "user_id", "course_id", "customcert_id",
                "certificate_name", "issued_at"
            ])

        # Связываем выдачу с курсом через mdl_customcert
        cert_map = certs.set_index("id").to_dict("index")

        issues["course_id"] = issues["customcertid"].map(
            lambda x: cert_map.get(x, {}).get("course")
        )
        issues["certificate_name"] = issues["customcertid"].map(
            lambda x: cert_map.get(x, {}).get("name")
        )
        issues["issued_at"] = self._ts_to_datetime(issues["timecreated"])

        issues = issues.dropna(subset=["course_id", "userid"])
        issues["course_id"] = issues["course_id"].astype(int)
        issues["userid"] = issues["userid"].astype(int)

        return issues.rename(columns={
            "userid": "user_id",
            "customcertid": "customcert_id",
        })[["id", "user_id", "course_id", "customcert_id",
            "certificate_name", "issued_at"]]




    # ORCHESTRATION

    def transform_all(self) -> dict:
        """Собирает все dimension и fact таблицы."""
        print("Трансформация данных...")
        builders = {
            "dim_users": self.build_dim_users,
            "dim_courses": self.build_dim_courses,
            "dim_modules": self.build_dim_modules,
            "fact_enrolments": self.build_fact_enrolments,
            "fact_completions": self.build_fact_completions,
            "fact_grades": self.build_fact_grades,
            "fact_quiz_attempts": self.build_fact_quiz_attempts,
            "fact_question_attempts": self.build_fact_question_attempts,
            "fact_logs": self.build_fact_logs,
            "fact_lesson_grades": self.build_fact_lesson_grades,
            "fact_lesson_timer": self.build_fact_lesson_timer,
            "fact_certificates": self.build_fact_certificates,
        }

        for name, builder in builders.items():
            try:
                self.clean[name] = builder()
                print(f"  ✓ {name}: {len(self.clean[name])} записей")
            except Exception as e:
                print(f"  ✗ {name}: {e}")
                import traceback
                traceback.print_exc()
                self.clean[name] = pd.DataFrame()

        return self.clean
