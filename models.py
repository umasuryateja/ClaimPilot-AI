from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
import re
from datetime import datetime, date
from utils import logger

class ClaimType(str, Enum):
    COLLISION = "Collision"
    INJURY = "Injury"
    PROPERTY_DAMAGE = "Property Damage"
    THEFT = "Theft"
    FIRE = "Fire"
    OTHER = "Other"

# Exact list of mandatory fields for validation and routing purposes
MANDATORY_FIELDS = [
    "policy_number",
    "policyholder_name",
    "incident_date",
    "incident_location",
    "incident_description",
    "claimant",
    "asset_type",
    "estimated_damage",
    "claim_type",
    "attachments",
    "initial_estimate"
]

class ExtractedFields(BaseModel):
    # Policy Information
    policy_number: Optional[str] = Field(default=None, description="Mandatory policy number")
    policyholder_name: Optional[str] = Field(default=None, description="Mandatory policyholder name")
    effective_dates: Optional[str] = Field(default=None, description="Optional policy effective dates (e.g., YYYY-MM-DD to YYYY-MM-DD)")
    
    # Incident Information
    incident_date: Optional[str] = Field(default=None, description="Mandatory incident date")
    incident_time: Optional[str] = Field(default=None, description="Optional incident time")
    incident_location: Optional[str] = Field(default=None, description="Mandatory incident location")
    incident_description: Optional[str] = Field(default=None, description="Mandatory incident description")
    
    # Involved Parties
    claimant: Optional[str] = Field(default=None, description="Mandatory claimant name")
    third_parties: Optional[str] = Field(default=None, description="Optional third parties")
    contact_details: Optional[str] = Field(default=None, description="Optional contact details")
    
    # Asset Details
    asset_type: Optional[str] = Field(default=None, description="Mandatory asset type")
    asset_id: Optional[str] = Field(default=None, description="Optional asset identification")
    estimated_damage: Optional[float] = Field(default=None, description="Mandatory estimated damage to the asset")
    
    # Other Mandatory Fields
    claim_type: Optional[str] = Field(default=None, description="Mandatory claim type")
    attachments: Optional[List[str]] = Field(default=None, description="Mandatory attachments (list of filenames or [] if confirmed none, null if not mentioned)")
    initial_estimate: Optional[float] = Field(default=None, description="Mandatory initial estimate of loss")

    @field_validator("estimated_damage", "initial_estimate", mode="before")
    @classmethod
    def clean_numeric(cls, v: Any) -> Optional[float]:
        """Cleans and converts raw input to float. Strips currency symbols and commas."""
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            # Strip currency symbols, spaces, commas, and other non-numeric stuff (except decimal point and minus sign)
            cleaned = re.sub(r"[^\d\.\-]", "", v)
            if not cleaned:
                return None
            try:
                return float(cleaned)
            except ValueError:
                logger.warning(f"Could not parse numeric value: {v}")
                return None
        return None

    @field_validator("attachments", mode="before")
    @classmethod
    def validate_attachments_input(cls, v: Any) -> Optional[List[str]]:
        """Maintains the distinction between null (not mentioned) and empty list (no attachments)."""
        if v is None:
            return None
        if isinstance(v, list):
            return [str(item) for item in v]
        if isinstance(v, str):
            # Check if text indicates none
            v_lower = v.lower().strip()
            if v_lower in ["none", "n/a", "no attachments", "none stated", "[]"]:
                return []
            return [v]
        return None

    def get_validation_errors(self) -> List[str]:
        """Runs custom business validations on the extracted fields and returns errors/warnings.
        
        This covers:
        - Unrecognized Claim Type values
        - Invalid/negative Estimated Damage or Initial Estimate
        - Invalid or impossible dates (e.g. future incident date, malformed strings)
        - Conflicting values (e.g. incident date after policy effective date)
        """
        errors = []
        
        # 1. Claim Type Validation
        if self.claim_type:
            allowed_types = [t.value for t in ClaimType]
            # Case insensitive check, but standardizing
            matched = False
            for t in allowed_types:
                if self.claim_type.strip().lower() == t.lower():
                    matched = True
                    break
            if not matched:
                errors.append(f"Unrecognized Claim Type '{self.claim_type}'. Allowed: {', '.join(allowed_types)}")
        
        # 2. Negative Values Check
        if self.estimated_damage is not None and self.estimated_damage < 0:
            errors.append(f"Invalid Estimated Damage: {self.estimated_damage} cannot be negative.")
        if self.initial_estimate is not None and self.initial_estimate < 0:
            errors.append(f"Invalid Initial Estimate: {self.initial_estimate} cannot be negative.")
            
        # 3. Dates validation
        incident_dt = None
        if self.incident_date:
            try:
                # Expecting YYYY-MM-DD
                incident_dt = datetime.strptime(self.incident_date.strip(), "%Y-%m-%d").date()
                # Check for future date (based on local time 2026-07-02)
                today = date(2026, 7, 2)
                if incident_dt > today:
                    errors.append(f"Incident Date '{self.incident_date}' is in the future (relative to current date 2026-07-02).")
            except ValueError:
                errors.append(f"Incident Date '{self.incident_date}' is not in YYYY-MM-DD format.")
                
        # 4. Conflicting values (Incident Date vs Policy Effective Dates)
        if incident_dt and self.effective_dates:
            # Parse effective dates. Typical formats: "YYYY-MM-DD to YYYY-MM-DD", "YYYY-MM-DD - YYYY-MM-DD", "YYYY-MM-DD"
            date_pattern = r"(\d{4}-\d{2}-\d{2})"
            found_dates = re.findall(date_pattern, self.effective_dates)
            if len(found_dates) >= 2:
                try:
                    start_dt = datetime.strptime(found_dates[0], "%Y-%m-%d").date()
                    end_dt = datetime.strptime(found_dates[1], "%Y-%m-%d").date()
                    if incident_dt < start_dt or incident_dt > end_dt:
                        errors.append(
                            f"Conflict: Incident Date ({self.incident_date}) falls outside the policy effective dates "
                            f"({start_dt} to {end_dt})."
                        )
                except ValueError:
                    pass  # Handled or skipped if parsing fails
            elif len(found_dates) == 1:
                try:
                    start_dt = datetime.strptime(found_dates[0], "%Y-%m-%d").date()
                    if incident_dt < start_dt:
                        errors.append(
                            f"Conflict: Incident Date ({self.incident_date}) is before policy start date ({start_dt})."
                        )
                except ValueError:
                    pass
                    
        return errors
