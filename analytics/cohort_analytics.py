"""
Analytics — Cohort Analysis
Когортный анализ: группировка пользователей по месяцу первой активности,
retention curve, сравнение поведения когорт.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
from etl.load import Loader


class CohortAnalytics:
    """Когорты: 'Когда ты пришёл' определяет 'Как ты себя ведёшь'."""

    def __init__(self, loader: Loader = None):
        self.loader = loader or Loader()

    def _get_user_first_activity(self) -> pd.DataFrame:
        """Первая активность каждого пользователя в логах."""
        return self.loader.query("""
            SELECT user_id, MIN(event_at) as first_active
            FROM fact_logs
            WHERE user_id IS NOT NULL AND user_id NOT IN (2,227,229,355,359,377)
            GROUP BY user_id
        """)

    def retention_matrix(self) -> dict:
        """
        Матрица retention: по оси X — месяц после когорты (0, 1, 2...),
        по оси Y — когорта (месяц первой активности).
        Значение — % пользователей когорты, активных в этом месяце.
        """
        first_active = self._get_user_first_activity()
        first_active["first_active"] = pd.to_datetime(first_active["first_active"])
        first_active["cohort"] = first_active["first_active"].dt.to_period("M")

        # Все события каждого пользователя по месяцам
        all_activity = self.loader.query("""
            SELECT user_id, substr(event_at, 1, 7) as month
            FROM fact_logs
            WHERE user_id IS NOT NULL AND user_id NOT IN (2,227,229,355,359,377) AND event_at IS NOT NULL
            GROUP BY user_id, month
        """)
        all_activity["month"] = pd.to_datetime(all_activity["month"], format="%Y-%m").dt.to_period("M")

        # Джойн
        merged = all_activity.merge(
            first_active[["user_id", "cohort"]], on="user_id", how="left"
        )
        merged = merged.dropna(subset=["cohort"])
        merged["months_since"] = (merged["month"] - merged["cohort"]).apply(
            lambda x: x.n if pd.notna(x) else None
        )
        merged = merged[merged["months_since"] >= 0]

        # Размер когорт
        cohort_sizes = first_active.groupby("cohort")["user_id"].nunique()

        # Активность по когорте и месяцу-после
        retention_counts = (
            merged.groupby(["cohort", "months_since"])["user_id"]
            .nunique()
            .reset_index()
        )

        retention_counts["cohort_size"] = retention_counts["cohort"].map(cohort_sizes)
        retention_counts["retention_pct"] = (
            retention_counts["user_id"] / retention_counts["cohort_size"] * 100
        ).round(1)

        # Пивот в матрицу
        pivot_pct = retention_counts.pivot(
            index="cohort", columns="months_since", values="retention_pct"
        ).fillna(0)

        pivot_users = retention_counts.pivot(
            index="cohort", columns="months_since", values="user_id"
        ).fillna(0).astype(int)

        # Конвертация в JSON-сериализуемый формат
        cohorts = [str(c) for c in pivot_pct.index]
        max_periods = int(pivot_pct.columns.max()) + 1 if len(pivot_pct.columns) else 0

        matrix = []
        for cohort in pivot_pct.index:
            row = {"cohort": str(cohort), "size": int(cohort_sizes.get(cohort, 0)), "values": []}
            for m in range(max_periods):
                if m in pivot_pct.columns:
                    pct = float(pivot_pct.loc[cohort, m])
                    users = int(pivot_users.loc[cohort, m])
                    row["values"].append({"month": m, "retention": pct, "users": users})
                else:
                    row["values"].append({"month": m, "retention": 0, "users": 0})
            matrix.append(row)

        return {
            "cohorts": cohorts,
            "max_periods": max_periods,
            "matrix": matrix,
        }

    def cohort_comparison(self) -> list:
        """Сравнение когорт по ключевым метрикам."""
        first_active = self._get_user_first_activity()
        first_active["first_active"] = pd.to_datetime(first_active["first_active"])
        first_active["cohort"] = first_active["first_active"].dt.to_period("M").astype(str)

        # Оценки по пользователю
        user_grades = self.loader.query("""
            SELECT user_id, AVG(grade_percent) as avg_grade
            FROM fact_grades
            WHERE grade_percent IS NOT NULL
            GROUP BY user_id
        """)

        # Завершения по пользователю
        user_completions = self.loader.query("""
            SELECT user_id,
                   SUM(is_completed) as completions,
                   COUNT(*) as activities
            FROM fact_completions
            GROUP BY user_id
        """)

        # События по пользователю
        user_events = self.loader.query("""
            SELECT user_id, COUNT(*) as events
            FROM fact_logs
            WHERE user_id IS NOT NULL AND user_id NOT IN (2,227,229,355,359,377)
            GROUP BY user_id
        """)

        merged = first_active.merge(user_grades, on="user_id", how="left") \
                             .merge(user_completions, on="user_id", how="left") \
                             .merge(user_events, on="user_id", how="left")

        grouped = merged.groupby("cohort").agg(
            users=("user_id", "nunique"),
            avg_grade=("avg_grade", "mean"),
            avg_completions=("completions", "mean"),
            avg_events=("events", "mean"),
            completion_ratio=("completions",
                              lambda x: (x / merged.loc[x.index, "activities"].replace(0, np.nan)).mean() * 100),
        ).reset_index()

        grouped = grouped.round(1).fillna(0)
        grouped = grouped.sort_values("cohort")

        return grouped.to_dict("records")

    def weekly_retention(self) -> list:
        """
        Простой недельный retention: % пользователей, вернувшихся через N недель
        после первой активности.
        """
        first = self.loader.query("""
            SELECT user_id, MIN(event_at) as first_active
            FROM fact_logs
            WHERE user_id IS NOT NULL AND user_id NOT IN (2,227,229,355,359,377)
            GROUP BY user_id
        """)
        first["first_active"] = pd.to_datetime(first["first_active"])
        first["first_week"] = first["first_active"].dt.isocalendar().week + first["first_active"].dt.year * 100

        all_act = self.loader.query("""
            SELECT user_id, event_at FROM fact_logs
            WHERE user_id IS NOT NULL AND user_id NOT IN (2,227,229,355,359,377) AND event_at IS NOT NULL
        """)
        all_act["event_at"] = pd.to_datetime(all_act["event_at"])

        merged = all_act.merge(first[["user_id", "first_active"]], on="user_id")
        merged["weeks_since"] = ((merged["event_at"] - merged["first_active"]).dt.days // 7).astype(int)
        merged = merged[merged["weeks_since"] >= 0]

        total = first["user_id"].nunique()
        result = []
        for w in range(0, 13):
            active = merged[merged["weeks_since"] == w]["user_id"].nunique()
            pct = round(active / total * 100, 1) if total else 0
            result.append({"week": w, "retention": pct, "users": int(active)})
        return result
