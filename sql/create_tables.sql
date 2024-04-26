-- noinspection SqlDialectInspectionForFile

-- noinspection SqlNoDataSourceInspectionForFile

CREATE TABLE farcaster_fids (
    fid BIGINT PRIMARY KEY,
    created_at TIMESTAMP(6),
    updated_at TIMESTAMP(6),
    custody_address BYTEA
);

CREATE TABLE farcaster_storage (
    id BIGINT PRIMARY KEY,
    created_at TIMESTAMP(6),
    updated_at TIMESTAMP(6),
    deleted_at TIMESTAMP(6),
    timestamp TIMESTAMP(6),
    fid BIGINT,
    units BIGINT,
    expiry TIMESTAMP(6)
);

CREATE TABLE farcaster_links (
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

CREATE TABLE farcaster_casts (
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

CREATE TABLE farcaster_user_data (
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

CREATE TABLE farcaster_reactions (
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

CREATE TABLE farcaster_fnames (
    fid BIGINT PRIMARY KEY,
    created_at TIMESTAMP(6),
    updated_at TIMESTAMP(6),
    custody_address BYTEA,
    expires_at TIMESTAMP(6),
    deleted_at TIMESTAMP(6),
    fname VARCHAR
);

CREATE TABLE farcaster_signers (
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

CREATE TABLE farcaster_verifications (
    id BIGINT PRIMARY KEY,
    created_at TIMESTAMP(6),
    updated_at TIMESTAMP(6),
    deleted_at TIMESTAMP(6),
    timestamp TIMESTAMP(6),
    fid BIGINT,
    hash BYTEA,
    claim VARCHAR
);