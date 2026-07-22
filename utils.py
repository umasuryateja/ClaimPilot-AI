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
GEMINI_MODEL: str = "gemini-2.0-flash"

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
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        /* Global Reset & Base Setup */
        *, *:before, *:after {
            box-sizing: border-box !important;
        }

        /* Framer-style Background Canvas */
        .framer-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-color: #050508 !important;
            z-index: -10;
            overflow: hidden;
            pointer-events: none;
        }

        /* Fine Grid Layer */
        .framer-grid {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                linear-gradient(rgba(255, 255, 255, 0.012) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.012) 1px, transparent 1px);
            background-size: 50px 50px;
            background-position: center;
            opacity: 0.9;
            mask-image: radial-gradient(circle at 50% 50%, black 50%, transparent 100%);
            -webkit-mask-image: radial-gradient(circle at 50% 50%, black 50%, transparent 100%);
        }

        /* Dynamic Blurry Orbs */
        .framer-orb {
            position: absolute;
            border-radius: 50%;
            filter: blur(130px);
            -webkit-filter: blur(130px);
            opacity: 0.38;
            mix-blend-mode: screen;
            pointer-events: none;
            will-change: transform;
        }

        .orb-emerald {
            width: 550px;
            height: 550px;
            background: radial-gradient(circle, rgba(16, 185, 129, 0.3) 0%, transparent 75%);
            top: -120px;
            left: -120px;
            animation: floatOrb1 25s ease-in-out infinite alternate;
        }

        .orb-violet {
            width: 650px;
            height: 650px;
            background: radial-gradient(circle, rgba(124, 58, 237, 0.28) 0%, transparent 75%);
            bottom: -180px;
            right: -120px;
            animation: floatOrb2 30s ease-in-out infinite alternate;
        }

        .orb-gold {
            width: 480px;
            height: 480px;
            background: radial-gradient(circle, rgba(245, 158, 11, 0.18) 0%, transparent 75%);
            top: 35%;
            left: 15%;
            animation: floatOrb3 28s ease-in-out infinite alternate;
        }

        /* Subtle Noise Overlay */
        .framer-noise {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.015'/%3E%3C/svg%3E");
            opacity: 0.7;
            z-index: 1;
            pointer-events: none;
        }

        @keyframes floatOrb1 {
            0% { transform: translate(0, 0) scale(1); }
            50% { transform: translate(100px, 70px) scale(1.1); }
            100% { transform: translate(-30px, 140px) scale(0.95); }
        }

        @keyframes floatOrb2 {
            0% { transform: translate(0, 0) scale(1); }
            50% { transform: translate(-120px, -80px) scale(0.9); }
            100% { transform: translate(60px, 50px) scale(1.05); }
        }

        @keyframes floatOrb3 {
            0% { transform: translate(0, 0) scale(1); }
            50% { transform: translate(80px, -100px) scale(1.15); }
            100% { transform: translate(-60px, 30px) scale(0.98); }
        }

        .stApp {
            background-color: transparent !important;
            color: #FFFFFF !important;
        }

        [data-testid="stAppViewContainer"] {
            background: transparent !important;
        }

        [data-testid="stHeader"] {
            background: transparent !important;
        }

        /* Typography */
        html, body, p, td, li, .stMarkdown {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
            color: #B8B8C5;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }

        h1, h2, h3, h4, h5, h6, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
            font-family: 'Inter', sans-serif !important;
            color: #FFFFFF !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em !important;
        }

        /* Main Container Centering & Padding */
        .block-container {
            max-width: 980px !important;
            padding-top: 2rem !important;
            padding-bottom: 3.5rem !important;
        }

        /* Hero Header Glass Banner */
        .header-banner {
            background: rgba(255, 255, 255, 0.02) !important;
            backdrop-filter: blur(24px) !important;
            -webkit-backdrop-filter: blur(24px) !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            border-radius: 16px !important;
            padding: 2.2rem 2.5rem !important;
            margin-bottom: 2rem !important;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
            position: relative;
            overflow: hidden;
        }
        .header-banner::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, #10B981, #7C3AED, #FBBF24);
        }
        .banner-title {
            font-size: 2.5rem !important;
            font-weight: 800 !important;
            margin: 0 !important;
            line-height: 1.2 !important;
            background: linear-gradient(135deg, #FFFFFF 0%, #10B981 40%, #7C3AED 100%);
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            letter-spacing: -0.03em !important;
        }
        .banner-subtitle {
            color: #B8B8C5 !important;
            font-size: 1.05rem !important;
            font-weight: 400 !important;
            margin-top: 0.5rem !important;
            letter-spacing: 0.01em;
        }

        /* Native Streamlit Container Glassmorphism Override */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255, 255, 255, 0.03) !important;
            backdrop-filter: blur(20px) !important;
            -webkit-backdrop-filter: blur(20px) !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            border-radius: 16px !important;
            padding: 1.3rem 1.45rem !important;
            margin-bottom: 1.2rem !important;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.04) !important;
            transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: rgba(16, 185, 129, 0.28) !important;
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.5), 0 0 25px rgba(16, 185, 129, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
            transform: translateY(-3px) scale(1.005);
        }

        /* Custom Key-Value Field Rows */
        .field-pair {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.6rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            gap: 16px;
        }
        .field-pair:last-child {
            border-bottom: none;
        }
        .field-label {
            font-size: 0.88rem;
            font-weight: 500;
            color: #B8B8C5;
            letter-spacing: 0.01em;
            flex-shrink: 0;
        }
        .field-value {
            font-size: 0.92rem;
            font-weight: 600;
            color: #FFFFFF;
            text-align: right;
            word-break: break-word;
        }
        .field-value-empty {
            color: rgba(184, 184, 197, 0.4);
            font-weight: 400;
            font-style: italic;
        }

        /* Glowing Neon Badges for Route Decision */
        .badge-wrapper {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 0.8rem 0;
        }
        .neon-badge {
            font-size: 0.98rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            padding: 0.75rem 1.4rem;
            border-radius: 10px;
            display: inline-flex;
            align-items: center;
            gap: 0.6rem;
            transition: all 0.3s ease;
        }
        .badge-fasttrack {
            color: #10B981 !important;
            background: rgba(16, 185, 129, 0.12) !important;
            border: 1px solid rgba(16, 185, 129, 0.4) !important;
            box-shadow: 0 0 20px rgba(16, 185, 129, 0.25), inset 0 0 10px rgba(16, 185, 129, 0.1) !important;
        }
        .badge-manual {
            color: #F59E0B !important;
            background: rgba(245, 158, 11, 0.12) !important;
            border: 1px solid rgba(245, 158, 11, 0.4) !important;
            box-shadow: 0 0 20px rgba(245, 158, 11, 0.25), inset 0 0 10px rgba(245, 158, 11, 0.1) !important;
        }
        .badge-investigation {
            color: #EF4444 !important;
            background: rgba(239, 68, 68, 0.12) !important;
            border: 1px solid rgba(239, 68, 68, 0.4) !important;
            box-shadow: 0 0 20px rgba(239, 68, 68, 0.25), inset 0 0 10px rgba(239, 68, 68, 0.1) !important;
        }
        .badge-specialist {
            color: #A78BFA !important;
            background: rgba(124, 58, 237, 0.15) !important;
            border: 1px solid rgba(124, 58, 237, 0.4) !important;
            box-shadow: 0 0 20px rgba(124, 58, 237, 0.25), inset 0 0 10px rgba(124, 58, 237, 0.1) !important;
        }
        .badge-standard {
            color: #D1D5DB !important;
            background: rgba(156, 163, 175, 0.12) !important;
            border: 1px solid rgba(156, 163, 175, 0.3) !important;
            box-shadow: 0 0 15px rgba(156, 163, 175, 0.15) !important;
        }

        /* Missing Field Badges */
        .badge-missing {
            display: inline-block;
            font-size: 0.8rem;
            font-weight: 600;
            background: rgba(239, 68, 68, 0.12);
            color: #EF4444;
            border: 1px solid rgba(239, 68, 68, 0.3);
            padding: 0.3rem 0.6rem;
            border-radius: 6px;
            margin: 0.2rem 0.15rem;
            box-shadow: 0 0 10px rgba(239, 68, 68, 0.15);
        }

        /* Reasoning Box */
        .reasoning-box {
            background: rgba(255, 255, 255, 0.03);
            border-left: 3px solid #10B981;
            border-radius: 0 8px 8px 0;
            padding: 0.9rem 1.1rem;
            font-size: 0.88rem;
            color: #B8B8C5;
            line-height: 1.65;
            margin-top: 0.8rem;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }

        /* Streamlit File Uploader Glassmorphic Fix (Prevents Double Text Bug) */
        [data-testid="stFileUploader"] label,
        [data-testid="stFileUploader"] [data-testid="stWidgetLabel"] {
            display: none !important;
        }
        [data-testid="stFileUploader"] {
            background: rgba(255, 255, 255, 0.03) !important;
            border: 2px dashed rgba(16, 185, 129, 0.35) !important;
            border-radius: 12px !important;
            padding: 1.2rem !important;
            transition: all 0.3s ease !important;
        }
        [data-testid="stFileUploader"]:hover {
            border-color: #10B981 !important;
            box-shadow: 0 0 20px rgba(16, 185, 129, 0.2) !important;
        }
        [data-testid="stFileUploader"] section small {
            display: none !important;
        }
        [data-testid="stFileUploader"] svg {
            display: none !important;
        }

        /* Buttons Styling */
        .stButton > button {
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            font-size: 0.92rem !important;
            background: linear-gradient(135deg, #10B981 0%, #7C3AED 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.65rem 1.3rem !important;
            box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3) !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #059669 0%, #6D28D9 100%) !important;
            box-shadow: 0 6px 22px rgba(124, 58, 237, 0.4) !important;
            transform: translateY(-2px) !important;
        }
        .stDownloadButton > button {
            font-family: 'Inter', sans-serif !important;
            font-weight: 700 !important;
            font-size: 0.92rem !important;
            background: linear-gradient(135deg, #7C3AED 0%, #FBBF24 100%) !important;
            color: #0B0B0F !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.7rem 1.4rem !important;
            box-shadow: 0 4px 16px rgba(124, 58, 237, 0.35) !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }
        .stDownloadButton > button:hover {
            box-shadow: 0 6px 24px rgba(251, 191, 36, 0.45) !important;
            transform: translateY(-2px) !important;
        }

        /* Metric & Progress Bar Styling */
        [data-testid="stMetricValue"] {
            color: #10B981 !important;
            font-weight: 700 !important;
            font-size: 1.8rem !important;
            text-shadow: 0 0 15px rgba(16, 185, 129, 0.35) !important;
        }
        [data-testid="stMetricLabel"] {
            color: #B8B8C5 !important;
        }
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #10B981 0%, #7C3AED 50%, #FBBF24 100%) !important;
            border-radius: 10px !important;
            box-shadow: 0 0 12px rgba(16, 185, 129, 0.4) !important;
        }

        /* Code Block & Expander Styling */
        [data-testid="stExpander"] {
            background: rgba(255, 255, 255, 0.03) !important;
            backdrop-filter: blur(16px) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 10px !important;
        }
        pre, code {
            font-family: 'JetBrains Mono', monospace !important;
            border-radius: 8px !important;
            color: #FFFFFF !important;
        }

        /* Sidebar Glassmorphism & Custom Styling */
        [data-testid="stSidebar"] {
            background-color: rgba(10, 10, 14, 0.95) !important;
            backdrop-filter: blur(24px) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
        }
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] .stMarkdown {
            color: #E2E8F0 !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] {
            background-color: rgba(255, 255, 255, 0.04) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 8px !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] * {
            color: #E2E8F0 !important;
        }

        /* Streamlit Selectbox dropdown popup list styling */
        div[role="listbox"] {
            background-color: #0F0F14 !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 8px !important;
        }
        div[role="option"] {
            color: #E2E8F0 !important;
            background-color: transparent !important;
        }
        div[role="option"]:hover, div[role="option"][aria-selected="true"] {
            background-color: rgba(16, 185, 129, 0.15) !important;
            color: #10B981 !important;
    </style>
    """



