
By default, widget contacts production environment of CCDB. When alternative requirements are required, such as TEST,
it is possible to configure that via ``PYCCDA_HOST`` environment variable, since the widget uses :mod:`pyccda`
underneath to perform the requests, e.g.

.. code-block:: bash

   # This corresponds to the "TEST" CCDA endpoint
   export PYCCDA_HOST=https://ccda-test.cern.ch:8902/api
