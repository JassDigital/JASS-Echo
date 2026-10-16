from pathlib import Path
import os
from app.config import EXCLUDED_DIRS
from app.core.extractors import extract_text
from app.core.fingerprint import sha256_file
def scan_folder(root):
    root = Path(root).expanduser().resolve()
    if not root.is_dir(): raise ValueError(f"Not a folder: {root}")
    for current, dirs, names in os.walk(root, topdown=True, followlinks=False):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith(".")]
        for name in names:
            path = Path(current)/name
            try:
                if path.is_symlink() or not path.is_file(): continue
                st = path.stat()
                yield {"path":str(path),"name":path.name,"extension":path.suffix.lower(),"size":st.st_size,"modified":st.st_mtime,"sha256":sha256_file(path),"text":extract_text(path)}
            except OSError:
                continue
