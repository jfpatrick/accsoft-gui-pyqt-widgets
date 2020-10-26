
.. graphviz::
   :align: center
   :caption: PropertyEdit widget architecture
   :alt: PropertyEdit widget architecture

   digraph hierarchy {
     graph[resolution=120];
     size="5,5"
     node[shape=record,style=filled,fillcolor=gray95];
     edge[dir=back, arrowtail=empty];

     widget [label="{PropertyEdit|+ buttons\l+ title\l+ sendOnlyUpdatedValues\l...|+ setValue()\l...}"]
     field [label="{PropertyEditField|+ field\l+ type\l+ editable\l+ label\l+ user_data\l|}"]
     abs_layout_delegate [label="{AbstractPropertyEditLayoutDelegate||+ create_layout()\l+ layout_widgets()\l}"]
     abs_widget_delegate [label="{AbstractPropertyEditWidgetDelegate||+ create_widget()\l+ display_data()\l+ send_data()\l}"]
     layout_delegate [label="{PropertyEditLayoutDelegate||+ create_layout()\l+ layout_widgets()\l}"]
     widget_delegate [label="{PropertyEditWidgetDelegate||+ create_widget()\l+ display_data()\l+ send_data()\l}"]

     abs_layout_delegate -> layout_delegate [style=dashed, arrowtail=onormal];
     abs_widget_delegate -> widget_delegate [style=dashed, arrowtail=onormal];
     widget -> {abs_layout_delegate, abs_widget_delegate} [arrowtail=normal];
     rank=same; widget -> field [arrowtail=diamond];
   }

