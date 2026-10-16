import math
from PySide6.QtCore import QPointF, Signal, Qt
from PySide6.QtGui import QColor, QPen, QBrush, QFont, QPainter
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsItem, QGraphicsSimpleTextItem

COLORS = {"Exact duplicate": "#e7a34d", "Shared identifier": "#4dc6bd", "Shared term": "#7187bc"}

def short_label(name, limit=28):
    return name if len(name) <= limit else name[:limit - 1] + "…"

class NodeItem(QGraphicsEllipseItem):
    def __init__(self, record, center=False, show_full_labels=False):
        radius = 29 if not center else 35
        super().__init__(-radius, -radius, radius * 2, radius * 2)
        self.record = record
        self.setBrush(QBrush(QColor("#e7a34d" if center else "#263a50")))
        self.setPen(QPen(QColor("#f3c879" if center else "#4c718a"), 2 if center else 1.2))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)
        self.setToolTip(f"{record['name']}\n{record['path']}\nDouble-click to focus this file")
        self.setZValue(2)
        self.label = QGraphicsSimpleTextItem(record["name"] if show_full_labels else short_label(record["name"]), self)
        self.label.setBrush(QBrush(QColor("#f3f6fb")))
        self.label.setFont(QFont("Segoe UI", 8))
        self.label.setPos(-min(160, max(56, self.label.boundingRect().width() / 2)), radius + 5)
        self.label.setVisible(show_full_labels)

    def set_label_visible(self, visible):
        self.label.setVisible(visible)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            self.setPen(QPen(QColor("#ffffff"), 3 if value else 1.2))
        return super().itemChange(change, value)

class GraphView(QGraphicsView):
    node_selected = Signal(int)
    node_activated = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene_obj = QGraphicsScene(self)
        self.setScene(self.scene_obj)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setBackgroundBrush(QBrush(QColor("#0d1320")))
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setMinimumHeight(360)
        self.nodes = {}
        self._show_full_labels = False

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        item = self.itemAt(event.position().toPoint())
        while item and not isinstance(item, NodeItem):
            item = item.parentItem()
        if isinstance(item, NodeItem):
            self.node_selected.emit(int(item.record["id"]))

    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        while item and not isinstance(item, NodeItem):
            item = item.parentItem()
        if isinstance(item, NodeItem):
            self.node_activated.emit(int(item.record["id"]))
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def set_full_labels(self, visible):
        self._show_full_labels = bool(visible)
        for node in self.nodes.values():
            node.label.setText(node.record["name"] if visible else short_label(node.record["name"]))
            node.label.setPos(-min(160, max(56, node.label.boundingRect().width() / 2)),
                              node.rect().height() / 2 + 5)
            node.set_label_visible(visible)

    def fit_graph(self):
        rect = self.scene_obj.itemsBoundingRect().adjusted(-45, -45, 45, 45)
        if not rect.isNull():
            self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)

    def draw_graph(self, records, edges, center_id=None, kind_filter="All"):
        self.scene_obj.clear()
        self.nodes = {}
        if kind_filter != "All":
            edges = [e for e in edges if e["kind"] == kind_filter]
        by_id = {int(r["id"]): r for r in records}
        ids = set()
        for edge in edges:
            ids.update((int(edge["source_id"]), int(edge["target_id"])))
        if center_id and int(center_id) in by_id:
            ids.add(int(center_id))
        if not ids:
            item = self.scene_obj.addText("No connections match this filter. Try another relationship type or scan a folder.", QFont("Segoe UI", 12))
            item.setDefaultTextColor(QColor("#9ba8bd"))
            self.scene_obj.setSceneRect(-360, -180, 720, 360)
            return
        ids = [fid for fid in ids if fid in by_id]
        center = int(center_id) if center_id and int(center_id) in by_id else ids[0]
        others = [fid for fid in ids if fid != center]
        positions = {center: QPointF(0, 0)}
        for index, fid in enumerate(others):
            angle = index * 2.399963229728653
            radius = 205 + 48 * math.sqrt(index + 1)
            positions[fid] = QPointF(math.cos(angle) * radius, math.sin(angle) * radius)
        for edge in edges:
            a, b = int(edge["source_id"]), int(edge["target_id"])
            if a not in positions or b not in positions:
                continue
            line = QGraphicsLineItem(positions[a].x(), positions[a].y(), positions[b].x(), positions[b].y())
            color = QColor(COLORS.get(edge["kind"], "#7187bc"))
            color.setAlpha(175 if edge["kind"] != "Shared term" else 95)
            line.setPen(QPen(color, 2.4 if edge["kind"] == "Exact duplicate" else 1.2))
            line.setZValue(0)
            line.setToolTip("{} · score {:.2f}\\n{}".format(
                edge.get("kind", "Relationship"), float(edge.get("score", 0)),
                edge.get("reason", "")))
            self.scene_obj.addItem(line)
        for fid, pos in positions.items():
            node = NodeItem(by_id[fid], fid == center, self._show_full_labels)
            node.setPos(pos)
            self.scene_obj.addItem(node)
            self.nodes[fid] = node
        self.scene_obj.setSceneRect(self.scene_obj.itemsBoundingRect().adjusted(-110, -100, 110, 100))
        self.centerOn(positions[center])
        self.fit_graph()
