# app/services/ingestion.py
import re


class IngestionEngine:
    def process(self, db, project_id, raw_text, terms_list):
        """
        db: 数据库实例
        project_id: 当前项目ID
        raw_text: 文章全文
        terms_list: 用户输入的词汇列表 ["Lithography", "Wafer", ...]
        """

        # 1. 先把词汇存入数据库 (如果不存在)
        # 同时建立一个内存映射 map: {'lithography': 101, 'wafer': 102}
        term_map = {}
        for term in terms_list:
            clean_term = term.strip()
            if clean_term:
                # 简单处理：先存入，暂时不写定义
                term_id = db.add_term(project_id, clean_term)
                term_map[clean_term] = term_id

        # 2. 简单的分句逻辑 (按 . ! ? 分割)
        # 实际生产中可以用 nltk.sent_tokenize
        sentences = re.split(r'(?<=[.!?])\s+', raw_text)

        processed_sentences = []

        # 3. 遍历句子，进行匹配
        for sent in sentences:
            clean_sent = sent.strip()
            if len(clean_sent) < 5: continue  # 太短的忽略

            found_terms = []
            for t_text in term_map.keys():
                # 使用正则进行全词匹配 (避免 'apple' 匹配到 'pineapple')
                # \b 表示单词边界
                if re.search(r'\b' + re.escape(t_text) + r'\b', clean_sent, re.IGNORECASE):
                    found_terms.append(t_text)

            # 只有当句子包含至少一个术语时，我们才存它 (或者你可以选择存所有句子)
            if found_terms:
                processed_sentences.append({
                    "text": clean_sent,
                    "matched_terms": found_terms
                })

        # 4. 存入数据库
        db.insert_processed_data(project_id, term_map, processed_sentences)

        return len(processed_sentences)