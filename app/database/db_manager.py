import sqlite3
import os
from pathlib import Path

# Define paths relative to this file
CURRENT_DIR = Path(__file__).parent
DB_PATH = CURRENT_DIR.parent.parent / "data" / "deepgloss.db"
SCHEMA_PATH = CURRENT_DIR / "schema.sql"


class DBManager:
    def __init__(self):
        # Ensure database directory exists
        if not DB_PATH.parent.exists():
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Connect to SQLite
        # FIX 1: Set timeout=30.0 so Streamlit waits for external software to release the lock instead of crashing instantly.
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=30.0)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

        # FIX 2: Enable WAL (Write-Ahead Logging) mode.
        # This allows simultaneous readers and writers, permanently solving "database is locked".
        self.conn.execute("PRAGMA journal_mode=WAL")

        # Initialize schema
        self._execute_schema_script()

    def _execute_schema_script(self):
        """Initializes tables and performs safe schema migrations."""
        if SCHEMA_PATH.exists():
            with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
                self.conn.executescript(f.read())

        # Safe migrations for existing databases (adds columns if missing)
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

        try:
            self.conn.execute("ALTER TABLE terms ADD COLUMN image_paths TEXT")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass

    # ==========================================
    # 1. Domain Operations
    # ==========================================
    def add_domain(self, name):
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO domain (name) VALUES (?)", (name,))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # If exists, return existing ID
            cursor = self.conn.execute("SELECT id FROM domain WHERE name=?", (name,))
            return cursor.fetchone()['id']

    def get_all_domains(self):
        return self.conn.execute("SELECT id, name FROM domain").fetchall()

    # ==========================================
    # 2. Term Operations
    # ==========================================
    def add_term(self, domain_id, word, definition="", frequency=1, star_level=1):
        # Check for duplicates (case-insensitive)
        cursor = self.conn.execute(
            "SELECT id FROM terms WHERE domain_id=? AND LOWER(word)=LOWER(?)", (domain_id, word)
        )
        res = cursor.fetchone()

        if res:
            return res['id']

        # Insert new term
        cursor = self.conn.execute(
            "INSERT INTO terms (domain_id, word, definition, frequency, star_level) VALUES (?, ?, ?, ?, ?)",
            (domain_id, word, definition, frequency, star_level)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_terms_by_domain(self, domain_id, only_active=False):
        if only_active:
            return self.conn.execute("SELECT * FROM terms WHERE domain_id=? AND is_active=1", (domain_id,)).fetchall()
        return self.conn.execute("SELECT * FROM terms WHERE domain_id=?", (domain_id,)).fetchall()

    def bulk_update_terms(self, updates_list):
        cursor = self.conn.cursor()
        for row in updates_list:
            cursor.execute("""
                UPDATE terms 
                SET word = ?, definition = ?, star_level = ?, is_active = ?
                WHERE id = ?
            """, (row['word'], row['definition'], row['star_level'], row['is_active'], row['id']))
        self.conn.commit()

    def get_term_by_id(self, term_id):
        return self.conn.execute("SELECT * FROM terms WHERE id=?", (term_id,)).fetchone()

    def update_term_info(self, term_id, definition=None, audio_path=None, star_level=None, image_paths=None):
        if definition is not None:
            self.conn.execute("UPDATE terms SET definition=? WHERE id=?", (definition, term_id))
        if audio_path is not None:
            self.conn.execute("UPDATE terms SET audio_hash=? WHERE id=?", (audio_path, term_id))
        if star_level is not None:
            self.conn.execute("UPDATE terms SET star_level=? WHERE id=?", (star_level, term_id))
        if image_paths is not None:
            self.conn.execute("UPDATE terms SET image_paths=? WHERE id=?", (image_paths, term_id))
        self.conn.commit()

    # ==========================================
    # 3. Sentence Operations
    # ==========================================
    def add_sentence(self, domain_id, content):
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO sentences (domain_id, content_en) VALUES (?, ?)", (domain_id, content))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Return existing ID if content is identical
            return self.conn.execute("SELECT id FROM sentences WHERE content_en=?", (content,)).fetchone()['id']

    def get_sentences_by_domain(self, domain_id):
        return self.conn.execute("SELECT * FROM sentences WHERE domain_id=?", (domain_id,)).fetchall()

    def update_sentence_info(self, sent_id, content_cn=None, audio_path=None, cn_explanation=None):
        if content_cn is not None:
            self.conn.execute("UPDATE sentences SET content_cn=? WHERE id=?", (content_cn, sent_id))
        if audio_path is not None:
            self.conn.execute("UPDATE sentences SET audio_hash=? WHERE id=?", (audio_path, sent_id))
        if cn_explanation is not None:
            print(sent_id)
            self.conn.execute("UPDATE sentences SET cn_explanation=? WHERE id=?", (cn_explanation, sent_id))
        self.conn.commit()

    # ==========================================
    # 4. Search & Matches (Hybrid Logic)
    # ==========================================
    def search_sentences_by_text(self, domain_id, term_text):
        query = f"%{term_text}%"
        sql = """
            SELECT * FROM sentences 
            WHERE domain_id = ? 
            AND content_en LIKE ?
        """
        return self.conn.execute(sql, (domain_id, query)).fetchall()

    def search_sentences_hybrid(self, domain_id, term_text):
        """
        Hybrid Independent Search:
        1. Search SQLite (Exact/Fuzzy).
        2. If empty, search Independent VectorDB (Semantic).
        """
        # 1. Try SQLite
        sql_rows = self.search_sentences_by_text(domain_id, term_text)
        candidates = [dict(r) for r in sql_rows]

        # 2. If SQLite yielded no results, try VectorDB
        if not candidates:
            try:
                # Lazy import to avoid circular dependency
                from app.services.vector_manager import VectorManager
                vm = VectorManager()

                # Search for similar text in independent store
                vector_texts = vm.search_similar_text(term_text, domain_id, n_results=5)

                # Wrap raw text into a dict structure compatible with UI
                # ID is marked as 'vdb_only' to indicate it's not in SQL yet
                for i, txt in enumerate(vector_texts):
                    candidates.append({
                        "id": f"vdb_{i}",
                        "content_en": txt,
                        "domain_id": domain_id
                    })
            except Exception as e:
                print(f"Vector search failed: {e}")

        return candidates

    def add_match(self, term_id, sentence_id):
        """
        Links a term to a sentence.
        Fix: Checks for existence first to prevent duplicate rows.
        """
        # 1. Check if the link already exists
        check_sql = "SELECT id FROM matches WHERE term_id = ? AND sentence_id = ?"
        existing = self.conn.execute(check_sql, (term_id, sentence_id)).fetchone()

        if existing:
            return  # Skip insertion if already linked

        # 2. Insert if not found
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