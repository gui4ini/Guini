import sys
import configparser
import pathlib
from configupdater import ConfigUpdater
import resources_rc  # Import the compiled resources # noqa
import re
from datetime import datetime
from PySide6.QtCore import QProcess, Qt, QUrl, QTimer

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
    QTabWidget,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QComboBox,
    QFrame,
    QSpinBox,
    QMessageBox,
)
from PySide6.QtGui import (  # noqa
    QPalette,
    QColor,
    QIntValidator,
    QDoubleValidator,
    QAction,
    QKeySequence,
    QCloseEvent,
    QIcon,
    QPixmap,
    QDesktopServices,
    QTextCursor,  # noqa
)

__version__ = "0.7.0"
APP_NAME = "Guini"


class FileNameWidget(QWidget):
    """A composite widget for a line edit and a browse button."""

    def __init__(self, initial_path: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.line_edit = QLineEdit(initial_path)
        self.browse_button = QPushButton("...")
        self.layout.addWidget(self.line_edit)
        self.layout.addWidget(self.browse_button)

        self.browse_button.clicked.connect(self._open_file_dialog)
        self._file_filter = "All Files (*)"
        self._start_dir = "."

    def set_dialog_options(self, file_filter: str, start_dir: str):
        """Sets the options for the file dialog."""
        self._file_filter = file_filter
        self._start_dir = start_dir

    def _open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select a File", self._start_dir, filter=self._file_filter
        )
        if file_path:
            self.line_edit.setText(file_path)

    def text(self) -> str:
        return self.line_edit.text()


