.. rst_epilog sometimes fails, so we need to include this explicitly, for colors
.. include:: <s5defs.txt>


Graphs
======

The Graph library is based on the pure Python plotting library `PyQtGraph <http://www.pyqtgraph.org/>`__ and extends
it with features inspired by `JDataViewer <https://wikis.cern.ch/display/InCA/JDVE+-+Demos>`__. It uses the coordinate
system based on `PyQtGraph's PlotWidget <http://www.pyqtgraph.org/documentation/plotting.html>`__ but provides a more
convenient API for live data plotting and fixes some of PyQtGraph's quirks.

Features
--------

Implemented features are check-marked.

- |check| Sliding pointer chart (similar to SPS Vistar)
- |check| Scrolling chart (similar to LEIR Vistar)
- |check| Support for different data representations (found in LEIR Vistar): lines, bar graphs, injection bars, timing marks, etc.
- |check| Multiple Y-axes on the same chart.
- |check| Function editor (dragging points up and down in editable chart and apply functions to them) [Based on Contribution by Kevin Li]
- |missing| Improved performance (see :doc:`perf`)
- |missing| Ability to render HDF5 files (currently, matplotlib is being used for this use-case)
- |missing| Polar plot (low priority)


PyQtGraph crash course
----------------------

In short, PyQtGraph is a capable and fast library for graphics and user interfaces
that is using Qt's `GraphicsView Framework <https://doc.qt.io/qt-5/graphicsview.html>`__ for drawing. For complete
documentation on PyQtGraph, visit the `official page <http://www.pyqtgraph.org/documentation/>`__. The main concepts
of PyQtGraph are:

- :class:`~pyqtgraph.PlotWidget`: subclass of :class:`QWidget`, it is not directly responsible for plotting
- :class:`~pyqtgraph.PlotItem`: can be a part of :class:`~pyqtgraph.PlotWidget`. It is a subclass of :class:`QGraphicsItem`
  and defines the primitives being drawn
- :class:`~pyqtgraph.ViewBox`: area where :class:`~pyqtgraph.PlotItem` is drawn in. It can be panned or zoomed through mouse interactions
- :class:`~pyqtgraph.AxisItem`: connected scale representing the :class:`~pyqtgraph.ViewBox`'s visible range

Data can be represented in different ways controlled by different :class:`QGraphicsItem`-based classes. The most
important one is the :class:`~pyqtgraph.PlotDataItem`, which can represent X and Y data as curves or points. Other
data representation types include :class:`~pyqtgraph.BarGraphItem` and :class:`~pyqtgraph.ErrorBarItem`. All of them
can be added to a :class:`~pyqtgraph.ViewBox` to display data in a common scene. In addition, it is possible to add
other :class:`QGraphicsItem`-based items to the scene, for instance, :class:`~pyqtgraph.InfiniteLine`, which allows
displaying static infinite lines and the :class:`~pyqtgraph.TextItem` for displaying static text not affected by scaling
that is placed inside a :class:`~pyqtgraph.ViewBox`.

Further read
------------

.. toctree::
   :maxdepth: 2

   usage
   concepts
   perf
   alt
   api/modules


.. |check| raw:: html

   <input type="checkbox" checked />

.. |missing| raw:: html

   <input type="checkbox" />

