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

There are two ways to run a MAC. With :field:`PORT_CTRL.LINK_AN` set, the MAC takes speed,
duplex and pause from the built-in PHY or from in-band SGMII status. With it clear, the MAC
is forced and uses these fields:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Field
     - Sets
   * - :field:`PORT_CTRL.SPEED`
     - Speed, a code of the :enum:`speed` list
   * - :field:`PORT_CTRL.DUPLEX_FULL`
     - Full duplex
   * - :field:`PORT_CTRL.RX_PAUSE`
     - Obey received pause frames
   * - :field:`PORT_CTRL.TX_PAUSE`
     - Send pause frames

In both modes the MAC passes frames only while :field:`PORT_CTRL.RX_MAC_EN` and
:field:`PORT_CTRL.TX_MAC_EN` are set. To take a port down, clear those two bits and
:field:`PORT_CTRL.LINK_AN`.

Forcing is the confirmed way for a port with a built-in PHY: the :ref:`Linux driver <sources-list>` watches the PHY
itself and, on a link change, writes the negotiated speed, duplex and pause into
:reg:`PORT_CTRL`. It sets :field:`PORT_CTRL.LINK_AN` and :field:`PORT_CTRL.PAUSE_AN` only for
a SerDes with in-band status. That the same bits make a copper port follow its built-in PHY
is inferred from their names.

.. tab-set::

   .. tab-item:: C
      :sync: c

      From :download:`guide.c <../bindings/c/examples/guide.c>`.

      .. literalinclude:: ../bindings/c/examples/guide.c
           :language: c
           :start-after: /* [port-up] */
           :end-before: /* [port-up end] */

   .. tab-item:: MicroPython
      :sync: micropython

      From :download:`guide.py <../bindings/micropython/examples/guide.py>`.

      .. literalinclude:: ../bindings/micropython/examples/guide.py
           :language: python
           :start-after: # [port-up]
           :end-before: # [port-up end]

.. _ports-status:

Read the link state
-------------------

Read :reg:`PORT_STATUS` to learn what a MAC runs with: :field:`PORT_STATUS.LINK` is the link
state, :field:`PORT_STATUS.SPEED` a code of the :enum:`speed` list and
:field:`PORT_STATUS.DUPLEX_FULL` the duplex. On a forced port the register repeats what the
driver wrote to :reg:`PORT_CTRL`.

.. yt-bitfield:: PORT_STATUS

.. tab-set::

   .. tab-item:: C
      :sync: c

      From :download:`guide.c <../bindings/c/examples/guide.c>`.

      .. literalinclude:: ../bindings/c/examples/guide.c
           :language: c
           :start-after: /* [port-status] */
           :end-before: /* [port-status end] */

   .. tab-item:: MicroPython
      :sync: micropython

      From :download:`guide.py <../bindings/micropython/examples/guide.py>`.

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
   :field:`SERDES.SPEED`, :field:`SERDES.DUPLEX_FULL`, :field:`SERDES.RX_PAUSE` and
   :field:`SERDES.TX_PAUSE` and set
   :field:`SERDES.LINK`, then force :reg:`PORT_CTRL` to the same values.
5. Enable the MAC as in :ref:`ports-up`.

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - :field:`SERDES.MODE`
     - Value
     - Use
   * - :val:`SERDES.MODE.SGMII`
     - 0
     - SGMII, the switch on the MAC side
   * - :val:`SERDES.MODE.REVSGMII`
     - 1
     - SGMII, the switch on the PHY side
   * - :val:`SERDES.MODE.V1000BASEX`
     - 2
     - 1000BASE-X
   * - :val:`SERDES.MODE.V100BASEX`
     - 3
     - 100BASE-FX
   * - :val:`SERDES.MODE.V2500BASEX`
     - 4
     - 2500BASE-X

.. _ports-xmii:

xMII
~~~~

1. Set the port's bit in :reg:`XMII_CTRL` and clear it in :reg:`SERDES_CTRL`.
2. Set the pin voltage in :reg:`IO_LEVEL`.
3. Write :reg:`XMII`: the interface type in :field:`XMII.MODE`, the clock directions
   (:field:`XMII.TX_CLK_IN`, :field:`XMII.RX_CLK_IN`), for RGMII the delays
   (:field:`XMII.RGMII_RX_DELAY_150PS`, :field:`XMII.RGMII_TX_DELAY_150PS`,
   :field:`XMII.RGMII_TX_DELAY_2NS`), and :field:`XMII.EN`.
4. No PHY reports the link of a MAC-to-MAC connection, so tell the switch: write speed and
   duplex and :field:`MDIO_POLLING.LINK` to :reg:`MDIO_POLLING` of the port and set
   :field:`XMII.LINK`.
