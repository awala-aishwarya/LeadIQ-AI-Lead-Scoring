"""Classification thresholds shared by the application."""
THRESHOLDS = {"Hot": (75, 100), "Warm": (45, 74), "Cold": (0, 44)}


def classify(score: int) -> str:
    if score >= 75:
        return "Hot"
    if score >= 45:
        return "Warm"
    return "Cold"
