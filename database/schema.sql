-- Database Schema for Telegram MT5 Trading Assistant
-- SQLite schema - production-ready, migration-friendly

-- Users table: Telegram users
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Settings: per-user configuration
CREATE TABLE IF NOT EXISTS user_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    default_symbol_base TEXT DEFAULT 'XAU',
    symbol_prefix TEXT DEFAULT '',
    symbol_suffix TEXT DEFAULT '',
    default_order_type TEXT DEFAULT 'LIMIT',
    risk_type TEXT DEFAULT 'fixed_usd' CHECK(risk_type IN ('fixed_usd', 'percent')),
    risk_value REAL DEFAULT 100.0,
    default_rr_ratio REAL DEFAULT 2.0,
    default_account_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (default_account_id) REFERENCES accounts(id)
);

-- MT5 Accounts: User's trading accounts
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    account_number INTEGER NOT NULL,
    broker_name TEXT NOT NULL,
    account_name TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, account_number)
);

-- Setups: User-defined trade setups
CREATE TABLE IF NOT EXISTS setups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    setup_code TEXT NOT NULL,
    setup_name TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, setup_code)
);

-- Trades: Complete trade journal
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,

    -- Trade parameters
    symbol TEXT NOT NULL,
    order_type TEXT NOT NULL CHECK(order_type IN ('LIMIT_BUY', 'LIMIT_SELL')),
    entry REAL NOT NULL,
    sl REAL NOT NULL,
    tp REAL NOT NULL,
    volume REAL NOT NULL,

    -- Risk management
    risk_usd REAL NOT NULL,
    rr REAL,

    -- Trade psychology & setup
    emotion TEXT NOT NULL CHECK(emotion IN ('calm', 'confident', 'fomo', 'stressed', 'revenge')),
    setup_code TEXT NOT NULL,
    chart_url TEXT,

    -- MT5 execution
    mt5_ticket INTEGER,
    mt5_open_price REAL,
    mt5_close_price REAL,
    mt5_open_time TIMESTAMP,
    mt5_close_time TIMESTAMP,
    mt5_profit REAL,

    -- Status tracking
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'filled', 'closed', 'cancelled', 'failed')),

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES accounts(id),
    FOREIGN KEY (setup_code, user_id) REFERENCES setups(setup_code, user_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_account_id ON trades(account_id);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
CREATE INDEX IF NOT EXISTS idx_trades_created_at ON trades(created_at);
CREATE INDEX IF NOT EXISTS idx_trades_emotion ON trades(emotion);
CREATE INDEX IF NOT EXISTS idx_trades_setup_code ON trades(setup_code);
CREATE INDEX IF NOT EXISTS idx_setups_user_id ON setups(user_id);
CREATE INDEX IF NOT EXISTS idx_accounts_user_id ON accounts(user_id);

-- Trigger to update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_users_timestamp
AFTER UPDATE ON users
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_user_settings_timestamp
AFTER UPDATE ON user_settings
BEGIN
    UPDATE user_settings SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_accounts_timestamp
AFTER UPDATE ON accounts
BEGIN
    UPDATE accounts SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_trades_timestamp
AFTER UPDATE ON trades
BEGIN
    UPDATE trades SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
