import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from core.scoring_engine import score_lead
from core.lead_validator import normalize_lead, validate_lead

SAMPLE = {"name":"Rahul Sharma","company_name":"ABC Technologies","website":"www.abctechnologies.com","job_title":"Founder","industry":"IT Services","company_location":"Bangalore","company_size":"50-100 Employees","lead_source":"Website","requirement":"Looking for CRM software","email":"rahul@example.com","phone":"+91 9876543210"}

def test_identical_inputs_are_deterministic():
    assert score_lead(SAMPLE) == score_lead(SAMPLE)

def test_score_is_bounded():
    result = score_lead(SAMPLE)
    assert 0 <= result["score"] <= 100

def test_sample_lead_is_hot():
    assert score_lead(SAMPLE)["classification"] == "Hot"

def test_missing_data_reduces_completeness_but_still_scores():
    lead = {"job_title":"Founder", "requirement":"Looking for CRM software"}
    result = score_lead(lead)
    assert 0 <= result["score"] <= 100
    assert result["data_completeness"] < 100
    assert result["confidence"] == "Low"

def test_invalid_email_is_reported():
    lead = normalize_lead({"company_name":"Acme", "email":"not-an-email"})
    assert any("Email" in error for error in validate_lead(lead))

def test_empty_lead_is_rejected_by_validator():
    assert validate_lead(normalize_lead({}))
