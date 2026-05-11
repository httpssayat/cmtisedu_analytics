"""
Analytics — Quizzes & Grades
Детальная аналитика тестов и распределения оценок.
"""

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from etl.load import Loader


class AssessmentAnalytics:

    def __init__(self, loader: Loader = None):
        self.loader = loader or Loader()

    def quiz_overview(self) -> dict:
        stats = self.loader.query("""
            SELECT
                COUNT(*) as total_attempts,
                SUM(is_finished) as finished,
                SUM(CASE WHEN state='inprogress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN state='abandoned' THEN 1 ELSE 0 END) as abandoned,
                ROUND(AVG(CASE WHEN is_finished=1 THEN duration_min END), 1) as avg_duration
            FROM fact_quiz_attempts
        """).iloc[0]

        per_quiz = self.loader.query("""
            SELECT
                quiz_id,
                COALESCE(quiz_name, 'Quiz ' || quiz_id) as quiz_name,
                COUNT(*) as attempts,
                COUNT(DISTINCT user_id) as unique_users,
                SUM(is_finished) as finished,
                ROUND(AVG(CASE WHEN is_finished=1 THEN duration_min END), 1) as avg_duration,
                ROUND(AVG(sumgrades), 1) as avg_score
            FROM fact_quiz_attempts
            WHERE quiz_id IS NOT NULL
            GROUP BY quiz_id, quiz_name
            ORDER BY attempts DESC
        """)

        return {
            "summary": {
                "total": int(stats["total_attempts"]),
                "finished": int(stats["finished"] or 0),
                "in_progress": int(stats["in_progress"] or 0),
                "abandoned": int(stats["abandoned"] or 0),
                "avg_duration_min": float(stats["avg_duration"] or 0),
            },
            "per_quiz": per_quiz.to_dict("records"),
        }

    def grade_distribution(self) -> dict:
        df = self.loader.query("""
            SELECT grade_percent
            FROM fact_grades
            WHERE grade_percent IS NOT NULL
        """)
        if df.empty:
            return {}

        bins = list(range(0, 101, 10))
        labels = [f"{b}-{b+10}" for b in bins[:-1]]
        df["bin"] = pd.cut(df["grade_percent"], bins=bins, labels=labels, include_lowest=True)
        counts = df["bin"].value_counts().reindex(labels, fill_value=0)

        return {
            "bins": labels,
            "counts": [int(x) for x in counts.values],
            "mean": round(float(df["grade_percent"].mean()), 1),
            "median": round(float(df["grade_percent"].median()), 1),
            "std": round(float(df["grade_percent"].std()), 1),
            "total_grades": len(df),
        }

    def grades_by_module_type(self) -> list:
        df = self.loader.query("""
            SELECT
                itemmodule as module_type,
                COUNT(*) as n,
                ROUND(AVG(grade_percent), 1) as avg_grade,
                ROUND(
                    AVG(CASE WHEN grade_percent >= 70 THEN 1.0 ELSE 0.0 END) * 100, 1
                ) as pass_rate
            FROM fact_grades
            WHERE grade_percent IS NOT NULL AND itemmodule IS NOT NULL
            GROUP BY itemmodule
            ORDER BY n DESC
        """)
        return df.to_dict("records")

    def duration_distribution(self) -> dict:
        df = self.loader.query("""
            SELECT duration_min
            FROM fact_quiz_attempts
            WHERE is_finished=1 AND duration_min IS NOT NULL
        """)
        if df.empty:
            return {}

        bins = [0, 1, 3, 5, 10, 20, 30, 60, 120, 300]
        labels = ["<1м", "1-3м", "3-5м", "5-10м", "10-20м", "20-30м", "30-60м", "1-2ч", "2-5ч"]
        df["bin"] = pd.cut(df["duration_min"], bins=bins, labels=labels, include_lowest=True)
        counts = df["bin"].value_counts().reindex(labels, fill_value=0)

        return {
            "bins": labels,
            "counts": [int(x) for x in counts.values],
            "avg": round(float(df["duration_min"].mean()), 1),
            "median": round(float(df["duration_min"].median()), 1),
        }
