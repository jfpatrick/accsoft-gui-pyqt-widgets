# ACCSoft GUI PyQt Widgets

[![pipeline status](https://gitlab.cern.ch/acc-co/accsoft/gui/accsoft-gui-pyqt-widgets/badges/develop/pipeline.svg)](https://gitlab.cern.ch/acc-co/accsoft/gui/accsoft-gui-pyqt-widgets/pipelines)
[![coverage report](https://gitlab.cern.ch/acc-co/accsoft/gui/accsoft-gui-pyqt-widgets/badges/develop/coverage.svg)](https://gitlab.cern.ch/acc-co/accsoft/gui/accsoft-gui-pyqt-widgets/pipelines)

## Installation
For installation this package execute `pip install .` This will install the all necessary dependencies along with this package. All dependencies are collected in [setup.py](./setup.py) Dependencies for each package are collected inside their folder in **requirements.txt** files, which get collected and added on execution of the setup.

Dependencies for development like testing-frameworks, that are not necessary for execution, are collected separately in **dev_requirements.txt** files along the user dependencies. To install them run `pip install .[testing]`. They will be collected in the same way as the user requirements, but not installed unless you run the mentioned command.

For adding new dependencies in an own package, add the requirement text files, if necessary and add your package-name in [setup.py](./setup.py), so the setup knows where to look for dependencies.

## Extended PyQtGraph PlotWidget
The goal of the Extended PyQtGraph PlotWidget is to provide an version of PyQtGraph's [PlotWidget](http://www.pyqtgraph.org/documentation/widgets/plotwidget.html?highlight=plotwidget) that provides additional ways of plotting data described in the [Requirements](https://wikis.cern.ch/display/ACCPY/Charting+libraries#Chartinglibraries-Featurewishlist) and is supporting PYDMs channel mechanism for updates. The Widget can either be used directly in a PyQt Application or as a plugin through QtDesigner. More details can be found in the [project](accwidgets/graph) itself.
