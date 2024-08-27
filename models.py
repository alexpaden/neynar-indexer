from sqlalchemy import Column, BigInteger, TIMESTAMP, VARCHAR, Integer, JSON, SmallInteger
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import text

Base = declarative_base()

class Fids(Base):
    __tablename__ = 'fids'
    fid = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP, default=text('CURRENT_TIMESTAMP'), nullable=False)
    updated_at = Column(TIMESTAMP, default=text('CURRENT_TIMESTAMP'), nullable=False)
    custody_address = Column(BYTEA, nullable=False)
    registered_at = Column(TIMESTAMP(timezone=True))

class Storage(Base):
    __tablename__ = 'storage'
    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP, default=text('CURRENT_TIMESTAMP'), nullable=False)
    updated_at = Column(TIMESTAMP, default=text('CURRENT_TIMESTAMP'), nullable=False)
    deleted_at = Column(TIMESTAMP)
    timestamp = Column(TIMESTAMP, nullable=False)
    fid = Column(BigInteger, nullable=False)
    units = Column(BigInteger, nullable=False)
    expiry = Column(TIMESTAMP, nullable=False)

class Links(Base):
    __tablename__ = 'links'
    id = Column(BigInteger, primary_key=True)
    fid = Column(BigInteger)
    target_fid = Column(BigInteger)
    hash = Column(BYTEA, nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, default=text('CURRENT_TIMESTAMP'), nullable=False)
    updated_at = Column(TIMESTAMP, default=text('CURRENT_TIMESTAMP'), nullable=False)
    deleted_at = Column(TIMESTAMP)
    type = Column(VARCHAR)
    display_timestamp = Column(TIMESTAMP)

class Casts(Base):
    __tablename__ = 'casts'
    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP, default=text('CURRENT_TIMESTAMP'), nullable=False)
    updated_at = Column(TIMESTAMP, default=text('CURRENT_TIMESTAMP'), nullable=False)
    deleted_at = Column(TIMESTAMP)
    timestamp = Column(TIMESTAMP, nullable=False)
    fid = Column(BigInteger, nullable=False)
    hash = Column(BYTEA, nullable=False)
    parent_hash = Column(BYTEA)
    parent_fid = Column(BigInteger)
    parent_url = Column(VARCHAR)
    text = Column(VARCHAR, nullable=False)
    embeds = Column(JSON, default='{}', nullable=False)
    mentions = Column(BigInteger, default='{}', nullable=False)
    mentions_positions = Column(SmallInteger, default='{}', nullable=False)
    root_parent_hash = Column(BYTEA)
    root_parent_url = Column(VARCHAR)

class UserData(Base):
    __tablename__ = 'user_data'
    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP, default=text('CURRENT_TIMESTAMP'), nullable=False)
    updated_at = Column(TIMESTAMP, default=text('CURRENT_TIMESTAMP'), nullable=False)
    deleted_at = Column(TIMESTAMP)
    timestamp = Column(TIMESTAMP, nullable=False)
    fid = Column(BigInteger, nullable=False)
    hash = Column(BYTEA, nullable=False, unique=True)
    type = Column(SmallInteger, nullable=False)
    value = Column(VARCHAR, nullable=False)

class Reactions(Base):
    __tablename__ = 'reactions'
    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP, default=text('CURRENT_TIMESTAMP'), nullable=False)
    updated_at = Column(TIMESTAMP, default=text('CURRENT_TIMESTAMP'), nullable=False)
    deleted_at = Column(TIMESTAMP)
    timestamp = Column(TIMESTAMP, nullable=False)
    reaction_type = Column(SmallInteger, nullable=False)
    fid = Column(BigInteger, nullable=False)
    hash = Column(BYTEA, nullable=False)
    target_hash = Column(BYTEA)
    target_fid = Column(BigInteger)
    target_url = Column(VARCHAR)

class Fnames(Base):
    __tablename__ = 'fnames'
    fname = Column(VARCHAR, primary_key=True)
    created_at = Column(TIMESTAMP, default=text('CURRENT_TIMESTAMP'), nullable=False)
    updated_at = Column(TIMESTAMP, default=text('CURRENT_TIMESTAMP'), nullable=False)
    custody_address = Column(BYTEA)
    expires_at = Column(TIMESTAMP)
    fid = Column(BigInteger)
    deleted_at = Column(TIMESTAMP)

class Signers(Base):
    __tablename__ = 'signers'
    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP, default=text('CURRENT_TIMESTAMP'), nullable=False)
    updated_at = Column(TIMESTAMP, default=text('CURRENT_TIMESTAMP'), nullable=False)
    deleted_at = Column(TIMESTAMP)
    timestamp = Column(TIMESTAMP, nullable=False)
    fid = Column(BigInteger, nullable=False)
    hash = Column(BYTEA)
    custody_address = Column(BYTEA)
    signer = Column(BYTEA, nullable=False)
    name = Column(VARCHAR)
    app_fid = Column(BigInteger)

class Verifications(Base):
    __tablename__ = 'verifications'
    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP, default=text('CURRENT_TIMESTAMP'), nullable=False)
    updated_at = Column(TIMESTAMP, default=text('CURRENT_TIMESTAMP'), nullable=False)
    deleted_at = Column(TIMESTAMP)
    timestamp = Column(TIMESTAMP, nullable=False)
    fid = Column(BigInteger, nullable=False)
    hash = Column(BYTEA, nullable=False, unique=True)
    claim = Column(JSON, nullable=False)

class WarpcastPowerUsers(Base):
    __tablename__ = 'warpcast_power_users'
    fid = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP, default=text('CURRENT_TIMESTAMP'), nullable=False)
    updated_at = Column(TIMESTAMP, default=text('CURRENT_TIMESTAMP'), nullable=False)
    deleted_at = Column(TIMESTAMP)

class ProfileWithAddresses(Base):
    __tablename__ = 'profile_with_addresses'
    fid = Column(BigInteger, primary_key=True)
    fname = Column(VARCHAR)
    display_name = Column(VARCHAR)
    avatar_url = Column(VARCHAR)
    bio = Column(VARCHAR)
    verified_addresses = Column(JSON, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)

class FileTracking(Base):
    __tablename__ = 'file_tracking'
    file_name = Column(VARCHAR, primary_key=True)
    processed_at = Column(TIMESTAMP, default=text('CURRENT_TIMESTAMP'))

class Channel(Base):
    __tablename__ = 'channels'
    id = Column(VARCHAR, primary_key=True)
    name = Column(VARCHAR)
    description = Column(VARCHAR)
    image_url = Column(VARCHAR)
    url = Column(VARCHAR)