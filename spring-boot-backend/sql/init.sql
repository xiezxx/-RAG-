-- 初始化数据库表
-- 答辩前换成 MySQL，这个给 H2 开发用

CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(200) NOT NULL,
    name VARCHAR(100) DEFAULT '',
    phone VARCHAR(30) DEFAULT '',
    role VARCHAR(20) DEFAULT 'USER',
    status VARCHAR(20) DEFAULT '启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS labour_cases (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    case_number VARCHAR(100),
    court VARCHAR(200),
    judge_date VARCHAR(50),
    case_content TEXT,
    issues TEXT,
    reasoning TEXT,
    judgment TEXT,
    legal_basis TEXT,
    keywords TEXT,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT,
    question TEXT,
    answer TEXT,
    sources TEXT,
    rating INT DEFAULT 0,
    feedback VARCHAR(500) DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS statutes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(50),
    article_count INT DEFAULT 0,
    publish_date VARCHAR(20) DEFAULT '',
    effective_date VARCHAR(20) DEFAULT '',
    expiry_date VARCHAR(20) DEFAULT '',
    status VARCHAR(20) DEFAULT '现行有效',
    document_number VARCHAR(100) DEFAULT '',
    issuing_authority VARCHAR(200) DEFAULT '',
    applicable_region VARCHAR(200) DEFAULT '',
    applicable_subject VARCHAR(200) DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 默认管理员（密码 admin123，BCrypt 哈希）
INSERT INTO users (username, password, role) VALUES ('admin', '$2b$10$M0KMx22Wm4XqpnALN4ztF.mgba4nt754D63mZDJWZTbrPDx.mODRG', 'ADMIN');
