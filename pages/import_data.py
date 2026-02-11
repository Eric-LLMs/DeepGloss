import streamlit as st
import pandas as pd
from app.database.db_manager import DBManager
import re

st.set_page_config(page_title="Data Management", layout="wide")
st.title("📥 Data Import Center")

db = DBManager()

tab1, tab2, tab3 = st.tabs(["1. Domain Management", "2. Import Vocabulary", "3. Import Sentences"])

# ================= Tab 1: Domain =================
with tab1:
    st.subheader("Create or View Domains")

    with st.form("new_domain"):
        new_name = st.text_input("New Domain Name", placeholder="e.g. Legal English / Stanford_CS336_Lecture")
        if st.form_submit_button("Create Domain"):
            if new_name:
                db.add_domain(new_name)
                st.success(f"✅ Domain '{new_name}' created successfully.")
                st.rerun()

    st.divider()
    domains = db.get_all_domains()
    if domains:
        st.write("Existing Domains:")
        st.table([{"ID": d['id'], "Name": d['name']} for d in domains])
    else:
        st.info("No domains available. Please create one.")

# ================= Tab 2: Terms =================
with tab2:
    st.subheader("Import Vocabulary")

    if not domains:
        st.warning("Please create a domain in Tab 1 first.")
        st.stop()

    d_opts = {d['name']: d['id'] for d in domains}
    sel_d_name_t = st.selectbox("Select Target Domain:", list(d_opts.keys()), key="dom_term")
    sel_d_id_t = d_opts[sel_d_name_t]

    st.divider()

    sub_t1, sub_t2 = st.tabs(["📂 Upload Excel/CSV", "✍️ Manual Paste"])

    with sub_t1:
        uploaded_file = st.file_uploader("Upload Vocabulary File", type=['xlsx', 'xls', 'csv'], key="term_uploader")

        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)

                st.write("👀 Data Preview (First 5 rows):")
                st.dataframe(df.head())

                cols = df.columns.tolist()
                col1, col2 = st.columns(2)
                with col1:
                    word_col = st.selectbox("Select the [Word] Column:", cols, key="word_col_select")
                with col2:
                    freq_col = st.selectbox("Select the [Frequency] Column:", ["-- Ignore --"] + cols, key="freq_col_select")

                if st.button("🚀 Confirm File Import", type="primary", key="btn_import_term_file"):
                    count = 0
                    with st.spinner("Importing..."):
                        for index, row in df.iterrows():
                            raw_word = str(row[word_col]).strip()
                            freq_val = 1
                            if freq_col != "-- Ignore --":
                                try:
                                    freq_val = int(float(row[freq_col]))
                                except:
                                    freq_val = 1

                            if raw_word and raw_word.lower() != 'nan':
                                db.add_term(sel_d_id_t, raw_word, frequency=freq_val, star_level=1)
                                count += 1

                    st.success(f"✅ Successfully imported {count} terms to '{sel_d_name_t}'.")
            except Exception as e:
                st.error(f"❌ Failed to read file: {e}")

    with sub_t2:
        st.caption("Format: `Word` or `Word Frequency` (e.g., KV cache 18). Duplicates will be skipped automatically.")
        raw_terms = st.text_area("Enter Vocabulary (One per line)", height=300, key="term_text_area")

        if st.button("📥 Import from Text Box", key="btn_import_term_txt"):
            lines = raw_terms.split('\n')
            count = 0
            for line in lines:
                clean_word = re.sub(r'\s+\d+$', '', line).strip()
                if clean_word:
                    db.add_term(sel_d_id_t, clean_word, frequency=1, star_level=1)
                    count += 1
            st.success(f"✅ Successfully imported {count} terms to '{sel_d_name_t}'.")

# ================= Tab 3: Sentences =================
with tab3:
    st.subheader("Import Sentences / Corpus")

    if not domains:
        st.stop()

    sel_d_name_s = st.selectbox("Select Target Domain:", list(d_opts.keys()), key="dom_sent")
    sel_d_id_s = d_opts[sel_d_name_s]

    st.divider()

    sub_s1, sub_s2 = st.tabs(["📂 Upload Text/Data File", "✍️ Manual Paste"])

    with sub_s1:
        up_sent_file = st.file_uploader("Upload Sentences (txt/csv/xlsx)", type=['txt', 'csv', 'xlsx'], key="sent_uploader")
        if up_sent_file:
            if up_sent_file.name.endswith('.txt'):
                string_data = up_sent_file.getvalue().decode("utf-8")
                if st.button("📥 Import TXT Content", key="btn_import_sent_txt_file"):
                    lines = string_data.splitlines()
                    c = 0
                    for line in lines:
                        if len(line.strip()) > 5:
                            db.add_sentence(sel_d_id_s, line.strip())
                            c += 1
                    st.success(f"✅ Imported {c} sentences.")
            else:
                try:
                    if up_sent_file.name.endswith('.csv'):
                        sdf = pd.read_csv(up_sent_file)
                    else:
                        sdf = pd.read_excel(up_sent_file)
                    st.dataframe(sdf.head(3))

                    s_col = st.selectbox("Select [Sentence] Column:", sdf.columns, key="sent_col_select")
                    if st.button("📥 Import Sentences from Table", key="btn_import_sent_tbl"):
                        c = 0
                        for i, r in sdf.iterrows():
                            val = str(r[s_col]).strip()
                            if len(val) > 5:
                                db.add_sentence(sel_d_id_s, val)
                                c += 1
                        st.success(f"✅ Imported {c} sentences.")
                except Exception as e:
                    st.error(f"❌ Parsing failed: {e}")

    with sub_s2:
        raw_sents = st.text_area("Enter Sentences (One per line)", height=300, key="sent_text_area_2")
        if st.button("📥 Import from Text Box", key="btn_import_sent_txt_box"):
            lines = raw_sents.split('\n')
            count = 0
            for line in lines:
                clean_sent = line.strip()
                if len(clean_sent) > 5:
                    db.add_sentence(sel_d_id_s, clean_sent)
                    count += 1
            st.success(f"✅ Successfully imported {count} sentences to '{sel_d_name_s}'.")