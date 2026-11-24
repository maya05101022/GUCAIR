SITE_NAME = "Global University Consortium of AI Readiness"
SITE_SHORT_NAME = "GUCAIR"
SITE_EMAIL = "secretariat@gucair.org"


def site_context(request):
    context = {
        "site_name": SITE_NAME,
        "site_short_name": SITE_SHORT_NAME,
        "site_email": SITE_EMAIL,
        "current_year": __import__("datetime").date.today().year,
    }
    if request.user.is_authenticated:
        profile = getattr(request.user, "profile", None)
        context["user_profile"] = profile
        context["user_university"] = getattr(profile, "university", None)
        if profile and profile.is_administrator:
            from universities.models import University

            context["admin_pending_count"] = University.objects.pending().count()
            from core.models import ContactMessage

            context["admin_open_messages"] = ContactMessage.objects.filter(
                is_resolved=False
            ).count()
    return context
