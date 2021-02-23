Led
============

.. image:: ../../img/led.png

.. note:: To start using this widget, make sure to specify ``led`` as an extra, when installing accwidgets, or
          use ``all-widgets``. More on :ref:`install:Specifying dependencies`.

:class:`~accwidgets.led.Led` displays a single LED useful for representing binary values or other color-coded values.
It is a non-interactive (read-only) widget.

:class:`~accwidgets.led.Led` is meant to work either with status Enums or arbitrary colors. When used with statuses,
it receives a predefined color, related to a specific status:

* :attr:`~accwidgets.led.Led.Status.ON` - green
* :attr:`~accwidgets.led.Led.Status.OFF` - gray
* :attr:`~accwidgets.led.Led.Status.WARNING` - yellow
* :attr:`~accwidgets.led.Led.Status.ERROR` - red
* :attr:`~accwidgets.led.Led.Status.NONE` - does not change color from the previous state

Further read
------------

.. toctree::
   :maxdepth: 1

   examples
   api