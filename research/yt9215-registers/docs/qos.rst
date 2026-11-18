.. _qos:

Priorities
==========

Every frame gets an internal priority from 0 to 7 on receive. The priority selects the
transmit queue and is what the CPU tag reports. The registers are in the :blk:`qos` block.

.. _qos-sources:

Priority sources
----------------

Up to eight sources can supply the priority of a frame. :reg:`PORT_PRIO_ORD` ranks them per
port: each source has a 3-bit weight, and of the sources that apply to a frame the one with
the highest weight wins. Weight 0 turns a source off, except the port default priority (:field:`PORT_QOS.PRIO`), which
then still applies when no other source does.

.. yt-bitfield:: PORT_PRIO_ORD

.. list-table::
   :header-rows: 1
   :widths: 10 22 68

   * - Index
     - Source (:enum:`app_selector`)
     - Priority comes from
   * - 0
     - ``MAC_SA``
     - The forwarding database entry of the source address (:field:`FDB_IN2.PRIO`)
   * - 1
     - ``MAC_DA``
     - The forwarding database entry of the destination address
   * - 2
     - ``VID``
     - The VLAN table entry (:field:`VLAN_CTRL.PRIO`)
   * - 3
     - ``ACL``
     - An ACL rule (:field:`ACL_ACT.PRIO`)
   * - 4
     - ``DSCP``
     - The IP DSCP value, mapped by :reg:`IPM_DSCP`
   * - 5
     - ``CVLAN_PCP``
     - The customer tag priority, mapped by :reg:`IPM_PCP`
   * - 6
     - ``SVLAN_PCP``
     - The service tag priority, mapped by :reg:`IPM_PCP`
   * - 7
     - ``PORT``
     - The port default in :field:`PORT_QOS.PRIO`

To trust DSCP first and the tag priority second, as the Linux driver does for such a request,
give ``DSCP`` weight 7 and both ``CVLAN_PCP`` and ``SVLAN_PCP`` weight 6. The Linux driver uses
only these three sources; the others are described from the names in its header.

.. _qos-maps:

Mapping tables
--------------

:reg:`IPM_DSCP` has one entry per DSCP value and :reg:`IPM_PCP` one per tag priority and drop
eligible bit. Each entry gives the internal priority and a colour that the
:doc:`meters <rate>` use.

.. yt-bitfield:: IPM_PCP

There are two :reg:`IPM_PCP` maps; :field:`PORT_QOS.CVLAN_PRIO_MAP_ID` and
:field:`PORT_QOS.SVLAN_PRIO_MAP_ID` choose the one a port uses for each tag kind. The address
of an entry is ``0x180100 + 64 × map + 32 × dei + 4 × pcp``.

The Linux driver fills the tables once at start-up: every DSCP value gets the priority that
IETF RFC 8325 assigns to it, and every tag priority maps to itself, with colour yellow when
the drop eligible bit is set.

.. _qos-port:

Port default priority
---------------------

Set :field:`PORT_QOS.PRIO` and :field:`PORT_QOS.PRIO_EN` to give all frames of a port one
priority when no better source applies.
