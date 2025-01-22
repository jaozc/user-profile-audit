-- init.sql

-- Creation of the user_profiles table
-- This table stores user profile information, including a unique identifier,
-- name, email, and a flag indicating if the profile is deleted.
CREATE TABLE IF NOT EXISTS user_profiles (
    id VARCHAR(255) PRIMARY KEY,          -- Unique identifier for the user profile
    name VARCHAR(255) NOT NULL,           -- Name of the user, cannot be null
    email VARCHAR(255) NOT NULL UNIQUE,   -- User's email, must be unique and cannot be null
    is_deleted BOOLEAN DEFAULT FALSE       -- Soft delete flag, defaults to false
);

-- Creation of the audit_events table
-- This table records audit events related to user actions, including the event's
-- unique identifier, associated user ID, action performed, timestamp, resource,
-- details about the event, and any changes made.
CREATE TABLE IF NOT EXISTS audit_events (
    id VARCHAR(255) PRIMARY KEY,           -- Unique identifier for the audit event
    user_id VARCHAR(255),                  -- ID of the user associated with the event
    action VARCHAR(255),                   -- Action performed that triggered the audit event
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp of when the event occurred
    resource VARCHAR(255),                  -- Resource that the action was performed on
    details TEXT,                          -- Optional details about the event
    changes JSONB                          -- JSONB field to record changes made during the event
);