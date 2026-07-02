from typing import Dict, Any, List
from models import ExtractedFields, MANDATORY_FIELDS
from utils import logger

# Map from snake_case model fields to the exact mandatory field names requested in Section 3
MANDATORY_FIELD_MAPPING = {
    "policy_number": "Policy Number",
    "policyholder_name": "Policyholder Name",
    "incident_date": "Incident Date",
    "incident_location": "Incident Location",
    "incident_description": "Incident Description",
    "claimant": "Claimant",
    "asset_type": "Asset Type",
    "estimated_damage": "Estimated Damage",
    "claim_type": "Claim Type",
    "attachments": "Attachments",
    "initial_estimate": "Initial Estimate"
}

def evaluate_rules(fields: ExtractedFields) -> Dict[str, Any]:
    """Applies business rules in priority order and outputs the final 4-key JSON.
    
    Mandatory field set for routing/validation purposes:
    - Policy Number
    - Policyholder Name
    - Incident Date
    - Incident Location
    - Incident Description
    - Claimant
    - Asset Type
    - Estimated Damage
    - Claim Type
    - Attachments
    - Initial Estimate
    
    Priority Order:
    1. Investigation Flag: incident_description contains "fraud", "staged", or "inconsistent" (case-insensitive substring match).
    2. Manual Review: any mandatory field is missing, blank, or null (except attachments which can be []).
    3. Specialist Queue: claim_type is "Injury" (case-insensitive).
    4. Fast-track: estimated_damage < 25000.
    5. Standard Review: Default if no other rules match.
    
    Args:
        fields (ExtractedFields): The validated Pydantic fields model.
        
    Returns:
        Dict[str, Any]: Exactly 4 keys: 'extractedFields', 'missingFields', 'recommendedRoute', 'reasoning'.
    """
    logger.info("Evaluating claims routing rules...")
    
    # 1. Evaluate missing mandatory fields
    missing_fields_list: List[str] = []
    for field_key, display_name in MANDATORY_FIELD_MAPPING.items():
        val = getattr(fields, field_key)
        # Check if missing/blank/null
        is_missing = False
        if val is None:
            is_missing = True
        elif isinstance(val, str) and not val.strip():
            is_missing = True
        # Note: attachments = [] is NOT missing. Only attachments = None is missing.
        
        if is_missing:
            missing_fields_list.append(display_name)
            
    # 2. Check each routing rule condition
    matched_rules = []
    
    # Rule 1: Investigation Flag
    desc = fields.incident_description or ""
    desc_lower = desc.lower()
    found_keywords = [kw for kw in ["fraud", "staged", "inconsistent"] if kw in desc_lower]
    if found_keywords:
        matched_rules.append({
            "route": "Investigation Flag",
            "priority": 1,
            "reason": f"the incident description contains flagged terminology ('{found_keywords[0]}') suggesting inconsistency or potential fraud"
        })
        
    # Rule 2: Manual Review
    if len(missing_fields_list) > 0:
        matched_rules.append({
            "route": "Manual Review",
            "priority": 2,
            "reason": f"mandatory fields are missing or not stated in the document ({', '.join(missing_fields_list)})"
        })
        
    # Rule 3: Specialist Queue
    c_type = fields.claim_type or ""
    is_injury = (c_type.strip().lower() == "injury")
    if is_injury:
        matched_rules.append({
            "route": "Specialist Queue",
            "priority": 3,
            "reason": "the claim is classified as an Injury claim type, requiring bodily injury specialist handling"
        })
        
    # Rule 4: Fast-track
    # Assumes USD default. If currency other than USD is detected, we keep it in numeric and flag in reasoning.
    is_fasttrack = False
    if fields.estimated_damage is not None and fields.estimated_damage < 25000:
        is_fasttrack = True
        matched_rules.append({
            "route": "Fast-track",
            "priority": 4,
            "reason": f"the estimated asset damage (${fields.estimated_damage:,.2f}) is below the $25,000 threshold for expedited processing"
        })
        
    # 3. Sort matched rules by priority (highest first, i.e., priority 1 is highest)
    matched_rules.sort(key=lambda x: x["priority"])
    
    # 4. Determine final recommended route and reasoning
    if matched_rules:
        primary_match = matched_rules[0]
        recommended_route = primary_match["route"]
        
        # Build reasoning explanation (2-4 sentences)
        primary_reason = primary_match["reason"].capitalize()
        reasoning_sentences = [f"Claim routed to {recommended_route} because {primary_match['reason']}."]
        
        # Add details about other rules that matched
        other_matches = matched_rules[1:]
        if other_matches:
            other_routes = [m["route"] for m in other_matches]
            reasoning_sentences.append(f"It also matched criteria for: {', '.join(other_routes)}.")
            
        # Add validation warning summary if Pydantic business rules failed
        validation_warnings = fields.get_validation_errors()
        if validation_warnings:
            reasoning_sentences.append(f"Validation warnings: {'; '.join(validation_warnings)}.")
            
        reasoning = " ".join(reasoning_sentences)
    else:
        # Default route
        recommended_route = "Standard Review"
        reasoning = (
            "Claim routed to Standard Review. The document is complete, no potential fraud indicators "
            "were detected, the claim is not for an injury, and estimated damage meets or exceeds the fast-track threshold."
        )
        # Check if validation warnings exist even without routing matches
        validation_warnings = fields.get_validation_errors()
        if validation_warnings:
            reasoning += f" Validation warnings: {'; '.join(validation_warnings)}."
            
    # 5. Build final dictionary matching exact keys requested in Section 5
    return {
        "extractedFields": fields.model_dump(),
        "missingFields": missing_fields_list,
        "recommendedRoute": recommended_route,
        "reasoning": reasoning
    }
