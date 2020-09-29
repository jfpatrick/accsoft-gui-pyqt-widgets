
Performance Requirements
========================

To view current performance report, refer to `this page <https://wikis.cern.ch/display/DEV/PyQtGraph+Performance+Evaluation>`_.

Currently, we are aware of the following use-cases for charting components:

#. 25 FPS refresh rate. Up to 100k points in a single curve. Should plot up to 8 curves like that. Only one chart per application. (BE-CO-HT)
#. 2D plot with 1000x1000 points at most. Data is viewable offline, therefore refresh rate for the new data is not important. What matters is responsiveness when rendering the static data set. (BE-OP-SPS)
#. Display 3000 datasets on the same chart, 2 hours long each, updating every second. 2 * 3600 * 3000 points. (BE-OP-LHC)

.. note:: If the current solution proves to be inefficient, we shall investigate `QCustomPlot <https://www.qcustomplot.com/>`__
          and plausibility to generate Python bindings with SIP. There have been
          `attempts in the past <https://github.com/dimv36/QCustomPlot-PyQt5>`__, but it is more than 2 years old and needs
          verification if it is still valid.
