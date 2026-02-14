import streamlit as st
import urllib.parse
import os
import streamlit.components.v1 as components
from app.ui.mic_widget import render_mic_widget
from app.utils.image_scraper import fetch_term_images
from config import PROJECT_ROOT


def get_safe_abs_path(path_str):
    """Converts a relative path to absolute for safe loading. Leaves absolute paths intact."""
    if not path_str: return None
    if os.path.isabs(path_str): return path_str
    return str(PROJECT_ROOT / path_str)


def get_rel_path(path_str):
    """Converts an absolute path to a relative path for database storage."""
    if not path_str: return path_str
    try:
        return os.path.relpath(path_str, PROJECT_ROOT).replace('\\', '/')
    except ValueError:
        return str(path_str).replace('\\', '/')


def _on_study_dialog_dismiss():
    if "active_study_index" in st.session_state:
        del st.session_state["active_study_index"]
    if "current_viewed_term_id" in st.session_state:
        del st.session_state["current_viewed_term_id"]


def ai_parse_callback(word, context, target_key, llm):
    try:
        enhanced_context = f"{context}\n\n(Instruction: You MUST provide the explanation of the term in BOTH English and Chinese.)"
        res = llm.explain_term_in_context(word, enhanced_context)
        if isinstance(res, dict) and 'translation' in res:
            st.session_state[target_key] = res['translation']
            st.session_state[f"msg_{target_key}"] = res['explanation']
    except Exception as e:
        st.session_state[f"err_{target_key}"] = str(e)


