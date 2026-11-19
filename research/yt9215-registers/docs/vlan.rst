.. _vlan:

VLANs
=====

The switch implements `IEEE 802.1Q <https://en.wikipedia.org/wiki/IEEE_802.1Q>`__ VLANs with a
table of 4096 entries. The registers are in the :blk:`vlan` block. The :ref:`register overview <vlan-overview-table>` names the register for each setting.

.. _vlan-overview-table:

.. list-table::
   :header-rows: 1
   :widths: 44 28 28

   * - Setting
     - Register
     - Section
   * - Identifiers that mark a tag
     - :reg:`TPID_IGR`
     - :ref:`vlan-aware`
   * - Tags that a port recognises
     - :reg:`PORT_IGR_TPID`
     - :ref:`vlan-aware`
   * - VLAN of an untagged frame
     - :reg:`PORT_VLAN_CTRL`
     - :ref:`vlan-pvid`
   * - Frames that a port refuses by tag
     - :reg:`PORT_VLAN_CTRL1`
     - :ref:`vlan-filter`
   * - Ports that check VLAN membership
     - :reg:`VLAN_IGR_FILTER`
     - :ref:`vlan-filter`
   * - Member ports of a VLAN
     - :reg:`VLAN_CTRL`
     - :ref:`vlan-table`
   * - Members that send without a tag
     - :reg:`VLAN_CTRL`
     - :ref:`vlan-egress`
   * - Identifier that a port sends
     - :reg:`PORT_EGR`
     - :ref:`vlan-egress`
   * - Identifiers that can be sent
     - :reg:`TPID_EGR`
     - :ref:`vlan-egress`
   * - Ports that send to members only
     - :reg:`VLAN_EGR_FILTER`
     - :ref:`vlan-egress`

The switch knows two kinds of tag. The customer tag is the ordinary tag of
`IEEE 802.1Q <https://en.wikipedia.org/wiki/IEEE_802.1Q>`__. The
service tag is the outer tag of `IEEE 802.1ad <https://en.wikipedia.org/wiki/IEEE_802.1ad>`__. A
plain
`IEEE 802.1Q <https://en.wikipedia.org/wiki/IEEE_802.1Q>`__ set-up uses customer tags only.

.. _vlan-aware:

VLAN-aware and VLAN-unaware ports
---------------------------------

It is :ev:`inferred` from the name of :reg:`TPID_IGR` that it holds four tag protocol
identifiers. :reg:`PORT_IGR_TPID` says, for each port,
which of the four mark a customer tag and which mark a service tag.

.. yt-bitfield:: PORT_IGR_TPID

.. _vlan-aware-table:

.. list-table::
   :header-rows: 1
   :widths: 22 30 24 24

   * - Port behaviour
     - Field written with 1
     - VLAN of a tagged frame
     - Priority bits of the tag
   * - VLAN-aware
     - :field:`PORT_IGR_TPID.CTAG`
     - VLAN ID of the tag
     - read
   * - VLAN-unaware
     - :field:`PORT_IGR_TPID.STAG`
     - :ref:`port VLAN ID <vlan-pvid>`
     - read

The value 1 sets element 0 of the field. It is :ev:`inferred` from the names that element 0
stands for the identifier in element 0 of :reg:`TPID_IGR`. Both rows of the :ref:`mode table <vlan-aware-table>` are :ev:`confirmed` by
:lx:`yt921x_vlan_aware_set`. Its comment says that the VLAN-unaware setting works although :field:`VLAN_CTRL.SVLAN_EN` is never set.

Write ``0x8100`` to element 0 of :reg:`TPID_IGR` before the first frame arrives. The
:ref:`Linux driver <sources-list>` never writes :reg:`TPID_IGR`, so it is :ev:`inferred` that
the element holds ``0x8100`` after reset.

.. _vlan-pvid:

Port VLAN ID
------------

A frame without a customer tag joins the VLAN in :field:`PORT_VLAN_CTRL.CVID`, the port VLAN
ID. :lx:`yt921x_port_set_pvid` writes the field. :ref:`vlan-zero` describes the handling of a frame
tagged with VLAN ID 0.

.. yt-bitfield:: PORT_VLAN_CTRL

Give a VLAN-unaware port a port VLAN ID that no tagged traffic uses.
:lx:`yt921x_vlan_filtering` uses :lx:`4095 <chip.c:82>` for such a port.

.. _vlan-filter:

Ingress filtering
-----------------

.. _vlan-filter-table:

.. list-table::
   :header-rows: 1
   :widths: 34 44 22

   * - Frames to drop
     - Field to set
     - :ref:`Evidence <evidence>`
   * - VLAN does not include the receiving port
     - :field:`VLAN_IGR_FILTER.PORT`
     - :ev:`confirmed`
   * - Untagged
     - :field:`PORT_VLAN_CTRL1.CVLAN_DROP_UNTAGGED`
     - :ev:`confirmed`
   * - Tagged
     - :field:`PORT_VLAN_CTRL1.CVLAN_DROP_TAGGED`
     - :ev:`confirmed`

