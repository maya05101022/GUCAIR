from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import UserProfile
from universities.models import University

from .utils import login, make_university, make_user


class PublicUniversityTests(TestCase):
    def setUp(self):
        self.approved = make_university(name="Approved University", country="Bangladesh")
        self.pending = make_university(
            name="Pending University",
            status=University.STATUS_PENDING,
            city="Chattogram",
        )

    def test_list_only_shows_approved_universities(self):
        response = self.client.get(reverse("universities:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Approved University")
        self.assertNotContains(response, "Pending University")

    def test_list_search_matches_name_or_city(self):
        response = self.client.get(reverse("universities:list"), {"q": "Chattogram"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["universities"]), [])

        response = self.client.get(reverse("universities:list"), {"q": "Approved"})
        self.assertEqual(list(response.context["universities"]), [self.approved])

    def test_list_filters_by_country(self):
        response = self.client.get(
            reverse("universities:list"), {"country": "Bangladesh"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Approved University")

    def test_approved_university_detail_is_public(self):
        response = self.client.get(
            reverse("universities:detail", args=[self.approved.slug])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["university"], self.approved)
        self.assertFalse(response.context["can_view_scores"])

    def test_pending_university_detail_is_hidden_from_anonymous_users(self):
        response = self.client.get(
            reverse("universities:detail", args=[self.pending.slug])
        )

        self.assertEqual(response.status_code, 404)

    def test_owner_can_view_own_pending_university(self):
        rep = make_user(username="owner_rep", university=self.pending)
        login(self.client, rep)

        response = self.client.get(
            reverse("universities:detail", args=[self.pending.slug])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_owner"])

    def test_administrator_can_view_pending_university(self):
        admin = make_user(username="detail_admin", role=UserProfile.ROLE_ADMIN)
        login(self.client, admin)

        response = self.client.get(
            reverse("universities:detail", args=[self.pending.slug])
        )

        self.assertEqual(response.status_code, 200)

    def test_other_representative_cannot_view_pending_university(self):
        make_university(name="Other University")
        rep = make_user(username="outside_rep", university=make_university(name="Outside University"))
        login(self.client, rep)

        response = self.client.get(
            reverse("universities:detail", args=[self.pending.slug])
        )

        self.assertEqual(response.status_code, 404)


class RepresentativeUniversityTests(TestCase):
    def setUp(self):
        self.rep = make_user(username="university_rep")
        login(self.client, self.rep)

    def test_representative_can_register_university_profile(self):
        response = self.client.post(
            reverse("universities:create"),
            {
                "name": "New Horizon University",
                "country": "Bangladesh",
                "city": "Sylhet",
                "website": "newhorizon.example.edu",
                "description": (
                    "New Horizon University is building interdisciplinary AI teaching, "
                    "research capacity and governance structures across its faculties."
                ),
            },
        )

        self.assertRedirects(response, reverse("dashboard:home"))
        university = University.objects.get(name="New Horizon University")
        self.assertEqual(university.status, University.STATUS_PENDING)
        self.assertEqual(university.created_by, self.rep)
        self.assertEqual(university.website, "https://newhorizon.example.edu")
        self.rep.profile.refresh_from_db()
        self.assertEqual(self.rep.profile.university, university)

    def test_representative_with_university_is_sent_to_edit(self):
        university = make_university(name="Linked University")
        self.rep.profile.university = university
        self.rep.profile.save(update_fields=["university"])

        response = self.client.get(reverse("universities:create"))

        self.assertRedirects(response, reverse("universities:edit"))

    def test_representative_can_update_own_university(self):
        university = make_university(name="Editable University")
        self.rep.profile.university = university
        self.rep.profile.save(update_fields=["university"])

        response = self.client.post(
            reverse("universities:edit"),
            {
                "name": "Renamed University",
                "country": "Bangladesh",
                "city": "Khulna",
                "website": "",
                "description": (
                    "Renamed University has refreshed its institutional profile to "
                    "describe AI teaching, research and governance priorities."
                ),
            },
        )

        self.assertRedirects(response, reverse("dashboard:home"))
        university.refresh_from_db()
        self.assertEqual(university.name, "Renamed University")
        self.assertEqual(university.city, "Khulna")

    def test_duplicate_university_name_is_rejected(self):
        make_university(name="Taken University")

        response = self.client.post(
            reverse("universities:create"),
            {
                "name": "Taken University",
                "country": "Bangladesh",
                "city": "Dhaka",
                "website": "",
                "description": (
                    "A duplicate institutional profile that should be rejected by the "
                    "server-side uniqueness validation on the university name field."
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("name", response.context["form"].errors)
        self.assertEqual(University.objects.filter(name="Taken University").count(), 1)

    def test_administrator_is_redirected_to_management(self):
        admin = make_user(username="create_admin", role=UserProfile.ROLE_ADMIN)
        login(self.client, admin)

        response = self.client.get(reverse("universities:create"))

        self.assertRedirects(response, reverse("universities:manage"))


class AdminUniversityManagementTests(TestCase):
    def setUp(self):
        self.admin = make_user(username="uni_admin", role=UserProfile.ROLE_ADMIN)
        self.pending = make_university(
            name="Review University",
            status=University.STATUS_PENDING,
            country="Nepal",
        )
        login(self.client, self.admin)

    def test_management_page_requires_admin(self):
        self.client.logout()
        rep = make_user(username="blocked_rep")
        login(self.client, rep)

        response = self.client.get(reverse("universities:manage"))

        self.assertEqual(response.status_code, 403)

    def test_management_page_lists_pending_universities(self):
        response = self.client.get(reverse("universities:manage"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Review University")
        self.assertEqual(response.context["pending_count"], 1)

    def test_management_status_filter(self):
        make_university(name="Approved University")

        response = self.client.get(
            reverse("universities:manage"), {"status": University.STATUS_APPROVED}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Approved University")
        self.assertNotContains(response, "Review University")

    def test_approve_university_sets_status_and_timestamp(self):
        response = self.client.post(
            reverse("universities:approve", args=[self.pending.pk]),
            {"review_note": "Meets consortium criteria."},
        )

        self.assertRedirects(response, reverse("universities:manage"))
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, University.STATUS_APPROVED)
        self.assertIsNotNone(self.pending.approved_at)
        self.assertEqual(self.pending.review_note, "Meets consortium criteria.")

    def test_reject_university_records_note(self):
        response = self.client.post(
            reverse("universities:reject", args=[self.pending.pk]),
            {"review_note": "Insufficient institutional detail."},
        )

        self.assertRedirects(response, reverse("universities:manage"))
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, University.STATUS_REJECTED)
        self.assertIsNone(self.pending.approved_at)
        self.assertEqual(self.pending.review_note, "Insufficient institutional detail.")

    def test_reject_uses_default_note_when_blank(self):
        self.client.post(reverse("universities:reject", args=[self.pending.pk]), {})

        self.pending.refresh_from_db()
        self.assertTrue(self.pending.review_note)

    def test_delete_requires_exact_name_confirmation(self):
        response = self.client.post(
            reverse("universities:delete", args=[self.pending.pk]),
            {"confirm_name": "wrong name"},
        )

        self.assertRedirects(response, reverse("universities:manage"))
        self.assertTrue(University.objects.filter(pk=self.pending.pk).exists())

    def test_delete_removes_university_and_assessments(self):
        from .utils import make_assessment, seed_questions

        seed_questions()
        make_assessment(self.pending)

        response = self.client.post(
            reverse("universities:delete", args=[self.pending.pk]),
            {"confirm_name": self.pending.name},
        )

        self.assertRedirects(response, reverse("universities:manage"))
        self.assertFalse(University.objects.filter(pk=self.pending.pk).exists())

    def test_admin_edit_updates_status_and_approval_timestamp(self):
        response = self.client.post(
            reverse("universities:admin_edit", args=[self.pending.pk]),
            {
                "name": self.pending.name,
                "country": "Nepal",
                "city": "Kathmandu",
                "website": "",
                "description": (
                    "Updated institutional profile describing AI strategy, teaching "
                    "and research priorities for consortium review."
                ),
                "status": University.STATUS_APPROVED,
                "review_note": "Approved after review.",
            },
        )

        self.assertRedirects(response, reverse("universities:manage"))
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, University.STATUS_APPROVED)
        self.assertIsNotNone(self.pending.approved_at)

    def test_admin_edit_clears_timestamp_when_not_approved(self):
        self.pending.status = University.STATUS_APPROVED
        self.pending.approved_at = timezone.now()
        self.pending.save(update_fields=["status", "approved_at"])

        self.client.post(
            reverse("universities:admin_edit", args=[self.pending.pk]),
            {
                "name": self.pending.name,
                "country": "Nepal",
                "city": "Kathmandu",
                "website": "",
                "description": (
                    "Updated institutional profile describing AI strategy, teaching "
                    "and research priorities for consortium review."
                ),
                "status": University.STATUS_PENDING,
                "review_note": "Further evidence requested.",
            },
        )

        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, University.STATUS_PENDING)
        self.assertIsNone(self.pending.approved_at)
