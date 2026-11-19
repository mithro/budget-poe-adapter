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

:reg:`CPU_COPY` chooses where the switch sends the frames it traps or copies "to the CPU".
Set :field:`CPU_COPY.TO_EXT_CPU` for the port in :reg:`EXT_CPU_PORT`.
:lx:`yt921x_chip_setup_dsa` of the :ref:`Linux driver <sources-list>` writes both registers
in this way. It is :ev:`inferred` from their names that :field:`CPU_COPY.TO_INT_CPU` and
:field:`CPU_COPY.FORCE_INT_PORT` direct such frames to the internal microcontroller on
port 10.

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

A tagged CPU port needs 8 more bytes of frame size, which :ref:`ports-mtu` sets.

.. _cpu-tag-format:

The tag
-------

The tag is 8 bytes (:const:`TAG_LEN`) placed after the source address, where a VLAN tag would
be. It begins with the EtherType in :reg:`CPU_TAG_TPID`, ``0x9988`` after reset. The 16-bit
words are sent most significant byte first.

Word 1 (bytes 2 and 3) holds a VLAN tag in a frame that the switch sends to the host. In a
frame from the host, send 0. The layout of the four words is the header comment of
:lx:`tag_yt921x.c:7`, and :lx:`yt921x_tag_xmit` writes 0 to word 1 with the comment that the
VLAN tag is unrelated on transmit.

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
     - Content
   * - 15
     - .. _tag-rx-port-en:

       PORT_EN
     - 1 when RX_PORT is valid
   * - 14:11
     - .. _tag-rx-port:

       RX_PORT
     - receiving port
   * - 10:8
     - .. _tag-prio:

       PRIO
     - priority of the frame
   * - 7
     - .. _tag-code-en:

       CODE_EN
     - 1 when CODE is valid
   * - 6:1
     - .. _tag-code:

       CODE
     - :ref:`reason code <cpu-tag-codes>`
   * - 0
     - none
     - :ev:`not known`

.. _cpu-tag-codes:

Reason codes
~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 12 20 34 34

   * - CODE
     - Name
     - Reason
     - Register that causes it
   * - ``0x00``
     - .. _tag-code-forward:

       FORWARD
     - normal forwarding
     - none
   * - ``0x17``
     - .. _tag-code-acl:

       ACL
     - trapped by an ACL rule
     - :field:`ACL_ACT.FWD`
   * - ``0x19``
     - .. _tag-code-unk-ucast:

       UNK_UCAST
     - unknown unicast destination
     - :reg:`ACT_UNK_UCAST`
   * - ``0x1a``
     - .. _tag-code-unk-mcast:

       UNK_MCAST
     - unknown multicast destination
     - :reg:`ACT_UNK_MCAST`
   * - ``0x1b``
     - .. _tag-code-port-copy:

       PORT_COPY
     - copied by a port setting
     - :ev:`not known`
   * - ``0x1c``
     - .. _tag-code-fdb-copy:

       FDB_COPY
     - copied by a forwarding database entry
     - :field:`FDB_IN2.COPY_TO_CPU`

The six codes are the list ``enum yt921x_tag_code`` of :lx:`tag_yt921x.c:50`, whose comment
calls the list incomplete. The reasons of :ref:`PORT_COPY <tag-code-port-copy>` and
:ref:`FDB_COPY <tag-code-fdb-copy>` are :ev:`inferred` from the two names.

:lx:`yt921x_tag_rcv` treats the codes in two groups.

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Code
     - Switch has forwarded the frame
     - Host has to forward the frame
   * - :ref:`FORWARD <tag-code-forward>`
     - yes
     - no
   * - :ref:`PORT_COPY <tag-code-port-copy>`
     - yes
     - no
   * - :ref:`FDB_COPY <tag-code-fdb-copy>`
     - yes
     - no
   * - :ref:`ACL <tag-code-acl>`
     - no
     - yes
   * - :ref:`UNK_UCAST <tag-code-unk-ucast>`
     - no
     - yes
   * - :ref:`UNK_MCAST <tag-code-unk-mcast>`
     - no
     - yes

The codes :ref:`UNK_UCAST <tag-code-unk-ucast>` and :ref:`UNK_MCAST <tag-code-unk-mcast>` do
not tell a trapped frame from a copied one, so do not combine the copy action of
:ref:`forwarding-flood` with forwarding in the host. Discard a received frame whose
:ref:`PORT_EN <tag-rx-port-en>` bit is clear, as :lx:`yt921x_tag_rcv` does.

.. _cpu-tag-tx:

Frames from the host to the switch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The host sets :ref:`CODE_EN <tag-code-en>` in word 2 with :ref:`CODE <tag-code>` 0 and the
wanted priority in :ref:`PRIO <tag-prio>`, and puts the destination ports in word 3.
:lx:`yt921x_tag_xmit` builds the tag in this way. It is :ev:`inferred` from that use that the
switch sends the frame to exactly the ports of word 3 and removes the tag.

.. yt-diagram:: tag-word3
   :caption: Tag word 3 (bytes 6 and 7).

.. list-table::
   :header-rows: 1
   :widths: 12 18 70

   * - Bits
     - Field
     - Content
   * - 15
     - .. _tag-tx-port-en:

       PORT_EN
     - 1 when TX_PORTS is valid
   * - 10:0
     - .. _tag-tx-ports:

       TX_PORTS
     - mask of the destination ports

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

Set the action for unknown destinations to drop on the CPU port itself, with the registers
of :ref:`forwarding-flood`, so that an untagged frame from the host is not flooded.
:lx:`yt921x_chip_setup_dsa` writes this setting.
