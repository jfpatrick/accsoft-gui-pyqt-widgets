# AccSoft Plotting Widgets

Goal of this repository is to create new Widgets based on PyQtGraph that meet the special plotting needs mentioned in the [Requirements](https://wikis.cern.ch/display/ACCPY/Charting+libraries#Chartinglibraries-Featurewishlist) and more.

## Installation
Dependencies that are mandatory for using the library are listed in [requirements.txt](../../accwidgets/graph/requirements.txt). Dependencies that are necessary for development and executing tests are listed in [dev_requirements.txt](../../accwidgets/graph/dev_requirements.txt). They will be collected automatically by [setup.py](../../setup.py) and don't have to be installed by hand. Refer to the [README.md](../../README.md) for installation.


## Components of this Project
The project is mainly divided into two parts. The first are the Widgets, that implement the graphical user interface that can be included in an PyQt based application. The second one handles the connection between the widgets and their sources for data and timing as well as the datamodel that is used to save the data. Changes between them are simply published with Qt's Signal Slot mechanism.

## Testing
The package is tested using **pytest** in combination with the plugin **pytest-qt**. For execution run `python -m pytest`.

## Usage
Usage examples for different use cases and examples for updating the graph are provided in the examples folder.

## Additional features compared to pure PyQtGraph

### Live-Data Plotting

One big feature that differentiates this library the easy-to-use Live-Data plotting capabilities without having to handle the saving and sorting of data by its timestamps yourself. The data can be displayed in to different styles, in a Scrolling and a Sliding Pointer format explained below.  

![Sliding Pointer Widget](./img/Live_Plotting.png?raw=true "Sliding Pointer Widget")

#### Style I: Sliding Pointer
The data is drawn in an fixed cycle. When the data reaches the cycle end, it starts overdrawing itself starting from the cycle start again. 

![Sliding Pointer Widget](./img/SlidingPointerWidget.png?raw=true "Sliding Pointer Widget")

#### Style II: Scrolling Plot
As new data gets available, it is appended on the right site of the screen. The graph shows a fixed range of time from (currenttime - cyclesize) to currenttime.

![Scrolling Plot Widget](./img/ScrollingPlotWidget.png?raw=true "Scrolling Plot Widget")


### Multi Y Axises in one Plot

Compared to pure PyQtGraph this library offers convenient functionality for adding multiple Y axes to your plot and displaying data in it. Each Y axis can have its own range that can also be moved individually and simultaneously while viewing the data.

![Scrolling Plot Widget](./img/MultiLayer.png?raw=true "Multiple Y axises")