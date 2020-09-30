Implementing custom Qt Widgets
==============================

- `The Model/View Pattern`_
- `Qt Bindings`_
- `Qt Designer Plugins`_

  * `Plugin filenames`_
  * `Code organization`_
  * `Defining properties`_
  * `Widget in Qt Designer`_
  * `Context menu plugins`_



The Model/View Pattern
----------------------

Before you start developing a new widget, make sure to be familiar with Qt conventions for a good widget architecture.
Qt Widgets, in general, follow the `Model/View pattern <https://doc.qt.io/qt-5/model-view-programming.html>`__. In
short, widgets are divided into a "Model" that is responsible for data acquisition and storage, and a "View"
responsible for visualizing the data stored in the model, as well as forwarding user's interactions. Following this
architecture, you will make your widget fulfill PyQt developer's expectations, is easier to test, and is also easy to
integrate into other projects, such as `ComRAD
<https://acc-py.web.cern.ch/gitlab/acc-co/accsoft/gui/rad/accsoft-gui-rad-comrad/docs/stable>`__.


Qt Bindings
-----------

Use `qtpy <https://github.com/spyder-ide/qtpy>`__ for importing Qt classes instead of importing them directly from
PyQt5. qtpy is an abstraction layer over PyQt and PySide that allows your code to work, no matter which Qt bindings
the user has installed:

.. code-block:: python

   # instead of
   from PyQt5.QtWidgets import QApplication
   from PyQt5.QtCore import pyqtSignal, pyqtSlot
   # do
   from qtpy.QtWidgets import QApplication
   from qtpy.QtCore import Signal, Slot


Qt Designer Plugins
-------------------

PyQt enables implementation of Qt Designer plugins in Python, while originally they are meant to be written in C++.
For many widgets, it is very useful to provide a widget plugin that allows users to drag-and-drop it in Qt Designer.
`This page <https://wiki.python.org/moin/PyQt/Using_Python_Custom_Widgets_in_Qt_Designer>`__ provides a detailed guide
of creating widget plugins.

Plugin filenames
^^^^^^^^^^^^^^^^

Qt Designer PyQt plugins are subject to specifics of Python import system. It is very important to keep the filenames
of the plugins unique, as otherwise Python import system will cache the first loaded module and won't load others.
This is driven by the fact, that plugins are imported from their containing directory disregarding their path information.

For instance, 2 plugins located in 2 different directories ``/path/to/component1/designer_plugin.py`` and
``/path/to/component2/designer_plugin.py`` will be imported into Qt Designer as "designer_plugin". Thus, depending
which of the 2 paths comes first in the plugin search paths, will have its plugin loaded, while the second plugin will
receive an already loaded plugin.

To avoid name collisions withing :mod:`accwidgets` package, as well as potential collisions with other user plugins, we
follow the convention of naming plugin files as ``accwidgets_<component name>_designer_plugin.py``.


Code organization
^^^^^^^^^^^^^^^^^

Widget plugins must inherit from :class:`QPyDesignerCustomWidgetPlugin`. Your widget class can define Qt signals
and slots to be accessible from the "Signal/Slot editor" in Qt Designer, as well as Qt properties to expose parameters
of your widget to be edited via "Property editor". When done well, widget configuration can be done fully in Qt
Designer, thus reducing the amount of code that the user needs to type in manually.


Defining properties
^^^^^^^^^^^^^^^^^^^

In some cases, you might want to define a property that shouldn't appear in Qt Designer. It is done by setting
``designable`` attribute on the property to :obj:`False`. In derived classes, you can change property's visibility by
redefining it with the different ``designable`` value.

**Creating a hidden property**

.. code-block:: python
   :linenos:

   from qtpy.QtCore import Property

   class MyBaseClass:
       def _get_my_property(self) -> bool:
           # ...

       def _set_my_property(self, new_val: bool):
           # ...

       myProperty: bool = Property(bool, _get_my_property, _set_my_property, designable=False)
       """
       Property description for IDE hints. (note, ": bool" annotation will work only for PyQt
       "Property", not for Python "property".
       """


   class MyDerivedClass(MyBaseClass):

       myProperty: bool = Property(bool, MyBaseClass._get_my_property, MyBaseClass._set_my_property, designable=True)
      """Property description for IDE hints"""

Widget in Qt Designer
^^^^^^^^^^^^^^^^^^^^^

To make your widget blend in well and be easily distinguishable from others, make sure that:

- Each widget has a unique and meaningful **icon**
- Each widget is placed in the appropriate **group**

Context menu plugins
^^^^^^^^^^^^^^^^^^^^

Some properties are more complex than primitive values which makes them hard to use in "Property Editor". Custom
dialogs are a good alternative for such cases and they can be integrated with widget's context menu.

- Implement a subclass of :class:`QPyDesignerTaskMenuExtension` where you define the actions to be added to the task menu
- Implement a subclass of :class:`QExtensionFactory` that instantiates your task menu extension
- Define a :class:`QAction` that will be added to the task menu and shows the dialog on click
- Create your dialog that subclasses :class:`QDialog` and contains everything needed to modify widget properties

**Task Menu Extension (Simplified) Example Code**

.. code-block:: python
   :linenos:

   class MyTaskMenuExtension(QPyDesignerTaskMenuExtension):

       def __init__(self, widget: MyWidget):
           self._widget = widget
           self._my_action = QAction("Edit My Property...")
           self._my_action.triggered.connect(self._launch_editor_dialog)
           self._actions = [self._my_action]

       def _launch_editor_dialog(self):
           dialog = MyEditorDialog(self._widget)
           dialog.exec_()

       def taskActions(self) -> List[QAction]:
           return self._actions


   class MyEditorDialog(QDialog):

       def __init__(self, widget: MyWidget):
           self._widget = widget


   class MyExtensionFactory(QExtensionFactory):

       def createExtension(self, widget: QObject, iid: str, parent: QObject) -> Optional[MyTaskMenuExtension]:
           if not isinstance(widget, MyWidget) or iid != "org.qt-project.Qt.Designer.TaskMenu":
               return None
           return MyTaskMenuExtension(widget)


   class MyWidgetDesignerPlugin(QPyDesignerCustomWidgetPlugin):

       def initialize(self, core: QDesignerFormEditorInterface):
           # ...
           if core.extensionManager():
               core.extensionManager().registerExtensions(
                   MyTaskMenuExtensionFactory(),
                   "org.qt-project.Qt.Designer.TaskMenu"
               )
           # ...
