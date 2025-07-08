-- Migration script for mg_ prefixed tables
-- This creates new tables with mg_ prefix to avoid conflicts with existing tables

-- Create mg_users table
CREATE TABLE IF NOT EXISTS mg_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    phone_number VARCHAR(15),
    role VARCHAR(20) DEFAULT 'admin' NOT NULL,
    user_type VARCHAR(20) DEFAULT 'admin' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_login DATETIME,
    failed_login_attempts INT DEFAULT 0,
    locked_until DATETIME,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_phone (phone_number)
);

-- Create mg_loans table
CREATE TABLE IF NOT EXISTS mg_loans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    loan_id VARCHAR(20) UNIQUE NOT NULL,
    user_id INT NOT NULL,
    original_amount DECIMAL(10,2) NOT NULL,
    outstanding_balance DECIMAL(10,2) NOT NULL,
    interest_rate DECIMAL(5,2) DEFAULT 15.0,
    term_months INT DEFAULT 12,
    status VARCHAR(20) DEFAULT 'active' NOT NULL,
    disbursement_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    completed_at DATETIME,
    
    FOREIGN KEY (user_id) REFERENCES mg_users(id) ON DELETE CASCADE,
    INDEX idx_loan_id (loan_id),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
);

-- Create mg_transactions table
CREATE TABLE IF NOT EXISTS mg_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    loan_id INT,
    reference VARCHAR(100) UNIQUE NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    method VARCHAR(20) NOT NULL,
    transaction_type VARCHAR(20) DEFAULT 'loan_payment' NOT NULL,
    poll_url TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    instructions TEXT,
    paynow_reference VARCHAR(100),
    hash VARCHAR(256),
    redirect_url TEXT,
    has_redirect BOOLEAN DEFAULT FALSE,
    remoteotpurl TEXT,
    otpreference VARCHAR(100),
    description TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    paid_at DATETIME,
    completed_at DATETIME,
    paynow_result TEXT,
    otp_response TEXT,
    is_test BOOLEAN DEFAULT FALSE,
    
    FOREIGN KEY (user_id) REFERENCES mg_users(id) ON DELETE SET NULL,
    FOREIGN KEY (loan_id) REFERENCES mg_loans(id) ON DELETE SET NULL,
    INDEX idx_reference (reference),
    INDEX idx_user_id (user_id),
    INDEX idx_loan_id (loan_id),
    INDEX idx_status (status),
    INDEX idx_method (method)
);

-- Create mg_login_attempts table
CREATE TABLE IF NOT EXISTS mg_login_attempts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT,
    success BOOLEAN DEFAULT FALSE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    INDEX idx_username (username),
    INDEX idx_ip_address (ip_address),
    INDEX idx_created_at (created_at)
);

-- Insert sample admin user (password: admin123)
INSERT IGNORE INTO mg_users (username, email, password_hash, full_name, role, user_type) 
VALUES ('admin', 'admin@loanpay.com', 'scrypt:32768:8:1$8X9Q2vZJzNbXqY3P$7d4e9c8f5a6b3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1', 'System Administrator', 'admin', 'admin');

-- Verify tables were created
SELECT 'mg_users' as table_name, COUNT(*) as record_count FROM mg_users
UNION ALL
SELECT 'mg_loans' as table_name, COUNT(*) as record_count FROM mg_loans
UNION ALL  
SELECT 'mg_transactions' as table_name, COUNT(*) as record_count FROM mg_transactions
UNION ALL
SELECT 'mg_login_attempts' as table_name, COUNT(*) as record_count FROM mg_login_attempts;
