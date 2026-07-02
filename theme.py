import streamlit as st

def inject_theme_css() -> None:
    """Injects custom CSS to style Streamlit widgets."""
    from utils import get_custom_css
    st.markdown(get_custom_css(), unsafe_allow_html=True)