def render_detail_body(term_data, db, tts, llm):
    t_id = term_data['id']
    term_dict = dict(term_data)
    word = term_dict['word']
    domain_id = term_dict['domain_id']

    current_level = term_dict.get('star_level', 1)
    star_options = {1: "⭐", 2: "⭐⭐", 3: "⭐⭐⭐", 4: "⭐⭐⭐⭐", 5: "⭐⭐⭐⭐⭐"}
    new_level = st.radio("Importance Level", options=[1, 2, 3, 4, 5], format_func=lambda x: star_options[x],
                         index=current_level - 1, horizontal=True, label_visibility="collapsed",
                         key=f"star_radio_{t_id}")

    col_t1, col_t2 = st.columns([1, 1.2])

    with col_t1:
        st.markdown("**Pronunciation**")
        term_audio_ph = st.empty()
        t_audio = st.session_state.get(f"new_audio_{t_id}", term_dict.get('audio_hash'))

        if t_audio:
            abs_t_audio = get_safe_abs_path(t_audio)
            if abs_t_audio and os.path.exists(abs_t_audio):
                term_audio_ph.audio(abs_t_audio)
            else:
                term_audio_ph.info("🔇 Audio file missing")
        else:
            term_audio_ph.info("🔇 No audio available")

        if st.button("✨ Gen Pronunciation", key=f"t_online_{t_id}", use_container_width=True):
            with st.spinner("Generating..."):
                path = tts.get_audio_path(word)
                if path:
                    rel_path = get_rel_path(path)
                    st.session_state[f"new_audio_{t_id}"] = rel_path
                    term_audio_ph.audio(path)

    with col_t2:
        st.markdown("**Definition**")
        def_key = f"term_def_input_{t_id}"

        if def_key not in st.session_state:
            if not term_dict['definition']:
                with st.spinner("Auto-fetching definition..."):
                    prompt = f"Provide a clear, concise English definition and its Chinese translation for the term '{word}'."
                    ai_def = llm.get_completion(prompt,
                                                system_prompt="You are a helpful dictionary assistant. Output only the definition.")
                    st.session_state[def_key] = ai_def
            else:
                st.session_state[def_key] = term_dict['definition']

        st.text_area("Definition", key=def_key, label_visibility="collapsed", height=130)
        google_img_url = "https://www.google.com/search?tbm=isch&q=" + urllib.parse.quote(word)
        st.markdown(f"↳ [🔍 Search Images on Google]({google_img_url})")

    st.divider()

    linked_sents = db.get_matches_for_term(t_id)
    searched_sents = db.search_sentences_hybrid(domain_id, word)

    all_sents_map = {s['id']: s for s in linked_sents}
    for s in searched_sents:
        if s['id'] not in all_sents_map:
            all_sents_map[s['id']] = s

    all_sents = list(all_sents_map.values())

    def _sent_len(row):
        return len(str(dict(row).get("content_en", "")).strip())

    final_sents = [max(all_sents, key=_sent_len)] if all_sents else []

    context_str = dict(final_sents[0]).get('content_en', '') if final_sents else ""
    def_str = st.session_state.get(def_key, term_dict.get('definition', ''))

    visual_context_container = st.container()

    st.markdown("#### Contextual Sentences")

    if not final_sents:
        st.info("No contextual sentences found.")

    for i, sent in enumerate(final_sents):
        s_dict = dict(sent)
        s_id = s_dict['id']

        is_vdb_only = str(s_id).startswith("vdb_")
        is_linked = s_id in [s['id'] for s in linked_sents]

        with st.container(border=True):
            if is_vdb_only:
                st.caption("🤖 Vector Match (Not in SQL)")
            elif is_linked:
                st.caption("✓ Linked Match")
            else:
                st.caption("? SQLite Match")

            st.markdown(f"**{s_dict['content_en']}**")
            st.write("")

            sc1, sc2 = st.columns([1, 1])

            with sc1:
                sent_audio_ph = st.empty()
                s_audio = st.session_state.get(f"new_sent_audio_{s_id}", s_dict.get('audio_hash'))

                if s_audio:
                    abs_s_audio = get_safe_abs_path(s_audio)
                    if abs_s_audio and os.path.exists(abs_s_audio):
                        sent_audio_ph.audio(abs_s_audio)
                    else:
                        sent_audio_ph.info("🔇 Audio file missing")
                else:
                    sent_audio_ph.info("🔇 No audio available")

                if st.button("✨ Gen Pronunciation", key=f"s_gen_{s_id}", use_container_width=True):
                    with st.spinner("Generating..."):
                        path = tts.get_audio_path(s_dict['content_en'])
                        if path:
                            rel_path = get_rel_path(path)
                            st.session_state[f"new_sent_audio_{s_id}"] = rel_path
                            sent_audio_ph.audio(path)

                st.write("")
                render_mic_widget()

            with sc2:
                input_key = f"s_cn_input_{s_id}"
                if input_key not in st.session_state:
                    st.session_state[input_key] = s_dict.get('content_cn', '') if s_dict.get('content_cn') else ""

                msg_key = f"msg_{input_key}"
                if msg_key not in st.session_state:
                    saved_expl = s_dict.get("cn_explanation")
                    if saved_expl: st.session_state[msg_key] = saved_expl

                st.text_area("Translation", key=input_key, height=200, label_visibility="collapsed",
                             placeholder="Enter translation here...")

                st.button("✨ AI Explain", key=f"s_ai_{s_id}", on_click=ai_parse_callback,
                          args=(word, s_dict['content_en'], input_key, llm))

                if f"msg_{input_key}" in st.session_state:
                    st.success(f"💡 {st.session_state[f'msg_{input_key}']}")
                if f"err_{input_key}" in st.session_state:
                    st.error(st.session_state[f"err_{input_key}"])

    st.divider()

    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        if st.button("💾 Save", type="primary", use_container_width=True, key=f"modal_save_{t_id}"):
            new_def = st.session_state.get(f"term_def_input_{t_id}")
            new_term_audio = get_rel_path(st.session_state.get(f"new_audio_{t_id}"))
            saved_level = st.session_state.get(f"star_radio_{t_id}")

            saved_images = st.session_state.get(f"img_paths_{t_id}", "")
            if saved_images in ["NOT_FOUND", "NEEDS_FETCH", "FETCHING"]:
                saved_images = ""

            db.update_term_info(t_id, definition=new_def, audio_path=new_term_audio, star_level=saved_level,
                                image_paths=saved_images)

            for sent in final_sents:
                s_dict = dict(sent)
                temp_s_id = s_dict['id']
                content_en = s_dict['content_en']

                input_key = f"s_cn_input_{temp_s_id}"
                user_cn = st.session_state.get(input_key)
                user_audio = get_rel_path(st.session_state.get(f"new_sent_audio_{temp_s_id}"))
                user_expl = st.session_state.get(f"msg_{input_key}")

                real_s_id = temp_s_id

                if str(temp_s_id).startswith("vdb_"):
                    real_s_id = db.add_sentence(domain_id, content_en)

                if user_cn or user_audio or user_expl:
                    db.update_sentence_info(real_s_id, content_cn=user_cn, audio_path=user_audio,
                                            cn_explanation=user_expl)

                db.add_match(t_id, real_s_id)

            st.toast("Saved successfully! Data is now linked.", icon="✅")

    with col_btn2:
        if st.button("✖ Close", use_container_width=True, key=f"modal_close_{t_id}"):
            if 'active_study_index' in st.session_state:
                del st.session_state.active_study_index
            st.rerun()

    with visual_context_container:
        st.markdown("#### 🖼️ Visual Context")

        img_state_key = f"img_paths_{t_id}"

        if f"is_regen_{t_id}" not in st.session_state:
            st.session_state[f"is_regen_{t_id}"] = False

        if img_state_key not in st.session_state:
            db_paths = term_dict.get('image_paths', '')
            valid_paths = []

            if db_paths:
                for p in db_paths.split(","):
                    if p.strip():
                        abs_p = get_safe_abs_path(p.strip())
                        if abs_p and os.path.exists(abs_p):
                            valid_paths.append(p.strip())

            if valid_paths:
                st.session_state[img_state_key] = ",".join(valid_paths)
            else:
                st.session_state[img_state_key] = "NEEDS_FETCH"

        col_title, col_regen = st.columns([4, 1])
        with col_regen:
            if st.button("🔄 Regenerate", key=f"regen_{t_id}", use_container_width=True):
                st.session_state[img_state_key] = "NEEDS_FETCH"
                st.session_state[f"is_regen_{t_id}"] = True
                st.rerun()

        js_spinner = """
        <div id="loader-container" style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 160px; background-color: #f8fafc; border-radius: 8px; border: 1px dashed #cbd5e1;">
            <div class="spinner"></div>
            <div id="loading-text" style="margin-top: 15px; font-family: sans-serif; color: #475569; font-size: 14px; font-weight: 500;">
                Searching & extracting context images...
            </div>
            <style>
            .spinner {
                width: 40px;
                height: 40px;
                border: 4px solid #e2e8f0;
                border-top: 4px solid #3b82f6;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            </style>
            <script>
                const textEl = document.getElementById('loading-text');
                let dots = 0;
                setInterval(() => {
                    dots = (dots + 1) % 4;
                    textEl.innerText = 'Searching & extracting context images' + '.'.repeat(dots);
                }, 400);
            </script>
        </div>
        """

        img_display_area = st.empty()
        state = st.session_state[img_state_key]

        if state == "NEEDS_FETCH":
            with img_display_area.container():
                components.html(js_spinner, height=180)
            st.session_state[img_state_key] = "FETCHING"
            st.rerun()

        elif state == "FETCHING":
            with img_display_area.container():
                components.html(js_spinner, height=180)

            is_regen = st.session_state.get(f"is_regen_{t_id}", False)
            new_paths = fetch_term_images(word, def_str, context_str, t_id, is_regenerate=is_regen)

            if new_paths:
                st.session_state[img_state_key] = new_paths
            else:
                st.session_state[img_state_key] = "NOT_FOUND"

            st.rerun()

        elif state not in ["NOT_FOUND", ""]:
            with img_display_area.container():
                paths = state.split(",")
                img_cols = st.columns(3)
                for i, p in enumerate(paths):
                    if i < 3:
                        abs_p = get_safe_abs_path(p)
                        if abs_p and os.path.exists(abs_p):
                            with img_cols[i]:
                                st.image(abs_p, use_container_width=True)

        elif state == "NOT_FOUND":
            img_display_area.warning(
                "⚠️ Could not fetch images automatically. Please check your network or try Regenerate.")

        st.divider()


