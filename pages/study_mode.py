import streamlit as st
import math
from app.database.db_manager import DBManager
from app.services.tts_manager import TTSManager
from app.services.llm_client import LLMClient
from app.ui.study_dialog import trigger_study_dialog

# --- Initialization ---
st.set_page_config(page_title="Study Mode", layout="wide")

# 初始化核心服务组件
db = DBManager()
tts = TTSManager()
llm = LLMClient()

# --- Session State 初始化 (用于排序和分页) ---
if 'sort_col' not in st.session_state:
    st.session_state.sort_col = 'word'  # 默认按单词排序
if 'sort_asc' not in st.session_state:
    st.session_state.sort_asc = True  # 默认升序
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1


# --- 回调函数 ---
def reset_pagination():
    """当切换领域、筛选条件或搜索时，重置回第一页"""
    st.session_state.current_page = 1


def handle_sort(col_name):
    """处理表头点击排序的逻辑"""
    if st.session_state.sort_col == col_name:
        # 如果点击的是当前排序列，切换升降序
        st.session_state.sort_asc = not st.session_state.sort_asc
    else:
        # 如果点击了新列，设为该列并默认升序
        st.session_state.sort_col = col_name
        st.session_state.sort_asc = True
    # 排序改变时，重置到第一页
    st.session_state.current_page = 1


def prev_page():
    if st.session_state.current_page > 1:
        st.session_state.current_page -= 1


def next_page(total_pages):
    if st.session_state.current_page < total_pages:
        st.session_state.current_page += 1


# 注入全局 CSS：压缩间距 + 强制垂直居中 + 扁平化表头按钮
st.markdown("""
    <style>
    /* 强制所有列内容垂直居中对齐 */
    [data-testid="column"] {
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    /* 隐藏 popover 按钮的默认 margin */
    [data-testid="stPopover"] button {
        margin: 0 !important;
    }
    /* 搜索框微调 */
    .stTextInput input {
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# Main View: Vocabulary List
# ==========================================
st.markdown("## Vocabulary List")

# 1. 顶部过滤区 (Dropdowns)
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

# 2. 搜索框 (实时联动，输入时重置分页)
st.write("")  # 小间距
search_term = st.text_input(
    "Search terms",
    placeholder="🔍 Search for a term...",
    label_visibility="collapsed",
    on_change=reset_pagination
)

# 3. 从数据库获取数据 (全部获取到内存)
terms = db.get_terms_by_domain(sel_d_id)
if not terms:
    st.info("No vocabulary found in this domain.")
    st.stop()

# 转换为标准字典列表
terms = [dict(t) for t in terms]

# 4. 应用 过滤 & 搜索 逻辑
if star_filter != "All Levels":
    target_stars = int(star_filter.split(" ")[1])
    terms = [t for t in terms if t.get('star_level', 1) == target_stars]

if search_term:
    terms = [t for t in terms if search_term.lower() in t['word'].lower()]

if not terms:
    st.info("No vocabulary matches the current criteria.")
    st.stop()

# 5. 应用排序逻辑 (内存排序)
is_reverse = not st.session_state.sort_asc
if st.session_state.sort_col == 'word':
    terms.sort(key=lambda x: x['word'].lower(), reverse=is_reverse)
elif st.session_state.sort_col == 'freq':
    terms.sort(key=lambda x: x.get('frequency', 1), reverse=is_reverse)
elif st.session_state.sort_col == 'level':
    terms.sort(key=lambda x: x.get('star_level', 1), reverse=is_reverse)

# 6. 分页计算逻辑
ITEMS_PER_PAGE = 10  # 每页显示的单词数量
total_items = len(terms)
total_pages = math.ceil(total_items / ITEMS_PER_PAGE)

# 防止筛选后页码越界
if st.session_state.current_page > total_pages:
    st.session_state.current_page = max(1, total_pages)

start_idx = (st.session_state.current_page - 1) * ITEMS_PER_PAGE
end_idx = start_idx + ITEMS_PER_PAGE
paginated_terms = terms[start_idx:end_idx]  # 切片拿到当前页的数据

# ==========================================
# 渲染表头 & 列表区
# ==========================================

st.markdown("<hr style='margin: 0.5em 0; border: none; border-top: 2px solid #e5e7eb;'>", unsafe_allow_html=True)

# ✅ 新增：可点击的列名表头 (Headers)
hc1, hc2, hc3, hc4, hc5 = st.columns([3, 1.5, 1.5, 1.5, 1.5])


def get_sort_icon(col_name):
    if st.session_state.sort_col == col_name:
        return " 🔼" if st.session_state.sort_asc else " 🔽"
    return ""


with hc1:
    st.button(f"WORD{get_sort_icon('word')}", key="sort_word", on_click=handle_sort, args=('word',),
              use_container_width=True, type="tertiary")
with hc2:
    st.button(f"FREQUENCY{get_sort_icon('freq')}", key="sort_freq", on_click=handle_sort, args=('freq',),
              use_container_width=True, type="tertiary")
with hc3:
    st.button(f"LEVEL{get_sort_icon('level')}", key="sort_level", on_click=handle_sort, args=('level',),
              use_container_width=True, type="tertiary")

header_text_style = "<div style='color: #374151; font-weight: 600; font-size: 14px; text-align: center; padding-top: 4px;'>{}</div>"
with hc4:
    st.markdown(header_text_style.format("DEFINITION"), unsafe_allow_html=True)
with hc5:
    st.markdown(header_text_style.format("ACTION"), unsafe_allow_html=True)

st.markdown("<hr style='margin: 0.5em 0; border: none; border-top: 1px solid #e5e7eb;'>", unsafe_allow_html=True)

# 7. 渲染当前页的数据行
for t_dict in paginated_terms:
    col1, col2, col3, col4, col5 = st.columns([3, 1.5, 1.5, 1.5, 1.5])

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
        if st.button("⚡ Practice", key=f"start_{t_dict['id']}", use_container_width=True):
            trigger_study_dialog(t_dict['id'], t_dict['word'], db, tts, llm)

    st.markdown("<hr style='margin: 0.2em 0; border: none; border-top: 1px solid #f9fafb;'>", unsafe_allow_html=True)

# ==========================================
# 8. 底部渲染：分页控制器
# ==========================================
st.write("")  # 增加一点空隙
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