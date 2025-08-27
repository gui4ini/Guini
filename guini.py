import subprocess
import sys
import pathlib

if __name__ == "__main__":
    """
    This script acts as a simple launcher for the main application script, gui4ini_v0.4.py.
    It ensures that the application is run using the correct Python interpreter
    and that the target script is located correctly.
    """
    try:
        # Get the directory where this launcher script is located
        script_dir = pathlib.Path(__file__).parent.resolve()
        # Construct the full path to the target application script
        # target_script_path = script_dir / "Past Versions\gui4ini_v0.5.py"
        target_script_path = script_dir / "gui4ini_v0.6.py"

        # Check if the target script actually exists before trying to run it
        if not target_script_path.exists():
            # Provide a clear error message to the user
            error_message = f"Error: The main application file 'gui4ini_v_0.5.py' was not found in the directory:\n{script_dir}"
            print(error_message, file=sys.stderr)
            sys.exit(1)

        # Execute the main application script using the same Python interpreter that is running this launcher.
        # This is crucial for environments like Conda or venv.
        subprocess.run([sys.executable, str(target_script_path)], check=True)

    except subprocess.CalledProcessError as e:
        # This will catch errors if the target script exits with a non-zero status code
        print(f"The application 'gui4ini_v0.5.py' exited with an error (code {e.returncode}).", file=sys.stderr)
        sys.exit(e.returncode)
    except Exception as e:
        # Catch any other unexpected errors during launch
        print(f"An unexpected error occurred while trying to launch 'gui4ini_v0.5.py':\n{e}", file=sys.stderr)
        sys.exit(1)
