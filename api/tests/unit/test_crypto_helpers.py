"""Unit tests for cryptographic helper utilities.

Tests base64, secure comparison, random generation, hashing,
and WebSocket message encryption/decryption helpers.
"""

import pytest
from core.crypto.aes_cipher import AESCipher, generate_key
from core.crypto.helpers import (
    base64_encode,
    base64_decode,
    secure_compare,
    generate_random_bytes,
    generate_random_string,
    hash_data,
    encrypt_websocket_message,
    decrypt_websocket_message,
    validate_wss_connection,
    encrypt_handshake_data,
)


class TestBase64:
    """Test URL-safe base64 encoding/decoding."""

    def test_encode_decode_roundtrip(self):
        raw = b"hello world"
        assert base64_decode(base64_encode(raw)) == raw

    def test_encode_produces_no_padding(self):
        # URL-safe base64 strips '=' padding
        encoded = base64_encode(b"any bytes")
        assert "=" not in encoded

    def test_decode_handles_missing_padding(self):
        # Should not raise even if padding was stripped
        encoded = base64_encode(b"flow")
        assert base64_decode(encoded) == b"flow"

    def test_encode_returns_string(self):
        assert isinstance(base64_encode(b"test"), str)

    def test_decode_returns_bytes(self):
        assert isinstance(base64_decode(base64_encode(b"test")), bytes)


class TestSecureCompare:
    """Test timing-safe comparison."""

    def test_equal_bytes_returns_true(self):
        assert secure_compare(b"secret", b"secret") is True

    def test_different_bytes_returns_false(self):
        assert secure_compare(b"secret", b"differ") is False

    def test_different_lengths_returns_false(self):
        assert secure_compare(b"short", b"muchlonger") is False

    def test_empty_bytes_equal(self):
        assert secure_compare(b"", b"") is True


class TestRandomGeneration:
    """Test cryptographically secure random generators."""

    def test_random_bytes_correct_length(self):
        assert len(generate_random_bytes(16)) == 16
        assert len(generate_random_bytes(32)) == 32

    def test_random_bytes_are_different(self):
        assert generate_random_bytes(16) != generate_random_bytes(16)

    def test_random_string_returns_string(self):
        assert isinstance(generate_random_string(16), str)

    def test_random_strings_are_different(self):
        assert generate_random_string(16) != generate_random_string(16)


class TestHashData:
    """Test SHA-256 hashing."""

    def test_hash_returns_hex_string(self):
        result = hash_data(b"test")
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex digest = 64 chars

    def test_same_input_same_hash(self):
        assert hash_data(b"hello") == hash_data(b"hello")

    def test_different_input_different_hash(self):
        assert hash_data(b"hello") != hash_data(b"world")


class TestWebSocketHelpers:
    """Test WebSocket message encryption/decryption helpers."""

    def setup_method(self):
        self.key = generate_key()
        self.cipher = AESCipher(self.key)

    def test_encrypt_sets_encrypted_flag(self):
        msg = {"type": "task", "command": "whoami"}
        enc = encrypt_websocket_message(self.cipher, msg)
        assert enc.get("encrypted") is True

    def test_encrypt_decrypt_roundtrip(self):
        msg = {"type": "task", "command": "whoami", "task_id": "abc123"}
        enc = encrypt_websocket_message(self.cipher, msg)
        dec = decrypt_websocket_message(self.cipher, enc)
        assert dec == msg

    def test_decrypt_tampered_message_raises(self):
        import base64
        msg = {"type": "task", "command": "id"}
        enc = encrypt_websocket_message(self.cipher, msg)
        raw = base64.b64decode(enc["ciphertext"])
        enc["ciphertext"] = base64.b64encode(bytes([raw[0] ^ 0xFF]) + raw[1:]).decode()
        with pytest.raises((ValueError, Exception)):
            decrypt_websocket_message(self.cipher, enc)

    def test_decrypt_wrong_key_raises(self):
        msg = {"type": "heartbeat"}
        enc = encrypt_websocket_message(self.cipher, msg)
        wrong_cipher = AESCipher(generate_key())
        with pytest.raises((ValueError, Exception)):
            decrypt_websocket_message(wrong_cipher, enc)

    def test_decrypt_non_encrypted_message_raises(self):
        with pytest.raises((ValueError, Exception)):
            decrypt_websocket_message(self.cipher, {"type": "plain", "encrypted": False})


class TestHandshakeEncryption:
    """Test WebSocket handshake encryption."""

    def test_handshake_flag_is_set(self):
        cipher = AESCipher(generate_key())
        data = {"agent_id": "agent_abc123", "platform": "linux"}
        enc = encrypt_handshake_data(cipher, data)
        assert enc.get("handshake") is True
        assert enc.get("encrypted") is True

    def test_handshake_data_recoverable(self):
        cipher = AESCipher(generate_key())
        data = {"agent_id": "agent_xyz", "hostname": "victim-pc"}
        enc = encrypt_handshake_data(cipher, data)
        dec = decrypt_websocket_message(cipher, enc)
        assert dec == data


class TestWSSValidation:
    """Test WebSocket Secure connection validation."""

    def test_secure_connection_accepted(self):
        assert validate_wss_connection(True) is True

    def test_insecure_connection_rejected(self):
        assert validate_wss_connection(False) is False

    def test_proxy_forwarded_https_accepted(self):
        assert validate_wss_connection(False, {"X-Forwarded-Proto": "https"}) is True

    def test_proxy_forwarded_http_rejected(self):
        assert validate_wss_connection(False, {"X-Forwarded-Proto": "http"}) is False

    def test_empty_headers_insecure(self):
        assert validate_wss_connection(False, {}) is False
