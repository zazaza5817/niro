
CREATE TABLE IF NOT EXISTS users (
    tg_id INTEGER PRIMARY KEY,
    status TEXT,
    expiry TEXT,
    connection_link TEXT,
    email TEXT,
    server_id INTEGER,
    id TEXT,
    jwt_token TEXT
);

CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);

-- Таблица реферальных кодов
CREATE TABLE IF NOT EXISTS referral_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    max_uses INTEGER DEFAULT NULL, -- NULL = безлимитно
    current_uses INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT NULL, -- NULL = не истекает
    is_active BOOLEAN DEFAULT TRUE
);

-- Таблица использований реферальных кодов
CREATE TABLE IF NOT EXISTS referral_usage (
    id SERIAL PRIMARY KEY,
    referral_code_id INTEGER REFERENCES referral_codes(id),
    user_tg_id INTEGER REFERENCES users(tg_id),
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(referral_code_id, user_tg_id)
);

CREATE INDEX IF NOT EXISTS idx_referral_codes_code ON referral_codes(code);
CREATE INDEX IF NOT EXISTS idx_referral_usage_user ON referral_usage(user_tg_id);

-- Таблица реферальных планов (кастомные и дефолтные планы для реферальных кодов)
CREATE TABLE IF NOT EXISTS referral_plans (
    id SERIAL PRIMARY KEY,
    referral_code_id INTEGER REFERENCES referral_codes(id) ON DELETE CASCADE,
    is_default BOOLEAN DEFAULT FALSE, -- true = дефолтный план из plans.json, false = кастомный
    default_plan_payload VARCHAR(50), -- payload из plans.json (если is_default = true)
    discount_percent INTEGER DEFAULT 0, -- скидка в процентах
    -- Кастомные поля плана (если is_default = false)
    price INTEGER,
    duration INTEGER,
    title TEXT,
    description TEXT,
    label TEXT,
    payload VARCHAR(50),
    name VARCHAR(100),
    price_per_month INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_referral_plans_code ON referral_plans(referral_code_id);
CREATE INDEX IF NOT EXISTS idx_referral_plans_payload ON referral_plans(default_plan_payload);
CREATE INDEX IF NOT EXISTS idx_referral_plans_is_default ON referral_plans(is_default);