.. _ports:

Ports
=====

Each port has a MAC with its own control and status registers. A port with a built-in PHY
needs only :ref:`its MAC enabled <ports-up>`. Ports 8 and 9 also need
:ref:`their interface selected <ports-external>`. The registers are in the :blk:`port` and
:blk:`eee` blocks.

.. _ports-up:

Bring a port up
---------------

:reg:`PORT_CTRL` holds the MAC settings of a port and :reg:`PORT_STATUS` shows what the MAC
runs with. The low eight bits of the two registers have the same layout, as the
comment in :lx:`chip.h:92` states.

.. yt-bitfield:: PORT_CTRL

There are two ways to run a MAC. It is :ev:`inferred` from the name of
:field:`PORT_CTRL.LINK_AN` that with the bit set, the MAC takes speed and duplex from the
in-band status of the SerDes, and that with it clear, the MAC is forced and uses the fields
of the :ref:`forced-mode table <ports-forced>`. :field:`PORT_CTRL.PAUSE_AN` does the same
for pause alone: :lx:`yt921x_serdes_config` sets it only for a link other than SGMII with
in-band negotiation enabled whose pause result the MAC may take.

.. _ports-forced:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Field
     - Content
   * - :field:`PORT_CTRL.SPEED`
     - speed code of the :enum:`speed` list
   * - :field:`PORT_CTRL.DUPLEX_FULL`
     - 1 for full duplex
   * - :field:`PORT_CTRL.RX_PAUSE`
     - 1 to obey received pause frames
   * - :field:`PORT_CTRL.TX_PAUSE`
     - 1 to send pause frames

In both modes the MAC passes frames only while :field:`PORT_CTRL.RX_MAC_EN` and
:field:`PORT_CTRL.TX_MAC_EN` are set. To take a port down, clear
:field:`PORT_CTRL.RX_MAC_EN`, :field:`PORT_CTRL.TX_MAC_EN` and :field:`PORT_CTRL.LINK_AN`, as
:lx:`yt921x_port_down` of the :ref:`Linux driver <sources-list>` does.

Forcing is the :ev:`confirmed` way for a port with a built-in PHY. The Linux kernel watches
the PHY and, on a link change, :lx:`yt921x_port_up` writes the negotiated speed, duplex and
pause into :reg:`PORT_CTRL`. That function sets :field:`PORT_CTRL.LINK_AN` only for a SerDes
with in-band status. Both bits are :ev:`confirmed` for a SerDes by :lx:`yt921x_serdes_config`. It is
:ev:`inferred` from their names that the two bits also make a copper port follow its built-in
PHY.

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
:field:`PORT_STATUS.DUPLEX_FULL` the duplex. The register has the level :ev:`header`:
:lx:`chip.h:96` defines it with the field layout of :reg:`PORT_CTRL`, and no function of the
:ref:`Linux driver <sources-list>` reads it. It is :ev:`inferred` that on a forced port the
register repeats what the driver wrote to :reg:`PORT_CTRL`.

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

The link state of a built-in PHY can also be read from register 1 of the PHY, with the
transfer of :ref:`phy-mbus`.

.. _ports-external:

External ports 8 and 9
----------------------

An external port uses either its SerDes or its xMII pins. :ref:`reference-parts-ports` shows
which of the two each part has. Select one before enabling the MAC.
:lx:`yt921x_port_config` writes the values for the SerDes in the
:ref:`selection table <ports-select-table>`. The values for the xMII pins are :ev:`inferred` as
their mirror image.

.. _ports-select-table:

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

The two enable fields are indexed differently: port 8 is bit 0 of :reg:`SERDES_CTRL` but
bit 1 of :reg:`XMII_CTRL`. The field macros of the :ref:`bindings <bindings-naming>` take the
port number and hide this.

.. _ports-serdes:

SerDes
~~~~~~

1. Set the port's bit in :reg:`SERDES_CTRL`, clear it in :reg:`XMII_CTRL`, and make sure
   :field:`SERDES_CTRL.TEST` is clear.
2. Write the protocol to :field:`SERDES.MODE`.
3. For a link with in-band status (SGMII to a PHY), set :field:`PORT_CTRL.LINK_AN`, write
   :field:`PORT_CTRL.PAUSE_AN` and leave :field:`SERDES.LINK` clear. The PCS of the SerDes negotiates; its registers are standard
   `clause 22 <https://en.wikipedia.org/wiki/Management_Data_Input/Output>`__ registers
   on the :ref:`internal MDIO master <phy-mbus>` at the address of the
   port number.
