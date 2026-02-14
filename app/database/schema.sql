-- 1. Domain Table
CREATE TABLE IF NOT EXISTS domain (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Terms Table
CREATE TABLE IF NOT EXISTS terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain_id INTEGER,
    word TEXT NOT NULL,
    definition TEXT,
    frequency INTEGER DEFAULT 1,
    star_level INTEGER DEFAULT 1,
    audio_hash TEXT,
    is_active INTEGER DEFAULT 1,  -- 🌟 新增字段：1 表示 Enable (默认)，0 表示 Disable
    FOREIGN KEY(domain_id) REFERENCES domain(id) ON DELETE CASCADE
);

-- 3. Sentences Table
CREATE TABLE IF NOT EXISTS sentences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain_id INTEGER,
    origin_source TEXT,
    content_en TEXT UNIQUE,
    content_cn TEXT,
    audio_hash TEXT,
    cn_explanation TEXT,
    FOREIGN KEY(domain_id) REFERENCES domain(id) ON DELETE CASCADE
);

-- 4. Matches Table
CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_id INTEGER,
    sentence_id INTEGER,
    FOREIGN KEY(term_id) REFERENCES terms(id) ON DELETE CASCADE,
    FOREIGN KEY(sentence_id) REFERENCES sentences(id) ON DELETE CASCADE
);