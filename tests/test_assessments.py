from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import UserProfile
from assessments.models import (
    Assessment,
    AssessmentQuestion,
    AssessmentResponse,
    AssessmentResult,
    category_for_score,
)
from assessments.questions_data import QUESTIONS
from assessments.services import (
    build_recommendations,
    compute_scores,
    create_assessment,
    get_active_questions,
)
from universities.models import University

from .utils import login, make_assessment, make_university, make_user, seed_questions


class ScoringTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_questions()

    def test_question_bank_contains_six_dimensions_and_24_questions(self):
        questions = get_active_questions()

        self.assertEqual(len(questions), 24)
        dimensions = {question.dimension for question in questions}
        self.assertEqual(len(dimensions), 6)
        for dimension, items in QUESTIONS.items():
            self.assertEqual(
                sum(1 for question in questions if question.dimension == dimension),
                len(items),
            )

    def test_all_maximum_answers_produce_100_leading(self):
        questions = get_active_questions()
        answers = {question.pk: 4 for question in questions}

        assessment = create_assessment(
            make_university(name="Top University"), None, answers
        )

        self.assertEqual(assessment.overall_score, Decimal("100.00"))
        self.assertEqual(assessment.category, "Leading")
        self.assertEqual(assessment.total_raw_score, 96)
        self.assertEqual(assessment.max_raw_score, 96)
        self.assertEqual(assessment.results.count(), 6)
        self.assertEqual(assessment.responses.count(), 24)

    def test_all_zero_answers_produce_0_initial(self):
        questions = get_active_questions()
        answers = {question.pk: 0 for question in questions}

        assessment = create_assessment(
            make_university(name="Baseline University"), None, answers
        )

        self.assertEqual(assessment.overall_score, Decimal("0.00"))
        self.assertEqual(assessment.category, "Initial")

    def test_mixed_answers_are_normalised_per_dimension(self):
        questions = get_active_questions()
        answers = {question.pk: 2 for question in questions}

        results, total_raw, total_max, overall = compute_scores(questions, answers)

        self.assertEqual(overall, Decimal("50.00"))
        self.assertEqual(total_raw, 48)
        self.assertEqual(total_max, 96)
        for item in results:
            self.assertEqual(item["score"], Decimal("50.00"))

    def test_dimension_scores_use_four_questions_each(self):
        questions = get_active_questions()
        answers = {question.pk: 0 for question in questions}
        infrastructure = [q for q in questions if q.dimension == "infrastructure"]
        for question in infrastructure:
            answers[question.pk] = 4

        results, _, _, overall = compute_scores(questions, answers)
        by_key = {item["dimension"]: item for item in results}

        self.assertEqual(by_key["infrastructure"]["score"], Decimal("100.00"))
        self.assertEqual(by_key["curriculum"]["score"], Decimal("0.00"))
        self.assertEqual(overall, Decimal("16.67"))

    def test_missing_answers_are_rejected(self):
        questions = get_active_questions()
        answers = {question.pk: 3 for question in questions}
        answers.pop(questions[0].pk)

        with self.assertRaises(ValidationError):
            compute_scores(questions, answers)

        with self.assertRaises(ValidationError):
            create_assessment(make_university(name="Missing University"), None, answers)

    def test_out_of_range_answer_is_rejected(self):
        questions = get_active_questions()
        answers = {question.pk: 5 for question in questions}

        with self.assertRaises(ValidationError):
            compute_scores(questions, answers)

    def test_category_boundaries_match_framework(self):
        cases = {
            0: "Initial",
            39.99: "Initial",
            40: "Developing",
            59.99: "Developing",
            60: "Advanced",
            79.99: "Advanced",
            80: "Leading",
            100: "Leading",
        }
        for score, expected in cases.items():
            self.assertEqual(category_for_score(score), expected)

    def test_ordered_results_follow_framework_order(self):
        assessment = make_assessment(make_university(name="Ordered University"))

        dimensions = [result.dimension for result in assessment.ordered_results]

        self.assertEqual(
            dimensions,
            [
                "infrastructure",
                "curriculum",
                "research",
                "faculty",
                "governance",
                "integration",
            ],
        )

    def test_recommendations_target_lowest_scoring_dimensions(self):
        university = make_university(name="Advice University")
        answers = {question.pk: 4 for question in get_active_questions()}
        for question in get_active_questions():
            if question.dimension == "governance":
                answers[question.pk] = 0

        assessment = create_assessment(university, None, answers)
        recommendations = build_recommendations(assessment)

        self.assertEqual(recommendations[0]["dimension"], "governance")
        self.assertEqual(recommendations[0]["category"], "Initial")
        self.assertIn("policy", recommendations[0]["advice"].lower())


class AssessmentFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_questions()

    def setUp(self):
        self.university = make_university(name="Flow University")
        self.rep = make_user(username="flow_rep", university=self.university)
        login(self.client, self.rep)

    def _answers(self, value=4):
        return {
            f"q_{question.pk}": value for question in AssessmentQuestion.objects.all()
        }

    def test_overview_renders_for_approved_representative(self):
        response = self.client.get(reverse("assessments:overview"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["can_assess"])
        self.assertEqual(response.context["question_count"], 24)

    def test_overview_is_read_only_for_pending_university(self):
        pending = make_university(
            name="Pending Flow University", status=University.STATUS_PENDING
        )
        rep = make_user(username="pending_rep", university=pending)
        login(self.client, rep)

        response = self.client.get(reverse("assessments:overview"))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["can_assess"])

    def test_take_page_renders_24_grouped_questions(self):
        response = self.client.get(reverse("assessments:take"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["question_count"], 24)
        self.assertEqual(len(response.context["groups"]), 6)

    def test_valid_submission_creates_assessment_and_redirects(self):
        response = self.client.post(reverse("assessments:take"), self._answers())

        self.assertEqual(Assessment.objects.filter(university=self.university).count(), 1)
        assessment = Assessment.objects.get(university=self.university)
        self.assertRedirects(
            response, reverse("assessments:detail", args=[assessment.pk])
        )
        self.assertEqual(assessment.overall_score, Decimal("100.00"))
        self.assertEqual(assessment.submitted_by, self.rep)
        self.assertEqual(assessment.responses.count(), 24)

    def test_incomplete_submission_is_rejected(self):
        payload = self._answers()
        payload.pop(next(iter(payload)))

        response = self.client.post(reverse("assessments:take"), payload)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Some responses are missing or invalid")
        self.assertFalse(Assessment.objects.filter(university=self.university).exists())

    def test_pending_university_cannot_submit_assessment(self):
        pending = make_university(
            name="Blocked Flow University", status=University.STATUS_PENDING
        )
        rep = make_user(username="blocked_pending_rep", university=pending)
        login(self.client, rep)

        response = self.client.post(reverse("assessments:take"), self._answers())

        self.assertRedirects(response, reverse("dashboard:home"))
        self.assertFalse(Assessment.objects.filter(university=pending).exists())

    def test_representative_without_university_is_redirected_to_registration(self):
        rep = make_user(username="no_university_rep")
        login(self.client, rep)

        response = self.client.get(reverse("assessments:take"))

        self.assertRedirects(response, reverse("universities:create"))

    def test_administrator_is_redirected_to_admin_dashboard(self):
        admin = make_user(username="flow_admin", role=UserProfile.ROLE_ADMIN)
        login(self.client, admin)

        response = self.client.get(reverse("assessments:overview"))

        self.assertRedirects(response, reverse("dashboard:admin_home"))

    def test_detail_is_restricted_to_owning_university(self):
        assessment = make_assessment(self.university)
        other = make_university(name="Other Flow University")
        other_rep = make_user(username="other_flow_rep", university=other)
        login(self.client, other_rep)

        response = self.client.get(reverse("assessments:detail", args=[assessment.pk]))

        self.assertEqual(response.status_code, 404)

    def test_administrator_can_open_any_assessment(self):
        assessment = make_assessment(self.university)
        admin = make_user(username="detail_flow_admin", role=UserProfile.ROLE_ADMIN)
        login(self.client, admin)

        response = self.client.get(reverse("assessments:detail", args=[assessment.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_admin_view"])

    def test_detail_calculates_delta_against_previous_assessment(self):
        first = make_assessment(self.university, value=2)
        second = make_assessment(self.university, value=4)

        response = self.client.get(reverse("assessments:detail", args=[second.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context["delta"])
        self.assertEqual(response.context["previous"], first)
        self.assertAlmostEqual(response.context["delta"], 50.0)

    def test_history_lists_assessments(self):
        make_assessment(self.university)

        response = self.client.get(reverse("assessments:history"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total"], 1)

    def test_management_page_requires_administrator(self):
        response = self.client.get(reverse("assessments:manage"))

        self.assertEqual(response.status_code, 403)

    def test_administrator_can_filter_and_delete_assessments(self):
        assessment = make_assessment(self.university)
        admin = make_user(username="manage_admin", role=UserProfile.ROLE_ADMIN)
        login(self.client, admin)

        response = self.client.get(reverse("assessments:manage"), {"category": "Leading"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total"], 1)

        response = self.client.post(
            reverse("assessments:delete", args=[assessment.pk])
        )
        self.assertRedirects(response, reverse("assessments:manage"))
        self.assertFalse(Assessment.objects.filter(pk=assessment.pk).exists())
        self.assertEqual(AssessmentResponse.objects.count(), 0)
        self.assertEqual(AssessmentResult.objects.count(), 0)
