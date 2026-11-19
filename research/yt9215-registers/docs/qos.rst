.. _qos:

Priorities
==========

It is :ev:`inferred` from the registers of this page that every frame gets an internal
priority from 0 to 7 on receive. The field
:ref:`PRIO <tag-prio>` of the :ref:`CPU tag <cpu-tag-format>` reports it. It is
:ev:`inferred` that the priority selects the transmit queue; the queue registers are among
the :ref:`vendor SDK tables <reference-sdk>` that this manual does not describe. The
registers of this page are in the :blk:`qos` block.

.. _qos-sources:

Priority sources
----------------

Up to eight sources can supply the priority of a frame. :reg:`PORT_PRIO_ORD` ranks them per
port: each source has a 3-bit weight, and it is :ev:`inferred` that of the sources that apply to a
frame the one with the highest weight wins. :lx:`yt921x_dsa_port_set_apptrust` of the
:ref:`Linux driver <sources-list>` gives the most trusted source weight 7 and each next one a
weight that is 1 lower. :lx:`yt921x_port_setup` writes 0 to the register to turn all sources
off. The comment in :lx:`chip.h:208` reads "0: disabled, except PORT_QOS_PRIO", so the port default
priority (:field:`PORT_QOS.PRIO`) still applies with weight 0.

.. yt-bitfield:: PORT_PRIO_ORD

.. _qos-source-table:

.. list-table::
   :header-rows: 1
   :widths: 8 22 30 24 16

   * - Index
     - Source (:enum:`app_selector`)
     - Priority comes from
     - Register that holds it
     - :ref:`Evidence <evidence>`
   * - 0
     - :val:`app_selector.MAC_SA`
     - database entry of the source address
     - :field:`FDB_IN2.PRIO`
     - :ev:`inferred`
   * - 1
     - :val:`app_selector.MAC_DA`
     - database entry of the destination address
     - :field:`FDB_IN2.PRIO`
     - :ev:`inferred`
   * - 2
     - :val:`app_selector.VID`
     - VLAN table entry
     - :field:`VLAN_CTRL.PRIO`
     - :ev:`inferred`
   * - 3
     - :val:`app_selector.ACL`
     - ACL rule
     - :field:`ACL_ACT.PRIO`
     - :ev:`inferred`
   * - 4
     - :val:`app_selector.DSCP`
     - IP DSCP value
     - :reg:`IPM_DSCP`
     - :ev:`confirmed`
   * - 5
     - :val:`app_selector.CVLAN_PCP`
     - customer tag priority
     - :reg:`IPM_PCP`
     - :ev:`confirmed`
   * - 6
     - :val:`app_selector.SVLAN_PCP`
     - service tag priority
     - :reg:`IPM_PCP`
     - :ev:`confirmed`
   * - 7
     - :val:`app_selector.PORT`
     - port default
     - :field:`PORT_QOS.PRIO`
     - :ev:`header`

To trust DSCP first and the tag priority second, give :val:`app_selector.DSCP` weight 7 and
both :val:`app_selector.CVLAN_PCP` and :val:`app_selector.SVLAN_PCP` weight 6. The :ev:`confirmed`
rows of the :ref:`source table <qos-source-table>` are the three sources that
:lx:`yt921x_dsa_port_set_apptrust` writes. The other rows follow the names of the list
:lx:`enum yt921x_app_selector <chip.h:210>`, and the row of :val:`app_selector.PORT` follows the
comment in :lx:`chip.h:218`.

.. _qos-maps:

Mapping tables
--------------

:reg:`IPM_DSCP` has one entry per DSCP value and :reg:`IPM_PCP` one per tag priority and drop
eligible bit. Each entry gives the internal priority in :field:`IPM_PCP.PRIO` and, in
:field:`IPM_PCP.COLOR`, a colour. It is :ev:`inferred` from the field :field:`METER_CTRL.COLOR_BLIND` that the
:ref:`meters <rate-meter>` use this colour.

.. yt-bitfield:: IPM_PCP

There are two :reg:`IPM_PCP` maps. :field:`PORT_QOS.CVLAN_PRIO_MAP_ID` and
:field:`PORT_QOS.SVLAN_PRIO_MAP_ID` choose the one a port uses for each tag kind. No function of the
:ref:`Linux driver <sources-list>` writes the two fields. The
:ref:`vendor SDK <sources-list>` functions
`fal_tiger_qos_intPri_cpri_map_set() <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_qos.c#L148>`__
and
`fal_tiger_qos_intPri_spri_map_set() <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_qos.c#L195>`__
write a fixed map number to them and use it as the index of the map: 0 for the customer tag
and 1 for the service tag. The
reference entry of :reg:`IPM_PCP` gives the address of each map entry.

Fill the tables once at start-up, as :lx:`yt921x_chip_setup_qos` does. That function gives
every DSCP value the priority that the kernel function
`ietf_dscp_to_ieee8021q_tt() <https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/net/core/ieee8021q_helpers.c>`__
assigns to it, which follows `RFC 8325 <https://www.rfc-editor.org/rfc/rfc8325>`__. It maps
every tag priority to itself, with the colour :val:`IPM_PCP.COLOR.YELLOW` when the drop
eligible bit is set, and it writes both :reg:`IPM_PCP` maps alike. It is therefore
:ev:`not known` which map a tag kind uses after reset.

.. _qos-port:

Port default priority
---------------------

Set :field:`PORT_QOS.PRIO` and :field:`PORT_QOS.PRIO_EN` to give all frames of a port one
priority. :lx:`yt921x_dsa_port_set_default_prio` writes the two fields. It is :ev:`inferred`
that a source with a higher weight in :reg:`PORT_PRIO_ORD` takes precedence.
