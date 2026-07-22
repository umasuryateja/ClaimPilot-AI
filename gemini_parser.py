import json
import re
import time
import logging
import google.generativeai as genai
from typing import Dict, Any, Tuple
from utils import GEMINI_MODEL, get_api_key
from prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# Character limit to stay within a reasonable token budget and cost constraints
# 40,000 characters is roughly 10,000 tokens, which easily fits any typical FNOL document.
MAX_CHAR_LIMIT = 40000

def extract_json_from_response(raw_text: str) -> dict:
    """Robustly extract a JSON object from Gemini's raw text response.
    
    No manual quote-boundary checks. Relies only on json.loads with
    markdown-fence stripping and brace-boundary isolation.
    """
    if not raw_text or not raw_text.strip():
        raise ValueError("Gemini returned an empty response.")

    text = raw_text.strip()

    # Strip markdown code fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        logger.error("No JSON object found. Raw response: %s", raw_text[:1000])
        raise ValueError("The AI response did not contain a valid JSON object.")

    json_candidate = text[start:end + 1]

    try:
        return json.loads(json_candidate)
    except json.JSONDecodeError as e:
        logger.error("JSON decode failed: %s. Candidate text: %s", e, json_candidate[:1000])
        raise ValueError(f"The AI response could not be parsed as JSON ({e}).")

def parse_fnol_document(document_text: str) -> Tuple[Dict[str, Any], bool]:
    """Sends the document text to Gemini, parses the returned JSON, and handles retries.
    
    Args:
        document_text (str): The raw text extracted from the FNOL.
        
    Returns:
        Tuple[Dict[str, Any], bool]: A tuple containing:
            - Dict[str, Any]: The extracted fields dictionary conforming to the schema.
            - bool: True if the document text was truncated due to size limits, False otherwise.
            
    Raises:
        ValueError: If JSON parsing fails after retries.
    """
    # 1. Check/Truncate document size
    is_truncated = False
    if len(document_text) > MAX_CHAR_LIMIT:
        logger.warning(f"Document text exceeds character limit ({len(document_text)} > {MAX_CHAR_LIMIT}). Truncating...")
        document_text = document_text[:MAX_CHAR_LIMIT] + "\n[TRUNCATED FOR SIZE CONSTRAINTS]"
        is_truncated = True
        
    # 2. Get API Key
    api_key = get_api_key()
    genai.configure(api_key=api_key)
    
    # 3. Formulate Prompt
    prompt = SYSTEM_PROMPT.replace("{document_text}", document_text)
    
    # 4. Invoke model with retry logic
    max_retries = 2
    backoff_factor = 2.0
    last_error = None
    
    # Try the configured model first, fallback to stable gemini-2.5-flash or gemini-3.5-flash if needed
    models_to_try = [GEMINI_MODEL, "gemini-2.5-flash", "gemini-3.5-flash"]
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            for attempt in range(max_retries + 1):
                try:
                    logger.info(f"Invoking Gemini model {model_name} (Attempt {attempt + 1}/{max_retries + 1})...")
                    
                    # Request JSON response format
                    response = model.generate_content(
                        prompt,
                        generation_config={
                            "temperature": 0.0,
                            "response_mime_type": "application/json"
                        }
                    )
                    
                    raw_response = response.text
                    
                    # Clean and parse JSON using the robust extractor
                    parsed_json = extract_json_from_response(raw_response)
                    
                    # Success
                    logger.info(f"Successfully extracted and parsed JSON from Gemini using {model_name}.")
                    return parsed_json, is_truncated
                    
                except ValueError as ve:
                    last_error = ve
                    logger.warning(f"Failed to parse JSON response on attempt {attempt + 1} with {model_name}: {str(ve)}")
                    if attempt < max_retries:
                        sleep_time = backoff_factor ** attempt
                        logger.info(f"Retrying in {sleep_time} seconds...")
                        time.sleep(sleep_time)
                except Exception as e:
                    last_error = e
                    err_msg = str(e)
                    logger.error(f"Gemini API error on attempt {attempt + 1} with {model_name}: {err_msg}")
                    
                    # If rate limit or quota exceeded, try retrying or let loop switch to fallback model
                    if attempt < max_retries:
                        sleep_time = backoff_factor ** attempt
                        logger.info(f"Retrying in {sleep_time} seconds...")
                        time.sleep(sleep_time)
        except Exception as outer_e:
            logger.warning(f"Failed to initialize or run calls using {model_name}: {str(outer_e)}")
            last_error = outer_e
            
    # If we get here, all attempts on all models failed.
    # Raise a clear error indicating quota limit so the pipeline can trigger heuristic fallback.
    err_str = str(last_error)
    if "429" in err_str or "quota" in err_str.lower():
        raise ValueError(
            "🔑 Gemini API Quota Exceeded (429 Error). "
            "You have hit the request limit for the free tier on all models."
        ) from last_error
        
    raise ValueError(f"The AI response could not be parsed as JSON (after retries). Last error: {last_error}")
