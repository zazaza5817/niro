
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