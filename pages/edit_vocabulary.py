import streamlit as st
import streamlit.components.v1 as components
import math
from app.database.db_manager import DBManager
from app.ui.sidebar import render_sidebar

# --- Initialization ---
st.set_page_config(page_title="Manage Vocabulary", layout="wide")
render_sidebar()

st.title("🛠️ Manage Vocabulary")
db = DBManager()

# --- CSS Injection (Targeting Exact iOS Colors and Layout) ---
st.markdown("""
    <style>
    [data-testid="column"] { 
        display: flex; 
        flex-direction: column; 
        justify-content: center; 
    }

    /* Definition Text Area: hidden by default, expands via JS */
    div[data-testid="stTextArea"] textarea {
        background-color: transparent !important;
        border: 1px solid transparent !important;
        box-shadow: none !important;
        resize: none !important;
        overflow: hidden !important;
        height: 38px !important;
        min-height: 38px !important;
        padding-top: 8px !important;
        color: #4b5563 !important;
        transition: all 0.25s ease !important;
        cursor: pointer;
        line-height: 1.2;
    }
    </style>
""", unsafe_allow_html=True)

# --- Session State ---
if 'edit_sort_col' not in st.session_state:
    st.session_state.edit_sort_col = 'level'
if 'edit_sort_asc' not in st.session_state:
    st.session_state.edit_sort_asc = False
if 'edit_page' not in st.session_state:
    st.session_state.edit_page = 1


def reset_edit_page():
    st.session_state.edit_page = 1


def handle_edit_sort(col_name):
    if st.session_state.edit_sort_col == col_name:
        st.session_state.edit_sort_asc = not st.session_state.edit_sort_asc
    else:
        st.session_state.edit_sort_col = col_name
        st.session_state.edit_sort_asc = False if col_name in ['level', 'freq'] else True
    st.session_state.edit_page = 1


def prev_page():
    if st.session_state.edit_page > 1:
        st.session_state.edit_page -= 1


def next_page(total_pages):
    if st.session_state.edit_page < total_pages:
        st.session_state.edit_page += 1


# ==========================================
# 1. Filters Section
# ==========================================
col_filt1, col_filt2 = st.columns(2)
with col_filt1:
    domains = db.get_all_domains()
    if not domains:
        st.warning("Please import data first.")
        st.stop()
    d_opts = {d["name"]: d["id"] for d in domains}
    sel_d_name = st.selectbox("Select Domain", list(d_opts.keys()), label_visibility="collapsed",
                              on_change=reset_edit_page)
    sel_d_id = d_opts[sel_d_name]

with col_filt2:
    star_filter = st.selectbox(
        "Filter by Level",
        ["All Levels", "⭐ 1 Star", "⭐⭐ 2 Stars", "⭐⭐⭐ 3 Stars", "⭐⭐⭐⭐ 4 Stars", "⭐⭐⭐⭐⭐ 5 Stars"],
        label_visibility="collapsed", on_change=reset_edit_page
    )

st.write("")
search_term = st.text_input("Search terms", placeholder="🔍 Search for a term to edit...", label_visibility="collapsed",
                            on_change=reset_edit_page)

# ==========================================
# 2. Data Fetching & Global Sorting
# ==========================================
terms_raw = db.get_terms_by_domain(sel_d_id, only_active=False)
if not terms_raw:
    st.info("No vocabulary found in this domain.")
    st.stop()

terms = [dict(t) for t in terms_raw]

if star_filter != "All Levels":
    target_stars = int(star_filter.split(" ")[1])
    terms = [t for t in terms if t.get('star_level', 1) == target_stars]

if search_term:
    terms = [t for t in terms if search_term.lower() in t['word'].lower()]

if not terms:
    st.info("No vocabulary matches your search.")
    st.stop()

# Sorting Logic
is_reverse = not st.session_state.edit_sort_asc
if st.session_state.edit_sort_col == 'word':
    terms.sort(key=lambda x: x['word'].lower(), reverse=is_reverse)
elif st.session_state.edit_sort_col == 'freq':
    terms.sort(key=lambda x: x.get('frequency', 1), reverse=is_reverse)
