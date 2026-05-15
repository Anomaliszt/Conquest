"""Unit tests for KeyManager.

Tests key generation, storage, retrieval, and rotation.
"""

import json
import pytest
from unittest.mock import MagicMock, patch, call
from api.app.crypto.key_manager import KeyManager, generate_master_key
from api.app.crypto.aes_cipher import AESCipher, key_to_base64


def _make_manager():
    """Return a KeyManager with a fresh master key."""
    return KeyManager(generate_master_key())


class TestKeyManager:
    """Test key management functionality."""

    @patch('api.app.crypto.key_manager.get_session')
    def test_generate_agent_key_returns_32_bytes(self, mock_get_session):
        """Test that generated agent keys are 32 bytes."""
        session = MagicMock()
        mock_get_session.return_value = session

        km = _make_manager()
        key = km.generate_agent_key("agent_001")

        assert isinstance(key, bytes)
        assert len(key) == 32
        session.add.assert_called_once()
        session.commit.assert_called_once()
        session.close.assert_called_once()

    @patch('api.app.crypto.key_manager.get_session')
    def test_generated_keys_are_unique_per_agent(self, mock_get_session):
        """Test that different agents get different keys."""
        mock_get_session.return_value = MagicMock()

        km = _make_manager()
        key1 = km.generate_agent_key("agent_001")
        key2 = km.generate_agent_key("agent_002")

        assert key1 != key2

    @patch('api.app.crypto.key_manager.get_session')
    def test_get_agent_key_retrieves_stored_key(self, mock_get_session):
        """Test key retrieval from database."""
        master_key = generate_master_key()
        km = KeyManager(master_key)
        master_cipher = AESCipher(master_key)

        # Build a valid encrypted_key blob as the DB would store it
        raw_agent_key = b'A' * 32
        encrypted_blob = json.dumps(
            master_cipher.encrypt_json({"key": key_to_base64(raw_agent_key)})
        )

        mock_record = MagicMock()
        mock_record.encrypted_key = encrypted_blob
        mock_record.revoked_at = None

        session = MagicMock()
        session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_record
        mock_get_session.return_value = session

        result = km.get_agent_key("agent_001")

        assert result == raw_agent_key

    @patch('api.app.crypto.key_manager.get_session')
    def test_get_agent_key_returns_none_when_missing(self, mock_get_session):
        """Test that None is returned when no key exists."""
        session = MagicMock()
        session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_get_session.return_value = session

        km = _make_manager()
        result = km.get_agent_key("agent_missing")

        assert result is None

    @patch('api.app.crypto.key_manager.get_session')
    def test_rotate_agent_key_generates_new_key(self, mock_get_session):
        """Test key rotation creates a new, different key."""
        # First call: rotate queries for last key version
        mock_last = MagicMock()
        mock_last.key_version = 1
        session = MagicMock()
        session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_last
        mock_get_session.return_value = session

        km = _make_manager()
        new_key = km.rotate_agent_key("agent_001")

        assert isinstance(new_key, bytes)
        assert len(new_key) == 32
        # The new AgentKey record should have key_version = 2
        added_record = session.add.call_args[0][0]
        assert added_record.key_version == 2

    @patch('api.app.crypto.key_manager.get_session')
    def test_revoke_agent_key_marks_as_revoked(self, mock_get_session):
        """Test key revocation sets revoked_at on all records."""
        mock_records = [MagicMock(revoked_at=None), MagicMock(revoked_at=None)]
        session = MagicMock()
        session.query.return_value.filter.return_value.all.return_value = mock_records
        mock_get_session.return_value = session

        km = _make_manager()
        km.revoke_agent_key("agent_001")

        for r in mock_records:
            assert r.revoked_at is not None
        session.commit.assert_called_once()


class TestMasterKeyGeneration:
    """Test master key generation."""

    def test_generate_master_key_returns_32_bytes(self):
        """Test master key generation."""
        key = generate_master_key()
        assert isinstance(key, bytes)
        assert len(key) == 32

    def test_master_keys_are_unique(self):
        """Test that generated master keys are always different."""
        key1 = generate_master_key()
        key2 = generate_master_key()
        assert key1 != key2
