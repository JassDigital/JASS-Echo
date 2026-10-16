import os, subprocess, sys, time
from PySide6.QtCore import Qt,QThread,Signal
from PySide6.QtWidgets import (QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QFileDialog,QMessageBox,QTabWidget,QTreeWidget,QTreeWidgetItem,QLineEdit,QPlainTextEdit,QProgressBar,QHeaderView,QComboBox,QSplitter,QCheckBox)
from app.config import APP_NAME,APP_VERSION
from app.services.indexing_service import IndexingService
from app.ui.graph_view import GraphView

class Worker(QThread):
    done=Signal(int,int); failed=Signal(str); progress=Signal(int,str)
    def __init__(self,repo,folder): super().__init__(); self.repo=repo; self.folder=folder
    def run(self):
        try:
            self.service=IndexingService(self.repo)
            count,edges=self.service.index_folder(self.folder,lambda n,p:self.progress.emit(n,p))
            self.done.emit(count,edges)
        except Exception as e: self.failed.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self,repo):
        super().__init__(); self.repo=repo; self.worker=None; self.selected_id=None
        self.setWindowTitle(f"{APP_NAME} — Local Discovery"); self.resize(1380,880); self.setMinimumSize(1000,650)
        central=QWidget(); self.setCentralWidget(central); layout=QVBoxLayout(central); layout.setContentsMargins(22,18,22,18); layout.setSpacing(12)
        head=QHBoxLayout(); titles=QVBoxLayout()
        hero=QLabel("JASS ECHO"); hero.setObjectName("Hero")
        sub=QLabel("LOCAL DISCOVERY  /  Find the connections hiding in your files"); sub.setObjectName("Muted")
        titles.addWidget(hero); titles.addWidget(sub); head.addLayout(titles); head.addStretch()
        self.add_btn=QPushButton("＋  Add Folder"); self.scan_btn=QPushButton("↻  Scan / Update")
        self.add_btn.clicked.connect(self.add_folder); self.scan_btn.clicked.connect(self.scan_existing)
        head.addWidget(self.add_btn); head.addWidget(self.scan_btn); layout.addLayout(head)
        self.status=QLabel("Private by design · Indexing stays on this computer"); self.status.setObjectName("Muted"); layout.addWidget(self.status)
        self.tabs=QTabWidget(); layout.addWidget(self.tabs,1)
        self.collection_tab=QWidget(); self.search_tab=QWidget(); self.connections_tab=QWidget(); self.graph_tab=QWidget(); self.investigation_tab=QWidget()
        self.tabs.addTab(self.collection_tab,"Collections"); self.tabs.addTab(self.search_tab,"Search")
        self.tabs.addTab(self.graph_tab,"Discovery Map"); self.tabs.addTab(self.connections_tab,"Evidence")
        self.tabs.addTab(self.investigation_tab,"Investigations")
        self.build_collections(); self.build_search(); self.build_graph(); self.build_connections(); self.build_investigations()
        self.progress=QProgressBar(); self.progress.setRange(0,0); self.progress.hide(); layout.addWidget(self.progress)
        self.statusBar().showMessage(f"JASS ECHO v{APP_VERSION}"); self.refresh()
    def build_collections(self):
        l=QVBoxLayout(self.collection_tab); self.files=QTreeWidget(); self.files.setHeaderLabels(["File / collection","Type","Size","Modified"])
        self.files.header().setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch); self.files.itemSelectionChanged.connect(self.file_selected); l.addWidget(self.files)
        self.preview=QPlainTextEdit(); self.preview.setReadOnly(True); self.preview.setMaximumHeight(125); self.preview.setPlaceholderText("Select a file to inspect metadata and text preview."); l.addWidget(self.preview)
    def build_search(self):
        l=QVBoxLayout(self.search_tab); row=QHBoxLayout(); self.query=QLineEdit(); self.query.setPlaceholderText("Search names, paths, or indexed text…"); self.query.returnPressed.connect(self.search)
        b=QPushButton("Search"); b.clicked.connect(self.search); row.addWidget(self.query,1); row.addWidget(b); l.addLayout(row)
        self.results=QTreeWidget(); self.results.setHeaderLabels(["Result","Type","Size","Path"]); self.results.header().setSectionResizeMode(3,QHeaderView.ResizeMode.Stretch); self.results.itemDoubleClicked.connect(self.open_item); self.results.itemSelectionChanged.connect(self.search_selected); l.addWidget(self.results,1)
        self.search_note=QLabel("Double-click a result to open it; select a result to view its relationships."); self.search_note.setObjectName("Muted"); l.addWidget(self.search_note)
    def build_graph(self):
        l=QVBoxLayout(self.graph_tab); row=QHBoxLayout()
        intro=QLabel("Select a node to inspect its evidence. Scroll to zoom; drag to pan."); intro.setObjectName("Muted"); row.addWidget(intro,1)
        self.filter=QComboBox(); self.filter.addItems(["All","Exact duplicate","Shared identifier","Shared term"]); self.filter.currentTextChanged.connect(self.refresh_graph); row.addWidget(QLabel("Relationship:")); row.addWidget(self.filter)
        reset=QPushButton("Show all connected files"); reset.clicked.connect(self.show_all_graph); row.addWidget(reset)
        fit=QPushButton("Fit map"); fit.clicked.connect(lambda: self.graph.fit_graph()); row.addWidget(fit)
        self.full_labels=QCheckBox("Show full filenames"); self.full_labels.toggled.connect(lambda value: self.graph.set_full_labels(value)); row.addWidget(self.full_labels)
        l.addLayout(row)
        self.graph=GraphView(); self.graph.node_selected.connect(self.graph_node_selected); self.graph.node_activated.connect(self.graph_node_activated); l.addWidget(self.graph,1)
        self.graph_info=QLabel("Click a node for evidence · Double-click to focus · Scroll to zoom · Drag to pan · Hover for full path"); self.graph_info.setObjectName("Muted"); l.addWidget(self.graph_info)
    def build_connections(self):
        l=QVBoxLayout(self.connections_tab); self.conn_title=QLabel("Choose a file to inspect its connections"); self.conn_title.setObjectName("Hero"); l.addWidget(self.conn_title)
        self.connections=QTreeWidget(); self.connections.setHeaderLabels(["Related file","Relationship","Evidence","Score"])
        self.connections.header().setSectionResizeMode(0,QHeaderView.ResizeMode.ResizeToContents)
        self.connections.header().setSectionResizeMode(1,QHeaderView.ResizeMode.ResizeToContents)
        self.connections.header().setSectionResizeMode(2,QHeaderView.ResizeMode.Stretch)
        self.connections.header().setSectionResizeMode(3,QHeaderView.ResizeMode.ResizeToContents)
        self.connections.setWordWrap(False)
        self.connections.itemDoubleClicked.connect(self.open_item); self.connections.itemSelectionChanged.connect(self.connection_selected)
        split=QSplitter(Qt.Orientation.Vertical)
        split.addWidget(self.connections)
        self.evidence_detail=QPlainTextEdit(); self.evidence_detail.setReadOnly(True)
        self.evidence_detail.setPlaceholderText("Select a connection to compare both files and inspect the evidence.")
        split.addWidget(self.evidence_detail); split.setSizes([430,190]); l.addWidget(split,1)
    def build_investigations(self):
        layout=QVBoxLayout(self.investigation_tab)
        bar=QHBoxLayout()
        self.investigation_pick=QComboBox()
        self.investigation_pick.currentIndexChanged.connect(self.load_investigation)
        new_btn=QPushButton("＋ New investigation"); new_btn.clicked.connect(self.new_investigation)
        save_btn=QPushButton("Save title / notes"); save_btn.clicked.connect(self.save_investigation)
        add_btn=QPushButton("Add selected file"); add_btn.clicked.connect(self.add_file_to_investigation)
        remove_btn=QPushButton("Remove selected file"); remove_btn.clicked.connect(self.remove_file_from_investigation)
        delete_btn=QPushButton("Delete investigation"); delete_btn.clicked.connect(self.delete_current_investigation)
        export_btn=QPushButton("Export HTML report"); export_btn.clicked.connect(self.export_investigation_report)
        for widget in (self.investigation_pick,new_btn,save_btn,add_btn,remove_btn,delete_btn,export_btn): bar.addWidget(widget)
        layout.addLayout(bar)
        self.investigation_title=QLineEdit(); self.investigation_title.setPlaceholderText("Investigation title")
        layout.addWidget(self.investigation_title)
        self.investigation_files_view=QTreeWidget()
        self.investigation_files_view.setHeaderLabels(["Evidence file","Type","Size","Full path"])
        self.investigation_files_view.header().setSectionResizeMode(0,QHeaderView.ResizeMode.ResizeToContents)
        self.investigation_files_view.header().setSectionResizeMode(3,QHeaderView.ResizeMode.Stretch)
        self.investigation_files_view.itemDoubleClicked.connect(self.open_item)
        layout.addWidget(self.investigation_files_view,2)
        layout.addWidget(QLabel("Investigation notes (saved locally in your ECHO database)"))
        self.investigation_notes=QPlainTextEdit()
        self.investigation_notes.setPlaceholderText("Record your working theory, dates, questions, and next steps. These notes are not written into original files.")
        layout.addWidget(self.investigation_notes,1)
        self.refresh_investigations()

    def refresh_investigations(self, select_id=None):
        if not hasattr(self,"investigation_pick"): return
        rows=self.repo.investigations()
        self.investigation_pick.blockSignals(True)
        self.investigation_pick.clear()
        for row in rows:
            self.investigation_pick.addItem(f"{row['title']}  ({row['file_count']} files)", row["id"])
        idx=next((i for i in range(self.investigation_pick.count())
                  if self.investigation_pick.itemData(i)==select_id), 0 if rows else -1)
        self.investigation_pick.setCurrentIndex(idx)
        self.investigation_pick.blockSignals(False)
        self.load_investigation()

    def current_investigation_id(self):
        return self.investigation_pick.currentData() if hasattr(self,"investigation_pick") else None

    def load_investigation(self, *args):
        if not hasattr(self,"investigation_files_view"): return
        iid=self.current_investigation_id()
        self.investigation_files_view.clear()
        row=self.repo.investigation_by_id(iid) if iid else None
        self.investigation_title.setText(row["title"] if row else "")
        self.investigation_notes.setPlainText(row["notes"] if row else "")
        for f in (self.repo.investigation_files(iid) if row else []):
            item=QTreeWidgetItem([f["name"],f["extension"] or "—",self.size_text(f["size"]),f["path"]])
            item.setData(0,Qt.ItemDataRole.UserRole,f["id"])
            self.investigation_files_view.addTopLevelItem(item)
        enabled=bool(row)
        self.investigation_title.setEnabled(enabled); self.investigation_notes.setEnabled(enabled)
        for name in ("save_btn",): pass

    def new_investigation(self):
        iid=self.repo.create_investigation("New investigation")
        self.refresh_investigations(iid)
        self.investigation_title.setFocus(); self.investigation_title.selectAll()

    def save_investigation(self):
        iid=self.current_investigation_id()
        if not iid: return
        self.repo.save_investigation(iid,self.investigation_title.text(),self.investigation_notes.toPlainText())
        self.refresh_investigations(iid)
        self.statusBar().showMessage("Investigation saved locally",3000)

    def add_file_to_investigation(self):
        iid=self.current_investigation_id()
        if not iid:
            QMessageBox.information(self,APP_NAME,"Create an investigation first."); return
        if not self.selected_id:
            QMessageBox.information(self,APP_NAME,"Select a file in Collections, Search, or the Discovery Map first."); return
        self.repo.add_investigation_file(iid,self.selected_id)
        self.refresh_investigations(iid)

    def remove_file_from_investigation(self):
        iid=self.current_investigation_id()
        item=self.investigation_files_view.currentItem()
        if iid and item and item.data(0,Qt.ItemDataRole.UserRole):
            self.repo.remove_investigation_file(iid,int(item.data(0,Qt.ItemDataRole.UserRole)))
            self.refresh_investigations(iid)

    def delete_current_investigation(self):
        iid=self.current_investigation_id()
        if not iid: return
        answer=QMessageBox.question(self,APP_NAME,"Delete this investigation and its notes? Indexed files will not be deleted.")
        if answer==QMessageBox.StandardButton.Yes:
            self.repo.delete_investigation(iid)
            self.refresh_investigations()

    def export_investigation_report(self):
        iid=self.current_investigation_id()
        investigation=self.repo.investigation_by_id(iid) if iid else None
        if not investigation:
            QMessageBox.information(self,APP_NAME,"Create or select an investigation first.")
            return
        # Save pending edits before exporting, so the report contains the visible title and notes.
        self.repo.save_investigation(iid,self.investigation_title.text(),self.investigation_notes.toPlainText())
        investigation=self.repo.investigation_by_id(iid)
        files=self.repo.investigation_files(iid)
        suggested="".join(c if c.isalnum() or c in "-_ " else "_" for c in investigation["title"]).strip()
        destination,_=QFileDialog.getSaveFileName(
            self,"Export investigation report",f"{suggested or 'investigation'}-report.html",
            "HTML report (*.html)"
        )
        if not destination: return
        rows=[]
        for f in files:
            connections=self.repo.connections_for(f["id"])
            links=[]
            for edge in connections:
                links.append(
                    "<li><strong>{}</strong> — {} (score {:.2f}): {}</li>".format(
                        html.escape(str(edge["related_name"])),
                        html.escape(str(edge["kind"])),
                        float(edge["score"]),
                        html.escape(str(edge["reason"]))
                    )
                )
            rows.append(
                "<section class='file'><h2>{}</h2><p class='path'>{}</p>"
                "<dl><dt>Type</dt><dd>{}</dd><dt>Size</dt><dd>{}</dd>"
                "<dt>Modified</dt><dd>{}</dd><dt>SHA-256</dt><dd class='hash'>{}</dd></dl>"
                "<h3>Indexed text preview</h3><pre>{}</pre>"
                "<h3>Connections and evidence</h3><ul>{}</ul></section>".format(
                    html.escape(str(f["name"])),html.escape(str(f["path"])),
                    html.escape(str(f.get("extension") or "—")),self.size_text(int(f.get("size") or 0)),
                    datetime.datetime.fromtimestamp(float(f.get("modified") or 0)).astimezone().strftime("%Y-%m-%d %H:%M:%S") if f.get("modified") else "Unknown",
                    html.escape(str(f.get("sha256") or "Not calculated")),
                    html.escape(str(f.get("text_content") or "")[:5000]),
                    "".join(links) if links else "<li>No indexed connections.</li>"
                )
            )
        notes=html.escape(investigation.get("notes") or "")
        title=html.escape(investigation["title"])
        generated=datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
        document="""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} — JASS ECHO report</title>
<style>
:root{{color-scheme:light}}body{{font:15px/1.55 system-ui,Segoe UI,Arial,sans-serif;max-width:1100px;margin:32px auto;padding:0 22px;color:#182230}}
h1{{border-bottom:3px solid #2c7185;padding-bottom:12px}}h2{{margin-top:0}}.meta,.file{{border:1px solid #d4dce5;border-radius:10px;padding:18px;margin:18px 0;break-inside:avoid}}
.path,.hash{{overflow-wrap:anywhere;color:#46556a}}dt{{font-weight:700;float:left;clear:left;width:100px}}dd{{margin-left:110px;overflow-wrap:anywhere}}
pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f6fa;padding:12px;border-radius:6px}}
.notes{{white-space:pre-wrap;background:#f8fafc;padding:14px;border-left:4px solid #2c7185}}.muted{{color:#64748b}}li{{margin:5px 0}}
@media print{{body{{margin:0;max-width:none}}.file{{page-break-inside:avoid}}}}
</style></head><body><h1>JASS ECHO — Investigation Report</h1>
<p class="muted">Generated locally on {generated}. This report is an export of indexed metadata and relationship evidence; it does not certify the truth of any inference.</p>
<div class="meta"><h2>{title}</h2><p><strong>Created:</strong> {created}<br><strong>Last updated:</strong> {updated}<br><strong>Evidence files:</strong> {count}</p>
<h3>Investigation notes</h3><div class="notes">{notes}</div></div>
<h2>Evidence files</h2>{files}
<footer class="muted"><hr>JASS ECHO · Local-first report · Original files were not modified.</footer></body></html>""".format(
            title=title,generated=html.escape(generated),
            created=html.escape(str(investigation.get("created_at") or "Unknown")),
            updated=html.escape(str(investigation.get("updated_at") or "Unknown")),
            count=len(files),notes=notes,files="".join(rows) if rows else "<p>No evidence files have been added to this investigation.</p>"
        )
        try:
            Path(destination).write_text(document,encoding="utf-8")
            self.statusBar().showMessage(f"Report exported: {destination}",5000)
            QMessageBox.information(self,APP_NAME,f"Investigation report exported successfully:\\n{destination}")
        except OSError as exc:
            QMessageBox.warning(self,APP_NAME,f"Could not export report:\\n{exc}")

    @staticmethod
    def size_text(n):
        if n<1024:return f"{n} B"
        if n<1024**2:return f"{n/1024:.1f} KB"
        if n<1024**3:return f"{n/1024**2:.1f} MB"
        return f"{n/1024**3:.2f} GB"
    def add_folder(self):
        folder=QFileDialog.getExistingDirectory(self,"Choose a folder to index")
        if folder:self.start_scan(folder)
    def scan_existing(self):
        rows=self.repo.collections()
        if rows:self.start_scan(rows[0]["root_path"])
        else:self.add_folder()
    def start_scan(self,folder):
        if self.worker and self.worker.isRunning():QMessageBox.information(self,APP_NAME,"A scan is already running.");return
        self.progress.show();self.add_btn.setEnabled(False);self.scan_btn.setEnabled(False);self.tabs.setEnabled(False);self.status.setText(f"Scanning locally: {folder}")
        self.worker=Worker(self.repo,folder);self.worker.progress.connect(lambda n,p:self.status.setText(f"Indexed {n} files… {p}"))
        self.worker.done.connect(self.scan_done);self.worker.failed.connect(self.scan_failed);self.worker.start()
    def scan_done(self,count,edges):
        self.progress.hide();self.add_btn.setEnabled(True);self.scan_btn.setEnabled(True);self.tabs.setEnabled(True)
        stats=getattr(getattr(self.worker,"service",None),"last_stats",None)
        stats=getattr(getattr(self.worker,"service",None),"last_stats",{})
        self.status.setText(
            f"Scan complete · {count} files · {stats.get('unchanged',0)} unchanged · "
            f"{stats.get('removed',0)} removed · {edges} connections"
        )
        self.refresh();self.refresh_graph();self.refresh_investigations()
    def scan_failed(self,message):
        self.progress.hide();self.add_btn.setEnabled(True);self.scan_btn.setEnabled(True);self.tabs.setEnabled(True);self.status.setText("Scan failed");QMessageBox.warning(self,APP_NAME,message)
    def refresh(self):
        self.files.clear()
        for collection in self.repo.collections():
            root=QTreeWidgetItem([collection["root_path"],"Collection","",""]);root.setData(0,Qt.ItemDataRole.UserRole+1,collection["root_path"]);self.files.addTopLevelItem(root)
            for r in self.repo.conn.execute("SELECT * FROM files WHERE collection_id=? ORDER BY path",(collection["id"],)):
                item=QTreeWidgetItem([r["name"],r["extension"] or "—",self.size_text(r["size"]),time.strftime("%Y-%m-%d %H:%M",time.localtime(r["modified"]))])
                item.setData(0,Qt.ItemDataRole.UserRole,r["id"]);item.setToolTip(0,r["path"]);root.addChild(item)
            root.setExpanded(True)
        total=sum(self.files.topLevelItem(i).childCount() for i in range(self.files.topLevelItemCount()))
        self.statusBar().showMessage(f"{total} indexed files")
    def set_selected(self,fid):
        if not fid:return
        self.selected_id=int(fid);self.show_connections(self.selected_id);self.refresh_graph(self.filter.currentText() if hasattr(self,"filter") else "All",self.selected_id)
    def file_selected(self):
        item=self.files.currentItem()
        if not item:return
        fid=item.data(0,Qt.ItemDataRole.UserRole)
        if not fid:self.preview.setPlainText(item.text(0));return
        r=self.repo.file_by_id(int(fid))
        if not r:return
        self.preview.setPlainText(
            f"Path: {r['path']}\n"
            f"Size: {self.size_text(r['size'])} | Type: {r['extension'] or 'no extension'}\n"
            f"SHA-256: {r['sha256'] or 'not calculated'}\n\n"
            f"Text preview:\n{r['text_content'][:1000]}"
        )
        self.set_selected(int(fid))
    def search(self):
        q=self.query.text().strip();self.results.clear();found=self.repo.search(q)
        for r in found:
            item=QTreeWidgetItem([r["name"],r["extension"] or "—",self.size_text(r["size"]),r["path"]]);item.setData(0,Qt.ItemDataRole.UserRole,r["id"]);self.results.addTopLevelItem(item)
        self.search_note.setText(f"{len(found)} result(s) for “{q}”")
    def search_selected(self):
        item=self.results.currentItem()
        if item and item.data(0,Qt.ItemDataRole.UserRole):self.set_selected(item.data(0,Qt.ItemDataRole.UserRole))
    def show_connections(self,fid):
        r=self.repo.file_by_id(fid)
        if not r:return
        self.conn_title.setText(f"Connections for: {r['name']}");self.connections.clear()
        for e in self.repo.connections_for(fid):
            item=QTreeWidgetItem([e["related_name"],e["kind"],e["reason"],f"{e['score']:.2f}"])
            item.setData(0,Qt.ItemDataRole.UserRole,e["related_id"])
            item.setData(0,Qt.ItemDataRole.UserRole+1,e["reason"])
            item.setData(0,Qt.ItemDataRole.UserRole+2,e["kind"])
            item.setData(0,Qt.ItemDataRole.UserRole+3,e["score"])
            item.setToolTip(0,e["related_path"])
            self.connections.addTopLevelItem(item)
        self.evidence_detail.setPlainText("Select a relationship above to compare the two files.")
        self.tabs.setTabText(3,f"Evidence ({self.connections.topLevelItemCount()})")
    def connection_selected(self):
        item=self.connections.currentItem()
        if not item or not item.data(0,Qt.ItemDataRole.UserRole): return
        related_id=int(item.data(0,Qt.ItemDataRole.UserRole))
        related=self.repo.file_by_id(related_id)
        primary=self.repo.file_by_id(self.selected_id) if self.selected_id else None
        if not related or not primary: return
        reason=item.data(0,Qt.ItemDataRole.UserRole+1) or item.text(2)
        kind=item.data(0,Qt.ItemDataRole.UserRole+2) or item.text(1)
        score=item.data(0,Qt.ItemDataRole.UserRole+3)
        detail=(
            f"RELATIONSHIP: {kind}\nCONFIDENCE SCORE: {float(score):.2f}\n\n"
            f"WHY THESE FILES ARE CONNECTED\n{reason}\n\n"
            f"FILE A\n{primary['name']}\n{primary['path']}\n"
            f"SHA-256: {primary['sha256'] or 'not calculated'}\n\n"
            f"FILE B\n{related['name']}\n{related['path']}\n"
            f"SHA-256: {related['sha256'] or 'not calculated'}\n\n"
            f"FILE A PREVIEW\n{(primary['text_content'] or '')[:1400]}\n\n"
            f"FILE B PREVIEW\n{(related['text_content'] or '')[:1400]}"
        )
        self.evidence_detail.setPlainText(detail)
        self.statusBar().showMessage(f"Evidence: {primary['name']} ↔ {related['name']}", 5000)
    def graph_node_selected(self,fid):
        self.selected_id=int(fid)
        self.show_connections(self.selected_id)
        row=self.repo.file_by_id(fid)
        if row:
            self.statusBar().showMessage(f"Selected: {row['path']}", 5000)
    def graph_node_activated(self,fid):
        self.selected_id=int(fid)
        self.refresh_graph(center_id=self.selected_id)
    def show_all_graph(self):
        self.selected_id = None
        self.refresh_graph(center_id=None)
    def refresh_graph(self,kind=None,center_id=None):
        if not hasattr(self,"graph"):return
        kind=kind or self.filter.currentText()
        if center_id is None:center_id=self.selected_id
        records,edges=self.repo.graph_data(center_id=center_id,max_nodes=80,max_edges=140)
        self.graph.draw_graph(records,edges,center_id,kind)
    def open_item(self,item,column=0):
        fid=item.data(0,Qt.ItemDataRole.UserRole)
        if not fid:return
        r=self.repo.file_by_id(int(fid))
        if not r:return
        path=r["path"]
        try:
            if sys.platform=="win32":os.startfile(path)
            elif sys.platform=="darwin":subprocess.Popen(["open",path])
            else:subprocess.Popen(["xdg-open",path])
        except Exception as e:QMessageBox.warning(self,APP_NAME,f"Could not open file:\n{e}")
