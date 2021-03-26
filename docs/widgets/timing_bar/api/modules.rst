API reference
=============

.. automodule:: accwidgets.timing_bar


.. graphviz::
   :align: center
   :caption: TimingBar widget architecture
   :alt: TimingBar widget architecture

   digraph hierarchy {
     graph[resolution=120];
     size="5,5"
     node[shape=record,style=filled,fillcolor=gray95];
     edge[dir=back, arrowtail=empty];

     widget [label="{TimingBar|+ model\l+ labels\l+ indicateHeartbeat\l+ highlightedUser\l+ renderSuperCycle\l+ showMicroSeconds\l+ showTimeZone\l+ color_palette\l...|+ showSuperCycle()\l+ hideSuperCycle()\l+ toggleSuperCycle()\l...}"]
     palette [label="{TimingBarPalette|+ text\l+ error_text\l+ active_cycle\l+ inactive_cycle\l+ timing_mark\l+ timing_mark_text\l+ frame\l+ bg_top\l+ bg_bottom\l+ bg_pattern\l+ bg_top_alt\l+ bg_bottom_alt\l+ bg_pattern_alt\l|}"]
     model [label="{TimingBarModel|+ domain\l+ monitoring\l+ current_basic_period\l+ last_info\l+ is_supercycle_mode\l+ supercycle\l+ cycle_count\l+ supercycle_duration\l+ current_cycle_index\l+ has_error\l+ activate\l|+ activate()\l...}"]
     domain [label="{TimingBarDomain|...|}"]

     widget -> model [arrowtail=diamond];
     widget -> palette [arrowtail=normal];
     model -> domain [arrowtail=none];
   }

.. toctree::
   :maxdepth: 4

   model/modules
   view/modules

* :ref:`modindex`
* :ref:`genindex`