class SettingsDialog(QDialog):
    """A dialog to configure application-wide settings."""

    def __init__(
        self,
        parent: QWidget | None = None,
        settings_parser: configparser.ConfigParser | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Application Settings")
        if settings_parser is None:
            self.settings = configparser.ConfigParser()
        else:
            self.settings = settings_parser

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # --- UI Settings ---
        ui_label = QLabel("User Interface")
        ui_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        form_layout.addRow(ui_label)

        self.multi_tab_checkbox = QCheckBox("Enable Multi-Tab Mode")
        self.multi_tab_checkbox.setToolTip(
            "Allows opening multiple script outputs in tabs.\nRequires application restart."
        )
        self.multi_tab_checkbox.setChecked(
            self.settings.getboolean(
                "Settings", "multi_tab_mode", fallback=False
            )
        )
        form_layout.addRow(self.multi_tab_checkbox)

        self.show_icons_checkbox = QCheckBox("Show icons on buttons and menus")
        self.show_icons_checkbox.setToolTip(
            "Toggles the visibility of icons on the toolbar and in menus."
        )
        self.show_icons_checkbox.setChecked(
            self.settings.getboolean("Settings", "show_icons", fallback=True)
        )
        form_layout.addRow(self.show_icons_checkbox)

        self.remember_size_checkbox = QCheckBox("Remember window size on exit")
        self.remember_size_checkbox.setChecked(
            self.settings.getboolean(
                "Settings", "remember_window_size", fallback=True
            )
        )
        form_layout.addRow(self.remember_size_checkbox)

        # --- Theme Settings ---
        theme_label = QLabel("Theme")
        theme_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        form_layout.addRow(theme_label)
        self.theme_combobox = QComboBox()
        self.theme_combobox.addItems(["System", "Light", "Dark"])
        self.theme_combobox.setToolTip(
            "Set the application color theme.\n'System' follows your OS setting."
        )
        self.theme_combobox.setCurrentText(
            self.settings.get("Settings", "theme", fallback="System").title()
        )
        form_layout.addRow("Color Theme:", self.theme_combobox)

        # --- Execution Settings ---
        execution_label = QLabel("Execution")
        execution_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        form_layout.addRow(execution_label)

        self.run_background_checkbox = QCheckBox(
            "Run scripts in the background (using pythonw)"
        )
        self.run_background_checkbox.setToolTip(
            "If checked, scripts will be launched with 'pythonw.exe', detaching them from the GUI.\nNo output will be captured."
        )
        self.run_background_checkbox.setChecked(
            self.settings.getboolean(
                "Settings", "run_in_background", fallback=False
            )
        )
        form_layout.addRow(self.run_background_checkbox)

        layout_label = QLabel("Layout")
        layout_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        form_layout.addRow(layout_label)

        self.columns_spinbox = QSpinBox()
        self.columns_spinbox.setMinimum(1)
        self.columns_spinbox.setMaximum(4)  # A reasonable maximum
        self.columns_spinbox.setToolTip(
            "Sets the number of columns for the arguments section.\nRequires re-opening the INI file."
        )
        self.columns_spinbox.setValue(
            self.settings.getint("Settings", "argument_columns", fallback=1)
        )
        form_layout.addRow("Argument Columns:", self.columns_spinbox)

        layout.addLayout(form_layout)

        # OK and Cancel buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def apply_settings(self):
        """Updates the settings ConfigParser object with values from the dialog."""
        self.settings.set(
            "Settings",
            "multi_tab_mode",
            str(self.multi_tab_checkbox.isChecked()).lower(),
        )
        self.settings.set(
            "Settings",
            "remember_window_size",
            str(self.remember_size_checkbox.isChecked()).lower(),
        )
        self.settings.set(
            "Settings",
            "show_icons",
            str(self.show_icons_checkbox.isChecked()).lower(),
        )
        self.settings.set(
            "Settings", "theme", self.theme_combobox.currentText().lower()
        )
        self.settings.set(
            "Settings",
            "run_in_background",
            str(self.run_background_checkbox.isChecked()).lower(),
        )
        self.settings.set(
            "Settings", "argument_columns", str(self.columns_spinbox.value())
        )


class MainWindow(QMainWindow):
    """
    Our main application window.
    We inherit from QMainWindow to get all the standard window features.
    """

    SETTINGS_SECTION = "Settings"

    def __init__(self):
        super().__init__()
        self.setWindowIcon(
            QIcon(":/logo/app_icon")
        )  # Use the dedicated icon for the window
        self.config_file: pathlib.Path | None = None
        self.new_tab_button: QPushButton | None = None

        # --- App Settings Handling ---
        self.script_dir = pathlib.Path(__file__).parent.resolve()
        self.settings_file = self.script_dir / "guini.ini"
        self.app_settings = configparser.ConfigParser()
        self._load_app_settings()  # This will create the file if it doesn't exist

        self.multi_tab_enabled = self.app_settings.getboolean(
            self.SETTINGS_SECTION, "multi_tab_mode", fallback=False
        )
        self.remember_window_size = self.app_settings.getboolean(
            self.SETTINGS_SECTION, "remember_window_size", fallback=True
        )
        self.run_in_background = self.app_settings.getboolean(
            self.SETTINGS_SECTION, "run_in_background", fallback=False
        )
        self.show_icons = self.app_settings.getboolean(
            self.SETTINGS_SECTION, "show_icons", fallback=True
        )
        self.theme = self.app_settings.get(
            self.SETTINGS_SECTION, "theme", fallback="System"
        ).lower()
        # --- End App Settings ---

        self.setWindowTitle(f"{APP_NAME} v{__version__}")

        if self.remember_window_size:
            width = self.app_settings.getint(
                "Settings", "window_width", fallback=600
            )
            height = self.app_settings.getint(
                "Settings", "window_height", fallback=500
            )
            self.resize(width, height)
        else:
            self.resize(600, 500)

        # --- State Tracking ---
        self.is_dirty = False  # To track unsaved changes

        self.editors = {}
        # Maps a QTextEdit widget in a tab to its running QProcess
        self.tab_process_map = {}
        # Counter to give new tabs unique names
        self.tab_counter = 0

        self._create_actions()
        self._create_menus()

        self.config = ConfigUpdater()

        # Main layout and the container widget
        self.main_layout = QVBoxLayout()
        self.central_widget = QWidget()
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)

        # Use a QGridLayout to allow for multiple columns
        # Create the banner frame early to ensure it exists before _apply_theme is called.
        self.banner_frame = QFrame()
        banner_layout = QHBoxLayout(self.banner_frame)
        banner_layout.setContentsMargins(5, 5, 5, 5)

        self.config_layout = QGridLayout()
        self.main_layout.addLayout(self.config_layout)

        # Add a status bar for feedback *before* we might use it
        self.setStatusBar(QStatusBar(self))

        # --- Button Layout ---
        # We create two rows of buttons to prevent the window from being too wide.
        button_layout_1 = QHBoxLayout()
        button_layout_2 = QHBoxLayout()

        # --- Row 1: INI File Operations ---
        self.save_button = QPushButton("Save INI")
        self.save_button.setToolTip(
            "Save the current configuration values (Ctrl+S)."
        )
        self.save_button.clicked.connect(self.save_config)
        self.save_button.setEnabled(False)  # Enabled when dirty
        button_layout_1.addWidget(self.save_button)

        self.reload_button = QPushButton("Reload INI")
        self.reload_button.setToolTip(
            "Reload the current INI file from disk (F5)."
        )
        self.reload_button.clicked.connect(self._reload_current_file)
        self.reload_button.setEnabled(False)  # Enabled when a file is loaded
        button_layout_1.addWidget(self.reload_button)

        self.edit_ini_button = QPushButton("Edit INI")
        self.edit_ini_button.setToolTip(
            "Open the current INI file in the default text editor (Ctrl+E)."
        )
        self.edit_ini_button.clicked.connect(self._open_ini_in_editor)
        self.edit_ini_button.setEnabled(False)
        button_layout_1.addWidget(self.edit_ini_button)
        button_layout_1.addStretch()

        # --- Row 2: Script and Application Operations ---
        self.run_button = QPushButton("Run")
        self.run_button.setToolTip(
            "Execute the script with the current INI settings."
        )
        self.run_button.clicked.connect(self.run_script)
        button_layout_2.addWidget(self.run_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setToolTip("Terminate the currently running script.")
        self.stop_button.clicked.connect(self.stop_script)
        self.stop_button.setEnabled(False)
        button_layout_2.addWidget(self.stop_button)

        # Add a separator for visual grouping
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Plain)
        button_layout_2.addWidget(separator)

        self.clear_button = QPushButton("Clear Output")
        self.clear_button.setToolTip(
            "Clear all text from the output window (Ctrl+L)."
        )
        self.clear_button.clicked.connect(self.clear_output)
        button_layout_2.addWidget(self.clear_button)
        button_layout_2.addStretch()

        self.settings_button = QPushButton("Settings")
        self.settings_button.setToolTip("Open application settings.")
        self.settings_button.clicked.connect(self.open_settings_dialog)
        button_layout_2.addWidget(self.settings_button)

        if self.multi_tab_enabled:
            self.new_tab_button = QPushButton("New Output Tab")
            self.new_tab_button.setToolTip("Open a new tab to run a script in.")
            self.new_tab_button.clicked.connect(self.create_new_tab)
            button_layout_2.addWidget(self.new_tab_button)

        self.main_layout.addLayout(button_layout_1)
        self.main_layout.addLayout(button_layout_2)

        # --- Tabbed Output Area ---
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(self.multi_tab_enabled)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.update_button_states)
        self.main_layout.setStretchFactor(self.tab_widget, 1)
        self.main_layout.addWidget(self.tab_widget)

        # Define and apply icons now that all buttons and actions have been created.
        self._define_icon_map()
        self._apply_icons()
        self._apply_theme()  # Apply theme after all widgets are created

        # --- DETERMINE INITIAL SCRIPT CONFIG FILE ---
        # This is the file with [Command], [Arguments], etc.
        initial_script_config_path_str = self.app_settings.get(
            self.SETTINGS_SECTION, "last_loaded_ini", fallback=None
        )
        initial_script_config_path = None

        if initial_script_config_path_str:
            path_obj = pathlib.Path(initial_script_config_path_str)
            if path_obj.is_absolute():
                path_candidate = path_obj
            else:
                # If relative, resolve it against the application's directory.
                path_candidate = self.script_dir / path_obj

            if path_candidate.exists():
                initial_script_config_path = path_candidate

        # Fallback to a default if the last one doesn't exist or isn't set
        if not initial_script_config_path:
            initial_script_config_path = self.script_dir / "default.ini"
        # --- END DETERMINATION ---

        # Initial load and UI setup using the determined script config file
        self._load_and_build_ui(initial_script_config_path)
        self.create_new_tab()

    def closeEvent(self, event: QCloseEvent):
        """Override the close event to check for unsaved changes and running processes."""
        if not self._prompt_to_save_if_dirty():
            event.ignore()  # User cancelled the close operation
            return

        # Check for any running processes in the tabs
        running_processes = [
            p
            for p in self.tab_process_map.values()
            if p.state() == QProcess.ProcessState.Running
        ]
        if running_processes:
            reply = QMessageBox.question(
                self,
                "Processes are Running",
                "One or more scripts are still running.\n"
                "Closing this window will terminate them. Are you sure?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

        if self.remember_window_size:
            size = self.size()
            self.app_settings.set(
                self.SETTINGS_SECTION, "window_width", str(size.width())
            )
            self.app_settings.set(
                self.SETTINGS_SECTION, "window_height", str(size.height())
            )
            self._save_app_settings()

        event.accept()

    def _set_dirty(self, is_dirty: bool):
        """Sets the dirty status and updates the window title accordingly."""
        if self.is_dirty == is_dirty:
            return  # No change

        self.is_dirty = is_dirty
        title = self.windowTitle()
        if is_dirty and not title.endswith("*"):
            self.setWindowTitle(title + "*")
        elif not is_dirty and "*" in title:
            self.setWindowTitle(title[:-1])

        # Also update the save button's state.
        # We check for the attribute in case this is called before the button is created,
        # though in the current flow it will exist.
        if hasattr(self, "save_button"):
            self.save_button.setEnabled(is_dirty)

    def _create_actions(self):
        """Creates all the QAction objects for menus and toolbars."""
        self.open_action = QAction("&Open INI File...", self)
        self.open_action.setToolTip("Open a different INI configuration file.")
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_action.triggered.connect(self._prompt_open_file)

        self.edit_ini_action = QAction("&Edit INI File", self)
        self.edit_ini_action.triggered.connect(self._open_ini_in_editor)
        self.edit_ini_action.setEnabled(False)
        self.edit_ini_action.setShortcut("Ctrl+E")

        self.save_action = QAction("&Save INI", self)
        self.save_action.setToolTip(
            "Save the current configuration values to the INI file."
        )
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_action.triggered.connect(self.save_config)

        self.reload_action = QAction("&Reload INI File", self)
        self.reload_action.setToolTip(
            "Reload the current INI file from disk (F5)."
        )
        self.reload_action.setShortcut(QKeySequence.StandardKey.Refresh)  # F5
        self.reload_action.triggered.connect(self._reload_current_file)
        self.reload_action.setEnabled(False)  # Disabled until a file is loaded

        self.save_output_action = QAction("Save &Output As...", self)
        self.save_output_action.setToolTip(
            "Save the contents of the output window to a text file."
        )
        self.save_output_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.save_output_action.triggered.connect(self.save_output)

        self.clear_output_action = QAction("&Clear Output", self)
        self.clear_output_action.setToolTip(
            "Clear all text from the output window."
        )
        self.clear_output_action.setShortcut("Ctrl+L")
        self.clear_output_action.triggered.connect(self.clear_output)

        self.settings_action = QAction("&Settings...", self)
        self.settings_action.triggered.connect(self.open_settings_dialog)

    def _create_menus(self):
        """Creates the main menu bar."""
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.edit_ini_action)
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.reload_action)
        file_menu.addSeparator()
        file_menu.addAction(self.save_output_action)

        edit_menu = self.menuBar().addMenu("&Edit")
        edit_menu.addAction(self.clear_output_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.settings_action)

    def _define_icon_map(self):
        """Defines the mapping from widgets to their standard icon names."""
        self.icon_map = {
            # Actions
            self.open_action: "document-open",
            self.save_action: "document-save",
            self.reload_action: "view-refresh",
            self.save_output_action: "document-save-as",
            self.settings_action: "preferences-system",
            self.clear_output_action: "edit-clear",
            self.edit_ini_action: "document-edit",
            # Buttons
            self.run_button: "media-playback-start",
            self.stop_button: "media-playback-stop",
            self.save_button: "document-save",
            self.reload_button: "view-refresh",
            self.clear_button: "edit-clear",
            self.settings_button: "preferences-system",
            self.edit_ini_button: "document-edit",
        }

    def _apply_icons(self):
        """Applies or removes icons from all widgets based on the current setting."""
        for widget, icon_name in self.icon_map.items():
            if self.show_icons:
                widget.setIcon(QIcon.fromTheme(icon_name))
            else:
                widget.setIcon(QIcon())  # Set an empty icon to remove it

    def _apply_theme(self):
        """Applies the selected color theme to the application."""
        if self.theme == "dark":
            palette = create_dark_palette()
            self.banner_frame.setStyleSheet(
                "QFrame { background-color: #c1c1c1; border-radius: 5px; }"
            )
        elif self.theme == "light":
            palette = create_light_palette()
            self.banner_frame.setStyleSheet(
                "QFrame { background-color: transparent; }"
            )
        else:  # System theme
            palette = QApplication.style().standardPalette()
            self.banner_frame.setStyleSheet(
                "QFrame { background-color: transparent; }"
            )

        self.central_widget.setPalette(palette)
        self.menuBar().setPalette(palette)

    def _prompt_to_save_if_dirty(self) -> bool:
        """Checks for unsaved changes and prompts the user. Returns False if action is cancelled."""
        if not self.is_dirty:
            return True  # Nothing to do, proceed
        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            "You have unsaved changes. Do you want to save them?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Save:
            self.save_config()
        elif reply == QMessageBox.StandardButton.Cancel:
            return False
        return True

    def update_button_states(self):
        """Enables/disables Run/Stop buttons based on the current tab's state."""
        current_widget = self.tab_widget.currentWidget()
        if not current_widget:
            self.run_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            return

        process = self.tab_process_map.get(current_widget)
        is_running = (
            process is not None
            and process.state() == QProcess.ProcessState.Running
        )

        self.run_button.setEnabled(not is_running)
        self.stop_button.setEnabled(is_running)

    def stop_script(self):
        """Terminates the running QProcess in the current tab."""
        current_widget = self.tab_widget.currentWidget()
        if current_widget in self.tab_process_map:
            process = self.tab_process_map[current_widget]
            if process.state() == QProcess.ProcessState.Running:
                process.terminate()
                self.statusBar().showMessage(
                    "Attempting to stop the process...", 3000
                )

    def create_new_tab(self):
        """Creates a new, empty tab for script output."""
        self.tab_counter += 1
        output_widget = QTextEdit()
        output_widget.setReadOnly(True)

        tab_name = f"Output {self.tab_counter}"
        index = self.tab_widget.addTab(output_widget, tab_name)
        self.tab_widget.setCurrentIndex(index)

        self._set_initial_output_info(output_widget)
        self.update_button_states()
        return output_widget

    def close_tab(self, index: int):
        """Handles the request to close a tab."""
        if not self.multi_tab_enabled or self.tab_widget.count() <= 1:
            return

        widget_to_close = self.tab_widget.widget(index)
        process = self.tab_process_map.get(widget_to_close)

        if process and process.state() == QProcess.ProcessState.Running:
            reply = QMessageBox.question(
                self,
                "Process is Running",
                "A script is still running in this tab. Do you want to terminate it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                process.terminate()  # The finished signal will handle cleanup
                self.tab_widget.removeTab(index)  # Remove tab immediately
            else:
                return  # User cancelled, do nothing
        else:
            # No process running, or it's already finished.
            if widget_to_close in self.tab_process_map:
                # Clean up a finished process entry if it exists
                del self.tab_process_map[widget_to_close]
            self.tab_widget.removeTab(index)

    def _find_widget_for_process(self, process: QProcess) -> QTextEdit | None:
        """Finds the QTextEdit widget associated with a given QProcess."""
        for widget, p in self.tab_process_map.items():
            if p is process:
                return widget
        return None

    def handle_tab_output(self, process: QProcess):
        widget = self._find_widget_for_process(process)
        if not widget:
            return
        data = process.readAllStandardOutput()
        text = bytes(data).decode("utf-8", errors="ignore").strip()
        for line in text.splitlines():
            self._log_message(widget, f"> {line}")

    def handle_tab_error(self, process: QProcess):
        widget = self._find_widget_for_process(process)
        if not widget:
            return
        data = process.readAllStandardError()
        error_text = bytes(data).decode("utf-8", errors="ignore").strip()
        for line in error_text.splitlines():
            self._log_message(widget, f"! ERROR: {line}", color="red")

    def tab_process_finished(self, process: QProcess):
        widget = self._find_widget_for_process(process)
        if not widget:
            return  # Widget might have been closed

        start_time = process.property("start_time")
        end_time = datetime.now()
        elapsed_str = (
            f"{(end_time - start_time).total_seconds():.2f}s"
            if start_time
            else "N/A"
        )

        exit_code = process.exitCode()
        exit_status = process.exitStatus()

        finish_time_str = end_time.strftime("%H:%M:%S")
        self._log_message(
            widget,
            f"\n--- Finished at {finish_time_str} (Elapsed: {elapsed_str}) ---",
            bold=True,
        )
        if exit_status == QProcess.ExitStatus.CrashExit:
            self._log_message(
                widget,
                "! Process was terminated or crashed.",
                color="red",
                bold=True,
            )
        else:
            message = f"--- Process finished with exit code {exit_code} ---"
            color = "green" if exit_code == 0 else None
            self._log_message(widget, message, color=color, bold=True)

        # Update tab title
        index = self.tab_widget.indexOf(widget)
        if index != -1:
            tab_text = self.tab_widget.tabText(index)
            if not tab_text.startswith("[Finished]"):
                self.tab_widget.setTabText(index, f"[Finished] {tab_text}")
        widget.append("")  # Add a blank line for spacing

        # The process is finished, so it's no longer "running" in this tab.
        if widget in self.tab_process_map:
            del self.tab_process_map[widget]

        process.deleteLater()
        self.update_button_states()

    def _get_ui_values(self) -> dict[tuple[str, str], str]:
        """Reads all current values from the UI editor widgets and returns them in a dictionary."""
        ui_values = {}
        for (section, key), editor in self.editors.items():
            if isinstance(editor, FileNameWidget):
                ui_values[(section, key)] = editor.text()
            elif isinstance(editor, QCheckBox):
                ui_values[(section, key)] = str(editor.isChecked()).lower()
            elif isinstance(editor, QLineEdit):
                ui_values[(section, key)] = editor.text()
        return ui_values

    def _get_script_and_args(
        self,
    ) -> tuple[pathlib.Path, list[str]] | tuple[None, None]:
        """Reads UI values, validates the script, and returns the script path and sorted arguments."""
        ui_values = self._get_ui_values()

        script_filename = ui_values.get(("Command", "script_file_name"))
        if not script_filename:
            QMessageBox.critical(
                self,
                "Error",
                "'script_file_name' not found in the [Command] section.",
            )
            return None, None

        script_path = self.script_dir / script_filename
        if not script_path.exists():
            QMessageBox.critical(
                self, "Error", f"Script file not found at '{script_path}'."
            )
            return None, None

        args = []
        if self.config.has_section("ArgParse"):
            # New ArgParse logic
            for key, definition_obj in self.config.items("ArgParse"):
                definition_text = definition_obj.value
                flag, _ = self._parse_argparse_definition(definition_text)
                if not flag:
                    continue

                editor = self.editors.get(("Arguments", key))
                ui_value = ui_values.get(("Arguments", key))

                if isinstance(editor, QCheckBox):
                    if ui_value == "true":
                        args.append(flag)
                elif ui_value:  # For text fields, only add if there is a value
                    args.append(flag)
                    args.append(ui_value)
        else:
            # Fallback to old argN logic for backward compatibility
            argument_keys = [
                k
                for s, k in ui_values.keys()
                if s == "Arguments" and k.startswith("arg") and k[3:].isdigit()
            ]
            sorted_arg_keys = sorted(argument_keys, key=lambda k: int(k[3:]))
            args = [ui_values[("Arguments", key)] for key in sorted_arg_keys]

            last_non_empty_index = -1
            for i, value in reversed(list(enumerate(args))):
                if value:
                    last_non_empty_index = i
                    break

            if last_non_empty_index > 0:
                for i in range(last_non_empty_index):
                    if not args[i]:
                        arg_number = i + 1
                        QMessageBox.warning(
                            self,
                            "Invalid Arguments",
                            f"Argument 'arg{arg_number}' is empty, but a later argument has a value.\n\nPlease fill in all preceding arguments before running the script.",
                        )
                        return None, None

        return script_path, args

    def _load_app_settings(self):
        """Loads app settings from the dedicated INI file, creating it if it doesn't exist."""
        if self.settings_file.exists():
            self.app_settings.read(self.settings_file)

        # Ensure the 'Settings' section exists
        if not self.app_settings.has_section(self.SETTINGS_SECTION):
            self.app_settings.add_section(self.SETTINGS_SECTION)

        # Check for default values and write the file if it was missing or incomplete
        made_changes = False
        if not self.app_settings.has_option(
            self.SETTINGS_SECTION, "multi_tab_mode"
        ):
            self.app_settings.set(
                self.SETTINGS_SECTION, "multi_tab_mode", "false"
            )
            made_changes = True
        if not self.app_settings.has_option(
            self.SETTINGS_SECTION, "remember_window_size"
        ):
            self.app_settings.set(
                self.SETTINGS_SECTION, "remember_window_size", "true"
            )
            made_changes = True
        if not self.app_settings.has_option(
            self.SETTINGS_SECTION, "run_in_background"
        ):
            self.app_settings.set(
                self.SETTINGS_SECTION, "run_in_background", "false"
            )
            made_changes = True
        if not self.app_settings.has_option(
            self.SETTINGS_SECTION, "window_width"
        ):
            self.app_settings.set(self.SETTINGS_SECTION, "window_width", "600")
            made_changes = True
        if not self.app_settings.has_option(
            self.SETTINGS_SECTION, "window_height"
        ):
            self.app_settings.set(self.SETTINGS_SECTION, "window_height", "500")
            made_changes = True
        if not self.app_settings.has_option(
            self.SETTINGS_SECTION, "argument_columns"
        ):
            self.app_settings.set(
                self.SETTINGS_SECTION, "argument_columns", "1"
            )
            made_changes = True
        if not self.app_settings.has_option(
            self.SETTINGS_SECTION, "show_icons"
        ):
            self.app_settings.set(self.SETTINGS_SECTION, "show_icons", "true")
            made_changes = True
        if not self.app_settings.has_option(
            self.SETTINGS_SECTION, "last_loaded_ini"
        ):
            default_ini_path = self.script_dir / "default.ini"
            self.app_settings.set(
                self.SETTINGS_SECTION,
                "last_loaded_ini",
                str(default_ini_path.resolve()),
            )
            made_changes = True

        if made_changes:
            self._save_app_settings()

    def _save_app_settings(self):
        """Saves the current app settings to the dedicated INI file."""
        try:
            with open(self.settings_file, "w") as f:
                self.app_settings.write(f)
        except Exception as e:
            self.statusBar().showMessage(
                f"Warning: Could not save settings: {e}", 5000
            )

    def open_settings_dialog(self):
        """Opens the settings dialog to allow user configuration."""
        # Create a deep copy of the settings to detect any changes
        old_settings = {
            section: dict(self.app_settings.items(section))
            for section in self.app_settings.sections()
        }

        dialog = SettingsDialog(self, settings_parser=self.app_settings)

        if dialog.exec():
            dialog.apply_settings()
            self._save_app_settings()

            new_settings = {
                section: dict(self.app_settings.items(section))
                for section in self.app_settings.sections()
            }

            # If any setting has changed, prompt for a restart.
            if old_settings != new_settings:
                reply = QMessageBox.question(
                    self,
                    "Restart Required",
                    "Settings have been changed. A restart is required for them to take effect.\n\nRestart now?",
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.restart_application()
            else:
                QMessageBox.information(
                    self,
                    "Settings Saved",
                    "Your settings have been saved and will be applied on the next restart.",
                )

    def restart_application(self):
        """Saves state and restarts the application."""
        # The close() call will trigger the closeEvent, which saves settings and checks for running processes.
        # If close() returns True, it means the window was closed successfully.
        if self.close():
            executable = sys.executable
            if executable:
                QProcess.startDetached(executable, sys.argv)
            else:
                QMessageBox.critical(
                    self,
                    "Restart Failed",
                    "Could not determine the Python executable path to restart.",
                )

    def _reload_current_file(self):
        """Reloads the current INI file, prompting to save if dirty."""
        if not self.config_file:
            self.statusBar().showMessage(
                "No INI file is currently loaded.", 3000
            )
            return

        if not self._prompt_to_save_if_dirty():
            return  # User cancelled

        self.statusBar().showMessage(
            f"Reloading {self.config_file.name}...", 2000
        )
        self._load_and_build_ui(self.config_file)

        # After reloading the UI, the QTextEdit might scroll to the top.
        # This ensures the view remains at the bottom, where the last output is.
        # We use a QTimer to schedule this action for after the layout has settled.
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, QTextEdit):
            # Schedule the scroll to happen after the current event processing is finished.
            QTimer.singleShot(
                0,
                lambda: current_widget.verticalScrollBar().setValue(
                    current_widget.verticalScrollBar().maximum()
                ),
            )

    def _open_file_dialog(
        self, line_edit_widget: QLineEdit, file_filter: str = "All Files (*)"
    ):
        """Opens a file dialog and sets the selected path in the provided QLineEdit."""
        # We use self.script_dir to give the dialog a sensible starting place
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select a File", str(self.script_dir), filter=file_filter
        )
        if file_path:
            line_edit_widget.setText(file_path)

    def _prompt_open_file(self):
        """Opens a dialog to select a new INI file and reloads the UI."""
        if not self._prompt_to_save_if_dirty():
            return  # User cancelled

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open INI File",
            str(self.script_dir),
            "INI Files (*.ini);;All Files (*)",
        )
        if file_path:
            self._load_and_build_ui(pathlib.Path(file_path))

    def _clear_config_layout(self):
        """Removes all widgets from the config layout."""
        while self.config_layout.count():
            item = self.config_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def _build_command_section_ui(
        self, section_items: list, start_row: int
    ) -> int:
        """Builds the UI for the [Command] section."""
        num_columns = self.app_settings.getint(
            self.SETTINGS_SECTION, "argument_columns", fallback=1
        )
        current_row = start_row

        # Add the logo as a banner at the top of the command section.
        # The self.banner_frame is pre-created in __init__ to avoid initialization order errors.
        logo_label = QLabel()
        pixmap = QPixmap(":/logo/app_banner")  # Use the detailed banner logo
        logo_label.setPixmap(
            pixmap.scaledToHeight(
                70, Qt.TransformationMode.SmoothTransformation
            )
        )
        logo_label.setToolTip("Guini - GUI for INI")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.banner_frame.layout().addWidget(logo_label)
        self.banner_frame.setMaximumWidth(600)  # Set a max width for the banner

        # Add the banner frame to the main config layout, spanning all columns
        self.config_layout.addWidget(
            self.banner_frame, current_row, 0, 1, num_columns * 2
        )
        current_row += 1

        for key, option_obj in section_items:
            value = option_obj.value
            if self.config.has_section("Labels"):
                # get() can return an Option object or a string fallback. We need to handle both.
                label_text_or_obj = self.config.get("Labels", key, fallback=key)
                label_text = (
                    label_text_or_obj.value
                    if hasattr(label_text_or_obj, "value")
                    else label_text_or_obj
                )
            else:
                label_text = key
            clean_label, type_hint = self._parse_label(label_text)
            editor, _ = self._create_editor_for_value(
                key, value, type_hint=type_hint
            )
            label = QLabel(clean_label)
            self.config_layout.addWidget(label, current_row, 0)

            self.config_layout.addWidget(
                editor, current_row, 1, 1, num_columns * 2 - 1
            )
            # The script_file_name widget should not span multiple columns,
            # as its default size can force an undesirably large minimum window width.
            # We set its column span to 1.
            column_span = 1
            self.config_layout.addWidget(editor, current_row, 1, 1, column_span)

            self.editors[("Command", key)] = editor
            current_row += 1
        return current_row

    def _build_arguments_section_ui(
        self, section_items: list, start_row: int
    ) -> int:
        """Builds the UI for the [Arguments] section with multiple columns."""
        num_columns = self.app_settings.getint(
            self.SETTINGS_SECTION, "argument_columns", fallback=1
        )

        if self.config.has_section("ArgParse"):
            # New ArgParse logic
            arg_definitions = list(self.config.items("ArgParse"))
            num_args = len(arg_definitions)
            rows_per_col = (num_args + num_columns - 1) // num_columns

            for i, (key, definition_obj) in enumerate(arg_definitions):
                target_col = i // rows_per_col
                target_row_offset = i % rows_per_col
                definition_text = definition_obj.value
                display_label = key.replace("_", " ").title()
                label = QLabel(display_label)
                _, type_hint = self._parse_argparse_definition(definition_text)
                # Get the option object from the [Arguments] section
                default_value_obj = self.config.get(
                    "Arguments", key, fallback=None
                )
                # Extract the string value, or use an empty string as a fallback
                default_value = (
                    default_value_obj.value if default_value_obj else ""
                )
                editor, _ = self._create_editor_for_value(
                    key, default_value, type_hint=type_hint
                )
                self.config_layout.addWidget(
                    label, start_row + target_row_offset, target_col * 2
                )
                self.config_layout.addWidget(
                    editor, start_row + target_row_offset, target_col * 2 + 1
                )
                self.editors[("Arguments", key)] = editor
            return start_row + rows_per_col
        else:
            # Fallback to old argN logic
            num_args = len(section_items)
            rows_per_col = (num_args + num_columns - 1) // num_columns
            for i, (key, option_obj) in enumerate(section_items):
                target_col = i // rows_per_col
                target_row_offset = i % rows_per_col
                value = option_obj.value
                if self.config.has_section("Labels"):
                    # get() can return an Option object or a string fallback. We need to handle both.
                    label_text_or_obj = self.config.get(
                        "Labels", key, fallback=key
                    )
                    label_text = (
                        label_text_or_obj.value
                        if hasattr(label_text_or_obj, "value")
                        else label_text_or_obj
                    )
                else:
                    label_text = key
                clean_label, type_hint = self._parse_label(label_text)
                editor, _ = self._create_editor_for_value(
                    key, value, type_hint=type_hint
                )
                label = QLabel(clean_label)
                self.config_layout.addWidget(
                    label, start_row + target_row_offset, target_col * 2
                )
                self.config_layout.addWidget(
                    editor, start_row + target_row_offset, target_col * 2 + 1
                )
                self.editors[("Arguments", key)] = editor
            return start_row + rows_per_col

    def _load_and_build_ui(self, file_path: pathlib.Path):
        """Clears the current UI and builds a new one from the given INI file."""
        # Add robust error handling for file loading
        if not file_path.exists():
            QMessageBox.critical(
                self,
                "Config File Not Found",
                f"The configuration file could not be found at:\n{file_path}",
            )
            # We can't proceed without a config file, so leave the UI empty.
            return

        self.config_file = (
            file_path  # This is the currently loaded SCRIPT config
        )
        self.reload_button.setEnabled(True)
        self.reload_action.setEnabled(True)
        self.edit_ini_button.setEnabled(True)
        self.edit_ini_action.setEnabled(True)
        self.setWindowTitle(
            f"{APP_NAME} v{__version__} - {self.config_file.name}"
        )
        self._clear_config_layout()
        self.editors.clear()

        self.config = ConfigUpdater()
        try:
            self.config.read(self.config_file, encoding="utf-8")
        except configparser.Error as e:
            msg = f"Error parsing INI file: {e}"
            self.statusBar().showMessage(msg, 5000)
            return

        # --- SAVE THIS PATH AS THE LAST LOADED INI ---
        try:
            # Store path relative to the script directory for portability
            relative_path = self.config_file.relative_to(self.script_dir)
            path_to_save = str(relative_path)
        except ValueError:
            # This occurs if the file is on a different drive (on Windows).
            # In this case, fall back to an absolute path.
            path_to_save = str(self.config_file.resolve())

        self.app_settings.set(
            self.SETTINGS_SECTION, "last_loaded_ini", path_to_save
        )
        self._save_app_settings()
        # --- END SAVE ---

        # num_columns = self.app_settings.getint('Settings', 'argument_columns', fallback=1)
        current_row = 0

        sections_to_display = ["Command", "Arguments"]
        for section_name in sections_to_display:
            if self.config.has_section(section_name):
                if section_name == "Arguments":
                    items = list(self.config.items(section_name))
                    current_row = self._build_arguments_section_ui(
                        items, current_row
                    )
                elif section_name == "Command":
                    items = list(self.config.items(section_name))
                    current_row = self._build_command_section_ui(
                        items, current_row
                    )

        # Final check to ensure the critical command section was loaded
        if not self.config.has_section("Command"):
            msg = "Error: INI file is missing the required [Command] section."
            self.statusBar().showMessage(msg, 5000)

        # After loading, the state is clean
        self._set_dirty(False)

    def clear_output(self):
        """Clears the output text area of the current tab."""
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, QTextEdit):
            self._set_initial_output_info(current_widget)
            self.statusBar().showMessage("Current tab cleared.", 3000)

    def _set_initial_output_info(self, widget: QTextEdit):
        """Clears the output and prints the initial session info."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        py_version = sys.version.split("\n")[0]

        widget.clear()
        self._log_message(
            widget, f"--- Session started at: {now} ---", bold=True
        )
        self._log_message(widget, f"Python Version: {py_version}", color="blue")
        self._log_message(
            widget, f"Executable: {sys.executable}", color="#666666"
        )
        self._log_message(
            widget, "----------------------------------", bold=True
        )

    def _log_message(
        self,
        widget: QTextEdit,
        text: str,
        color: str | None = None,
        bold: bool = False,
    ):
        """Appends a message to the output area with optional styling."""
        # Theme-aware color mapping
        if color:
            if self.theme == "dark":
                if color == "blue":
                    color = "#569CD6"  # A lighter, more readable blue
                elif color == "red":
                    color = "#F44747"  # A brighter red
                elif color == "green":
                    color = "#6A9955"  # A clear green
                elif color == "#666666":
                    color = "#999999"  # A light gray for commands
            else:  # Light theme colors (can be adjusted if needed)
                if color == "red":
                    color = "#D32F2F"

        # Check if the scrollbar is at the bottom before we add new text.
        # This allows the user to scroll up and inspect output without being forced back down.
        scrollbar = widget.verticalScrollBar()
        is_at_bottom = scrollbar.value() >= (
            scrollbar.maximum() - 4
        )  # A small tolerance

        if bold:
            text = f"<b>{text}</b>"
        if color:
            # Using a span with inline CSS is more modern than <font>
            # but <font> is simple and works perfectly here.
            text = f'<font color="{color}">{text}</font>'

        widget.append(text)

        if is_at_bottom:
            # If we were at the bottom, stay at the bottom.
            scrollbar.setValue(scrollbar.maximum())

    def save_output(self):
        """Saves the content of the current tab's output area to a text file."""
        current_widget = self.tab_widget.currentWidget()
        if (
            not isinstance(current_widget, QTextEdit)
            or not current_widget.toPlainText()
        ):
            self.statusBar().showMessage(
                "Current tab is empty. Nothing to save.", 3000
            )
            return

        # Suggest a default filename and filter for text files
        default_path = self.script_dir / "output.txt"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Output As",
            str(default_path),
            "Text Files (*.txt);;All Files (*)",
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(current_widget.toPlainText())
                self.statusBar().showMessage(
                    f"Output saved to {file_path}", 4000
                )
            except Exception as e:
                error_msg = f"Error saving file: {e}"
                self.statusBar().showMessage(error_msg, 5000)

    def _parse_label(self, label_text: str) -> tuple[str, str | None]:
        """Parses a label string to extract a clean label and an optional type hint."""
        # Only match specific, known type hints. This allows other parenthetical text in the label.
        type_pattern = r"\s*\((integer|float|boolean|filename)\)\s*$"
        match = re.search(type_pattern, label_text, re.IGNORECASE)
        if match:
            # The clean label is everything before the matched pattern.
            clean_label = label_text[: match.start()].strip()
            type_hint = match.group(1).strip().lower()
            return clean_label, type_hint
        return label_text, None

    def _parse_argparse_definition(
        self, text: str
    ) -> tuple[str | None, str | None]:
        """Parses '--flag (type)' to get the flag and type hint."""
        flag_pattern = r"^\s*(?P<flag>--?[\w-]+)"
        flag_match = re.match(flag_pattern, text)
        flag = flag_match.group("flag") if flag_match else None

        # This pattern now supports list types, e.g., (list[int])
        type_pattern = r"\((list\[\w+\]|integer|float|boolean|filename)\)"
        type_match = re.search(type_pattern, text, re.IGNORECASE)
        type_hint = type_match.group(1).strip().lower() if type_match else None

        return flag, type_hint

    def _create_editor_for_value(
        self, key: str, value: str, type_hint: str | None = None
    ) -> tuple[QWidget, str]:
        """Creates the appropriate editor widget, prioritizing the type_hint if provided."""
        # Special case: the script_file_name key should always be a filename editor.
        if key == "script_file_name":
            final_type = "filename"
        else:
            # Determine the type, using the hint if available, otherwise guess from the value
            final_type = type_hint
            if not final_type:
                if value.lower() in ["true", "false"]:
                    final_type = "boolean"
                else:
                    try:
                        int(value)
                        final_type = "integer"
                    except ValueError:
                        try:
                            float(value)
                            final_type = "float"
                        except ValueError:
                            final_type = "string"

        # Create the widget based on the determined type
        if final_type and final_type.startswith("list["):
            editor = QLineEdit(value)
            editor.textChanged.connect(lambda: self._set_dirty(True))
            # Provide a helpful tooltip based on the inner type
            inner_type_match = re.search(r"list\[(\w+)\]", final_type)
            inner_type = (
                inner_type_match.group(1) if inner_type_match else "items"
            )
            if inner_type == "file":
                editor.setToolTip(
                    "A comma-separated list of files.\nYou can also use wildcards (e.g., data/*.csv)."
                )
            else:
                editor.setToolTip(
                    f"A comma-separated list of {inner_type}s (e.g., 1, 2, 3)."
                )
            return editor, final_type

        if final_type == "boolean":
            editor = QCheckBox()
            editor.stateChanged.connect(lambda: self._set_dirty(True))
            editor.setChecked(value.lower() == "true")
            editor.setToolTip("A boolean value (true or false).")
            return editor, "boolean"
        elif final_type == "integer":
            editor = QLineEdit(value)
            editor.textChanged.connect(lambda: self._set_dirty(True))
            editor.setValidator(QIntValidator())
            editor.setToolTip("An integer value (e.g., 1, -10, 100).")
            return editor, "integer"
        elif final_type == "float":
            editor = QLineEdit(value)
            editor.textChanged.connect(lambda: self._set_dirty(True))
            editor.setValidator(QDoubleValidator())
            editor.setToolTip("A floating-point value (e.g., 1.0, -3.14).")
            return editor, "float"
        elif final_type == "filename":
            editor = FileNameWidget(value)
            editor.line_edit.textChanged.connect(lambda: self._set_dirty(True))
            start_dir = str(self.script_dir)
            file_filter = (
                "Python Scripts (*.py *.pyw);;All Files (*)"
                if key == "script_file_name"
                else "All Files (*)"
            )
            editor.set_dialog_options(
                file_filter=file_filter, start_dir=start_dir
            )
            if key == "script_file_name":
                pass  # Already handled by the filter logic above
            editor.setToolTip("A path to a file.")
            return editor, "filename"

        # Default to string for any other case (including unknown type hints)
        editor = QLineEdit(value)
        editor.textChanged.connect(lambda: self._set_dirty(True))
        editor.setToolTip("A string of text.")
        return editor, "string"

    def save_config(self):
        """Saves the current UI values back to the INI file, preserving comments and structure."""
        ui_values = self._get_ui_values()

        # self.config is a ConfigUpdater object which handles round-trip modifications
        for (section, key), value in ui_values.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
            self.config.set(section, key, value)

        if self.config_file:
            self.config.update_file()

        self.statusBar().showMessage(
            f"Configuration saved to {self.config_file}", 3000
        )
        self._set_dirty(False)

    def _open_ini_in_editor(self):
        """Opens the currently loaded INI file in the default system editor."""
        if self.config_file and self.config_file.exists():
            # Prompt to save unsaved changes first, as external edits will cause a reload.
            if self.is_dirty:
                reply = QMessageBox.question(
                    self,
                    "Unsaved Changes",
                    "You have unsaved changes. Do you want to save them before editing the file externally?\n\n"
                    "Editing the file externally without saving may cause your changes to be lost.",
                    QMessageBox.StandardButton.Save
                    | QMessageBox.StandardButton.Discard
                    | QMessageBox.StandardButton.Cancel,
                )
                if reply == QMessageBox.StandardButton.Save:
                    self.save_config()
                elif reply == QMessageBox.StandardButton.Cancel:
                    return

            url = QUrl.fromLocalFile(str(self.config_file))
            QDesktopServices.openUrl(url)
            self.statusBar().showMessage(
                f"Opening {self.config_file.name} in editor...", 3000
            )
        else:
            self.statusBar().showMessage("No INI file loaded to edit.", 3000)

    def run_script(self):
        """Runs the configured script in the currently active tab."""
        current_widget = self.tab_widget.currentWidget()
        if not isinstance(current_widget, QTextEdit):
            self.statusBar().showMessage("No active output tab selected.", 3000)
            return

        if (
            current_widget in self.tab_process_map
            and self.tab_process_map[current_widget].state()
            == QProcess.ProcessState.Running
        ):
            self.statusBar().showMessage(
                "A script is already running in this tab.", 3000
            )
            return

        script_path, args = self._get_script_and_args()
        if not script_path:
            return  # Error was already shown

        # Log a separator for the new run instead of clearing the output
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._log_message(current_widget, "\n" + "=" * 60, bold=True)
        self._log_message(
            current_widget, f"--- Starting new run at: {now} ---", bold=True
        )

        executable = sys.executable

        # --- Handle background (detached) execution ---
        if self.run_in_background:
            python_exe_path = pathlib.Path(sys.executable)
            pythonw_exe = str(python_exe_path.with_name("pythonw.exe"))

            if not pathlib.Path(pythonw_exe).exists():
                self._log_message(
                    current_widget,
                    '<font color="orange">Warning: pythonw.exe not found. Launching attached process with python.exe instead.</font>',
                )
                # Fall through to the normal (attached) execution path below
            else:
                executable = pythonw_exe
                self._log_message(
                    current_widget,
                    '<font color="red">Starting script in background with pythonw.exe. Output will not be captured.</font>',
                )
                self._log_command_string(
                    current_widget, executable, script_path, args
                )
                QProcess.startDetached(executable, [str(script_path)] + args)
                self.statusBar().showMessage(
                    f"Launched '{script_path.name}' in background.", 4000
                )
                return

        # --- Handle normal (attached) execution ---
        self._log_command_string(current_widget, executable, script_path, args)

        process = QProcess(self)
        self.tab_process_map[current_widget] = process

        # Store start time on the process object itself to retrieve later
        process.setProperty("start_time", datetime.now())

        process.readyReadStandardOutput.connect(
            lambda: self.handle_tab_output(process)
        )
        process.readyReadStandardError.connect(
            lambda: self.handle_tab_error(process)
        )
        process.finished.connect(lambda: self.tab_process_finished(process))

        self.statusBar().showMessage(f"Running '{script_path.name}'...")
        process.start(executable, [str(script_path)] + args)

        # Update UI
        current_index = self.tab_widget.currentIndex()
        self.tab_widget.setTabText(current_index, script_path.name)
        self.update_button_states()

    def _log_command_string(
        self,
        widget: QTextEdit,
        executable: str,
        script_path: pathlib.Path,
        args: list[str],
    ):
        """Constructs and logs the full command string being executed."""
        quoted_args = [f'"{arg}"' if " " in arg else arg for arg in args]
        command_str = f'"{executable}" "{script_path}" {" ".join(quoted_args)}'
        self._log_message(widget, f"$ {command_str}\n", color="#666666")


def create_light_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.ColorRole.Link, QColor(0, 0, 255))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    return palette


def create_dark_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    return palette


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Set the initial palette based on settings
    settings = configparser.ConfigParser()
    settings.read(pathlib.Path(__file__).parent.resolve() / "guini.ini")
    theme = settings.get("Settings", "theme", fallback="system").lower()
    if theme == "dark":
        app.setPalette(create_dark_palette())
    elif theme == "light":
        app.setPalette(create_light_palette())

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