def trigger_study_dialog(term_list, db, tts, llm):
    @st.dialog("🤖 Interactive Study", width="large", on_dismiss=_on_study_dialog_dismiss)
    def _dialog():
        if 'active_study_index' not in st.session_state:
            st.rerun()
            return

        curr_idx = st.session_state.active_study_index
        total_count = len(term_list)

        if curr_idx < 0 or curr_idx >= total_count:
            st.error("Index out of range")
            return

        current_term = term_list[curr_idx]
        term_id = current_term['id']
        term_word = current_term['word']

        if st.session_state.get("current_viewed_term_id") != term_id:
            st.session_state["current_viewed_term_id"] = term_id
            keys_to_clear = [f"img_paths_{term_id}", f"is_regen_{term_id}"]
            for k in keys_to_clear:
                if k in st.session_state:
                    del st.session_state[k]

        col_header, col_nav = st.columns([2, 1])

        with col_header:
            st.markdown(f"## 🎯 {term_word}")

        with col_nav:
            nav_c1, nav_c2 = st.columns(2)
            has_prev = curr_idx > 0
            has_next = curr_idx < total_count - 1

            with nav_c1:
                if st.button("⬅️ Prev", disabled=not has_prev, use_container_width=True, key=f"btn_prev_{curr_idx}"):
                    st.session_state.active_study_index -= 1
                    st.rerun()

            with nav_c2:
                if st.button("Next ➡️", disabled=not has_next, use_container_width=True, key=f"btn_next_{curr_idx}"):
                    st.session_state.active_study_index += 1
                    st.rerun()

        st.markdown(
            f"<div style='color:gray; font-size:0.8em; margin-bottom:10px;'>Word {curr_idx + 1} of {total_count}</div>",
            unsafe_allow_html=True)

        term_data_fresh = db.get_term_by_id(term_id)
        render_detail_body(term_data_fresh, db, tts, llm)

    _dialog()