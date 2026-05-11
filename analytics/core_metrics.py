"""
Analytics — Core Metrics
KPI верхнего уровня + воронка вовлечённости.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
from etl.load import Loader


class CoreMetrics:
    """Базовые KPI и воронки."""

    def __init__(self, loader: Loader = None):
        self.loader = loader or Loader()

    def kpis(self) -> dict:
        """Главные KPI платформы."""
        q = self.loader.query

        users = q("SELECT COUNT(*) as n FROM dim_users").iloc[0]["n"]
        active_users = q("SELECT COUNT(*) as n FROM dim_users WHERE is_active=1").iloc[0]["n"]
        logged_users = q("SELECT COUNT(DISTINCT user_id) as n FROM fact_logs WHERE user_id IS NOT NULL").iloc[0]["n"]

        courses = q("SELECT COUNT(*) as n FROM dim_courses WHERE is_system=0").iloc[0]["n"]
        enrolments = q("SELECT COUNT(*) as n FROM fact_enrolments").iloc[0]["n"]

        total_events = q("SELECT COUNT(*) as n FROM fact_logs").iloc[0]["n"]

        completions = q("""
            SELECT
                COUNT(*) as total,
                SUM(is_completed) as completed,
                SUM(is_passed) as passed,
                SUM(is_failed) as failed
            FROM fact_completions
        """).iloc[0]

        quiz_stats = q("""
            SELECT
                COUNT(*) as total,
                SUM(is_finished) as finished,
                ROUND(AVG(CASE WHEN is_finished=1 THEN duration_min END), 1) as avg_dur
            FROM fact_quiz_attempts
        """).iloc[0]

        grades = q("""
            SELECT
                COUNT(*) as n,
                ROUND(AVG(grade_percent), 1) as avg_pct,
                ROUND(AVG(CASE WHEN grade_percent >= 70 THEN 1.0 ELSE 0.0 END) * 100, 1) as pass_rate
            FROM fact_grades
            WHERE grade_percent IS NOT NULL
        """).iloc[0]

        # Период данных
        dates = q("""
            SELECT MIN(event_at) as min_date, MAX(event_at) as max_date
            FROM fact_logs
        """).iloc[0]

        # Сертификаты
        certs = q("""
            SELECT
                COUNT(*) as total_issued,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(DISTINCT course_id) as courses_with_certs
            FROM fact_certificates
        """).iloc[0]

        # Активность за последние 7 / 30 дней относительно последнего события
        recent = q("""
            WITH max_d AS (SELECT MAX(event_at) as md FROM fact_logs)
            SELECT
                COUNT(DISTINCT CASE
                    WHEN event_at >= datetime((SELECT md FROM max_d), '-7 days')
                    THEN user_id END) as dau_7d,
                COUNT(DISTINCT CASE
                    WHEN event_at >= datetime((SELECT md FROM max_d), '-30 days')
                    THEN user_id END) as dau_30d
            FROM fact_logs
            WHERE user_id IS NOT NULL AND user_id NOT IN (2,227,229,355,359,377)
        """).iloc[0]

        # Сертификаты за последние 7 дней (относительно последнего события платформы)
        certs_recent = q("""
            WITH max_d AS (SELECT MAX(event_at) as md FROM fact_logs)
            SELECT
                COUNT(*) as issued_7d,
                COUNT(DISTINCT user_id) as users_7d
            FROM fact_certificates
            WHERE issued_at IS NOT NULL
              AND issued_at >= datetime((SELECT md FROM max_d), '-7 days')
        """).iloc[0]

        # Топ-3 организации по числу студентов с активностью
        top_orgs = q("""
            SELECT u.organization, COUNT(DISTINCT u.id) as users
            FROM dim_users u
            WHERE u.is_active=1 AND u.organization IS NOT NULL
              AND u.organization != 'Физ. лицо'
            GROUP BY u.organization
            ORDER BY users DESC
            LIMIT 5
        """).to_dict("records")

        return {
            "total_users": int(users),
            "active_users": int(active_users),
            "users_with_activity": int(logged_users),
            "engagement_rate": round(logged_users / active_users * 100, 1) if active_users else 0,
            "total_courses": int(courses),
            "total_enrolments": int(enrolments),
            "total_events": int(total_events),
            "completion_rate": round(completions["completed"] / completions["total"] * 100, 1)
                if completions["total"] else 0,
            "total_completions": int(completions["completed"] or 0),
            "total_quiz_attempts": int(quiz_stats["total"]),
            "finished_quiz_attempts": int(quiz_stats["finished"] or 0),
            "avg_quiz_duration_min": float(quiz_stats["avg_dur"] or 0),
            "avg_grade_percent": float(grades["avg_pct"] or 0),
            "grade_pass_rate": float(grades["pass_rate"] or 0),
            "period_start": dates["min_date"],
            "period_end": dates["max_date"],
            # Новые метрики
            "certificates_issued": int(certs["total_issued"] or 0),
            "users_with_certificate": int(certs["unique_users"] or 0),
            "courses_with_certificates": int(certs["courses_with_certs"] or 0),
            "certification_rate": round(
                (certs["unique_users"] or 0) / logged_users * 100, 1
            ) if logged_users else 0,
            "active_last_7d": int(recent["dau_7d"] or 0),
            "active_last_30d": int(recent["dau_30d"] or 0),
            "certificates_last_7d": int(certs_recent["issued_7d"] or 0),
            "users_with_certificate_7d": int(certs_recent["users_7d"] or 0),
            "top_organizations": top_orgs,
        }

    def engagement_funnel(self) -> list:
        """Воронка: регистрация → запись → активность → завершение → успех."""
        q = self.loader.query

        registered = q("SELECT COUNT(*) as n FROM dim_users WHERE is_active=1").iloc[0]["n"]

        enrolled = q("""
            SELECT COUNT(DISTINCT user_id) as n FROM fact_enrolments
        """).iloc[0]["n"]

        active = q("""
            SELECT COUNT(DISTINCT user_id) as n FROM fact_logs
            WHERE user_id IS NOT NULL
        """).iloc[0]["n"]

        made_attempts = q("""
            SELECT COUNT(DISTINCT user_id) as n FROM fact_quiz_attempts
        """).iloc[0]["n"]

        completed = q("""
            SELECT COUNT(DISTINCT user_id) as n FROM fact_completions
            WHERE is_completed = 1
        """).iloc[0]["n"]

        graduated = q("""
            SELECT COUNT(DISTINCT user_id) as n FROM fact_grades
            WHERE grade_percent >= 60
        """).iloc[0]["n"]

        # Сертификаты — конечная цель пользовательского путешествия
        certified = q("""
            SELECT COUNT(DISTINCT user_id) as n FROM fact_certificates
        """).iloc[0]["n"]

        stages = [
            ("Зарегистрированы", int(registered)),
            ("Записались на курс", int(enrolled)),
            ("Были активны", int(active)),
            ("Начали тесты", int(made_attempts)),
            ("Завершили модули", int(completed)),
            ("Сдали с оценкой ≥ 60%", int(graduated)),
            ("Получили сертификат", int(certified)),
        ]

        funnel = []
        prev_count = stages[0][1] or 1
        first_count = stages[0][1] or 1
        for i, (name, cnt) in enumerate(stages):
            funnel.append({
                "stage": name,
                "count": cnt,
                # Конверсия от предыдущего шага
                "conversion_step": round((cnt / prev_count * 100) if prev_count else 0, 1),
                # Конверсия от вершины воронки (от зарегистрированных)
                "conversion_total": round((cnt / first_count * 100) if first_count else 0, 1),
                # Сколько потеряли на этом шаге
                "drop_off": (prev_count - cnt) if i > 0 else 0,
            })
            prev_count = cnt
        return funnel

    def dau_90_days(self) -> list:
        """
        Динамика DAU за последние 90 дней относительно MAX(event_at).
        Возвращает список словарей: {date, dau, events}.
        Дата всегда полная YYYY-MM-DD — корректно работает на стыке годов.
        """
        q = self.loader.query

        max_d = q("SELECT MAX(event_at) as md FROM fact_logs").iloc[0]["md"]
        if not max_d:
            return []

        rows = q("""
            WITH max_d AS (SELECT MAX(event_at) as md FROM fact_logs)
            SELECT
                substr(event_at, 1, 10) as date,
                COUNT(DISTINCT user_id) as dau,
                COUNT(*) as events
            FROM fact_logs
            WHERE user_id IS NOT NULL
              AND user_id NOT IN (2,227,229,355,359,377)
              AND event_at >= datetime((SELECT md FROM max_d), '-90 days')
            GROUP BY date
            ORDER BY date
        """)
        return rows.to_dict("records")

    def overall_effectiveness(self) -> dict:
        """
        Общий коэффициент эффективности всех курсов платформы (0–100).

        Считается аналогично health-score одного курса, но усреднённо
        по всем активным курсам с записанными студентами:

            effectiveness = (Σ active_users / Σ students) * 30      # активность
                          + min(avg_certification_rate, 100) * 0.4   # сертификация
                          + avg_pass_rate * 0.3                      # успеваемость

        Возвращает разложение по компонентам — это даёт админу понимание,
        что именно тянет показатель вниз.
        """
        q = self.loader.query

        agg = q("""
            WITH course_users AS (
                SELECT course_id, COUNT(DISTINCT user_id) as students
                FROM fact_enrolments
                GROUP BY course_id
            ),
            course_activity AS (
                SELECT course_id, COUNT(DISTINCT user_id) as active_users
                FROM fact_logs
                WHERE course_id > 0 AND user_id IS NOT NULL
                  AND user_id NOT IN (2,227,229,355,359,377)
                GROUP BY course_id
            ),
            course_certs AS (
                SELECT course_id, COUNT(DISTINCT user_id) as cert_users
                FROM fact_certificates
                GROUP BY course_id
            ),
            course_grades AS (
                SELECT course_id,
                       AVG(CASE WHEN grade_percent >= 70 THEN 1.0 ELSE 0.0 END) * 100 as pass_rate
                FROM fact_grades
                WHERE grade_percent IS NOT NULL
                GROUP BY course_id
            )
            SELECT
                COUNT(*) as courses_total,
                SUM(COALESCE(cu.students, 0)) as total_students,
                SUM(COALESCE(ca.active_users, 0)) as total_active,
                AVG(CASE WHEN cu.students > 0
                         THEN (cc.cert_users * 100.0 / cu.students) ELSE 0 END) as avg_cert_rate,
                AVG(COALESCE(cg.pass_rate, 0)) as avg_pass_rate
            FROM dim_courses c
            LEFT JOIN course_users cu ON c.course_id = cu.course_id
            LEFT JOIN course_activity ca ON c.course_id = ca.course_id
            LEFT JOIN course_certs cc ON c.course_id = cc.course_id
            LEFT JOIN course_grades cg ON c.course_id = cg.course_id
            WHERE c.is_system = 0 AND COALESCE(cu.students, 0) > 0
        """).iloc[0]

        students = float(agg["total_students"] or 0)
        active = float(agg["total_active"] or 0)
        cert_rate = float(agg["avg_cert_rate"] or 0)
        pass_rate = float(agg["avg_pass_rate"] or 0)

        # компоненты health-score, такие же как в course_analytics
        activity_pts = min((active / students) * 30, 30) if students else 0
        cert_pts = min(cert_rate * 0.4, 40)
        pass_pts = min(pass_rate * 0.3, 30)
        total = round(activity_pts + cert_pts + pass_pts, 1)

        # Категория эффективности
        if total >= 70:
            category = "high"
            label = "Высокая"
        elif total >= 40:
            category = "medium"
            label = "Средняя"
        else:
            category = "low"
            label = "Низкая"

        return {
            "score": total,
            "category": category,
            "label": label,
            "courses_count": int(agg["courses_total"] or 0),
            "components": {
                "activity": round(activity_pts, 1),
                "activity_max": 30,
                "certification": round(cert_pts, 1),
                "certification_max": 40,
                "pass_rate": round(pass_pts, 1),
                "pass_rate_max": 30,
            },
            "raw": {
                "activity_ratio": round((active / students * 100) if students else 0, 1),
                "avg_certification_rate": round(cert_rate, 1),
                "avg_pass_rate": round(pass_rate, 1),
            },
        }

    def certificates_filter_data(self) -> dict:
        """
        Подготовка данных для интерактивного фильтра сертификатов.

        Отдаёт:
          - список курсов (id, имя, всего сертификатов, дата первого/последнего)
          - все события выдачи сертификатов в виде {date, course_id} для агрегации
            на стороне браузера при изменении фильтра пользователем
          - границы дат

        Все даты — полные YYYY-MM-DD, чтобы переход через год не путался.
        """
        q = self.loader.query

        # Список курсов с сертификатами + общие счётчики
        courses = q("""
            SELECT
                fc.course_id,
                COALESCE(c.course_name, '— курс не найден —') as course_name,
                c.course_code,
                COUNT(*) as certs_total,
                COUNT(DISTINCT fc.user_id) as users_total,
                MIN(substr(fc.issued_at, 1, 10)) as first_issued,
                MAX(substr(fc.issued_at, 1, 10)) as last_issued
            FROM fact_certificates fc
            LEFT JOIN dim_courses c ON c.course_id = fc.course_id
            WHERE fc.issued_at IS NOT NULL
            GROUP BY fc.course_id, c.course_name, c.course_code
            ORDER BY certs_total DESC
        """).to_dict("records")

        # Все события выдачи: для интерактивной агрегации в браузере
        # (формат компактный: одна строка на сертификат)
        issues = q("""
            SELECT
                substr(issued_at, 1, 10) as date,
                course_id,
                user_id
            FROM fact_certificates
            WHERE issued_at IS NOT NULL
            ORDER BY issued_at
        """).to_dict("records")

        # Границы периода
        bounds = q("""
            SELECT
                MIN(substr(issued_at, 1, 10)) as min_date,
                MAX(substr(issued_at, 1, 10)) as max_date
            FROM fact_certificates
            WHERE issued_at IS NOT NULL
        """).iloc[0]

        return {
            "courses": courses,
            "issues": issues,
            "min_date": bounds["min_date"],
            "max_date": bounds["max_date"],
        }

    def activity_over_time(self) -> dict:
        """Активность по времени: месяцы, DAU, дни недели, часы."""
        q = self.loader.query

        monthly = q("""
            SELECT
                substr(event_at, 1, 7) as month,
                COUNT(*) as events,
                COUNT(DISTINCT user_id) as active_users
            FROM fact_logs
            WHERE event_at >= '2025-07-01'
            GROUP BY month
            ORDER BY month
        """)

        daily = q("""
            SELECT
                substr(event_at, 1, 10) as date,
                COUNT(*) as events,
                COUNT(DISTINCT user_id) as dau
            FROM fact_logs
            WHERE event_at >= '2025-07-01'
            GROUP BY date
            ORDER BY date
        """)

        # Для дня недели и часа нужен pandas
        logs = q("SELECT event_at FROM fact_logs WHERE event_at >= '2025-07-01' LIMIT 500000")
        logs["dt"] = pd.to_datetime(logs["event_at"], errors="coerce")
        logs = logs.dropna()

        weekday_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        wd = logs["dt"].dt.dayofweek.value_counts().sort_index()
        weekday = [{"day": weekday_names[i], "events": int(wd.get(i, 0))} for i in range(7)]

        hr = logs["dt"].dt.hour.value_counts().sort_index()
        hourly = [{"hour": h, "events": int(hr.get(h, 0))} for h in range(24)]

        # Heatmap day x hour
        logs2 = logs.copy()
        logs2["wd"] = logs2["dt"].dt.dayofweek
        logs2["hr"] = logs2["dt"].dt.hour
        heatmap = logs2.groupby(["wd", "hr"]).size().reset_index(name="events")
        heatmap_matrix = [[0] * 24 for _ in range(7)]
        for _, r in heatmap.iterrows():
            heatmap_matrix[int(r["wd"])][int(r["hr"])] = int(r["events"])

        return {
            "monthly": monthly.to_dict("records"),
            "daily": daily.to_dict("records"),
            "weekday": weekday,
            "hourly": hourly,
            "heatmap": {
                "days": weekday_names,
                "hours": list(range(24)),
                "matrix": heatmap_matrix,
            },
        }
