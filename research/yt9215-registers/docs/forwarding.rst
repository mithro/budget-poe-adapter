.. _forwarding:

Forwarding control
==================

This page covers what decides where a frame may go apart from its VLAN: port isolation,
spanning tree states, address learning and the handling of unknown destinations. The registers
are in the :blk:`l2` and :blk:`flood` blocks.

.. _forwarding-isolation:

Port isolation
--------------

:reg:`PORT_ISOLATION` of a port lists the ports that frames received on it must never be sent
to. Setting bit *n* in the register of port *p* blocks the direction from *p* to *n* only.

.. yt-bitfield:: PORT_ISOLATION

Isolation separates ports into groups without VLANs. The table gives the bits to clear in
:reg:`PORT_ISOLATION`; every other bit of the register is set.

.. list-table::
   :header-rows: 1
   :widths: 30 30 20 20

   * - Goal
     - Register of
     - Bits of the group members
     - Bit of the :ref:`CPU port <cpu-tag-port>`
   * - One switch of all ports
     - every port
     - clear
     - clear
   * - Port talks to the CPU port only
     - that port
     - set
     - clear
   * - Group of ports plus the CPU port
     - every member
     - clear
     - clear
   * - CPU port sends only where its tag says
     - the CPU port
     - set
     - set

:lx:`yt921x_userport_standalone` of the :ref:`Linux driver <sources-list>` writes the second
row, :lx:`yt921x_bridge` the third and :lx:`yt921x_port_setup` the fourth. The own bit of a port
blocks hairpin forwarding, the sending of a frame back to the port it
arrived on. :lx:`yt921x_bridge` sets the own bit of a port unless the port is in hairpin
mode.

.. tab-set::

   .. tab-item:: C
      :sync: c

      From :download:`guide.c <../bindings/c/examples/guide.c>`.

      .. literalinclude:: ../bindings/c/examples/guide.c
           :language: c
           :start-after: /* [isolation] */
           :end-before: /* [isolation end] */

   .. tab-item:: MicroPython
      :sync: micropython

      From :download:`guide.py <../bindings/micropython/examples/guide.py>`.

      .. literalinclude:: ../bindings/micropython/examples/guide.py
           :language: python
           :start-after: # [isolation]
           :end-before: # [isolation end]

Isolation is applied after the destination lookup. If the forwarding database knows the
destination on a blocked port, the frame is dropped; it is not flooded to the allowed ports.
A comment in :lx:`yt921x_chip_setup_dsa` states this. It matters when two groups learn into
the same VLAN, because an address learned in one group then hides the same address in the
other. Give each group its own VLAN, with the steps of :ref:`vlan-port-based`, or trap such
frames to the host and forward them there, as :lx:`yt921x_chip_setup_dsa` sets up.

.. _forwarding-stp:

Spanning tree states
--------------------

:reg:`STP` holds a 2-bit state for every port. There are :const:`MSTI_NUM` such registers,
one per spanning tree instance. A VLAN picks its instance with :field:`VLAN_CTRL.STP_ID`, and
a switch with a single spanning tree uses instance 0 only. The
:ref:`state table <forwarding-stp-table>` is the mapping that
:lx:`yt921x_dsa_port_mst_state_set` applies.

.. yt-bitfield:: STP

.. _forwarding-stp-table:

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - `IEEE 802.1D <https://en.wikipedia.org/wiki/IEEE_802.1D>`__ state
     - Value
     - Name
   * - Disabled
     - 0
     - :val:`STP.PORT.DISABLED`
   * - Listening
     - 1
     - :val:`STP.PORT.LEARNING`
   * - Learning
     - 1
     - :val:`STP.PORT.LEARNING`
   * - Blocking
     - 2
     - :val:`STP.PORT.BLOCKING`
   * - Forwarding
     - 3
     - :val:`STP.PORT.FORWARD`

.. _forwarding-learning:

Address learning
----------------

The switch learns the source address of received frames into the forwarding database by
itself. :reg:`PORT_LEARN` controls this per port.

.. list-table::
   :header-rows: 1
   :widths: 40 36 24

   * - Goal
     - Field to set
     - :ref:`Evidence <evidence>`
   * - No learning on a port
     - :field:`PORT_LEARN.DIS`
     - :ev:`confirmed`
   * - Limit the number of learned addresses
     - :field:`PORT_LEARN.LIMIT`
     - :ev:`inferred`
   * - Limit the number of learned addresses
     - :field:`PORT_LEARN.LIMIT_EN`
     - :ev:`inferred`
   * - Drop frames from addresses over the limit
     - :field:`PORT_LEARN.DROP_ON_EXCEEDED`
     - :ev:`inferred`
   * - No learning in one VLAN
     - :field:`VLAN_CTRL.LEARN_DIS`
     - :ev:`confirmed`

