from sqlalchemy import Column, BigInteger, TIMESTAMP, VARCHAR, Integer
from sqlalchemy.dialects.postgresql import BYTEA  # Correct import for BYTEA
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import text

Base = declarative_base()

class Fids(Base):
    __tablename__ = 'fids'
    fid = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)
    custody_address = Column(BYTEA)

class Storage(Base):
    __tablename__ = 'storage'
    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)
    deleted_at = Column(TIMESTAMP)
    timestamp = Column(TIMESTAMP)
    fid = Column(BigInteger)
    units = Column(BigInteger)
    expiry = Column(TIMESTAMP)

class Links(Base):
    __tablename__ = 'links'
    id = Column(BigInteger, primary_key=True)
    fid = Column(BigInteger)
    target_fid = Column(BigInteger)
    hash = Column(BYTEA)
    timestamp = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)
    deleted_at = Column(TIMESTAMP)
    type = Column(VARCHAR)
    display_timestamp = Column(TIMESTAMP)

class Casts(Base):
    __tablename__ = 'casts'
    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)
    deleted_at = Column(TIMESTAMP)
    timestamp = Column(TIMESTAMP)
    fid = Column(BigInteger)
    hash = Column(BYTEA)
    parent_hash = Column(BYTEA)
    parent_fid = Column(BigInteger)
    parent_url = Column(VARCHAR)
    text = Column(VARCHAR)
    embeds = Column(VARCHAR)
    mentions = Column(VARCHAR)
    mentions_positions = Column(VARCHAR)
    root_parent_hash = Column(BYTEA)
    root_parent_url = Column(VARCHAR)

class UserData(Base):
    __tablename__ = 'user_data'
    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)
    deleted_at = Column(TIMESTAMP)
    timestamp = Column(TIMESTAMP)
    fid = Column(BigInteger)
    hash = Column(BYTEA)
    type = Column(BigInteger)
    value = Column(VARCHAR)

class Reactions(Base):
    __tablename__ = 'reactions'
    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)
    deleted_at = Column(TIMESTAMP)
    timestamp = Column(TIMESTAMP)
    reaction_type = Column(BigInteger)
    fid = Column(BigInteger)
    hash = Column(BYTEA)
    target_hash = Column(BYTEA)
    target_fid = Column(BigInteger)
    target_url = Column(VARCHAR)

class Fnames(Base):
    __tablename__ = 'fnames'
    fid = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)
    custody_address = Column(BYTEA)
    expires_at = Column(TIMESTAMP)
    deleted_at = Column(TIMESTAMP)
    fname = Column(VARCHAR)

class Signers(Base):
    __tablename__ = 'signers'
    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)
    deleted_at = Column(TIMESTAMP)
    timestamp = Column(TIMESTAMP)
    fid = Column(BigInteger)
    signer = Column(BYTEA)
    name = Column(VARCHAR)
    app_fid = Column(BigInteger)

class Verifications(Base):
    __tablename__ = 'verifications'
    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)
    deleted_at = Column(TIMESTAMP)
    timestamp = Column(TIMESTAMP)
    fid = Column(BigInteger)
    hash = Column(BYTEA)
    claim = Column(VARCHAR)

class WarpcastPowerUsers(Base):
    __tablename__ = 'warpcast_power_users'
    fid = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)
    deleted_at = Column(TIMESTAMP)

class FileTracking(Base):
    __tablename__ = 'file_tracking'
    file_name = Column(VARCHAR, primary_key=True)
    processed_at = Column(TIMESTAMP, default=text('CURRENT_TIMESTAMP'))
