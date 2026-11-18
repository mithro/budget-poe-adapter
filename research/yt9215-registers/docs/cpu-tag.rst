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
port are to carry the tag described below.

.. yt-bitfield:: EXT_CPU_PORT

:reg:`CPU_COPY` chooses where the switch sends the frames it traps or copies "to the CPU":
set :field:`CPU_COPY.TO_EXT_CPU` for the port named above. The other two bits direct such
frames to the internal microcontroller on port 10.

.. tab-set::

   .. tab-item:: C
      :sync: c

      .. literalinclude:: ../bindings/c/examples/guide.c
           :language: c
           :start-after: /* [cpu-port] */
           :end-before: /* [cpu-port end] */

   .. tab-item:: MicroPython
      :sync: micropython

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
     - RX_PORT is valid. The Linux driver discards received frames without it.
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
     - Reason the frame reached the CPU, from the table below.

.. list-table::
   :header-rows: 1
   :widths: 14 30 56

   * - CODE
     - Name
     - Reason
   * - ``0x00``
     - FORWARD
     - Normal forwarding; the switch has already sent the frame to any other destination.
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
     - Copied to the CPU by a port setting; the switch also forwarded it.
   * - ``0x1c``
     - FDB_COPY
     - Copied to the CPU by a forwarding database entry (:field:`FDB_IN2.COPY_TO_CPU`); the
       switch also forwarded it.

A frame that was trapped has not been forwarded by the switch, so the host must forward it if
it should go anywhere. Other codes exist; these are the ones the Linux driver names.

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

      .. literalinclude:: ../bindings/c/examples/guide.c
           :language: c
           :start-after: /* [tag] */
           :end-before: /* [tag end] */

   .. tab-item:: MicroPython
      :sync: micropython

      .. literalinclude:: ../bindings/micropython/examples/guide.py
           :language: python
           :start-after: # [tag]
           :end-before: # [tag end]

The Linux driver sets the action for unknown destinations to drop on the CPU port itself
(:ref:`forwarding-flood`), so that an untagged frame from the host is not flooded.
