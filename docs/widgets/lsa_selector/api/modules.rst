API reference
=============

.. automodule:: accwidgets.lsa_selector


.. graphviz::
   :align: center
   :caption: LsaSelector widget architecture
   :alt: LsaSelector widget architecture

   digraph hierarchy {
     graph[resolution=160];
     size="5,5"
     node[shape=record,style=filled,fillcolor=gray95];
     edge[dir=back, arrowtail=empty];

     widget [label="{LsaSelector|+ model\l+ accelerator\l+ fetchResidentOnly\l+ contextCategories\l+ hideHorizontalHeader\l+ showNameFilter\l+ showCategoryFilter\l+ selected_context\l...|+ select_user()\l}"]
     model [label="{LsaSelectorModel|+ accelerator\l+ resident_only\l+ categories\l+ filter_title\l+ filter_categories\l+ last_error\l...|+ color()\l+ set_color()\l+ refetch()\l+ find_stored_categories()\l+ connect_table()\l}"]
     acc [label="{LsaSelectorAccelerator|...|}"]
	 role [label="{LsaSelectorColorRole|...|}"]
     ctx [label="{AbstractLsaSelectorContext|+ name\l+ category\l|}"]
     res_ctx [label="{AbstractLsaSelectorResidentContext|+ name\l+ category\l+ user\l|}"]
     nores_ctx [label="{LsaSelectorNonResidentContext|+ name\l+ category\l+ multiplexed\l+ can_become_resident\l|}"]
     ppm_res_ctx [label="{LsaSelectorMultiplexedResidentContext|+ name\l+ category\l+ user\l+ user_type\l|}"]
     noppm_res_ctx [label="{LsaSelectorNonMultiplexedResidentContext|+ name\l+ category\l+ user\l|}"]

     widget -> model [arrowtail=diamond];
     model -> acc [arrowtail=none];
     model -> role [arrowtail=none];
     model -> ctx [arrowtail=odiamond];
     ctx -> res_ctx [style=dashed, arrowtail=onormal];
     ctx -> nores_ctx [style=dashed, arrowtail=onormal];
     res_ctx -> ppm_res_ctx [style=dashed, arrowtail=onormal];
     res_ctx -> noppm_res_ctx [style=dashed, arrowtail=onormal];
   }


.. toctree::
   :maxdepth: 4

   lsaselector
   lsaselectormodel
   lsaselectoraccelerator
   lsaselectormultiplexedresidentcontext
   lsaselectornonmultiplexedresidentcontext
   lsaselectornonresidentcontext
   abstractlsaselectorresidentcontext
   abstractlsaselectorcontext
   lsaselectorcolorrole

* :ref:`modindex`
* :ref:`genindex`