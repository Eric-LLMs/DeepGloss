import streamlit as st
import os
from app.database.db_manager import DBManager
from app.services.tts_manager import TTSManager
from app.services.llm_client import LLMClient  # ✅ 1. 改为通用引用

# --- 初始化 ---
st.set_page_config(page_title="深度学习模式", layout="wide")
db = DBManager()
tts = TTSManager()
llm = LLMClient()  # ✅ 2. 通用初始化

# --- Session State 管理 ---
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'list'
if 'current_term_id' not in st.session_state:
    st.session_state.current_term_id = None


# --- 辅助函数 ---
def go_to_list():
    st.session_state.view_mode = 'list'
    st.session_state.current_term_id = None


def go_to_detail(term_id):
    st.session_state.view_mode = 'detail'
    st.session_state.current_term_id = term_id


# ✅ 3. 新增回调函数 (解决 StreamlitAPIException 的关键)
# 这个函数会在点击按钮后、页面重新渲染前执行，所以可以安全地修改 session_state
def ai_parse_callback(word, context, target_key):
    try:
        res = llm.explain_term_in_context(word, context)
        if isinstance(res, dict) and 'translation' in res:
            # 更新输入框绑定的 key
            st.session_state[target_key] = res['translation']
            # 将解释暂存，以便在页面刷新后显示
            st.session_state[f"msg_{target_key}"] = res['explanation']
    except Exception as e:
        st.session_state[f"err_{target_key}"] = str(e)


# ==========================================
# 视图 1: 词汇列表页
# ==========================================
if st.session_state.view_mode == 'list':
    st.title("📚 词汇列表")

    domains = db.get_all_domains()
    if not domains:
        st.warning("请先去导入数据")
        st.stop()

    d_opts = {d['name']: d['id'] for d in domains}
    sel_d_name = st.selectbox("选择领域", list(d_opts.keys()))
    sel_d_id = d_opts[sel_d_name]

    terms = db.get_terms_by_domain(sel_d_id)
    if not terms:
        st.info("该领域下暂无词汇")
        st.stop()

    st.markdown("---")
    for t in terms:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"### {t['word']}")
            if t['definition']:
                st.caption(t['definition'])
        with col2:
            if st.button("🚀 学习", key=f"start_{t['id']}", use_container_width=True):
                go_to_detail(t['id'])
                st.rerun()
        st.divider()

# ==========================================
# 视图 2: 详细学习页
# ==========================================
elif st.session_state.view_mode == 'detail':
    t_id = st.session_state.current_term_id
    term_data = db.get_term_by_id(t_id)
    word = term_data['word']

    if st.button("← 返回列表"):
        go_to_list()
        st.rerun()

    st.title(f"🔤 {word}")

    # --- A. 词汇信息区 ---
    st.subheader("1. 词汇信息")
    col_t1, col_t2 = st.columns([1, 1])

    with col_t1:
        st.markdown("**读音 (TTS)**")
        c1, c2 = st.columns(2)
        has_local_audio = bool(term_data['audio_hash'])
        if c1.button("📂 本地", key="t_local", disabled=not has_local_audio):
            st.audio(term_data['audio_hash'])

        if c2.button("☁️ 在线生成", key="t_online"):
            with st.spinner("生成中..."):
                path = tts.get_audio_path(word)
                if path:
                    st.session_state[f"new_audio_{t_id}"] = path
                    st.audio(path)
                    st.success("已生成")

    with col_t2:
        st.markdown("**释义 / 翻译**")
        def_val = st.text_area("释义", value=term_data['definition'] or "", key="term_def_input")
        if st.button("🧠 AI 自动解释", key="t_explain"):
            st.info("请使用下方例句的 AI 解析功能")

    st.divider()

    # --- B. 句子匹配区 ---
    st.subheader("2. 语境例句")

    linked_sents = db.get_matches_for_term(t_id)
    searched_sents = db.search_sentences_by_text(term_data['domain_id'], word)

    all_sents_map = {s['id']: s for s in linked_sents}
    saved_ids = set(all_sents_map.keys())
    for s in searched_sents:
        if s['id'] not in all_sents_map:
            all_sents_map[s['id']] = s
    final_sents = list(all_sents_map.values())

    if not final_sents:
        st.info("没有找到相关例句。")

    for i, sent in enumerate(final_sents):
        s_id = sent['id']
        is_saved = s_id in saved_ids

        with st.container(border=True):
            if is_saved:
                st.caption("✅ 已关联")
            else:
                st.caption("❓ 潜在匹配")

            st.markdown(f"**{sent['content_en']}**")

            sc1, sc2 = st.columns([1, 1])

            # S1. 读音
            with sc1:
                st.write("🔊 读音")
                b1, b2 = st.columns(2)
                s_audio = st.session_state.get(f"new_sent_audio_{s_id}", sent['audio_hash'])

                if b1.button("📂 播放", key=f"s_play_{s_id}", disabled=not s_audio):
                    st.audio(s_audio)

                if b2.button("☁️ 生成", key=f"s_gen_{s_id}"):
                    with st.spinner("生成中..."):
                        path = tts.get_audio_path(sent['content_en'])
                        if path:
                            st.session_state[f"new_sent_audio_{s_id}"] = path
                            st.audio(path)
                            st.rerun()

            # S2. 翻译 & AI 解析
            with sc2:
                st.write("🇨🇳 翻译 & 语境")

                input_key = f"s_cn_input_{s_id}"

                # 初始化输入框的值
                if input_key not in st.session_state:
                    st.session_state[input_key] = sent['content_cn'] if sent['content_cn'] else ""

                st.text_area("中文", key=input_key, height=70)

                # ✅ 4. 使用 on_click 绑定回调函数 (彻底解决报错)
                st.button(
                    "🧠 AI 解析",
                    key=f"s_ai_{s_id}",
                    on_click=ai_parse_callback,
                    args=(word, sent['content_en'], input_key)
                )

                # 如果有回调产生的消息，在这里显示
                if f"msg_{input_key}" in st.session_state:
                    st.success(f"💡 {st.session_state[f'msg_{input_key}']}")
                    # 显示一次后清除，避免一直占位 (可选)
                    # del st.session_state[f"msg_{input_key}"]

                if f"err_{input_key}" in st.session_state:
                    st.error(st.session_state[f"err_{input_key}"])

    st.divider()

    # --- C. 保存区 ---
    if st.button("💾 保存所有更改", type="primary", use_container_width=True):
        updated_count = 0

        new_def = st.session_state.get("term_def_input")
        new_term_audio = st.session_state.get(f"new_audio_{t_id}")
        db.update_term_info(t_id, definition=new_def, audio_path=new_term_audio)

        for sent in final_sents:
            s_id = sent['id']
            # 从 Key 取值，确保保存的是最新输入
            user_cn_input = st.session_state.get(f"s_cn_input_{s_id}")
            new_s_audio = st.session_state.get(f"new_sent_audio_{s_id}")

            if user_cn_input or new_s_audio:
                db.update_sentence_info(s_id, content_cn=user_cn_input, audio_path=new_s_audio)

            db.add_match(t_id, s_id)
            updated_count += 1

        st.success(f"✅ 保存成功！更新了 {updated_count} 个句子。")
        import time

        time.sleep(1)
        st.rerun()