# JASS ECHO v0.2.0 — Visual Discovery

JASS ECHO is a local-first desktop app for discovering explainable relationships between files.

## Requirements
- Python 3.11+
- PySide6 (`pip install PySide6`)
- No virtual environment is required.

## Run
```powershell
pip install PySide6
python run.py
```
On Linux, use `python3 run.py` if `python` is not mapped to Python 3.

## Features
- Local folder indexing with SQLite
- Full-text search (FTS5 when available, LIKE fallback otherwise)
- Exact duplicate detection via SHA-256
- Explainable shared-identifier and distinctive-term relationships
- Interactive relationship graph with click-to-inspect
- Graph filters and selected-file neighborhood
- Read-only scan; no cloud or AI requirement

Database:
- Windows: `%LOCALAPPDATA%/JASS/ECHO/echo.sqlite3`
- Linux: `~/.local/share/JASS/ECHO/echo.sqlite3`

PDF/DOCX extraction, cancellation, truly incremental indexing, and packaging are future milestones.

\n## v0.3.0 improvements
- Complete multi-part identifiers such as `CASE-2026-014` are extracted intact.
- One connection per file pair consolidates all supporting evidence.
- The all-files map is bounded to 80 nodes and 160 strongest edges; a selected
  file shows up to 24 strongest direct connections.
- Smaller labels and a spiral layout reduce graph clutter.
- Existing database schema remains compatible; no database reset is required.

Upgrade safely: close the app and back up the project folder before replacing
source files. The user database is stored separately and is not included in this ZIP.

\n## v0.4.0 — Graph usability and evidence
- Added a Fit map control and automatic fit-to-view after rendering.
- Added optional full filename labels; hover on any node to see its full path.
- Single-click a node to select it and update its evidence; double-click to focus
  the map on that file and its strongest direct connections.
- Increased spacing between graph nodes and made relationship edges easier to distinguish.
- Kept the existing SQLite schema and user database compatible. No database reset is needed.

Upgrade: close ECHO, back up the project folder, then replace the project source files
with this release. Do not delete or replace the separate user database.

\n## v0.5.0 — Incremental indexing and document text
- Reuses existing indexed records when file size and modification timestamp are unchanged.
- Removes records for files deleted from a scanned collection; cleanup is scoped to that collection.
- Adds optional text extraction for PDF and DOCX files using `pypdf` and `python-docx`.
- Keeps the existing SQLite database and schema; no reset or migration is required.

Install optional document support with `pip install pypdf python-docx`, or install all
listed packages with `pip install -r requirements.txt`. If either library is missing
or a document cannot be read, ECHO still indexes the file metadata and continues.

\n## v0.6.0 — Evidence Explorer
- Evidence tab now includes a relationship detail pane with both file paths, SHA-256 values,
  score, connection reason, and text previews from both files.
- Relationship rows retain evidence metadata for direct inspection.
- Graph nodes are spaced farther apart and edge tooltips expose relationship type, score,
  and explanation.
- Identifier extraction accepts lowercase/mixed-case hyphenated identifiers and normalizes
  extracted values for matching.
- Existing database schema is unchanged; re-scan a collection to rebuild its connection evidence.

Upgrade by closing ECHO, backing up the project folder, and replacing project source files.
Keep the existing user database. No virtual environment is required.


## v0.7.0 — Investigation Workspace
- Create named investigations and maintain notes locally.
- Add the currently selected indexed file as evidence; remove it from an investigation without deleting the original file.
- Review evidence file names, types, sizes, and full paths.
- Delete an investigation with confirmation; indexed files and collections are preserved.
- New `investigations` and `investigation_files` tables are added automatically to the existing database. Existing indexed files and connections are retained.

### Suggested workflow
1. Select a file in Collections, Search, or the Discovery Map.
2. Open Investigations and create an investigation.
3. Return to the file and select it, then return to Investigations and choose Add selected file.
4. Add notes and click Save title / notes.


## v0.8.0 — Investigation Reports
- Export any investigation as a self-contained HTML report that opens in a browser and can be printed to PDF.
- Includes investigation title, timestamps, notes, evidence file paths, type, size, modified time, SHA-256, text preview, and indexed relationship evidence.
- Fixes line breaks in the Evidence comparison panel and improves relationship-table column sizing.
- Report generation uses the Python standard library; no extra dependency or database migration is required.
- Reports are generated locally. The report explicitly notes that relationship inferences are not proof and original files are not modified.

### Exporting a report
Open Investigations, select an investigation, click **Export HTML report**, and choose where to save it. Open the HTML file in a browser; use Print → Save as PDF if you need a PDF copy.


## User Help

See [`HELP.md`](HELP.md) for the full user guide, installation and launch instructions, feature explanations, troubleshooting, privacy notes, and a suggested sample workflow.