elif st.session_state.edit_sort_col == 'level':
    terms.sort(key=lambda x: x.get('star_level', 1), reverse=is_reverse)

# ==========================================
# 3. Pagination Logic
# ==========================================
ITEMS_PER_PAGE = 10
total_items = len(terms)
total_pages = math.ceil(total_items / ITEMS_PER_PAGE) if total_items > 0 else 1
if st.session_state.edit_page > total_pages: st.session_state.edit_page = max(1, total_pages)

start_idx = (st.session_state.edit_page - 1) * ITEMS_PER_PAGE
paginated_terms = terms[start_idx: start_idx + ITEMS_PER_PAGE]

# ==========================================
# 4. List Rendering
# ==========================================
st.markdown("<hr style='margin: 0.5em 0; border: none; border-top: 2px solid #e5e7eb;'>", unsafe_allow_html=True)
hc1, hc2, hc3, hc4, hc5 = st.columns([1, 2.5, 1.2, 1.3, 3])


def get_sort_icon(col_name):
    if st.session_state.edit_sort_col == col_name:
        return " 🔼" if st.session_state.edit_sort_asc else " 🔽"
    return ""


header_text_style = "<div style='color: #374151; font-weight: 600; font-size: 13px; text-align: center;'>{}</div>"
with hc1: st.markdown(header_text_style.format("ENABLE"), unsafe_allow_html=True)
with hc2: st.button(f"WORD{get_sort_icon('word')}", key="es_w", on_click=handle_edit_sort, args=('word',),
                    use_container_width=True, type="tertiary")
with hc3: st.button(f"FREQ{get_sort_icon('freq')}", key="es_f", on_click=handle_edit_sort, args=('freq',),
                    use_container_width=True, type="tertiary")
with hc4: st.button(f"LEVEL{get_sort_icon('level')}", key="es_l", on_click=handle_edit_sort, args=('level',),
                    use_container_width=True, type="tertiary")
with hc5: st.markdown(header_text_style.format("DEFINITION (DOUBLE CLICK TO EDIT)"), unsafe_allow_html=True)

st.markdown("<hr style='margin: 0.5em 0; border: none; border-top: 1px solid #e5e7eb;'>", unsafe_allow_html=True)

# ==========================================
# 5. Form & Data Rows
# ==========================================
with st.form("edit_list_form", clear_on_submit=False):
    for i, t_dict in enumerate(paginated_terms):
        tid = t_dict['id']
        c1, c2, c3, c4, c5 = st.columns([1, 2.5, 1.2, 1.3, 3])

        with c1:
            st.toggle("Enable", value=bool(t_dict['is_active']), key=f"edit_active_{tid}", label_visibility="collapsed")
        with c2:
            st.text_input("Word", value=t_dict['word'], key=f"edit_word_{tid}", label_visibility="collapsed")
        with c3:
            freq = t_dict.get('frequency', 1)
            st.markdown(
                f"<div style='text-align: center;'><span style='color: #4b5563; font-size: 0.95em;'>🔄 {freq}</span></div>",
                unsafe_allow_html=True)
        with c4:
            star_options = {1: "⭐", 2: "⭐⭐", 3: "⭐⭐⭐", 4: "⭐⭐⭐⭐", 5: "⭐⭐⭐⭐⭐"}
            st.selectbox("Level", options=[1, 2, 3, 4, 5], format_func=lambda x: star_options[x],
                         index=t_dict.get('star_level', 1) - 1, key=f"edit_level_{tid}", label_visibility="collapsed")
        with c5:
            st.text_area("Def", value=t_dict['definition'] if t_dict['definition'] else "", key=f"edit_def_{tid}",
                         label_visibility="collapsed")

        st.markdown("<hr style='margin: 0.2em 0; border: none; border-top: 1px solid #f9fafb;'>",
                    unsafe_allow_html=True)

    submit_btn = st.form_submit_button("💾 Save Current Page", type="primary")

    if submit_btn:
        updates = []
        for t in paginated_terms:
            tid = t['id']
            updates.append({
                'id': tid,
                'is_active': 1 if st.session_state[f"edit_active_{tid}"] else 0,
                'word': st.session_state[f"edit_word_{tid}"].strip(),
                'star_level': st.session_state[f"edit_level_{tid}"],
                'definition': st.session_state[f"edit_def_{tid}"].strip()
            })
        db.bulk_update_terms(updates)
        st.toast("✅ Changes saved successfully!", icon="✅")
        st.rerun()

