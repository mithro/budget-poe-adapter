.. _cpu-tag:

CPU port and frame tag
======================

A host that only configures the switch needs nothing from this page. A host that also sends
and receives frames through the switch, as a managed switch or a router does, connects a MAC
to one port and names it as the CPU port. The registers are in the :blk:`cpu` block.

.. _cpu-tag-port:

Choose the CPU port
-------------------

Write :reg:`EXT_CPU_PORT` with the port number in :field:`EXT_CPU_PORT.PORT` and
:field:`EXT_CPU_PORT.PORT_EN` set. Set :field:`EXT_CPU_PORT.TAG_EN` as well if frames on the
port are to carry :ref:`the tag <cpu-tag-format>`.

.. yt-bitfield:: EXT_CPU_PORT

:reg:`CPU_COPY` chooses where the switch sends the frames it traps or copies "to the CPU":
set :field:`CPU_COPY.TO_EXT_CPU` for the port in :reg:`EXT_CPU_PORT`. The other two bits direct such
frames to the internal microcontroller on port 10.

.. tab-set::

   .. tab-item:: C
      :sync: c

      From :download:`guide.c <../bindings/c/examples/guide.c>`.

      .. literalinclude:: ../bindings/c/examples/guide.c
           :language: c
           :start-after: /* [cpu-port] */
           :end-before: /* [cpu-port end] */

   .. tab-item:: MicroPython
      :sync: micropython

      From :download:`guide.py <../bindings/micropython/examples/guide.py>`.

      .. literalinclude:: ../bindings/micropython/examples/guide.py
           :language: python
           :start-after: # [cpu-port]
           :end-before: # [cpu-port end]

Remember that a tagged CPU port needs 8 more bytes of frame size; see :ref:`ports-mtu`.

.. _cpu-tag-format:

The tag
-------

The tag is 8 bytes (:const:`TAG_LEN`) placed after the source address, where a VLAN tag would
be. It begins with the EtherType in :reg:`CPU_TAG_TPID`, ``0x9988`` after reset. The 16-bit
words are sent most significant byte first.

Word 1 (bytes 2 and 3) holds the VLAN tag of a frame the switch sends to the host; do not
expect it to be zero. In a frame from the host the switch ignores it, so send 0.

.. yt-diagram:: tagged-frame
   :caption: A frame on the CPU port and the four 16-bit words of the tag.

.. _cpu-tag-rx:

Frames from the switch to the host
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Word 2 tells the host where the frame came from and why it was sent to the CPU.

.. yt-diagram:: tag-word2
   :caption: Tag word 2 (bytes 4 and 5).

.. list-table::
   :header-rows: 1
   :widths: 12 18 70

   * - Bits
     - Field
     - Meaning
   * - 15
     - PORT_EN
     - RX_PORT is valid.
   * - 14:11
     - RX_PORT
     - Port the frame was received on.
   * - 10:8
     - PRIO
     - Priority of the frame, 0 to 7.
   * - 7
     - CODE_EN
     - CODE is valid.
   * - 6:1
     - CODE
     - Reason the frame reached the CPU, a :ref:`code <cpu-tag-codes>`.

.. _cpu-tag-codes:

.. list-table::
   :header-rows: 1
   :widths: 14 30 56

   * - CODE
     - Name
     - Reason
   * - ``0x00``
     - FORWARD
     - Normal forwarding.
   * - ``0x17``
     - ACL
     - An ACL rule trapped the frame (:field:`ACL_ACT.FWD`).
   * - ``0x19``
     - UNK_UCAST
     - Unknown unicast destination, trapped by :reg:`ACT_UNK_UCAST`.
   * - ``0x1a``
     - UNK_MCAST
     - Unknown multicast destination, trapped by :reg:`ACT_UNK_MCAST`.
   * - ``0x1b``
     - PORT_COPY
     - Copied to the CPU by a port setting.
   * - ``0x1c``
     - FDB_COPY
     - Copied to the CPU by a forwarding database entry (:field:`FDB_IN2.COPY_TO_CPU`).

A frame with the code FORWARD, PORT_COPY or FDB_COPY has also been sent by the switch to its
other destinations. A frame that was trapped (ACL, UNK_UCAST, UNK_MCAST) has not, so the host
must forward it if it should go anywhere. The codes UNK_UCAST and UNK_MCAST do not tell a
trapped frame from a copied one, so do not combine the copy action of
:ref:`forwarding-flood` with forwarding in the host. Discard a received frame whose PORT_EN bit is
clear, as the :ref:`Linux driver <sources-list>` does. Other codes exist; these are the ones the :ref:`Linux driver <sources-list>`
names, and the meanings of PORT_COPY and FDB_COPY are inferred from the names.

.. _cpu-tag-tx:

Frames from the host to the switch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The host sets word 2 to CODE_EN with CODE 0 and the wanted priority in PRIO, and puts the
destination ports in word 3. The switch sends the frame to exactly those ports and removes the
tag.

.. yt-diagram:: tag-word3
   :caption: Tag word 3 (bytes 6 and 7).

.. list-table::
   :header-rows: 1
   :widths: 12 18 70

   * - Bits
     - Field
     - Meaning
   * - 15
     - PORT_EN
     - TX_PORTS is valid.
   * - 10:0
     - TX_PORTS
     - Ports to send the frame to, one bit per port.

.. tab-set::

   .. tab-item:: C
      :sync: c

      From :download:`guide.c <../bindings/c/examples/guide.c>`.

      .. literalinclude:: ../bindings/c/examples/guide.c
           :language: c
           :start-after: /* [tag] */
           :end-before: /* [tag end] */

   .. tab-item:: MicroPython
      :sync: micropython

      From :download:`guide.py <../bindings/micropython/examples/guide.py>`.

      .. literalinclude:: ../bindings/micropython/examples/guide.py
           :language: python
           :start-after: # [tag]
           :end-before: # [tag end]

Set the action for unknown destinations to drop on the CPU port itself
(:ref:`forwarding-flood`), so that an untagged frame from the host is not flooded; the :ref:`Linux driver <sources-list>`
confirms this setting. That the switch sends a tagged frame to exactly the ports of
word 3 is how the :ref:`Linux driver <sources-list>` uses the tag.