4. For a fixed link (to another MAC, or 1000BASE-X or 2500BASE-X without negotiation), write
   :field:`SERDES.SPEED`, :field:`SERDES.DUPLEX_FULL`, :field:`SERDES.RX_PAUSE` and
   :field:`SERDES.TX_PAUSE` and set
   :field:`SERDES.LINK`, then force :reg:`PORT_CTRL` to the same values.
5. Enable the MAC with the fields of :ref:`ports-up`.

The steps are :ev:`confirmed` by four functions of the :ref:`Linux driver <sources-list>`.

.. list-table::
   :header-rows: 1
   :widths: 14 50 36

   * - Step
     - Part of the step
     - Function
   * - 1
     - Two port bits
     - :lx:`yt921x_port_config`
   * - 1
     - :field:`SERDES_CTRL.TEST` clear
     - :lx:`yt921x_chip_setup`
   * - 2
     - :field:`SERDES.MODE`
     - :lx:`yt921x_serdes_config`
   * - 3
     - :field:`PORT_CTRL.LINK_AN` set
     - :lx:`yt921x_serdes_config`
   * - 3
     - :field:`PORT_CTRL.PAUSE_AN`
     - :lx:`yt921x_serdes_config`
   * - 3
     - :field:`SERDES.LINK` clear
     - :lx:`yt921x_serdes_config`
   * - 3
     - PCS registers
     - :lx:`yt921x_serdes_config`
   * - 4
     - Fields of :reg:`SERDES`
     - :lx:`yt921x_port_up`
   * - 4
     - Fields of :reg:`PORT_CTRL`
     - :lx:`yt921x_port_up`
   * - 5
     - MAC enable fields
     - :lx:`yt921x_port_up`

:lx:`yt921x_port_up` writes :reg:`PORT_CTRL` before :reg:`SERDES`. It writes
:field:`SERDES.SPEED`, :field:`SERDES.DUPLEX_FULL`, :field:`SERDES.RX_PAUSE` and
:field:`SERDES.TX_PAUSE` for a link with in-band status too.

.. _ports-serdes-modes:

.. list-table::
   :header-rows: 1
   :widths: 30 12 24 18 16

   * - :field:`SERDES.MODE`
     - Value
     - Protocol
     - Role of the switch
     - :ref:`Evidence <evidence>`
   * - :val:`SERDES.MODE.SGMII`
     - 0
     - SGMII
     - MAC side
     - :ev:`confirmed`
   * - :val:`SERDES.MODE.REVSGMII`
     - 1
     - SGMII
     - PHY side
     - :ev:`header`
   * - :val:`SERDES.MODE.V1000BASEX`
     - 2
     - 1000BASE-X
     - none
     - :ev:`confirmed`
   * - :val:`SERDES.MODE.V100BASEX`
     - 3
     - 100BASE-FX
     - none
     - :ev:`confirmed`
   * - :val:`SERDES.MODE.V2500BASEX`
     - 4
     - 2500BASE-X
     - none
     - :ev:`confirmed`

The column "Role of the switch" of the :ref:`mode table <ports-serdes-modes>` is :ev:`inferred`
from the value name :val:`SERDES.MODE.REVSGMII`. The :ref:`Linux driver <sources-list>` names value 3 100BASEX and the |ds| lists the fibre mode of
the extension ports as 100FX in the section "Extension Ports Fiber Mode (100FX/1000BX/2500BX)".

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
5. Force :reg:`PORT_CTRL` to the same speed and duplex, with the fields of the
   :ref:`forced-mode table <ports-forced>`.

Steps 4 and 5 are :ev:`confirmed` by :lx:`yt921x_port_up`, which writes :reg:`PORT_CTRL`
first, then :field:`XMII.LINK` and then :reg:`MDIO_POLLING`. It is :ev:`not known` whether the
order matters. The :ref:`Linux driver <sources-list>`
configures no xMII mode: :lx:`yt921x_port_config` accepts SerDes modes only. Steps 1 to 3 for
RGMII follow the function
`yt9215rb_init() <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/yt9215rb_mdio_driver/yt9215rb.c#L322>`__
of the :ref:`YT9215RB vendor driver <sources-list>`, which brings up RGMII on port 8 with the
writes of the :ref:`RGMII table <ports-rgmii-table>`. The modes MII and RMII are :ev:`header` definitions in :lx:`chip.h`. The three delay fields of the
:ref:`RGMII table <ports-rgmii-table>` depend on the board, and the vendor driver takes them from
its configuration.

