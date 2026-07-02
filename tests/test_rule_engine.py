import pytest
from models import ExtractedFields
from rule_engine import evaluate_rules

def test_rule_priority_investigation_flag():
    # Description contains "staged" (fraud keyword)
    # Also has missing fields and is an injury claim under 25k.
    # Because Investigation Flag is priority 1, it must be selected.
    fields = ExtractedFields(
        policy_number=None, # Missing mandatory field (normally priority 2)
        policyholder_name="Jane Doe",
        incident_date="2026-01-01",
        incident_location="123 Main St",
        incident_description="This crash was staged by the driver.", # Priority 1 keyword
        claimant="Jane Doe",
        asset_type="Car",
        estimated_damage=15000.0, # Fast-track candidate (normally priority 4)
        claim_type="Injury", # Injury claim (normally priority 3)
        attachments=[],
        initial_estimate=15000.0
    )
    result = evaluate_rules(fields)
    assert result["recommendedRoute"] == "Investigation Flag"
    assert "staged" in result["reasoning"].lower()
    assert "Manual Review" in result["reasoning"] # Reasoning must mention other matches
    assert "Specialist Queue" in result["reasoning"]
    assert "Fast-track" in result["reasoning"]

def test_rule_priority_manual_review():
    # Missing fields, is an injury claim under 25k.
    # No fraud description.
    # Should route to Manual Review (priority 2) over Specialist Queue (priority 3).
    fields = ExtractedFields(
        policy_number=None, # Missing
        policyholder_name="Jane Doe",
        incident_date="2026-01-01",
        incident_location="123 Main St",
        incident_description="Rear-ended at stop light.",
        claimant="Jane Doe",
        asset_type="Car",
        estimated_damage=10000.0,
        claim_type="Injury", # Specialist Queue match
        attachments=[],
        initial_estimate=10000.0
    )
    result = evaluate_rules(fields)
    assert result["recommendedRoute"] == "Manual Review"
    assert "Policy Number" in result["missingFields"]
    assert "Specialist Queue" in result["reasoning"]
    assert "Fast-track" in result["reasoning"]

def test_rule_priority_specialist_queue():
    # Complete document, Injury type, damage < 25k.
    # No fraud, no missing fields.
    # Specialist Queue (priority 3) should take precedence over Fast-track (priority 4).
    fields = ExtractedFields(
        policy_number="POL-12345",
        policyholder_name="Jane Doe",
        incident_date="2026-01-01",
        incident_location="123 Main St",
        incident_description="Rear-ended at stop light, driver has neck pain.",
        claimant="Jane Doe",
        asset_type="Car",
        estimated_damage=10000.0,
        claim_type="Injury",
        attachments=[],
        initial_estimate=10000.0
    )
    result = evaluate_rules(fields)
    assert result["recommendedRoute"] == "Specialist Queue"
    assert "whiplash" not in result["reasoning"] # standard injury check
    assert "Fast-track" in result["reasoning"] # should mention fast-track matched as well

def test_rule_priority_fast_track():
    # Complete document, Collision type, damage < 25k.
    # No fraud, no missing, no injury.
    # Routes to Fast-track (priority 4).
    fields = ExtractedFields(
        policy_number="POL-12345",
        policyholder_name="Jane Doe",
        incident_date="2026-01-01",
        incident_location="123 Main St",
        incident_description="Rear-ended at stop light, minor fender dent.",
        claimant="Jane Doe",
        asset_type="Car",
        estimated_damage=5000.0,
        claim_type="Collision",
        attachments=[],
        initial_estimate=5000.0
    )
    result = evaluate_rules(fields)
    assert result["recommendedRoute"] == "Fast-track"
    assert len(result["missingFields"]) == 0

def test_rule_priority_standard_review():
    # Complete document, Collision type, damage >= 25k.
    # No fraud, no missing, no injury, high damage.
    # Default route: Standard Review.
    fields = ExtractedFields(
        policy_number="POL-12345",
        policyholder_name="Jane Doe",
        incident_date="2026-01-01",
        incident_location="123 Main St",
        incident_description="T-boned at intersection, severe frame damage.",
        claimant="Jane Doe",
        asset_type="Car",
        estimated_damage=30000.0,
        claim_type="Collision",
        attachments=[],
        initial_estimate=30000.0
    )
    result = evaluate_rules(fields)
    assert result["recommendedRoute"] == "Standard Review"
