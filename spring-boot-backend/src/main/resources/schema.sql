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

-- 科普专题文章（生成式科普，内容由 RAG+LLM 生成后缓存）
CREATE TABLE IF NOT EXISTS popularization_articles (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL DEFAULT '',
    description VARCHAR(500) DEFAULT '',
    search_query VARCHAR(200) DEFAULT '',
    content MEDIUMTEXT,
    sources TEXT,
    generated_at TIMESTAMP NULL DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_title (title)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 案情诊断报告（诊断成功后落库，支持历史查看与下载）
CREATE TABLE IF NOT EXISTS diagnosis_reports (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    reason VARCHAR(50) NOT NULL DEFAULT '',
    years DECIMAL(4,1) NOT NULL DEFAULT 0,
    monthly_wage DECIMAL(10,2) NOT NULL DEFAULT 0,
    has_contract TINYINT(1) NOT NULL DEFAULT 1,
    description TEXT,
    summary TEXT,
    issues TEXT,
    warnings TEXT,
    next_steps TEXT,
    estimation TEXT,
    sources TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    KEY idx_report_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 操作日志（管理员可查，此前漏建——全新部署需此表）
CREATE TABLE IF NOT EXISTS operation_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT,
    username VARCHAR(50) DEFAULT '',
    action VARCHAR(50) DEFAULT '',
    target VARCHAR(200) DEFAULT '',
    ip VARCHAR(50) DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    KEY idx_olog_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 登录记录（每次登录尝试：成功/失败 + IP，管理员可查）
CREATE TABLE IF NOT EXISTS login_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT,
    username VARCHAR(50) DEFAULT '',
    ip VARCHAR(50) DEFAULT '',
    success TINYINT(1) NOT NULL DEFAULT 0,
    message VARCHAR(200) DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    KEY idx_llog_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT IGNORE INTO popularization_articles (title, category, description, search_query) VALUES
('加班费怎么算？', '工资报酬', '加班工资的计算基数、倍率与举证要点', '加班费 加班工资 计算基数 延时加班 休息日加班 法定节假日'),
('经济补偿金，你该拿多少？', '离职维权', 'N、N+1、2N 的区别与经济补偿金计算规则', '经济补偿金 解除劳动合同 工作年限 月工资'),
('试用期里的法律红线', '劳动合同', '试用期时长、工资标准与违法约定试用期的后果', '试用期 劳动合同 试用期工资 违法约定试用期'),
('竞业限制与保密协议', '劳动合同', '竞业限制的适用对象、期限与经济补偿', '竞业限制 保密协议 违约金 经济补偿'),
('工伤认定与赔偿指南', '工伤保险', '工伤认定的情形、申请流程与赔偿项目', '工伤 工伤认定 工伤保险 工伤赔偿 职业病'),
('女职工的特殊劳动保护', '特殊保护', '三期保护、产假与禁忌劳动范围', '女职工 孕期 产期 哺乳期 产假 劳动保护'),
('被辞退怎么办？离职维权指南', '离职维权', '违法解除的认定、赔偿金与仲裁维权流程', '违法解除 辞退 经济补偿 赔偿金 劳动仲裁'),
('不签劳动合同的双倍工资', '劳动合同', '未签书面劳动合同的法律后果与双倍工资规则', '未签订书面劳动合同 双倍工资 事实劳动关系');
