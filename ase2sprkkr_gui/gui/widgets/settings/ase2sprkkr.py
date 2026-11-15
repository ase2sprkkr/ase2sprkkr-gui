"""Editor for ase2sprkkr's shared (non-GUI) user configuration."""
from __future__ import annotations

import re
from typing import Any

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from ase2sprkkr import config
from ase2sprkkr.common.configuration_transaction import ConfigurationTransaction
from ase2sprkkr.common.output_printing import (
    normalize_output_filter,
    output_filter_from_gui as output_filter_value,
)


def output_filter_selection(value: Any) -> tuple[str, str] | None:
    """Project core ase2sprkkr output normalization onto the four GUI modes."""
    try:
        normalized = normalize_output_filter(value)
        if normalized.listeners:
            return None
        return normalized.mode, normalized.regex_text
    except (TypeError, ValueError, re.error):
        return None


class Ase2sprkkrSettingsPage(QFrame):
    """Stage global ase2sprkkr settings without changing GUI preferences."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        configuration: Any | None = None,
    ) -> None:
        super().__init__(parent)
        self._config = config if configuration is None else configuration
        self._original_empty = self._config.running.empty_spheres()
        self._original_output = self._config.running.print_output()
        self._original_token = self._config.nomad.token()

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        heading = QLabel("Ase2sprkkr configuration", self)
        font = heading.font()
        font.setPointSize(font.pointSize() + 3)
        font.setBold(True)
        heading.setFont(font)
        layout.addWidget(heading)

        self.scope_notice = QLabel(
            "<b>These are ase2sprkkr library settings, not GUI-specific "
            "preferences.</b> They affect ase2sprkkr Python scripts and the "
            "<code>ase2sprkkr</code> command-line interface as well as "
            "calculations launched from the GUI. GUI-only preferences are "
            "on the General tab.",
            self,
        )
        self.scope_notice.setWordWrap(True)
        layout.addWidget(self.scope_notice)

        running_group = QGroupBox("Calculation defaults", self)
        running_form = QFormLayout(running_group)

        self.empty_spheres = QComboBox(running_group)
        self.empty_spheres.addItem("Automatic (recommended)", "auto")
        self.empty_spheres.addItem("Always", True)
        self.empty_spheres.addItem("Never", False)
        self.empty_spheres.setCurrentIndex(
            self.empty_spheres.findData(self._original_empty)
        )
        self.empty_spheres.setToolTip(
            "Default for finding empty spheres before SPR-KKR calculations. "
            "A calculation may override this setting."
        )
        running_form.addRow("Empty spheres:", self.empty_spheres)

        self.output_mode = QComboBox(running_group)
        self.output_mode.addItem("All", "all")
        self.output_mode.addItem("Info+Regex", "info_regex")
        self.output_mode.addItem("Regex", "regex")
        self.output_mode.addItem("None", "none")

        self.output_filter = QLineEdit(running_group)
        self.output_filter.setPlaceholderText("e.g. ERROR|WARNING")
        self.output_filter.setToolTip(
            'One regex (ERROR|WARNING) or multiple separate regexes '
            '("ERROR"|"WARNING"). Double quotes inside quoted patterns.'
        )
        self.regex_label = QLabel("Regex:", running_group)
        self.regex_hint = QLabel(
            "Info+Regex also displays the SCF iteration summary. "
            "Leave the regex empty for the summary alone.",
            running_group,
        )
        self.regex_hint.setWordWrap(True)

        selected = output_filter_selection(self._original_output)
        if selected is None:
            # The editor deliberately supports four common modes only. Do
            # not rewrite an unsupported configuration on an unrelated Save.
            mode, regex = "none", ""
        else:
            mode, regex = selected
        self.output_filter.setText(regex)
        self._output_edited = False
        self.output_mode.setCurrentIndex(self.output_mode.findData(mode))
        running_form.addRow("Program output:", self.output_mode)
        running_form.addRow(self.regex_label, self.output_filter)
        running_form.addRow("", self.regex_hint)
        self.output_mode.currentIndexChanged.connect(self._output_mode_changed)
        self.output_filter.textChanged.connect(self._regex_edited)
        self._update_output_mode()
        self.output_compatibility_note = QLabel(running_group)
        self.output_compatibility_note.setWordWrap(True)
        self.output_compatibility_note.setText(
            "The existing output configuration cannot be represented by the "
            "four modes. It will be preserved unless you choose a new mode."
        )
        self.output_compatibility_note.setVisible(selected is None)
        running_form.addRow("", self.output_compatibility_note)

        layout.addWidget(running_group)

        nomad_group = QGroupBox("NOMAD", self)
        nomad_form = QFormLayout(nomad_group)
        self.nomad_token = QLineEdit(nomad_group)
        self.nomad_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.nomad_token.setPlaceholderText(
            "Configured — leave blank to keep" if self._original_token
            else "Enter an authentication token"
        )
        self.nomad_token.setToolTip(
            "The token is stored in ase2sprkkr's user configuration, "
            "not in the GUI settings."
        )
        self.remove_token = QCheckBox("Remove configured token", nomad_group)
        self.remove_token.setEnabled(self._original_token is not None)
        self.remove_token.toggled.connect(
            lambda checked: self.nomad_token.setEnabled(not checked)
        )
        nomad_form.addRow("Authentication token:", self.nomad_token)
        nomad_form.addRow("", self.remove_token)
        layout.addWidget(nomad_group)
        layout.addStretch(1)

    def _output_mode_changed(self, _index: int) -> None:
        self._output_edited = True
        self.output_compatibility_note.setVisible(False)
        self._update_output_mode()

    def _regex_edited(self, _text: str) -> None:
        self._output_edited = True
        self.output_compatibility_note.setVisible(False)

    def _update_output_mode(self) -> None:
        mode = self.output_mode.currentData()
        needs_regex = mode in ("info_regex", "regex")
        self.regex_label.setVisible(needs_regex)
        self.output_filter.setVisible(needs_regex)
        self.regex_hint.setVisible(needs_regex)
        if mode == "regex":
            self.regex_hint.setText(
                'Only matching lines are displayed. Multiple separate '
                'regexes: "ERROR"|"WARNING".'
            )
        elif mode == "info_regex":
            self.regex_hint.setText(
                "Show SCF iteration summaries plus matching lines. "
                'Leave empty for the summary alone; multiple regexes: '
                '"ERROR"|"WARNING".'
            )

    def changes(self) -> list[tuple[Any, Any]]:
        """Validate the draft and return only actual changes."""
        out = []
        empty = self.empty_spheres.currentData()
        if empty != self._original_empty:
            out.append((self._config.running.empty_spheres, empty))

        # Parsing may normalize an existing multi-regex value for display.
        # Preserve the original representation until the user edits the mode
        # or regex text.
        if self._output_edited:
            output = output_filter_value(
                self.output_mode.currentData(), self.output_filter.text()
            )
            if output != self._original_output:
                out.append((self._config.running.print_output, output))

        if self.remove_token.isChecked():
            if self._original_token is not None:
                out.append((self._config.nomad.token, None))
        elif self.nomad_token.text():
            token = self.nomad_token.text().strip()
            if not token:
                raise ValueError("NOMAD token cannot consist only of whitespace.")
            if token != self._original_token:
                out.append((self._config.nomad.token, token))
        return out

    def save(self) -> None:
        """Save through ase2sprkkr, rolling back staged values on I/O failure."""
        changes = self.changes()
        if not changes:
            return
        with ConfigurationTransaction.use(self._config):
            for option, value in changes:
                option.set(value)
            self._config.save_user_preferences()

        self._original_empty = self._config.running.empty_spheres()
        self._original_output = self._config.running.print_output()
        self._output_edited = False
        self._original_token = self._config.nomad.token()
        self.nomad_token.clear()
        self.remove_token.setChecked(False)
        self.remove_token.setEnabled(self._original_token is not None)
        self.nomad_token.setPlaceholderText(
            "Configured — leave blank to keep" if self._original_token
            else "Enter an authentication token"
        )
