API reference
=============

.. automodule:: accwidgets.rbac


.. graphviz::
   :align: center
   :caption: RbaButton widget architecture
   :alt: RbaButton widget architecture

   digraph hierarchy {
     graph[resolution=130];
     size="5,5"
     node[shape=record,style=filled,fillcolor=gray95];
     edge[dir=back, arrowtail=empty];

     widget [label="{RbaButton|+ model\l...|}"]
     model [label="{RbaButtonModel|+ token\l|+ update_token()\l+ logout()\l+ login_by_location()\l+ login_explicitly()\l...}"]
     token [label="{RbaToken|+ roles\l+ username\l+ login_method\l+ location\l+ valid\l+ serial_id\l+ auth_timestamp\l+ app_name\l...|+ get_encoded()\l}"]
     role [label="{RbaRole|+ name\l+ lifetime\l+ active\l+ is_critical\l|}"]

     widget -> model [arrowtail=diamond];
     model -> token [arrowtail=diamond];
     token -> role [arrowtail=odiamond];
   }


.. toctree::
   :maxdepth: 4

   rbabutton
   rbabuttonmodel
   rbatoken
   rbarole

* :ref:`modindex`
* :ref:`genindex`