:lx:`yt921x_bridge_flags` sets :field:`PORT_LEARN.DIS` and :lx:`yt921x_chip_setup_dsa` sets
:field:`VLAN_CTRL.LEARN_DIS`. The :ev:`inferred` rows follow the field names in :lx:`chip.h`.
Learned entries age out after the time in :reg:`AGEING`, which :ref:`fdb-ageing` describes.

.. _forwarding-flood:

Unknown destinations
--------------------

When the destination address is not in the forwarding database, two sets of registers decide
what happens.

The :ref:`register table <forwarding-flood-registers>` names the two sets. An action
register chooses, per receiving port, one of the four actions of the
:ref:`action table <forwarding-flood-actions>`. :reg:`ACT_UNK_MCAST` has the same four values
as :reg:`ACT_UNK_UCAST`.

.. _forwarding-flood-registers:

.. list-table::
   :header-rows: 1
   :widths: 34 33 33

   * - Frame
     - Action register
     - Flood filter register
   * - Unknown unicast
     - :reg:`ACT_UNK_UCAST`
     - :reg:`FILTER_UNK_UCAST`
   * - Unknown multicast
     - :reg:`ACT_UNK_MCAST`
     - :reg:`FILTER_UNK_MCAST`
   * - Any multicast
     - none
     - :reg:`FILTER_MCAST`
   * - Broadcast
     - none
     - :reg:`FILTER_BCAST`

.. _forwarding-flood-actions:

.. list-table::
   :header-rows: 1
   :widths: 10 34 28 28

   * - Value
     - Name
     - Frame is flooded
     - Frame is sent to the CPU
   * - 0
     - :val:`ACT_UNK_UCAST.ACT.FORWARD`
     - yes
     - no
   * - 1
     - :val:`ACT_UNK_UCAST.ACT.TRAP`
     - no
     - yes
   * - 2
     - :val:`ACT_UNK_UCAST.ACT.DROP`
     - no
     - no
   * - 3
     - :val:`ACT_UNK_UCAST.ACT.COPY`
     - yes
     - yes

A flooded frame goes to the ports that the flood filter register of its kind allows.

.. warning::

   The CPU tag carries the same :ref:`code <cpu-tag-codes>` for a trapped and for a copied
   unknown frame. A host that forwards trapped frames itself must not use
   :val:`ACT_UNK_UCAST.ACT.COPY` or :val:`ACT_UNK_MCAST.ACT.COPY`, or those frames are sent
   twice. A comment in :lx:`yt921x_tag_rcv` states this.

A set bit in a filter register keeps flooded frames of that kind away from the port. This polarity
is :ev:`inferred` from the word "filter" in the register names. The only value that the
:ref:`Linux driver <sources-list>` writes, ``0x7ff`` in :lx:`yt921x_chip_setup_dsa` together with
trapping every unknown frame, is consistent with it.

.. yt-bitfield:: ACT_UNK_UCAST

The :ref:`configuration table <forwarding-flood-config>` gives the register values for a
switch that floods by itself and for a host that forwards unknown frames in software.

.. _forwarding-flood-config:

.. list-table::
   :header-rows: 1
   :widths: 28 22 25 25

   * - Register
     - Element
     - Hardware switch
     - Host forwards unknown frames
   * - :reg:`ACT_UNK_UCAST`
     - Ordinary ports
     - :val:`ACT_UNK_UCAST.ACT.FORWARD`
     - :val:`ACT_UNK_UCAST.ACT.TRAP`
   * - :reg:`ACT_UNK_UCAST`
     - CPU port
     - :val:`ACT_UNK_UCAST.ACT.FORWARD`
     - :val:`ACT_UNK_UCAST.ACT.DROP`
   * - :reg:`ACT_UNK_MCAST`
     - Ordinary ports
     - :val:`ACT_UNK_MCAST.ACT.FORWARD`
     - :val:`ACT_UNK_MCAST.ACT.TRAP`
   * - :reg:`ACT_UNK_MCAST`
     - CPU port
     - :val:`ACT_UNK_MCAST.ACT.FORWARD`
     - :val:`ACT_UNK_MCAST.ACT.DROP`
   * - :reg:`FILTER_UNK_UCAST`
     - Whole register
     - 0
     - ``0x7ff``
   * - :reg:`FILTER_UNK_MCAST`
     - Whole register
     - 0
     - ``0x7ff``

The column "Host forwards unknown frames" is :ev:`confirmed` by
:lx:`yt921x_chip_setup_dsa`: every unknown frame is trapped to the host, which floods it in
software to the right group of ports. The column "Hardware switch" lets the switch flood by
itself, within the limits of :ref:`port isolation <forwarding-isolation>`. It is
:ev:`inferred` from the meaning of :val:`ACT_UNK_UCAST.ACT.FORWARD` and from the filter
polarity.
