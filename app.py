import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve and load .env from the absolute parent directory before any other imports
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

import streamlit as st
import json
import traceback
from typing import Optional, Dict, Any

from utils import logger, get_api_key, GEMINI_MODEL
from theme import inject_theme_css
from extractor import extract_text_from_file
from gemini_parser import parse_fnol_document
from models import ExtractedFields
from rule_engine import evaluate_rules, MANDATORY_FIELD_MAPPING

def run_pipeline(file_path: str, file_name: str) -> None:
    """Runs the ingestion pipeline from end-to-end and stores results in session state."""
    st.session_state.file_name = file_name
    st.session_state.extracted_text = None
    st.session_state.is_ocr_triggered = False
    st.session_state.parsed_json = None
    st.session_state.final_output = None
    st.session_state.error_message = None
    st.session_state.is_truncated = False
    
    try:
        # 1. Extraction (PDF / TXT text extraction + OCR fallback)
        text, is_ocr = extract_text_from_file(file_path)
        st.session_state.extracted_text = text
        st.session_state.is_ocr_triggered = is_ocr
        
        # Hard stop if extraction produced nothing
        if not text or not text.strip():
            st.error("Could not extract any text from this file. Please check that the PDF is not empty, corrupted, or a blank scanned page.")
            st.stop()
            
        # 2. Parsing (Gemini AI parses structured JSON)
        parsed_data, truncated = parse_fnol_document(text)
        st.session_state.parsed_json = parsed_data
        st.session_state.is_truncated = truncated
        
        # 3. Validation & Routing (Pydantic model + rule priority engine)
        extracted_fields_model = ExtractedFields(**parsed_data)
        final_results = evaluate_rules(extracted_fields_model)
        st.session_state.final_output = final_results
        
    except Exception:
        import traceback
        st.code(traceback.format_exc())
        raise

def render_native_field(label: str, value: Any) -> None:
    """Renders a key-value field cleanly inside columns using native Streamlit widgets."""
    col_l, col_r = st.columns([2, 3])
    with col_l:
        st.markdown(f"**{label}**")
    with col_r:
        if value is None or value == "":
            st.markdown("*Not Stated*")
        elif isinstance(value, list):
            if not value:
                st.markdown("`[]` (None)")
            else:
                st.markdown(", ".join(f"`{v}`" for v in value))
        else:
            st.markdown(str(value))

