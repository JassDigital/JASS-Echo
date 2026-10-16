from pathlib import Path
import os, sys
APP_NAME = "JASS ECHO"
APP_VERSION = "0.8.0"
TEXT_EXTENSIONS = {".txt",".md",".markdown",".py",".js",".jsx",".ts",".tsx",".json",".csv",".tsv",".html",".htm",".css",".scss",".yaml",".yml",".toml",".ini",".cfg",".conf",".sql",".log",".xml",".sh",".ps1",".bat",".cmd",".rst", ".pdf", ".docx"}
EXCLUDED_DIRS = {".git",".hg",".svn",".venv","venv","env","node_modules","__pycache__",".pytest_cache",".mypy_cache","dist","build",".next",".cache","vendor"}
MAX_TEXT_BYTES = 2 * 1024 * 1024
MAX_HASH_BYTES = 512 * 1024 * 1024
def data_dir():
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    result = base / "JASS" / "ECHO"
    result.mkdir(parents=True, exist_ok=True)
    return result
def database_path():
    return data_dir() / "echo.sqlite3"
