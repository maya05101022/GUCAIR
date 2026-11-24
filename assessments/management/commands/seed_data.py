"""Seed GUCAIR's question bank, resource library and optional demo institutions.

Usage:
    python manage.py seed_data              # questions + resources
    python manage.py seed_data --demo       # also 6 clearly-labelled demo universities

Demonstration records are flagged is_demo=True and labelled throughout the UI.
They are never presented as real consortium members.
"""

import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from assessments.models import AssessmentQuestion
from assessments.questions_data import QUESTIONS
from assessments.services import create_assessment
from resources.models import Resource
from universities.models import University

RESOURCES = [
    {
        "title": "AI Readiness Assessment Handbook",
        "category": Resource.CATEGORY_IMPLEMENTATION,
        "summary": "How the six-dimension GUCAIR instrument works, how responses are scored and how to interpret the results responsibly.",
        "content": (
            "The GUCAIR AI Readiness Assessment is an institutional self-assessment instrument. "
            "It is designed to support structured reflection, peer learning and improvement planning. "
            "It is not an accreditation decision and should not be described as one.\n\n"
            "The instrument contains 24 questions across six dimensions: AI Infrastructure; AI Education "
            "and Curriculum; Research and Innovation; Faculty AI Skills; AI Governance and Ethics; and "
            "AI Integration and Adoption. Each question uses a five-point maturity scale from 0 (Not "
            "Implemented) to 4 (Fully Implemented).\n\n"
            "Dimension scores are calculated by summing the responses for that dimension and dividing by "
            "the maximum possible score (four points multiplied by the number of questions). The result is "
            "normalised to 0-100. The overall score uses the same calculation across all 24 questions, so "
            "every question carries equal weight.\n\n"
            "Scores are grouped into four bands: Initial (0-39), Developing (40-59), Advanced (60-79) and "
            "Leading (80-100). Bands describe the current state of institutional practice; they do not "
            "measure teaching quality or research excellence.\n\n"
            "When completing the assessment, bring together academic leadership, IT, quality assurance, "
            "research and governance colleagues. Evidence should be current. If a practice exists only in "
            "one department, choose Developing rather than Established. Reassess at least annually and "
            "compare trends rather than isolated scores."
        ),
    },
    {
        "title": "Building an Institutional AI Governance Framework",
        "category": Resource.CATEGORY_GOVERNANCE,
        "summary": "A practical structure for policy approval, accountability, risk triage and assurance of AI systems in universities.",
        "content": (
            "AI governance translates institutional values into repeatable decisions. A workable framework "
            "has five components: an approved policy statement; named accountability; risk classification; "
            "review and assurance processes; and transparency with affected communities.\n\n"
            "Start with an acceptable-use policy covering approved tools, prohibited uses, human oversight, "
            "data handling and disclosure. Assign ownership at executive level and create an operational "
            "group with academic, legal, IT, privacy and student representation.\n\n"
            "Use a tiered risk approach. Low-risk productivity tools may only require registration and data "
            "protection checks. Systems that affect admissions, assessment, employment or student welfare "
            "require documented impact assessment, bias testing, appeals routes and periodic audit.\n\n"
            "Procurement is a governance control point. Require vendors to disclose training data practices, "
            "retention, model change notifications and security arrangements. Retain the right to audit and "
            "to exit.\n\n"
            "Finally, publish clear guidance for staff and students, log AI systems in an inventory, and "
            "test an incident process before an incident occurs. Review the framework annually against "
            "regulatory change and lessons learned."
        ),
    },
    {
        "title": "AI Literacy for Every Graduate: Curriculum Design Notes",
        "category": Resource.CATEGORY_LEARNING,
        "summary": "Design principles for embedding AI literacy outcomes across disciplines without adding disconnected modules.",
        "content": (
            "AI literacy is not only programming. It includes understanding how AI systems make predictions, "
            "recognising limitations and bias, evaluating outputs, protecting data, and using AI accountably "
            "within a discipline.\n\n"
            "Begin with programme-level outcomes rather than a single module. Each graduate should be able to "
            "explain core AI concepts, apply appropriate tools to a disciplinary problem, critique outputs and "
            "document their use ethically.\n\n"
            "Integrate rather than bolt on. A law programme can examine algorithmic decision-making; a nursing "
            "programme can evaluate clinical decision support; a business programme can audit predictive "
            "analytics. Shared learning outcomes allow local relevance while preserving comparability.\n\n"
            "Assessment must evolve with the tools. Prefer authentic tasks that require process evidence, oral "
            "defence, reflection on AI use, or data-informed critique. Publish integrity guidance that "
            "distinguishes permitted assistance from substitution of student work.\n\n"
            "Staff capability determines success. Provide discipline-specific development and examples, "
            "moderate expectations in the first year, and evaluate whether graduates can demonstrate the "
            "outcomes rather than merely whether modules were offered."
        ),
    },
    {
        "title": "Responsible AI: Questions Universities Should Ask",
        "category": Resource.CATEGORY_RESPONSIBLE,
        "summary": "A compact checklist for fairness, transparency, accountability, privacy and human oversight before deploying an AI system.",
        "content": (
            "Before deploying an AI system, teams should answer a consistent set of questions and record "
            "the answers.\n\n"
            "Purpose and necessity: What decision or service does the system support? Is AI necessary, or "
            "would a simpler rule-based approach be safer?\n\n"
            "Data: What data trains or feeds the system? Is its use lawful, proportionate and explained to "
            "affected people? Could historical bias be reproduced or amplified?\n\n"
            "Performance and limits: How was accuracy tested, for which groups, and under what conditions? "
            "What happens when the system is wrong or uncertain?\n\n"
            "Transparency: Are users told that AI is involved? Can they obtain a meaningful explanation and "
            "a route to human review?\n\n"
            "Accountability: Who owns the decision? Who monitors drift, complaints and incidents? What is the "
            "rollback plan?\n\n"
            "Human oversight: Where must a qualified person review or override output? Is that oversight real "
            "or nominal?\n\n"
            "Document the answers, review them with affected stakeholders where appropriate, and schedule "
            "reassessment. Responsible AI is an ongoing practice, not a one-time sign-off."
        ),
    },
    {
        "title": "From Pilot to Practice: Scaling AI in University Operations",
        "category": Resource.CATEGORY_INTEGRATION,
        "summary": "How to move from isolated AI experiments to governed services with measurable benefits and human oversight.",
        "content": (
            "Most universities begin AI adoption with scattered experiments. Scaling requires a pipeline that "
            "selects, evaluates and retires initiatives deliberately.\n\n"
            "Create a single intake route for proposals. Require a problem statement, affected stakeholders, "
            "data sources, risk tier and success measures. A cross-functional group should review the portfolio "
            "monthly to avoid duplication and unmanaged risk.\n\n"
            "Pilot with a defined comparison baseline. Measure quality, time, cost and user experience before "
            "and after. Include failure modes and a stop condition. Do not scale on vendor demonstrations "
            "alone.\n\n"
            "Prepare operations before launch: ownership, service levels, support, monitoring, training and "
            "communication. Update procurement and data agreements. Ensure human review is designed into "
            "high-impact workflows.\n\n"
            "After launch, report benefits realisation and incidents to leadership. Retire tools that do not "
            "deliver value. Publish lessons so other units can reuse patterns rather than repeat discovery."
        ),
    },
    {
        "title": "Faculty Development Pathways for AI Capability",
        "category": Resource.CATEGORY_LEARNING,
        "summary": "A staged professional learning model from foundational awareness to advanced disciplinary practice.",
        "content": (
            "Faculty confidence varies widely, and one-off workshops rarely change practice. A staged pathway "
            "works better.\n\n"
            "Stage one builds shared vocabulary: what AI can and cannot do, data protection basics, and "
            "institutional policy. Keep sessions short, practical and discipline-neutral.\n\n"
            "Stage two develops disciplinary application. Staff redesign one assessment or workflow, test it, "
            "and discuss results with peers. Communities of practice sustain momentum and reduce duplication.\n\n"
            "Stage three supports advanced practice: AI-integrated research methods, curriculum innovation, "
            "supervision of AI-related projects and contribution to governance.\n\n"
            "Recognise participation in workload and promotion criteria. Provide protected time, not only "
            "optional lunchtime sessions. Use peer mentors and showcase authentic examples.\n\n"
            "Evaluate change in practice, not attendance. Track redesigned assessments, adopted tools, "
            "student outcomes and staff confidence over time."
        ),
    },
    {
        "title": "Research Data and Compute: A Planning Primer",
        "category": Resource.CATEGORY_RESEARCH,
        "summary": "Key decisions for shared AI research infrastructure, access models, data stewardship and cost sustainability.",
        "content": (
            "AI research capacity depends on more than hardware. Institutions need an access model, data "
            "stewardship, technical support and a funding path.\n\n"
            "Inventory existing compute and demand. Decide which workloads need local resources and which can "
            "use cloud or national facilities. Publish allocation criteria and a fair access process.\n\n"
            "Data is usually the harder constraint. Establish catalogues, retention rules, consent tracking and "
            "secure environments for sensitive data. Provide guidance on licences and provenance.\n\n"
            "Plan support roles: research software engineers, data stewards and platform administrators. "
            "Without them, equipment utilisation and reproducibility suffer.\n\n"
            "Model total cost including energy, refresh cycles and support. Consider chargeback or priority "
            "allocations, but protect exploratory work and early-career researchers.\n\n"
            "Report utilisation and research outcomes so investment decisions are evidence-based and "
            "sustainable."
        ),
    },
    {
        "title": "Procuring AI Tools: Due Diligence Checklist",
        "category": Resource.CATEGORY_IMPLEMENTATION,
        "summary": "The minimum questions to ask before a university signs an AI vendor agreement.",
        "content": (
            "AI procurement combines standard technology due diligence with specific questions about data, "
            "model behaviour and accountability.\n\n"
            "Data: Where is data stored and processed? Is institutional data used to train vendor models? What "
            "are retention and deletion terms? Can the institution export its data?\n\n"
            "Security and privacy: Which certifications apply? How are access control, encryption and incident "
            "notification handled? Is a data processing agreement in place?\n\n"
            "Model behaviour: What is the intended use and known limitation? How is accuracy evaluated? How "
            "are updates communicated? Can the institution pin a version or audit changes?\n\n"
            "Transparency and redress: Are users informed that AI is involved? Can outputs be explained? What "
            "is the appeals route for affected individuals?\n\n"
            "Exit and continuity: What happens at contract end? Can the institution migrate or delete data? "
            "Are there lock-in risks?\n\n"
            "Record the answers in the procurement file. High-impact uses require deeper review and executive "
            "sign-off."
        ),
    },
]


