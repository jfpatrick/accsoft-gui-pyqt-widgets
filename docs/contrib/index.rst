For contributors
================

This chapter will guide you through everything you need to know to contribute your widgets to the library by
showing you the structure of the repository and the process of integrating your changes.

**Sharing is caring** and we encourage sharing with Acc-Py community! However, make sure your widgets are not
too specific for your scenario, otherwise you might be better off providing your own repository. With such independent
repositories, feel free to advertise them to the community on the
`Community Widgets wiki page <https://wikis.cern.ch/display/ACCPY/Community+Widgets>`__.

Good widget checklist
---------------------

- **Implementation:** widget can be used in any PyQt application and follows Qt conventions
- **Tests:** Your widget is properly tested and can be relied on. Ensure good test coverage with `pytest-cov <https://pypi.org/project/pytest-cov/>`__
- **Documentation:**

  * **Docstrings:** Your widget and its public APIs are documented properly, with description of classes, methods,
    public variables, method arguments and method return values
  * **Type-Hints:** All public APIs are fully typed (method arguments, return types, public variables)
  * **Conceptual Documentation:** Document concepts and design decisions of your widget for the auto-generated documentation

- **Plugin for Qt Designer**, that allows including your widgets in forms created using Qt Designer.

  * **Properties:** All major parameters of your widget should be configurable via "Property Editor" (or task menu extension, if necessary)
  * **Group:** The widget is placed in an appropriate group in "Widget Box"
  * **Icon:** Your widget is much easier to locate in "Widget Box" and "Object Inspector" if it has a unique icon

- **Interactive Examples:** Teach newcomers by providing Python snippets that showcase the usage of your widget

The following chapters will guide you through fulfilling these requirements in more detail.

Other topics
------------

.. toctree::
   :titlesonly:

   hierarchy
   custom_widgets
   guidelines
   submit