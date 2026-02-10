import sqlite3
import os
from pathlib import Path

CURRENT_DIR = Path(__file__).parent
DB_PATH = CURRENT_DIR.parent.parent / "data" / "deepgloss.db"
SCHEMA_PATH = CURRENT_DIR / "schema.sql"


class DBManager:
    def __init__(self):
        if not DB_PATH.parent.exists():
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._execute_schema_script()

    def _execute_schema_script(self):
        if SCHEMA_PATH.exists():
            with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
                self.conn.executescript(f.read())

    # --- 1. Domain ---
    def add_domain(self, name):
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO domain (name) VALUES (?)", (name,))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            cursor = self.conn.execute("SELECT id FROM domain WHERE name=?", (name,))
            return cursor.fetchone()['id']

    def get_all_domains(self):
        return self.conn.execute("SELECT id, name FROM domain").fetchall()

    # --- 2. Terms ---
    def add_term(self, domain_id, word, definition="", frequency=0):
        # 1. 检查是否存在
        cursor = self.conn.execute(
            "SELECT id FROM terms WHERE domain_id=? AND word=?", (domain_id, word)
        )
        res = cursor.fetchone()

        # 2. 如果存在，更新词频 (取较大的那个)
        if res:
            term_id = res['id']
            # 可选：如果新导入的词频更高，就更新它
            if frequency > 0:
                self.conn.execute("UPDATE terms SET frequency=? WHERE id=? AND frequency<?",
                                  (frequency, term_id, frequency))
                self.conn.commit()
            return term_id

        # 3. 如果不存在，插入新词
        cursor = self.conn.execute(
            "INSERT INTO terms (domain_id, word, definition, frequency) VALUES (?, ?, ?, ?)",
            (domain_id, word, definition, frequency)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_terms_by_domain(self, domain_id):
        return self.conn.execute("SELECT * FROM terms WHERE domain_id=?", (domain_id,)).fetchall()

    def get_term_by_id(self, term_id):
        return self.conn.execute("SELECT * FROM terms WHERE id=?", (term_id,)).fetchone()

    def update_term_info(self, term_id, definition=None, audio_path=None):
        """更新词汇的定义或音频路径"""
        if definition:
            self.conn.execute("UPDATE terms SET definition=? WHERE id=?", (definition, term_id))
        if audio_path:
            self.conn.execute("UPDATE terms SET audio_hash=? WHERE id=?", (audio_path, term_id))
        self.conn.commit()

    # --- 3. Sentences ---
    def add_sentence(self, domain_id, content):
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO sentences (domain_id, content_en) VALUES (?, ?)", (domain_id, content))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return self.conn.execute("SELECT id FROM sentences WHERE content_en=?", (content,)).fetchone()['id']

    def update_sentence_info(self, sent_id, content_cn=None, audio_path=None):
        """更新句子的翻译或音频路径"""
        if content_cn:
            self.conn.execute("UPDATE sentences SET content_cn=? WHERE id=?", (content_cn, sent_id))
        if audio_path:
            self.conn.execute("UPDATE sentences SET audio_hash=? WHERE id=?", (audio_path, sent_id))
        self.conn.commit()

    # --- 4. Search & Matches (核心逻辑升级) ---

    def search_sentences_by_text(self, domain_id, term_text):
        """
        动态文本匹配：在指定 Domain 下，查找包含 term_text 的所有句子
        """
        # 使用 SQLite 的 LIKE 进行模糊查询，%表示通配符
        query = f"%{term_text}%"
        # 排除太短的句子，排除已经建立关联的句子(可选，这里先全部查出来)
        sql = """
            SELECT * FROM sentences 
            WHERE domain_id = ? 
            AND content_en LIKE ?
        """
        return self.conn.execute(sql, (domain_id, query)).fetchall()

    def add_match(self, term_id, sentence_id):
        """建立词和句子的关联"""
        try:
            self.conn.execute("INSERT INTO matches (term_id, sentence_id) VALUES (?, ?)", (term_id, sentence_id))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass  # 已经关联过，忽略

    def get_matches_for_term(self, term_id):
        """获取已经确认关联的句子"""
        sql = """
            SELECT s.* FROM sentences s
            JOIN matches m ON s.id = m.sentence_id
            WHERE m.term_id = ?
        """
        return self.conn.execute(sql, (term_id,)).fetchall()