.. _ports-rgmii-table:

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
     - :field:`XMII_CTRL.PORT` element 8
     - 1
   * - :reg:`XMII` of port 8
     - :field:`XMII.MODE`
     - :val:`XMII.MODE.RGMII`
   * - :reg:`XMII` of port 8
     - :field:`XMII.LINK`
     - 1
   * - :reg:`XMII` of port 8
     - :field:`XMII.EN`
     - 1
   * - :reg:`XMII` of port 8
     - SDK field `EN_MACMODE_LNKDN_SWH <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_struct.c#L152>`__
     - 1
   * - :reg:`XMII` of port 8
     - SDK field `RGMII_TXC_DLY100_10_EN <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_struct.c#L153>`__
     - 1
   * - :reg:`XMII` of port 8
     - :field:`XMII.RGMII_RX_DELAY_150PS`
     - board specific
   * - :reg:`XMII` of port 8
     - :field:`XMII.RGMII_TX_DELAY_150PS`
     - board specific
   * - :reg:`XMII` of port 8
     - :field:`XMII.RGMII_TX_DELAY_2NS`
     - board specific
   * - :reg:`PORT_CTRL` of port 8
     - :field:`PORT_CTRL.SPEED`
     - :val:`speed.V1000`
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

The `YT9215RB vendor driver <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/yt9215rb_mdio_driver/yt9215rb.c>`__ writes four register values. The value for :reg:`XMII` leaves out
the delay fields.

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - Register
     - Value written
   * - :reg:`IO_LEVEL`
     - ``0x0000000f``
   * - :reg:`XMII_CTRL`
     - ``0x00000002``
   * - :reg:`XMII` of port 8
     - ``0x841c0000``
   * - :reg:`PORT_CTRL` of port 8
     - ``0x000001fa``

The `YT9215RB vendor driver <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/yt9215rb_mdio_driver/yt9215rb.c>`__ writes :reg:`IO_LEVEL` only for 1.8 V RGMII pins. Its value 3 disagrees
with :lx:`chip.h`, which gives 1.8 V as 2 in :field:`IO_LEVEL.YT9215_RGMII0` and
:field:`IO_LEVEL.YT9215_RGMII1` and has no value 3. It is :ev:`not known` which is right. The
:ref:`Linux driver <sources-list>` does not name bits 26 and 20 of :reg:`XMII`. The
:ref:`vendor SDK <sources-list>` table :sdk:`EXTIF0_MODE` names bit 26
`EN_MACMODE_LNKDN_SWH <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_struct.c#L152>`__
and bit 20
`RGMII_TXC_DLY100_10_EN <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_struct.c#L153>`__.
What the two bits do is :ev:`not known`. The :ref:`YT9215RB vendor driver <sources-list>` does not write
:reg:`SERDES_CTRL` or :reg:`MDIO_POLLING`.

.. _ports-mtu:

Frame size
----------

:field:`MAC_FRAME.SIZE` is the longest frame a port accepts, counted from the destination
address to the frame check sequence. For an IP MTU of *m* bytes write *m* + 18, and
:const:`TAG_LEN` (8) more on a CPU port that carries tags. :lx:`yt921x_dsa_port_change_mtu`
computes the value in this way. The largest value is :const:`FRAME_SIZE_MAX` (9216). A
comment in the same function states that the field holds the largest value after reset, which
:ref:`sources-reset` records.

.. _ports-eee:

Energy Efficient Ethernet
-------------------------

Energy Efficient Ethernet has one enable for the whole chip and one per port.

1. Chip: set :field:`PON_STRAP_FUNC.EEE` and :field:`PON_STRAP_VAL.EEE`. This is the strap
   override of :ref:`bringup-strap-override`. Clear both when no port uses the function.
2. Port: set the port's :field:`EEE_CTRL.EN` bit and :field:`EEE_VAL.DATA` of the port.

The sequence is :ev:`confirmed` by :lx:`yt921x_set_eee`. A comment in that function reads "Poor datasheet for EEE operations", and no source explains what the four bits do individually.
