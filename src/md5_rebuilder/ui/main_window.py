from __future__ import annotations

import time
from pathlib import Path

from loguru import logger
from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from md5_rebuilder.core.hashing import md5_file
from md5_rebuilder.core.models import (
    PRESETS,
    JobState,
    RateControl,
    RenderJob,
    RenderProfile,
    VideoMeta,
    VideoOrientation,
)
from md5_rebuilder.services.planner import JobPlanner
from md5_rebuilder.services.probe import MediaProbe
from md5_rebuilder.ui.style import build_app_style
from md5_rebuilder.ui.workers import EncodeThread, ProbeThread
from md5_rebuilder.utils.config import SettingsStore
from md5_rebuilder.utils.formatting import duration_text, size_text

VIDEO_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov", ".flv", ".wmv", ".webm", ".m4v", ".mpg", ".mpeg"}
AI_TOOLTIP = "按下后自动修改规格为，规格为横版/竖版 720p，码率为5Mpbs，时长默认为0-15秒"


class DragSpinBox(QSpinBox):
    def __init__(self):
        super().__init__()
        self._drag_start_x: int | None = None
        self._drag_start_value = 0
        self.setCursor(Qt.SizeHorCursor)
        self.lineEdit().setCursor(Qt.SizeHorCursor)
        self.lineEdit().installEventFilter(self)
        self._line_dragging = False

    def begin_row_drag(self, global_x: int) -> None:
        self._drag_start_x = global_x
        self._drag_start_value = self.value()

    def update_row_drag(self, global_x: int) -> None:
        if self._drag_start_x is None:
            return
        delta = global_x - self._drag_start_x
        self.setValue(self._drag_start_value + round(delta / 8))

    def end_row_drag(self) -> None:
        self._drag_start_x = None

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            self.begin_row_drag(event.globalPosition().toPoint().x())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_start_x is not None and event.buttons() & Qt.LeftButton:
            self.update_row_drag(event.globalPosition().toPoint().x())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self.end_row_drag()
        super().mouseReleaseEvent(event)

    def eventFilter(self, watched, event):  # noqa: N802
        if watched is self.lineEdit():
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self.begin_row_drag(event.globalPosition().toPoint().x())
                self._line_dragging = False
            elif event.type() == QEvent.MouseMove and event.buttons() & Qt.LeftButton:
                if self._drag_start_x is not None:
                    delta = event.globalPosition().toPoint().x() - self._drag_start_x
                    if self._line_dragging or abs(delta) >= 3:
                        self._line_dragging = True
                        self.update_row_drag(event.globalPosition().toPoint().x())
                        event.accept()
                        return True
            elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                dragged = self._line_dragging
                self._line_dragging = False
                self.end_row_drag()
                if dragged:
                    event.accept()
                    return True
        return super().eventFilter(watched, event)


class DragDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, drag_step: float = 0.1):
        super().__init__()
        self._drag_step = drag_step
        self._drag_start_x: int | None = None
        self._drag_start_value = 0.0
        self.setCursor(Qt.SizeHorCursor)
        self.lineEdit().setCursor(Qt.SizeHorCursor)
        self.lineEdit().installEventFilter(self)
        self._line_dragging = False

    def begin_row_drag(self, global_x: int) -> None:
        self._drag_start_x = global_x
        self._drag_start_value = self.value()

    def update_row_drag(self, global_x: int) -> None:
        if self._drag_start_x is None:
            return
        delta = global_x - self._drag_start_x
        steps = round(delta / 8)
        self.setValue(self._drag_start_value + steps * self._drag_step)

    def end_row_drag(self) -> None:
        self._drag_start_x = None

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            self.begin_row_drag(event.globalPosition().toPoint().x())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_start_x is not None and event.buttons() & Qt.LeftButton:
            self.update_row_drag(event.globalPosition().toPoint().x())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self.end_row_drag()
        super().mouseReleaseEvent(event)

    def eventFilter(self, watched, event):  # noqa: N802
        if watched is self.lineEdit():
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self.begin_row_drag(event.globalPosition().toPoint().x())
                self._line_dragging = False
            elif event.type() == QEvent.MouseMove and event.buttons() & Qt.LeftButton:
                if self._drag_start_x is not None:
                    delta = event.globalPosition().toPoint().x() - self._drag_start_x
                    if self._line_dragging or abs(delta) >= 3:
                        self._line_dragging = True
                        self.update_row_drag(event.globalPosition().toPoint().x())
                        event.accept()
                        return True
            elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                dragged = self._line_dragging
                self._line_dragging = False
                self.end_row_drag()
                if dragged:
                    event.accept()
                    return True
        return super().eventFilter(watched, event)


