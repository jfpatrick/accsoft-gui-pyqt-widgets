API reference
=============

.. automodule:: accwidgets.cycle_selector


.. graphviz::
   :align: center
   :caption: Cycle selector architecture
   :alt: Cycle selector architecture

   digraph hierarchy {
     graph[resolution=93];
     size="5,5"
     node[shape=record,style=filled,fillcolor=gray95];
     edge[dir=back, arrowtail=empty];

     dialog [label="{CycleSelectorDialog|+ value\l+ onlyUsers\l+ allowAllUser\l+ requireSelector\l+ enforcedDomain\l|}"]
     action [label="{CycleSelectorAction|+ value\l+ onlyUsers\l+ allowAllUser\l+ requireSelector\l+ enforcedDomain\l|}"]
     widget [label="{CycleSelector|+ value\l+ onlyUsers\l+ allowAllUser\l+ requireSelector\l+ enforcedDomain\l+ model\l|+ refetch()\l}"]
     model [label="{CycleSelectorModel||+ fetch()\l}"]
     error [label="{CycleSelectorConnectionError||}"]
     value [label="{CycleSelectorValue|+ domain\l+ group\l+ line\l|}"]

     model -> error [arrowtail=none];
     widget -> model [arrowtail=diamond];
     widget -> value [arrowtail=none];
     dialog -> widget [arrowtail=diamond];
     action -> widget [arrowtail=diamond];
   }


.. toctree::
   :maxdepth: 4

   cycleselectormodel
   cycleselector
   cycleselectorvalue
   cycleselectordialog
   cycleselectoraction

CycleSelectorConnectionError
----------------------------

.. autoclass:: accwidgets.cycle_selector.CycleSelectorConnectionError
   :members:
   :undoc-members:
   :show-inheritance:


* :ref:`modindex`
* :ref:`genindex`
