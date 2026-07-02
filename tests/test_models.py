import pytest
from models import ExtractedFields

def test_clean_numeric():
    # Valid string formats
    fields = ExtractedFields(
        estimated_damage="$24,500.50",
        initial_estimate="15000",
        policy_number="POL-1",
        policyholder_name="John Doe",
        incident_date="2026-01-01",
        incident_location="Main St",
        incident_description="Collision",
        claimant="John Doe",
        asset_type="Car",
        claim_type="Collision",
        attachments=[]
    )
    assert fields.estimated_damage == 24500.50
    assert fields.initial_estimate == 15000.0

    # Handles floats directly
    fields2 = ExtractedFields(
        estimated_damage=123.45,
        initial_estimate=123.45
    )
    assert fields2.estimated_damage == 123.45
    assert fields2.initial_estimate == 123.45

def test_negative_numeric_fails_validation():
    fields = ExtractedFields(
        estimated_damage=-100.0,
        initial_estimate=-50.0,
        claim_type="Collision"
    )
    errors = fields.get_validation_errors()
    assert any("cannot be negative" in err for err in errors)

def test_claim_type_validation():
    # Valid
    fields_valid = ExtractedFields(claim_type="Collision")
    errors = fields_valid.get_validation_errors()
    assert not any("Unrecognized Claim Type" in err for err in errors)

    # Invalid
    fields_invalid = ExtractedFields(claim_type="Extreme Catastrophe")
    errors = fields_invalid.get_validation_errors()
    assert any("Unrecognized Claim Type" in err for err in errors)

def test_date_validations():
    # Test valid date
    fields_ok = ExtractedFields(incident_date="2026-05-10")
    assert not any("Incident Date" in err for err in fields_ok.get_validation_errors())

    # Test future date (past 2026-07-02)
    fields_future = ExtractedFields(incident_date="2026-12-25")
    errors = fields_future.get_validation_errors()
    assert any("in the future" in err for err in errors)

    # Test malformed date
    fields_malformed = ExtractedFields(incident_date="05/10/2026")
    errors = fields_malformed.get_validation_errors()
    assert any("not in YYYY-MM-DD format" in err for err in errors)

def test_policy_effective_date_conflicts():
    # Incident fits within range
    fields_ok = ExtractedFields(incident_date="2026-02-10", effective_dates="2026-01-01 to 2026-12-31")
    assert not any("Conflict:" in err for err in fields_ok.get_validation_errors())

    # Incident before range
    fields_before = ExtractedFields(incident_date="2025-12-15", effective_dates="2026-01-01 to 2026-12-31")
    errors = fields_before.get_validation_errors()
    assert any("falls outside the policy effective dates" in err for err in errors)

    # Incident after range
    fields_after = ExtractedFields(incident_date="2027-01-15", effective_dates="2026-01-01 to 2026-12-31")
    # Wait, 2027 incident is also in the future, so it might have 2 errors (future + conflict). Let's check for conflict.
    errors = fields_after.get_validation_errors()
    assert any("falls outside the policy effective dates" in err for err in errors)

def test_attachments_list_vs_null():
    # Attachments explicitly none
    fields_none = ExtractedFields(attachments="None")
    assert fields_none.attachments == []

    # Attachments explicitly empty list
    fields_empty = ExtractedFields(attachments=[])
    assert fields_empty.attachments == []

    # Attachments listed
    fields_items = ExtractedFields(attachments=["photo.jpg", "receipt.pdf"])
    assert fields_items.attachments == ["photo.jpg", "receipt.pdf"]

    # Attachments not mentioned
    fields_null = ExtractedFields(attachments=None)
    assert fields_null.attachments is None
