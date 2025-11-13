"""Encryption key management"""
from cryptography.fernet import Fernet
import os

# Encryption for API keys - Generate and persist securely
KEY_FILE = "data/.encryption_key"

def get_or_create_encryption_key():
    """Get existing encryption key or generate new one (persisted to file)"""
    # First check environment variable (for manual override if needed)
    env_key = os.getenv("ENCRYPTION_KEY")
    if env_key and env_key.strip():
        return env_key.strip()

    # Check if key file exists
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'rb') as f:
            return f.read().decode()

    # Generate new key and save it
    os.makedirs('data', exist_ok=True)
    new_key = Fernet.generate_key()

    # Save to file with restricted permissions
    with open(KEY_FILE, 'wb') as f:
        f.write(new_key)

    # Set file permissions to be readable only by owner (Linux/Mac)
    try:
        os.chmod(KEY_FILE, 0o600)
    except:
        pass  # Windows doesn't support chmod

    print(f"Generated new encryption key and saved to {KEY_FILE}")
    return new_key.decode()

# Initialize cipher
encryption_key = get_or_create_encryption_key()
cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
