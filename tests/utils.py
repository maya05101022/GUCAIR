"""Shared helpers for the GUCAIR automated test suite."""

from django.contrib.auth.models import User

from accounts.models import UserProfile
from assessments.models import AssessmentQuestion
from assessments.questions_data import QUESTIONS
from assessments.services import create_assessment
from universities.models import University


def seed_questions():
    for dimension, items in QUESTIONS.items():
        for index, (text, guidance) in enumerate(items, start=1):
            AssessmentQuestion.objects.update_or_create(
                dimension=dimension,
                order=index,
                defaults={"text": text, "guidance": guidance, "is_active": True},
            )


def make_user(username="rep", role="representative", university=None, password="TestPass!234"):
    user = User.objects.create_user(
        username=username,
        email=f"{username}@example.edu",
        password=password,
        first_name=username.title(),
        last_name="Tester",
    )
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.role = role
    profile.university = university
    if role == UserProfile.ROLE_ADMIN:
        profile.role = UserProfile.ROLE_ADMIN
        user.is_staff = True
        user.is_superuser = True
        user.save(update_fields=["is_staff", "is_superuser"])
    profile.save()
    return user


def make_university(name="Test University", status=University.STATUS_APPROVED, country="Bangladesh", city="Dhaka", **kwargs):
    university = University.objects.create(
        name=name,
        country=country,
        city=city,
        description=kwargs.pop(
            "description",
            "A test university institutional profile used for automated verification of GUCAIR features.",
        ),
        status=status,
        **kwargs,
    )
    if status == University.STATUS_APPROVED and not university.approved_at:
        from django.utils import timezone

        university.approved_at = timezone.now()
        university.save(update_fields=["approved_at"])
    return university


def make_assessment(university, value=4, submitted_by=None):
    answers = {question.pk: value for question in AssessmentQuestion.objects.all()}
    return create_assessment(university, submitted_by, answers)


def login(client, user, password="TestPass!234"):
    return client.login(username=user.username, password=password)
