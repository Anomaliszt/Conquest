from sqlalchemy import JSON, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from api.app.models.base import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True)  # agent_<unique_id>
    hostname = Column(String, nullable=False)
    os = Column(String, nullable=False)
    user = Column(String, nullable=False)
    version = Column(String, nullable=False)
    status = Column(
        String, nullable=False, default="online"
    )  # online, offline, dead, decommissioned
    last_seen = Column(String, nullable=False)
    created_at = Column(String, nullable=False)
    decommissioned_at = Column(String, nullable=True)
    agent_metadata = Column(JSON, nullable=True)  # Additional agent metadata

    refresh_tokens = relationship(
        "AgentRefreshToken",
        back_populates="agent",
        cascade="all, delete-orphan",
    )

    encryption_keys = relationship(
        "AgentKey",
        back_populates="agent",
        cascade="all, delete-orphan",
    )


class AgentRefreshToken(Base):
    __tablename__ = "agent_refresh_tokens"

    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    token_hash = Column(String, nullable=False, unique=True)
    token_family_id = Column(String, nullable=False)  # To detect token reuse
    created_at = Column(String, nullable=False)
    used_at = Column(String, nullable=True)
    revoked_at = Column(String, nullable=True)

    agent = relationship(
        "Agent",
        foreign_keys=[agent_id],
        back_populates="refresh_tokens",
        primaryjoin="AgentRefreshToken.agent_id == Agent.id",
    )


class AgentKey(Base):
    """Stores encrypted encryption keys for C2 agents.

    Each agent has a unique AES-256 key for encrypting communications.
    Keys are stored encrypted with the master key (defense in depth).
    """

    __tablename__ = "agent_keys"

    id = Column(String, primary_key=True)  # key_<unique_id>
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    encrypted_key = Column(
        String, nullable=False
    )  # JSON blob: master_cipher.encrypt_json({"key": base64_key})
    key_version = Column(Integer, nullable=False, default=1)
    created_at = Column(String, nullable=False)
    expires_at = Column(String, nullable=True)  # Set during rotation
    revoked_at = Column(String, nullable=True)  # Set on decommission/compromise

    agent = relationship(
        "Agent",
        foreign_keys=[agent_id],
        back_populates="encryption_keys",
    )
