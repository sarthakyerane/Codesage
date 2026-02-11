-- CodeSage Database Schema
CREATE DATABASE IF NOT EXISTS codesage;
USE codesage;

-- Fix for MySQL 8 authentication issues
ALTER USER 'codesage_user'@'%' IDENTIFIED WITH mysql_native_password BY 'codesage_pass';
FLUSH PRIVILEGES;

CREATE TABLE IF NOT EXISTS files (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    file_path   VARCHAR(512) NOT NULL,
    file_name   VARCHAR(255) NOT NULL,
    upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    function_count INT DEFAULT 0,
    UNIQUE KEY uq_filepath (file_path)
);

CREATE TABLE IF NOT EXISTS functions (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    file_id       INT NOT NULL,
    function_name VARCHAR(255) NOT NULL,
    return_type   VARCHAR(128),
    parameters    TEXT,
    line_start    INT,
    line_end      INT,
    complexity    INT DEFAULT 1,
    tags          VARCHAR(512),
    chroma_id     VARCHAR(255),
    body_preview  TEXT,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    INDEX idx_function_name (function_name),
    INDEX idx_file_id (file_id)
);

CREATE TABLE IF NOT EXISTS call_edges (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    caller_id   INT NOT NULL,
    callee_name VARCHAR(255) NOT NULL,
    FOREIGN KEY (caller_id) REFERENCES functions(id) ON DELETE CASCADE,
    INDEX idx_caller (caller_id)
);
