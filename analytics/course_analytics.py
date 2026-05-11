"""
Analytics — Courses
Подробная аналитика по курсам: записи, активность, оценки, completion.
"""

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from etl.load import Loader


class CourseAnalytics:

    def __init__(self, loader: Loader = None):
        self.loader = loader or Loader()

    def overview(self) -> list:
        """Сводная таблица по каждому курсу."""
        df = self.loader.query("""
            WITH course_users AS (
                SELECT course_id, COUNT(DISTINCT user_id) as students
                FROM fact_enrolments
                GROUP BY course_id
            ),
            course_activity AS (
                SELECT course_id,
                       COUNT(*) as events,
                       COUNT(DISTINCT user_id) as active_users
                FROM fact_logs
                WHERE course_id > 0
                GROUP BY course_id
            ),
            course_completion AS (
                SELECT course_id,
                       COUNT(*) as activities,
                       SUM(is_completed) as completed
                FROM fact_completions
                WHERE course_id IS NOT NULL
                GROUP BY course_id
            ),
            course_grades AS (
                SELECT course_id,
                       COUNT(*) as grade_count,
                       ROUND(AVG(grade_percent), 1) as avg_grade,
                       ROUND(
                           AVG(CASE WHEN grade_percent >= 70 THEN 1.0 ELSE 0.0 END) * 100, 1
                       ) as pass_rate
                FROM fact_grades
                WHERE grade_percent IS NOT NULL
                GROUP BY course_id
            ),
            course_certs AS (
                SELECT course_id,
                       COUNT(DISTINCT user_id) as cert_users,
                       COUNT(*) as cert_total
                FROM fact_certificates
                GROUP BY course_id
            )
            SELECT
                c.course_id,
                c.course_name,
                c.course_code,
                c.category_name,
                COALESCE(cu.students, 0) as students,
                COALESCE(ca.active_users, 0) as active_users,
                COALESCE(ca.events, 0) as events,
                CASE
                    WHEN cc.activities > 0
                    THEN ROUND(cc.completed * 100.0 / cc.activities, 1)
                    ELSE 0
                END as module_progress_rate,
                COALESCE(cg.avg_grade, 0) as avg_grade,
                COALESCE(cg.pass_rate, 0) as pass_rate,
                COALESCE(cg.grade_count, 0) as grade_count,
                COALESCE(cc2.cert_users, 0) as certificates_issued,
                CASE
                    WHEN cu.students > 0
                    THEN ROUND(cc2.cert_users * 100.0 / cu.students, 1)
                    ELSE 0
                END as certification_rate
            FROM dim_courses c
            LEFT JOIN course_users cu ON c.course_id = cu.course_id
            LEFT JOIN course_activity ca ON c.course_id = ca.course_id
            LEFT JOIN course_completion cc ON c.course_id = cc.course_id
            LEFT JOIN course_grades cg ON c.course_id = cg.course_id
            LEFT JOIN course_certs cc2 ON c.course_id = cc2.course_id
            WHERE c.is_system = 0
            ORDER BY students DESC, events DESC
        """)

        # Health score: композитный индикатор (0-100)
        # Используем certification_rate (доля сертифицированных) вместо
        # сырого module_progress_rate, потому что сертификат — это конечная цель.
        def health_score(row):
            if row["students"] == 0:
                return 0
            score = 0
            # активность: какая доля записанных вообще заходила
            score += min((row["active_users"] / row["students"]) * 30, 30)
            # сертификация: какая доля записанных получила сертификат
            score += min(row["certification_rate"] * 0.4, 40)
            # успеваемость: средний % сдачи
            score += row["pass_rate"] * 0.3
            return round(score, 1)

        df["health_score"] = df.apply(health_score, axis=1)
        return df.to_dict("records")

    def course_timeline(self, course_id: int) -> dict:
        """Динамика активности по конкретному курсу."""
        monthly = self.loader.query(f"""
            SELECT
                substr(event_at, 1, 7) as month,
                COUNT(*) as events,
                COUNT(DISTINCT user_id) as active_users
            FROM fact_logs
            WHERE course_id = {course_id} AND event_at IS NOT NULL
            GROUP BY month
            ORDER BY month
        """)
        return {"monthly": monthly.to_dict("records")}

    def module_mix(self) -> list:
        """Распределение типов модулей по платформе."""
        df = self.loader.query("""
            SELECT
                dm.module_type_name as module_type,
                COUNT(*) as count
            FROM fact_completions fc
            JOIN dim_modules dm ON fc.module_type_id = dm.module_type_id
            GROUP BY dm.module_type_name
            ORDER BY count DESC
        """)
        return df.to_dict("records")
