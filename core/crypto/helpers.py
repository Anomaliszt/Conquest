"""
Cryptographic helper utilities for the Conquest C2 framework.

This module provides utility functions that both Diogo and Emma can use
to encrypt/decrypt WebSocket messages using your AES cipher.

"""

import base64
import hashlib
import hmac
import json
import secrets
from typing import Any, Dict, Union

# ============================================================================
# Base64 Encoding/Decoding
# ============================================================================


def base64_encode(data: bytes) -> str:
    """
    Encode bytes to base64 string (URL-safe, no padding).

    Args:
        data: Raw bytes to encode

    Returns:
        Base64-encoded string

    Example:
        >>> base64_encode(b"hello")
        'aGVsbG8'
    """
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def base64_decode(data: str) -> bytes:
    """
    Decode base64 string to bytes.

    Args:
        data: Base64-encoded string

    Returns:
        Decoded bytes

    Raises:
        ValueError: If data is not valid base64
    """
    import binascii

    try:
        padding = 4 - len(data) % 4
        if padding != 4:
            data += "=" * padding
        return base64.urlsafe_b64decode(data)
    except (binascii.Error, ValueError) as e:
        raise ValueError(f"Invalid base64 data: {e}")


# ============================================================================
# Secure Random Generation
# ============================================================================


def secure_compare(a: bytes, b: bytes) -> bool:
    """
    Timing-safe comparison to prevent timing attacks.

    Never use == for comparing secrets!

    Args:
        a: First value
        b: Second value

    Returns:
        True if equal, False otherwise
    """
    return hmac.compare_digest(a, b)


def generate_random_bytes(length: int) -> bytes:
    """
    Generate cryptographically secure random bytes.

    Args:
        length: Number of bytes to generate

    Returns:
        Random bytes
    """
    return secrets.token_bytes(length)


def generate_random_string(length: int) -> str:
    """
    Generate cryptographically secure random URL-safe string.

    Args:
        length: Approximate length in bytes

    Returns:
        Random base64-URL-safe string
    """
    return secrets.token_urlsafe(length)


def hash_data(data: bytes) -> str:
    """
    SHA-256 hash of data.

    Args:
        data: Data to hash

    Returns:
        Hex-encoded hash
    """
    return hashlib.sha256(data).hexdigest()


# ============================================================================
# WebSocket Message Encryption Helpers
# (For Diogo and Emma to use)
# ============================================================================


def encrypt_websocket_message(cipher, message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Encrypt a WebSocket message for transmission.

    This helper is for Diogo and Emma to use in their WebSocket code.

    Args:
        cipher: AESCipher instance with the encryption key
        message: JSON-serializable message dict (e.g., {"type": "task", "command": "whoami"})

    Returns:
        Encrypted message dict:
        {
            "encrypted": true,
            "iv": "base64_iv",
            "ciphertext": "base64_ciphertext",
            "tag": "base64_tag"
        }

    Example usage by Diogo in his WebSocket handler:
        from app.crypto import AESCipher, KeyManager, encrypt_websocket_message

        key_manager = KeyManager()
        agent_key = key_manager.get_agent_key(agent_id)
        cipher = AESCipher(agent_key)

        task_message = {"type": "task", "task_id": "123", "command": "whoami"}
        encrypted = encrypt_websocket_message(cipher, task_message)
        socketio.emit('task_dispatch', encrypted, room=agent_id)

    Example usage by Emma in her agent:
        from crypto import AESCipher, encrypt_websocket_message

        cipher = AESCipher(agent_key)  # Key received during registration
        result_message = {"type": "result", "task_id": "123", "output": "root"}
        encrypted = encrypt_websocket_message(cipher, result_message)
        sio.emit('task_result', encrypted)
    """
    encrypted = cipher.encrypt_json(message)
    encrypted["encrypted"] = True
    return encrypted


def decrypt_websocket_message(
    cipher, encrypted_message: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Decrypt a WebSocket message.

    This helper is for Diogo and Emma to use.

    Args:
        cipher: AESCipher instance with the decryption key
        encrypted_message: Encrypted message dict from WebSocket

    Returns:
        Decrypted message dict

    Raises:
        ValueError: If message is tampered with or invalid

    Example usage by Diogo:
        @socketio.on('task_result')
        def handle_task_result(encrypted_msg):
            agent_id = request.sid  # Get agent ID from session
            agent_key = key_manager.get_agent_key(agent_id)
            cipher = AESCipher(agent_key)

            try:
                msg = decrypt_websocket_message(cipher, encrypted_msg)
                # Process decrypted task result
                task_service.store_result(msg['task_id'], msg['output'])
            except ValueError:
                # Message was tampered with!
                logger.error(f"Tampered message from agent {agent_id}")

    Example usage by Emma:
        @sio.on('task_dispatch')
        def handle_task(encrypted_msg):
            msg = decrypt_websocket_message(cipher, encrypted_msg)
            # Execute the decrypted task
            output = execute_command(msg['command'])
    """
    if not encrypted_message.get("encrypted"):
        raise ValueError("Message is not marked as encrypted")
    try:
        return cipher.decrypt_json(encrypted_message)
    except Exception as e:
        raise ValueError(f"Decryption failed — message may be tampered: {e}")


# ============================================================================
# WebSocket Handshake Security
# For ensuring WSS (WebSocket Secure) is used
# ============================================================================


def validate_wss_connection(is_secure: bool, headers: Dict[str, str] = None) -> bool:
    """
    Validate that WebSocket connection is using WSS (secure).

    Args:
        is_secure: Whether the connection is over TLS
        headers: Optional request headers to check for proxy forwarding

    Returns:
        bool: True if connection is secure, False otherwise

    Example (Diogo will use this in his WebSocket handler):
        @socketio.on('connect')
        def handle_connect():
            is_secure = request.is_secure
            headers = dict(request.headers)

            if not validate_wss_connection(is_secure, headers):
                logger.warning("Insecure WebSocket connection detected!")
                return False  # Reject connection
    """
    if headers is None:
        headers = {}
    forwarded_proto = headers.get("X-Forwarded-Proto", "")
    return is_secure or forwarded_proto == "https"


def encrypt_handshake_data(cipher, handshake_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Encrypt initial WebSocket handshake data.

    Defense-in-depth: Even though WSS encrypts at transport layer,
    this adds application-layer encryption for extra security.

    Args:
        cipher: AESCipher instance
        handshake_data: Handshake data dict (e.g., {"agent_id": "...", "platform": "linux"})

    Returns:
        Encrypted handshake dict

    Example (Emma will use this in her agent):
        from crypto import AESCipher, encrypt_handshake_data

        cipher = AESCipher(agent_key)
        handshake = {
            "agent_id": hardware_id,
            "platform": sys.platform,
            "hostname": socket.gethostname()
        }
        encrypted = encrypt_handshake_data(cipher, handshake)
        sio.emit('agent_handshake', encrypted)
    """
    encrypted = encrypt_websocket_message(cipher, handshake_data)
    encrypted["handshake"] = True
    return encrypted
