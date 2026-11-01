import os
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget


class BatchWorker(QThread):
    video_started = Signal(int, str)
    video_finished = Signal(int, str)
    video_failed = Signal(int, str)
    batch_finished = Signal()

    def __init__(self, videos: list[str], output_dir: str, parent=None):
        super().__init__(parent)
        self.videos = videos
        self.output_dir = output_dir

    def run(self):
        # Import in the worker thread, keeping pipeline dependencies out of UI startup.
        try:
            try:
                from pipeline import TracePipeline
            except ImportError:
                from ...pipeline import TracePipeline

            used_names = set()
            for index, video_path in enumerate(self.videos):
                self.video_started.emit(index, video_path)
                try:
                    name = Path(video_path).stem or f"video_{index + 1}"
                    output_name = name
                    suffix = 2
                    while output_name.casefold() in used_names:
                        output_name = f"{name}_{suffix}"
                        suffix += 1
                    used_names.add(output_name.casefold())

                    output_path = os.path.join(self.output_dir, output_name)
                    os.makedirs(output_path, exist_ok=True)
                    TracePipeline(video_path, output_path).run()
                    self.video_finished.emit(index, output_path)
                except Exception as error:
                    self.video_failed.emit(index, str(error))
        except Exception as error:
            # Import/setup failure applies to every queued video.
            for index, video_path in enumerate(self.videos):
                self.video_failed.emit(index, str(error))
        finally:
            self.batch_finished.emit()


class BatchProgressView(QWidget):
    home_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        self._statuses = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        title = QLabel("Batch Progress")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.summary = QLabel("Preparing batch…")
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("font-size: 13px;")
        self.done_button = QPushButton("Back to Batch Processing")
        self.done_button.setEnabled(False)
        self.done_button.clicked.connect(self.home_requested.emit)

        layout.addWidget(title)
        layout.addWidget(self.summary)
        layout.addWidget(self.file_list, stretch=1)
        layout.addWidget(self.done_button, alignment=Qt.AlignmentFlag.AlignRight)

    def begin_batch(self, videos: list[str]):
        self.file_list.clear()
        self._items = []
        self._statuses = ["queued"] * len(videos)
        for video in videos:
            item = QListWidgetItem(f"{video} — Queued")
            item.setToolTip(video)
            self.file_list.addItem(item)
            self._items.append(item)
        self.summary.setText(f"0 of {len(videos)} videos complete")
        self.done_button.setEnabled(False)

    def mark_started(self, index: int, video: str):
        self._statuses[index] = "processing"
        self._items[index].setText(f"{video} — Processing…")
        self.summary.setText(f"Processing video {index + 1} of {len(self._items)}")

    def mark_finished(self, index: int, output_path: str):
        self._statuses[index] = "complete"
        self._items[index].setText(f"{self._items[index].toolTip()} — Complete ({output_path})")
        self._refresh_count()

    def mark_failed(self, index: int, message: str):
        self._statuses[index] = "failed"
        self._items[index].setText(f"{self._items[index].toolTip()} — Failed: {message}")
        self._items[index].setToolTip(message)
        self._refresh_count()

    def finish_batch(self):
        succeeded = self._statuses.count("complete")
        failed = self._statuses.count("failed")
        self.summary.setText(f"Batch finished: {succeeded} complete, {failed} failed")
        self.done_button.setEnabled(True)

    def _refresh_count(self):
        finished = self._statuses.count("complete") + self._statuses.count("failed")
        self.summary.setText(f"{finished} of {len(self._items)} videos complete")
