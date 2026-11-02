
"""Confidence calculation based on available scoring evidence."""


def confidence_from_completeness(completeness: int) -> str:
    """Return confidence based on weighted data completeness."""

    completeness = max(0, min(100, int(completeness)))

    if completeness >= 85:
        return "High"

    if completeness >= 60:
        return "Medium"

    return "Low"
