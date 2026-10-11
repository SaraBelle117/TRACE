from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame

class BaseViewPlaceholder(QWidget):
    """Base template view providing a top bar with a Home navigation button."""
    home_requested = Signal()

    def __init__(self, title_text: str, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # Top Header Bar
        top_bar = QHBoxLayout()
        header = QLabel(title_text)
        header.setStyleSheet("font-size: 22px; font-weight: bold;")
        
        self.btn_home = QPushButton("Home")
        self.btn_home.setFixedWidth(80)
        self.btn_home.clicked.connect(self.home_requested.emit)
        
        top_bar.addWidget(header)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_home)
        
        self.layout.addLayout(top_bar)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        self.layout.addWidget(line)
        
        # Content placeholder area
        self.content_area = QVBoxLayout()
        self.layout.addLayout(self.content_area)
        self.layout.addStretch()

class BatchViewPlaceholder(BaseViewPlaceholder):
    def __init__(self, parent=None):
        super().__init__("Batch Processing", parent)
        lbl = QLabel("Placeholder for multi-folder selection, AI config, and batch runner.")
        self.content_area.addWidget(lbl)

class ReviewViewPlaceholder(BaseViewPlaceholder):
    def __init__(self, parent=None):
        super().__init__("Video Review", parent)
        lbl = QLabel("Placeholder for video player, overlays, timeline, and worm stat panels.")
        self.content_area.addWidget(lbl)

class SettingsViewPlaceholder(BaseViewPlaceholder):
    def __init__(self, parent=None):
        super().__init__("Settings", parent)
        lbl = QLabel("Placeholder for system configuration parameters.")
        self.content_area.addWidget(lbl)

class DocumentationViewPlaceholder(BaseViewPlaceholder):
    def __init__(self, parent=None):
        super().__init__("Documentation", parent)
        lbl = QLabel("Placeholder for user manuals and metric definitions.")
        self.content_area.addWidget(lbl)
