# app/ui/sidebar.py
import streamlit as st


def render_sidebar():
    st.markdown("""
        <style>
        /* Hide default Streamlit sidebar navigation */
        [data-testid="stSidebarNav"] {
            display: none;
        }

        /* Custom spacing for sidebar */
        [data-testid="stSidebar"] {
            padding-top: 2rem;
        }

        /* Base styling for all navigation links */
        div[data-testid="stPageLink-NavLink"] {
            padding: 0.6rem 1rem;
            border-radius: 0.5rem;
            margin-bottom: 0.5rem;
            transition: background-color 0.2s ease, transform 0.1s ease;
        }

        /* Hover effect for unselected links */
        div[data-testid="stPageLink-NavLink"]:hover {
            background-color: #f1f5f9;
            transform: translateX(2px);
        }

        /* Active (Selected) state styling */
        a[aria-current="page"] div[data-testid="stPageLink-NavLink"] {
            background-color: #e0f2fe !important;
            border-left: 5px solid #0ea5e9 !important;
            border-radius: 0 0.5rem 0.5rem 0;
            box-shadow: inset 1px 0px 3px rgba(0,0,0,0.05);
        }

        /* Active (Selected) text styling */
        a[aria-current="page"] p {
            color: #0369a1 !important;
            font-weight: 700 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### 🧠 DeepGloss")
        st.markdown("<hr style='margin-top:0.5rem; margin-bottom: 1.5rem;'>", unsafe_allow_html=True)

        # Link to pages
        st.page_link("main.py", label="Home", icon="🏠")
        st.page_link("pages/import_data.py", label="Import Data", icon="📥")
        st.page_link("pages/study_mode.py", label="Study Mode", icon="📖")
        st.page_link("pages/edit_vocabulary.py", label="Manage Vocabulary", icon="🛠️")