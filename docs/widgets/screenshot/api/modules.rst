API reference
=============

.. automodule:: accwidgets.screenshot


.. graphviz::
   :align: center
   :caption: ScreenshotButton widget architecture
   :alt: ScreenshotButton widget architecture

   digraph hierarchy {
     graph[resolution=90];
     size="5,5"
     node[shape=record,style=filled,fillcolor=gray95];
     edge[dir=back, arrowtail=empty];

     widget [label="{ScreenshotButton|+ model\l+ message\l+ source\l+ includeWindowDecorations\l+ maxMenuDays\l+ maxMenuEntries\l...|+ defaultAction()\l}"]
     action [label="{ScreenshotAction|+ model\l+ message\l+ source\l+ include_window_decorations\l+ max_menu_days\l+ max_menu_entries\l...|+ connect_rbac()\l+ disconnect_rbac()\l}"]
     model [label="{LogbookModel|+ logbook_activities\l|+ reset_rbac_token()\l+ create_logbook_event()\l+ get_logbook_event()\l+ attach_screenshot()\l+ get_logbook_events()\l+ validate()\l}"]

     widget -> action [arrowtail=none];
     action -> model [arrowtail=diamond];
   }


.. toctree::
   :maxdepth: 4

   screenshotbutton
   screenshotaction
   logbookmodel

.. data:: accwidgets.screenshot.ScreenshotSource

   Alias for the possible types of the widgets that can be captured in a screenshot.

.. data:: accwidgets._integrations.RbaButtonProtocol

   Alias for the :class:`~accwidgets.rbac.RbaButton` or API-compatible instances.


* :ref:`modindex`
* :ref:`genindex`