def main():
    # Inject custom UI theme CSS
    inject_theme_css()

    # Title & Subtitle Header inside a full-width deep navy colored banner card
    st.markdown('''
    <div class="header-banner">
        <h1 class="banner-title">ClaimPilot AI</h1>
        <p class="banner-subtitle">Autonomous Insurance Claims Processing Agent</p>
    </div>
    ''', unsafe_allow_html=True)

    # Enforce API Key validation in .env strictly
    try:
        get_api_key()
    except ValueError:
        st.error("🔑 GEMINI_API_KEY not found. Add it to your .env file and restart the app.")
        st.stop()

    # Initialize session states for processed data
    if "file_name" not in st.session_state:
        st.session_state.file_name = None
    if "extracted_text" not in st.session_state:
        st.session_state.extracted_text = None
    if "is_ocr_triggered" not in st.session_state:
        st.session_state.is_ocr_triggered = False
    if "parsed_json" not in st.session_state:
        st.session_state.parsed_json = None
    if "final_output" not in st.session_state:
        st.session_state.final_output = None
    if "error_message" not in st.session_state:
        st.session_state.error_message = None
    if "is_truncated" not in st.session_state:
        st.session_state.is_truncated = False

    # 1. Native Uploader Container (replaces HTML div to eliminate DOM overlap conflicts)
    with st.container(border=True):
        st.markdown("### 📄 Upload FNOL Document")
        st.markdown("Drag & Drop PDF or TXT here")
        uploaded_file = st.file_uploader(
            "Upload First Notice of Loss File",
            type=["pdf", "txt"],
            label_visibility="collapsed"
        )

    # 2. Pipeline Trigger Logic
    run_file_path = None
    run_file_name = None

    # Handle custom uploader files (runs automatically when file is added/changed)
    if uploaded_file is not None:
        if uploaded_file.name != st.session_state.file_name:
            # Save upload file locally
            os.makedirs("output", exist_ok=True)
            temp_path = os.path.join("output", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            run_file_path = temp_path
            run_file_name = uploaded_file.name

    # Execute processing automatic run
    if run_file_path and run_file_name:
        with st.spinner("Processing claim..."):
            run_pipeline(run_file_path, run_file_name)
        st.rerun()

    # Show General Error Message if general exceptions were encountered
    if st.session_state.error_message:
        st.error(f"❌ Error processing document: {st.session_state.error_message}")
        if st.button("Clear Error & Reset", key="clear_err_btn"):
            for key in ["file_name", "extracted_text", "is_ocr_triggered", "parsed_json", "final_output", "error_message", "is_truncated"]:
                if key in st.session_state:
                    st.session_state[key] = None
            st.rerun()
        st.stop()

    # 3. Render Results Section (only if output is loaded)
    if st.session_state.final_output:
        st.divider()  # Visual and layout divider (40-60px vertical spacing)

        final_data = st.session_state.final_output
        extracted = final_data["extractedFields"]
        missing = final_data["missingFields"]
        route = final_data["recommendedRoute"]
        reasoning = final_data["reasoning"]

        # OCR or Truncation notifications
        if st.session_state.is_ocr_triggered:
            st.warning("⚠️ Scanned PDF detected! Standard text extraction was empty. OCR Fallback was automatically triggered.")
        if st.session_state.is_truncated:
            st.warning("⚠️ Warning: The document was excessively long and was truncated to fit token limits prior to extraction.")

        # Expandable raw text block for manual verification
        with st.expander("🔍 View Raw Extracted Text Layer", expanded=False):
            st.text_area("Extracted Document Content", st.session_state.extracted_text, height=250, disabled=True)

        st.markdown("<br/>", unsafe_allow_html=True)

        # Results Layout: 2 Columns (Left: 65% for fields, Right: 35% for route, missing, completeness, actions)
        col1, col2 = st.columns([0.65, 0.35])

        with col1:
            # 📋 Policy Information
            with st.container(border=True):
                st.markdown("#### 📋 Policy Information")
                render_native_field("Policy Number", extracted.get("policy_number"))
                render_native_field("Policyholder Name", extracted.get("policyholder_name"))
                render_native_field("Effective Dates", extracted.get("effective_dates"))

            # 🚗 Incident Information
            with st.container(border=True):
                st.markdown("#### 🚗 Incident Information")
                render_native_field("Incident Date", extracted.get("incident_date"))
                render_native_field("Incident Time", extracted.get("incident_time"))
                render_native_field("Incident Location", extracted.get("incident_location"))
                render_native_field("Incident Description", extracted.get("incident_description"))

            # 👥 Involved Parties
            with st.container(border=True):
                st.markdown("#### 👥 Involved Parties")
                render_native_field("Claimant", extracted.get("claimant"))
                render_native_field("Third Parties", extracted.get("third_parties"))
                render_native_field("Contact Details", extracted.get("contact_details"))

            # 🚘 Asset Information
            with st.container(border=True):
                st.markdown("#### 🚘 Asset Information")
                render_native_field("Asset Type", extracted.get("asset_type"))
                render_native_field("Asset ID", extracted.get("asset_id"))
                dmg = extracted.get("estimated_damage")
                dmg_str = f"${dmg:,.2f}" if isinstance(dmg, (int, float)) else dmg
                render_native_field("Estimated Damage", dmg_str)

            # 📎 Other Details
            with st.container(border=True):
                st.markdown("#### 📎 Other Details")
                render_native_field("Claim Type", extracted.get("claim_type"))
                render_native_field("Attachments", extracted.get("attachments"))
                est = extracted.get("initial_estimate")
                est_str = f"${est:,.2f}" if isinstance(est, (int, float)) else est
                render_native_field("Initial Estimate", est_str)

        with col2:
            # Route Card (colored by recommended route status)
            with st.container(border=True):
                st.markdown("### 🔀 Recommended Route")
                route_upper = route.upper()
                if "FAST" in route_upper:
                    st.success(f"🟢 **{route_upper}**")
                elif "MANUAL" in route_upper:
                    st.warning(f"🟠 **{route_upper}**")
                elif "INVESTIGATION" in route_upper:
                    st.error(f"🔴 **{route_upper}**")
                elif "SPECIALIST" in route_upper:
                    st.info(f"🔵 **{route_upper}**")
                else:
                    st.info(f"⚪ **{route_upper}**")

                st.markdown(f"**Decision Explanation:**\n\n{reasoning}")

            # Missing Fields Card (pills/chips)
            if missing:
                with st.container(border=True):
                    st.markdown("### ⚠️ Missing Fields")
                    pills = " ".join([f"`{field}`" for field in missing])
                    st.markdown(pills)

            # Statistics Card
            with st.container(border=True):
                st.markdown("### 📊 Claim Completeness")
                non_null_fields = sum(1 for v in extracted.values() if v is not None and v != "")
                total_fields = len(extracted)
                completeness_pct = int((non_null_fields / total_fields) * 100)
                st.metric("Completeness Score", f"{completeness_pct}%")
                st.progress(non_null_fields / total_fields)

            # Reset Options Card
            with st.container(border=True):
                st.markdown("### 🧹 Actions")
                if st.button("🔄 Clear Current Results", key="clear_results_btn", use_container_width=True):
                    for key in ["file_name", "extracted_text", "is_ocr_triggered", "parsed_json", "final_output", "error_message", "is_truncated"]:
                        if key in st.session_state:
                            st.session_state[key] = None
                    st.rerun()

        # View Raw JSON Output Expander
        st.markdown("<br/>", unsafe_allow_html=True)
        with st.expander("📝 View Raw JSON Output", expanded=True):
            st.code(json.dumps(final_data, indent=2), language="json")

        # Center-aligned, wide download button
        st.markdown("---")
        col_btn_l, col_btn_m, col_btn_r = st.columns([1, 2, 1])
        with col_btn_m:
            json_payload = json.dumps(final_data, indent=2)
            st.download_button(
                label="📥 Download Structured JSON",
                data=json_payload,
                file_name=f"claim_pilot_route_{st.session_state.file_name.split('.')[0]}.json",
                mime="application/json",
                key="dl_payload_btn",
                use_container_width=True
            )

if __name__ == "__main__":
    main()
