import streamlit as st
import urllib.parse
from app.ui.mic_widget import render_mic_widget


def _on_study_dialog_dismiss():
    """
    对话框关闭时的回调函数。

    主要作用：
    - 当用户点击弹窗右上角的「X」或点击遮罩层关闭弹窗时，
      Streamlit 会触发 on_dismiss 回调。
    - 这里统一清理 `st.session_state.active_study_index`，
      避免在主页面任意点击都再次弹出对话框。
    """
    if "active_study_index" in st.session_state:
        del st.session_state["active_study_index"]


def ai_parse_callback(word, context, target_key, llm):
    """AI 解析翻译和释义的回调函数"""
    try:
        res = llm.explain_term_in_context(word, context)
        if isinstance(res, dict) and 'translation' in res:
            st.session_state[target_key] = res['translation']
            st.session_state[f"msg_{target_key}"] = res['explanation']
    except Exception as e:
        st.session_state[f"err_{target_key}"] = str(e)


def render_detail_body(term_data, db, tts, llm):
    """渲染弹窗的内部主体 UI 逻辑"""
    t_id = term_data['id']  # 获取 ID
    term_dict = dict(term_data)
    word = term_dict['word']

    # --- Star Rating UI ---
    current_level = term_dict.get('star_level', 1)
    star_options = {1: "⭐", 2: "⭐⭐", 3: "⭐⭐⭐", 4: "⭐⭐⭐⭐", 5: "⭐⭐⭐⭐⭐"}
    new_level = st.radio(
        "Importance Level",
        options=[1, 2, 3, 4, 5],
        format_func=lambda x: star_options[x],
        index=current_level - 1,
        horizontal=True,
        label_visibility="collapsed",
        key=f"star_radio_{t_id}"
    )

    # --- A. Term Info ---
    col_t1, col_t2 = st.columns([1, 1.2])

    with col_t1:
        st.markdown("**Pronunciation**")

        term_audio_ph = st.empty()
        t_audio = st.session_state.get(f"new_audio_{t_id}", term_dict.get('audio_hash'))
        if t_audio:
            term_audio_ph.audio(t_audio)
        else:
            term_audio_ph.info("🔇 No audio available")

        if st.button("✨ Gen Pronunciation", key=f"t_online_{t_id}", use_container_width=True):
            with st.spinner("Generating..."):
                path = tts.get_audio_path(word)
                if path:
                    st.session_state[f"new_audio_{t_id}"] = path
                    term_audio_ph.audio(path)

    with col_t2:
        st.markdown("**Definition**")
        def_key = f"term_def_input_{t_id}"

        # Auto-fetch if empty
        if def_key not in st.session_state:
            if not term_dict['definition']:
                with st.spinner("Auto-fetching definition..."):
                    prompt = f"Provide a clear, concise English definition and its Chinese translation for the term '{word}'."
                    ai_def = llm.get_completion(prompt,
                                                system_prompt="You are a helpful dictionary assistant. Output only the definition.")
                    st.session_state[def_key] = ai_def
            else:
                st.session_state[def_key] = term_dict['definition']

        st.text_area(
            "Definition",
            key=def_key,
            label_visibility="collapsed",
            height=130
        )

        google_img_url = "https://www.google.com/search?tbm=isch&q=" + urllib.parse.quote(word)
        st.markdown(f"↳ [🔍 Search Images on Google]({google_img_url})")

    st.divider()

    # --- B. Contextual Sentences ---
    st.markdown("#### Contextual Sentences")

    linked_sents = db.get_matches_for_term(t_id)
    searched_sents = db.search_sentences_by_text(term_dict['domain_id'], word)

    all_sents_map = {s['id']: s for s in linked_sents}
    saved_ids = set(all_sents_map.keys())
    for s in searched_sents:
        if s['id'] not in all_sents_map:
            all_sents_map[s['id']] = s

    all_sents = list(all_sents_map.values())

    def _sent_len(row):
        try:
            content = dict(row).get("content_en", "")
        except Exception:
            content = ""
        return len(str(content).strip()) if content else 0

    if all_sents:
        longest_sent = max(all_sents, key=_sent_len)
        final_sents = [longest_sent]
    else:
        final_sents = []

    if not final_sents:
        st.info("No contextual sentences found.")

    for i, sent in enumerate(final_sents):
        s_dict = dict(sent)
        s_id = s_dict['id']
        is_saved = s_id in saved_ids

        with st.container(border=True):
            if is_saved:
                st.caption("✓ Linked Match")
            else:
                st.caption("? Potential Match")

            st.markdown(f"**{s_dict['content_en']}**")
            st.write("")

            sc1, sc2 = st.columns([1, 1])

            # S1. Audio & Recording
            with sc1:
                sent_audio_ph = st.empty()
                s_audio = st.session_state.get(f"new_sent_audio_{s_id}", s_dict.get('audio_hash'))

                if s_audio:
                    sent_audio_ph.audio(s_audio)
                else:
                    sent_audio_ph.info("🔇 No audio available")

                if st.button("✨ Gen Pronunciation", key=f"s_gen_{s_id}", use_container_width=True):
                    with st.spinner("Generating..."):
                        path = tts.get_audio_path(s_dict['content_en'])
                        if path:
                            st.session_state[f"new_sent_audio_{s_id}"] = path
                            sent_audio_ph.audio(path)

                st.write("")
                render_mic_widget()

            # S2. Translation & AI
            with sc2:
                input_key = f"s_cn_input_{s_id}"

                if input_key not in st.session_state:
                    st.session_state[input_key] = s_dict.get('content_cn', '') if s_dict.get('content_cn') else ""

                msg_key = f"msg_{input_key}"
                if msg_key not in st.session_state:
                    saved_expl = s_dict.get("cn_explanation")
                    if saved_expl:
                        st.session_state[msg_key] = saved_expl

                st.text_area(
                    "Translation",
                    key=input_key,
                    height=200,
                    label_visibility="collapsed"
                )

                st.button(
                    "✨ AI Explain",
                    key=f"s_ai_{s_id}",
                    on_click=ai_parse_callback,
                    args=(word, s_dict['content_en'], input_key, llm)
                )

                if f"msg_{input_key}" in st.session_state:
                    st.success(f"💡 {st.session_state[f'msg_{input_key}']}")

                if f"err_{input_key}" in st.session_state:
                    st.error(st.session_state[f"err_{input_key}"])

    st.divider()

    # --- C. Save & Close Area ---
    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        if st.button("💾 Save", type="primary", use_container_width=True, key=f"modal_save_{t_id}"):
            updated_count = 0
            new_def = st.session_state.get(f"term_def_input_{t_id}")
            new_term_audio = st.session_state.get(f"new_audio_{t_id}")
            saved_level = st.session_state.get(f"star_radio_{t_id}")

            db.update_term_info(t_id, definition=new_def, audio_path=new_term_audio, star_level=saved_level)

            for sent in final_sents:
                s_id = dict(sent)['id']
                input_key = f"s_cn_input_{s_id}"
                user_cn_input = st.session_state.get(input_key)
                new_s_audio = st.session_state.get(f"new_sent_audio_{s_id}")
                cn_expl = st.session_state.get(f"msg_{input_key}")

                if user_cn_input or new_s_audio or cn_expl:
                    db.update_sentence_info(
                        s_id,
                        content_cn=user_cn_input,
                        audio_path=new_s_audio,
                        cn_explanation=cn_expl,
                    )

                db.add_match(t_id, s_id)
                updated_count += 1

            st.toast("Saved successfully!", icon="✅")

    with col_btn2:
        if st.button("✖ Close", use_container_width=True, key=f"modal_close_{t_id}"):
            if 'active_study_index' in st.session_state:
                del st.session_state.active_study_index
            st.rerun()


