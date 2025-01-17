-- Guilds table
CREATE TABLE IF NOT EXISTS guilds (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    member_count INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Bot settings table
CREATE TABLE IF NOT EXISTS bot_settings (
    guild_id TEXT PRIMARY KEY,
    prefix TEXT DEFAULT '!',
    welcome_channel_id TEXT,
    audit_log_channel_id TEXT,
    role_log_channel_id TEXT,
    FOREIGN KEY(guild_id) REFERENCES guilds(id) ON DELETE CASCADE
);

-- User roles tracking table
CREATE TABLE IF NOT EXISTS user_roles (
    guild_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    role_id TEXT NOT NULL,
    assigned_by TEXT NOT NULL,
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (guild_id, user_id, role_id),
    FOREIGN KEY(guild_id) REFERENCES guilds(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_user_roles_guild ON user_roles(guild_id);

-- Command usage tracking table
CREATE TABLE IF NOT EXISTS command_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    command_name TEXT NOT NULL,
    used_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT 1,
    error_message TEXT,
    FOREIGN KEY(guild_id) REFERENCES guilds(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_command_usage_guild ON command_usage(guild_id);
CREATE INDEX IF NOT EXISTS idx_command_usage_user ON command_usage(user_id);
