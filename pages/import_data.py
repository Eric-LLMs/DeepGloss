import streamlit as st
import pandas as pd
from app.database.db_manager import DBManager
from app.services.vector_manager import VectorManager
import re

st.set_page_config(page_title="Data Management", layout="wide")

# --- Custom 3D & Color Styling ---
st.markdown("""
    <style>
    /* Tab Container Layout */
    .stTabs [data-baseweb="tab-list"] { 
        gap: 8px; 
    }

    /* Default Tab Style (Unselected - Gray) */
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #f3f4f6; 
        border-radius: 8px 8px 0px 0px;
        box-shadow: 3px 3px 6px rgba(0,0,0,0.1), -1px -1px 2px rgba(255,255,255,0.8); /* 3D Effect */
        border: 1px solid #d1d5db;
        border-bottom: none;
        color: #6b7280;
        transition: all 0.2s ease;
        padding: 0 20px;
    }

    /* Active Tab Style (Selected - Light Blue) */
    .stTabs [aria-selected="true"] {
        background-color: #e0f2fe !important;
        border: 1px solid #38bdf8 !important;
        border-bottom: none !important;
        box-shadow: inset 2px 2px 5px rgba(0,0,0,0.05); /* Pressed/Inset Effect */
        color: #0284c7 !important;
        font-weight: 600;
        transform: translateY(2px); /* Slight movement */
    }

    /* Hover Effect */
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #e5e7eb;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📥 Data Import Center")
db = DBManager()

# --- Top Description Section ---
with st.container():
    st.info("""
    **👋 Welcome to the Data Management Dashboard!**

    Please follow the steps below to manage your learning resources:
    1.  **Domain Management**: Create separate topics (e.g., 'Physics', 'Daily Life').
    2.  **Import Vocabulary**: Bulk upload terms. Supports Excel/CSV (Columns: Word, Frequency).
    3.  **Import Sentences (SQL)**: Add sentences to SQLite for keyword matching. Supports TXT/Excel/CSV.
    4.  **Import VectorDB (Independent)**: Add sentences to VectorDB for semantic search. Supports TXT/Excel/CSV.
    """)

st.divider()

# --- 4 Tabs Layout ---
tab1, tab2, tab3, tab4 = st.tabs([
    "1. Domain Management",
    "2. Import Vocabulary",
    "3. Import Sentences (SQL)",
    "4. Import VectorDB (Independent)"
])

# ================= Tab 1: Domain =================
with tab1:
    st.subheader("Create or View Domains")
    with st.form("new_domain"):
        new_name = st.text_input("New Domain Name", placeholder="e.g. Stanford_CS336")
        if st.form_submit_button("Create Domain"):
            if new_name:
                db.add_domain(new_name)
                st.success("✅ Domain created.");
                st.rerun()

    domains = db.get_all_domains()
    if domains:
        st.write("Existing Domains:")
        st.table([{"ID": d['id'], "Name": d['name']} for d in domains])
    else:
        st.warning("No domains found. Please create one.")

# ================= Tab 2: Vocabulary =================
with tab2:
    st.subheader("Import Vocabulary")

    if not domains:
        st.warning("Please create a domain first.")
        st.stop()

    d_opts = {d['name']: d['id'] for d in domains}
    sel_d_name_t = st.selectbox("Target Domain:", list(d_opts.keys()), key="dom_t")
    sel_d_id_t = d_opts[sel_d_name_t]

    st.divider()

    # Sub-tabs for File vs Manual
    sub_t1, sub_t2 = st.tabs(["📂 File Upload (Excel/CSV)", "✍️ Manual Input"])

    with sub_t1:
        st.markdown("Upload a file with columns for **Word** and optional **Frequency**.")
        up_file = st.file_uploader("Upload Excel/CSV", type=['csv', 'xlsx'], key="voc_up")

        if up_file:
            try:
                if up_file.name.endswith('.csv'):
                    df = pd.read_csv(up_file)
                else:
                    df = pd.read_excel(up_file)

                st.dataframe(df.head(3))

                # Column selection
                cols = df.columns.tolist()
                c1, c2 = st.columns(2)
                with c1:
                    word_col = st.selectbox("Select 'Word' Column:", cols, key="v_w_col")
                with c2:
                    freq_col = st.selectbox("Select 'Frequency' Column (Optional):", ["-- None --"] + cols,
                                            key="v_f_col")

                if st.button("🚀 Import Vocabulary", type="primary"):
                    count = 0
                    with st.spinner("Importing..."):
                        for _, row in df.iterrows():
                            word = str(row[word_col]).strip()
                            freq = 1
                            if freq_col != "-- None --":
                                try:
                                    freq = int(row[freq_col])
                                except:
                                    freq = 1

                            if word and word.lower() != 'nan':
                                db.add_term(sel_d_id_t, word, frequency=freq)
                                count += 1
                    st.success(f"✅ Imported {count} terms to '{sel_d_name_t}'.")
            except Exception as e:
                st.error(f"Error reading file: {e}")

    with sub_t2:
        st.caption("Enter one word per line. Format: `Word` or `Word Frequency` (e.g. 'Apple 5').")
        raw_text = st.text_area("Paste Words Here", height=300, key="voc_txt")
        if st.button("📥 Import Text"):
            lines = raw_text.split('\n')
            count = 0
            for line in lines:
                # Remove trailing numbers for frequency if present
                clean_word = re.sub(r'\s+\d+$', '', line).strip()
                if clean_word:
                    db.add_term(sel_d_id_t, clean_word)
                    count += 1
            st.success(f"✅ Imported {count} terms.")

# ================= Tab 3: Sentences (SQL) =================
with tab3:
    st.subheader("Import to SQLite Corpus")
    st.caption("Sentences imported here are stored in SQL for exact keyword matching.")

    if not domains:
        st.stop()

    d_opts = {d['name']: d['id'] for d in domains}
    sel_d_name_s = st.selectbox("Target Domain:", list(d_opts.keys()), key="dom_s")
    sel_d_id_s = d_opts[sel_d_name_s]

    st.divider()

    sub_s1, sub_s2 = st.tabs(["📂 File Upload (TXT/Excel)", "✍️ Manual Input"])

    with sub_s1:
        up_sent = st.file_uploader("Upload File", type=['txt', 'csv', 'xlsx'], key="sent_up")

        if up_sent:
            # Handle TXT
            if up_sent.name.endswith('.txt'):
                string_data = up_sent.getvalue().decode("utf-8")
                st.text_area("Preview (First 500 chars)", string_data[:500], height=100, disabled=True)

                if st.button("📥 Import TXT"):
                    lines = string_data.splitlines()
                    c = 0
                    for line in lines:
                        if len(line.strip()) > 5:
                            db.add_sentence(sel_d_id_s, line.strip())
                            c += 1
                    st.success(f"✅ Imported {c} sentences.")

            # Handle Excel/CSV
            else:
                try:
                    if up_sent.name.endswith('.csv'):
                        df_s = pd.read_csv(up_sent)
                    else:
                        df_s = pd.read_excel(up_sent)

                    st.dataframe(df_s.head(3))
                    sent_col = st.selectbox("Select 'Sentence' Column:", df_s.columns, key="s_col")

                    if st.button("📥 Import Table Data"):
                        c = 0
                        for _, row in df_s.iterrows():
                            val = str(row[sent_col]).strip()
                            if len(val) > 5:
                                db.add_sentence(sel_d_id_s, val)
                                c += 1
                        st.success(f"✅ Imported {c} sentences.")
                except Exception as e:
                    st.error(f"Error: {e}")

    with sub_s2:
        raw_sents = st.text_area("Paste Sentences (one per line)", height=300, key="sent_sql_txt")
        if st.button("💾 Save to SQLite"):
            lines = raw_sents.split('\n')
            count = 0
            for line in lines:
                if len(line.strip()) > 5:
                    db.add_sentence(sel_d_id_s, line.strip())
                    count += 1
            st.success(f"✅ Saved {count} sentences to SQLite.")

# ================= Tab 4: VectorDB (Independent) =================
with tab4:
    st.subheader("Direct Import to Vector Database")
    st.markdown("""
    <div style="padding: 10px; background-color: #f0fdf4; border-left: 5px solid #22c55e; border-radius: 5px;">
        <b>Note:</b> Data here is stored <b>independently</b> in the AI Vector Database (ChromaDB).
        It is NOT synced with SQLite. Use this for semantic search when exact matches fail.
    </div>
    """, unsafe_allow_html=True)

    if not domains:
        st.stop()

    d_opts = {d['name']: d['id'] for d in domains}
    sel_d_name_v = st.selectbox("Target Domain:", list(d_opts.keys()), key="dom_v")
    sel_d_id_v = d_opts[sel_d_name_v]

    st.divider()

    # Updated: Added 3rd tab for Testing/Search
    sub_v1, sub_v2, sub_v3 = st.tabs(["📂 File Upload (TXT/Excel)", "✍️ Manual Input", "🧪 Test Search"])

    with sub_v1:
        up_vec = st.file_uploader("Upload Corpus for AI Indexing", type=['txt', 'csv', 'xlsx'], key="vec_up")

        if up_vec:
            # Handle TXT
            if up_vec.name.endswith('.txt'):
                string_data = up_vec.getvalue().decode("utf-8")
                st.text_area("Preview", string_data[:300] + "...", height=100, disabled=True)

                if st.button("🧠 Build Index (TXT)", type="primary"):
                    lines = [l.strip() for l in string_data.splitlines() if len(l.strip()) > 5]
                    if lines:
                        with st.spinner(f"Indexing {len(lines)} sentences..."):
                            vm = VectorManager()
                            vm.add_sentences_independent(lines, sel_d_id_v)
                        st.success(f"✅ Indexed {len(lines)} sentences.")

            # Handle Excel/CSV
            else:
                try:
                    if up_vec.name.endswith('.csv'):
                        df_v = pd.read_csv(up_vec)
                    else:
                        df_v = pd.read_excel(up_vec)

                    st.dataframe(df_v.head(3))
                    v_col = st.selectbox("Select 'Sentence' Column for Indexing:", df_v.columns, key="v_col_sel")

                    if st.button("🧠 Build Index (Table)", type="primary"):
                        vm = VectorManager()
                        lines = []
                        for _, row in df_v.iterrows():
                            val = str(row[v_col]).strip()
                            if len(val) > 5:
                                lines.append(val)

                        if lines:
                            with st.spinner(f"Indexing {len(lines)} sentences..."):
                                vm.add_sentences_independent(lines, sel_d_id_v)
                            st.success(f"✅ Indexed {len(lines)} sentences.")
                except Exception as e:
                    st.error(f"Error: {e}")

    with sub_v2:
        raw_vec_text = st.text_area("Paste raw text / sentences", height=300, key="vec_txt")

        if st.button("🧠 Build Independent Vector Index", type="primary", key="btn_vec_manual"):
            lines = [l.strip() for l in raw_vec_text.split('\n') if len(l.strip()) > 5]

            if lines:
                with st.spinner(f"Generating Embeddings for {len(lines)} sentences..."):
                    vm = VectorManager()
                    vm.add_sentences_independent(lines, sel_d_id_v)
                st.success(f"✅ Successfully indexed {len(lines)} sentences.")
            else:
                st.warning("Input is empty.")

    with sub_v3:
        st.markdown("### 🧪 Test Semantic Search")
        st.caption("Verify your VectorDB data by searching for similar sentences (fuzzy matching).")

        test_query = st.text_input("Enter a query sentence/phrase:", placeholder="e.g., neural network architecture",
                                   key="v_test_input")

        if st.button("🔎 Search in VectorDB", key="btn_v_test"):
            if test_query:
                vm = VectorManager()
                # Use independent search logic to find text directly
                results = vm.search_similar_text(test_query, sel_d_id_v)

                if results:
                    st.success(f"Found {len(results)} matches:")
                    for idx, txt in enumerate(results):
                        st.info(f"**{idx + 1}.** {txt}")
                else:
                    st.warning("No similar sentences found in this domain.")
            else:
                st.error("Please enter a query text.")