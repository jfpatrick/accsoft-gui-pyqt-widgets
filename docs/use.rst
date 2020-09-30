Getting started
===============

- `Interactive examples`_
- `Using with Qt Designer`_


The library can contain many different types of widgets, but all of them are separated into different namespaces.
For importing all widgets belonging to a specific sub-project, you can import them as follows:

.. code-block:: python

   import accwidgets.graph as accgraph
   # ...
   widget = accgraph.ExPlotWidget()

You can learn how to use the widgets in 2 ways:

#. Check the :doc:`api/index`
#. Try out `Interactive examples`_


Interactive examples
--------------------
Examples are normally found in the "examples" directory of the source code repository. All examples are grouped by
the widget they are related to. You run them using simple python command (remember to activate PyQt beforehand).

.. code-block:: bash
   :linenos:

   # Get the source code
   git clone git+ssh://git@gitlab.cern.ch:7999/acc-co/accsoft/gui/accsoft-gui-pyqt-widgets.git
   cd accsoft-gui-pyqt-widgets
   # Install the runtime dependencies
   pip install .
   # Run the example
   python examples/graph/minimum_example.py


Using with Qt Designer
----------------------

In order to load custom widgets into Qt Designer with PyQt, user has to specify ``PYQTDESIGNERPATH`` or place them
in one of the default locations (e.g. ``$HOME/.designer/plugins/python`` or
`library search paths known to Qt <https://doc.qt.io/qt-5/qcoreapplication.html#libraryPaths>`__). To aid the loading
of accwidgets plugins, we provide a command ``accwidgets_designer_path`` that will print a path value, suitable for
assigning to ``PYQTDESIGNERPATH``. Thus, you may access accwidgets in Qt Designer by running it as follows:

.. code-block:: bash

   PYQTDESIGNERPATH="$(accwidgets_designer_path):$PYQTDESIGNERPATH" designer
