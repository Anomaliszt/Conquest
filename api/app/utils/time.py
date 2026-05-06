from datetime import datetime, timezone


def time_now():
    return datetime.now(timezone.utc)

def now_iso():
    return datetime.now(timezone.utc).isoformat()


def is_expired(expires_at):
    if not expires_at:
        return False

    expiry = datetime.fromisoformat(expires_at)
    return expiry <= datetime.now(timezone.utc)