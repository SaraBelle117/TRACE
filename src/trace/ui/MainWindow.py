from PySide6.QtWidgets import QMainWindow, QStackedWidget
try:
    from ui.views.NavView import NavView
    from ui.views.Placeholders import (
        BatchViewPlaceholder,
        ReviewViewPlaceholder,
        SettingsViewPlaceholder,
        DocumentationViewPlaceholder
    )
except ImportError:
    from .views.NavView import NavView
    from .views.Placeholders import (
        BatchViewPlaceholder,
        ReviewViewPlaceholder,
        SettingsViewPlaceholder,
        DocumentationViewPlaceholder
    )

class MainWindow(QMainWindow):
    # Page Indices
    PAGE_NAV = 0
    PAGE_BATCH = 1
    PAGE_REVIEW = 2
    PAGE_SETTINGS = 3
    PAGE_DOCS = 4

    def __init__(self):
        super().__init__()
        self.setWindowTitle("OsmoTRACE")
        self.resize(1100, 700)

        # Central Stacked Widget
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Instantiate Views
        self.nav_view = NavView()
        self.batch_view = BatchViewPlaceholder()
        self.review_view = ReviewViewPlaceholder()
        self.settings_view = SettingsViewPlaceholder()
        self.doc_view = DocumentationViewPlaceholder()

        # Add Views to Stack
        self.stacked_widget.addWidget(self.nav_view)        # Index 0
        self.stacked_widget.addWidget(self.batch_view)      # Index 1
        self.stacked_widget.addWidget(self.review_view)     # Index 2
        self.stacked_widget.addWidget(self.settings_view)   # Index 3
        self.stacked_widget.addWidget(self.doc_view)        # Index 4

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

    def navigate_to(self, page_name: str):
        """Switches stacked widget page based on route string."""
        mapping = {
            "nav": self.PAGE_NAV,
            "batch": self.PAGE_BATCH,
            "review": self.PAGE_REVIEW,
            "settings": self.PAGE_SETTINGS,
            "doc": self.PAGE_DOCS
        }
        if page_name in mapping:
            self.stacked_widget.setCurrentIndex(mapping[page_name])

    def _open_recent_project(self, project_info: str):
        print(f"Opening recent project: {project_info}")
        # Automatically transition to review view when a recent project is opened
        self.navigate_to("review")
