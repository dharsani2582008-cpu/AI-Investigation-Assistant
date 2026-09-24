"""
AI Investigation Assistant — main entry point.

PHASE 1 scope:
- App shell + sidebar navigation
- Dashboard placeholder
- Evidence upload interface with basic validation

Later phases wire real functionality into the placeholder pages
without needing to change this file's navigation structure.
"""

import streamlit as st

from utils.config import APP_TITLE, APP_SUBTITLE, DISCLAIMER, ensure_data_dirs
from pages import dashboard, evidence, entities, relationships, assistant, reports

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Make sure data folders exist before anything else runs.
ensure_data_dirs()

PAGES = {
    "Dashboard": dashboard,
    "Evidence": evidence,
    "Entities": entities,
    "Relationships": relationships,
    "AI Assistant": assistant,
    "Reports": reports,
}


def main():
    with st.sidebar:
        st.title("🔍 " + APP_TITLE)
        st.caption(APP_SUBTITLE)
        st.divider()
        selection = st.radio("Navigate", list(PAGES.keys()), label_visibility="collapsed")
        st.divider()
        st.caption(DISCLAIMER)

    st.title(APP_TITLE)
    page_module = PAGES[selection]
    page_module.render()


if __name__ == "__main__":
    main()
