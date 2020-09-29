Installation
============

- `Prerequisites`_
- `Install`_

  * `Using "pip" from CO package index`_
  * `Using "pip" from Gitlab repository`_
  * `Using "pip" from source`_
  * `Installing outside of "Accelerating Python" environment`_


Prerequisites
-------------

Make sure that you have
`PyQt activated <https://wikis.cern.ch/display/ACCPY/PyQt+distribution#PyQtdistribution-Activationactivation>`__,
so you have a proper "pip" version and access to our package index.


Install
-------


Using "pip" from CO package index
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   pip install accwidgets


Using "pip" from Gitlab repository
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you have SSH access:

.. code-block:: bash

   pip install git+ssh://git@gitlab.cern.ch:7999/acc-co/accsoft/gui/accsoft-gui-pyqt-widgets.git

If you don't have SSH access (requires entering credentials manually):

.. code-block:: bash

   pip install git+https://gitlab.cern.ch/acc-co/accsoft/gui/accsoft-gui-pyqt-widgets.git

Or if you need specific branch (same approach for both SSH and HTTPS)

.. code-block:: bash

   pip install git+https://gitlab.cern.ch/acc-co/accsoft/gui/accsoft-gui-pyqt-widgets.git@branch-name


Using "pip" from source
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   git clone git+ssh://git@gitlab.cern.ch:7999/acc-co/accsoft/gui/accsoft-gui-pyqt-widgets.git
   cd accsoft-gui-pyqt-widgets
   pip install .


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
