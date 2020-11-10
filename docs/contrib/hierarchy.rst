Repository Structure
====================

- `Definition of dependencies`_

The repository is composed of 5 main locations hosting the files of each widget. These locations are for the source
code of the widget, documentation, benchmarks (optional), examples, and tests. For clarification, here the structure
from the fictitious widget ``calendar``.

.. To generate code below, I used VS Code with plugin "file-tree-generator". Right+Click on directory -> Generate to Tree

.. code-block::

    📦accsoft-gui-pyqt-widgets
     ┣ 📂accwidgets
     ┃ ┣ 📂...
     ┃ ┗ 📂calendar
     ┃ ┃ ┣ 📂designer
     ┃ ┃ ┃ ┣ 📂icons
     ┃ ┃ ┃ ┃ ┣ 📜Calendar.ico                          // Icon file for the Qt Designer plugin
     ┃ ┃ ┃ ┗ 📜accwidgets_calendar_designer_plugin.py  // Qt Designer plugin for the widget (must have unique file name amongst all Designer plugins)
     ┃ ┃ ┗ 📜_model.py                     // Model source code
     ┃ ┃ ┗ 📜_view.py                      // Widget (view) source code
     ┃ ┃ ┗ 📜__init__.py                   // Public interface of the widget
     ┣ 📂benchmarks
     ┃ ┣ 📂...
     ┃ ┗ 📂calendar                        // Optional if widget provides benchmarks
     ┃ ┃ ┗ 📜bench_calendar.py             // Standalone runner for a benchmark
     ┣ 📂docs
     ┃ ┣ 📂...
     ┃ ┣ 📂calendar                        // reStructuredText and other resources for documentation
     ┃ ┃ ┣ 📜calendar.rst
     ┃ ┃ ┗ 📜index.rst
     ┃ ┗ 📜conf.py                         // accwidgets Sphinx configuration
     ┣ 📂examples
     ┃ ┣ 📂...
     ┃ ┗ 📂calendar
     ┃ ┃ ┣ 📂designer
     ┃ ┃ ┃ ┣ 📜calendar_gui.ui             // Panel built using the calendar's Qt Designer plugin
     ┃ ┃ ┃ ┗ 📜ui_runner.py                // Executable script to load and display the UI file inside QApplication
     ┃ ┃ ┣ 📜choose_date_example.py        // Example use case: Choose a single date
     ┃ ┃ ┗ 📜choose_date_range_example.py  // Example use case: Choose a range of dates
     ┗ 📂tests
     ┃ ┣ 📂...
     ┃ ┗ 📂calendar
     ┃ ┃ ┣ 📜test_calendar.py              // Tests for calendar's view
     ┃ ┃ ┣ 📜test_designer_plugin.py       // Tests for calendar's Qt Designer plugin
     ┃ ┃ ┗ 📜test_calendar_model.py        // Tests for calendar's model


Definition of dependencies
--------------------------

All dependencies are defined on the top level and are groped per-widget and per category. You will find them in
``dependencies.ini`` file in the project root, e.g.:

.. literalinclude:: ../../dependencies.ini
   :language: ini
   :lines: 28-63

Here the dependencies are listed in *toml* format, naming the widgets between ``[ ]`` square brackets. This name should
correspond to your sub-directory names. In our case it would be ``calendar``. ``[accwidgets]`` is a reserved name and
defines common dependencies for the whole project.

The categories are:

- **core**: Required runtime dependencies
- **test**: Required packages to successfully run test suite
- **lint**: Required package for running code quality and inspection tools
- **doc**: Dependencies to build Sphinx documentation
- **bench**: Packages need for running benchmarks
- **release**: Tools needed for uploading the package to package repository

The specification format is standard for
`pip requirements files <https://pip.pypa.io/en/stable/reference/pip_install/#requirements-file-format>`__. We suggest
to use upper limits for the versions in order to make your widgets future-proof (we have observed even minor version
bumps containing breaking changes often, therefore we prefer to pin to range of patch versions within the same minor
version). `Semantic Versioning terminology <https://semver.org/>`__.

**Example requirement with version range**

.. code-block:: ini

   # Defining numpy as a requirement
   numpy>=1.16.4,<1.17

.. note:: It is a good practice to include all 3rd-party dependencies that you explicitly import in your code.
          Refrain from listing :mod:`PyQt5` in this file to avoid accidental installation when PyQt Distribution is
          not activated. When using :ref:`qtpy <contrib/custom_widgets:Qt Bindings>`, :mod:`PyQt5`
          will (almost) never be your explicit import, thus will not have to be mentioned in the requirements file.
          Exceptional cases are some :mod:`~PyQt5.QtTest` imports that :mod:`qtpy` does not cover completely.

.. note:: pip does not provide proper dependency graph resolution, therefore conflicting versions between different
          widget dependencies may break the package at some point. You need to pay careful attention when adding new
          dependencies.
