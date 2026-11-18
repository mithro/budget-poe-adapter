.. _ports:

Ports
=====

Each port has a MAC with its own control and status registers. Ports with a built-in PHY need
little more than that; ports 8 and 9 also need their interface selected. The registers are in
the :blk:`port` and :blk:`eee` blocks.

.. _ports-up:

Bring a port up
---------------

:reg:`PORT_CTRL` holds the MAC settings of a port and :reg:`PORT_STATUS` shows what the MAC
runs with. The low eight bits of the two registers have the same layout.

.. yt-bitfield:: PORT_CTRL

There are two ways to run a MAC:

.. list-table::
   :header-rows: 1
   :widths: 22 30 48

   * - Mode
     - :field:`PORT_CTRL.LINK_AN`
     - Speed, duplex and pause
   * - Follow the PHY
     - 1
     - The MAC takes them from the built-in PHY or from in-band SGMII status.
   * - Forced
     - 0
     - The MAC uses :field:`PORT_CTRL.SPEED`, :field:`PORT_CTRL.DUPLEX_FULL`,
       :field:`PORT_CTRL.RX_PAUSE` and :field:`PORT_CTRL.TX_PAUSE`.

In both modes the MAC passes frames only while :field:`PORT_CTRL.RX_MAC_EN` and
:field:`PORT_CTRL.TX_MAC_EN` are set. To take a port down, clear those two bits and
:field:`PORT_CTRL.LINK_AN`.

The Linux driver always forces the MAC: it watches the PHY itself and, on a link change,
writes the negotiated speed, duplex and pause into :reg:`PORT_CTRL`. A driver without its own
PHY state machine can set :field:`PORT_CTRL.LINK_AN` and :field:`PORT_CTRL.PAUSE_AN` and leave
the rest to the switch; the Linux driver uses that mode only for a SerDes with in-band
status. The speed codes are the :enum:`speed` list.

.. tab-set::

   .. tab-item:: C
      :sync: c

      .. literalinclude:: ../bindings/c/examples/guide.c
           :language: c
           :start-after: /* [port-up] */
           :end-before: /* [port-up end] */

   .. tab-item:: MicroPython
      :sync: micropython

      .. literalinclude:: ../bindings/micropython/examples/guide.py
           :language: python
           :start-after: # [port-up]
           :end-before: # [port-up end]

.. _ports-status:

Read the link state
-------------------

.. yt-bitfield:: PORT_STATUS

.. tab-set::

   .. tab-item:: C
      :sync: c

      .. literalinclude:: ../bindings/c/examples/guide.c
           :language: c
           :start-after: /* [port-status] */
           :end-before: /* [port-status end] */

   .. tab-item:: MicroPython
      :sync: micropython

      .. literalinclude:: ../bindings/micropython/examples/guide.py
           :language: python
           :start-after: # [port-status]
           :end-before: # [port-status end]

The link state of a built-in PHY can also be read from the PHY itself; see :ref:`phy-mbus`.

.. _ports-external:

External ports 8 and 9
----------------------

An external port uses either its SerDes or its xMII pins. :ref:`reference-parts-ports` shows
which of the two each part has. Select one before enabling the MAC:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Interface
     - Set
     - Clear
   * - SerDes
     - :field:`SERDES_CTRL.PORT` of the port
     - :field:`XMII_CTRL.PORT` of the port
   * - xMII
     - :field:`XMII_CTRL.PORT` of the port
     - :field:`SERDES_CTRL.PORT` of the port

The two enable fields are indexed differently: port 8 is bit 0 of :reg:`SERDES_CTRL` but bit 1
of :reg:`XMII_CTRL`. The field macros of the bindings take the port number and hide this.

.. _ports-serdes:

SerDes
~~~~~~

1. Set the port's bit in :reg:`SERDES_CTRL`, clear it in :reg:`XMII_CTRL`, and make sure
   :field:`SERDES_CTRL.TEST` is clear.
2. Write the protocol to :field:`SERDES.MODE`.
3. For a link with in-band status (SGMII to a PHY), set :field:`PORT_CTRL.LINK_AN` and leave
   :field:`SERDES.LINK` clear. The PCS of the SerDes negotiates; its registers are standard
   clause 22 registers on the :ref:`internal MDIO master <phy-mbus>` at the address of the
   port number.
4. For a fixed link (to another MAC, or 1000BASE-X or 2500BASE-X without negotiation), write
   :field:`SERDES.SPEED`, :field:`SERDES.DUPLEX_FULL` and the pause bits and set
   :field:`SERDES.LINK`, then force :reg:`PORT_CTRL` to the same values.
5. Enable the MAC as in :ref:`ports-up`.

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - :field:`SERDES.MODE`
     - Value
     - Use
   * - ``SGMII``
     - 0
     - SGMII, the switch on the MAC side
   * - ``REVSGMII``
     - 1
     - SGMII, the switch on the PHY side
   * - ``V1000BASEX``
     - 2
     - 1000BASE-X
   * - ``V100BASEX``
     - 3
     - 100BASE-FX
   * - ``V2500BASEX``
     - 4
     - 2500BASE-X

.. _ports-xmii:

xMII
~~~~

1. Set the port's bit in :reg:`XMII_CTRL` and clear it in :reg:`SERDES_CTRL`.
2. Set the pin voltage in :reg:`IO_LEVEL`.
3. Write :reg:`XMII`: the interface type in :field:`XMII.MODE`, the clock directions and
   RGMII delays, and :field:`XMII.EN`.
4. No PHY reports the link of a MAC-to-MAC connection, so tell the switch: write speed and
   duplex and :field:`MDIO_POLLING.LINK` to :reg:`MDIO_POLLING` of the port and set
   :field:`XMII.LINK`.
5. Force :reg:`PORT_CTRL` to the same speed and duplex as in :ref:`ports-up`.

The Linux driver writes :reg:`MDIO_POLLING` and :field:`XMII.LINK` as in steps 4 and 5 but
does not configure any xMII mode yet. Steps 2 and 3 follow the field definitions of its header
and are not confirmed by working code. RGMII delays in particular need checking on the board.

.. _ports-mtu:

Frame size
----------

:field:`MAC_FRAME.SIZE` is the longest frame a port accepts, counted from the destination
address to the frame check sequence. For an IP MTU of *m* bytes write *m* + 18, and 8 more
(:const:`TAG_LEN`) on a CPU port that carries tags. The largest value is 9216
(:const:`FRAME_SIZE_MAX`), which is also the value after reset.

.. _ports-eee:

Energy Efficient Ethernet
-------------------------

Energy Efficient Ethernet has one switch for the whole chip and one per port.

1. Chip: set :field:`PON_STRAP_FUNC.EEE` and :field:`PON_STRAP_VAL.EEE`. This overrides the
   strap pin, as described in :ref:`bringup-straps`. Clear both when no port uses it.
2. Port: set the port's :field:`EEE_CTRL.EN` bit and :field:`EEE_VAL.DATA` of the port.

This is the sequence of the Linux driver, whose author notes that the vendor documentation on
it is poor; treat it as known to work but not understood in detail.
