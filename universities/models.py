from django.db import models
from django.db.models import Avg
from django.urls import reverse
from django.utils.text import slugify


COUNTRIES = [
    "Afghanistan", "Albania", "Algeria", "Argentina", "Armenia", "Australia",
    "Austria", "Azerbaijan", "Bahrain", "Bangladesh", "Belgium", "Bhutan",
    "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei",
    "Bulgaria", "Cambodia", "Cameroon", "Canada", "Chile", "China", "Colombia",
    "Costa Rica", "Croatia", "Cyprus", "Czechia", "Denmark", "Ecuador",
    "Egypt", "Estonia", "Ethiopia", "Finland", "France", "Georgia", "Germany",
    "Ghana", "Greece", "Hungary", "Iceland", "India", "Indonesia", "Iran",
    "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan",
    "Kazakhstan", "Kenya", "Kuwait", "Kyrgyzstan", "Laos", "Latvia",
    "Lebanon", "Libya", "Lithuania", "Luxembourg", "Malaysia", "Maldives",
    "Malta", "Mexico", "Moldova", "Mongolia", "Montenegro", "Morocco",
    "Myanmar", "Nepal", "Netherlands", "New Zealand", "Nigeria",
    "North Macedonia", "Norway", "Oman", "Pakistan", "Palestine", "Panama",
    "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Rwanda",
    "Saudi Arabia", "Senegal", "Serbia", "Singapore", "Slovakia", "Slovenia",
    "South Africa", "South Korea", "Spain", "Sri Lanka", "Sudan", "Sweden",
    "Switzerland", "Syria", "Taiwan", "Tajikistan", "Tanzania", "Thailand",
    "Tunisia", "Turkey", "Turkmenistan", "Uganda", "Ukraine",
    "United Arab Emirates", "United Kingdom", "United States", "Uruguay",
    "Uzbekistan", "Vietnam", "Yemen", "Zambia", "Zimbabwe",
]


class UniversityQuerySet(models.QuerySet):
    def approved(self):
        return self.filter(status=University.STATUS_APPROVED)

    def pending(self):
        return self.filter(status=University.STATUS_PENDING)

    def with_latest_score(self):
        return self.annotate(
            avg_score=Avg("assessments__overall_score"),
        )


class University(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending review"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    country = models.CharField(max_length=100, db_index=True)
    city = models.CharField(max_length=120)
    website = models.URLField(max_length=300, blank=True)
    description = models.TextField(
        help_text="Institutional profile, focus areas and AI readiness context."
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True
    )
    review_note = models.CharField(
        max_length=400,
        blank=True,
        help_text="Optional note shown to the representative after review.",
    )
    is_demo = models.BooleanField(
        default=False,
        help_text="Marks clearly-labelled demonstration records seeded for evaluation.",
    )
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_universities",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    objects = UniversityQuerySet.as_manager()

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Universities"
        indexes = [
            models.Index(fields=["status", "country"]),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)[:200] or "university"
            slug = base
            counter = 2
            while University.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("universities:detail", kwargs={"slug": self.slug})

    @property
    def is_approved(self) -> bool:
        return self.status == self.STATUS_APPROVED

    @property
    def latest_assessment(self):
        return self.assessments.order_by("-created_at").first()

    @property
    def latest_score(self):
        assessment = self.latest_assessment
        return float(assessment.overall_score) if assessment else None

    @property
    def readiness_category(self):
        assessment = self.latest_assessment
        return assessment.category if assessment else None
