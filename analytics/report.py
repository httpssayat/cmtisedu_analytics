"""
Analytics — Main Aggregator
Собирает все метрики в единый JSON-отчёт для дашборда.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from etl.load import Loader
from analytics.core_metrics import CoreMetrics
from analytics.course_analytics import CourseAnalytics
from analytics.cohort_analytics import CohortAnalytics
from analytics.advanced_analytics import QuestionAnalytics, EngagementAnalytics
from analytics.assessment_analytics import AssessmentAnalytics


class AnalyticsReport:
    """Собирает полный отчёт по всем метрикам."""

    def __init__(self, loader: Loader = None):
        self.loader = loader or Loader()
        self.core = CoreMetrics(self.loader)
        self.courses = CourseAnalytics(self.loader)
        self.cohorts = CohortAnalytics(self.loader)
        self.questions = QuestionAnalytics(self.loader)
        self.engagement = EngagementAnalytics(self.loader)
        self.assessments = AssessmentAnalytics(self.loader)

    def generate(self) -> dict:
        print("Генерация аналитического отчёта...")
        report = {}

        steps = [
            ("kpis", self.core.kpis),
            ("funnel", self.core.engagement_funnel),
            ("activity", self.core.activity_over_time),
            ("dau_90d", self.core.dau_90_days),
            ("overall_effectiveness", self.core.overall_effectiveness),
            ("certificates_filter", self.core.certificates_filter_data),
            ("courses", self.courses.overview),
            ("module_mix", self.courses.module_mix),
            ("cohort_retention", self.cohorts.retention_matrix),
            ("cohort_comparison", self.cohorts.cohort_comparison),
            ("weekly_retention", self.cohorts.weekly_retention),
            ("question_difficulty", self.questions.question_difficulty),
            ("difficulty_distribution", self.questions.difficulty_distribution),
            ("problematic_questions", self.questions.problematic_questions),
            ("engagement", self.engagement.user_engagement_scores),
            ("at_risk", self.engagement.at_risk_students),
            ("quiz_overview", self.assessments.quiz_overview),
            ("grade_distribution", self.assessments.grade_distribution),
            ("grades_by_module", self.assessments.grades_by_module_type),
            ("duration_distribution", self.assessments.duration_distribution),
        ]

        for name, fn in steps:
            try:
                report[name] = fn()
                print(f"  ✓ {name}")
            except Exception as e:
                print(f"  ✗ {name}: {e}")
                import traceback
                traceback.print_exc()
                report[name] = None

        return report

    def save_json(self, report: dict, path: Path):
        def default(o):
            if hasattr(o, "item"):
                return o.item()
            if hasattr(o, "isoformat"):
                return o.isoformat()
            return str(o)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=default)
        print(f"Отчёт сохранён: {path}")
