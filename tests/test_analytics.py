from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from analytics.services import (
    category_distribution,
    comparison_data,
    consortium_statistics,
    latest_universities,
    monthly_assessments,
    public_statistics,
)
from assessments.models import Assessment
from universities.models import University

from .utils import (
    login,
    make_assessment,
    make_university,
    make_user,
    seed_questions,
)


class AnalyticsServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_questions()
        cls.u1 = make_university(name="Alpha University", country="Bangladesh", city="Dhaka")
        cls.u2 = make_university(name="Beta University", country="India", city="Delhi")
        cls.u3 = make_university(
            name="Gamma University",
            country="Bangladesh",
            status=University.STATUS_PENDING,
        )

        cls.a1_old = make_assessment(cls.u1, value=1)
        cls.a1_new = make_assessment(cls.u1, value=3)
        cls.a2 = make_assessment(cls.u2, value=4)
        Assessment.objects.filter(pk=cls.a1_old.pk).update(
            created_at=timezone.now() - timedelta(days=40)
        )
        Assessment.objects.filter(pk=cls.a2.pk).update(
            created_at=timezone.now() - timedelta(days=70)
        )

    def test_latest_universities_only_includes_approved(self):
        names = [u.name for u in latest_universities()]

        self.assertEqual(names, ["Alpha University", "Beta University"])

    def test_latest_universities_uses_most_recent_assessment(self):
        universities = {u.name: u for u in latest_universities()}

        self.assertEqual(float(universities["Alpha University"].latest_result_score), 75.0)
        self.assertEqual(universities["Alpha University"].latest_result_category, "Advanced")
        self.assertEqual(universities["Alpha University"].assessment_count, 2)

    def test_consortium_statistics_use_latest_scores(self):
        stats = consortium_statistics()

        self.assertEqual(stats["total_universities"], 2)
        self.assertEqual(stats["assessed_universities"], 2)
        self.assertEqual(stats["total_assessments"], 3)
        self.assertEqual(stats["average_score"], 87.5)
        self.assertEqual(stats["average_category"], "Leading")
        self.assertEqual(stats["countries"], 2)

    def test_dimensions_are_in_canonical_order(self):
        stats = consortium_statistics()

        self.assertEqual(
            [item["key"] for item in stats["dimensions"]],
            [
                "infrastructure",
                "curriculum",
                "research",
                "faculty",
                "governance",
                "integration",
            ],
        )
        self.assertEqual(stats["dimensions"][0]["average"], 87.5)

    def test_category_distribution_counts_latest_categories(self):
        stats = consortium_statistics()
        distribution = {item["label"]: item["count"] for item in stats["categories"]}

        self.assertEqual(distribution["Advanced"], 1)
        self.assertEqual(distribution["Leading"], 1)
        self.assertEqual(distribution["Initial"], 0)
        self.assertEqual(distribution["Developing"], 0)

    def test_country_statistics_group_assessed_universities(self):
        stats = consortium_statistics()
        by_country = {row["country"]: row for row in stats["by_country"]}

        self.assertEqual(by_country["Bangladesh"]["count"], 1)
        self.assertEqual(by_country["Bangladesh"]["average"], 75.0)
        self.assertEqual(by_country["India"]["average"], 100.0)

    def test_monthly_assessments_returns_six_buckets(self):
        rows = monthly_assessments()

        self.assertEqual(len(rows), 6)
        # Two Alpha assessments plus Beta's assessment fall inside the window.
        self.assertEqual(sum(row["count"] for row in rows), 3)
        self.assertEqual(rows[-1]["count"], 1)
        self.assertEqual(
            rows[-1]["label"], timezone.now().strftime("%b %Y")
        )

    def test_public_statistics_computes_coverage(self):
        stats = public_statistics()

        self.assertEqual(stats["university_count"], 2)
        self.assertEqual(stats["country_count"], 2)
        self.assertEqual(stats["assessment_count"], 3)
        self.assertEqual(stats["average_score"], 87.5)
        self.assertEqual(stats["assessment_coverage"], 100)
        self.assertEqual(stats["dimensions"][0]["average"], 87.5)
        self.assertEqual(stats["dimensions"][0]["count"], 2)

    def test_comparison_data_returns_dimension_scores(self):
        universities = list(latest_universities())
        rows = comparison_data(universities)

        self.assertEqual(len(rows), 2)
        alpha = next(row for row in rows if row["university"].name == "Alpha University")
        self.assertEqual(alpha["overall"], 75.0)
        self.assertEqual(len(alpha["dimensions"]), 6)
        self.assertEqual(alpha["dimensions"][0]["key"], "infrastructure")

    def test_comparison_data_skips_unassessed_universities(self):
        empty = make_university(name="Empty University")
        rows = comparison_data([empty])

        self.assertEqual(rows, [])

    def test_category_distribution_handles_empty_input(self):
        distribution = category_distribution([])

        self.assertEqual(sum(item["count"] for item in distribution), 0)
        self.assertTrue(all(item["percentage"] == 0 for item in distribution))


class AnalyticsViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_questions()
        cls.university = make_university(name="View University")
        make_assessment(cls.university, value=3)
        cls.rep = make_user(username="analytics_rep", university=cls.university)

    def test_analytics_dashboard_requires_login(self):
        response = self.client.get(reverse("analytics:dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response["Location"])

    def test_analytics_dashboard_renders_for_logged_in_user(self):
        login(self.client, self.rep)

        response = self.client.get(reverse("analytics:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["stats"]["total_universities"], 1)

    def test_comparison_page_renders_selected_universities(self):
        login(self.client, self.rep)

        response = self.client.get(
            reverse("analytics:comparison"), {"u": [self.university.pk]}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["rows"]), 1)
        self.assertEqual(response.context["selected_ids"], [self.university.pk])
        self.assertEqual(len(response.context["chart"]["overall"]), 1)

    def test_comparison_limits_selection_to_five(self):
        login(self.client, self.rep)

        response = self.client.get(
            reverse("analytics:comparison"),
            {"u": [str(self.university.pk)] * 6},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["too_many"])

    def test_public_summary_api_returns_json(self):
        response = self.client.get(reverse("analytics:summary_api"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["approved_universities"], 1)
        self.assertEqual(payload["completed_assessments"], 1)
        self.assertEqual(payload["average_readiness"], 75.0)
