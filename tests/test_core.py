from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import UserProfile
from core.models import ContactMessage

from .utils import login, make_user


class PublicPageTests(TestCase):
    def test_landing_page_renders(self):
        response = self.client.get(reverse("core:landing"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GUCAIR")
        self.assertIn("stats", response.context)

    def test_about_page_renders_six_dimensions(self):
        response = self.client.get(reverse("core:about"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["dimensions"]), 6)

    def test_contact_page_renders(self):
        response = self.client.get(reverse("core:contact"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Contact")

    def test_health_endpoint_reports_database_connection(self):
        response = self.client.get(reverse("core:health"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["database"], "connected")
        self.assertIn("universities", payload)

    def test_unknown_url_returns_custom_404(self):
        response = self.client.get("/this-path-does-not-exist/")

        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "404", status_code=404)

    def test_security_headers_are_present(self):
        response = self.client.get(reverse("core:landing"))

        self.assertEqual(response["X-Frame-Options"], "DENY")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")


class ContactFormTests(TestCase):
    def test_valid_contact_message_is_persisted(self):
        response = self.client.post(
            reverse("core:contact"),
            {
                "name": "Dr Farhana Ahmed",
                "email": "farhana@example.edu",
                "organization": "Example University",
                "subject": "Consortium membership",
                "message": "We would like to join the GUCAIR readiness programme.",
            },
        )

        self.assertRedirects(response, reverse("core:contact"))
        message = ContactMessage.objects.get(email="farhana@example.edu")
        self.assertFalse(message.is_resolved)

    def test_invalid_contact_message_is_not_saved(self):
        response = self.client.post(
            reverse("core:contact"),
            {"name": "", "email": "not-an-email", "subject": "", "message": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_contact_form_requires_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)

        response = csrf_client.post(
            reverse("core:contact"),
            {
                "name": "No Token",
                "email": "notoken@example.edu",
                "organization": "",
                "subject": "CSRF test",
                "message": "This request should be rejected without a CSRF token.",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(ContactMessage.objects.count(), 0)


class ContactMessageAdminTests(TestCase):
    def setUp(self):
        self.admin = make_user(username="message_admin", role=UserProfile.ROLE_ADMIN)
        self.rep = make_user(username="message_rep")
        self.message = ContactMessage.objects.create(
            name="Dr Karim",
            email="karim@example.edu",
            subject="Research collaboration",
            message="We are interested in a joint AI research programme.",
        )

    def test_contact_message_list_requires_admin(self):
        login(self.client, self.rep)

        response = self.client.get(reverse("core:contact_messages"))

        self.assertEqual(response.status_code, 403)

    def test_admin_can_view_and_filter_messages(self):
        login(self.client, self.admin)

        response = self.client.get(reverse("core:contact_messages"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Research collaboration")

        response = self.client.get(
            reverse("core:contact_messages"), {"status": "resolved"}
        )
        self.assertNotContains(response, "Research collaboration")

    def test_admin_can_toggle_message_resolution(self):
        login(self.client, self.admin)

        response = self.client.post(
            reverse("core:toggle_contact_message", args=[self.message.pk])
        )

        self.assertRedirects(response, reverse("core:contact_messages"))
        self.message.refresh_from_db()
        self.assertTrue(self.message.is_resolved)

    def test_toggle_requires_post(self):
        login(self.client, self.admin)

        response = self.client.get(
            reverse("core:toggle_contact_message", args=[self.message.pk])
        )

        self.assertEqual(response.status_code, 405)