# ==========================================
# 6. Pagination UI Controls
# ==========================================
st.write("")
pc1, pc2, pc3 = st.columns([1, 2, 1])
with pc1:
    st.button("⬅️ Prev", on_click=prev_page, disabled=(st.session_state.edit_page == 1), use_container_width=True)
with pc2:
    st.markdown(
        f"<div style='text-align: center; color: #4b5563; margin-top: 8px;'>Page <b>{st.session_state.edit_page}</b> of <b>{total_pages}</b> &nbsp;|&nbsp; Total: {total_items} terms</div>",
        unsafe_allow_html=True)
with pc3:
    st.button("Next ➡️", on_click=next_page, args=(total_pages,), disabled=(st.session_state.edit_page == total_pages),
              use_container_width=True)

# ==========================================
# 7. JS Injection for Double-Click Edit Logic
# ==========================================
components.html("""
<script>
    try {
        const doc = window.parent.document;

        // Apply Double-Click Logic to TextAreas
        function secureTextAreas() {
            const textAreas = doc.querySelectorAll('div[data-testid="stTextArea"] textarea');
            textAreas.forEach(ta => {
                if (!ta.dataset.dblMapped) {
                    ta.dataset.dblMapped = "true";

                    // Initial State: Locked & Label-like
                    ta.setAttribute('readonly', 'true');
                    ta.style.setProperty('background-color', 'transparent', 'important');
                    ta.style.setProperty('border', '1px solid transparent', 'important');
                    ta.style.setProperty('box-shadow', 'none', 'important');
                    ta.style.setProperty('resize', 'none', 'important');
                    ta.style.setProperty('height', '38px', 'important');
                    ta.style.setProperty('min-height', '38px', 'important');
                    ta.style.setProperty('overflow', 'hidden', 'important');
                    ta.style.setProperty('cursor', 'pointer', 'important');

                    // Double Click to Unlock & Expand
                    ta.addEventListener('dblclick', function(e) {
                        e.preventDefault();
                        this.removeAttribute('readonly');
                        this.style.setProperty('background-color', '#ffffff', 'important');
                        this.style.setProperty('border', '1px solid #3b82f6', 'important');
                        this.style.setProperty('box-shadow', '0 4px 6px -1px rgb(0 0 0 / 0.1)', 'important');
                        this.style.setProperty('resize', 'vertical', 'important');
                        this.style.setProperty('height', '120px', 'important');
                        this.style.setProperty('min-height', '120px', 'important');
                        this.style.setProperty('overflow', 'auto', 'important');
                        this.style.setProperty('cursor', 'text', 'important');
                        this.style.setProperty('position', 'relative', 'important');
                        this.style.setProperty('z-index', '10', 'important');
                        this.focus();
                    });

                    // Blur (click outside) to Lock again
                    ta.addEventListener('blur', function() {
                        this.setAttribute('readonly', 'true');
                        this.style.setProperty('background-color', 'transparent', 'important');
                        this.style.setProperty('border', '1px solid transparent', 'important');
                        this.style.setProperty('box-shadow', 'none', 'important');
                        this.style.setProperty('resize', 'none', 'important');
                        this.style.setProperty('height', '38px', 'important');
                        this.style.setProperty('min-height', '38px', 'important');
                        this.style.setProperty('overflow', 'hidden', 'important');
                        this.style.setProperty('cursor', 'pointer', 'important');
                        this.style.setProperty('position', 'static', 'important');
                        this.style.setProperty('z-index', '1', 'important');
                    });
                }
            });
        }

        function runOverrides() {
            secureTextAreas();
        }
        runOverrides();
        var observer = new MutationObserver(runOverrides);
        observer.observe(doc.body, { childList: true, subtree: true });

    } catch (e) {
        console.error("DeepGloss UI Override Error:", e);
    }
</script>
""", height=0, width=0)