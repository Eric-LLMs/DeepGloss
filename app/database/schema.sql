-- 1. 领域表 (原 projects 表)
CREATE TABLE IF NOT EXISTS domain (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. 词汇表 (Terms)
CREATE TABLE IF NOT EXISTS terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain_id INTEGER,
    word TEXT NOT NULL,
    definition TEXT,
    frequency INTEGER DEFAULT 0,  -- [新增] 存储词频
    audio_hash TEXT,
    FOREIGN KEY(domain_id) REFERENCES domain(id) ON DELETE CASCADE
);

-- 3. 句子表 (Sentences)
-- 注意：这里外键必须指向 domain(id)
CREATE TABLE IF NOT EXISTS sentences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain_id INTEGER,
    origin_source TEXT,
    content_en TEXT UNIQUE,
    content_cn TEXT,
    audio_hash TEXT,
    FOREIGN KEY(domain_id) REFERENCES domain(id) ON DELETE CASCADE
);

-- 4. 关联表 (Matches)
CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_id INTEGER,
    sentence_id INTEGER,
    FOREIGN KEY(term_id) REFERENCES terms(id) ON DELETE CASCADE,
    FOREIGN KEY(sentence_id) REFERENCES sentences(id) ON DELETE CASCADE
);