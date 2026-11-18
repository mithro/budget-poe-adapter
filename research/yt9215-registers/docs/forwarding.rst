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

Isolation is how ports are separated into groups without VLANs:

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Goal
     - :reg:`PORT_ISOLATION` of each port
   * - One switch of all ports
     - 0
   * - Port talks to the CPU port only
     - All ports except the CPU port
   * - Group of ports plus the CPU port
     - All ports except the other members of the group and the CPU port
   * - CPU port sends only where its tag says
     - All ports

A port's own bit makes no difference, because a frame never leaves on the port it arrived on.

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
This matters when two groups learn into the same VLAN, because an address learned in one group
then hides the same address in the other. Give each group its own VLAN, as in
:ref:`vlan-port-based`, or have the host forward such frames as the :ref:`Linux driver <sources-list>` does.

.. _forwarding-stp:

Spanning tree states
--------------------

:reg:`STP` holds a 2-bit state for every port. There are :const:`MSTI_NUM` such registers,
one per spanning tree instance; a VLAN picks its instance with :field:`VLAN_CTRL.STP_ID`, and
a switch with a single spanning tree uses instance 0 only.

.. yt-bitfield:: STP

.. list-table::
   :header-rows: 1
   :widths: 14 22 64

   * - Value
     - Name
     - Use for the 802.1D state
   * - 0
     - :val:`STP.PORT.DISABLED`
     - Disabled
   * - 1
     - :val:`STP.PORT.LEARNING`
     - Listening and learning
   * - 2
     - :val:`STP.PORT.BLOCKING`
     - Blocking
   * - 3
     - :val:`STP.PORT.FORWARD`
     - Forwarding

.. _forwarding-learning:

Address learning
----------------

The switch learns the source address of received frames into the forwarding database by
itself. :reg:`PORT_LEARN` controls this per port:

.. list-table::
   :header-rows: 1
   :widths: 36 64

   * - Goal
     - Field to set
   * - No learning on a port
     - :field:`PORT_LEARN.DIS`
   * - Limit the number of learned addresses
     - :field:`PORT_LEARN.LIMIT`
   * -
     - :field:`PORT_LEARN.LIMIT_EN`
   * - Drop frames from new addresses beyond the limit
     - :field:`PORT_LEARN.DROP_ON_EXCEEDED`
   * - No learning in one VLAN
     - :field:`VLAN_CTRL.LEARN_DIS`

:field:`PORT_LEARN.DIS` and :field:`VLAN_CTRL.LEARN_DIS` are confirmed by the :ref:`Linux driver <sources-list>`;
the other fields are inferred from their names. Learned entries age out after the time in
:reg:`AGEING`, counted in units of 5 seconds; see :ref:`fdb-ageing`.

.. _forwarding-flood:

Unknown destinations
--------------------

When the destination address is not in the forwarding database, two sets of registers decide
what happens.

The action registers choose, per receiving port, between four actions:

.. list-table::
   :header-rows: 1
   :widths: 12 20 68

   * - Value
     - Name
     - Effect
   * - 0
     - :val:`ACT_UNK_UCAST.ACT.FORWARD`
     - Flood the frame to the ports its flood filter register allows.
   * - 1
     - :val:`ACT_UNK_UCAST.ACT.TRAP`
     - Send the frame to the CPU only.
   * - 2
     - :val:`ACT_UNK_UCAST.ACT.DROP`
     - Discard the frame.
   * - 3
     - :val:`ACT_UNK_UCAST.ACT.COPY`
     - Flood the frame and also send it to the CPU.

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
     -
     - :reg:`FILTER_MCAST`
   * - Broadcast
     -
     - :reg:`FILTER_BCAST`

.. warning::

   The CPU tag carries the same :ref:`code <cpu-tag-codes>` for a trapped and for a copied
   unknown frame. A host that forwards trapped frames itself must not use
   :val:`ACT_UNK_UCAST.ACT.COPY`, or those frames are sent twice. The
   :ref:`Linux driver <sources-list>` states this.

A set bit in a filter register keeps flooded frames of that kind away from the port. This
polarity is inferred from the register names and from the values the :ref:`Linux driver <sources-list>` writes.

.. yt-bitfield:: ACT_UNK_UCAST

There are two usual configurations:

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

The host-forwarding column is confirmed by the :ref:`Linux driver <sources-list>`: every unknown frame is trapped
to the host, which floods it in software to the right group of ports. The hardware-switch
column lets the switch flood by itself, within the limits of
:ref:`port isolation <forwarding-isolation>`; it is inferred from the register descriptions.
