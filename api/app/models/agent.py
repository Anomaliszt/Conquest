from sqlalchemy import Column, String, JSON, ForeignKey
from sqlalchemy.orm import relationship

from api.app.models.base import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True)  # agent_<unique_id>
    hostname = Column(String, nullable=False)
    os = Column(String, nullable=False)
    user = Column(String, nullable=False)
    version = Column(String, nullable=False)
    status = Column(String, nullable=False, default="online")  # online, offline, dead, decommissioned
    last_seen = Column(String, nullable=False)
    created_at = Column(String, nullable=False)
    decommissioned_at = Column(String, nullable=True)
    agent_metadata = Column(JSON, nullable=True)  # Additional agent metadata

    refresh_tokens = relationship(
        "AgentRefreshToken",
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
