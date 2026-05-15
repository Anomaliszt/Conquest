"""Unit tests for AES cipher implementation.

Tests encryption, decryption, authentication, and error handling.
"""

import base64
import pytest
from api.app.crypto.aes_cipher import AESCipher, generate_key, key_to_base64, key_from_base64


class TestAESCipher:
    """Test AES-256-GCM encryption and decryption."""

    def test_encrypt_decrypt_roundtrip(self):
        """Test that encrypt->decrypt returns original plaintext."""
        key = generate_key()
        cipher = AESCipher(key)
        plaintext = b"This is a secret message"
        encrypted = cipher.encrypt(plaintext)
        decrypted = cipher.decrypt(encrypted)
        assert decrypted == plaintext

    def test_iv_uniqueness(self):
        """Test that each encryption uses a unique IV."""
        key = generate_key()
        cipher = AESCipher(key)
        msg = b"same message"
        enc1 = cipher.encrypt(msg)
        enc2 = cipher.encrypt(msg)
        assert enc1['iv'] != enc2['iv']
        assert enc1['ciphertext'] != enc2['ciphertext']

    def test_authentication_prevents_tampering(self):
        """Test that modifying ciphertext causes decryption to fail."""
        key = generate_key()
        cipher = AESCipher(key)
        encrypted = cipher.encrypt(b"tamper me")

        raw = base64.b64decode(encrypted['ciphertext'])
        tampered = bytes([raw[0] ^ 0xFF]) + raw[1:]
        encrypted['ciphertext'] = base64.b64encode(tampered).decode()

        with pytest.raises((ValueError, Exception)):
            cipher.decrypt(encrypted)

    def test_wrong_key_fails_decryption(self):
        """Test that using wrong key for decryption fails."""
        key1 = generate_key()
        key2 = generate_key()
        cipher1 = AESCipher(key1)
        cipher2 = AESCipher(key2)

        encrypted = cipher1.encrypt(b"secret")
        with pytest.raises((ValueError, Exception)):
            cipher2.decrypt(encrypted)

    def test_encrypt_json_roundtrip(self):
        """Test JSON encryption and decryption."""
        key = generate_key()
        cipher = AESCipher(key)
        data = {'task_id': 'task_123', 'command': 'whoami'}
        encrypted = cipher.encrypt_json(data)
        decrypted = cipher.decrypt_json(encrypted)
        assert decrypted == data

    def test_key_must_be_32_bytes(self):
        """Test that invalid key length raises error."""
        with pytest.raises(ValueError):
            AESCipher(b"tooshort")


class TestKeyGeneration:
    """Test key generation helpers."""

    def test_generate_key_returns_32_bytes(self):
        """Test that generated keys are correct length."""
        key = generate_key()
        assert len(key) == 32

    def test_generated_keys_are_random(self):
        """Test that multiple key generations produce different keys."""
        key1 = generate_key()
        key2 = generate_key()
        assert key1 != key2

    def test_key_to_base64_and_back(self):
        """Test key serialization roundtrip."""
        key = generate_key()
        encoded = key_to_base64(key)
        assert isinstance(encoded, str)
        decoded = key_from_base64(encoded)
        assert decoded == key
