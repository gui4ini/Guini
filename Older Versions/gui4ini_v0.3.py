import sys
import configparser
import pathlib
import re
from datetime import datetime
from PySide6.QtCore import QProcess, Signal
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QFormLayout,
    QLineEdit,
    QCheckBox,
    QStatusBar,
    QTextEdit,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtGui import QPalette, QColor, QIntValidator, QDoubleValidator, QAction


class OutputWindow(QWidget):
    """A simple window to hold the detached output widget."""
    # Signal to be emitted when the window is closed by the user
    window_closed = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Detached Output")
        self.setLayout(QVBoxLayout())
        self.resize(600, 400)
        self.setMinimumSize(400, 200)

    def closeEvent(self, event):
        # Emit the signal and then accept the event to allow the window to close
        self.window_closed.emit()
        super().closeEvent(event)


class MainWindow(QMainWindow):
    """
    Our main application window.
    We inherit from QMainWindow to get all the standard window features.
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("INI Script Runner v0.3")
        self.setMinimumSize(600, 500)

        # --- State Tracking ---
        self.is_dirty = False  # To track unsaved changes

        # This dictionary will hold our editor widgets for later access
        self.editors = {}
        self.detached_window = None
        self.process_start_time = None
        self.main_window_size_before_detach = None
        # --- Menu Bar ---
        file_menu = self.menuBar().addMenu("&File")
        self.open_action = QAction("&Open INI File...", self)
        self.open_action.setToolTip("Open a different INI configuration file.")
        self.open_action.triggered.connect(self._prompt_open_file)
        self.save_action = QAction("&Save Changes", self)
        self.save_action.setToolTip("Save the current configuration values to the INI file.")
        self.save_action.triggered.connect(self.save_config)
        self.save_output_action = QAction("Save &Output As...", self)
        self.save_output_action.setToolTip("Save the contents of the output window to a text file.")
        self.save_output_action.triggered.connect(self.save_output)
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_output_action)

        edit_menu = self.menuBar().addMenu("&Edit")
        self.clear_output_action = QAction("&Clear Output", self)
        self.clear_output_action.setToolTip("Clear all text from the output window.")
        self.clear_output_action.triggered.connect(self.clear_output)
        edit_menu.addAction(self.clear_output_action)

        view_menu = self.menuBar().addMenu("&View")
        self.detach_action = QAction("&Detach Output", self)
        self.detach_action.setToolTip("Move the output window to a separate, floating window.")
        self.detach_action.setCheckable(True)
        self.detach_action.triggered.connect(self.toggle_detach_output)
        view_menu.addAction(self.detach_action)

        # Dynamically determine the config file path based on the script's name
        script_path = pathlib.Path(__file__).resolve()
        self.script_dir = script_path.parent
        self.config_file = script_path.with_suffix(".ini")
        self.config = configparser.ConfigParser()

        # Main layout and the container widget
        self.main_layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

        # Use a QFormLayout for a nice key-value display
        self.form_layout = QFormLayout()
        self.main_layout.addLayout(self.form_layout)

        # Add a status bar for feedback *before* we might use it
        self.setStatusBar(QStatusBar(self))

        # --- Button Layout ---
        button_layout = QHBoxLayout()
        self.run_button = QPushButton("Run")
        self.run_button.setToolTip("Execute the script with the current INI settings.")
        self.run_button.clicked.connect(self.run_script)
        self.stop_button = QPushButton("Stop")
        self.stop_button.setToolTip("Terminate the currently running script.")
        self.stop_button.clicked.connect(self.stop_script)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.stop_button)
        self.main_layout.addLayout(button_layout)

        # --- Output Area ---
        # Create the output widget itself
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)

        # Create a container to hold it in the main window
        self.output_container = QWidget()
        self.output_container_layout = QVBoxLayout(self.output_container)
        self.output_container_layout.setContentsMargins(0, 0, 0, 0)
        self.output_container_layout.addWidget(QLabel("Output:"))
        self.output_container_layout.addWidget(self.output_area)
        self.main_layout.addWidget(self.output_container)

        # --- QProcess Setup ---
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)

        # Initial load of the default config file
        self._load_and_build_ui(self.config_file)

    def closeEvent(self, event):
        """Override the close event to check for unsaved changes."""
        if not self._prompt_to_save_if_dirty():
            event.ignore()  # User cancelled the close operation
            return
        event.accept()

    def _set_dirty(self, is_dirty: bool):
        """Sets the dirty status and updates the window title accordingly."""
        if self.is_dirty == is_dirty:
            return  # No change

        self.is_dirty = is_dirty
        title = self.windowTitle()
        if is_dirty and not title.endswith("*"):
            self.setWindowTitle(title + "*")
        elif not is_dirty and title.endswith("*"):
            self.setWindowTitle(title[:-1])

    def _prompt_to_save_if_dirty(self) -> bool:
        """Checks for unsaved changes and prompts the user. Returns False if action is cancelled."""
        if not self.is_dirty:
            return True  # Nothing to do, proceed
        reply = QMessageBox.question(self, "Unsaved Changes",
                                     "You have unsaved changes. Do you want to save them?",
                                     QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
        if reply == QMessageBox.StandardButton.Save:
            self.save_config()
        elif reply == QMessageBox.StandardButton.Cancel:
            return False
        return True

    def _set_ui_for_running_state(self, is_running: bool):
        """Enables/disables UI elements based on process state."""
        self.run_button.setEnabled(not is_running)
        self.stop_button.setEnabled(is_running)
        self.open_action.setEnabled(not is_running)
        self.save_action.setEnabled(not is_running)
        self.detach_action.setEnabled(not is_running)

    def stop_script(self):
        """Terminates the running QProcess."""
        if self.process.state() == QProcess.ProcessState.Running:
            self.process.terminate()
            self.statusBar().showMessage("Attempting to stop the process...", 3000)

    def _open_file_dialog(self, line_edit_widget: QLineEdit):
        """Opens a file dialog and sets the selected path in the provided QLineEdit."""
        # We use self.script_dir to give the dialog a sensible starting place
        file_path, _ = QFileDialog.getOpenFileName(self, "Select a File", str(self.script_dir))
        if file_path:
            line_edit_widget.setText(file_path)

    def _prompt_open_file(self):
        """Opens a dialog to select a new INI file and reloads the UI."""
        if not self._prompt_to_save_if_dirty():
            return # User cancelled

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open INI File", str(self.script_dir), "INI Files (*.ini);;All Files (*)"
        )
        if file_path:
            self._load_and_build_ui(pathlib.Path(file_path))

    def _clear_form_layout(self):
        """Removes all widgets from the form layout."""
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def _load_and_build_ui(self, file_path: pathlib.Path):
        """Clears the current UI and builds a new one from the given INI file."""
        self.config_file = file_path
        self.setWindowTitle(f"INI Script Runner - {self.config_file.name}")
        self._clear_form_layout()
        self.editors.clear()
        self._set_initial_output_info()
        # Add robust error handling for file loading
        if not self.config_file.exists():
            msg = f"Error: Configuration file not found at '{self.config_file}'"
            self.statusBar().showMessage(msg, 5000)
            self._log_message(f"\n{msg}", color="red")
            return

        self.config = configparser.ConfigParser()
        try:
            self.config.read(self.config_file, encoding='utf-8')
            self._log_message(f"Successfully loaded config: {self.config_file.name}", color="green")
        except configparser.Error as e:
            msg = f"Error parsing INI file: {e}"
            self.statusBar().showMessage(msg, 5000)
            self._log_message(f"\n{msg}", color="red")
            return

        sections_to_display = ['Command', 'Arguments']
        for section_name in sections_to_display:
            if self.config.has_section(section_name):
                section_label = QLabel(f"[{section_name}]")
                section_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
                self.form_layout.addRow(section_label)

                for key, value in self.config.items(section_name):
                    label_text = self.config.get('Labels', key, fallback=key)
                    clean_label, type_hint = self._parse_label(label_text)
                    editor, _ = self._create_editor_for_value(value, type_hint=type_hint)
                    label = QLabel(clean_label)
                    self.form_layout.addRow(label, editor)
                    self.editors[(section_name, key)] = editor

        # Final check to ensure the critical command section was loaded
        if not self.config.has_section('Command'):
            msg = "Error: INI file is missing the required [Command] section."
            self.statusBar().showMessage(msg, 5000)
            self._log_message(msg, color="red")

        # After loading, the state is clean
        self._set_dirty(False)

    def toggle_detach_output(self):
        """Detaches or attaches the output window."""
        if self.detached_window is None:  # It's attached, so we detach
            self.main_window_size_before_detach = self.size()
            self.detached_window = OutputWindow()
            self.detached_window.window_closed.connect(self.attach_output)

            # Move the output_area to the new window
            self.output_area.setParent(self.detached_window)
            self.detached_window.layout().addWidget(self.output_area)

            # Explicitly remove the container from the layout and reparent it
            self.output_container.hide()
            # Force the layout to recalculate its size hint
            self.main_layout.activate()

            # Temporarily remove the minimum height constraint to allow shrinking, then restore it.
            original_min_size = self.minimumSize()
            self.setMinimumSize(0, 0)
            self.adjustSize()
            self.setMinimumSize(original_min_size)

            self.detached_window.show()
            self.detach_action.setChecked(True)
        else:  # It's detached, so we attach
            # Closing the window will trigger the attach_output via the signal
            self.detached_window.close()

    def attach_output(self):
        """Re-attaches the output window to the main window."""
        if self.detached_window is None:
            return  # Nothing to do

        # Move the output area back to its container in the main window
        self.output_area.setParent(self.output_container)
        self.output_container_layout.addWidget(self.output_area)
        self.output_container.show()

        if self.main_window_size_before_detach:
            self.resize(self.main_window_size_before_detach)
            self.main_window_size_before_detach = None

        self.detach_action.setChecked(False)
        self.detached_window = None

    def clear_output(self):
        """Clears the output text area."""
        self._set_initial_output_info()
        self.statusBar().showMessage("Output cleared.", 3000)

    def _set_initial_output_info(self):
        """Clears the output and prints the initial session info."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        py_version = sys.version.split('\n')[0]

        self.output_area.clear()
        self._log_message(f"--- Session started at: {now} ---", bold=True)
        self._log_message(f"Python Version: {py_version}", color="blue")
        self._log_message(f"Executable: {sys.executable}", color="#666666")
        self._log_message("----------------------------------", bold=True)

    def _log_message(self, text: str, color: str = None, bold: bool = False):
        """Appends a message to the output area with optional styling."""
        if bold:
            text = f"<b>{text}</b>"
        if color:
            # Using a span with inline CSS is more modern than <font>
            # but <font> is simple and works perfectly here.
            text = f'<font color="{color}">{text}</font>'

        self.output_area.append(text)

    def save_output(self):
        """Saves the content of the output area to a text file."""
        if not self.output_area.toPlainText():
            self.statusBar().showMessage("Output is empty. Nothing to save.", 3000)
            return

        # Suggest a default filename and filter for text files
        default_path = self.script_dir / "output.txt"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Output As", str(default_path), "Text Files (*.txt);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.output_area.toPlainText())
                self.statusBar().showMessage(f"Output saved to {file_path}", 4000)
            except Exception as e:
                error_msg = f"Error saving file: {e}"
                self.statusBar().showMessage(error_msg, 5000)
                self._log_message(error_msg, color="red")

    def _parse_label(self, label_text: str) -> tuple[str, str | None]:
        """Parses a label string to extract a clean label and an optional type hint."""
        match = re.match(r'(.+?)\s*\((.+?)\)', label_text)
        if match:
            clean_label = match.group(1).strip()
            type_hint = match.group(2).strip().lower()
            return clean_label, type_hint
        return label_text, None

    def _create_editor_for_value(self, value: str, type_hint: str | None = None) -> tuple[QWidget, str]:
        """Creates the appropriate editor widget, prioritizing the type_hint if provided."""
        # Determine the type, using the hint if available, otherwise guess from the value
        final_type = type_hint
        if not final_type:
            if value.lower() in ['true', 'false']:
                final_type = 'boolean'
            else:
                try:
                    int(value)
                    final_type = 'integer'
                except ValueError:
                    try:
                        float(value)
                        final_type = 'float'
                    except ValueError:
                        final_type = 'string'

        # Create the widget based on the determined type
        if final_type == "boolean":
            editor = QCheckBox()
            editor.stateChanged.connect(lambda: self._set_dirty(True))
            editor.setChecked(value.lower() == 'true')
            return editor, "boolean"
        elif final_type == "integer":
            editor = QLineEdit(value)
            editor.textChanged.connect(lambda: self._set_dirty(True))
            editor.setValidator(QIntValidator())
            return editor, "integer"
        elif final_type == "float":
            editor = QLineEdit(value)
            editor.textChanged.connect(lambda: self._set_dirty(True))
            editor.setValidator(QDoubleValidator())
            return editor, "float"
        elif final_type == "filename":
            # Create a composite widget with a QLineEdit and a "Browse" button
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            line_edit = QLineEdit(value)
            line_edit.textChanged.connect(lambda: self._set_dirty(True))
            browse_button = QPushButton("...")
            browse_button.clicked.connect(lambda: self._open_file_dialog(line_edit))
            layout.addWidget(line_edit)
            layout.addWidget(browse_button)
            container.lineEdit = line_edit  # Store a reference for easy access
            return container, "filename"

        # Default to string for any other case (including unknown type hints)
        editor = QLineEdit(value)
        editor.textChanged.connect(lambda: self._set_dirty(True))
        return editor, "string"

    def save_config(self):
        """Iterate through the editors and save the values back to the config object."""
        for (section, key), editor in self.editors.items():
            value_to_save = ""
            if hasattr(editor, 'lineEdit'):  # Check for our composite file widget
                value_to_save = editor.lineEdit.text()
            elif isinstance(editor, QCheckBox):
                value_to_save = str(editor.isChecked()).lower()
            elif isinstance(editor, QLineEdit):
                value_to_save = editor.text()

            self.config.set(section, key, value_to_save)

        with open(self.config_file, "w") as configfile:
            self.config.write(configfile)

        self.statusBar().showMessage(f"Configuration saved to {self.config_file}", 3000)
        self._set_dirty(False)

    def run_script(self):
        """Read current values from the UI and execute the script."""
        if self.process.state() == QProcess.ProcessState.Running:
            self.statusBar().showMessage("A process is already running.", 3000)
            return

        # Add a timestamped separator for this run
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._log_message(f"\n--- Run at: {now} ---", bold=True)

        # Get the current values from the editor widgets
        ui_values = {}
        for (section, key), editor in self.editors.items():
            if hasattr(editor, 'lineEdit'):  # Check for our composite file widget
                ui_values[(section, key)] = editor.lineEdit.text()
            elif isinstance(editor, QCheckBox):
                ui_values[(section, key)] = str(editor.isChecked()).lower()
            elif isinstance(editor, QLineEdit):
                ui_values[(section, key)] = editor.text()

        # Find the script filename from the UI values
        script_filename = ui_values.get(('Command', 'script_file_name'))
        if not script_filename:
            self._log_message("Error: 'script_file_name' not found in the UI.", color="red")
            return

        script_path = self.script_dir / script_filename
        if not script_path.exists():
            self._log_message(f"Error: Script not found at '{script_path}'.", color="red")
            return

        # --- Collect and sort arguments numerically ---
        # Filter for keys like 'arg1', 'arg2', etc. that have a numeric part.
        argument_keys = [
            k for s, k in ui_values.keys()
            if s == 'Arguments' and k.startswith('arg') and k[3:].isdigit()
        ]
        # Sort keys based on the integer value of their numeric part.
        sorted_arg_keys = sorted(argument_keys, key=lambda k: int(k[3:]))
        # Build the final list of argument values in the correct order.
        args = [ui_values[('Arguments', key)] for key in sorted_arg_keys]

        # Display the command being run
        # Quote arguments with spaces for clarity
        quoted_args = [f'"{arg}"' if ' ' in arg else arg for arg in args]
        command_str = f"python \"{script_path}\" {' '.join(quoted_args)}"
        self._log_message(f"$ {command_str}\n", color="#666666")  # Use a dark gray for the command

        self.statusBar().showMessage(f"Running '{script_filename}'...")
        self._set_ui_for_running_state(True)

        self.process_start_time = datetime.now()
        self.process.start("python", [str(script_path)] + args)

    def handle_stdout(self):
        """Append standard output to the text area."""
        data = self.process.readAllStandardOutput()
        text = str(data, 'utf-8').strip()
        for line in text.splitlines():
            self._log_message(f"> {line}")

    def handle_stderr(self):
        """Append standard error to the text area."""
        data = self.process.readAllStandardError()
        error_text = str(data, 'utf-8').strip()
        for line in error_text.splitlines():
            self._log_message(f"! ERROR: {line}", color="red")

    def process_finished(self):
        """Called when the QProcess finishes."""
        if self.process_start_time:
            end_time = datetime.now()
            elapsed = end_time - self.process_start_time
            elapsed_str = f"{elapsed.total_seconds():.2f}s"
            self._log_message(
                f"\n\n--- Finished at: {end_time.strftime('%Y-%m-%d %H:%M:%S')} (Elapsed: {elapsed_str}) ---",
                bold=True
            )
            self.process_start_time = None

        exit_code = self.process.exitCode()
        exit_status = self.process.exitStatus()
        if exit_status == QProcess.ExitStatus.CrashExit:
            self.statusBar().showMessage("Process was terminated or crashed.", 4000)
        else:
            self.statusBar().showMessage(f"Process finished with exit code {exit_code}.", 4000)
        self._set_ui_for_running_state(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    light_palette = QPalette()
    light_palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
    light_palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
    light_palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    light_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(240, 240, 240))
    light_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
    light_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
    light_palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
    light_palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
    light_palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
    light_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    light_palette.setColor(QPalette.ColorRole.Link, QColor(0, 0, 255))
    light_palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
    light_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(light_palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
