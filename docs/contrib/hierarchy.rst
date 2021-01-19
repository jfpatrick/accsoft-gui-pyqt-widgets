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
     ┃ ┃ ┗ 📂__extras__
     ┃ ┃ ┃ ┗ 📜__deps__.py                 // Required extras for the widget (e.g. testing, linting, documentation or benchmarking)
     ┃ ┃ ┗ 📜_model.py                     // Model source code
     ┃ ┃ ┗ 📜_view.py                      // Widget (view) source code
     ┃ ┃ ┗ 📜__init__.py                   // Public interface of the widget
     ┃ ┃ ┗ 📜__deps__.py                   // Specification of runtime dependencies for the widget
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

Dependencies are defined on the per-widget basis and are split into 2 parts: main runtime dependencies, needed for the
widget to run; and extra dependencies for testing, linting, documentation and other auxiliary phases.

.. note:: It is a good practice to include all 3rd-party dependencies that you explicitly import in your code
          (basically any import except the built-in modules). Refrain from listing :mod:`PyQt5` in this file to
          avoid accidental installation when PyQt Distribution is not activated. When using
          :ref:`qtpy <contrib/custom_widgets:Qt Bindings>`, :mod:`PyQt5` will (almost) never be your explicit import,
          thus will not have to be mentioned in the requirements file. Exceptional cases may be :mod:`~PyQt5.QtTest`
          imports that :mod:`qtpy` does not cover completely (even though
          `pytest-qt <https://pypi.org/project/pytest-qt/>`__ package may cover those cases).

Runtime dependencies should be placed in the ``__deps__.py`` file. This file must expose a variable called ``core``
that represents a list of strings, formatted in the same way, as put in ``setup.py`` files, compatible with
`PEP440 <https://www.python.org/dev/peps/pep-0440>`__. For example:

.. literalinclude:: ../../accwidgets/led/__deps__.py
   :language: python

Similarly, the extra dependencies, located in ``__extras__/__deps__.py`` are using the same format. In this file, the
parser expects a variable called ``extras`` to be a dictionary, where keys are amongst the allowed extras names
(``test``, ``lint``, ``doc``, ``bench``, ``examples``), and values are lists of strings with
`PEP440 <https://www.python.org/dev/peps/pep-0440>`__ dependencies. For example:

.. literalinclude:: ../../accwidgets/led/__extras__/__deps__.py
   :language: python

Allowed extras can be classified as following:

- **test**: Required packages to successfully run test suite
- **lint**: Required package for running code quality and inspection tools
- **doc**: Dependencies to build Sphinx documentation
- **bench**: Packages need for running benchmarks

To fail early when dependencies are not respected, it is a good practice to put a runtime check in widget's main
``__init__.py`` file, e.g.

.. literalinclude:: ../../accwidgets/led/__init__.py
   :language: python
   :lines: 3-7

Some widgets may decide to opt out from checking it at the import time, if they are not completely isolated. E.g.
:class:`~accwidgets.timing_bar.TimingBar` is included by :class:`~accwidgets.timing_bar.ApplicationFrame`, but it's
not guaranteed that for all applications will use the functionality of the timing bar in the
:class:`~accwidgets.timing_bar.ApplicationFrame`. Therefore, dependency check here will be delayed until the
:class:`~accwidgets.timing_bar.TimingBar` is actually initialized and activated.