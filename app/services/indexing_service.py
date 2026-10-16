from pathlib import Path
from app.core.scanner import scan_folder

class IndexingService:
    def __init__(self, repo):
        self.repo = repo

    def index_folder(self, folder, progress=None):
        root = str(Path(folder).expanduser().resolve())
        cid = self.repo.add_collection(root)
        count = 0
        unchanged = 0
        seen_paths = set()
        for item in scan_folder(root):
            path = item["path"]
            seen_paths.add(path)
            same, existing_id = self.repo.unchanged_file(path, item["size"], item["modified"])
            if same and existing_id is not None:
                unchanged += 1
            else:
                self.repo.upsert_file(cid, item)
            count += 1
            if progress and count % 10 == 0:
                progress(count, path)
        removed = self.repo.remove_missing_files(cid, seen_paths)
        edge_count = self.repo.rebuild_connections()
        self.last_stats = {"processed": count, "unchanged": unchanged, "removed": removed, "connections": edge_count}
        return count, edge_count