def _demo_answers(base):
    """Build 24 answers around a target maturity level."""
    rng = random.Random(int(base * 100))
    answers = {}
    questions = AssessmentQuestion.objects.filter(is_active=True).order_by("dimension", "order")
    for question in questions:
        offset = rng.choice([-1, 0, 0, 1])
        answers[question.pk] = max(0, min(4, int(round(base)) + offset))
    return answers


class Command(BaseCommand):
    help = "Seed assessment questions, the resource library and optional demo universities."

    def add_arguments(self, parser):
        parser.add_argument(
            "--demo",
            action="store_true",
            help="Create six clearly-labelled demonstration universities with assessments.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        created_questions = 0
        for dimension, items in QUESTIONS.items():
            for index, (text, guidance) in enumerate(items, start=1):
                _, created = AssessmentQuestion.objects.update_or_create(
                    dimension=dimension,
                    order=index,
                    defaults={"text": text, "guidance": guidance, "is_active": True},
                )
                created_questions += int(created)
        self.stdout.write(
            self.style.SUCCESS(
                f"Question bank ready: {AssessmentQuestion.objects.count()} active questions "
                f"({created_questions} newly created)."
            )
        )

        admin_user = User.objects.filter(is_superuser=True).first()
        created_resources = 0
        for item in RESOURCES:
            _, created = Resource.objects.update_or_create(
                title=item["title"],
                defaults={
                    "category": item["category"],
                    "summary": item["summary"],
                    "content": item["content"],
                    "is_published": True,
                    "created_by": admin_user,
                },
            )
            created_resources += int(created)
        self.stdout.write(
            self.style.SUCCESS(
                f"Resource library ready: {Resource.objects.count()} resources "
                f"({created_resources} newly created)."
            )
        )

        if not options["demo"]:
            self.stdout.write(
                "Skipped demo institutions. Use --demo to seed clearly-labelled demonstration records."
            )
            return

        demo_data = [
            {
                "name": "Demo — Meridian University (Canada)",
                "country": "Canada",
                "city": "Toronto",
                "website": "https://example.edu",
                "base": 3.7,
                "description": (
                    "Demonstration record used to illustrate a leading AI readiness profile. "
                    "This institution is fictional and is not a real consortium member."
                ),
            },
            {
                "name": "Demo — Nordic Institute of Technology (Sweden)",
                "country": "Sweden",
                "city": "Stockholm",
                "website": "https://example.edu",
                "base": 3.1,
                "description": (
                    "Demonstration record showing an advanced AI readiness profile. "
                    "This institution is fictional and is not a real consortium member."
                ),
            },
            {
                "name": "Demo — Gulf University of Innovation (UAE)",
                "country": "United Arab Emirates",
                "city": "Abu Dhabi",
                "website": "https://example.edu",
                "base": 2.8,
                "description": (
                    "Demonstration record used for analytics examples. "
                    "This institution is fictional and is not a real consortium member."
                ),
            },
            {
                "name": "Demo — Andes National University (Chile)",
                "country": "Chile",
                "city": "Santiago",
                "website": "https://example.edu",
                "base": 2.3,
                "description": (
                    "Demonstration record used for analytics examples. "
                    "This institution is fictional and is not a real consortium member."
                ),
            },
            {
                "name": "Demo — Mekong Polytechnic (Vietnam)",
                "country": "Vietnam",
                "city": "Ho Chi Minh City",
                "website": "https://example.edu",
                "base": 1.6,
                "description": (
                    "Demonstration record showing an early-stage AI readiness profile. "
                    "This institution is fictional and is not a real consortium member."
                ),
            },
            {
                "name": "Demo — Sahara Open University (Egypt)",
                "country": "Egypt",
                "city": "Cairo",
                "website": "https://example.edu",
                "base": 1.1,
                "description": (
                    "Demonstration record showing an initial AI readiness profile. "
                    "This institution is fictional and is not a real consortium member."
                ),
            },
        ]

        for data in demo_data:
            university, _ = University.objects.update_or_create(
                name=data["name"],
                defaults={
                    "country": data["country"],
                    "city": data["city"],
                    "website": data["website"],
                    "description": data["description"],
                    "status": University.STATUS_APPROVED,
                    "is_demo": True,
                    "approved_at": timezone.now(),
                },
            )
            if not university.assessments.exists():
                if data["base"] >= 2.8:
                    create_assessment(
                        university=university,
                        submitted_by=None,
                        answers=_demo_answers(max(0.4, data["base"] - 0.6)),
                    )
                create_assessment(
                    university=university,
                    submitted_by=None,
                    answers=_demo_answers(data["base"]),
                )
        self.stdout.write(
            self.style.SUCCESS(
                f"Demo universities ready: {University.objects.filter(is_demo=True).count()} "
                "clearly-labelled demonstration records."
            )
        )
