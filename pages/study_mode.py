import streamlit as st
import math
from app.database.db_manager import DBManager
from app.services.tts_manager import TTSManager
from app.services.llm_client import LLMClient
from app.ui.study_dialog import trigger_study_dialog
from app.ui.sidebar import render_sidebar


# --- Initialization ---
st.set_page_config(page_title="Study Mode", layout="wide")
render_sidebar()  # Render custom sidebar

# Initialize core services
db = DBManager()
tts = TTSManager()
llm = LLMClient()

# --- Session State Initialization ---
if 'sort_col' not in st.session_state:
    st.session_state.sort_col = 'level'  # Default sort by Level
if 'sort_asc' not in st.session_state:
    st.session_state.sort_asc = False  # Default Descending (High to Low)
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1


# --- Callback Functions ---
def reset_pagination():
    """Reset to page 1 when filters change."""
    st.session_state.current_page = 1


def handle_sort(col_name):
    """Handle column header clicks for sorting."""
    if st.session_state.sort_col == col_name:
        st.session_state.sort_asc = not st.session_state.sort_asc
    else:
        st.session_state.sort_col = col_name
        # Default sort direction based on column type
        if col_name in ['level', 'freq']:
            st.session_state.sort_asc = False  # High to Low
        else:
            st.session_state.sort_asc = True  # A to Z
    st.session_state.current_page = 1


def prev_page():
    if st.session_state.current_page > 1:
        st.session_state.current_page -= 1


def next_page(total_pages):
    if st.session_state.current_page < total_pages:
        st.session_state.current_page += 1


