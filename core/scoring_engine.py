
"""Deterministic and explainable lead scoring engine."""

from __future__ import annotations

from typing import Any
import re
import math

WEIGHTS = {
    "decision_authority": 20,
    "purchase_intent": 25,
    "company_size": 15,
    "industry_fit": 15,
    "lead_source": 10,
    "contactability": 15,
}

ROLE_SCORES = {
    "founder": 100,
    "co-founder": 100,
    "ceo": 100,
    "chief executive officer": 100,
    "owner": 100,
    "managing director": 95,
    "vp": 90,
    "vice president": 90,
    "director": 85,
    "head": 80,
    "manager": 65,
    "team lead": 60,
    "consultant": 50,
    "analyst": 40,
    "executive": 35,
    "intern": 15,
}

INTENT_RULES = [
    (100, [
        "ready to purchase", "ready to buy", "schedule a demo",
        "request a demo", "pricing", "quote", "proposal",
        "implementation", "urgent", "immediately"
    ]),
    (85, [
        "looking for", "need", "require", "shortlisting",
        "evaluating", "actively searching", "purchase", "buying"
    ]),
    (65, [
        "interested in", "exploring", "considering",
        "comparing", "planning"
    ]),
    (40, [
        "learn more", "information", "know more", "research"
    ]),
]

INDUSTRY_SCORES = {
    "it services": 100,
    "information technology": 100,
    "software": 100,
    "saas": 100,
    "technology": 95,
    "financial services": 90,
    "banking": 90,
    "healthcare": 85,
    "education": 80,
    "manufacturing": 75,
    "retail": 75,
    "real estate": 70,
}

SOURCE_SCORES = {
    "website": 100,
    "demo request": 100,
    "contact form": 90,
    "referral": 95,
    "partner referral": 95,
    "webinar": 80,
    "linkedin": 75,
    "organic search": 75,
    "event": 70,
    "paid ads": 60,
    "social media": 55,
    "cold email": 35,
    "purchased list": 15,
}

SIZE_SCORES = [
    ((1000, float("inf")), 100),
    ((200, 999), 90),
    ((50, 199), 85),
    ((11, 49), 70),
    ((2, 10), 55),
    ((1, 1), 40),
]


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _is_missing(value: Any) -> bool:
    return (
        value is None
        or str(value).strip().lower()
        in {"", "nan", "none", "null", "n/a"}
    )


def _size_score(value: Any) -> int | None:
    """Convert employee ranges into a representative company size."""

    if _is_missing(value):
        return None

    raw = _clean(value).replace(",", "")
    numbers = re.findall(r"\d+", raw)

    if not numbers:
        return None

    if len(numbers) >= 2:
        count = (int(numbers[0]) + int(numbers[1])) / 2
    else:
        count = int(numbers[0])

    for (low, high), score in SIZE_SCORES:
        if low <= count <= high:
            return score

    return 30 if count < 1 else 100


def _role_score(value: Any) -> int | None:
    """Evaluate decision-making authority from job title."""

    if _is_missing(value):
        return None

    title = _clean(value)

    for role, score in ROLE_SCORES.items():
        pattern = r"(?<!\w)" + re.escape(role) + r"(?!\w)"
        if re.search(pattern, title):
            return score

    return 45


def _intent_score(value: Any) -> int | None:
    """Evaluate purchase intent using predefined buying signals."""

    if _is_missing(value):
        return None

    text = _clean(value)

    for score, phrases in INTENT_RULES:
        if any(phrase in text for phrase in phrases):
            return score

    return 25


def _industry_score(value: Any) -> int | None:
    if _is_missing(value):
        return None

    industry = _clean(value)

    for key, score in INDUSTRY_SCORES.items():
        if key in industry:
            return score

    return 60


def _source_score(value: Any) -> int | None:
    if _is_missing(value):
        return None

    source = _clean(value)

    for key, score in SOURCE_SCORES.items():
        if key in source:
            return score

    return 50


def _contact_score(email: Any, phone: Any) -> int | None:
    """Evaluate the availability of valid contact channels."""

    if _is_missing(email) and _is_missing(phone):
        return None

    score = 0

    if not _is_missing(email):
        email_value = str(email).strip()
        email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

        if re.fullmatch(email_pattern, email_value):
            score += 60

    if not _is_missing(phone):
        digits = re.sub(r"\D", "", str(phone))

        if 10 <= len(digits) <= 15:
            score += 40

    return score


