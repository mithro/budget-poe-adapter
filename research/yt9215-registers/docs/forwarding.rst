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
     - 0, or only the port's own bit
   * - Port talks to the CPU port only
     - All ports except the CPU port
   * - Group of ports plus the CPU port
     - All ports except the other members of the group and the CPU port
   * - CPU port sends only where its tag says
     - All ports

.. tab-set::

   .. tab-item:: C
      :sync: c

      .. literalinclude:: ../bindings/c/examples/guide.c
           :language: c
           :start-after: /* [isolation] */
           :end-before: /* [isolation end] */

   .. tab-item:: MicroPython
      :sync: micropython

      .. literalinclude:: ../bindings/micropython/examples/guide.py
           :language: python
           :start-after: # [isolation]
           :end-before: # [isolation end]

Isolation is applied after the destination lookup. If the forwarding database knows the
destination on a blocked port, the frame is dropped; it is not flooded to the allowed ports.
This matters when two groups learn into the same VLAN, because an address learned in one group
then hides the same address in the other. Give each group its own VLAN, as in
:ref:`vlan-port-based`, or have the host forward such frames as the Linux driver does.

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
     - ``DISABLED``
     - Disabled
   * - 1
     - ``LEARNING``
     - Listening and learning
   * - 2
     - ``BLOCKING``
     - Blocking
   * - 3
     - ``FORWARD``
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
     - Setting
   * - No learning on a port
     - Set :field:`PORT_LEARN.DIS`
   * - Limit the number of learned addresses
     - Set :field:`PORT_LEARN.LIMIT` and :field:`PORT_LEARN.LIMIT_EN`
   * - Drop frames from new addresses beyond the limit
     - Also set :field:`PORT_LEARN.DROP_ON_EXCEEDED`
   * - No learning in one VLAN
     - Set :field:`VLAN_CTRL.LEARN_DIS` of the VLAN

Of these the Linux driver uses :field:`PORT_LEARN.DIS` and :field:`VLAN_CTRL.LEARN_DIS`; the
other fields are described from their names. Learned entries age out after the time in
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
     - ``FORWARD``
     - Flood the frame to the ports allowed by the filter registers below.
   * - 1
     - ``TRAP``
     - Send the frame to the CPU only.
   * - 2
     - ``DROP``
     - Discard the frame.
   * - 3
     - ``COPY``
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

A set bit in a filter register keeps flooded frames of that kind away from the port.

.. yt-bitfield:: ACT_UNK_UCAST

There are two usual configurations:

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Register
     - Hardware switch
     - Host forwards unknown frames
   * - :reg:`ACT_UNK_UCAST`
     - ``FORWARD`` on every port
     - ``TRAP`` on every port, ``DROP`` on the CPU port
   * - :reg:`ACT_UNK_MCAST`
     - ``FORWARD`` on every port
     - ``TRAP`` on every port, ``DROP`` on the CPU port
   * - :reg:`FILTER_UNK_UCAST`
     - 0
     - ``0x7ff``
   * - :reg:`FILTER_UNK_MCAST`
     - 0
     - ``0x7ff``

The right column is what the Linux driver writes: it traps every unknown frame to the host,
which floods it in software to the right group of ports. The left column lets the switch
flood by itself, within the limits of :ref:`port isolation <forwarding-isolation>`; it follows
from the register descriptions and has not been run on hardware by this project.
