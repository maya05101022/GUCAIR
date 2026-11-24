"""Assessment question bank for the six GUCAIR readiness dimensions.

Four questions per dimension produce a 24-question instrument. Every response
uses the same 0-4 maturity scale, which keeps dimension scores directly
comparable and normalises cleanly onto a 0-100 scale.
"""

QUESTIONS = {
    "infrastructure": [
        (
            "Dedicated AI computing capacity",
            "Consider GPU/CPU clusters, cloud credits and shared research computing available to staff and students.",
        ),
        (
            "Data infrastructure and management",
            "Consider data warehouses, catalogues, quality controls, retention rules and interoperability standards.",
        ),
        (
            "Campus connectivity and platform reliability",
            "Consider network performance, identity management, labs and availability of core digital services.",
        ),
        (
            "Technical support for AI systems",
            "Consider specialist support staff, service desks, monitoring and lifecycle management for AI tools.",
        ),
    ],
    "curriculum": [
        (
            "AI content embedded in degree programmes",
            "Consider AI literacy modules and AI components in disciplines beyond computer science.",
        ),
        (
            "Dedicated AI degree and certificate pathways",
            "Consider majors, minors, micro-credentials and postgraduate AI programmes that are actively delivered.",
        ),
        (
            "AI learning outcomes and assessment design",
            "Consider published outcomes, authentic assessment and academic integrity guidance for AI-assisted work.",
        ),
        (
            "Student access to applied AI practice",
            "Consider projects, internships, hackathons and laboratory work that build practical AI competence.",
        ),
    ],
    "research": [
        (
            "Active AI research portfolio",
            "Consider funded projects, publications and research groups working on AI or AI-adjacent problems.",
        ),
        (
            "AI research funding and infrastructure",
            "Consider internal grants, external awards, compute allocation and research data support.",
        ),
        (
            "Interdisciplinary and industry collaboration",
            "Consider joint projects with industry, public bodies and other disciplines or institutions.",
        ),
        (
            "Responsible innovation and knowledge transfer",
            "Consider commercialisation, policy engagement, open science and responsible research review.",
        ),
    ],
    "faculty": [
        (
            "Faculty AI literacy baseline",
            "Consider how many academic staff can confidently explain and use core AI concepts.",
        ),
        (
            "Structured professional development",
            "Consider training programmes, certifications, communities of practice and release time for upskilling.",
        ),
        (
            "AI expertise depth in academic units",
            "Consider the number of staff with advanced AI expertise and how it is distributed across faculties.",
        ),
        (
            "Recognition and incentives for AI teaching",
            "Consider workload recognition, promotion criteria and rewards for AI innovation in teaching.",
        ),
    ],
    "governance": [
        (
            "Institutional AI policy",
            "Consider an approved policy covering acceptable use, procurement, transparency and accountability.",
        ),
        (
            "Ethics review for AI projects",
            "Consider an ethics board, review thresholds, bias assessment and escalation routes.",
        ),
        (
            "Data protection and privacy controls",
            "Consider consent, minimisation, retention, vendor agreements and handling of sensitive data.",
        ),
        (
            "Monitoring, audit and incident response",
            "Consider model oversight, logging, redress mechanisms and a tested AI incident process.",
        ),
    ],
    "integration": [
        (
            "AI in administrative operations",
            "Consider adoption in admissions, finance, facilities, HR or student services with human oversight.",
        ),
        (
            "AI in teaching and learning services",
            "Consider learning analytics, tutoring, content support and accessibility tools in active use.",
        ),
        (
            "Institution-wide adoption strategy",
            "Consider a roadmap, governance ownership, success measures and cross-unit coordination.",
        ),
        (
            "Change management and stakeholder engagement",
            "Consider communication, staff and student involvement, pilot evaluation and scaling decisions.",
        ),
    ],
}

RESPONSE_SCALE = [
    (0, "Not Implemented", "No activity, capability or formal arrangement exists."),
    (1, "Initial", "Isolated experiments or informal activity without institutional support."),
    (2, "Developing", "Defined activity in some units with partial resources and coordination."),
    (3, "Established", "Institution-wide practice, documented and resourced with routine review."),
    (4, "Fully Implemented", "Systematic, measured, continuously improved and externally recognised."),
]
