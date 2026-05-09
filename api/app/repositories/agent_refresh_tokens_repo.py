from sqlalchemy.exc import IntegrityError
import uuid

from api.app.db.database import get_session
from api.app.models import AgentRefreshToken


def create_agent_refresh_token(agent_id, token_hash, created_at):
    """Creates a new agent refresh token in the database."""
    session = get_session()

    try:
        token_id = f"refresh_{uuid.uuid4().hex[:12]}"
        token_family_id = f"family_{uuid.uuid4().hex[:12]}"
        
        refresh_token = AgentRefreshToken(
            id=token_id,
            agent_id=agent_id,
            token_hash=token_hash,
            token_family_id=token_family_id,
            created_at=created_at,
        )
        session.add(refresh_token)
        session.commit()
        return refresh_token
    except IntegrityError:
        session.rollback()
        raise
    finally:
        session.close()


def get_agent_refresh_token_by_hash(token_hash):
    """Retrieves a refresh token by its hash."""
    session = get_session()

    try:
        return session.query(AgentRefreshToken).filter(
            AgentRefreshToken.token_hash == token_hash
        ).first()
    finally:
        session.close()


def mark_agent_refresh_token_used(token_hash, used_at):
    """Marks a refresh token as used."""
    session = get_session()

    try:
        token = session.query(AgentRefreshToken).filter(
            AgentRefreshToken.token_hash == token_hash
        ).first()
        if token:
            token.used_at = used_at
            session.commit()
        return token
    finally:
        session.close()


def revoke_agent_refresh_token_family(token_family_id, revoked_at):
    """Revokes all tokens in a family (used when token reuse is detected)."""
    session = get_session()

    try:
        tokens = session.query(AgentRefreshToken).filter(
            AgentRefreshToken.token_family_id == token_family_id
        ).all()
        
        for token in tokens:
            token.revoked_at = revoked_at
        
        session.commit()
        return len(tokens)
    finally:
        session.close()


def get_active_agent_refresh_tokens(agent_id):
    """Retrieves all active (non-revoked, unused) refresh tokens for an agent."""
    session = get_session()

    try:
        return session.query(AgentRefreshToken).filter(
            AgentRefreshToken.agent_id == agent_id,
            AgentRefreshToken.revoked_at.is_(None),
            AgentRefreshToken.used_at.is_(None),
        ).all()
    finally:
        session.close()


def revoke_agent_all_tokens(agent_id, revoked_at):
    """Revokes all refresh tokens for an agent (used during decommissioning)."""
    session = get_session()

    try:
        tokens = session.query(AgentRefreshToken).filter(
            AgentRefreshToken.agent_id == agent_id
        ).all()
        
        for token in tokens:
            token.revoked_at = revoked_at
        
        session.commit()
        return len(tokens)
    finally:
        session.close()
