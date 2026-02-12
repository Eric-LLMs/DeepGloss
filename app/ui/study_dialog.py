import streamlit as st
import urllib.parse
from app.ui.mic_widget import render_mic_widget


def _on_study_dialog_dismiss():
    """
    Dialog dismissal callback.
    Clears session state to prevent immediate reopening.
    """
    if "active_study_index" in st.session_state:
        del st.session_state["active_study_index"]


def ai_parse_callback(word, context, target_key, llm):
    """Callback for AI parsing of translation and explanation"""
    try:
        res = llm.explain_term_in_context(word, context)
        if isinstance(res, dict) and 'translation' in res:
            st.session_state[target_key] = res['translation']
            st.session_state[f"msg_{target_key}"] = res['explanation']
    except Exception as e:
        st.session_state[f"err_{target_key}"] = str(e)


def render_detail_body(term_data, db, tts, llm):
    """Renders the internal UI body of the study dialog"""
    t_id = term_data['id']
    term_dict = dict(term_data)
    word = term_dict['word']
    domain_id = term_dict['domain_id']  # We need this to save new sentences

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

    # Hybrid Search: SQLite first -> Then VectorDB
    searched_sents = db.search_sentences_hybrid(term_dict['domain_id'], word)

    # Merge results (using ID as key to deduplicate)
    all_sents_map = {s['id']: s for s in linked_sents}
    for s in searched_sents:
        if s['id'] not in all_sents_map:
            all_sents_map[s['id']] = s

    all_sents = list(all_sents_map.values())

    # Helper for length
    def _sent_len(row):
        try:
            content = dict(row).get("content_en", "")
        except Exception:
            content = ""
        return len(str(content).strip()) if content else 0

    # Logic: Pick the longest sentence (Top 1) from recall list
    if all_sents:
        longest_sent = max(all_sents, key=_sent_len)
        final_sents = [longest_sent]
    else:
        final_sents = []

    if not final_sents:
        st.info("No contextual sentences found.")

    for i, sent in enumerate(final_sents):
        s_dict = dict(sent)
        s_id = s_dict['id']  # This could be int (SQLite) or str starting with 'vdb_'

        # Determine source type for UI badge
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
                    label_visibility="collapsed",
                    placeholder="Enter translation here..."
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
        # [UPDATED SAVE LOGIC]
        if st.button("💾 Save", type="primary", use_container_width=True, key=f"modal_save_{t_id}"):
            # 1. Save Term Info (Definition, etc.)
            new_def = st.session_state.get(f"term_def_input_{t_id}")
            new_term_audio = st.session_state.get(f"new_audio_{t_id}")
            saved_level = st.session_state.get(f"star_radio_{t_id}")

            db.update_term_info(t_id, definition=new_def, audio_path=new_term_audio, star_level=saved_level)

            # 2. Save/Update Sentences and Links
            for sent in final_sents:
                s_dict = dict(sent)
                temp_s_id = s_dict['id']
                content_en = s_dict['content_en']

                # Retrieve user inputs from session state using the UI key (temp_s_id)
                input_key = f"s_cn_input_{temp_s_id}"
                user_cn = st.session_state.get(input_key)
                user_audio = st.session_state.get(f"new_sent_audio_{temp_s_id}")
                user_expl = st.session_state.get(f"msg_{input_key}")

                real_s_id = temp_s_id

                # [CRITICAL LOGIC] Handle VectorDB-only sentences
                if str(temp_s_id).startswith("vdb_"):
                    # Check if user actually interacted with it or we just want to save the link
                    # Strategy: Always insert into SQLite to create a permanent record

                    # db.add_sentence handles duplication (returns existing ID if content matches)
                    # If it's a new sentence, it creates a new ID.
                    real_s_id = db.add_sentence(domain_id, content_en)

                # Now we have a real integer ID (real_s_id).
                # Update the record in SQLite with user's translation/audio
                if user_cn or user_audio or user_expl:
                    db.update_sentence_info(
                        real_s_id,
                        content_cn=user_cn,
                        audio_path=user_audio,
                        cn_explanation=user_expl,
                    )

                # Finally, create the link in the matches table
                db.add_match(t_id, real_s_id)

            st.toast("Saved successfully! Sentence is now linked.", icon="✅")

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
    Driven by session_state, including Prev/Next logic
    """

    @st.dialog("🤖 Interactive Study", width="large", on_dismiss=_on_study_dialog_dismiss)
    def _dialog():
        if 'active_study_index' not in st.session_state:
            st.rerun()
            return

        curr_idx = st.session_state.active_study_index
        total_count = len(term_list)

        # Safety check
        if curr_idx < 0 or curr_idx >= total_count:
            st.error("Index out of range")
            return

        # Get current term
        current_term = term_list[curr_idx]
        term_id = current_term['id']
        term_word = current_term['word']

        # ------------------------------------
        # Top Nav (Title + Prev/Next Buttons)
        # ------------------------------------
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

        # Render Body
        term_data_fresh = db.get_term_by_id(term_id)
        render_detail_body(term_data_fresh, db, tts, llm)

    _dialog()