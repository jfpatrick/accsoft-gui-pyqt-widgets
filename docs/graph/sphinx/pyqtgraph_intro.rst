============
Introduction
============

This package contains widgets for displaying data as graphs. All widgets are
based on the graphics library PyQtGraph.

----------------------
PyQtGraph crash course
----------------------

This graph library is an extension to PyQtGraph which adds some functionality
pure PyQtGraph is missing. Here is a very brief and simple introduction to
important components, which were extended or used in this library.
In short, PyQtGraph is a capable and fast library for graphics and user interfaces
that is using Qt's GraphicsView Framework for drawing.

This quick introduction does by far not cover all of PyQtGraph's features. It
is only here for giving a little bit of context when reading through this documentation.
For a full and much more detailed introduction, have a look at PyQtGraph's
own documentation http://www.pyqtgraph.org/documentation/


Important components
--------------------

The main PyQt widget PyQtGraph offers is called **PlotWidget** which is a subclass
of QWidget. The PlotWidget itself is not yet the component responsible for plotting.
Plotting itself is done on the **PlotItem**, which can be part of a PlotWidget. The
PlotItem is a subclass of Qt's QGraphicsItem and is mainly built from a **ViewBox**,
which is the area data is drawn in, as well as **AxisItems** on all sides that are
connected to the ViewBoxes viewing range. The ViewBox can be moved and scaled
through interaction with the mouse.

Data itself can be represented in different ways controlled by different QGraphicsItem
based classes. The most important one is the **PlotDataItem**, which can represent
x and y data as curves or points. Other data representation classes are for example
the **BarGraphItem**  for bargraphs or the **ErrorBarItem** for error bars. All
of these can be added to a PlotItem's ViewBox to display data in a common scene.
Next to these, it is also possible to add other QGraphicsItem based items to the scene.
Two examples for these are the **InfiniteLineItem**, which allows displaying static
infinite lines and the **TextItem** for displaying Text in a ViewBox, which is not
affected by scaling.


--------
Features
--------

Multi Y Layer Plotting
----------------------

PyQtGraph does not provide proper support for plotting data against different
y axes. This feature is especially handy when plotting datasets with different
y-value ranges. Accgraph does introduce a concept for plotting values against
these different y axes, while keeping the ability to interact with each of the
different y-axes.


Convenience Layer for live data plotting
----------------------------------------

Accgraph provides a special mechanism for plotting live data. This allows easy
displaying of new values without having to store or sort data (when it f.e. older
data arrives from a data logging system) yourself.


Runnable Examples
-----------------

Accgraph comes with runnable examples, which allow exploring the different features
of the library, which show everything in greater detail.