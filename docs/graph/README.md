# PyQtGraph-Extensions

Extensions for PyQtGraph that allow some custom plotting based on PyQtGraphs PlotWidget. Goal of this repository is to create new Widgets based on PyQtGraph that meet the special plotting needs mentioned in the [Requirements](https://wikis.cern.ch/display/ACCPY/Charting+libraries#Chartinglibraries-Featurewishlist)

**Important:** In its current state the project is only implemented on top of PyQtGraph and PyQt and does neither integrate any PyDM features nor a QtDesigner plugin.

## Installation
Dependencies that are mandatory for using the library are listed in [requirements.txt](../../accsoft_gui_pyqt_widgets/graph/requirements.txt). Dependencies that are necessary for development and executing tests are listed in [dev_requirements.txt](../../accsoft_gui_pyqt_widgets/graph/dev_requirements.txt). They will be collected automatically by [setup.py](../../setup.py) and don't have to be installed by hand. Refer to the [README.md](../../README.md) for installation.


## Components of this Project
The project is mainly divided into two parts. The first are the Widgets, that implement the graphical user interface that can be included in an PyQt based application. The second one handles the connection between the widgets and their sources for data and timing. Timing and Data updates are simply published with Qt's Signal Slot mechanism. If a new Timestamp or data-set is available, the Connection class will emit a fitting Signal that can trigger an visual update in the User Interface.

## Testing
The package is tested using **pytest** in combination with the plugin **pytest-qt**. For execution run `pytest`.

## Usage
An [Example](../../examples/graph/graph_example.py) of using the library is provided. [Data](../../accsoft_gui_pyqt_widgets/graph/connection/connection.py) and [Timing](../../accsoft_gui_pyqt_widgets/graph/connection/connection.py) Updates in this example are simulated by QTimer and Random numbers. The display style can be changed by providing a different style in the Extended Plot Widget's constructor. For execution run `python examples/graph/graph_usage_example.py`.

## Supported Display Styles
### Sliding Pointer Widget
The existing curve gets overdrawn as time progresses. The current time is displayed as a vertical line. ![Sliding Pointer Widget](./img/SlidingPointerWidget.png?raw=true "Sliding Pointer Widget")

### Scrolling Plot Widget
As new data gets available, it is appended on the right site of the screen. The graph shows a fixed range of time from (currenttime - cyclesize) to currenttime. Parts of the graph that are located behind the end of this range will be clipped.
![Scrolling Plot Widget](./img/ScrollingPlotWidget.png?raw=true "Scrolling Plot Widget")

### New plotting styles
New plotting styles can be added by adding new implementations of the [ExtendedPlotItem](../../accsoft_gui_pyqt_widgets/graph/widgets/extended_plotitem.py) class
