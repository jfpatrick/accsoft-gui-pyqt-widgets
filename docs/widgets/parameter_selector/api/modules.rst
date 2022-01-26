API reference
=============

.. automodule:: accwidgets.parameter_selector


.. graphviz::
   :align: center
   :caption: Parameter selector architecture
   :alt: Parameter selector architecture

   digraph hierarchy {
     graph[resolution=73];
     size="5,5"
     node[shape=record,style=filled,fillcolor=gray95];
     edge[dir=back, arrowtail=empty];

     dialog [label="{ParameterSelectorDialog|+ value\l|}"]
     lineedit [label="{ParameterLineEdit|+ value\l+ enableProtocols\l+ placeholderText\l|+ clear()\l}"]
     delegate [label="{ParameterLineEditColumnDelegate||}"]

     lineedit -> delegate [arrowtail=none];
     dialog -> lineedit [arrowtail=none];
   }


.. toctree::
   :maxdepth: 4

   parameterselectordialog
   parameterlineedit
   parameterlineeditcolumndelegate

* :ref:`modindex`
* :ref:`genindex`
