-- PromptFlow MySQL Setup
CREATE DATABASE IF NOT EXISTS promptflow CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'pf_user'@'localhost' IDENTIFIED BY 'pf_pass_2024';
GRANT ALL PRIVILEGES ON promptflow.* TO 'pf_user'@'localhost';
FLUSH PRIVILEGES;
-- Tables auto-created by SQLAlchemy on startup
