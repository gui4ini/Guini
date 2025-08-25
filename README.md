# [Guini](https://github.com/gui4ini/Guini): Graphical User Interface (GUI) for INI files

<p align="center">
    <img src="docs/imgs/Guini - Logo.png" height="400">
</p>

## Table of Contents

  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Description](#description)
  - [Usage](#usage)
  - [`*.ini` files for Guini](#ini-files-for-guini)
    - [Adding variable types](#adding-variable-types)
  - [Solving dependencies with `conda`](#solving-dependencies-with-conda)
  - [More Screenshots of the GUI (for version 0.3)](#more-screenshots-of-the-gui-for-version-03)
    - [Example 1 `*.ini` file](#example-1-ini-file)
    - [Example 1 GUI](#example-1-gui)
    - [Example 2 `*.ini` file - Use with `matplotlib`](#example-2-ini-file---use-with-matplotlib)
    - [Example 2 GUI - Use with `matplotlib`](#example-2-gui---use-with-matplotlib)
  - [Future developments](#future-developments)
    - [TO-DO List](#to-do-list)
    - [List of Current Features](#list-of-current-features)
    - [List of Features to add](#list-of-features-to-add)
  - [FAQ](#faq)

## Description

This is small project based on [PySide](https://doc.qt.io/qtforpython/PySide/) that builds a Graphical User Interface (GUI) from an [`*.ini`](https://docs.python.org/3.10/library/configparser.html#supported-ini-file-structure) file, and then run a python script with the values from the file.

It does two main things:

1. Create a GUI from a `*.ini` file with arbiratry number of arguments. It dynamically adjust window size and argument types for better user experience.
2. Run a *user-defined* python script with the arguments of the GUI. The output of the scripts is shown in the *Output* part of the GUI.

For instance, the `*.ini` file below

```ini
[Command]
script_file_name = argument_analyzer.py

[Arguments]
arg1 = first_argument
arg2 = 123
arg3 = another_argument
arg4 = true
arg5 = C:\path\to\your\file.txt

[Labels]
script_file_name = Script File (filename)
arg1 = First Argument (String)
arg2 = Second Argument (Integer)
arg3 = Third Argument
arg4 = Fourth Argument (Boolean)
```

will generate the following GUI.

<p align="center">
    <img src="docs/imgs/Screenshot v0p3.png" height="500">
</p>

When the user presses the `Run` button, the following command will be run:

```bash
python <script_file_name> <arg1> <arg2> <arg3> ... <arg N>
```

which in the example of the `*.ini` file above will be:

```bash
python argument_analyzer.py first_argument 123 another_argument true C:\path\to\your\file.txt
```

The outputs of the python script will be shown in the *Output* terminal in the GUI (see line number 6 in the *Output* terminal of the image above). One can run the script several times.

## Usage

This is the recomended workflow to use Guini:

1. The very first step is to have a python script that can parse command line arguments, for instance using the [sys.argv](https://docs.python.org/3/library/sys.html?highlight%3Dargv%23sys.argv=#sys.argv) list. The examples in the [script](./scripts/) folder all have that capbility.

2. Next you need to create the `*.ini` with sections, keys and arguments as described in the section *`*.ini` files for Guini* below.

3. Run the file `guini.py` as

    ```bash
    python guini.py
    ```

4. Guini will first load the file `guini.ini`. To load your `.ini` there are two options:
   * You can rename the `.ini` file you created as `guini.ini`. This is the recomended option if you will run your script several times.
   * In the GUI, go to `File->Open INI file`, and located your own file.

5. When all the arguments are correct, press the button `Run`. The command that Guini will run will be displayed in the Output window. Any error that occur when run the script will also be displayed in the Output window (*try it!*).

## `*.ini` files for Guini

See the [configparser](https://docs.python.org/3.10/library/configparser.html#supported-ini-file-structure) library for more info on the format of `*.ini` files.

For Guini, the requirements for the `*.ini` file are:

* The only mandatory sections are `[Command]` and `[Arguments]`.
* The section `[Labels]` is optional.
* The keys are also required to be named `script_file_name`, `arg1`, `arg2`, ...,  `argN`, accordingly.

### Adding variable types

It is optional to provide the variable types when providing labels. To provide the variable type, add the type *in parenthesis* to the `args` in the `[Label]` section. Example:

```ini
[Labels]
script_file_name = Script File (filename)
arg1 = First Argument (Integer)
arg2 = Second Argument (Float)
```

If you do not provide the types, Guini will try to guess then. The variable types acceptable are

* `Integers`
* `Floats`
* `Booleans`
* `Strings`
* `filename`: Path to files

For instance, by providing the `filename` type, Guini will provide use the `Open->File` button in the GUI to search for the file.

## Solving dependencies with `conda`

The only mandatory dependency is Python and PySide. Other dependencies are for the examples added in the project.

```bash
conda create --name gui_env python=3.12
conda activate gui_env
conda install -c conda-forge pyside numpy matplotlib
```

## More Screenshots of the GUI (for version 0.3)

### Example 1 `*.ini` file

```ini
[Command]
script_file_name = argument_analyzer.py

[Arguments]
arg1 = first_argument
arg2 = 123
arg3 = another_argument
arg4 = true
arg5 = C:\path\to\your\file.txt
arg6 = C:\path\to\another_file.txt
arg7 =
arg8 =
arg9 =
arg10 =

[Labels]
script_file_name = Script File (filename)
arg1 = First Argument (String)
arg2 = Second Argument (Integer)
arg3 = Third Argument
arg4 = Fourth Argument (Boolean)
arg5 = Fifth Argument (filename)
arg6 = Sixth Argument (filename)
arg7 = Seventh Argument
arg8 = Eighth Argument
arg9 =
```

### Example 1 GUI

<p align="center">
    <img src="docs/imgs/Screenshot 2025-08-23 223802.png" height="400">
</p>



### Example 2 `*.ini` file - Use with `matplotlib`

We use Guini to plot a graph using `matplotlib`. Note that all the `matplotlib` functions are completely outside Guini. In this case, this is handled by [`plot_polyn.py`](docs/imgs/plot_polyn.py).

```ini
[Command]
script_file_name = C:/Users/wcgri/workspace/sandbox4Sagan/gui4ini/scripts/plot_polyn.py

[Arguments]
arg1 = -5.0
arg2 = 10.00
arg3 = 50
arg4 = 3
arg5 = 1
arg6 = 2
arg7 = 1

[Labels]
script_file_name = Plotting Script (filename)
arg1 = X min (Float)
arg2 = X max (Float)
arg3 = Number of points (integer)
arg4 = coef order 1 (Float)
arg5 = coef order 2 (Float)
arg6 = coef order 3 (Float)
arg7 = coef order 4 (Float)
```

### Example 2 GUI - Use with `matplotlib`

<p align="center">
    <img src="docs/imgs/Screenshot v0p3 with matplotlib.png" height="400">
</p>


## Future developments

*(Developers Area)*

### TO-DO List

* [ ] Test with multicore scripts
* [ ] Test in a bootstrap mode: add guini inside the  `if __name__ == "__main__":` part, and the the script run it from within. 

### List of Current Features

* [x] Select the `*.ini` file to be loaded.
* [x] Reconize `filepath` as an option to have `File->Open`

### List of Features to add

* [ ] Installation using `pip`
* [ ] Run multiple instances of the python script
* [ ] Two colunns when the GUI is too tall.
* [ ] (Maybe) a dedicated section for itself inside the `*.ini` file with a few option. Suggestions:
  * 2 columns
  * detached output display
  * font size for display
* [ ] (Maybe) use `guini.ini` to save parameters of guini only.
* [ ] Recognize list of numbers
* [ ] Reconize list of Files
* [ ] Add buttons to Add/Remove/Edit keys, which will then be added to the `*.ini` file.

## FAQ

**Q: Why the name *Guini*?**

**ANS:** It simply means *GUI for INI*.

**Q: Why is the logo a guinea pig?**

**ANS:** It is just because *Guini* sounds line *guinea*.