# --- Global CSS Injection ---
st.markdown("""
    <style>
    [data-testid="column"] { display: flex; flex-direction: column; justify-content: center; }
    [data-testid="stPopover"] button { margin: 0 !important; }
    .stTextInput input { border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# Main View: Vocabulary List
# ==========================================
st.markdown("## Vocabulary List")

# 1. Filters Section
col_filt1, col_filt2 = st.columns(2)

with col_filt1:
    domains = db.get_all_domains()
    if not domains:
        st.warning("Please import data first.")
        st.stop()
    d_opts = {d["name"]: d["id"] for d in domains}
    sel_d_name = st.selectbox("Select Domain", list(d_opts.keys()), label_visibility="collapsed",
                              on_change=reset_pagination)
    sel_d_id = d_opts[sel_d_name]

with col_filt2:
    star_filter = st.selectbox(
        "Filter by Level",
        ["All Levels", "⭐ 1 Star", "⭐⭐ 2 Stars", "⭐⭐⭐ 3 Stars", "⭐⭐⭐⭐ 4 Stars", "⭐⭐⭐⭐⭐ 5 Stars"],
        label_visibility="collapsed",
        on_change=reset_pagination
    )

# 2. Search Bar
st.write("")
search_term = st.text_input(
    "Search terms",
    placeholder="🔍 Search for a term...",
    label_visibility="collapsed",
    on_change=reset_pagination
)

# 3. Data Fetching (Fetch all to memory)
terms_raw = db.get_terms_by_domain(sel_d_id, only_active=True)
if not terms_raw:
    st.info("No vocabulary found in this domain.")
    st.stop()

# Convert to list of dicts
terms = [dict(t) for t in terms_raw]

# 4. Filter Logic
if star_filter != "All Levels":
    target_stars = int(star_filter.split(" ")[1])
    terms = [t for t in terms if t.get('star_level', 1) == target_stars]

if search_term:
    terms = [t for t in terms if search_term.lower() in t['word'].lower()]

if not terms:
    st.info("No vocabulary matches the current criteria.")
    st.stop()

# 5. Sorting Logic
is_reverse = not st.session_state.sort_asc
if st.session_state.sort_col == 'word':
    terms.sort(key=lambda x: x['word'].lower(), reverse=is_reverse)
elif st.session_state.sort_col == 'freq':
    terms.sort(key=lambda x: x.get('frequency', 1), reverse=is_reverse)
elif st.session_state.sort_col == 'level':
    terms.sort(key=lambda x: x.get('star_level', 1), reverse=is_reverse)

# 6. Pagination Logic
ITEMS_PER_PAGE = 10
total_items = len(terms)
total_pages = math.ceil(total_items / ITEMS_PER_PAGE)

if st.session_state.current_page > total_pages:
    st.session_state.current_page = max(1, total_pages)

start_idx = (st.session_state.current_page - 1) * ITEMS_PER_PAGE
end_idx = start_idx + ITEMS_PER_PAGE
paginated_terms = terms[start_idx:end_idx]

# ==========================================
# List Headers & Content
# ==========================================

st.markdown("<hr style='margin: 0.5em 0; border: none; border-top: 2px solid #e5e7eb;'>", unsafe_allow_html=True)

# Column Headers
hc1, hc2, hc3, hc4, hc5 = st.columns([3, 1.5, 1.5, 1.5, 1.5])


def get_sort_icon(col_name):
    if st.session_state.sort_col == col_name:
        return " 🔼" if st.session_state.sort_asc else " 🔽"
    return ""


with hc1: st.button(f"WORD{get_sort_icon('word')}", key="sort_word", on_click=handle_sort, args=('word',),
                    use_container_width=True, type="tertiary")
with hc2: st.button(f"FREQUENCY{get_sort_icon('freq')}", key="sort_freq", on_click=handle_sort, args=('freq',),
                    use_container_width=True, type="tertiary")
with hc3: st.button(f"LEVEL{get_sort_icon('level')}", key="sort_level", on_click=handle_sort, args=('level',),
                    use_container_width=True, type="tertiary")

header_text_style = "<div style='color: #374151; font-weight: 600; font-size: 14px; text-align: center; padding-top: 4px;'>{}</div>"
with hc4: st.markdown(header_text_style.format("DEFINITION"), unsafe_allow_html=True)
with hc5: st.markdown(header_text_style.format("ACTION"), unsafe_allow_html=True)

st.markdown("<hr style='margin: 0.5em 0; border: none; border-top: 1px solid #e5e7eb;'>", unsafe_allow_html=True)

# 7. Render Data Rows
for i, t_dict in enumerate(paginated_terms):
    col1, col2, col3, col4, col5 = st.columns([3, 1.5, 1.5, 1.5, 1.5])

    # Calculate global index for navigation
    global_index = start_idx + i

    with col1:
        st.markdown(f"**{t_dict['word']}**")
    with col2:
        freq = t_dict.get('frequency', 1)
        st.markdown(
            f"<div style='text-align: center;'><span style='color: #4b5563; font-size: 0.95em;'>🔄 {freq}</span></div>",
            unsafe_allow_html=True)
    with col3:
        level = t_dict.get('star_level', 1)
        st.markdown(f"<div style='text-align: center;'>{'⭐' * level}</div>", unsafe_allow_html=True)
    with col4:
        if t_dict["definition"]:
            with st.popover("📖 View", use_container_width=True):
                st.markdown(f"**{t_dict['word']}**")
                st.write(t_dict["definition"])
        else:
            st.write("")
    with col5:
        # Trigger dialog by setting state and rerunning
        if st.button("🤿 Deep Dive", key=f"start_{t_dict['id']}", use_container_width=True):
            st.session_state.active_study_index = global_index
            st.rerun()

    st.markdown("<hr style='margin: 0.2em 0; border: none; border-top: 1px solid #f9fafb;'>", unsafe_allow_html=True)

# ==========================================
# 8. Pagination Controls
# ==========================================
st.write("")
pc1, pc2, pc3 = st.columns([1, 2, 1])

with pc1:
    st.button("⬅️ Prev", on_click=prev_page, disabled=(st.session_state.current_page == 1), use_container_width=True)
with pc2:
    st.markdown(
        f"<div style='text-align: center; color: #4b5563; margin-top: 8px;'>Page <b>{st.session_state.current_page}</b> of <b>{total_pages}</b> &nbsp;|&nbsp; Total: {total_items} terms</div>",
        unsafe_allow_html=True)
with pc3:
    st.button("Next ➡️", on_click=next_page, args=(total_pages,),
              disabled=(st.session_state.current_page == total_pages), use_container_width=True)

# ==========================================
# 9. Dialog Handler
# ==========================================
# If active_study_index exists, trigger the dialog
if 'active_study_index' in st.session_state:
    trigger_study_dialog(terms, db, tts, llm)