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

CREATE TABLE IF NOT EXISTS file_tracking (
    file_name VARCHAR PRIMARY KEY,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
