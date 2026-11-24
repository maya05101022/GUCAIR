from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import UserProfile
from universities.models import University

from .utils import login, make_university, make_user

PASSWORD = "StrongPass!2345"


def registration_payload(**overrides):
    payload = {
        "first_name": "Amina",
        "last_name": "Rahman",
        "username": "amina_rep",
        "email": "amina@example.edu",
        "job_title": "Director of Digital Learning",
        "phone": "+8801700000000",
        "university_name": "Amina Institute of Technology",
        "country": "Bangladesh",
        "city": "Dhaka",
        "website": "https://amina.example.edu",
        "description": (
            "Amina Institute of Technology is a teaching-led institution investing "
            "in applied AI, digital learning infrastructure and responsible adoption."
        ),
        "password1": PASSWORD,
        "password2": PASSWORD,
    }
    payload.update(overrides)
    return payload


class RegistrationTests(TestCase):
    def test_registration_creates_account_profile_and_pending_university(self):
        response = self.client.post(reverse("accounts:register"), registration_payload())

        self.assertRedirects(response, reverse("dashboard:home"))
        user = User.objects.get(username="amina_rep")
        self.assertEqual(user.email, "amina@example.edu")
        self.assertTrue(user.check_password(PASSWORD))
        self.assertFalse(user.is_staff)

        profile = user.profile
        self.assertEqual(profile.role, UserProfile.ROLE_REPRESENTATIVE)
        self.assertEqual(profile.job_title, "Director of Digital Learning")

        university = profile.university
        self.assertIsNotNone(university)
        self.assertEqual(university.status, University.STATUS_PENDING)
        self.assertEqual(university.created_by, user)
        self.assertEqual(university.slug, "amina-institute-of-technology")
        self.assertIsNone(university.approved_at)

        # The new representative is signed in immediately after registration.
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_registration_rejects_duplicate_email(self):
        make_user(username="existing")
        User.objects.filter(username="existing").update(email="amina@example.edu")

        response = self.client.post(reverse("accounts:register"), registration_payload())

        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["form"].errors)
        self.assertFalse(User.objects.filter(username="amina_rep").exists())

    def test_registration_rejects_duplicate_university_name(self):
        make_university(name="Amina Institute of Technology")

        response = self.client.post(reverse("accounts:register"), registration_payload())

        self.assertEqual(response.status_code, 200)
        self.assertIn("university_name", response.context["form"].errors)
        self.assertFalse(User.objects.filter(username="amina_rep").exists())

    def test_registration_rejects_short_description(self):
        response = self.client.post(
            reverse("accounts:register"),
            registration_payload(description="Too short"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("description", response.context["form"].errors)
        self.assertFalse(University.objects.filter(name="Amina Institute of Technology").exists())

    def test_authenticated_user_is_redirected_away_from_registration(self):
        user = make_user(username="signed_in")
        login(self.client, user)

        response = self.client.get(reverse("accounts:register"))

        self.assertRedirects(response, reverse("dashboard:home"))


class AuthenticationTests(TestCase):
    def test_login_accepts_valid_credentials(self):
        user = make_user(username="login_rep")

        response = self.client.post(
            reverse("accounts:login"),
            {"username": "login_rep", "password": "TestPass!234"},
        )

        self.assertRedirects(response, reverse("dashboard:home"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_login_rejects_invalid_credentials(self):
        make_user(username="login_rep")

        response = self.client.post(
            reverse("accounts:login"),
            {"username": "login_rep", "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_protected_pages_redirect_anonymous_users_to_login(self):
        response = self.client.get(reverse("accounts:profile"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response["Location"])
        self.assertIn("next=", response["Location"])

    def test_logout_signs_user_out(self):
        user = make_user(username="logout_rep")
        login(self.client, user)

        response = self.client.post(reverse("accounts:logout"))

        self.assertRedirects(response, reverse("core:landing"))
        self.assertNotIn("_auth_user_id", self.client.session)


class ProfileTests(TestCase):
    def setUp(self):
        self.university = make_university(name="Profile University")
        self.user = make_user(username="profile_rep", university=self.university)
        login(self.client, self.user)

    def test_profile_page_renders(self):
        response = self.client.get(reverse("accounts:profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Profile University")

    def test_profile_update_saves_user_and_profile_fields(self):
        response = self.client.post(
            reverse("accounts:profile"),
            {
                "first_name": "Nadia",
                "last_name": "Islam",
                "email": "nadia@example.edu",
                "job_title": "AI Lead",
                "phone": "+8801800000000",
            },
        )

        self.assertRedirects(response, reverse("accounts:profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Nadia")
        self.assertEqual(self.user.email, "nadia@example.edu")
        self.assertEqual(self.user.profile.job_title, "AI Lead")
        self.assertEqual(self.user.profile.phone, "+8801800000000")

    def test_profile_rejects_email_used_by_another_account(self):
        make_user(username="other").__class__.objects.filter(username="other").update(
            email="taken@example.edu"
        )

        response = self.client.post(
            reverse("accounts:profile"),
            {
                "first_name": "Nadia",
                "last_name": "Islam",
                "email": "taken@example.edu",
                "job_title": "AI Lead",
                "phone": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["form"].errors)
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.email, "taken@example.edu")

    def test_password_change_updates_credentials(self):
        response = self.client.post(
            reverse("accounts:password_change"),
            {
                "old_password": "TestPass!234",
                "new_password1": PASSWORD,
                "new_password2": PASSWORD,
            },
        )

        self.assertRedirects(response, reverse("accounts:profile"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(PASSWORD))


class AdminUserManagementTests(TestCase):
    def setUp(self):
        self.admin = make_user(username="admin_user", role=UserProfile.ROLE_ADMIN)
        self.rep = make_user(username="managed_rep")
        login(self.client, self.admin)

    def test_admin_can_view_user_list(self):
        response = self.client.get(reverse("accounts:user_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "admin_user")
        self.assertContains(response, "managed_rep")

    def test_user_list_search_filters_results(self):
        response = self.client.get(reverse("accounts:user_list"), {"q": "managed"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "managed_rep")
        self.assertNotContains(response, "admin_user")

    def test_representative_cannot_access_user_management(self):
        self.client.logout()
        login(self.client, self.rep)

        response = self.client.get(reverse("accounts:user_list"))

        self.assertEqual(response.status_code, 403)

    def test_admin_can_toggle_another_account_active_state(self):
        response = self.client.post(
            reverse("accounts:user_toggle_active", args=[self.rep.pk])
        )

        self.assertRedirects(response, reverse("accounts:user_list"))
        self.rep.refresh_from_db()
        self.assertFalse(self.rep.is_active)

    def test_admin_cannot_deactivate_own_account(self):
        response = self.client.post(
            reverse("accounts:user_toggle_active", args=[self.admin.pk])
        )

        self.assertRedirects(response, reverse("accounts:user_list"))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_admin_can_change_user_role(self):
        response = self.client.post(
            reverse("accounts:user_set_role", args=[self.rep.pk]),
            {"role": UserProfile.ROLE_ADMIN},
        )

        self.assertRedirects(response, reverse("accounts:user_list"))
        self.rep.refresh_from_db()
        self.rep.profile.refresh_from_db()
        self.assertEqual(self.rep.profile.role, UserProfile.ROLE_ADMIN)
        self.assertTrue(self.rep.is_staff)

    def test_admin_cannot_remove_own_admin_role(self):
        response = self.client.post(
            reverse("accounts:user_set_role", args=[self.admin.pk]),
            {"role": UserProfile.ROLE_REPRESENTATIVE},
        )

        self.assertRedirects(response, reverse("accounts:user_list"))
        self.admin.profile.refresh_from_db()
        self.assertEqual(self.admin.profile.role, UserProfile.ROLE_ADMIN)

    def test_unknown_role_is_rejected(self):
        response = self.client.post(
            reverse("accounts:user_set_role", args=[self.rep.pk]),
            {"role": "superhero"},
        )

        self.assertRedirects(response, reverse("accounts:user_list"))
        self.rep.profile.refresh_from_db()
        self.assertEqual(self.rep.profile.role, UserProfile.ROLE_REPRESENTATIVE)

    def test_admin_flag_promotes_profile_role_on_save(self):
        user = User.objects.create_user(
            username="promoted", email="promoted@example.edu", password=PASSWORD
        )
        user.is_staff = True
        user.save(update_fields=["is_staff"])

        user.profile.refresh_from_db()
        self.assertEqual(user.profile.role, UserProfile.ROLE_ADMIN)

    def test_passwords_are_hashed(self):
        raw = User.objects.get(username="managed_rep").password

        self.assertNotEqual(raw, "TestPass!234")
        self.assertTrue(
            raw.startswith(("pbkdf2_", "argon2", "scrypt", "bcrypt", "md5$"))
        )
