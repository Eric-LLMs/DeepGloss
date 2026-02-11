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

        # 自动升级旧数据库：增加新字段，静默处理已存在的错误
        try:
            self.conn.execute("ALTER TABLE sentences ADD COLUMN cn_explanation TEXT")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            self.conn.execute("ALTER TABLE terms ADD COLUMN frequency INTEGER DEFAULT 1")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            self.conn.execute("ALTER TABLE terms ADD COLUMN star_level INTEGER DEFAULT 1")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass

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
    def add_term(self, domain_id, word, definition="", frequency=1, star_level=1):
        """防重复添加：如果同 Domain 下存在该词（忽略大小写），直接跳过"""
        cursor = self.conn.execute(
            "SELECT id FROM terms WHERE domain_id=? AND LOWER(word)=LOWER(?)", (domain_id, word)
        )
        res = cursor.fetchone()

        if res:
            # 已经存在，直接返回已存在词的 ID，不重复导入
            term_id = res['id']
            # 如果想在重复导入时累加词频，可以取消注释下面的代码
            # self.conn.execute("UPDATE terms SET frequency=frequency+? WHERE id=?", (frequency, term_id))
            # self.conn.commit()
            return term_id

        # 不存在则插入
        cursor = self.conn.execute(
            "INSERT INTO terms (domain_id, word, definition, frequency, star_level) VALUES (?, ?, ?, ?, ?)",
            (domain_id, word, definition, frequency, star_level)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_terms_by_domain(self, domain_id):
        return self.conn.execute("SELECT * FROM terms WHERE domain_id=?", (domain_id,)).fetchall()

    def get_term_by_id(self, term_id):
        return self.conn.execute("SELECT * FROM terms WHERE id=?", (term_id,)).fetchone()

    def update_term_info(self, term_id, definition=None, audio_path=None, star_level=None):
        """更新词汇的定义、音频路径或星级"""
        if definition is not None:
            self.conn.execute("UPDATE terms SET definition=? WHERE id=?", (definition, term_id))
        if audio_path is not None:
            self.conn.execute("UPDATE terms SET audio_hash=? WHERE id=?", (audio_path, term_id))
        if star_level is not None:
            self.conn.execute("UPDATE terms SET star_level=? WHERE id=?", (star_level, term_id))
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

    def update_sentence_info(self, sent_id, content_cn=None, audio_path=None, cn_explanation=None):
        if content_cn is not None:
            self.conn.execute("UPDATE sentences SET content_cn=? WHERE id=?", (content_cn, sent_id))
        if audio_path is not None:
            self.conn.execute("UPDATE sentences SET audio_hash=? WHERE id=?", (audio_path, sent_id))
        if cn_explanation is not None:
            self.conn.execute("UPDATE sentences SET cn_explanation=? WHERE id=?", (cn_explanation, sent_id))
        self.conn.commit()

    # --- 4. Search & Matches ---
    def search_sentences_by_text(self, domain_id, term_text):
        query = f"%{term_text}%"
        sql = """
            SELECT * FROM sentences 
            WHERE domain_id = ? 
            AND content_en LIKE ?
        """
        return self.conn.execute(sql, (domain_id, query)).fetchall()

    def add_match(self, term_id, sentence_id):
        try:
            self.conn.execute("INSERT INTO matches (term_id, sentence_id) VALUES (?, ?)", (term_id, sentence_id))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass

    def get_matches_for_term(self, term_id):
        sql = """
            SELECT s.* FROM sentences s
            JOIN matches m ON s.id = m.sentence_id
            WHERE m.term_id = ?
        """
        return self.conn.execute(sql, (term_id,)).fetchall()