:lx:`yt921x_vlan_filtering` sets the fields of the rows "VLAN does not include the receiving
port" and "Untagged" of the :ref:`filter table <vlan-filter-table>`. It sets :field:`PORT_VLAN_CTRL1.CVLAN_DROP_UNTAGGED` for a VLAN-aware
port that has no port VLAN. It always clears :field:`PORT_VLAN_CTRL1.CVLAN_DROP_TAGGED`, and
its comment leaves the dropping of tagged frames to :reg:`VLAN_IGR_FILTER`. The :ref:`Linux driver <sources-list>`
therefore :ev:`confirms <confirmed>` the field only by clearing it; the effect of setting it is
:ev:`inferred` from its name. An access port is a use for it.

.. _vlan-table:

VLAN table
----------

:reg:`VLAN_CTRL` has one 64-bit entry per VLAN ID.

.. yt-bitfield:: VLAN_CTRL

A basic VLAN needs two fields. :field:`VLAN_CTRL.PORTS` holds the member ports.
:field:`VLAN_CTRL.UNTAG_PORTS` holds the members that send the frames of the VLAN without a
tag. :lx:`yt921x_vlan_add` sets both and :lx:`yt921x_vlan_del` clears both. Include the
:ref:`CPU port <cpu-tag-port>` in the members if the host is to see the VLAN. The entry is
two words. Write the low word first, as :ref:`access-wide` explains.

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

The :ref:`field table <vlan-table-fields>` lists the other fields of the entry that the guide
uses.

.. _vlan-table-fields:

.. list-table::
   :header-rows: 1
   :widths: 34 33 33

   * - Field
     - Content
     - Section
   * - :field:`VLAN_CTRL.STP_ID`
     - Spanning tree instance
     - :ref:`forwarding-stp`
   * - :field:`VLAN_CTRL.LEARN_DIS`
     - Address learning off
     - :ref:`forwarding-learning`
   * - :field:`VLAN_CTRL.FID`
     - Filtering ID
     - :ref:`sources-open`
   * - :field:`VLAN_CTRL.PRIO`
     - Priority of the VLAN
     - :ref:`qos-sources`
   * - :field:`VLAN_CTRL.METER_ID`
     - Meter of the VLAN
     - :ref:`rate-meter`

.. _vlan-zero:

VLAN 0
~~~~~~

It is :ev:`inferred` that the switch looks up a tag with VLAN ID 0 in entry 0 of
:reg:`VLAN_CTRL`, because the :ref:`Linux driver <sources-list>` writes that entry. Write entry 0 once
at start-up with all ports in :field:`VLAN_CTRL.PORTS` and with :field:`VLAN_CTRL.LEARN_DIS`
set, and use VLAN 0 for nothing else. :lx:`yt921x_chip_setup_dsa` writes this entry. Its
:lx:`comment <chip.c:2334>` says that a frame tagged with VLAN ID 0 should be treated as
untagged and that this "confuses the hardware a lot".

.. _vlan-egress:

Egress
------

A frame leaves with a customer tag unless the sending port is in :field:`VLAN_CTRL.UNTAG_PORTS` of
its VLAN. :lx:`yt921x_vlan_add` :ev:`confirms <confirmed>` this field. No function of the
:ref:`Linux driver <sources-list>` uses the registers of the
:ref:`tag register table <vlan-egress-table>`, so their functions are :ev:`inferred` from their names
and from the names of the :ref:`vendor SDK <sources-list>` tables at the same addresses.

.. _vlan-egress-table:

.. list-table::
   :header-rows: 1
   :widths: 22 14 42 22

   * - Register
     - Direction
     - Function
     - :ref:`Vendor SDK <sources-list>` table
   * - :reg:`TPID_EGR`
     - egress
     - Four tag protocol identifiers to send
     - :sdk:`EGR_TPID_PROFILE`
   * - :reg:`PORT_EGR`
     - egress
     - Choice among the four for each port
     - :sdk:`EGR_PORT_CTRLN`
   * - :reg:`VLAN_EGR_FILTER`
     - egress
     - Ports that send to member ports only
     - :sdk:`L2_EGR_VLAN_FILTER_EN`
   * - :reg:`PVID_SEL`
     - ingress
     - Ports that classify by the service tag
     - :sdk:`LOOK_UP_VLAN_SEL`

It is :ev:`inferred` from the name of :field:`PORT_EGR.TPID_CTAG` that the field chooses the
identifier of the customer tag.

.. _vlan-port-based:

Port-based VLANs
----------------

The steps split the ports into groups that cannot see each other, without any tag on the
wire.

1. Pick an unused VLAN ID for each group.
2. Write the :reg:`VLAN_CTRL` entry of that ID with the ports of the group and the
   :ref:`CPU port <cpu-tag-port>` in both :field:`VLAN_CTRL.PORTS` and
   :field:`VLAN_CTRL.UNTAG_PORTS`.
3. Set :field:`PORT_VLAN_CTRL.CVID` of every port of the group to that ID.
4. Leave the ports :ref:`VLAN-unaware <vlan-aware-table>`.

Each group then learns addresses under its own VLAN ID, which avoids the lookup problem
that :ref:`forwarding-isolation` describes. Every field of the steps is :ev:`confirmed`, but
the :ref:`Linux driver <sources-list>` does not use this combination, and
:ref:`no code of this manual has run on hardware <sources-open>`.
