from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Resource(models.Model):
    CATEGORY_LEARNING = "learning"
    CATEGORY_IMPLEMENTATION = "implementation"
    CATEGORY_RESPONSIBLE = "responsible"
    CATEGORY_GOVERNANCE = "governance"
    CATEGORY_RESEARCH = "research"
    CATEGORY_INTEGRATION = "integration"
    CATEGORY_CHOICES = [
        (CATEGORY_LEARNING, "AI Learning"),
        (CATEGORY_IMPLEMENTATION, "Implementation Guidelines"),
        (CATEGORY_RESPONSIBLE, "Responsible AI"),
        (CATEGORY_GOVERNANCE, "AI Governance"),
        (CATEGORY_RESEARCH, "AI Research"),
        (CATEGORY_INTEGRATION, "University Integration"),
    ]

    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, unique=True, blank=True)
    category = models.CharField(
        max_length=30, choices=CATEGORY_CHOICES, db_index=True
    )
    summary = models.CharField(
        max_length=400, help_text="One or two sentences shown in resource listings."
    )
    content = models.TextField(
        help_text="Plain text or light HTML. Paragraph breaks are preserved."
    )
    external_link = models.URLField(
        max_length=400,
        blank=True,
        help_text="Optional external source or reference (not an endorsement).",
    )
    is_published = models.BooleanField(default=True, db_index=True)
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_resources",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or "resource"
            slug = base
            counter = 2
            while Resource.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("resources:detail", kwargs={"slug": self.slug})
