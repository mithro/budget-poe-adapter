.. _vlan:

VLANs
=====

The switch implements IEEE 802.1Q VLANs with a full table of 4096 entries. The registers are in
the :blk:`vlan` block. Three things have to be set up: how a port recognises and classifies
tags, what each VLAN contains, and how frames leave.

.. list-table::
   :header-rows: 1
   :widths: 34 33 33

   * - Question
     - Register
     - Section
   * - Which tags does a port recognise?
     - :reg:`TPID_IGR`
     - :ref:`vlan-aware`
   * -
     - :reg:`PORT_IGR_TPID`
     - :ref:`vlan-aware`
   * - Which VLAN does an untagged frame join?
     - :reg:`PORT_VLAN_CTRL`
     - :ref:`vlan-pvid`
   * - Which frames does a port refuse?
     - :reg:`PORT_VLAN_CTRL1`
     - :ref:`vlan-filter`
   * -
     - :reg:`VLAN_IGR_FILTER`
     - :ref:`vlan-filter`
   * - Which ports belong to a VLAN?
     - :reg:`VLAN_CTRL`
     - :ref:`vlan-table`
   * - Does a frame leave with a tag?
     - :reg:`VLAN_CTRL`
     - :ref:`vlan-egress`
   * -
     - :reg:`PORT_EGR`
     - :ref:`vlan-egress`
   * -
     - :reg:`TPID_EGR`
     - :ref:`vlan-egress`
   * -
     - :reg:`VLAN_EGR_FILTER`
     - :ref:`vlan-egress`

The switch knows two kinds of tag, the customer tag (C-tag, the ordinary 802.1Q tag) and the
service tag (S-tag, the outer tag of 802.1ad). A plain 802.1Q setup uses customer tags only.

.. _vlan-aware:

VLAN-aware and VLAN-unaware ports
---------------------------------

:reg:`TPID_IGR` holds four tag protocol identifiers. :reg:`PORT_IGR_TPID` says, for each port,
which of the four mark a customer tag and which a service tag.

.. yt-bitfield:: PORT_IGR_TPID

.. list-table::
   :header-rows: 1
   :widths: 24 30 46

   * - Port behaviour
     - :reg:`PORT_IGR_TPID`
     - Effect
   * - VLAN-aware
     - Element 0 of :field:`PORT_IGR_TPID.CTAG` set
     - A tag with the identifier in element 0 of :reg:`TPID_IGR` selects the VLAN of the frame.
   * - VLAN-unaware
     - Element 0 of :field:`PORT_IGR_TPID.STAG` set
     - The same tag is seen as a service tag. It does not select the VLAN, so every frame
       joins the port VLAN, but its priority bits are still read.

Both rows are confirmed by the :ref:`Linux driver <sources-list>`, which notes that the second works although
:field:`VLAN_CTRL.SVLAN_EN` is never set. Write ``0x8100`` to element 0 of :reg:`TPID_IGR`
first: the :ref:`Linux driver <sources-list>` relies on that value being there after reset, which is not
confirmed.

.. _vlan-pvid:

Port VLAN ID
------------

A frame without a customer tag joins the VLAN in :field:`PORT_VLAN_CTRL.CVID`, the port VLAN
ID. A frame tagged with VLAN ID 0 (a priority tag) should be handled as untagged, but the
switch looks it up in entry 0 of the table; see :ref:`vlan-zero`.

.. yt-bitfield:: PORT_VLAN_CTRL

Give a VLAN-unaware port a port VLAN ID that no tagged traffic uses; the :ref:`Linux driver <sources-list>` uses
4095.

.. _vlan-filter:

Ingress filtering
-----------------

.. list-table::
   :header-rows: 1
   :widths: 44 56

   * - Goal
     - Setting
   * - Drop frames whose VLAN does not include the receiving port
     - Set the port's bit in :field:`VLAN_IGR_FILTER.PORT`
   * - Drop untagged frames (a port with no port VLAN)
     - Set :field:`PORT_VLAN_CTRL1.CVLAN_DROP_UNTAGGED`
   * - Drop tagged frames (an access port)
     - Set :field:`PORT_VLAN_CTRL1.CVLAN_DROP_TAGGED`

