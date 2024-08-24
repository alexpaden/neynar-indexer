-- noinspection SqlDialectInspectionForFile
-- noinspection SqlNoDataSourceInspectionForFile

CREATE TABLE IF NOT EXISTS fids (
    fid BIGINT PRIMARY KEY,
    created_at TIMESTAMP(6),
    updated_at TIMESTAMP(6),
    custody_address BYTEA
);

CREATE TABLE IF NOT EXISTS storage (
    id BIGINT PRIMARY KEY,
    created_at TIMESTAMP(6),
    updated_at TIMESTAMP(6),
    deleted_at TIMESTAMP(6),
    timestamp TIMESTAMP(6),
    fid BIGINT,
    units BIGINT,
    expiry TIMESTAMP(6)
);

CREATE TABLE IF NOT EXISTS links (
    id BIGINT PRIMARY KEY,
    fid BIGINT,
    target_fid BIGINT,
    hash BYTEA,
    timestamp TIMESTAMP(6),
    created_at TIMESTAMP(6),
    updated_at TIMESTAMP(6),
    deleted_at TIMESTAMP(6),
    type VARCHAR,
    display_timestamp TIMESTAMP(6)
);

CREATE TABLE IF NOT EXISTS casts (
    id BIGINT PRIMARY KEY,
    created_at TIMESTAMP(6),
    updated_at TIMESTAMP(6),
    deleted_at TIMESTAMP(6),
    timestamp TIMESTAMP(6),
    fid BIGINT,
    hash BYTEA,
    parent_hash BYTEA,
    parent_fid BIGINT,
    parent_url VARCHAR,
    text VARCHAR,
    embeds VARCHAR,
    mentions VARCHAR,
    mentions_positions VARCHAR,
    root_parent_hash BYTEA,
    root_parent_url VARCHAR
);

CREATE TABLE IF NOT EXISTS user_data (
    id BIGINT PRIMARY KEY,
    created_at TIMESTAMP(6),
    updated_at TIMESTAMP(6),
    deleted_at TIMESTAMP(6),
    timestamp TIMESTAMP(6),
    fid BIGINT,
    hash BYTEA,
    type BIGINT,
    value VARCHAR
);

CREATE TABLE IF NOT EXISTS reactions (
    id BIGINT PRIMARY KEY,
    created_at TIMESTAMP(6),
    updated_at TIMESTAMP(6),
    deleted_at TIMESTAMP(6),
    timestamp TIMESTAMP(6),
    reaction_type BIGINT,
    fid BIGINT,
    hash BYTEA,
    target_hash BYTEA,
    target_fid BIGINT,
    target_url VARCHAR
);

CREATE TABLE IF NOT EXISTS fnames (
    fid BIGINT PRIMARY KEY,
    created_at TIMESTAMP(6),
    updated_at TIMESTAMP(6),
    custody_address BYTEA,
    expires_at TIMESTAMP(6),
    deleted_at TIMESTAMP(6),
    fname VARCHAR
);

CREATE TABLE IF NOT EXISTS signers (
    id BIGINT PRIMARY KEY,
    created_at TIMESTAMP(6),
    updated_at TIMESTAMP(6),
    deleted_at TIMESTAMP(6),
    timestamp TIMESTAMP(6),
    fid BIGINT,
    signer BYTEA,
    name VARCHAR,
    app_fid BIGINT
);

CREATE TABLE IF NOT EXISTS verifications (
    id BIGINT PRIMARY KEY,
    created_at TIMESTAMP(6),
    updated_at TIMESTAMP(6),
    deleted_at TIMESTAMP(6),
    timestamp TIMESTAMP(6),
    fid BIGINT,
    hash BYTEA,
    claim VARCHAR
);

CREATE TABLE IF NOT EXISTS warpcast_power_users (
    fid BIGINT PRIMARY KEY,
    created_at TIMESTAMP(6),
    updated_at TIMESTAMP(6),
    deleted_at TIMESTAMP(6)
);

CREATE TABLE IF NOT EXISTS profile_with_addresses (
    fid BIGINT PRIMARY KEY,
    fname VARCHAR,
    display_name VARCHAR,
    avatar_url VARCHAR,
    bio VARCHAR,
    verified_addresses VARCHAR,
    updated_at TIMESTAMP(6)
);

CREATE TABLE IF NOT EXISTS file_tracking (
    file_name VARCHAR PRIMARY KEY,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS channels (
    id VARCHAR PRIMARY KEY,
    name VARCHAR,
    description VARCHAR,
    image_url VARCHAR,
    url VARCHAR
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