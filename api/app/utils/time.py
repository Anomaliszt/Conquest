from datetime import datetime, timezone
import uuid


def time_now():
    return datetime.now(timezone.utc)

def now_iso():
    return datetime.now(timezone.utc).isoformat()


def generate_request_id():
    """Generate a unique request ID in the format req_<timestamp>_<random>.
    
    Format: req_01HXABCDEF1234567890ABCDEF
    Where the hex part is timestamp + random for uniqueness.
    """
    # Use timestamp + random for uniqueness
    timestamp_hex = hex(int(datetime.now(timezone.utc).timestamp() * 1000000))[2:]
    random_hex = uuid.uuid4().hex[:12]
    return f"req_{timestamp_hex}{random_hex}"[:24].lower()


def is_expired(expires_at):
    if not expires_at:
        return False

    expiry = datetime.fromisoformat(expires_at)
    return expiry <= datetime.now(timezone.utc)