from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.core.exceptions import ValidationError

from .models import (
    DIMENSIONS,
    DIMENSION_LABELS,
    Assessment,
    AssessmentQuestion,
    AssessmentResponse,
    AssessmentResult,
    category_for_score,
)
from .questions_data import RESPONSE_SCALE


def round_score(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_active_questions():
    questions = list(
        AssessmentQuestion.objects.filter(is_active=True).order_by("dimension", "order")
    )
    dimension_order = {key: index for index, (key, _, _) in enumerate(DIMENSIONS)}
    questions.sort(key=lambda q: (dimension_order.get(q.dimension, 99), q.order, q.id))
    return questions


def compute_scores(questions, answers):
    """Compute dimension and overall scores from validated answers.

    Each answer is on a 0-4 maturity scale. A dimension score is the sum of its
    raw answers divided by four times the number of dimension questions, then
    expressed on a 0-100 scale. The overall score uses the same formula across
    all questions, so every question carries equal weight.
    """
    dimension_raw = {}
    for key, _, _ in DIMENSIONS:
        dimension_raw[key] = {"raw": 0, "max": 0, "count": 0}

    for question in questions:
        answer = answers.get(question.id)
        if answer is None:
            raise ValidationError("Every assessment question must be answered.")
        if answer not in range(0, 5):
            raise ValidationError("Responses must use the 0-4 scale.")
        bucket = dimension_raw[question.dimension]
        bucket["raw"] += answer
        bucket["max"] += 4
        bucket["count"] += 1

    results = []
    for key, label, _ in DIMENSIONS:
        bucket = dimension_raw[key]
        if bucket["max"] == 0:
            raise ValidationError(f"No active questions found for {label}.")
        results.append(
            {
                "dimension": key,
                "raw_score": bucket["raw"],
                "max_score": bucket["max"],
                "score": round_score(bucket["raw"] / bucket["max"] * 100),
            }
        )

    total_raw = sum(item["raw_score"] for item in results)
    total_max = sum(item["max_score"] for item in results)
    overall = round_score(total_raw / total_max * 100)
    return results, total_raw, total_max, overall


@transaction.atomic
def create_assessment(university, submitted_by, answers):
    questions = get_active_questions()
    if not questions:
        raise ValidationError(
            "The assessment question bank is empty. Contact the consortium administrator."
        )
    missing = [q for q in questions if q.id not in answers]
    if missing:
        raise ValidationError("Every assessment question must be answered.")

    results, total_raw, total_max, overall = compute_scores(questions, answers)
    assessment = Assessment.objects.create(
        university=university,
        submitted_by=submitted_by,
        overall_score=overall,
        category=category_for_score(overall),
        total_raw_score=total_raw,
        max_raw_score=total_max,
    )
    AssessmentResponse.objects.bulk_create(
        [
            AssessmentResponse(
                assessment=assessment,
                question=question,
                score=int(answers[question.id]),
            )
            for question in questions
        ]
    )
    AssessmentResult.objects.bulk_create(
        [
            AssessmentResult(
                assessment=assessment,
                dimension=item["dimension"],
                score=item["score"],
                raw_score=item["raw_score"],
                max_score=item["max_score"],
            )
            for item in results
        ]
    )
    return assessment


RECOMMENDATIONS = {
    "infrastructure": {
        "default": "Define a shared AI compute and data platform roadmap with funded ownership, capacity monitoring and a specialist support model.",
        "Initial": "Establish a baseline inventory of compute, data and connectivity assets, then fund one shared pilot platform with named technical ownership.",
        "Developing": "Consolidate fragmented infrastructure into governed shared services with service-level targets, cost visibility and secure data pipelines.",
        "Advanced": "Introduce demand forecasting, chargeback or allocation models, and resilience testing so AI infrastructure scales reliably.",
        "Leading": "Pursue federated or sovereign AI infrastructure partnerships and publish utilisation, energy and service performance metrics.",
    },
    "curriculum": {
        "default": "Embed AI literacy outcomes across every faculty and establish governed pathways from introductory modules to advanced specialisms.",
        "Initial": "Approve AI literacy learning outcomes and pilot two cross-faculty modules with authentic, AI-aware assessment.",
        "Developing": "Formalise AI pathways, micro-credentials and integrity guidance, then evaluate graduate AI competence annually.",
        "Advanced": "Scale interdisciplinary AI capstones and industry-embedded projects with systematic curriculum review and student outcome data.",
        "Leading": "Export AI curriculum models through open resources and international partnerships, with external validation of graduate readiness.",
    },
    "research": {
        "default": "Set a focused AI research agenda with internal seed funding, ethical review and clear routes to translation.",
        "Initial": "Map existing AI research capability, seed two interdisciplinary projects and appoint a research coordination lead.",
        "Developing": "Create a competitive internal AI grant scheme and formal industry or public-sector collaboration agreements.",
        "Advanced": "Build large-scale funded programmes with dedicated research infrastructure, open-science practices and commercialisation support.",
        "Leading": "Sustain internationally recognised AI research clusters and measure societal and economic impact beyond publication counts.",
    },
    "faculty": {
        "default": "Adopt a staff AI capability framework with protected development time, recognition and faculty-level targets.",
        "Initial": "Run a staff capability census and deliver foundational AI literacy workshops for every faculty.",
        "Developing": "Introduce role-specific development pathways, communities of practice and workload recognition for AI teaching innovation.",
        "Advanced": "Embed AI capability in promotion and workload models, with advanced practitioner networks and peer review.",
        "Leading": "Operate a continuous professional learning system with external certification and measurable teaching impact.",
    },
    "governance": {
        "default": "Publish an institutional AI policy, operationalise ethics review and test an AI incident response process.",
        "Initial": "Draft and approve an AI acceptable-use policy and establish an ethics review route for high-risk projects.",
        "Developing": "Extend policy into procurement, vendor assessment, data protection and bias review with documented accountability.",
        "Advanced": "Introduce model registers, audit trails and regular assurance reporting to council or senate.",
        "Leading": "Continuously audit AI systems, publish transparency information and contribute to national or international AI governance standards.",
    },
    "integration": {
        "default": "Create a cross-institution adoption roadmap with human oversight, measurable outcomes and a disciplined pilot-to-scale process.",
        "Initial": "Select two administrative or learning processes for an AI pilot with explicit success measures and human oversight.",
        "Developing": "Coordinate adoption through a cross-functional AI steering group and standardise evaluation before scaling.",
        "Advanced": "Scale proven AI services with change management, monitoring and benefits realisation reported to leadership.",
        "Leading": "Embed continuous AI service improvement and share evaluated adoption models across the consortium.",
    },
}


def build_recommendations(assessment, limit=4):
    results = list(assessment.results.all())
    ranked = sorted(results, key=lambda item: item.score_value)
    recommendations = []
    for result in ranked[:limit]:
        label = DIMENSION_LABELS.get(result.dimension, result.dimension.title())
        advice = RECOMMENDATIONS.get(result.dimension, {}).get(
            result.category,
            RECOMMENDATIONS.get(result.dimension, {}).get("default", ""),
        )
        recommendations.append(
            {
                "dimension": result.dimension,
                "label": label,
                "score": result.score_value,
                "category": result.category,
                "advice": advice,
            }
        )
    return recommendations


def response_scale_choices():
    return [(value, label) for value, label, _ in RESPONSE_SCALE]
