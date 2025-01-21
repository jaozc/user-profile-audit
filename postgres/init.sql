-- init.sql

-- Criação da tabela de perfis de usuários
CREATE TABLE IF NOT EXISTS user_profiles (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- Criação da tabela de eventos de auditoria
CREATE TABLE IF NOT EXISTS audit_events (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    action VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resource VARCHAR(255),
    details TEXT,
    changes JSONB
);