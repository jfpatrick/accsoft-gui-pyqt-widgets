Installation
============

- `Prerequisites`_
- `Specifying dependencies`_
- `Install`_

  * `Using "pip" in virtual environment`_

    - `Using "pip" from CO package index`_
    - `Using "pip" from Gitlab repository`_
    - `Using "pip" from source`_

  * `Specify accwidgets as a dependency for a Python project`_

    - `Stable accwidgets version`_
    - `accwidgets from Gitlab repository`_

  * `Installing outside of "Accelerating Python" environment`_


Prerequisites
-------------

Make sure that you have
`PyQt activated <https://wikis.cern.ch/display/ACCPY/PyQt+distribution#PyQtdistribution-Activationactivation>`__,
so you have a proper "pip" version and access to our package index.

Specifying dependencies
-----------------------

.. note:: It is highly suggested to specify the widgets that are going to be used, as extras during the installation.

This will ensure that widget-specific transitive dependencies are installed. Extras have to be specified
between ``[]`` and can be comma-separated to specify more than one widget, e.g.
``accwidgets[timing_bar,graph]``. Widget specifiers are identical to the subpackage that is imported in code.
For example, when importing

.. code-block:: python

   from accwidgets.log_console import ..

in code, ``log_console`` is the specifier, and will assume installation of ``accwidgets[log_console]``.

It is also possible possible to use a reserved extra ``all-widgets`` to install dependencies for all widgets that are
shipped with the library, i.e. ``accwidgets[all-widgets]``.

.. note:: When ``accwidgets`` is installed without specified extras, only basic transitive dependencies will be
          installed, likely insufficient for all but the simplest widgets.

Most widgets perform a runtime check at the import time to verify that all dependencies are installed. If not,
an :exc:`ImportError` will be triggered, e.g.

.. code-block:: bash

   accwidgets.graph is intended to be used with "pyqtgraph" package. Please specify this widget as an extra of your
   accwidgets dependency, e.g. accwidgets[graph] in order to keep using the widget. To quickly install it in the
   environment, use: 'pip install accwidgets[graph]'.


Install
-------

.. note:: In the following examples, ``<widgets>`` is a placeholder for the specifiers that are described in `Specifying dependencies`_.

Using "pip" in virtual environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is useful when you are just installing the package into a virtual environment via command line interface.

Using "pip" from CO package index
*********************************

.. code-block:: bash

   pip install accwidgets[<widgets>]


Using "pip" from Gitlab repository
**********************************

If you have SSH access:

.. code-block:: bash

   pip install git+ssh://git@gitlab.cern.ch:7999/acc-co/accsoft/gui/accsoft-gui-pyqt-widgets.git#egg=accwidgets[<widgets>]

If you don't have SSH access (requires entering credentials manually):

.. code-block:: bash

   pip install git+https://gitlab.cern.ch/acc-co/accsoft/gui/accsoft-gui-pyqt-widgets.git#egg=accwidgets[<widgets>]

Or if you need a specific branch (same approach for both SSH and HTTPS)

.. code-block:: bash

   pip install git+https://gitlab.cern.ch/acc-co/accsoft/gui/accsoft-gui-pyqt-widgets.git@branch-name#egg=accwidgets[<widgets>]


Using "pip" from source
***********************

.. code-block:: bash

   git clone git+ssh://git@gitlab.cern.ch:7999/acc-co/accsoft/gui/accsoft-gui-pyqt-widgets.git
   cd accsoft-gui-pyqt-widgets
   pip install .[<widgets>]

Specify accwidgets as a dependency for a Python project
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Similarly to above, dependency for the project can be specified to the stable package version from CO package index or
from the Gitlab repository. This chapter presents the formats that are compatible with ``install_requires`` defined
in ``setup.py``, the `setup <https://pythonhosted.org/an_example_pypi_project/setuptools.html>`__ function.

Stable accwidgets version
*************************

It is highly suggested to define version range for the dependencies, to avoid unforeseen breaking if the dependency
updates with breaking changes.

.. code-block:: python

   "accwidgets[<widgets>]>=1.0,<2.0a0"


accwidgets from Gitlab repository
*********************************

The following format is understood by setuptools.

.. note::" This is not compatible with deployed applications and is suitable only for development purposes.

If you have SSH access:

.. code-block:: python

   "accwidgets @ git+ssh://git@gitlab.cern.ch:7999/acc-co/accsoft/gui/accsoft-gui-pyqt-widgets.git#egg=accwidgets[<widgets>]"

If you don't have SSH access (requires entering credentials manually during the installation of your project):

.. code-block:: python

   "accwidgets @ git+https://gitlab.cern.ch/acc-co/accsoft/gui/accsoft-gui-pyqt-widgets.git#egg=accwidgets[<widgets>]"

Or if you need a specific branch (same approach for both SSH and HTTPS)

.. code-block:: python

   "accwidgets @ git+https://gitlab.cern.ch/acc-co/accsoft/gui/accsoft-gui-pyqt-widgets.git@branch-name#egg=accwidgets[<widgets>]"


Installing outside of "Accelerating Python" environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All of the above commands are true without "Accelerating Python" environment, however you need to make
sure that packages can be installed correctly.

1. Make sure you have an updated version of "pip" (standard pip3 v9.* does not handle installs from git):

   .. code-block:: bash

      pip install -U pip

2. Ensure that you have access to acc-py Nexus repository, as described in
   `Getting started with acc-python <https://wikis.cern.ch/display/ACCPY/Getting+started+with+acc-python>`__.

   Namely, you would need to configure "pip" to trust our server, and point to the one of the endpoints, e.g.:

   .. code-block:: bash

      export PIP_TRUSTED_HOST="acc-py-repo.cern.ch"
      export PIP_INDEX_URL="http://acc-py-repo.cern.ch:8081/repository/vr-py-releases/simple/"
      # Call your pip install command here

   or specify package index inside pip command:

   .. code-block:: bash

      pip install --trusted-host acc-py-repo.cern.ch ... --index-url http://acc-py-repo.cern.ch:8081/repository/vr-py-releases/simple/
