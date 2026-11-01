import os
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QFileDialog,
    QFrame,
    QComboBox,
    QGroupBox
)

class ConfigureAIDialog(QDialog):
    """Modal dialog for tweaking vision pipeline filters and background subtraction parameters."""

    def __init__(self, selected_files: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure AI Vision")
        self.resize(900, 650)
        self.selected_files = selected_files or ["/home/user/raw_video.avi"]
        self.current_file_idx = 0

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        # ---------------------------------------------------------------------
        # 1. Dual Video Preview Area (Raw vs Filtered)
        # ---------------------------------------------------------------------
        video_preview_layout = QHBoxLayout()
        video_preview_layout.setSpacing(10)

        # Raw Video Container
        raw_box = QGroupBox("Raw Video")
        raw_layout = QVBoxLayout(raw_box)
        self.lbl_raw_feed = QLabel("Raw Video Feed\n(No Filter Applied)")
        self.lbl_raw_feed.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_raw_feed.setStyleSheet("background-color: #1e1e1e; color: #888888; border-radius: 4px; min-height: 250px;")
        raw_layout.addWidget(self.lbl_raw_feed)

        # Filtered Video Container
        filtered_box = QGroupBox("Filtered Video")
        filtered_layout = QVBoxLayout(filtered_box)
        self.lbl_filtered_feed = QLabel("Filtered Video Feed\n(Background Subtraction / Thresholding)")
        self.lbl_filtered_feed.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_filtered_feed.setStyleSheet("background-color: #1e1e1e; color: #888888; border-radius: 4px; min-height: 250px;")
        filtered_layout.addWidget(self.lbl_filtered_feed)

        video_preview_layout.addWidget(raw_box)
        video_preview_layout.addWidget(filtered_box)
        main_layout.addLayout(video_preview_layout)

        # ---------------------------------------------------------------------
        # 2. File Selection Bar (Prev / File Path Display / Remove)
        # ---------------------------------------------------------------------
        file_bar_box = QGroupBox("Selected File Preview Tuning")
        file_bar_layout = QHBoxLayout(file_bar_box)

        self.btn_prev_file = QPushButton("Prev")
        self.btn_prev_file.setFixedWidth(60)
        self.btn_prev_file.clicked.connect(self._prev_file)

        self.txt_active_file = QLineEdit()
        self.txt_active_file.setReadOnly(True)

        self.btn_next_file = QPushButton("Next")
        self.btn_next_file.setFixedWidth(60)
        self.btn_next_file.clicked.connect(self._next_file)

        self.btn_remove = QPushButton("Remove")
        self.btn_remove.setStyleSheet("background-color: #d9534f; color: white;")
        self.btn_remove.clicked.connect(self._remove_current_file)

        file_bar_layout.addWidget(self.btn_prev_file)
        file_bar_layout.addWidget(self.txt_active_file)
        file_bar_layout.addWidget(self.btn_next_file)
        file_bar_layout.addWidget(self.btn_remove)

        main_layout.addWidget(file_bar_box)

        # ---------------------------------------------------------------------
        # 3. Vision Pipeline Config File Selection
        # ---------------------------------------------------------------------
        config_box = QGroupBox("Pipeline Parameters & Background Image")
        config_grid = QGridLayout(config_box)

        config_grid.addWidget(QLabel("Config File (.json):"), 0, 0)
        self.txt_config_path = QLineEdit("/home/user/config_file.json")
        btn_browse_config = QPushButton("Browse...")
        btn_browse_config.clicked.connect(self._browse_config)
        btn_save_config = QPushButton("Save")

        config_grid.addWidget(self.txt_config_path, 0, 1)
        config_grid.addWidget(btn_browse_config, 0, 2)
        config_grid.addWidget(btn_save_config, 0, 3)

        config_grid.addWidget(QLabel("Background Image:"), 1, 0)
        self.txt_bg_path = QLineEdit("Auto-generated background")
        btn_browse_bg = QPushButton("Browse...")
        btn_browse_bg.clicked.connect(self._browse_bg)

        config_grid.addWidget(self.txt_bg_path, 1, 1)
        config_grid.addWidget(btn_browse_bg, 1, 2)

        main_layout.addWidget(config_box)

        # ---------------------------------------------------------------------
        # 4. Action Buttons (Apply & Close)
        # ---------------------------------------------------------------------
        action_layout = QHBoxLayout()
        action_layout.addStretch()

        btn_apply = QPushButton("Select Files to Apply")
        btn_apply.setFixedHeight(35)
        btn_apply.setStyleSheet("font-weight: bold; padding-left: 15px; padding-right: 15px;")
        btn_apply.clicked.connect(self.accept)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedHeight(35)
        btn_cancel.clicked.connect(self.reject)

        action_layout.addWidget(btn_apply)
        action_layout.addWidget(btn_cancel)

        main_layout.addLayout(action_layout)

        self._update_file_display()

    def _update_file_display(self):
        if self.selected_files:
            file_path = self.selected_files[self.current_file_idx]
            self.txt_active_file.setText(f"File {self.current_file_idx + 1}/{len(self.selected_files)}: {file_path}")
        else:
            self.txt_active_file.setText("No files selected")

    def _prev_file(self):
        if self.selected_files and self.current_file_idx > 0:
            self.current_file_idx -= 1
            self._update_file_display()

    def _next_file(self):
        if self.selected_files and self.current_file_idx < len(self.selected_files) - 1:
            self.current_file_idx += 1
            self._update_file_display()

    def _remove_current_file(self):
        if self.selected_files:
            self.selected_files.pop(self.current_file_idx)
            if self.current_file_idx >= len(self.selected_files) and self.current_file_idx > 0:
                self.current_file_idx -= 1
            self._update_file_display()

    def _browse_config(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Vision Config", "", "JSON Files (*.json)")
        if path:
            self.txt_config_path.setText(path)

    def _browse_bg(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Background Image", "", "Image Files (*.png *.jpg *.tiff)")
        if path:
            self.txt_bg_path.setText(path)
