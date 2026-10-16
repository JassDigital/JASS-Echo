import hashlib
from app.config import MAX_HASH_BYTES
def sha256_file(path):
    try:
        if path.stat().st_size > MAX_HASH_BYTES: return None
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024*1024), b""): h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None
