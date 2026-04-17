-- ClearTimerBot PostgreSQL Schema

CREATE TABLE IF NOT EXISTS servers (
    server_id   TEXT PRIMARY KEY,
    server_name TEXT NOT NULL DEFAULT '',
    timezone    TEXT,
    language    TEXT DEFAULT 'en'
);

CREATE TABLE IF NOT EXISTS channels (
    server_id       TEXT NOT NULL REFERENCES servers(server_id) ON DELETE CASCADE,
    channel_id      TEXT NOT NULL,
    timer           TEXT NOT NULL,
    next_run_time   TIMESTAMPTZ NOT NULL,
    view_message_id TEXT,
    PRIMARY KEY (server_id, channel_id)
);

CREATE TABLE IF NOT EXISTS ignored_messages (
    server_id  TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    message_id TEXT NOT NULL,
    PRIMARY KEY (server_id, channel_id, message_id),
    FOREIGN KEY (server_id, channel_id) REFERENCES channels(server_id, channel_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ignored_users (
    server_id  TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    user_id    TEXT NOT NULL,
    PRIMARY KEY (server_id, channel_id, user_id),
    FOREIGN KEY (server_id, channel_id) REFERENCES channels(server_id, channel_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS blacklist (
    server_id      TEXT PRIMARY KEY,
    server_name    TEXT NOT NULL DEFAULT 'Unknown',
    blacklisted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reason         TEXT,
    blacklisted_by TEXT
);

CREATE TABLE IF NOT EXISTS removed_servers (
    server_id      TEXT PRIMARY KEY,
    server_name    TEXT NOT NULL,
    removed_at     TIMESTAMPTZ NOT NULL,
    removal_reason TEXT
);

CREATE TABLE IF NOT EXISTS errors (
    error_id    TEXT PRIMARY KEY,
    timestamp   TIMESTAMPTZ NOT NULL,
    level       TEXT NOT NULL,
    area        TEXT NOT NULL,
    message     TEXT NOT NULL,
    stack_trace TEXT,
    guild_id    TEXT,
    channel_id  TEXT,
    user_id     TEXT,
    command     TEXT
);

CREATE TABLE IF NOT EXISTS config_admins (
    user_id TEXT PRIMARY KEY
);

-- Timezone abbreviation -> IANA timezone name mappings (e.g. 'EST' -> 'America/New_York')
-- Populate this table manually with your desired mappings.
CREATE TABLE IF NOT EXISTS config_timezones (
    abbreviation TEXT PRIMARY KEY,
    timezone     TEXT NOT NULL
);