5. Force :reg:`PORT_CTRL` to the same speed and duplex as in :ref:`ports-up`.

The :ref:`Linux driver <sources-list>` writes :reg:`MDIO_POLLING` and :field:`XMII.LINK` as in steps 4 and 5 but
configures no xMII mode. Steps 1 to 3 largely match the
`vendor driver for the YT9215RB <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/yt9215rb_mdio_driver/yt9215rb.c#L322>`__, which brings up
RGMII on port 8 with the writes of this table. Other modes follow the field definitions only. RGMII
delays need checking on the board.

.. list-table::
   :header-rows: 1
   :widths: 22 44 34

   * - Register
     - Field
     - Value
   * - :reg:`IO_LEVEL`
     - :field:`RGMII0 <IO_LEVEL.YT9215_RGMII0>`
     - 3
   * - :reg:`IO_LEVEL`
     - :field:`RGMII1 <IO_LEVEL.YT9215_RGMII1>`
     - 3
   * - :reg:`XMII_CTRL`
     - Bit of port 8 in :field:`XMII_CTRL.PORT`
     - 1
   * - :reg:`XMII` of port 8
     - :field:`XMII.MODE`
     - :val:`XMII.MODE.RGMII` (4)
   * - :reg:`XMII` of port 8
     - :field:`XMII.LINK`
     - 1
   * - :reg:`XMII` of port 8
     - :field:`XMII.EN`
     - 1
   * - :reg:`XMII` of port 8
     - Bit 26
     - 1
   * - :reg:`XMII` of port 8
     - Bit 20
     - 1
   * - :reg:`XMII` of port 8
     - :field:`XMII.RGMII_RX_DELAY_150PS`
     - From the board description
   * - :reg:`XMII` of port 8
     - :field:`XMII.RGMII_TX_DELAY_150PS`
     - From the board description
   * - :reg:`XMII` of port 8
     - :field:`XMII.RGMII_TX_DELAY_2NS`
     - From the board description
   * - :reg:`PORT_CTRL` of port 8
     - :field:`PORT_CTRL.SPEED`
     - :val:`speed.V1000` (2)
   * - :reg:`PORT_CTRL` of port 8
     - :field:`PORT_CTRL.DUPLEX_FULL`
     - 1
   * - :reg:`PORT_CTRL` of port 8
     - :field:`PORT_CTRL.RX_PAUSE`
     - 1
   * - :reg:`PORT_CTRL` of port 8
     - :field:`PORT_CTRL.TX_PAUSE`
     - 1
   * - :reg:`PORT_CTRL` of port 8
     - :field:`PORT_CTRL.HALF_PAUSE`
     - 1
   * - :reg:`PORT_CTRL` of port 8
     - :field:`PORT_CTRL.RX_MAC_EN`
     - 1
   * - :reg:`PORT_CTRL` of port 8
     - :field:`PORT_CTRL.TX_MAC_EN`
     - 1

The register values are ``0x0000000f`` for :reg:`IO_LEVEL`, ``0x00000002`` for
:reg:`XMII_CTRL`, ``0x841c0000`` for :reg:`XMII` before the delays and ``0x000001fa`` for
:reg:`PORT_CTRL`. The vendor driver writes :reg:`IO_LEVEL` only for 1.8 V RGMII pins, and its
value 3 disagrees with the Linux header, which gives 1.8 V as 2 in these two fields and has
no value 3; which is right is not known. Bits 26 and 20 of :reg:`XMII` have no known name.
The vendor driver does not write :reg:`SERDES_CTRL` or :reg:`MDIO_POLLING`.

.. _ports-mtu:

Frame size
----------

:field:`MAC_FRAME.SIZE` is the longest frame a port accepts, counted from the destination
address to the frame check sequence. For an IP MTU of *m* bytes write *m* + 18, and 8 more
(:const:`TAG_LEN`) on a CPU port that carries tags. The largest value is 9216
(:const:`FRAME_SIZE_MAX`). A comment in the :ref:`Linux driver <sources-list>` gives it as
the value after reset too; like the other :ref:`reset values <sources-reset>` this is not
confirmed by a read from hardware.

.. _ports-eee:

Energy Efficient Ethernet
-------------------------

Energy Efficient Ethernet has one switch for the whole chip and one per port.

1. Chip: set :field:`PON_STRAP_FUNC.EEE` and :field:`PON_STRAP_VAL.EEE`. This overrides the
   strap pin, as described in :ref:`bringup-straps`. Clear both when no port uses it.
2. Port: set the port's :field:`EEE_CTRL.EN` bit and :field:`EEE_VAL.DATA` of the port.

The sequence is confirmed by the :ref:`Linux driver <sources-list>`, whose author notes that the vendor
documentation on it is poor; treat it as known to work but not understood in detail.
