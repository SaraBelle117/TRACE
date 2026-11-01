import os
from PySide6.QtWidgets import QMainWindow, QStackedWidget, QMessageBox
try:
    from ui.views.NavView import NavView
    from ui.views.BatchView import BatchView
    from ui.views.BatchProgressView import BatchProgressView, BatchWorker
    from ui.views.Placeholders import (
        ReviewViewPlaceholder,
        SettingsViewPlaceholder,
        DocumentationViewPlaceholder
    )
except ImportError:
    from .views.NavView import NavView
    from .views.BatchView import BatchView
    from .views.BatchProgressView import BatchProgressView, BatchWorker
    from .views.Placeholders import (
        ReviewViewPlaceholder,
        SettingsViewPlaceholder,
        DocumentationViewPlaceholder
    )

class MainWindow(QMainWindow):
    PAGE_NAV = 0
    PAGE_BATCH = 1
    PAGE_REVIEW = 2
    PAGE_SETTINGS = 3
    PAGE_DOCS = 4
    PAGE_BATCH_PROGRESS = 5

    def __init__(self):
        super().__init__()
        self.setWindowTitle("OsmoTRACE")
        self.resize(1100, 700)

        # Central Stacked Widget
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Instantiate Views
        self.nav_view = NavView()
        self.batch_view = BatchView()
        self.batch_progress_view = BatchProgressView()
        self.review_view = ReviewViewPlaceholder()
        self.settings_view = SettingsViewPlaceholder()
        self.doc_view = DocumentationViewPlaceholder()

        # Add Views to Stack
        self.stacked_widget.addWidget(self.nav_view)        # Index 0
        self.stacked_widget.addWidget(self.batch_view)      # Index 1
        self.stacked_widget.addWidget(self.review_view)     # Index 2
        self.stacked_widget.addWidget(self.settings_view)   # Index 3
        self.stacked_widget.addWidget(self.doc_view)        # Index 4
        self.stacked_widget.addWidget(self.batch_progress_view)  # Index 5
        self._batch_worker = None

        # Connect Navigation Signals
        self._connect_signals()

    def _connect_signals(self):
        # Handle Nav View routing
        self.nav_view.navigate_requested.connect(self.navigate_to)
        self.nav_view.project_selected.connect(self._open_recent_project)

        # Handle Home button clicks from child views
        self.batch_view.home_requested.connect(lambda: self.navigate_to("nav"))
        self.review_view.home_requested.connect(lambda: self.navigate_to("nav"))
        self.settings_view.home_requested.connect(lambda: self.navigate_to("nav"))
        self.doc_view.home_requested.connect(lambda: self.navigate_to("nav"))

        self.batch_view.start_batch_requested.connect(self._handle_start_batch)
        self.batch_progress_view.home_requested.connect(lambda: self.navigate_to("batch"))

    def navigate_to(self, page_name: str):
        """Switches stacked widget page based on route string."""
        mapping = {
            "nav": self.PAGE_NAV,
            "batch": self.PAGE_BATCH,
            "review": self.PAGE_REVIEW,
            "settings": self.PAGE_SETTINGS,
            "doc": self.PAGE_DOCS,
            "batch_progress": self.PAGE_BATCH_PROGRESS,
        }
        if page_name in mapping:
            self.stacked_widget.setCurrentIndex(mapping[page_name])

    def _open_recent_project(self, project_info: str):
        print(f"Opening recent project: {project_info}")
        # Automatically transition to review view when a recent project is opened
        self.navigate_to("review")

    def _handle_start_batch(self, files: list, options: dict):
        output_dir = options["output_dir"]
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as error:
            QMessageBox.critical(self, "Cannot Create Output Folder", str(error))
            return

        self.batch_progress_view.begin_batch(files)
        worker = BatchWorker(files, output_dir, self)
        worker.video_started.connect(self.batch_progress_view.mark_started)
        worker.video_finished.connect(self.batch_progress_view.mark_finished)
        worker.video_failed.connect(self.batch_progress_view.mark_failed)
        worker.batch_finished.connect(self.batch_progress_view.finish_batch)
        worker.finished.connect(self._batch_worker_finished)
        self._batch_worker = worker
        self.navigate_to("batch_progress")
        worker.start()

    def _batch_worker_finished(self):
        self._batch_worker = None
