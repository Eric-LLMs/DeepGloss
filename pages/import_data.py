import streamlit as st
import pandas as pd
from app.database.db_manager import DBManager
import re

st.set_page_config(page_title="数据管理", layout="wide")
st.title("📥 数据导入中心")

db = DBManager()

# --- Tab 分组 ---
tab1, tab2, tab3 = st.tabs(["1. 管理领域 (Domain)", "2. 导入词汇 (Terms)", "3. 导入句库 (Sentences)"])

# ================= Tab 1: 领域管理 =================
with tab1:
    st.subheader("创建或查看领域")

    # 新建
    with st.form("new_domain"):
        new_name = st.text_input("新领域名称", placeholder="例如: 法律英语 / 医学术语 / CS336_Lecture")
        if st.form_submit_button("创建"):
            if new_name:
                db.add_domain(new_name)
                st.success(f"✅ 领域 '{new_name}' 已创建")
                st.rerun()

    # 列表
    st.divider()
    domains = db.get_all_domains()
    if domains:
        st.write("已存在的领域：")
        st.table([{"ID": d['id'], "Name": d['name']} for d in domains])
    else:
        st.info("暂无领域")

# ================= Tab 2: 导入词汇 =================
with tab2:
    st.subheader("导入专业术语")

    if not domains:
        st.warning("请先在 Tab 1 创建领域")
        st.stop()

    d_opts = {d['name']: d['id'] for d in domains}
    sel_d_name_t = st.selectbox("选择目标领域:", list(d_opts.keys()), key="dom_term")
    sel_d_id_t = d_opts[sel_d_name_t]

    st.divider()

    # 子选项卡：文件 vs 文本
    sub_t1, sub_t2 = st.tabs(["📂 上传 Excel/CSV (推荐)", "✍️ 手动粘贴"])

    # --- A. 文件上传模式 ---
    with sub_t1:
        uploaded_file = st.file_uploader("上传词表", type=['xlsx', 'xls', 'csv'], key="term_uploader")

        if uploaded_file:
            try:
                # 1. 读取文件
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)

                st.write("👀 数据预览 (前 5 行):")
                st.dataframe(df.head())

                # 2. 选择列
                cols = df.columns.tolist()
                col1, col2 = st.columns(2)
                with col1:
                    word_col = st.selectbox("请选择【单词】所在的列:", cols, key="word_col_select")
                with col2:
                    # 去掉了 "(仅展示)" 的提示
                    freq_col = st.selectbox("请选择【词频】所在的列:", ["-- 忽略 --"] + cols, key="freq_col_select")

                # 3. 导入按钮
                if st.button("🚀 确认导入文件数据", type="primary"):
                    count = 0
                    with st.spinner("正在导入..."):
                        for index, row in df.iterrows():
                            # A. 获取单词
                            raw_word = str(row[word_col]).strip()

                            # B. 获取词频 (处理可能的格式错误)
                            freq_val = 0
                            if freq_col != "-- 忽略 --":
                                try:
                                    val = row[freq_col]
                                    # 处理 '18' 或 '18.0' 这种格式
                                    freq_val = int(float(val))
                                except:
                                    freq_val = 0  # 如果转换失败(比如是空的)，默认为0

                            if raw_word and raw_word.lower() != 'nan':
                                # 调用新的 add_term，传入 frequency
                                db.add_term(sel_d_id_t, raw_word, frequency=freq_val)
                                count += 1

                    st.success(f"✅ 成功导入 {count} 个词汇 (含词频) 到 '{sel_d_name_t}'")

                # 3. 导入按钮
                if st.button("🚀 确认导入文件数据", type="primary"):
                    count = 0
                    with st.spinner("正在导入..."):
                        for index, row in df.iterrows():
                            # 获取单词并转为字符串，去除前后空格
                            raw_word = str(row[word_col]).strip()
                            if raw_word and raw_word.lower() != 'nan':
                                db.add_term(sel_d_id_t, raw_word)
                                count += 1
                    st.success(f"✅ 成功从文件导入 {count} 个词汇到 '{sel_d_name_t}'")

            except Exception as e:
                st.error(f"❌ 读取文件失败: {e}")
                st.info("提示: 如果是 Excel 文件，请确保已安装依赖: `pip install openpyxl`")

    # --- B. 手动粘贴模式 ---
    with sub_t2:
        st.caption("格式支持：`Word` 或 `Word Frequency` (例如: KV cache 18)")
        raw_terms = st.text_area("输入词汇 (每行一个)", height=300, key="term_text_area")

        if st.button("📥 导入文本框数据"):
            lines = raw_terms.split('\n')
            count = 0
            for line in lines:
                # 清洗：去除末尾数字和空格 (兼容粘贴 Excel 两列数据的情况)
                clean_word = re.sub(r'\s+\d+$', '', line).strip()
                if clean_word:
                    db.add_term(sel_d_id_t, clean_word)
                    count += 1
            st.success(f"成功导入 {count} 个词汇到 '{sel_d_name_t}'")

# ================= Tab 3: 导入句子 =================
with tab3:
    st.subheader("导入语料库/句子")

    if not domains:
        st.stop()

    sel_d_name_s = st.selectbox("选择目标领域:", list(d_opts.keys()), key="dom_sent")
    sel_d_id_s = d_opts[sel_d_name_s]

    st.divider()

    sub_s1, sub_s2 = st.tabs(["📂 上传文本文件", "✍️ 手动粘贴"])

    # --- A. 文件上传 ---
    with sub_s1:
        up_sent_file = st.file_uploader("上传句子文件 (txt/csv/xlsx)", type=['txt', 'csv', 'xlsx'], key="sent_uploader")
        if up_sent_file:
            # 简单处理 TXT
            if up_sent_file.name.endswith('.txt'):
                string_data = up_sent_file.getvalue().decode("utf-8")
                if st.button("📥 导入 TXT 内容"):
                    lines = string_data.splitlines()
                    c = 0
                    for line in lines:
                        if len(line.strip()) > 5:
                            db.add_sentence(sel_d_id_s, line.strip())
                            c += 1
                    st.success(f"已导入 {c} 条句子")

            # 处理 Excel/CSV
            else:
                try:
                    if up_sent_file.name.endswith('.csv'):
                        sdf = pd.read_csv(up_sent_file)
                    else:
                        sdf = pd.read_excel(up_sent_file)
                    st.dataframe(sdf.head(3))

                    s_col = st.selectbox("选择【句子内容】列:", sdf.columns)
                    if st.button("📥 导入表格中的句子"):
                        c = 0
                        for i, r in sdf.iterrows():
                            val = str(r[s_col]).strip()
                            if len(val) > 5:
                                db.add_sentence(sel_d_id_s, val)
                                c += 1
                        st.success(f"已导入 {c} 条句子")
                except Exception as e:
                    st.error(f"解析失败: {e}")

    # --- B. 手动粘贴 ---
    with sub_s2:
        raw_sents = st.text_area("输入句子 (每行一句)", height=300, key="sent_text_area")
        if st.button("📥 导入文本框句子"):
            lines = raw_sents.split('\n')
            count = 0
            for line in lines:
                clean_sent = line.strip()
                if len(clean_sent) > 5:
                    db.add_sentence(sel_d_id_s, clean_sent)
                    count += 1
            st.success(f"成功导入 {count} 条句子到 '{sel_d_name_s}'")