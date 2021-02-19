PropertyEdit
============

.. image:: ../../img/propertyedit.png

.. note:: To start using this widget, make sure to add ``property_edit`` as a widget specifier, when installing
          accwidgets, or use ``all-widgets``. More on :ref:`install:Specifying dependencies`.

:class:`~accwidgets.property_edit.PropertyEdit` allows interacting with multiple fields of the same property
(as a concept of CERN's device properties), similar to the "Knob" of a
`WorkingSet <https://wikis.cern.ch/display/CTF3OP/WorkingSet>`__. Its main advantage is that it allows writing (or
getting) multiple fields in an atomic way with a single button click.

The widget can display "Get" or "Set" buttons (or both) based on configuration
:attr:`~accwidgets.property_edit.PropertyEdit.buttons`. These buttons trigger corresponding slots:
:attr:`~accwidgets.property_edit.PropertyEdit.valueRequested` and
:attr:`~accwidgets.property_edit.PropertyEdit.valueUpdated`. When no explicit "Get" button is displayed, it can still
receive subscription data via :meth:`~accwidgets.property_edit.PropertyEdit.setValue` slot.

.. note:: This widget only displays data. Communication with the control system has to be done by the user.

By default this component will layout widgets in a form, picking the best matching widget for each of the field types.
However, it is possible to customize both layout and rendered widgets via the delegate system
(:attr:`~accwidgets.property_edit.PropertyEdit.layout_delegate` and
:attr:`~accwidgets.property_edit.PropertyEdit.widget_delegate` respectively). If you are sticking with default "form"
layout, it is possible to modify its margins and alignment properties exposed on
:class:`~accwidgets.property_edit.PropertyEdit` widget directly, e.g.
:attr:`~accwidgets.property_edit.PropertyEdit.formRowWrapPolicy`,
:attr:`~accwidgets.property_edit.PropertyEdit.formLabelAlignment`, etc.

.. note:: Currently this widget does not contact CCDB for device information, thus fields configuration has to be done
          by the user.

Further read
------------

.. toctree::
   :maxdepth: 1

   examples
   api/modules