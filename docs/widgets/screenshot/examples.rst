Examples
==========

This page briefly explains the examples, that can be found in ``examples/screenshot`` directory of the project's
`source code <https://gitlab.cern.ch/acc-co/accsoft/gui/accsoft-gui-pyqt-widgets>`__. To ensure presence of additional
packages needed to run examples, it is advised to install a special ``examples`` category:

.. code-block:: bash

   pip install .[examples]

- `Basic example`_


Basic example
-------------

To launch this example from the project root, run:

.. code-block:: bash

   python examples/screenshot/basic_example.py

This example shows the simplest way of using :class:`~accwidgets.screenshot.ScreenshotButton` widget. When no sources
are specified, the button will grab a screenshot of the parent window. We can control the appearance of the window
screenshot with :attr:`~accwidgets.screenshot.ScreenshotButton.includeWindowDecorations` property. For the sake of
example, we are using custom model that does connect to the ``TEST`` e-logbook server.

.. image:: ../../img/examples_screenshot_basic.png

.. container:: collapsible-block

   .. container:: collapsible-title

      .. raw:: html

         Show contents of basic_example.py...

   .. literalinclude:: ../../../examples/screenshot/basic_example.py

.. raw:: html

   <p />