def score_lead(lead: dict[str, Any]) -> dict[str, Any]:
    """
    Calculate a deterministic lead score.

    Missing dimensions are excluded and remaining weights
    are normalized to maintain a score between 0 and 100.
    """

    dimensions = {
        "Decision-making authority": (
            "decision_authority",
            _role_score(lead.get("job_title"))
        ),
        "Purchase intent": (
            "purchase_intent",
            _intent_score(lead.get("requirement"))
        ),
        "Company size fit": (
            "company_size",
            _size_score(lead.get("company_size"))
        ),
        "Industry relevance": (
            "industry_fit",
            _industry_score(lead.get("industry"))
        ),
        "Lead source quality": (
            "lead_source",
            _source_score(lead.get("lead_source"))
        ),
        "Contactability": (
            "contactability",
            _contact_score(
                lead.get("email"),
                lead.get("phone")
            )
        ),
    }

    available_weight = sum(
        WEIGHTS[key]
        for key, value in dimensions.values()
        if value is not None
    )

    weighted_points = sum(
        value * WEIGHTS[key] / 100
        for key, value in dimensions.values()
        if value is not None
    )

    if available_weight:
        score = math.floor(
            (weighted_points / available_weight) * 100 + 0.5
        )
    else:
        score = 0

    breakdown = []
    positive = []
    negative = []
    missing = []

    for label, (key, raw_score) in dimensions.items():

        weight = WEIGHTS[key]

        if raw_score is None:
            missing.append(label)

            breakdown.append({
                "factor": label,
                "weight": weight,
                "rating": None,
                "weighted_points": None,
                "status": "Missing",
            })
            continue

        contribution = round(raw_score * weight / 100, 2)

        breakdown.append({
            "factor": label,
            "weight": weight,
            "rating": raw_score,
            "weighted_points": contribution,
            "status": "Available",
        })

        if raw_score >= 70:
            positive.append(
                f"{label} is strong ({raw_score}/100; weight {weight}%)."
            )
        elif raw_score < 50:
            negative.append(
                f"{label} is weak ({raw_score}/100; weight {weight}%)."
            )

    classification = (
        "Hot" if score >= 75
        else "Warm" if score >= 45
        else "Cold"
    )

    completeness = round(available_weight)

    confidence = (
        "High" if completeness >= 85
        else "Medium" if completeness >= 60
        else "Low"
    )

    quality = {
        "Hot": "Strong-fit lead with clear buying signals.",
        "Warm": "Potentially suitable lead; qualify needs and buying timeline.",
        "Cold": "Low-priority lead based on the information currently available.",
    }[classification]

    if missing:
        quality += " Missing data: " + ", ".join(missing) + "."

    action = {
        "Hot": (
            "Prioritize a personal sales follow-up within one business day; "
            "offer a tailored demo and confirm buying timeline."
        ),
        "Warm": (
            "Send a relevant case study and schedule a qualification "
            "conversation; clarify budget, authority and timeline."
        ),
        "Cold": (
            "Place in a low-frequency nurture sequence; gather missing "
            "details before assigning sales time."
        ),
    }[classification]

    if confidence == "Low":
        action = (
            "First enrich the lead record and verify contact details; "
            "then reassess before committing sales resources."
        )

    available_dimensions = len(dimensions) - len(missing)

    explanation = (
        f"The lead scored {score}/100 and is classified as {classification}. "
        f"The weighted contribution is {weighted_points:.2f} points "
        f"across {available_weight}% available weight. "
        f"The score is calculated as "
        f"({weighted_points:.2f} / {available_weight}) * 100. "
        f"{available_dimensions} of {len(dimensions)} dimensions "
        f"contain available information. Missing dimensions are excluded "
        f"and the remaining weights are normalized."
        if available_weight else
        "No scoring dimensions contain sufficient information. "
        "Please provide additional lead details."
    )

    return {
        "score": score,
        "classification": classification,
        "quality": quality,
        "positive_factors": positive or [
            "No strong positive factor identified from the supplied data."
        ],
        "negative_factors": negative or [
            "No major weak factor identified among the supplied data."
        ],
        "missing_fields": missing,
        "confidence": confidence,
        "data_completeness": completeness,
        "recommended_action": action,
        "explanation": explanation,
        "breakdown": breakdown,
    }