The first two settings are confirmed by the :ref:`Linux driver <sources-list>`. It does not use the third and
leaves the dropping of unwanted tagged frames to the membership check, so the third is
inferred from the field name.

.. _vlan-table:

VLAN table
----------

:reg:`VLAN_CTRL` has one 64-bit entry per VLAN ID, at ``0x188000 + 8 × vid``.

.. yt-bitfield:: VLAN_CTRL

For a basic VLAN only two fields matter: :field:`VLAN_CTRL.PORTS`, the member ports, and
:field:`VLAN_CTRL.UNTAG_PORTS`, the members that send the VLAN's frames without a tag. Include
the CPU port in the members if the host is to see the VLAN. The entry is two words; write the
low word first, as :ref:`access-wide` explains.

.. tab-set::

   .. tab-item:: C
      :sync: c

      From :download:`guide.c <../bindings/c/examples/guide.c>`.

      .. literalinclude:: ../bindings/c/examples/guide.c
           :language: c
           :start-after: /* [vlan] */
           :end-before: /* [vlan end] */

   .. tab-item:: MicroPython
      :sync: micropython

      From :download:`guide.py <../bindings/micropython/examples/guide.py>`.

      .. literalinclude:: ../bindings/micropython/examples/guide.py
           :language: python
           :start-after: # [vlan]
           :end-before: # [vlan end]

Other fields of the entry:

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Field
     - Use
   * - :field:`VLAN_CTRL.STP_ID`
     - Spanning tree instance; see :ref:`forwarding-stp`.
   * - :field:`VLAN_CTRL.LEARN_DIS`
     - No address learning in this VLAN; see :ref:`forwarding-learning`.
   * - :field:`VLAN_CTRL.FID`
     - Filtering ID; not used by any public driver.
   * - :field:`VLAN_CTRL.PRIO`
     - Priority of the VLAN; see :ref:`qos-sources`.
   * - :field:`VLAN_CTRL.METER_ID`
     - Meter for the VLAN; see :ref:`rate-meter`.

.. _vlan-zero:

VLAN 0
~~~~~~

The switch does not treat a tag with VLAN ID 0 as "untagged" by itself. Write entry 0 once
at start-up with all ports as members and :field:`VLAN_CTRL.LEARN_DIS` set, and do not use
VLAN 0 otherwise. The :ref:`Linux driver <sources-list>` confirms the need: its comment says such frames otherwise
"confuse the hardware".

.. _vlan-egress:

Egress
------

A frame leaves with a customer tag unless the sending port is in
:field:`VLAN_CTRL.UNTAG_PORTS` of its VLAN. The tag protocol identifier written is one of the
four in :reg:`TPID_EGR`, chosen per port by :field:`PORT_EGR.TPID_CTAG`.
:reg:`VLAN_EGR_FILTER` stops a port from sending frames of VLANs it is not a member of.
:reg:`PVID_SEL` makes a port classify by the service tag instead; it belongs to 802.1ad
setups that no public driver exercises.

Of this section the :ref:`Linux driver <sources-list>` confirms
:field:`VLAN_CTRL.UNTAG_PORTS`. The behaviour of :reg:`TPID_EGR`, :reg:`PORT_EGR`,
:reg:`VLAN_EGR_FILTER` and :reg:`PVID_SEL` is inferred from their names and from the names
the vendor SDK gives the same bits.

.. _vlan-port-based:

Port-based VLANs
----------------

To split the ports into groups that cannot see each other, without any tags on the wire:

1. Pick an unused VLAN ID per group.
2. Write its :reg:`VLAN_CTRL` entry with the group's ports (and the CPU port) in both
   :field:`VLAN_CTRL.PORTS` and :field:`VLAN_CTRL.UNTAG_PORTS`.
3. Set :field:`PORT_VLAN_CTRL.CVID` of every port of the group to that ID.
4. Leave the ports VLAN-unaware, or make them VLAN-aware and set
   :field:`PORT_VLAN_CTRL1.CVLAN_DROP_TAGGED`.

Each group then learns addresses under its own VLAN ID, which avoids the lookup problem
described in :ref:`forwarding-isolation`. The steps use only registers the :ref:`Linux driver <sources-list>`
exercises, but this combination has not been run on hardware by this project.
