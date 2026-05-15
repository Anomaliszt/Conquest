"""AES-256-GCM encryption implementation for C2 framework.

This module provides authenticated encryption using AES-256-GCM mode.
GCM (Galois/Counter Mode) provides both confidentiality and authenticity.
"""

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import base64
import json


class AESCipher:
    """AES-256-GCM encryption for secure C2 communications.
    
    Uses:
    - AES-256 (32-byte key)
    - GCM mode (provides authentication)
    - Random IV for each encryption (96 bits / 12 bytes recommended for GCM)
    - Authentication tag (128 bits / 16 bytes)
    
    Security properties:
    - Confidentiality: Data is encrypted
    - Authenticity: Data cannot be modified without detection
    - IV uniqueness: Each message has unique IV
    """
    
    def __init__(self, key: bytes):
        """Initialize cipher with AES-256 key.
        
        Args:
            key: 32-byte key for AES-256
            
        Raises:
            ValueError: If key is not exactly 32 bytes
        """
        if len(key) != 32:
            raise ValueError(f"Key must be 32 bytes for AES-256, got {len(key)} bytes")
        self.key = key
    
    def encrypt(self, plaintext: bytes) -> dict:
        """Encrypt plaintext using AES-256-GCM.
        
        Process:
        1. Generate random 12-byte IV
        2. Create AES-GCM cipher
        3. Encrypt plaintext
        4. Get authentication tag
        5. Return base64-encoded IV, ciphertext, and tag
        
        Args:
            plaintext: Data to encrypt (bytes)
            
        Returns:
            dict: {
                'iv': base64-encoded initialization vector (12 bytes),
                'ciphertext': base64-encoded encrypted data,
                'tag': base64-encoded authentication tag (16 bytes)
            }
            
        Example:
            cipher = AESCipher(key)
            encrypted = cipher.encrypt(b"secret message")
            # encrypted = {'iv': '...', 'ciphertext': '...', 'tag': '...'}
        """
        iv = os.urandom(12)

        cipher = Cipher(algorithms.AES(self.key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        tag = encryptor.tag

        return {
            'iv': base64.b64encode(iv).decode('utf-8'),
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
            'tag': base64.b64encode(tag).decode('utf-8'),
        }
    
    def decrypt(self, encrypted_data: dict) -> bytes:
        """Decrypt ciphertext using AES-256-GCM.
        
        Process:
        1. Base64-decode IV, ciphertext, and tag
        2. Create AES-GCM cipher with IV
        3. Decrypt and verify authentication tag
        4. Return plaintext
        
        Args:
            encrypted_data: dict with 'iv', 'ciphertext', 'tag' (all base64-encoded)
            
        Returns:
            bytes: Decrypted plaintext
            
        Raises:
            ValueError: If authentication fails (data was tampered with)
            KeyError: If encrypted_data missing required fields
            
        Example:
            cipher = AESCipher(key)
            plaintext = cipher.decrypt(encrypted_data)
        """
        iv = base64.b64decode(encrypted_data['iv'])
        ciphertext = base64.b64decode(encrypted_data['ciphertext'])
        tag = base64.b64decode(encrypted_data['tag'])

        cipher = Cipher(algorithms.AES(self.key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()

        try:
            return decryptor.update(ciphertext) + decryptor.finalize()
        except Exception:
            raise ValueError("Decryption failed: authentication tag mismatch — data may have been tampered with")
    
    def encrypt_json(self, data: dict) -> dict:
        """Encrypt a JSON-serializable dictionary.
        
        Convenience method that handles JSON serialization.
        
        Args:
            data: Dictionary to encrypt
            
        Returns:
            dict: Encrypted data in same format as encrypt()
        """
        plaintext = json.dumps(data).encode('utf-8')
        return self.encrypt(plaintext)
    
    def decrypt_json(self, encrypted_data: dict) -> dict:
        """Decrypt and deserialize JSON data.
        
        Args:
            encrypted_data: Encrypted dictionary from encrypt_json()
            
        Returns:
            dict: Decrypted and deserialized data
        """
        plaintext = self.decrypt(encrypted_data)
        return json.loads(plaintext.decode('utf-8'))


# Helper functions for testing
def generate_key() -> bytes:
    """Generate a random 32-byte key for AES-256.
    
    Returns:
        bytes: Cryptographically secure random key
    """
    return os.urandom(32)


def key_to_base64(key: bytes) -> str:
    """Convert key to base64 string for storage.
    
    Args:
        key: Binary key
        
    Returns:
        str: Base64-encoded key
    """
    return base64.b64encode(key).decode('utf-8')


def key_from_base64(key_str: str) -> bytes:
    """Convert base64 string back to binary key.
    
    Args:
        key_str: Base64-encoded key
        
    Returns:
        bytes: Binary key
    """
    return base64.b64decode(key_str)
