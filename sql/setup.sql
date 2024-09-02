-- noinspection SqlDialectInspectionForFile
-- noinspection SqlNoDataSourceInspectionForFile

CREATE TABLE IF NOT EXISTS fids (
    fid BIGINT PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    custody_address BYTEA NOT NULL,
    registered_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS storage (
    id BIGINT PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    timestamp TIMESTAMP NOT NULL,
    fid BIGINT NOT NULL,
    units BIGINT NOT NULL,
    expiry TIMESTAMP NOT NULL,
    CONSTRAINT unique_fid_units_expiry UNIQUE (fid, units, expiry)
);

CREATE TABLE IF NOT EXISTS links (
    id BIGINT PRIMARY KEY,
    fid BIGINT,
    target_fid BIGINT,
    hash BYTEA NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    type TEXT,
    display_timestamp TIMESTAMP,
    CONSTRAINT links_fid_target_fid_type_unique UNIQUE (fid, target_fid, type),
    CONSTRAINT links_hash_unique UNIQUE (hash)
);

CREATE TABLE IF NOT EXISTS casts (
    id BIGINT PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    timestamp TIMESTAMP NOT NULL,
    fid BIGINT NOT NULL,
    hash BYTEA NOT NULL,
    parent_hash BYTEA,
    parent_fid BIGINT,
    parent_url TEXT,
    text TEXT NOT NULL,
    embeds JSONB NOT NULL DEFAULT '{}'::jsonb,
    mentions BIGINT[] NOT NULL DEFAULT '{}'::bigint[],
    mentions_positions SMALLINT[] NOT NULL DEFAULT '{}'::smallint[],
    root_parent_hash BYTEA,
    root_parent_url TEXT,
    CONSTRAINT casts_hash_unique UNIQUE (hash)
);

CREATE TABLE IF NOT EXISTS user_data (
    id BIGINT PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    timestamp TIMESTAMP NOT NULL,
    fid BIGINT NOT NULL,
    hash BYTEA NOT NULL UNIQUE,
    type SMALLINT NOT NULL,
    value TEXT NOT NULL,
    CONSTRAINT user_data_fid_type_unique UNIQUE (fid, type)
);

CREATE TABLE IF NOT EXISTS reactions (
    id BIGINT PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    timestamp TIMESTAMP NOT NULL,
    reaction_type SMALLINT NOT NULL,
    fid BIGINT NOT NULL,
    hash BYTEA NOT NULL,
    target_hash BYTEA,
    target_fid BIGINT,
    target_url TEXT,
    CONSTRAINT reactions_hash_unique UNIQUE (hash)
);

CREATE TABLE IF NOT EXISTS fnames (
    fname TEXT PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    custody_address BYTEA,
    expires_at TIMESTAMP,
    fid BIGINT,
    deleted_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS signers (
    id BIGINT PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    timestamp TIMESTAMP NOT NULL,
    fid BIGINT NOT NULL,
    hash BYTEA,
    custody_address BYTEA,
    signer BYTEA NOT NULL,
    name TEXT,
    app_fid BIGINT,
    CONSTRAINT unique_timestamp_fid_signer UNIQUE (timestamp, fid, signer)
);

CREATE TABLE IF NOT EXISTS verifications (
    id BIGINT PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    timestamp TIMESTAMP NOT NULL,
    fid BIGINT NOT NULL,
    hash BYTEA NOT NULL UNIQUE,
    claim JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS warpcast_power_users (
    fid BIGINT PRIMARY KEY,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS profile_with_addresses (
    fid BIGINT PRIMARY KEY,
    fname TEXT,
    display_name TEXT,
    avatar_url TEXT,
    bio TEXT,
    verified_addresses JSONB NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS file_tracking (
    file_name VARCHAR PRIMARY KEY,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS channels (
    id TEXT PRIMARY KEY,
    name TEXT,
    description TEXT,
    image_url TEXT,
    url TEXT
);

-- Reaction Query Indexes
CREATE INDEX IF NOT EXISTS idx_casts_hash
ON public.casts (hash);

CREATE INDEX IF NOT EXISTS idx_casts_root_parent_deleted
ON public.casts (root_parent_hash, deleted_at);

CREATE INDEX IF NOT EXISTS idx_reactions_target_type
ON public.reactions (target_hash, reaction_type);

CREATE INDEX IF NOT EXISTS idx_warpcast_power_users_fid
ON public.warpcast_power_users (fid);

-- Full neynar results indexes
CREATE INDEX IF NOT EXISTS idx_casts_root_parent_hash
ON public.casts (root_parent_hash);

CREATE INDEX IF NOT EXISTS idx_reactions_target_fid_type
ON public.reactions (target_hash, fid, reaction_type);

CREATE INDEX IF NOT EXISTS idx_casts_hash_parent_hash
ON public.casts (hash, parent_hash);

CREATE INDEX IF NOT EXISTS idx_profile_with_addresses_fid
ON public.profile_with_addresses (fid);

CREATE INDEX IF NOT EXISTS idx_casts_parent_hash
ON public.casts (parent_hash);

CREATE INDEX IF NOT EXISTS idx_casts_fid ON casts(fid);
CREATE INDEX IF NOT EXISTS idx_reactions_target_hash ON reactions(target_hash);
CREATE INDEX IF NOT EXISTS idx_casts_parent_hash ON casts(parent_hash);
CREATE INDEX IF NOT EXISTS idx_casts_timestamp ON casts(timestamp);