class DragValueRow(QWidget):
    def __init__(self, label: str, spinbox: DragSpinBox | DragDoubleSpinBox):
        super().__init__()
        self.spinbox = spinbox
        self._dragging = False
        self.setObjectName("DragValueRow")
        self.setCursor(Qt.SizeHorCursor)
        self.setToolTip("可在整行左右拖动调整数值")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.label = QLabel(label)
        self.label.setFixedWidth(72)
        self.label.setCursor(Qt.SizeHorCursor)
        self.label.setToolTip("可在整行左右拖动调整数值")
        layout.addWidget(self.label)
        layout.addWidget(spinbox, 1)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self.spinbox.begin_row_drag(event.globalPosition().toPoint().x())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._dragging and event.buttons() & Qt.LeftButton:
            self.spinbox.update_row_drag(event.globalPosition().toPoint().x())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if self._dragging:
            self._dragging = False
            self.spinbox.end_row_drag()
            event.accept()
            return
        super().mouseReleaseEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = SettingsStore()
        self.theme_preference = str(self.settings.data.get("theme", "auto"))
        self.theme = self._resolve_theme(self.theme_preference)
        self.metas: dict[Path, VideoMeta] = {}
        self.probe_threads: list[ProbeThread] = []
        self.jobs: dict[str, RenderJob] = {}
        self.workers: dict[str, EncodeThread] = {}
        self.running = False
        self.setAcceptDrops(True)
        self.setStyleSheet(build_app_style(self.theme))
        self._build_ui()
        self._restore_settings()
        self._sync_start_state()

    def _build_ui(self) -> None:
        self.setWindowTitle("视频 MD5 重构工具V2")
        self.resize(1220, 760)
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(8)
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title = QLabel("视频 MD5 重构工具V2")
        title.setObjectName("Title")
        self.theme_btn = QPushButton(self._theme_button_text())
        self.theme_btn.setObjectName("Theme")
        self.theme_btn.clicked.connect(self.toggle_theme)
        title_row.addWidget(title)
        title_row.addWidget(self.theme_btn, 0, Qt.AlignVCenter)
        title_row.addStretch()
        desc = QLabel("批量导入、重新编码、改变视频MD5，支持音频输出控制、支持截取时间段  作者：YJY")
        desc.setObjectName("Muted")
        title_box.addLayout(title_row)
        title_box.addWidget(desc)
        header.addLayout(title_box)
        header.addStretch()
        self.add_btn = QPushButton("添加视频")
        self.add_btn.clicked.connect(self.pick_files)
        self.clear_btn = QPushButton("清空")
        self.clear_btn.clicked.connect(self.clear_all)
        header.addWidget(self.add_btn)
        header.addWidget(self.clear_btn)
        layout.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(8)
        body.addWidget(self._source_panel(), 2)
        body.addWidget(self._settings_panel(), 1)
        layout.addLayout(body, 1)
        layout.addWidget(self._output_panel())
        layout.addWidget(self._queue_panel(), 1)

        footer = QHBoxLayout()
        footer.setSpacing(8)
        self.total_progress = QProgressBar()
        self.total_progress.setRange(0, 100)
        self.total_progress.setValue(0)
        self.action_btn = QPushButton("开始重构")
        self.action_btn.setObjectName("Primary")
        self.action_btn.setEnabled(False)
        self.action_btn.setMinimumWidth(112)
        self.action_btn.clicked.connect(self._on_action_clicked)
        footer.addWidget(self.total_progress, 1)
        footer.addWidget(self.action_btn, 0, Qt.AlignRight)
        layout.addLayout(footer)

    def _panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Panel")
        return panel

    def _source_panel(self) -> QFrame:
        panel = self._panel()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        title = QLabel("素材列表")
        title.setObjectName("SectionTitle")
        self.source_hint = QLabel("拖拽视频到这里，或点击右上角添加视频")
        self.source_hint.setObjectName("Muted")
        self.source_list = QListWidget()
        self.source_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(title)
        layout.addWidget(self.source_hint)
        layout.addWidget(self.source_list, 1)
        return panel

    def _settings_panel(self) -> QFrame:
        panel = self._panel()
        grid = QGridLayout(panel)
        grid.setContentsMargins(10, 10, 10, 10)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)
        title = QLabel("输出设置")
        title.setObjectName("SectionTitle")
        self.reset_btn = QPushButton("重置")
        self.reset_btn.setObjectName("Reset")
        self.reset_btn.setToolTip("恢复默认输出参数")
        self.reset_btn.clicked.connect(self.reset_settings)
        grid.addWidget(title, 0, 0)
        grid.addWidget(self.reset_btn, 0, 1, alignment=Qt.AlignRight)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems([preset.label for preset in PRESETS])
        self.rate_combo = QComboBox()
        self.rate_combo.addItems(["CRF 质量优先", "CBR 固定码率"])
        self.crf_spin = DragSpinBox()
        self.crf_spin.setRange(15, 28)
        self.crf_spin.setValue(18)
        self.bitrate_spin = DragDoubleSpinBox(0.1)
        self.bitrate_spin.setRange(1.0, 30.0)
        self.bitrate_spin.setDecimals(1)
        self.bitrate_spin.setValue(8.0)
        self.suffix_input = QLineEdit("new")
        self.audio_check = QCheckBox("输出音频")
        self.audio_check.setChecked(True)
        self.clip_check = QCheckBox("启用截取")
        self.ai_btn = QPushButton("一键适配AI导入格式")
        self.ai_btn.setObjectName("AI")
        self.ai_btn.setToolTip(AI_TOOLTIP)
        self.ai_btn.clicked.connect(self.apply_ai_preset)
        self.start_spin = DragDoubleSpinBox(0.1)
        self.start_spin.setRange(0.0, 999999.0)
        self.start_spin.setDecimals(1)
        self.end_spin = DragDoubleSpinBox(0.1)
        self.end_spin.setRange(0.0, 999999.0)
        self.end_spin.setDecimals(1)

        rows = [
            ("分辨率", self.preset_combo),
            ("码率模式", self.rate_combo),
        ]
        for row, (label, widget) in enumerate(rows, start=1):
            grid.addWidget(QLabel(label), row, 0)
            grid.addWidget(widget, row, 1)

        self.crf_row = DragValueRow("CRF", self.crf_spin)
        self.bitrate_row = DragValueRow("码率 Mbps", self.bitrate_spin)
        self.rate_value_stack = QStackedWidget()
        self.rate_value_stack.setObjectName("RateValueStack")
        self.rate_value_stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.rate_value_stack.addWidget(self.crf_row)
        self.rate_value_stack.addWidget(self.bitrate_row)
        self.rate_combo.currentIndexChanged.connect(self._sync_rate_value_row)
        grid.addWidget(self.rate_value_stack, 3, 0, 1, 2)
        grid.addWidget(QLabel("文件后缀"), 4, 0)
        grid.addWidget(self.suffix_input, 4, 1)

        option_row = QHBoxLayout()
        option_row.setSpacing(8)
        option_checks = QVBoxLayout()
        option_checks.setContentsMargins(0, 0, 0, 0)
        option_checks.setSpacing(2)
        option_checks.addWidget(self.audio_check)
        option_checks.addWidget(self.clip_check)
        self.ai_btn.setFixedWidth(150)
        option_row.addLayout(option_checks)
        option_row.addWidget(self.ai_btn, 0, Qt.AlignVCenter)
        option_row.addStretch()
        grid.addLayout(option_row, 5, 0, 1, 2)
        grid.addWidget(DragValueRow("开始秒", self.start_spin), 6, 0, 1, 2)
        grid.addWidget(DragValueRow("结束秒", self.end_spin), 7, 0, 1, 2)
        grid.setRowStretch(8, 1)
        self._sync_rate_value_row(self.rate_combo.currentIndex())
        return panel

    def _output_panel(self) -> QFrame:
        panel = self._panel()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)
        title = QLabel("输出目录")
        title.setObjectName("SectionTitle")
        self.output_input = QLineEdit()
        self.output_input.setPlaceholderText("留空则输出到原视频目录")
        output_btn = QPushButton("选择")
        output_btn.clicked.connect(self.pick_output_dir)
        layout.addWidget(title)
        layout.addWidget(self.output_input, 1)
        layout.addWidget(output_btn)
        return panel

    def _queue_panel(self) -> QFrame:
        panel = self._panel()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        title_row = QHBoxLayout()
        title = QLabel("任务队列")
        title.setObjectName("SectionTitle")
        self.queue_summary = QLabel("0 个任务")
        self.queue_summary.setObjectName("Muted")
        title_row.addWidget(title)
        title_row.addStretch()
        title_row.addWidget(self.queue_summary)
        layout.addLayout(title_row)
        self.queue_list = QListWidget()
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        layout.addWidget(self.queue_list, 2)
        layout.addWidget(self.log_view, 1)
        return panel

    def _restore_settings(self) -> None:
        data = self.settings.data
        self.theme_preference = str(data.get("theme", "auto"))
        self.theme = self._resolve_theme(self.theme_preference)
        self._apply_theme(save=False)
        preset = str(data.get("preset", "1080p 横版"))
        preset_index = self.preset_combo.findText(preset)
        self.preset_combo.setCurrentIndex(preset_index if preset_index >= 0 else 2)
        self.rate_combo.setCurrentIndex(1 if data.get("rate_control") == "CBR" else 0)
        self._sync_rate_value_row(self.rate_combo.currentIndex())
        self.bitrate_spin.setValue(float(data.get("bitrate_mbps", 8.0)))
        self.crf_spin.setValue(int(data.get("crf", 18)))
        self.suffix_input.setText(str(data.get("suffix", "new")))
        self.audio_check.setChecked(bool(data.get("include_audio", True)))
        self.output_input.clear()

    def reset_settings(self) -> None:
        self.preset_combo.setCurrentText("1080p 横版")
        self.rate_combo.setCurrentIndex(0)
        self.crf_spin.setValue(18)
        self.bitrate_spin.setValue(8.0)
        self.suffix_input.setText("new")
        self.audio_check.setChecked(True)
        self.clip_check.setChecked(False)
        self.start_spin.setValue(0.0)
        self.end_spin.setValue(0.0)
        self._log("已恢复默认输出参数")

    def _sync_rate_value_row(self, index: int) -> None:
        """Keep one rate-control value visible, matching the active encoding mode."""
        self.rate_value_stack.setCurrentIndex(index)

    def pick_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择视频",
            "",
            "视频文件 (*.mp4 *.avi *.mkv *.mov *.flv *.wmv *.webm *.m4v *.mpg *.mpeg);;所有文件 (*.*)",
        )
        self.add_paths([Path(file) for file in files])

    def pick_output_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if directory:
            self.output_input.setText(directory)

    def add_paths(self, paths: list[Path]) -> None:
        added_any = False
        for path in paths:
            if path.suffix.lower() not in VIDEO_EXTENSIONS or path in self.metas:
                continue
            added_any = True
            item = QListWidgetItem(f"{path.name}    分析中...")
            item.setData(Qt.UserRole, str(path))
            self.source_list.addItem(item)
            self._log(f"已添加素材: {path}")
            self._probe(path)
        if added_any:
            self.output_input.clear()
        self._sync_start_state()

    def _probe(self, path: Path) -> None:
        thread = ProbeThread(path)
        thread.finished_probe.connect(self._probe_done)
        thread.finished.connect(lambda t=thread: self._remove_probe_thread(t))
        self.probe_threads.append(thread)
        thread.start()

    def _remove_probe_thread(self, thread: ProbeThread) -> None:
        if thread in self.probe_threads:
            self.probe_threads.remove(thread)

    def _probe_done(self, path_text: str, meta: VideoMeta | None) -> None:
        path = Path(path_text)
        if not meta:
            self._update_source_row(path, f"{path.name}    分析失败")
            self._log(f"分析失败: {path}")
            return
        self.metas[path] = meta
        size = path.stat().st_size if path.exists() else 0
        text = f"{path.name}    {meta.width}x{meta.height}    {duration_text(meta.duration)}    {size_text(size)}"
        self._update_source_row(path, text)
        self._log(f"分析完成: {path.name} ({meta.width}x{meta.height})")
        if len(self.metas) == 1:
            self.preset_combo.setCurrentText(MediaProbe.suggest_preset(meta).label)
            if meta.bitrate:
                self.bitrate_spin.setValue(max(1.0, min(30.0, round(meta.bitrate / 1_000_000, 1))))
        self._sync_start_state()

    def _update_source_row(self, path: Path, text: str) -> None:
        for index in range(self.source_list.count()):
            item = self.source_list.item(index)
            if Path(item.data(Qt.UserRole)) == path:
                item.setText(text)
                break

    def apply_ai_preset(self) -> None:
        orientation = self._current_material_orientation()
        preset_label = "720p 竖版" if orientation == VideoOrientation.PORTRAIT else "720p 横版"
        self.preset_combo.setCurrentText(preset_label)
        self.rate_combo.setCurrentIndex(1)
        self.bitrate_spin.setValue(5.0)
        self.suffix_input.setText("_AI适配版")
        self.clip_check.setChecked(True)
        self.start_spin.setValue(0.0)
        self.end_spin.setValue(15.0)
        self._log("已应用一键适配 AI 导入格式：720p、CBR 5.0 Mbps、后缀 _AI适配版、截取 0-15 秒")

    def _current_material_orientation(self) -> VideoOrientation:
        if self.metas:
            return next(iter(self.metas.values())).orientation
        current = next(preset for preset in PRESETS if preset.label == self.preset_combo.currentText())
        return current.orientation

    def active_profile(self) -> RenderProfile:
        preset = next(preset for preset in PRESETS if preset.label == self.preset_combo.currentText())
        rate = RateControl.CBR if self.rate_combo.currentIndex() == 1 else RateControl.CRF
        output = Path(self.output_input.text()) if self.output_input.text().strip() else None
        start = self.start_spin.value() if self.clip_check.isChecked() else None
        end = self.end_spin.value() if self.clip_check.isChecked() and self.end_spin.value() > 0 else None
        return RenderProfile(
            preset=preset,
            rate_control=rate,
            bitrate_mbps=self.bitrate_spin.value(),
            crf=self.crf_spin.value(),
            start_second=start,
            end_second=end,
            output_dir=output,
            suffix=self.suffix_input.text().strip() or "new",
            include_audio=self.audio_check.isChecked(),
        )

    def start_render(self) -> None:
        if self.running:
            return
        metas = list(self.metas.values())
        if not metas:
            return
        profile = self.active_profile()
        if (
            profile.start_second is not None
            and profile.end_second is not None
            and profile.start_second >= profile.end_second
        ):
            QMessageBox.warning(self, "参数错误", "开始秒必须小于结束秒")
            return
        if profile.output_dir:
            profile.output_dir.mkdir(parents=True, exist_ok=True)
        self.settings.save(
            {
                "preset": profile.preset.label,
                "rate_control": profile.rate_control.value,
                "bitrate_mbps": profile.bitrate_mbps,
                "crf": profile.crf,
                "suffix": profile.suffix,
                "include_audio": profile.include_audio,
                "theme": self.theme_preference,
            }
        )
        planned = JobPlanner().plan(metas, profile)
        self.jobs = {job.id: job for job in planned}
        self.queue_list.clear()
        self.total_progress.setValue(0)
        for job in planned:
            job.state = JobState.QUEUED
            self._add_job_row(job)
        self.running = True
        self._sync_start_state()
        self._log(f"开始重构，共 {len(planned)} 个任务")
        self._pump_queue()

    def _add_job_row(self, job: RenderJob) -> None:
        item = QListWidgetItem(self._job_text(job))
        item.setData(Qt.UserRole, job.id)
        self.queue_list.addItem(item)
        self._sync_queue_summary()

    def _pump_queue(self) -> None:
        if not self.running:
            return
        while len(self.workers) < 4:
            queued = next((job for job in self.jobs.values() if job.state == JobState.QUEUED), None)
            if not queued:
                break
            self._start_job(queued)
        if self.jobs and all(job.state.finished for job in self.jobs.values()) and not self.workers:
            self._finish_batch()

    def _start_job(self, job: RenderJob) -> None:
        job.state = JobState.RUNNING
        self._refresh_job(job)
        worker = EncodeThread(job)
        worker.progress.connect(self._job_progress)
        worker.finished_encode.connect(self._job_done)
        worker.finished.connect(lambda job_id=job.id: self._worker_done(job_id))
        self.workers[job.id] = worker
        worker.start()
        self._log(f"正在处理: {job.source.name}")

    def _job_progress(self, job_id: str, value: float) -> None:
        job = self.jobs.get(job_id)
        if job is None:
            return
        job.progress = value
        self._refresh_job(job)
        self._update_total_progress()

    def _job_done(self, job_id: str, ok: bool, message: str) -> None:
        job = self.jobs.get(job_id)
        if job is None:
            return
        job.state = JobState.DONE if ok else (JobState.CANCELLED if message == "用户已取消" else JobState.FAILED)
        job.message = message
        job.progress = 100.0 if ok else job.progress
        self._refresh_job(job)
        self._log(f"{'完成' if ok else '失败'}: {job.source.name} - {message}")
        if ok:
            self._log(f"输出 MD5: {md5_file(job.target) or '读取失败'}")

    def _worker_done(self, job_id: str) -> None:
        self.workers.pop(job_id, None)
        QTimer.singleShot(50, self._pump_queue)

    def _refresh_job(self, job: RenderJob) -> None:
        for index in range(self.queue_list.count()):
            item = self.queue_list.item(index)
            if item.data(Qt.UserRole) == job.id:
                item.setText(self._job_text(job))
                break

    def _job_text(self, job: RenderJob) -> str:
        state = {
            JobState.READY: "就绪",
            JobState.QUEUED: "排队",
            JobState.RUNNING: "处理",
            JobState.DONE: "完成",
            JobState.FAILED: "失败",
            JobState.CANCELLED: "取消",
        }[job.state]
        return f"{state:>4}  {job.progress:>5.1f}%  {job.source.name}  ->  {job.target.name}"

    def _update_total_progress(self) -> None:
        if not self.jobs:
            self.total_progress.setValue(0)
            return
        value = sum(job.progress for job in self.jobs.values()) / len(self.jobs)
        self.total_progress.setValue(int(value))

    def _finish_batch(self) -> None:
        self.running = False
        self._sync_start_state()
        failed = [job for job in self.jobs.values() if job.state == JobState.FAILED]
        self._log(f"全部任务结束，失败 {len(failed)} 个")
        QMessageBox.information(self, "重构完成", f"任务已完成，失败 {len(failed)} 个")

    def cancel_all(self) -> None:
        for worker in list(self.workers.values()):
            worker.cancel()
        for job in self.jobs.values():
            if job.state in {JobState.QUEUED, JobState.RUNNING}:
                job.state = JobState.CANCELLED
                job.message = "用户已取消"
                self._refresh_job(job)
        self.running = False
        self._sync_start_state()
        self._log("已取消当前任务")

    def _wait_for_workers(self, timeout_ms: int = 4000) -> None:
        """Wait for encoder threads to stop so QThread objects can be destroyed safely."""
        workers = list(self.workers.values())
        if not workers:
            return
        deadline = time.monotonic() + timeout_ms / 1000.0
        for worker in workers:
            remaining_ms = max(0, int((deadline - time.monotonic()) * 1000))
            worker.wait(remaining_ms)
        self.workers.clear()

    def clear_all(self) -> None:
        if self.running:
            self.cancel_all()
        self._wait_for_workers()
        self.metas.clear()
        self.jobs.clear()
        self.source_list.clear()
        self.queue_list.clear()
        self.log_view.clear()
        self.total_progress.setValue(0)
        self._sync_start_state()
        self._sync_queue_summary()

    def toggle_theme(self) -> None:
        self.theme = "light" if self.theme == "dark" else "dark"
        self.theme_preference = self.theme
        self._apply_theme(save=True)

    def _apply_theme(self, save: bool) -> None:
        self.setStyleSheet(build_app_style(self.theme))
        if hasattr(self, "theme_btn"):
            self.theme_btn.setText(self._theme_button_text())
        if save:
            self.settings.save({"theme": self.theme_preference})

    def _resolve_theme(self, preference: str) -> str:
        if preference in {"light", "dark"}:
            return preference
        palette = QApplication.palette()
        window_color = palette.color(QPalette.ColorRole.Window)
        return "dark" if window_color.lightness() < 128 else "light"

    def _theme_button_text(self) -> str:
        return "浅色主题" if self.theme == "light" else "深色主题"

    def _sync_start_state(self) -> None:
        self._sync_action_button()

    def _on_action_clicked(self) -> None:
        if self.running:
            self.cancel_all()
        else:
            self.start_render()

    def _sync_action_button(self) -> None:
        if self.running:
            self.action_btn.setText("取消任务")
            self.action_btn.setObjectName("Danger")
            self.action_btn.setEnabled(True)
        else:
            self.action_btn.setText("开始重构")
            self.action_btn.setObjectName("Primary")
            self.action_btn.setEnabled(bool(self.metas))
        self.action_btn.style().unpolish(self.action_btn)
        self.action_btn.style().polish(self.action_btn)
        self.action_btn.update()

    def _sync_queue_summary(self) -> None:
        self.queue_summary.setText(f"{self.queue_list.count()} 个任务")

    def _log(self, text: str) -> None:
        logger.info(text)
        self.log_view.append(text)

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802
        self.add_paths([Path(url.toLocalFile()) for url in event.mimeData().urls() if url.toLocalFile()])
        event.acceptProposedAction()

    def closeEvent(self, event) -> None:  # noqa: N802
        if self.running:
            self.cancel_all()
        self._wait_for_workers()
        event.accept()
