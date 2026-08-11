-- MySQL 建表脚本（Spring Boot 启动自动执行）
-- 先手动创建库: CREATE DATABASE IF NOT EXISTS labour_law DEFAULT CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(200) NOT NULL,
    name VARCHAR(100) DEFAULT '',
    phone VARCHAR(30) DEFAULT '',
    role VARCHAR(20) DEFAULT 'USER',
    status VARCHAR(20) DEFAULT '启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS chat_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT,
    question TEXT CHARACTER SET utf8mb4,
    answer TEXT CHARACTER SET utf8mb4,
    sources TEXT CHARACTER SET utf8mb4,
    rating INT DEFAULT 0,
    feedback VARCHAR(500) DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 默认管理员（密码 admin123，已 BCrypt 哈希）
INSERT IGNORE INTO users (username, password, role) VALUES ('admin', '$2b$10$M0KMx22Wm4XqpnALN4ztF.mgba4nt754D63mZDJWZTbrPDx.mODRG', 'ADMIN');
