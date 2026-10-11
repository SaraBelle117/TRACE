from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QFrame
)

class NavView(QWidget):
    # Signals emitted when navigation buttons or recent projects are clicked
    navigate_requested = Signal(str)  # "batch", "review", "settings", "doc"
    project_selected = Signal(str)   # passes project path/name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Header Title
        title = QLabel("TRACE")
        title.setStyleSheet("font-size: 28px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # 2x2 Grid for Core Action Buttons
        grid = QGridLayout()
        grid.setSpacing(15)

        self.btn_batch = QPushButton("Batch Processing")
        self.btn_review = QPushButton("Video Review")
        self.btn_settings = QPushButton("Settings")
        self.btn_doc = QPushButton("Documentation")

        # Give buttons fixed comfortable height
        for btn in (self.btn_batch, self.btn_review, self.btn_settings, self.btn_doc):
            btn.setFixedHeight(50)
            btn.setStyleSheet("font-size: 14px; font-weight: 500;")

        grid.addWidget(self.btn_batch, 0, 0)
        grid.addWidget(self.btn_review, 0, 1)
        grid.addWidget(self.btn_settings, 1, 0)
        grid.addWidget(self.btn_doc, 1, 1)

        layout.addLayout(grid)

        # Divider Line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # Recent Projects Section
        recent_label = QLabel("Recent Projects")
        recent_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(recent_label)

        self.recent_list = QListWidget()
        self.recent_list.setStyleSheet("font-size: 13px; padding: 5px;")
        layout.addWidget(self.recent_list)

        # Wire internal signals
        self.btn_batch.clicked.connect(lambda: self.navigate_requested.emit("batch"))
        self.btn_review.clicked.connect(lambda: self.navigate_requested.emit("review"))
        self.btn_settings.clicked.connect(lambda: self.navigate_requested.emit("settings"))
        self.btn_doc.clicked.connect(lambda: self.navigate_requested.emit("doc"))
        self.recent_list.itemDoubleClicked.connect(self._on_recent_item_double_clicked)

        # Populate sample recent projects
        self.populate_recent_projects([
            "Project 1 (/data/experiments/osmotic_run_1)",
            "Project 2 (/data/experiments/hypertonic_test_b)",
            "Project 3 (/data/experiments/control_group_3)"
        ])

    def populate_recent_projects(self, projects: list[str]):
        """Populates the recent projects list widget."""
        self.recent_list.clear()
        for proj in projects:
            item = QListWidgetItem(proj)
            self.recent_list.addItem(item)

    def _on_recent_item_double_clicked(self, item: QListWidgetItem):
        self.project_selected.emit(item.text())
