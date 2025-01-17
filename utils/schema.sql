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

-- Custom commands table
CREATE TABLE IF NOT EXISTS custom_commands (
    guild_id TEXT,
    name TEXT,
    response TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (guild_id, name),
    FOREIGN KEY(guild_id) REFERENCES guilds(id) ON DELETE CASCADE
);

-- Tickets table
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    ticket_type TEXT NOT NULL,
    status TEXT DEFAULT 'open',
    claimed_by TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    closed_at DATETIME,
    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(guild_id) REFERENCES guilds(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_tickets_guild_user ON tickets(guild_id, user_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);

-- Ticket messages table
CREATE TABLE IF NOT EXISTS ticket_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_ticket_messages_ticket ON ticket_messages(ticket_id);

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
