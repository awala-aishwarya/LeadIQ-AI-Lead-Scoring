"""Input normalization and lightweight validation."""
import re

FIELDS = ["name", "company_name", "website", "job_title", "industry", "company_location", "company_size", "lead_source", "requirement", "email", "phone"]


def normalize_lead(data: dict) -> dict:
    lead = {field: str(data.get(field, "") or "").strip() for field in FIELDS}
    lead["website"] = lead["website"].removeprefix("https://").removeprefix("http://").rstrip("/")
    return lead


def validate_lead(lead: dict) -> list[str]:
    errors = []
    email = lead.get("email", "")
    if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        errors.append("Email format looks invalid.")
    phone = lead.get("phone", "")
    if phone and len(re.sub(r"\D", "", phone)) < 10:
        errors.append("Phone number should contain at least 10 digits.")
    if not any(lead.get(key) for key in ["company_name", "name", "email", "phone"]):
        errors.append("Enter at least a name, company name, email or phone number.")
    return errors
