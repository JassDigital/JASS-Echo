import unittest
from pathlib import Path
import tempfile,unittest
from pathlib import Path
from app.core.fingerprint import sha256_file
from app.core.connections import build_connections, identifiers
from app.database.repository import Repository
class CoreTests(unittest.TestCase):
    def test_hashes(self):
        with tempfile.TemporaryDirectory() as d:
            a,b=Path(d)/"a.txt",Path(d)/"b.txt";a.write_text("same");b.write_text("same")
            self.assertEqual(sha256_file(a),sha256_file(b));b.write_text("different");self.assertNotEqual(sha256_file(a),sha256_file(b))
    def test_connections(self):
        rs=[{"id":1,"path":"a","sha256":"x","text_content":"Case AB-1234 orchid project"},{"id":2,"path":"b","sha256":"x","text_content":"AB-1234 orchid project"}]
        edges=build_connections(rs);self.assertTrue(any(e["kind"]=="Exact duplicate" for e in edges));self.assertTrue(any("Shared identifier: AB-1234" in e["reason"] for e in edges))
    def test_complete_identifier(self):
        self.assertIn("CASE-2026-014", identifiers("CASE-2026-014"))
        self.assertIn("PROJECT-ORCHID", identifiers("PROJECT-ORCHID"))

    def test_pair_edges_consolidate_reasons(self):
        rows = [
            {"id": 1, "path": "a", "sha256": "hash-a",
             "text_content": "CASE-2026-014 PROJECT-ORCHID orchard"},
            {"id": 2, "path": "b", "sha256": "hash-b",
             "text_content": "CASE-2026-014 PROJECT-ORCHID orchard"},
        ]
        edges = build_connections(rows)
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["kind"], "Shared identifier")
        self.assertIn("CASE-2026-014", edges[0]["reason"])
        self.assertIn("PROJECT-ORCHID", edges[0]["reason"])

    def test_search(self):
        with tempfile.TemporaryDirectory() as d:
            repo=Repository(Path(d)/"db.sqlite3");cid=repo.add_collection(d)
            repo.upsert_file(cid,{"path":str(Path(d)/"n.md"),"name":"n.md","extension":".md","size":8,"modified":1,"sha256":"x","text":"orchid constellation"})
            self.assertEqual(len(repo.search("constellation")),1);repo.close()


class RepositoryIndexingTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        from app.database.repository import Repository
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Repository(Path(self.tmp.name) / "test.sqlite3")
        self.cid = self.repo.add_collection(str(Path(self.tmp.name) / "collection"))

    def tearDown(self):
        self.repo.close()
        self.tmp.cleanup()

    def test_remove_missing_is_collection_scoped(self):
        self.repo.upsert_file(self.cid, {
            "path": str(Path(self.tmp.name) / "collection" / "keep.txt"),
            "name": "keep.txt", "extension": ".txt", "size": 1,
            "modified": 1.0, "sha256": "abc", "text": "sample"
        })
        removed = self.repo.remove_missing_files(self.cid, set())
        self.assertEqual(removed, 1)
        self.assertEqual(self.repo.all_files(), [])

    def test_unchanged_file_detection(self):
        path = str(Path(self.tmp.name) / "collection" / "a.txt")
        self.repo.upsert_file(self.cid, {
            "path": path, "name": "a.txt", "extension": ".txt", "size": 4,
            "modified": 10.0, "sha256": "abc", "text": "test"
        })
        same, fid = self.repo.unchanged_file(path, 4, 10.0)
        self.assertTrue(same)
        self.assertIsNotNone(fid)
        changed, _ = self.repo.unchanged_file(path, 5, 10.0)
        self.assertFalse(changed)


class EvidenceExplorerTests(unittest.TestCase):
    def test_mixed_case_hyphenated_identifier(self):
        self.assertIn("INV-7782", identifiers("invoice inv-7782 is referenced here"))

    def test_multiple_evidence_reasons_are_consolidated(self):
        rows = [
            {"id": 1, "path": "a", "sha256": "a1",
             "text_content": "CASE-2026-014 PROJECT-ORCHID"},
            {"id": 2, "path": "b", "sha256": "b2",
             "text_content": "CASE-2026-014 PROJECT-ORCHID"},
        ]
        edges = build_connections(rows)
        self.assertEqual(len(edges), 1)
        self.assertIn("CASE-2026-014", edges[0]["reason"])
        self.assertIn("PROJECT-ORCHID", edges[0]["reason"])


class InvestigationRepositoryTests(unittest.TestCase):
    def test_investigation_notes_and_files_persist(self):
        import tempfile, os
        from app.database.repository import Repository
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            repo = Repository(str(Path(tmp) / "test.sqlite3"))
            iid = repo.create_investigation("CASE-2026-014")
            repo.save_investigation(iid, "CASE-2026-014", "Check invoice references.")
            cid = repo.add_collection(str(Path(tmp) / "collection"))
            repo.upsert_file(cid, {"path": str(Path(tmp) / "collection" / "case.txt"),
                                   "name": "case.txt", "extension": ".txt", "size": 12,
                                   "modified": 1.0, "sha256": "abc", "text": "CASE-2026-014"})
            fid = repo.conn.execute("SELECT id FROM files WHERE name='case.txt'").fetchone()["id"]
            repo.add_investigation_file(iid, fid)
            self.assertEqual(repo.investigation_by_id(iid)["notes"], "Check invoice references.")
            self.assertEqual(len(repo.investigation_files(iid)), 1)
            repo.remove_investigation_file(iid, fid)
            self.assertEqual(len(repo.investigation_files(iid)), 0)
            repo.delete_investigation(iid)
            self.assertIsNone(repo.investigation_by_id(iid))
            repo.close()


class ReportEscapingTests(unittest.TestCase):
    def test_html_escape_available_for_untrusted_file_names(self):
        import html
        self.assertEqual(html.escape("<script>alert(1)</script>"),
                         "&lt;script&gt;alert(1)&lt;/script&gt;")
