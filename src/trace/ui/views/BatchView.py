import os
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QGroupBox,
    QMessageBox
)
from ui.dialogs.configure_ai import ConfigureAIDialog

class BatchView(QWidget):
    """View for high-throughput video selection, pipeline setup, and batch execution."""

    home_requested = Signal()
    start_batch_requested = Signal(list, dict)  # Emits (file_list, output_options)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.showing_only_selected = False
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # ---------------------------------------------------------------------
        # Top Header Bar
        # ---------------------------------------------------------------------
        top_bar = QHBoxLayout()
        header = QLabel("Batch Processing")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")

        btn_home = QPushButton("Home")
        btn_home.setFixedWidth(80)
        btn_home.setFixedHeight(32)
        btn_home.clicked.connect(self.home_requested.emit)

        top_bar.addWidget(header)
        top_bar.addStretch()
        top_bar.addWidget(btn_home)
        layout.addLayout(top_bar)

        # ---------------------------------------------------------------------
        # Directory Navigation Bar
        # ---------------------------------------------------------------------
        dir_layout = QHBoxLayout()

        self.txt_dir_path = QLineEdit()
        btn_select_folder = QPushButton("Select Folder")
        btn_select_folder.clicked.connect(self._select_folder)

        self.btn_toggle_view = QPushButton("Selected Files")
        self.btn_toggle_view.setCheckable(True)
        self.btn_toggle_view.toggled.connect(self._toggle_selected_view)

        self.btn_select_all = QPushButton("Select All")
        self.btn_select_all.clicked.connect(self._select_all_files)

        dir_layout.addWidget(self.txt_dir_path, stretch=4)
        dir_layout.addWidget(btn_select_folder)
        dir_layout.addWidget(self.btn_toggle_view)
        dir_layout.addWidget(self.btn_select_all)

        layout.addLayout(dir_layout)

        # ---------------------------------------------------------------------
        # File List with Checkboxes
        # ---------------------------------------------------------------------
        self.file_list_widget = QListWidget()
        self.file_list_widget.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.file_list_widget, stretch=1)

        # ---------------------------------------------------------------------
        # Bottom Controls Split Area
        # ---------------------------------------------------------------------
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)

        # Left Column: AI Configuration Button
        left_col = QVBoxLayout()
        btn_config_ai = QPushButton("Configure AI Vision")
        btn_config_ai.setFixedHeight(45)
        btn_config_ai.setStyleSheet("font-size: 14px; font-weight: bold;")
        btn_config_ai.clicked.connect(self._open_ai_config)
        left_col.addWidget(btn_config_ai)
        left_col.addStretch()

        # Right Column: Output Options
        output_box = QGroupBox("Output Options")
        output_layout = QVBoxLayout(output_box)

        out_path_layout = QHBoxLayout()
        out_path_layout.addWidget(QLabel("Output Folder:"))
        self.txt_output_dir = QLineEdit()
        btn_browse_output = QPushButton("Browse...")
        btn_browse_output.clicked.connect(self._select_output_folder)
        out_path_layout.addWidget(self.txt_output_dir)
        out_path_layout.addWidget(btn_browse_output)
        output_layout.addLayout(out_path_layout)

        bottom_layout.addLayout(left_col, stretch=1)
        bottom_layout.addWidget(output_box, stretch=2)

        layout.addLayout(bottom_layout)

        # ---------------------------------------------------------------------
        # Execute Action Bar
        # ---------------------------------------------------------------------
        run_layout = QHBoxLayout()
        run_layout.addStretch()

        self.btn_run = QPushButton("Run Batch")
        self.btn_run.setFixedHeight(45)
        self.btn_run.setFixedWidth(150)
        self.btn_run.setStyleSheet("background-color: #2b5b84; color: white; font-size: 15px; font-weight: bold;")
        self.btn_run.clicked.connect(self._on_run_clicked)

        run_layout.addWidget(self.btn_run)
        layout.addLayout(run_layout)

    def get_selected_files(self) -> list[str]:
        """Returns list of checked file paths."""
        selected = []
        base_path = self.txt_dir_path.text()
        for i in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(os.path.join(base_path, item.text()))
        return selected

    def _select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Video Directory")
        if folder:
            self.txt_dir_path.setText(folder)
            self.file_list_widget.clear()
            try:
                for file in os.listdir(folder):
                    if file.endswith(('.avi', '.mp4', '.mkv', '.mov')):
                        item = QListWidgetItem(file)
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                        item.setCheckState(Qt.CheckState.Unchecked)
                        self.file_list_widget.addItem(item)
            except Exception as e:
                QMessageBox.critical(self, "Error Reading Directory", str(e))

    def _select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if folder:
            self.txt_output_dir.setText(folder)

    def _select_all_files(self):
        for i in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(i)
            if not item.isHidden():
                item.setCheckState(Qt.CheckState.Checked)

    def _toggle_selected_view(self, checked: bool):
        self.showing_only_selected = checked
        self.btn_toggle_view.setText("Show All" if checked else "Selected Files")
        
        for i in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(i)
            if checked:
                item.setHidden(item.checkState() != Qt.CheckState.Checked)
            else:
                item.setHidden(False)

    def _open_ai_config(self):
        selected = self.get_selected_files()
        dialog = ConfigureAIDialog(selected, parent=self)
        dialog.exec()

    def _on_run_clicked(self):
        selected = self.get_selected_files()
        if not selected:
            QMessageBox.warning(self, "No Files Selected", "Please select at least one video to process.")
            return

        output_dir = self.txt_output_dir.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "Output Folder Required", "Please select an output folder.")
            return

        opts = {"output_dir": output_dir}
        self.start_batch_requested.emit(selected, opts)
