.. rst_epilog sometimes fails, so we need to include this explicitly, for colors
.. include:: <s5defs.txt>


Widgets
=======

The following is a list of widgets that are requested (implemented ones have status |done|).

.. table::
   :widths: 18 16 42 24

   =====================  ================  ================  ===============================================
   Name                   Status            Preview           Comments
   ---------------------  ----------------  ----------------  -----------------------------------------------
   |livecharts-link|      |done|            |livecharts|      JDataViewer-like features, PyQtGraph derivative
   |lsa-link|             |lsa-status|
   |device-sel-link|      |na|              |devicesel|
   |toggle-trigger-link|  |na|              |toggle-trigger|  For JAPC context
   |status-led-link|      |na|                                Changes its state only when all linked
                                                              properties change to a specific state
   |propedit-link|        |done|            |propedit|        Allows to explicitly Get/Set one or more fields
                                                              of a specific device property
   |log-link|             |wip|
   |trim-link|            |done|            |trim|
   |timing-link|          |done|            |timing|          `"XTIM" <https://wikis.cern.ch/display/TIMING/XTIM>`__
                                                              RDA device based timing
   |spinner-link|         |spinner-status|  |spinner|
   |app-frame-link|       |wip|                               Standard shell for PyQt accelerator
                                                              applications
   |led-link|             |done|            |led|             Works with arbitrary colors or a predefined
                                                              status: :attr:`~accwidgets.led.Led.Status.ON`,
                                                              :attr:`~accwidgets.led.Led.Status.OFF`,
                                                              :attr:`~accwidgets.led.Led.Status.WARNING`,
                                                              :attr:`~accwidgets.led.Led.Status.ERROR`,
                                                              :attr:`~accwidgets.led.Led.Status.NONE`
   =====================  ================  ================  ===============================================

In addition to explicitly requested widgets, those available in
`Inspector <https://wikis.cern.ch/display/INSP/Inspector+Home>`__ will be implemented in the order of
their usage statistics gathered from existing Inspector projects.
`Overview <https://wikis.cern.ch/display/DEV/PyDM+vs+Inspector#PyDMvsInspector-WidgetComparison>`__.


.. note:: If you would like to request the implementation of a new widget, or share your own implementation,
          you can do so, in the `Community Widgets <https://wikis.cern.ch/display/ACCPY/Community+Widgets>`__ page.

.. |livecharts-link| replace:: :doc:`Live Charts <graphs/index>`

.. |lsa-link| replace:: `LSA context selector <https://issues.cern.ch/browse/ACCPY-25>`__

.. |device-sel-link| replace:: `Device selector <https://issues.cern.ch/browse/ACCPY-44>`__

.. |app-frame-link| replace:: `Application frame <https://issues.cern.ch/browse/ACCPY-691>`__

.. |toggle-trigger-link| replace:: `Enable/disable trigger <https://issues.cern.ch/browse/ACCPY-38>`__

.. |lsa-status| replace:: `Contribution by Kevin Li to be reviewed. <https://issues.cern.ch/browse/ACCPY-25>`__

.. |status-led-link| replace:: `Status LED <https://issues.cern.ch/browse/ACCPY-251>`__

.. |propedit-link| replace:: :doc:`PropertyEdit <property_edit/index>`

.. |log-link| replace:: `Log Console <https://issues.cern.ch/browse/ACCPY-29>`__

.. |trim-link| replace:: :ref:`Trim function editor (Editable charts) <widgets/graphs/usage:Edit data using plots>`

.. |timing-link| replace:: :doc:`Timing bar <timing_bar/index>`

.. |spinner-link| replace:: `Spinner (wheel field) <https://issues.cern.ch/browse/ACCPY-32>`__

.. |spinner-status| replace:: `Contribution by Georges Trad to be reviewed. <https://issues.cern.ch/browse/ACCPY-32>`__

.. |led-link| replace:: :doc:`LED <led/index>`

.. |done| replace:: :green:`Available`

.. |na| replace:: N/A

.. |wip| replace:: :blue:`In progress`

.. |livecharts| image:: ../img/live-charts.png

.. |devicesel| image:: ../img/ascdevicecontrolbox.png

.. |toggle-trigger| image:: ../img/ascdiscretecontrol.png

.. |propedit| image:: ../img/propedit.png

.. |trim| image:: ../img/trimeditor.png
   :width: 250px

.. |timing| image:: ../img/timing_bar.png
   :width: 250px

.. |spinner| image:: ../img/wheelfield.gif

.. |led| image:: ../img/led.png


Explore individual widgets
--------------------------

.. toctree::
   :maxdepth: 1

   graphs/index
   property_edit/index
   led/index
   timing_bar/index
   qt/modules