# JASS ECHO — User Help

**Version:** 0.8.0  
**Platforms:** Windows and Linux  
**Purpose:** Local-first discovery of relationships between files.

JASS ECHO indexes selected folders on your own computer, searches indexed content, identifies possible relationships between files, and lets you collect files and notes into investigations. It is an investigative aid: a detected relationship is a lead to review, not proof that two files are factually connected.

## Contents

1. [What ECHO does](#what-echo-does)
2. [Requirements](#requirements)
3. [Install and run on Windows](#install-and-run-on-windows)
4. [Install and run on Linux](#install-and-run-on-linux)
5. [First-run walkthrough](#first-run-walkthrough)
6. [Feature guide](#feature-guide)
7. [Investigation reports](#investigation-reports)
8. [Local data, privacy, and safety](#local-data-privacy-and-safety)
9. [Troubleshooting](#troubleshooting)
10. [Suggested sample workflow](#suggested-sample-workflow)

## What ECHO does

- Scans folders you explicitly add and builds a local index.
- Records file metadata and hashes where supported by the indexer.
- Searches indexed filenames, paths, and extracted text.
- Finds candidate connections using shared identifiers, distinctive terms, and exact-file hashes.
- Displays connected files in an interactive discovery map.
- Shows relationship evidence so you can inspect why two files were linked.
- Lets you create investigations, attach indexed files, and write working notes.
- Exports an investigation as a self-contained HTML report that can be printed to PDF from a browser.

## Requirements

- Python 3.11 or later is recommended.
- PySide6, listed in `requirements.txt`.
- A desktop session (the application uses a Qt graphical interface).
- No virtual environment is required. A virtual environment can still be used if you prefer one.

Install dependencies from the extracted project folder:

```powershell
python -m pip install -r requirements.txt
```

If the project has only PySide6 in `requirements.txt`, this installs the graphical toolkit used by the app.

## Install and run on Windows

1. Download and extract `JASS-ECHO-v0.8.0.zip`.
2. Copy the extracted project files into your project folder, for example `D:\Github\JASS-ECHO`.
3. If upgrading an existing installation, close ECHO first and back up the project folder.
4. **Keep your existing ECHO database. Do not delete it when upgrading.**
5. Open PowerShell in the project folder.
6. Install dependencies and launch:

```powershell
python -m pip install -r requirements.txt
python run.py
```

If `python` is not found, install Python from the official Python distribution and enable its PATH option, or try the Windows Python launcher:

```powershell
py -3 -m pip install -r requirements.txt
py -3 run.py
```

## Install and run on Linux

From a terminal, enter the extracted project directory and run:

```bash
python3 -m pip install -r requirements.txt
python3 run.py
```

Use your distribution's supported Python/PySide6 installation method if pip reports that system Python packages are externally managed. Do not use `sudo pip` to force packages into the operating system's Python.

A graphical desktop session is required. On a headless machine, the GUI will not open unless a suitable display environment is configured.

## First-run walkthrough

1. Launch ECHO.
2. Choose **Add Folder** and select a test folder or a folder containing files you want to examine.
3. Wait for indexing to finish. The status area reports scan progress or completion.
4. Open **Collections** to browse indexed files.
5. Select a file to inspect its metadata and text preview.
6. Use **Search** to find a filename, path, identifier, or phrase.
7. Open **Discovery Map** to explore connected files.
8. Open **Evidence** to inspect the reasons behind a selected file's connections.
9. Use **Investigations** to create a case workspace, attach files, and record notes.
10. Export the investigation as an HTML report when ready.

Start with a small sample folder to learn how ECHO represents relationships before scanning a large archive.

## Feature guide

### 1. Add Folder and Scan / Update

- **Add Folder** lets you choose a folder for indexing.
- **Scan / Update** rescans folders already registered in the app.
- The scanner builds/updates the local index used by Search, Discovery Map, Evidence, and Investigations.
- Supported text extraction is intended for text and source/configuration files that the indexer recognizes. Do not assume every binary, image, or document format has readable text extracted.
- Large archives may take time to scan. Start with a small folder when testing.

### 2. Collections

Collections presents registered folders and their indexed files.

- Select a file to see its location, size, type, modification details, hash when available, and a text preview.
- Double-clicking a file entry may open it using the operating system's default application.
- The preview is only a partial view of indexed content, not necessarily the entire file.
- Removing a file from an investigation does not delete the original file.

### 3. Search

Search queries the local index. Depending on the indexed content, use:

- A filename or part of a filename.
- A folder/path fragment.
- A case number or invoice/reference identifier.
- A distinctive phrase from a text file.

Select a result to inspect it and its relationships. Double-click a result to open the underlying file if the application supports it.

### 4. Discovery Map

The map visualizes files as nodes and detected relationships as edges.

- **Click a node:** select it and inspect its relationship evidence.
- **Double-click a node:** focus the map on that file.
- **Scroll:** zoom in or out.
- **Drag:** pan around the map.
- **Relationship filter:** show all relationships or focus on a type, such as exact duplicates, shared identifiers, or shared terms.
- **Show all connected files:** return to the broader set of connected files.
- **Fit map:** fit the visible graph into the map area.
- **Show full filenames:** display longer filenames when labels are shortened.
- Hover over a node to inspect its full path where supported.

A busy map can contain overlapping labels or many edges. Filter relationship types, focus on one node, or use Evidence for a clearer explanation.

### 5. Evidence

The Evidence tab lists related files and the detected relationship, evidence description, and score.

Common relationship types include:

- **Exact duplicate:** files have matching content hashes when both hashes are available.
- **Shared identifier:** files mention the same identifier, such as a case number or invoice number.
- **Shared term:** files share terms considered distinctive by the current matching rules.

Select a relationship row to inspect the detailed explanation and available file metadata/previews. Scores are algorithmic relevance indicators, not probabilities that a claim is true. A shared identifier or term can occur coincidentally, so check the source files and surrounding context.

### 6. Investigations

Investigations lets you create a named workspace for a case, project, or research question.

- **New investigation:** create a workspace.
- **Title:** name it clearly, for example `CASE-2026-014 — Document Review`.
- **Add selected file:** first select a file in Collections, Search, or Discovery Map, then return to Investigations and add it.
- **Remove selected file:** remove a file from the current investigation's list; the original file and main index remain.
- **Investigation notes:** record hypotheses, dates, questions, follow-up tasks, and conclusions.
- **Save title / notes:** save your current edits.
- **Delete investigation:** delete the investigation and its notes after confirmation. This does not delete the indexed source files.

Investigations store references to indexed files rather than making copies of the originals. If a source file is moved or deleted outside ECHO, its stored path may no longer resolve until you scan/update the collection.

### 7. Export HTML report

1. Open **Investigations**.
2. Select the investigation.
3. Save pending title/notes changes.
4. Click **Export HTML report**.
5. Choose a destination and filename.

The report includes the investigation title and notes, evidence-file details, paths, hashes where available, text previews, and indexed connection evidence. It is a self-contained HTML file and can be opened in a web browser.

To create a PDF, open the HTML report in a browser and select **Print → Save as PDF**. Page layout depends on the browser and printer settings.

The report is an export of indexed data at the time of export. It does not modify the original files, and it does not certify the accuracy of inferred relationships.

## Local data, privacy, and safety

- ECHO is designed to keep its index on the local computer; it does not need a cloud account or a GPU.
- The local database stores file metadata, indexed text and relationships, plus investigation titles, notes, and file associations.
- Do not index folders you are not authorized to inspect.
- Reports may contain full paths, snippets of file content, and investigation notes. Store and share exported reports carefully.
- If you share a report, check it for private information first.
- ECHO's relationships are leads for human review, not legal, financial, or forensic conclusions.
- Back up the database and reports you need to retain.

### Database location

The app stores its database in the per-user application data area, rather than inside the source folder. Typical locations are:

- **Windows:** `%LOCALAPPDATA%\JASS\ECHO\echo.sqlite3`
- **Linux:** `~/.local/share/JASS/ECHO/echo.sqlite3`

The exact path can vary with the current build and operating system conventions. If you are upgrading, preserve the existing database.

## Troubleshooting

### The app does not start

- Confirm Python 3.11+ is installed.
- From the project folder, run `python -m pip install -r requirements.txt`.
- On Linux, use `python3` if `python` is not mapped to Python 3.
- Launch from a terminal so that any error message remains visible.

### `No module named PySide6`

Install the requirements with the same Python interpreter used to run ECHO:

```powershell
python -m pip install -r requirements.txt
python run.py
```

On Linux, replace `python` with `python3` as needed.

### Search or the map shows few connections

- Confirm the scan completed and that the intended folder is listed.
- Try a small sample collection with deliberately repeated identifiers.
- Some files may contain little extractable text, and unrelated files should not be expected to connect.
- Use the relationship filter and select individual nodes to reduce clutter.

### A file preview is incomplete

Previews are intentionally limited and depend on the file type and indexing limits. Open the original file in its usual application for complete content.

### An indexed path no longer works

The source file may have been moved, renamed, or deleted outside ECHO. Re-add or scan the correct folder. Do not delete the database as a first troubleshooting step.

### An upgrade appears to have lost previous data

Check that the app is using the same user account and existing database location. Restore the database from backup if necessary. Do not replace the database with a blank file.

### Report export fails

- Choose a folder where your user account has write permission.
- Use a simple filename and a local destination.
- Make sure the target HTML file is not locked by another application.

## Suggested sample workflow

Use a test folder with files that intentionally share references:

1. Create `CASE-2026-014_correspondence.txt` mentioning `CASE-2026-014` and `INV-7782`.
2. Create `CASE-2026-014_meeting_notes.txt` with the same case number.
3. Create `INV-7782_invoice.txt` mentioning the invoice identifier.
4. Create `unrelated_expense.txt` with no matching identifiers.
5. Add the sample folder, scan it, and explore Search, Discovery Map, and Evidence.
6. Create an investigation, add the related files, write notes, and export a report.

This makes it easier to see how shared identifiers can reveal candidate connections and how an unrelated file may remain unconnected.

---

**JASS ECHO v0.8.0** — local file discovery and investigation workspace.
