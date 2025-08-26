import sys
import configparser
import pathlib
import re
from PySide6.QtCore import QProcess
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
from PySide6.QtGui import QPalette, QColor, QIntValidator, QDoubleValidator


class MainWindow(QMainWindow):
    """
    Our main application window.
    We inherit from QMainWindow to get all the standard window features.
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("INI Script Runner v0.2")

        # Dynamically determine the config file path based on the script's name
        script_path = pathlib.Path(__file__).resolve()
        self.script_dir = script_path.parent
        self.config_file = script_path.with_suffix(".ini")
        self.config = configparser.ConfigParser()

        # This dictionary will hold our editor widgets for later access
        self.editors = {}

        # Main layout and the container widget
        main_layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Use a QFormLayout for a nice key-value display
        form_layout = QFormLayout()

        # Add a status bar for feedback *before* we might use it
        self.setStatusBar(QStatusBar(self))

        # Check if the file exists and show a warning if it doesn't
        if not self.config_file.exists():
            # Make the error message more specific for debugging
            msg = f"Warning: '{self.config_file.name}' not found. Check terminal for full path."
            self.statusBar().showMessage(msg, 8000)  # Show for 8 seconds
            print(f"DEBUG: The application is looking for the config file at this exact path:\n{self.config_file}")

        # Read the .ini file and create widgets
        self.config.read(self.config_file, encoding='utf-8')

        # Define which sections of the INI to display in the UI
        sections_to_display = ['Command', 'Arguments']
        for section_name in sections_to_display:
            if self.config.has_section(section_name):
                # Add a visual separator for the section
                section_label = QLabel(f"[{section_name}]")
                section_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
                form_layout.addRow(section_label)

                for key, value in self.config.items(section_name):
                    # Get custom label from [Labels] section and parse for a type hint
                    label_text = self.config.get('Labels', key, fallback=key)
                    clean_label, type_hint = self._parse_label(label_text)

                    editor, _ = self._create_editor_for_value(value, type_hint=type_hint)
                    label = QLabel(clean_label)
                    form_layout.addRow(label, editor)
                    # Store the editor widget with its section and key
                    self.editors[(section_name, key)] = editor

        # Add the form layout to the main layout
        main_layout.addLayout(form_layout)

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
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.save_output_button)
        main_layout.addLayout(button_layout)

        # --- Output Area ---
        main_layout.addWidget(QLabel("Output:"))
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        main_layout.addWidget(self.output_area)

        # --- QProcess Setup ---
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)

    def _set_ui_for_running_state(self, is_running: bool):
        """Enables/disables UI elements based on process state."""
        self.run_button.setEnabled(not is_running)
        self.save_button.setEnabled(not is_running)
        self.stop_button.setEnabled(is_running)

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

    def clear_output(self):
        """Clears the output text area."""
        self.output_area.clear()

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
                self.output_area.append(f'<font color="red">{error_msg}</font>')

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
            self.output_area.setHtml('<font color="red">Error: \'script_file_name\' not found in the UI.</font>')
            return

        script_path = self.script_dir / script_filename
        if not script_path.exists():
            self.output_area.setHtml(f'<font color="red">Error: Script not found at \'{script_path}\'.</font>')
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

        self.statusBar().showMessage(f"Running '{script_filename}'...")
        self._set_ui_for_running_state(True)

        self.process.start("python", [str(script_path)] + args)

    def handle_stdout(self):
        """Append standard output to the text area."""
        data = self.process.readAllStandardOutput()
        self.output_area.append(str(data, 'utf-8').strip())

    def handle_stderr(self):
        """Append standard error to the text area."""
        data = self.process.readAllStandardError()
        error_text = str(data, 'utf-8').strip()
        self.output_area.append(f'<font color="red">ERROR: {error_text}</font>')

    def process_finished(self):
        """Called when the QProcess finishes."""
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
