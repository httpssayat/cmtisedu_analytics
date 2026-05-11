"""
Analytics — Question Difficulty & Engagement
Анализ сложности вопросов тестов и вовлечённости пользователей.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
from etl.load import Loader


class QuestionAnalytics:
    """Какие вопросы сложные? Какие угадывают? Где пользователи сдаются?"""

    def __init__(self, loader: Loader = None):
        self.loader = loader or Loader()

    def question_difficulty(self, min_attempts: int = 5) -> list:
        """
        Индекс сложности по методологии CTT (Classical Test Theory):
        - avg_fraction = средняя доля правильности (0-100%), учитывает partial credit
        - p_correct = % полностью правильных ответов (для справки)
        Такой подход корректно отражает сложность для multichoice-вопросов,
        где частичный ответ не означает неправильный.
        """
        df = self.loader.query(f"""
            SELECT
                questionid,
                COALESCE(question_name, 'Вопрос #' || questionid) as question_name,
                qtype,
                COUNT(*) as attempts,
                SUM(is_correct) as fully_correct,
                SUM(is_partial) as partial,
                SUM(is_wrong) as wrong,
                SUM(is_gaveup) as gaveup,
                ROUND(AVG(fraction) * 100, 1) as avg_fraction,
                COUNT(DISTINCT user_id) as unique_users
            FROM fact_question_attempts
            WHERE questionid IS NOT NULL AND fraction IS NOT NULL
            GROUP BY questionid, question_name, qtype
            HAVING attempts >= {min_attempts}
            ORDER BY attempts DESC
        """)

        if df.empty:
            return []

        df["full_correct_rate"] = (df["fully_correct"] / df["attempts"] * 100).round(1)
        df["wrong_rate"] = (df["wrong"] / df["attempts"] * 100).round(1)
        df["giveup_rate"] = (df["gaveup"] / df["attempts"] * 100).round(1)

        # Индекс сложности = средняя fraction (0=самый сложный, 100=тривиальный)
        df["difficulty_index"] = df["avg_fraction"]

        # Для совместимости с существующим UI
        df["correct_rate"] = df["avg_fraction"]

        def classify(rate):
            if rate < 30:
                return "🔴 очень сложный"
            elif rate < 50:
                return "🟠 сложный"
            elif rate < 75:
                return "🟡 средний"
            elif rate < 90:
                return "🟢 лёгкий"
            else:
                return "⚪ тривиальный"

        df["difficulty_class"] = df["avg_fraction"].apply(classify)
        df["question_short"] = df["question_name"].fillna("").str.replace(r'<[^>]+>', '', regex=True).str.slice(0, 80)

        return df.to_dict("records")

    def difficulty_distribution(self) -> dict:
        """Распределение вопросов по уровню сложности (на основе avg fraction)."""
        df = self.loader.query("""
            SELECT
                questionid,
                COUNT(*) as attempts,
                AVG(fraction) * 100 as rate
            FROM fact_question_attempts
            WHERE questionid IS NOT NULL AND fraction IS NOT NULL
            GROUP BY questionid
            HAVING attempts >= 3
        """)
        if df.empty:
            return {}

        bins = [0, 30, 50, 75, 90, 100.01]
        labels = ["очень сложный (<30%)", "сложный (30-50%)",
                  "средний (50-75%)", "лёгкий (75-90%)", "тривиальный (≥90%)"]
        df["bin"] = pd.cut(df["rate"], bins=bins, labels=labels, include_lowest=True)
        counts = df["bin"].value_counts().reindex(labels, fill_value=0)

        return {
            "labels": labels,
            "counts": [int(x) for x in counts.values],
            "total_questions": len(df),
            "avg_difficulty": round(float(df["rate"].mean()), 1),
            "median_difficulty": round(float(df["rate"].median()), 1),
        }

    def problematic_questions(self, limit: int = 20) -> list:
        """Самые проблемные вопросы: низкий % правильных + много попыток."""
        df = pd.DataFrame(self.question_difficulty(min_attempts=10))
        if df.empty:
            return []
        return df.nsmallest(limit, "correct_rate").to_dict("records")


class EngagementAnalytics:
    """Вовлечённость: как активны пользователи, кто топ, кто слаб."""

    def __init__(self, loader: Loader = None):
        self.loader = loader or Loader()

    def user_engagement_scores(self, top_n: int = 30) -> dict:
        """
        Композитный engagement score (0-100) по каждому пользователю.
        Компоненты:
        - активность (логи)
        - регулярность (активные дни)
        - вовлечённость в контент (просмотры модулей)
        - завершение (completions)
        - успеваемость (grade %)
        """
        df = self.loader.query("""
            WITH user_events AS (
                SELECT user_id,
                       COUNT(*) as events,
                       COUNT(DISTINCT substr(event_at, 1, 10)) as active_days,
                       COUNT(DISTINCT course_id) as courses_touched
                FROM fact_logs
                WHERE user_id IS NOT NULL AND user_id NOT IN (2,227,229,355,359,377)
                GROUP BY user_id
            ),
            user_completions AS (
                SELECT user_id,
                       SUM(is_completed) as completions,
                       COUNT(*) as activities_started
                FROM fact_completions
                GROUP BY user_id
            ),
            user_grades AS (
                SELECT user_id,
                       COUNT(*) as grades_count,
                       AVG(grade_percent) as avg_grade
                FROM fact_grades
                WHERE grade_percent IS NOT NULL
                GROUP BY user_id
            ),
            user_quizzes AS (
                SELECT user_id,
                       SUM(is_finished) as quizzes_done,
                       COUNT(*) as quiz_attempts
                FROM fact_quiz_attempts
                GROUP BY user_id
            )
            SELECT
                du.id as user_id,
                du.full_name,
                du.email,
                COALESCE(du.organization, '') as organization,
                COALESCE(ue.events, 0) as events,
                COALESCE(ue.active_days, 0) as active_days,
                COALESCE(ue.courses_touched, 0) as courses,
                COALESCE(uc.completions, 0) as completions,
                COALESCE(uq.quizzes_done, 0) as quizzes_done,
                COALESCE(ug.avg_grade, 0) as avg_grade
            FROM dim_users du
            LEFT JOIN user_events ue ON du.id = ue.user_id
            LEFT JOIN user_completions uc ON du.id = uc.user_id
            LEFT JOIN user_grades ug ON du.id = ug.user_id
            LEFT JOIN user_quizzes uq ON du.id = uq.user_id
            WHERE du.is_active = 1
              AND ue.events IS NOT NULL
        """)

        if df.empty:
            return {"top_students": [], "distribution": []}

        # Нормализация компонентов (0-100)
        def pct_rank(col):
            return col.rank(pct=True) * 100

        df["score_activity"] = pct_rank(df["events"])
        df["score_regularity"] = pct_rank(df["active_days"])
        df["score_completion"] = pct_rank(df["completions"])
        df["score_grades"] = df["avg_grade"].fillna(0)
        df["score_quizzes"] = pct_rank(df["quizzes_done"])

        # Композитный score (веса)
        df["engagement_score"] = (
            df["score_activity"] * 0.20
            + df["score_regularity"] * 0.25
            + df["score_completion"] * 0.20
            + df["score_grades"] * 0.25
            + df["score_quizzes"] * 0.10
        ).round(1)

        # Классификация
        def label(score):
            if score >= 70: return "🔥 высокая"
            if score >= 40: return "✅ средняя"
            if score >= 20: return "⚠️ низкая"
            return "❄️ пассивная"

        df["engagement_class"] = df["engagement_score"].apply(label)

        # Топ
        top = df.nlargest(top_n, "engagement_score").copy()
        # Убираем NaN для JSON
        top = top.fillna(0)
        top_list = top.to_dict("records")

        # Распределение
        dist = df["engagement_class"].value_counts().to_dict()
        classes_order = ["🔥 высокая", "✅ средняя", "⚠️ низкая", "❄️ пассивная"]
        distribution = [{"class": c, "count": int(dist.get(c, 0))} for c in classes_order]

        return {
            "top_students": top_list,
            "distribution": distribution,
            "total_engaged": len(df),
        }

    def at_risk_students(self) -> dict:
        """
        Студенты с риском отсева:
        - записаны на курс, но не заходили
        - не заходили >14 дней
        - не заходили >30 дней
        """
        from datetime import datetime, timedelta

        # Берём дату последней записи как "текущий момент"
        max_date_row = self.loader.query(
            "SELECT MAX(event_at) as max_dt FROM fact_logs"
        )
        max_date = pd.to_datetime(max_date_row.iloc[0]["max_dt"])

        df = self.loader.query("""
            WITH user_last AS (
                SELECT user_id, MAX(event_at) as last_active
                FROM fact_logs
                WHERE user_id IS NOT NULL
                GROUP BY user_id
            )
            SELECT
                du.id as user_id,
                du.full_name,
                du.email,
                COALESCE(du.organization, '') as organization,
                ul.last_active,
                COUNT(DISTINCT fe.course_id) as courses_enrolled
            FROM dim_users du
            LEFT JOIN user_last ul ON du.id = ul.user_id
            LEFT JOIN fact_enrolments fe ON du.id = fe.user_id
            WHERE du.is_active = 1
            GROUP BY du.id, du.full_name, du.email, du.organization, ul.last_active
            HAVING courses_enrolled > 0
        """)

        df["last_active_dt"] = pd.to_datetime(df["last_active"])
        df["days_inactive"] = (max_date - df["last_active_dt"]).dt.days

        def classify(row):
            if pd.isna(row["last_active_dt"]):
                return "never_active"
            elif row["days_inactive"] > 30:
                return "inactive_30d"
            elif row["days_inactive"] > 14:
                return "inactive_14d"
            else:
                return "active"

        df["risk_status"] = df.apply(classify, axis=1)

        counts = df["risk_status"].value_counts().to_dict()

        # Список at-risk для отображения — очищаем NaN для JSON
        at_risk_df = df[df["risk_status"] != "active"].sort_values(
            "days_inactive", ascending=False, na_position="first"
        ).copy()
        at_risk_df["days_inactive"] = at_risk_df["days_inactive"].fillna(-1).astype(int)
        at_risk_df["last_active"] = at_risk_df["last_active"].fillna("")
        at_risk_df = at_risk_df.drop(columns=["last_active_dt"])
        at_risk_df = at_risk_df.where(pd.notna(at_risk_df), None)

        return {
            "total_enrolled": int(len(df)),
            "active": int(counts.get("active", 0)),
            "inactive_14d": int(counts.get("inactive_14d", 0)),
            "inactive_30d": int(counts.get("inactive_30d", 0)),
            "never_active": int(counts.get("never_active", 0)),
            "students_at_risk": at_risk_df.head(50).to_dict("records"),
        }
