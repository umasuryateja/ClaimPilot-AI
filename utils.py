import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Resolve parent directory to force load .env from the root
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Setup logging
def setup_logging() -> logging.Logger:
    """Configures and returns the application logger."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger("ClaimPilotAI")
    logger.setLevel(logging.INFO)
    return logger

logger = setup_logging()

# Constants
GEMINI_MODEL: str = "gemini-2.5-flash"

def get_api_key() -> str:
    """Retrieves the Gemini API key from the environment.
    
    Raises:
        ValueError: If GEMINI_API_KEY is not set.
    """
    # Force reload dotenv dynamically so changes to .env are picked up without restarting the server
    load_dotenv(override=True)
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        logger.error("GEMINI_API_KEY environment variable is not set.")
        raise ValueError(
            "GEMINI_API_KEY is missing. Please create a '.env' file in the root "
            "directory and add: GEMINI_API_KEY=your_actual_api_key"
        )
    return key

def get_custom_css() -> str:
    """Returns custom CSS to inject into Streamlit for styling."""
    return """
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        /* Apply fonts and override defaults globally to main elements without breaking widgets */
        *, *:before, *:after {
            box-sizing: border-box !important;
        }

        html, body, .stMarkdown, p, h1, h2, h3, h4, h5, h6, td {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }

        /* Container centering and max-width */
        .block-container {
            max-width: 900px !important;
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
        }

        /* Hide default file uploader instructions/helper text */
        [data-testid="stFileUploader"] section small {
            display: none !important;
        }

        /* Hide drag-and-drop file uploader icon to prevent overlaps */
        [data-testid="stFileUploader"] svg {
            display: none !important;
        }

        /* Header Banner Styling */
        .header-banner {
            background-color: #0F1B2B;
            padding: 2.2rem;
            border-radius: 8px;
            margin-bottom: 2.2rem;
            color: #ffffff;
            border-left: 5px solid #D98E04;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
        .banner-title {
            color: #ffffff !important;
            font-weight: 700 !important;
            font-size: 2.4rem !important;
            margin: 0 !important;
            line-height: 1.2 !important;
        }
        .banner-subtitle {
            color: #94A3B8 !important;
            font-size: 1.1rem !important;
            font-weight: 400 !important;
            margin: 0.6rem 0 0 0 !important;
        }

        /* Quote box styling for reasoning */
        .reasoning-box {
            background-color: #F8FAFC;
            border-left: 4px solid #D98E04;
            padding: 1rem;
            border-radius: 0 8px 8px 0;
            font-style: italic;
            color: #334155;
            margin-top: 0.5rem;
        }
    </style>
    """
