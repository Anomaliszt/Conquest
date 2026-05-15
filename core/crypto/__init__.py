"""Shared cryptography module for the Conquest C2 framework.

Import from here in all components:
    from core.crypto import AESCipher, generate_key
    from core.crypto import KeyManager, generate_master_key
    from core.crypto import encrypt_websocket_message, decrypt_websocket_message
"""

from core.crypto.aes_cipher import AESCipher, generate_key, key_to_base64, key_from_base64
from core.crypto.key_manager import KeyManager, generate_master_key, load_master_key_from_env
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

__all__ = [
    "AESCipher", "generate_key", "key_to_base64", "key_from_base64",
    "KeyManager", "generate_master_key", "load_master_key_from_env",
    "base64_encode", "base64_decode", "secure_compare",
    "generate_random_bytes", "generate_random_string", "hash_data",
    "encrypt_websocket_message", "decrypt_websocket_message",
    "validate_wss_connection", "encrypt_handshake_data",
]
