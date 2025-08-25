# [Guini](https://github.com/gui4ini/Guini): GUI for INI files

<p align="center">
    <img src="docs/imgs/Guini - Logo.png" height="400">
</p>

## Description

This is small project in [PySide](https://doc.qt.io/qtforpython/PySide/) that creates an GUI from an [`*.ini`](https://docs.python.org/3.10/library/configparser.html#supported-ini-file-structure) file, and then run a python script with the values from the file.

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

The outputs of the python script will be shown in the *Output* terminal in the GUI. One can run the script several times.

### `*.ini` files

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
````

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
</p

## Future developments

*(Developers Area)*.

### TO-DO List

* [ ] Test with multicore scripts

### List of Current Features

* [x] Select the `*.ini` file to be loaded.
* [x] Reconize `filepath` as an option to have `File->Open`

### List of Features to  add

* [ ] Installation using `pip`
* [ ] Two colunns when the GUI is too tall.
* [ ] Maybe a dedicated section for itself inside the `*.ini` file with a few option. Suggestions:
  * 2 columns
  * detached output display
  * font size for display
* [ ] Recognize list of numbers
* [ ] Reconize list of Files
* [ ] Add buttons to Add/Remove/Edit keys, which will then be added to the `*.ini` file.
