import sqlite3
from pathlib import Path
from app.config import database_path
from app.core.connections import build_connections
class Repository:
    def __init__(self, db_path=None):
        self.db_path=str(db_path or database_path())
        self.conn=sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory=sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(Path(__file__).with_name("schema.sql").read_text(encoding="utf-8"))
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS investigations(
            id INTEGER PRIMARY KEY, title TEXT NOT NULL, notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS investigation_files(
            investigation_id INTEGER NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
            file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
            added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(investigation_id, file_id)
        );
        """)
        self.fts_available=False
        try:
            self.conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(path UNINDEXED,name,text_content)")
            self.fts_available=True
        except sqlite3.OperationalError: pass
    def close(self): self.conn.close()
    def add_collection(self,root):
        self.conn.execute("INSERT OR IGNORE INTO collections(root_path) VALUES(?)",(root,)); self.conn.commit()
        return self.conn.execute("SELECT id FROM collections WHERE root_path=?",(root,)).fetchone()["id"]
    def collections(self): return self.conn.execute("SELECT * FROM collections ORDER BY added_at DESC").fetchall()
    def upsert_file(self,cid,item):
        self.conn.execute("""INSERT INTO files(collection_id,path,name,extension,size,modified,sha256,text_content) VALUES(?,?,?,?,?,?,?,?)
        ON CONFLICT(path) DO UPDATE SET collection_id=excluded.collection_id,name=excluded.name,extension=excluded.extension,size=excluded.size,modified=excluded.modified,sha256=excluded.sha256,text_content=excluded.text_content,indexed_at=CURRENT_TIMESTAMP""",
        (cid,item["path"],item["name"],item["extension"],item["size"],item["modified"],item["sha256"],item["text"]))
        self.conn.commit()
        if self.fts_available:
            self.conn.execute("DELETE FROM files_fts")
            self.conn.execute("INSERT INTO files_fts(path,name,text_content) SELECT path,name,text_content FROM files")
            self.conn.commit()
    def all_files(self): return [dict(r) for r in self.conn.execute("SELECT * FROM files")]
    def file_by_id(self,fid):
        row=self.conn.execute("SELECT * FROM files WHERE id=?",(fid,)).fetchone()
        return dict(row) if row else None
    def search(self,query,limit=200):
        q=query.strip()
        if not q: return []
        if self.fts_available:
            try:
                # Quote each token so punctuation in user queries doesn't break FTS syntax.
                safe=" AND ".join('"'+token.replace('"','""')+'"' for token in q.split())
                rows=self.conn.execute("SELECT f.* FROM files_fts x JOIN files f ON f.path=x.path WHERE files_fts MATCH ? LIMIT ?",(safe,limit)).fetchall()
                return [dict(r) for r in rows]
            except sqlite3.OperationalError: pass
        like=f"%{q}%"
        return [dict(r) for r in self.conn.execute("SELECT * FROM files WHERE name LIKE ? OR path LIKE ? OR text_content LIKE ? ORDER BY name LIMIT ?",(like,like,like,limit))]

    def unchanged_file(self, path, size, modified):
        row = self.conn.execute(
            "SELECT id,size,modified FROM files WHERE path=?", (str(path),)
        ).fetchone()
        if not row:
            return True, None
        same = int(row["size"]) == int(size) and abs(float(row["modified"]) - float(modified)) < 0.001
        return same, int(row["id"])

    def remove_missing_files(self, collection_id, seen_paths):
        rows = self.conn.execute(
            "SELECT id,path FROM files WHERE collection_id=?", (collection_id,)
        ).fetchall()
        stale = [r for r in rows if r["path"] not in seen_paths]
        if stale:
            ids = [int(r["id"]) for r in stale]
            placeholders = ",".join("?" for _ in ids)
            self.conn.execute(f"DELETE FROM files WHERE id IN ({placeholders})", ids)
            self.conn.commit()
        return len(stale)
    def rebuild_connections(self):
        edges=build_connections(self.all_files())
        self.conn.execute("DELETE FROM connections")
        self.conn.executemany("INSERT OR IGNORE INTO connections(source_id,target_id,kind,reason,score) VALUES(?,?,?,?,?)",[(e["source_id"],e["target_id"],e["kind"],e["reason"],e["score"]) for e in edges])
        self.conn.commit(); return len(edges)
    def connections_for(self,fid):
        rows=self.conn.execute("""SELECT c.*,f.id AS related_id,f.path AS related_path,f.name AS related_name FROM connections c
        JOIN files f ON f.id=CASE WHEN c.source_id=? THEN c.target_id ELSE c.source_id END
        WHERE c.source_id=? OR c.target_id=? ORDER BY c.score DESC,f.name""",(fid,fid,fid)).fetchall()
        return [dict(r) for r in rows]
    def graph_data(self, center_id=None, max_nodes=80, max_edges=160):
        files = self.all_files()
        edges = [dict(r) for r in self.conn.execute(
            "SELECT * FROM connections ORDER BY score DESC, kind"
        )]
        by_id = {int(r["id"]): r for r in files}
        if center_id and int(center_id) in by_id:
            center_id = int(center_id)
            edges = [e for e in edges
                     if int(e["source_id"]) == center_id or int(e["target_id"]) == center_id]
            edges.sort(key=lambda e: (e["score"], e["kind"] == "Exact duplicate"), reverse=True)
            edges = edges[:24]
            ids = {center_id}
            for edge in edges:
                ids.update((int(edge["source_id"]), int(edge["target_id"])))
            files = [r for r in files if int(r["id"]) in ids]
        else:
            degree = {}
            for edge in edges:
                degree[int(edge["source_id"])] = degree.get(int(edge["source_id"]), 0) + 1
                degree[int(edge["target_id"])] = degree.get(int(edge["target_id"]), 0) + 1
            ids = set(sorted(degree, key=lambda fid: (degree[fid], fid), reverse=True)[:max_nodes])
            if not ids and files:
                ids = {int(r["id"]) for r in files[:max_nodes]}
            files = [r for r in files if int(r["id"]) in ids]
            edges = [e for e in edges
                     if int(e["source_id"]) in ids and int(e["target_id"]) in ids]
            edges.sort(key=lambda e: (e["score"], e["kind"] == "Exact duplicate"), reverse=True)
            edges = edges[:max_edges]
        return files, edges


    # Investigation workspace methods (stored in the existing local database).
    def investigations(self):
        return [dict(r) for r in self.conn.execute(
            """SELECT i.*, COUNT(x.file_id) AS file_count
               FROM investigations i LEFT JOIN investigation_files x ON x.investigation_id=i.id
               GROUP BY i.id ORDER BY i.updated_at DESC, i.id DESC"""
        )]

    def create_investigation(self, title):
        title = (title or "").strip() or "Untitled investigation"
        cur = self.conn.execute("INSERT INTO investigations(title) VALUES(?)", (title,))
        self.conn.commit()
        return int(cur.lastrowid)

    def investigation_by_id(self, investigation_id):
        row = self.conn.execute("SELECT * FROM investigations WHERE id=?", (int(investigation_id),)).fetchone()
        return dict(row) if row else None

    def save_investigation(self, investigation_id, title, notes):
        self.conn.execute(
            "UPDATE investigations SET title=?, notes=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            ((title or "").strip() or "Untitled investigation", notes or "", int(investigation_id))
        )
        self.conn.commit()

    def investigation_files(self, investigation_id):
        return [dict(r) for r in self.conn.execute(
            """SELECT f.* FROM files f JOIN investigation_files x ON x.file_id=f.id
               WHERE x.investigation_id=? ORDER BY f.name""", (int(investigation_id),)
        )]

    def add_investigation_file(self, investigation_id, file_id):
        self.conn.execute(
            "INSERT OR IGNORE INTO investigation_files(investigation_id,file_id) VALUES(?,?)",
            (int(investigation_id), int(file_id))
        )
        self.conn.execute("UPDATE investigations SET updated_at=CURRENT_TIMESTAMP WHERE id=?", (int(investigation_id),))
        self.conn.commit()

    def remove_investigation_file(self, investigation_id, file_id):
        self.conn.execute(
            "DELETE FROM investigation_files WHERE investigation_id=? AND file_id=?",
            (int(investigation_id), int(file_id))
        )
        self.conn.execute("UPDATE investigations SET updated_at=CURRENT_TIMESTAMP WHERE id=?", (int(investigation_id),))
        self.conn.commit()

    def delete_investigation(self, investigation_id):
        self.conn.execute("DELETE FROM investigations WHERE id=?", (int(investigation_id),))
        self.conn.commit()