# ==========================================
# Dialog Trigger Function (State Driven)
# ==========================================
def trigger_study_dialog(term_list, db, tts, llm):
    """
    通过 session_state 驱动弹窗，包含 Prev/Next 导航逻辑
    """

    # ✅ 交互式学习
    @st.dialog("🤖 Interactive Study", width="large", on_dismiss=_on_study_dialog_dismiss)
    def _dialog():
        if 'active_study_index' not in st.session_state:
            st.rerun()
            return

        curr_idx = st.session_state.active_study_index
        total_count = len(term_list)

        # 安全检查
        if curr_idx < 0 or curr_idx >= total_count:
            st.error("Index out of range")
            return

        # 获取当前词
        current_term = term_list[curr_idx]
        term_id = current_term['id']
        term_word = current_term['word']

        # ------------------------------------
        # 3. 顶部导航区 (Title + Prev/Next Buttons)
        # ------------------------------------
        col_header, col_nav = st.columns([2, 1])

        with col_header:
            st.markdown(f"## 🎯 {term_word}")

        with col_nav:
            # 右侧导航区分割为两个小列
            nav_c1, nav_c2 = st.columns(2)

            has_prev = curr_idx > 0
            has_next = curr_idx < total_count - 1

            # ✅ 修改 2: 按钮增加文字说明
            with nav_c1:
                if st.button("⬅️ Prev", disabled=not has_prev, use_container_width=True, key=f"btn_prev_{curr_idx}"):
                    st.session_state.active_study_index -= 1
                    st.rerun()

            with nav_c2:
                if st.button("Next ➡️", disabled=not has_next, use_container_width=True, key=f"btn_next_{curr_idx}"):
                    st.session_state.active_study_index += 1
                    st.rerun()

        # 显示进度
        st.markdown(
            f"<div style='color:gray; font-size:0.8em; margin-bottom:10px;'>Word {curr_idx + 1} of {total_count}</div>",
            unsafe_allow_html=True)

        # 4. 获取详情并渲染主体
        term_data_fresh = db.get_term_by_id(term_id)
        render_detail_body(term_data_fresh, db, tts, llm)

    _dialog()