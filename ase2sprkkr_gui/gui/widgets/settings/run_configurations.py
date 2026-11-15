"""Run configuration settings page built from the existing profile editor."""
from __future__ import annotations

from copy import deepcopy

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ase2sprkkr_gui.gui.application.execution_profiles import (
    ExecutionProfileEditor,
    ExecutionProfileStore,
    draft_kind,
    kind_label,
)
from ase2sprkkr_gui.gui.widgets.execution_profiles import ProfileForm


class RunConfigurationsPage(QFrame):
    """Editable profile list and fields embedded in the Settings dialog."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        store: ExecutionProfileStore | None = None,
    ) -> None:
        super().__init__(parent)
        self._store = store or ExecutionProfileStore()
        self._editor = ExecutionProfileEditor(self._store)
        self._drafts = self._editor.drafts
        self._original_drafts = self._draft_snapshot()
        self._original_default = self._editor.default_profile
        self._loaded_values = None

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(12)

        heading = QLabel("Execution profiles", self)
        heading_font = heading.font()
        heading_font.setPointSize(heading_font.pointSize() + 3)
        heading_font.setBold(True)
        heading.setFont(heading_font)
        root.addWidget(heading)
        intro = QLabel(
            "Profiles define where SPR-KKR runs and how executables, MPI and remote workspaces are configured.",
            self,
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.setChildrenCollapsible(False)
        root.addWidget(splitter, 1)

        left = QWidget(splitter)
        left.setMinimumWidth(230)
        left.setMaximumWidth(330)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.setSpacing(8)
        list_heading = QLabel("Profiles", left)
        list_font = list_heading.font()
        list_font.setBold(True)
        list_heading.setFont(list_font)
        left_layout.addWidget(list_heading)
        self.list = QListWidget(left)
        self.list.setAlternatingRowColors(True)
        self.list.currentItemChanged.connect(self._selection_changed)
        left_layout.addWidget(self.list, 1)
        row = QHBoxLayout()
        self.add_button = QPushButton("New…", left)
        self.delete_button = QPushButton("Delete", left)
        self.add_button.clicked.connect(self._add_profile)
        self.delete_button.clicked.connect(self._delete_profile)
        row.addWidget(self.add_button)
        row.addWidget(self.delete_button)
        left_layout.addLayout(row)

        self.default_status = QLabel(left)
        self.default_status.setWordWrap(True)
        left_layout.addWidget(self.default_status)
        default_actions = QHBoxLayout()
        self.make_default_button = QPushButton("Make default", left)
        self.make_default_button.setToolTip(
            "Use this profile when a calculation does not select one explicitly."
        )
        self.make_default_button.clicked.connect(self._make_default)
        self.automatic_default_button = QPushButton("Use automatic", left)
        self.automatic_default_button.setToolTip(
            "Clear the explicit default and use ASE / legacy profile fallback."
        )
        self.automatic_default_button.clicked.connect(self._use_automatic_default)
        default_actions.addWidget(self.make_default_button)
        default_actions.addWidget(self.automatic_default_button)
        left_layout.addLayout(default_actions)
        splitter.addWidget(left)

        self.form = ProfileForm(splitter)
        splitter.addWidget(self.form)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([260, 700])

        self._reload_list()

    def _draft_snapshot(self):
        """Compare persisted draft values independently of the editor widgets."""
        return {
            name: (draft.read_only, deepcopy(draft.values))
            for name, draft in self._drafts.items()
        }

    def _store_current(self) -> None:
        item = self.list.currentItem()
        if item is None:
            return
        name = str(item.data(Qt.ItemDataRole.UserRole))
        draft = self._drafts[name]
        if not draft.read_only:
            values = self.form.values()
            if values != self._loaded_values:
                draft.values = values

    def _reload_list(self, select: str | None = None) -> None:
        current = select
        if current is None and self.list.currentItem() is not None:
            current = str(self.list.currentItem().data(Qt.ItemDataRole.UserRole))
        # Mark the explicitly chosen profile. If the default is automatic,
        # show the currently resolved ASE/legacy fallback when available.
        explicit = self._editor.default_profile
        implicit = (
            self._store.resolved_name(None)
            if explicit is None and self._original_default is None
            else None
        )
        marked = explicit if explicit is not None else implicit
        self.list.blockSignals(True)
        self.list.clear()
        for name in sorted(self._drafts):
            draft = self._drafts[name]
            kind = kind_label(draft_kind(draft.values))
            suffix = " · read-only" if draft.read_only else ""
            if name == marked:
                kind += " · default" if explicit is not None else " · automatic default"
            item = QListWidgetItem(f"{'★ ' if name == marked else ''}{name}\n{kind}{suffix}")
            if name == marked:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                item.setToolTip(
                    "Explicit default profile" if explicit is not None
                    else "Current automatic fallback profile"
                )
            item.setData(Qt.ItemDataRole.UserRole, name)
            self.list.addItem(item)
            if name == current:
                self.list.setCurrentItem(item)
        self.list.blockSignals(False)
        if self.list.currentItem() is None and self.list.count():
            self.list.setCurrentRow(0)
        else:
            self._selection_changed(self.list.currentItem(), None)
        if explicit is None:
            self.default_status.setText(
                "Default: Automatic (ASE / legacy fallback)"
            )
        else:
            self.default_status.setText(f"Default: {explicit}")

    def _selection_changed(
        self,
        current: QListWidgetItem | None,
        previous: QListWidgetItem | None,
    ) -> None:
        if previous is not None:
            name = str(previous.data(Qt.ItemDataRole.UserRole))
            draft = self._drafts.get(name)
            if draft is not None and not draft.read_only:
                values = self.form.values()
                if values != self._loaded_values:
                    draft.values = values
        if current is None:
            self._loaded_values = None
            self.form.setEnabled(False)
            self.delete_button.setEnabled(False)
            self.make_default_button.setEnabled(False)
            self.automatic_default_button.setEnabled(
                self._editor.default_profile is not None
            )
            return
        name = str(current.data(Qt.ItemDataRole.UserRole))
        draft = self._drafts[name]
        self.form.setEnabled(True)
        self.form.title.setText(name)
        self.form.load(draft)
        self._loaded_values = self.form.values()
        self.delete_button.setEnabled(not draft.read_only)
        self.make_default_button.setEnabled(
            name != self._editor.default_profile
        )
        self.automatic_default_button.setEnabled(
            self._editor.default_profile is not None
        )

    def _make_default(self) -> None:
        item = self.list.currentItem()
        if item is None:
            return
        self._store_current()
        name = str(item.data(Qt.ItemDataRole.UserRole))
        self._editor.set_default(name)
        self._reload_list(name)

    def _use_automatic_default(self) -> None:
        self._store_current()
        self._editor.set_default(None)
        self._reload_list()

    def _add_profile(self) -> None:
        self._store_current()
        name, ok = QInputDialog.getText(self, "New Execution Profile", "Profile name:")
        if not ok:
            return
        try:
            draft = self._editor.add(name)
        except ValueError as exc:
            QMessageBox.warning(self, "Profile Name", str(exc))
            return
        self._reload_list(draft.name)

    def _delete_profile(self) -> None:
        item = self.list.currentItem()
        if item is None:
            return
        name = str(item.data(Qt.ItemDataRole.UserRole))
        self._editor.delete(name)
        self._reload_list()

    def save(self) -> None:
        """Persist edits when the owning settings dialog is accepted."""
        self._store_current()
        if (self._draft_snapshot() != self._original_drafts
                or self._editor.default_profile != self._original_default):
            self._editor.save()


