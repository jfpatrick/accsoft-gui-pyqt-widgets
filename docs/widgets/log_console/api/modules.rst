API reference
=============

.. automodule:: accwidgets.log_console


.. graphviz::
   :align: center
   :caption: LogConsole widget architecture
   :alt: LogConsole widget architecture

   digraph hierarchy {
     node[shape=record,style=filled,fillcolor=gray95];
     edge[dir=back, arrowtail=empty];

     widget [label="{LogConsole|+ formatter\l+ model\l+ frozen\l+ expanded\l+ collapsible\l|+ clear()\l+ freeze()\l+ unfreeze()\l+ toggleFreeze()\l+ toggleExpandedMode()\l...}"]
     dock [label="{LogConsoleDock|+ console\l|...}"]
     record [label="{LogConsoleRecord|+ logger_name\l+ message\l+ level\l+ timestamp\l+ millis\l|}"]
     abs_fmt [label="{AbstractLogConsoleFormatter||+ format()\l+ create()\l+ configurable_attributes()\l}"]
     abs_model [label="{AbstractLogConsoleModel|+ all_records\l+ frozen\l+ buffer_size\l+ visible_levels\l+ selected_logger_levels\l+ available_logger_levels\l+ level_notice\l|+ clear()\l+ freeze()\l+ unfreeze()\l}"]
     fmt [label="{LogConsoleFormatter||+ format()\l+ configurable_attributes()\l...}"]
     model [label="{LogConsoleModel|+ all_records\l+ frozen\l+ buffer_size\l+ visible_levels\l+ selected_logger_levels\l+ level_notice\l+ level_changes_modify_loggers\l...|+ clear()\l+ freeze()\l+ unfreeze()\l...}"]
     level [label="{LogLevel|...|+ level_name()\l+ real_levels()\l}"]

     widget -> abs_model [arrowtail=diamond];
     dock -> widget [arrowtail=diamond];
     abs_model -> model [style=dashed, arrowtail=onormal];
     abs_model -> record [arrowtail=odiamond];
     abs_model -> level [arrowtail=none];
     abs_fmt -> record [arrowtail=normal];
     widget -> abs_fmt [arrowtail=normal];
     abs_fmt -> fmt [style=dashed, arrowtail=onormal];
   }

.. toctree::
   :maxdepth: 4

   model/modules
   view/modules

* :ref:`modindex`
* :ref:`genindex`
