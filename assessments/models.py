from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse


DIMENSIONS = [
    (
        "infrastructure",
        "AI Infrastructure",
        "Compute, data platforms, connectivity and technical foundations.",
    ),
    (
        "curriculum",
        "AI Education and Curriculum",
        "AI teaching, programmes, learning outcomes and student preparedness.",
    ),
    (
        "research",
        "Research and Innovation",
        "AI research capacity, funding, partnerships and knowledge transfer.",
    ),
    (
        "faculty",
        "Faculty AI Skills",
        "Staff capability, professional development and academic support.",
    ),
    (
        "governance",
        "AI Governance and Ethics",
        "Policy, ethics, data protection and accountable AI use.",
    ),
    (
        "integration",
        "AI Integration and Adoption",
        "Institution-wide adoption of AI in operations and services.",
    ),
]

DIMENSION_KEYS = [key for key, _, _ in DIMENSIONS]
DIMENSION_LABELS = {key: label for key, label, _ in DIMENSIONS}
DIMENSION_DESCRIPTIONS = {key: description for key, _, description in DIMENSIONS}
DIMENSION_ORDER = {key: index for index, key in enumerate(DIMENSION_KEYS)}

SCORE_CATEGORIES = [
    (0, 39, "Initial"),
    (40, 59, "Developing"),
    (60, 79, "Advanced"),
    (80, 100, "Leading"),
]


def category_for_score(score) -> str:
    """Return the readiness category for a 0-100 score."""
    score = float(score)
    if score < 40:
        return "Initial"
    if score < 60:
        return "Developing"
    if score < 80:
        return "Advanced"
    return "Leading"


class AssessmentQuestion(models.Model):
    dimension = models.CharField(max_length=40, choices=[(k, v) for k, v, _ in DIMENSIONS])
    text = models.CharField(max_length=400)
    guidance = models.CharField(
        max_length=400,
        blank=True,
        help_text="Explanatory text to help respondents choose a maturity level.",
    )
    order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["dimension", "order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["dimension", "order"], name="unique_question_order_per_dimension"
            )
        ]

    def __str__(self) -> str:
        return f"[{self.get_dimension_display()}] {self.text}"

    @property
    def dimension_index(self) -> int:
        return DIMENSION_ORDER.get(self.dimension, 99)


class Assessment(models.Model):
    university = models.ForeignKey(
        "universities.University",
        on_delete=models.CASCADE,
        related_name="assessments",
    )
    submitted_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_assessments",
    )
    overall_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
    )
    category = models.CharField(max_length=20)
    total_raw_score = models.PositiveSmallIntegerField()
    max_raw_score = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        get_latest_by = "created_at"

    def __str__(self) -> str:
        return f"{self.university.name} — {self.overall_score}% ({self.category})"

    def get_absolute_url(self) -> str:
        return reverse("assessments:detail", kwargs={"pk": self.pk})

    @property
    def score_display(self) -> str:
        return f"{float(self.overall_score):.1f}"

    def dimension_result(self, dimension: str):
        return self.results.filter(dimension=dimension).first()

    @property
    def ordered_results(self):
        """Results in canonical framework order rather than alphabetical."""
        return sorted(
            self.results.all(),
            key=lambda result: DIMENSION_ORDER.get(result.dimension, 99),
        )

    @property
    def is_latest(self) -> bool:
        latest = (
            Assessment.objects.filter(university=self.university)
            .order_by("-created_at")
            .values_list("pk", flat=True)
            .first()
        )
        return latest == self.pk


class AssessmentResponse(models.Model):
    assessment = models.ForeignKey(
        Assessment, on_delete=models.CASCADE, related_name="responses"
    )
    question = models.ForeignKey(
        AssessmentQuestion, on_delete=models.PROTECT, related_name="responses"
    )
    score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)]
    )

    class Meta:
        ordering = ["question__dimension", "question__order"]
        constraints = [
            models.UniqueConstraint(
                fields=["assessment", "question"], name="unique_response_per_question"
            )
        ]

    def __str__(self) -> str:
        return f"{self.question_id}: {self.score}"


class AssessmentResult(models.Model):
    assessment = models.ForeignKey(
        Assessment, on_delete=models.CASCADE, related_name="results"
    )
    dimension = models.CharField(max_length=40)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    raw_score = models.PositiveSmallIntegerField()
    max_score = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["dimension"]
        constraints = [
            models.UniqueConstraint(
                fields=["assessment", "dimension"], name="unique_result_per_dimension"
            )
        ]

    def __str__(self) -> str:
        return f"{self.get_dimension_display()}: {self.score}%"

    def get_dimension_display(self) -> str:
        return DIMENSION_LABELS.get(self.dimension, self.dimension.title())

    @property
    def score_value(self) -> float:
        return float(self.score)

    @property
    def category(self) -> str:
        return category_for_score(self.score)
