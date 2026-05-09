from sqlalchemy.exc import IntegrityError

from api.app.db.database import get_session
from api.app.models import Agent


def create_agent(agent_id, hostname, os, user, version, status, last_seen, created_at, metadata=None):
    """Creates a new agent in the database."""
    session = get_session()

    try:
        agent = Agent(
            id=agent_id,
            hostname=hostname,
            os=os,
            user=user,
            version=version,
            status=status,
            last_seen=last_seen,
            created_at=created_at,
            agent_metadata=metadata,
        )
        session.add(agent)
        session.commit()
        return agent
    except IntegrityError:
        session.rollback()
        raise
    finally:
        session.close()


def get_agent_by_id(agent_id):
    """Retrieves an agent by their ID."""
    session = get_session()

    try:
        return session.query(Agent).filter(Agent.id == agent_id).first()
    finally:
        session.close()


def get_agent_by_hostname(hostname):
    """Retrieves an agent by their hostname. Used to check for duplicates."""
    session = get_session()

    try:
        return session.query(Agent).filter(Agent.hostname == hostname).first()
    finally:
        session.close()


def list_agents(status=None, limit=50, offset=0):
    """Lists agents with optional status filtering and pagination."""
    session = get_session()

    try:
        query = session.query(Agent)
        
        if status:
            query = query.filter(Agent.status == status)
        
        agents = query.order_by(Agent.created_at.desc()).limit(limit).offset(offset).all()
        total_count = query.count()
        
        return agents, total_count
    finally:
        session.close()


def update_agent_status(agent_id, new_status, last_seen=None):
    """Updates the status and optionally last_seen timestamp of an agent."""
    session = get_session()

    try:
        agent = session.query(Agent).filter(Agent.id == agent_id).first()
        if agent:
            agent.status = new_status
            if last_seen:
                agent.last_seen = last_seen
            session.commit()
            session.refresh(agent)
            session.expunge(agent)
        return agent
    finally:
        session.close()


def mark_agent_decommissioned(agent_id, decommissioned_at):
    """Marks an agent as decommissioned."""
    session = get_session()

    try:
        agent = session.query(Agent).filter(Agent.id == agent_id).first()
        if agent:
            agent.status = "decommissioned"
            agent.decommissioned_at = decommissioned_at
            session.commit()
        return agent
    finally:
        session.close()
