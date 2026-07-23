-- Create table for common passwords
CREATE TABLE IF NOT EXISTS common_passwords (
    id SERIAL PRIMARY KEY,
    password VARCHAR(255) UNIQUE NOT NULL
);

-- Create table for user accounts
CREATE TABLE IF NOT EXISTS "2402242" (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);