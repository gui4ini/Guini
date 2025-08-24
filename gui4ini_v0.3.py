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

        # --- Menu Bar ---
        file_menu = self.menuBar().addMenu("&File")
        open_action = QAction("&Open INI File...", self)
        open_action.triggered.connect(self._prompt_open_file)
        file_menu.addAction(open_action)

        # Dynamically determine the config file path based on the script's name
        script_path = pathlib.Path(__file__).resolve()
        self.script_dir = script_path.parent
        self.config_file = script_path.with_suffix(".ini")
        self.config = configparser.ConfigParser()

        # This dictionary will hold our editor widgets for later access
        self.editors = {}
        self.detached_window = None
        self.process_start_time = None

        # Main layout and the container widget
        main_layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Use a QFormLayout for a nice key-value display
        self.form_layout = QFormLayout()
        main_layout.addLayout(self.form_layout)

        # Add a status bar for feedback *before* we might use it
        self.setStatusBar(QStatusBar(self))

        # --- Button Layout ---
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self.save_config)
        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.run_script)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_script)
        self.stop_button.setEnabled(False)
        self.clear_button = QPushButton("Clear Output")
        self.clear_button.clicked.connect(self.clear_output)
        self.save_output_button = QPushButton("Save Output")
        self.save_output_button.clicked.connect(self.save_output)
        self.detach_button = QPushButton("Detach Output")
        self.detach_button.clicked.connect(self.toggle_detach_output)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.save_output_button)
        button_layout.addWidget(self.detach_button)
        main_layout.addLayout(button_layout)

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
        main_layout.addWidget(self.output_container)

        # --- QProcess Setup ---
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)

        # Initial load of the default config file
        self._load_and_build_ui(self.config_file)

    def _set_ui_for_running_state(self, is_running: bool):
        """Enables/disables UI elements based on process state."""
        self.run_button.setEnabled(not is_running)
        self.save_button.setEnabled(not is_running)
        self.stop_button.setEnabled(is_running)
        self.detach_button.setEnabled(not is_running)

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
        self.setWindowTitle(f"INI Script Runner v0.3 - {self.config_file.name}")
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

    def toggle_detach_output(self):
        """Detaches or attaches the output window."""
        if self.detached_window is None:  # It's attached, so we detach
            self.detached_window = OutputWindow()
            self.detached_window.window_closed.connect(self.attach_output)

            # Move the output_area to the new window
            self.output_area.setParent(self.detached_window)
            self.detached_window.layout().addWidget(self.output_area)

            self.output_container.hide()
            self.detached_window.show()
            self.detach_button.setText("Attach Output")
        else:  # It's detached, so we attach
            # Closing the window will trigger the attach_output via the signal
            self.detached_window.close()

    def attach_output(self):
        """Re-attaches the output window to the main window."""
        if self.detached_window is None:
            return  # Nothing to do

        self.output_area.setParent(self.output_container)
        self.output_container_layout.addWidget(self.output_area)
        self.output_container.show()
        self.detach_button.setText("Detach Output")
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
            editor.setChecked(value.lower() == 'true')
            return editor, "boolean"
        elif final_type == "integer":
            editor = QLineEdit(value)
            editor.setValidator(QIntValidator())
            return editor, "integer"
        elif final_type == "float":
            editor = QLineEdit(value)
            editor.setValidator(QDoubleValidator())
            return editor, "float"
        elif final_type == "filename":
            # Create a composite widget with a QLineEdit and a "Browse" button
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            line_edit = QLineEdit(value)
            browse_button = QPushButton("...")
            browse_button.clicked.connect(lambda: self._open_file_dialog(line_edit))
            layout.addWidget(line_edit)
            layout.addWidget(browse_button)
            container.lineEdit = line_edit  # Store a reference for easy access
            return container, "filename"

        # Default to string for any other case (including unknown type hints)
        editor = QLineEdit(value)
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

        # Collect arguments, sorted by key (arg1, arg2, etc.)
        args = []
        # Filter for keys in the 'Arguments' section and sort them
        arg_keys = sorted([k for s, k in ui_values.keys() if s == 'Arguments'])
        for key in arg_keys:
            if key.startswith('arg'):
                args.append(ui_values[('Arguments', key)])

        # Display the command being run
        # Quote arguments with spaces for clarity
        quoted_args = [f'"{arg}"' if ' ' in arg else arg for arg in args]
        command_str = f"python \"{script_path}\" {' '.join(quoted_args)}"
        self._log_message(f"$ {command_str}\n", color="#666666") # Use a dark gray for the command

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
