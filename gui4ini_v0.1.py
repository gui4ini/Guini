import sys
import configparser
import pathlib
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
)
from PySide6.QtGui import QPalette, QColor, QIntValidator, QDoubleValidator


class MainWindow(QMainWindow):
    """
    Our main application window.
    We inherit from QMainWindow to get all the standard window features.
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("INI Script Runner v0.1")

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
        self.config.read(self.config_file)
        for section in self.config.sections():
            # Add a label for the section header
            section_label = QLabel(f"[{section}]")
            section_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            form_layout.addRow(section_label)

            for key, value in self.config.items(section):
                editor, guessed_type = self._create_editor_for_value(value)
                label = QLabel(f"{key} ({guessed_type})")
                form_layout.addRow(label, editor)
                self.editors[(section, key)] = editor

        # Add the form layout to the main layout
        main_layout.addLayout(form_layout)

        # --- Button Layout ---
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save Changes")
        save_button.clicked.connect(self.save_config)
        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.run_script)
        button_layout.addWidget(save_button)
        button_layout.addWidget(self.run_button)
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

    def _create_editor_for_value(self, value: str) -> tuple[QWidget, str]:
        """Creates the appropriate editor widget for a given string value and guesses its type."""
        if value.lower() in ['true', 'false']:
            editor = QCheckBox()
            editor.setChecked(value.lower() == 'true')
            return editor, "boolean"

        try:
            int(value)
            editor = QLineEdit(value)
            editor.setValidator(QIntValidator())
            return editor, "integer"
        except ValueError:
            try:
                float(value)
                editor = QLineEdit(value)
                editor.setValidator(QDoubleValidator())
                return editor, "float"
            except ValueError:
                editor = QLineEdit(value)
                return editor, "string"

    def save_config(self):
        """Iterate through the editors and save the values back to the config object."""
        for (section, key), editor in self.editors.items():
            value_to_save = ""
            if isinstance(editor, QCheckBox):
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

        self.output_area.clear()

        config_values = {}
        for (section, key), editor in self.editors.items():
            if isinstance(editor, QCheckBox):
                config_values[key] = str(editor.isChecked()).lower()
            elif isinstance(editor, QLineEdit):
                config_values[key] = editor.text()

        script_filename = config_values.get('filename')
        if not script_filename:
            self.output_area.setText("Error: No 'filename' key found in the configuration.")
            return

        script_path = self.script_dir / script_filename
        if not script_path.exists():
            self.output_area.setText(f"Error: Script not found at '{script_path}'.")
            return

        args = []
        for key in sorted(config_values.keys()):
            if key.startswith('arg'):
                args.append(config_values[key])

        self.statusBar().showMessage(f"Running '{script_filename}'...")
        self.run_button.setEnabled(False)

        self.process.start("python", [str(script_path)] + args)

    def handle_stdout(self):
        """Append standard output to the text area."""
        data = self.process.readAllStandardOutput()
        self.output_area.append(str(data, 'utf-8').strip())

    def handle_stderr(self):
        """Append standard error to the text area."""
        data = self.process.readAllStandardError()
        self.output_area.append(f"ERROR: {str(data, 'utf-8').strip()}")

    def process_finished(self):
        """Called when the QProcess finishes."""
        exit_code = self.process.exitCode()
        self.statusBar().showMessage(f"Process finished with exit code {exit_code}.", 4000)
        self.run_button.setEnabled(True)


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
