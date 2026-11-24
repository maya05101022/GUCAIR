from django.test import TestCase
from django.urls import reverse

from accounts.models import UserProfile
from resources.models import Resource

from .utils import login, make_user


def make_resource(title="AI Governance Playbook", published=True, category="governance"):
    return Resource.objects.create(
        title=title,
        category=category,
        summary="A practical reference for institutional AI governance and assurance.",
        content="Detailed guidance for policy, ethics review and accountable AI adoption.",
        is_published=published,
    )


class PublicResourceTests(TestCase):
    def setUp(self):
        self.published = make_resource()
        self.draft = make_resource(title="Draft Resource", published=False)

    def test_list_only_shows_published_resources(self):
        response = self.client.get(reverse("resources:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.published.title)
        self.assertNotContains(response, self.draft.title)

    def test_list_search_filters_resources(self):
        response = self.client.get(reverse("resources:list"), {"q": "Governance"})

        self.assertContains(response, self.published.title)
        self.assertNotContains(response, self.draft.title)

    def test_list_filters_by_category(self):
        response = self.client.get(
            reverse("resources:list"), {"category": "governance"}
        )

        self.assertContains(response, self.published.title)

        response = self.client.get(
            reverse("resources:list"), {"category": "learning"}
        )
        self.assertNotContains(response, self.published.title)

    def test_published_detail_is_public(self):
        response = self.client.get(
            reverse("resources:detail", args=[self.published.slug])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["resource"], self.published)

    def test_draft_detail_is_hidden_from_public(self):
        response = self.client.get(reverse("resources:detail", args=[self.draft.slug]))

        self.assertEqual(response.status_code, 404)

    def test_related_resources_exclude_current_item(self):
        make_resource(title="Related Governance Guide", category="governance")

        response = self.client.get(
            reverse("resources:detail", args=[self.published.slug])
        )

        related = list(response.context["related"])
        self.assertNotIn(self.published, related)
        self.assertEqual(len(related), 1)

    def test_slug_is_generated_and_unique(self):
        second = make_resource(title=self.published.title)

        self.assertEqual(self.published.slug, "ai-governance-playbook")
        self.assertEqual(second.slug, "ai-governance-playbook-2")


class ResourceAdminTests(TestCase):
    def setUp(self):
        self.admin = make_user(username="resource_admin", role=UserProfile.ROLE_ADMIN)
        self.rep = make_user(username="resource_rep")
        login(self.client, self.admin)

    def test_management_page_requires_admin(self):
        self.client.logout()
        login(self.client, self.rep)

        response = self.client.get(reverse("resources:manage"))

        self.assertEqual(response.status_code, 403)

    def test_admin_can_view_management_page(self):
        make_resource(title="Draft Resource", published=False)

        response = self.client.get(reverse("resources:manage"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Draft Resource")

    def test_admin_can_create_resource(self):
        response = self.client.post(
            reverse("resources:create"),
            {
                "title": "Responsible AI Checklist",
                "category": "responsible",
                "summary": "A concise checklist for responsible AI deployment.",
                "content": "Step-by-step checks covering fairness, transparency and review.",
                "external_link": "example.edu/checklist",
                "is_published": "on",
            },
        )

        self.assertRedirects(response, reverse("resources:manage"))
        resource = Resource.objects.get(title="Responsible AI Checklist")
        self.assertEqual(resource.created_by, self.admin)
        self.assertEqual(resource.external_link, "https://example.edu/checklist")
        self.assertTrue(resource.is_published)

    def test_admin_can_edit_resource(self):
        resource = make_resource()

        response = self.client.post(
            reverse("resources:edit", args=[resource.slug]),
            {
                "title": "Updated Governance Playbook",
                "category": "governance",
                "summary": "Updated summary for institutional AI governance.",
                "content": "Updated guidance covering policy and assurance.",
                "external_link": "",
                "is_published": "on",
            },
        )

        self.assertRedirects(response, reverse("resources:manage"))
        resource.refresh_from_db()
        self.assertEqual(resource.title, "Updated Governance Playbook")

    def test_admin_can_delete_resource(self):
        resource = make_resource()

        response = self.client.post(
            reverse("resources:delete", args=[resource.slug])
        )

        self.assertRedirects(response, reverse("resources:manage"))
        self.assertFalse(Resource.objects.filter(pk=resource.pk).exists())

    def test_admin_can_view_draft_detail(self):
        draft = make_resource(title="Internal Draft", published=False)

        response = self.client.get(reverse("resources:detail", args=[draft.slug]))

        self.assertEqual(response.status_code, 200)
