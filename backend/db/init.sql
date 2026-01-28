-- DocTranslator 数据库初始化脚本
-- 创建数据库和表结构

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS doc_translator CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE doc_translator;

-- ============================================
-- 用户表（管理员）
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    email VARCHAR(100) UNIQUE COMMENT '邮箱',
    role VARCHAR(20) DEFAULT 'admin' COMMENT '角色（admin/user）',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='管理员用户表';

-- ============================================
-- 普通用户表
-- ============================================
CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    password VARCHAR(255) NOT NULL COMMENT '密码',
    email VARCHAR(100) UNIQUE COMMENT '邮箱',
    phone VARCHAR(20) COMMENT '手机号',
    max_space BIGINT DEFAULT 1073741824 COMMENT '最大存储空间（1GB）',
    used_space BIGINT DEFAULT 0 COMMENT '已使用空间',
    status VARCHAR(20) DEFAULT 'active' COMMENT '状态（active/suspended）',
    vip_level VARCHAR(20) DEFAULT 'free' COMMENT 'VIP等级',
    vip_expire_at DATETIME COMMENT 'VIP过期时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    last_login_at DATETIME COMMENT '最后登录时间',
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='普通用户表';

-- ============================================
-- 翻译任务表
-- ============================================
CREATE TABLE IF NOT EXISTS translates (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '任务ID',
    uuid VARCHAR(36) NOT NULL UNIQUE COMMENT '唯一标识符',
    customer_id INT COMMENT '用户ID',
    prompt_id INT COMMENT '提示词ID',
    file_name VARCHAR(255) NOT NULL COMMENT '原始文件名',
    file_path VARCHAR(500) NOT NULL COMMENT '原始文件路径',
    file_size BIGINT DEFAULT 0 COMMENT '文件大小（字节）',
    file_type VARCHAR(20) NOT NULL COMMENT '文件类型',
    source_lang VARCHAR(20) DEFAULT 'auto' COMMENT '源语言',
    target_lang VARCHAR(20) NOT NULL COMMENT '目标语言',
    model_name VARCHAR(50) DEFAULT 'gpt-3.5-turbo' COMMENT 'AI模型',
    thread_count INT DEFAULT 5 COMMENT '线程数',
    result_file_path VARCHAR(500) COMMENT '结果文件路径',
    total_segments INT DEFAULT 0 COMMENT '总段数',
    translated_segments INT DEFAULT 0 COMMENT '已翻译段数',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '状态',
    progress INT DEFAULT 0 COMMENT '进度（0-100）',
    error_message TEXT COMMENT '错误信息',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    started_at DATETIME COMMENT '开始时间',
    completed_at DATETIME COMMENT '完成时间',
    options JSON COMMENT '额外配置',
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
    FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE SET NULL,
    INDEX idx_customer (customer_id),
    INDEX idx_status (status),
    INDEX idx_uuid (uuid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='翻译任务表';

-- ============================================
-- 提示词表
-- ============================================
CREATE TABLE IF NOT EXISTS prompts (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '提示词ID',
    name VARCHAR(100) NOT NULL COMMENT '名称',
    description VARCHAR(500) COMMENT '描述',
    content TEXT NOT NULL COMMENT '提示词内容',
    category VARCHAR(50) DEFAULT 'general' COMMENT '分类',
    language VARCHAR(20) DEFAULT 'en' COMMENT '适用语言',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    is_default BOOLEAN DEFAULT FALSE COMMENT '是否默认',
    use_count INT DEFAULT 0 COMMENT '使用次数',
    created_by INT COMMENT '创建者ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='提示词表';

-- ============================================
-- 术语对照表
-- ============================================
CREATE TABLE IF NOT EXISTS comparisons (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '术语ID',
    source_term VARCHAR(500) NOT NULL COMMENT '源术语',
    target_term VARCHAR(500) NOT NULL COMMENT '目标术语',
    source_lang VARCHAR(20) NOT NULL COMMENT '源语言',
    target_lang VARCHAR(20) NOT NULL COMMENT '目标语言',
    category VARCHAR(100) COMMENT '分类',
    description VARCHAR(500) COMMENT '描述',
    context TEXT COMMENT '使用场景',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    priority INT DEFAULT 0 COMMENT '优先级',
    created_by INT COMMENT '创建者ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_langs (source_lang, target_lang)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='术语对照表';

-- ============================================
-- 系统配置表
-- ============================================
CREATE TABLE IF NOT EXISTS settings (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '配置ID',
    `key` VARCHAR(100) NOT NULL UNIQUE COMMENT '配置键',
    value TEXT COMMENT '配置值',
    value_type VARCHAR(20) DEFAULT 'string' COMMENT '值类型',
    category VARCHAR(50) DEFAULT 'general' COMMENT '分类',
    description VARCHAR(500) COMMENT '描述',
    is_public BOOLEAN DEFAULT FALSE COMMENT '是否公开',
    is_editable BOOLEAN DEFAULT TRUE COMMENT '是否可编辑',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_key (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统配置表';

-- ============================================
-- 插入初始数据
-- ============================================

-- 插入默认管理员（用户名: admin, 密码: admin123）
-- 密码哈希是 bcrypt 加密后的值
INSERT INTO users (username, password_hash, email, role) VALUES
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEmc0i', 'admin@doctranslator.com', 'admin')
ON DUPLICATE KEY UPDATE username=username;

-- 插入默认提示词
INSERT INTO prompts (name, description, content, category, is_default) VALUES
('通用翻译', '适用于一般文档翻译', 'You are a professional translator. Please translate the following text into {target_lang}, maintaining the original meaning and style.', 'general', TRUE),
('技术文档', '适用于技术文档翻译', 'You are a technical document translator. Please translate the following technical text into {target_lang}, ensuring technical terms are accurately translated.', 'technical', FALSE),
('学术论文', '适用于学术论文翻译', 'You are an academic paper translator. Please translate the following academic text into {target_lang}, maintaining academic tone and terminology.', 'academic', FALSE)
ON DUPLICATE KEY UPDATE name=name;

-- 插入系统配置
INSERT INTO settings (`key`, value, value_type, category, description, is_public) VALUES
('max_file_size', '104857600', 'int', 'upload', '最大文件上传大小（100MB）', TRUE),
('supported_formats', '["docx","pdf","xlsx","pptx","md","txt"]', 'json', 'upload', '支持的文件格式', TRUE),
('default_model', 'gpt-3.5-turbo', 'string', 'translation', '默认AI模型', TRUE),
('max_thread_count', '10', 'int', 'translation', '最大翻译线程数', FALSE)
ON DUPLICATE KEY UPDATE `key`=`key`;
