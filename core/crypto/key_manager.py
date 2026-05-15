"""Key management for C2 agent encryption keys.

Manages per-agent encryption keys with secure storage.
"""

import json
import secrets
import uuid
from typing import Optional
from api.app.db.database import get_session
from api.app.models.agent import AgentKey
from api.app.utils.time import now_iso
from core.crypto.aes_cipher import AESCipher, key_to_base64, key_from_base64


class KeyManager:
    """Manages encryption keys for C2 agents.
    
    Responsibilities:
    - Generate unique key per agent
    - Store keys securely (encrypted with master key)
    - Retrieve agent keys
    - Rotate keys periodically
    - Revoke compromised keys
    """
    
    def __init__(self, master_key: bytes):
        """Initialize key manager with master encryption key.
        
        The master key is used to encrypt agent keys before storing in database.
        This provides defense in depth: even if database is compromised,
        agent keys are encrypted.
        
        Args:
            master_key: 32-byte master key for encrypting agent keys
            
        Raises:
            ValueError: If master_key is not 32 bytes
        """
        if len(master_key) != 32:
            raise ValueError(f"Master key must be 32 bytes, got {len(master_key)}")
        self.master_cipher = AESCipher(master_key)
    
    def generate_agent_key(self, agent_id: str) -> bytes:
        """Generate a unique encryption key for an agent.
        
        Process:
        1. Generate random 32-byte key
        2. Encrypt key with master key
        3. Store encrypted key in database
        4. Return plaintext key to caller (for transmission to agent)
        
        Args:
            agent_id: Unique agent identifier
            
        Returns:
            bytes: 32-byte encryption key for agent
            
        Example:
            key_manager = KeyManager(master_key)
            agent_key = key_manager.generate_agent_key("agent_abc123")
            # Send agent_key to agent during registration
        """
        agent_key = secrets.token_bytes(32)

        encrypted_blob = json.dumps(
            self.master_cipher.encrypt_json({"key": key_to_base64(agent_key)})
        )

        record = AgentKey(
            id=f"key_{uuid.uuid4().hex}",
            agent_id=agent_id,
            encrypted_key=encrypted_blob,
            key_version=1,
            created_at=now_iso(),
        )

        session = get_session()
        try:
            session.add(record)
            session.commit()
        finally:
            session.close()

        return agent_key
    
    def get_agent_key(self, agent_id: str) -> Optional[bytes]:
        """Retrieve agent's encryption key from database.
        
        Process:
        1. Query database for agent's encrypted key
        2. Decrypt key using master key
        3. Return plaintext key
        
        Args:
            agent_id: Unique agent identifier
            
        Returns:
            bytes: Agent's encryption key, or None if not found
        """
        session = get_session()
        try:
            record = (
                session.query(AgentKey)
                .filter(AgentKey.agent_id == agent_id, AgentKey.revoked_at == None)
                .order_by(AgentKey.key_version.desc())
                .first()
            )
        finally:
            session.close()

        if record is None:
            return None

        decrypted = self.master_cipher.decrypt_json(json.loads(record.encrypted_key))
        return key_from_base64(decrypted["key"])
    
    def rotate_agent_key(self, agent_id: str) -> bytes:
        """Generate new key for agent (key rotation).
        
        Best practice: Rotate keys periodically or after suspected compromise.
        Old key can be kept for some time to decrypt old messages.
        
        Args:
            agent_id: Unique agent identifier
            
        Returns:
            bytes: New encryption key
        """
        session = get_session()
        try:
            last = (
                session.query(AgentKey)
                .filter(AgentKey.agent_id == agent_id)
                .order_by(AgentKey.key_version.desc())
                .first()
            )
            next_version = (last.key_version + 1) if last else 1

            new_key = secrets.token_bytes(32)
            encrypted_blob = json.dumps(
                self.master_cipher.encrypt_json({"key": key_to_base64(new_key)})
            )

            record = AgentKey(
                id=f"key_{uuid.uuid4().hex}",
                agent_id=agent_id,
                encrypted_key=encrypted_blob,
                key_version=next_version,
                created_at=now_iso(),
            )
            session.add(record)
            session.commit()
        finally:
            session.close()

        return new_key
    
    def revoke_agent_key(self, agent_id: str):
        """Revoke all keys for an agent.
        
        Called when agent is decommissioned or compromised.
        
        Args:
            agent_id: Unique agent identifier
        """
        session = get_session()
        try:
            records = session.query(AgentKey).filter(AgentKey.agent_id == agent_id).all()
            for record in records:
                record.revoked_at = now_iso()
            session.commit()
        finally:
            session.close()
    
    def has_key(self, agent_id: str) -> bool:
        """Check if agent has an active encryption key.
        
        Args:
            agent_id: Unique agent identifier
            
        Returns:
            bool: True if agent has valid key
        """
        session = get_session()
        try:
            record = (
                session.query(AgentKey)
                .filter(AgentKey.agent_id == agent_id, AgentKey.revoked_at == None)
                .first()
            )
            return record is not None
        finally:
            session.close()


def generate_master_key() -> bytes:
    """Generate a cryptographically secure master key.
    
    This should be run once during setup and stored securely
    (environment variable, key management system, etc.)
    
    Returns:
        bytes: 32-byte master key
    """
    return secrets.token_bytes(32)


def load_master_key_from_env() -> bytes:
    """Load master key from environment variable.
    
    Returns:
        bytes: Master key from MASTER_ENCRYPTION_KEY env var
        
    Raises:
        ValueError: If env var not set or invalid
    """
    import os
    import base64

    raw = os.environ.get("MASTER_ENCRYPTION_KEY")
    if not raw:
        raise ValueError("MASTER_ENCRYPTION_KEY environment variable is not set")
    try:
        key = base64.b64decode(raw)
    except Exception as e:
        raise ValueError(f"MASTER_ENCRYPTION_KEY is not valid base64: {e}")
    if len(key) != 32:
        raise ValueError(f"MASTER_ENCRYPTION_KEY must decode to 32 bytes, got {len(key)}")
    return key
