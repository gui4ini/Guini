# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### To Be Added

* [ ] `pytest` integration and GitHub Actions for CI.
* [ ] Installation using `pip`.
* [x] Support for recognizing lists of numbers and files as argument types.
* [ ] UI controls to add, remove, or edit keys directly, updating the INI file.
* [x] Open `.ini` file in a text editor.
* [ ] Compatible to Linux and iOS(?)

### To Be Updated

* [ ] Documentation: Update screenshots to reflect the latest version.

### To be Tested

* [X] 'Reload INI' Button seems strange
* [ ] Test in a bootstrap mode: add guini inside the  `if __name__ == "__main__":` part, and the the script run it from within.

## [0.6.0] - 2023-10-27

This version introduced a major UI overhaul and significant feature enhancements for robustness and usability.

### Added

* **Background Execution**: Added an option in Settings to run scripts with `pythonw.exe` for detached, background execution.
* **Multi-Tab Interface**: The GUI now supports running multiple scripts in parallel, each in its own tab.
* **Application Settings**: A dedicated `guini.ini` file now stores application settings like multi-tab mode, window size, and argument column layout.
* **UI Branding**: Added a logo banner and application icon for improved branding.
* **Reload INI**: Added a "Reload" action (`File -> Reload`) to refresh the UI from the current INI file.
* **Argument Tooltips**: Type hints in the `[Labels]` section now generate helpful tooltips on the input fields.
* **Dynamic Argument Columns**: Users can now configure the number of columns for the arguments section via Settings.
* **Dark Mode**.

### Changed

* **default `ini` file**: `gui4ini_v**.ini` has been phased out. Now all versions sould use  `gui4ini.ini`

## [0.5.0] - 2023-09-20

Previous stable version. Key features included:

* **Dynamic UI Generation**: Automatically created input widgets based on the values in the INI file.
* **Type Inference**: Basic type detection for booleans, integers, and floats to create appropriate widgets with validation.
* **File Path Selector**: Recognized a `filepath` hint in the `[Labels]` section to generate a file selection dialog.
* **Single Output Panel**: Displayed all script output in a single, non-tabbed text area.
* **Core Execution**: Provided "Run" and "Stop" functionality for the loaded script.
