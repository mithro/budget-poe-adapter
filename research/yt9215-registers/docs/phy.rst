.. _phy:

PHYs and the MDIO masters
=========================

The built-in PHYs are not on the MDIO bus of the host. The switch has two MDIO masters of its
own, and the host reaches PHY registers by asking a master to run a frame. The registers are in
the :blk:`mbus` block.

The internal master reaches the built-in PHY of port *n* at address *n*, and the PCS of the
SerDes of port 8 or 9 at address 8 or 9. :lx:`yt921x_serdes_config` of the
:ref:`Linux driver <sources-list>` reaches the PCS in this way, and :lx:`yt921x_mbus_int_read`
passes the port number as the address of a PHY. The external master reaches
PHYs wired to the MDIO master pins of the switch, at their own addresses. Tables 16 and 17
of the |ds| name the pins of the two MDIO master groups: SMI1_MDC with SMI1_MDIO, and
SMI2_MDC with SMI2_MDIO. The file `fal_tiger_init.c <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_init.c#L119>`__ of the :ref:`vendor SDK <sources-list>` sets bit 2 of the address ``0x80358`` for two
boards under the comment "select mdio grp1 pin", so the group is selectable. This manual
does not describe that register, and it is :ev:`not known` which group the external master
drives after reset. Each
master has four registers, and :lx:`mdio_bus.h` defines the fields of the two sets under common
names.

.. _phy-registers-table:

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Role
     - Internal master
     - External master
   * - Start bit
     - :reg:`INT_MBUS_OP`
     - :reg:`EXT_MBUS_OP`
   * - Transfer set-up
     - :reg:`INT_MBUS_CTRL`
     - :reg:`EXT_MBUS_CTRL`
   * - Value to write
     - :reg:`INT_MBUS_DOUT`
     - :reg:`EXT_MBUS_DOUT`
   * - Value read
     - :reg:`INT_MBUS_DIN`
     - :reg:`EXT_MBUS_DIN`

.. _phy-mbus:

MDIO master transfer
--------------------

.. yt-diagram:: mbus-sequence
   :caption: Reading a PHY register. A write puts the value in the data-out register before
             the start and does not read the data-in register.

The steps name the registers of the internal master. For the external master, use the
register in the same row of the :ref:`register table <phy-registers-table>`.

1. Read :reg:`INT_MBUS_OP` until :field:`INT_MBUS_OP.START` is 0, in case a transfer is
   running.
2. Write :reg:`INT_MBUS_CTRL`: PHY address in :field:`INT_MBUS_CTRL.PORT`, register number in
   :field:`INT_MBUS_CTRL.REG`, and :val:`INT_MBUS_CTRL.OP.READ` or
   :val:`INT_MBUS_CTRL.OP.WRITE` in :field:`INT_MBUS_CTRL.OP`. On the external master also
   write :val:`EXT_MBUS_CTRL.TYPE.C22` to :field:`EXT_MBUS_CTRL.TYPE`. Change only these
   fields, because the other bits of the register are :ev:`not known`.
3. For a write, put the value in :reg:`INT_MBUS_DOUT`.
4. Write :field:`INT_MBUS_OP.START` to :reg:`INT_MBUS_OP`.
5. Read :reg:`INT_MBUS_OP` until :field:`INT_MBUS_OP.START` is 0, with the loop of
   :ref:`access-wait`.
6. For a read, take the value from :reg:`INT_MBUS_DIN`.

The six steps are :ev:`confirmed` by :lx:`yt921x_intif_read` and :lx:`yt921x_intif_write`
for the internal master and by :lx:`yt921x_extif_read` and :lx:`yt921x_extif_write` for the
external master.

.. yt-bitfield:: INT_MBUS_CTRL

The comments in :lx:`mdio_bus.h:22` and :lx:`mdio_bus.h:25` read "wild guess". The two
definitions on those lines serve both masters, so the widths of :field:`INT_MBUS_CTRL.TYPE`, :field:`INT_MBUS_CTRL.OP`, :field:`EXT_MBUS_CTRL.TYPE`
and :field:`EXT_MBUS_CTRL.OP` are :ev:`inferred`. The two functions for the external master write :val:`EXT_MBUS_CTRL.TYPE.C22` for
`clause 22 <https://en.wikipedia.org/wiki/Management_Data_Input/Output>`__ transfers. A
:lx:`comment <mdio_bus.c:287>` in :lx:`yt921x_mbus_ext_init` reads "TODO: c45?", and no source
describes a
`clause 45 <https://en.wikipedia.org/wiki/Management_Data_Input/Output>`__ transfer.

.. tab-set::

   .. tab-item:: C
      :sync: c

      From :download:`guide.c <../bindings/c/examples/guide.c>`.

      .. literalinclude:: ../bindings/c/examples/guide.c
           :language: c
           :start-after: /* [phy] */
           :end-before: /* [phy end] */

   .. tab-item:: MicroPython
      :sync: micropython

      From :download:`guide.py <../bindings/micropython/examples/guide.py>`.

      .. literalinclude:: ../bindings/micropython/examples/guide.py
           :language: python
           :start-after: # [phy]
           :end-before: # [phy end]

The functions :ref:`yt921x_phy_read() <bindings-api>` and
:ref:`yt921x_phy_write() <bindings-api>` of
:download:`yt921x.c <../bindings/c/yt921x.c>` implement the sequence for both masters.

.. _phy-registers:

PHY registers
-------------

The :ref:`Linux driver <sources-list>` registers the internal master as an ordinary MDIO bus in
:lx:`yt921x_mbus_int_init` and leaves the built-in PHYs to the generic PHY code of the kernel,
which uses the registers that
`IEEE 802.3 clause 22 <https://en.wikipedia.org/wiki/Management_Data_Input/Output>`__ defines.

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - PHY register
     - Content in `IEEE 802.3 clause 22 <https://en.wikipedia.org/wiki/Management_Data_Input/Output>`__
   * - 0
     - Basic control
   * - 1
     - Basic status
   * - 2
     - High half of the PHY identifier
   * - 3
     - Low half of the PHY identifier
   * - 4
     - Auto-negotiation advertisement
   * - 5
     - Link partner ability
   * - 9
     - 1000BASE-T control
   * - 10
     - 1000BASE-T status

A generic PHY driver of another system, such as Zephyr, needs the
:ref:`transfer <phy-mbus>` as its bus. Vendor specific PHY registers are outside the scope of
this manual.

The SerDes PCS at address 8 or 9 uses bits of register 0 with their
`clause 22 <https://en.wikipedia.org/wiki/Management_Data_Input/Output>`__ meaning.

.. list-table::
   :header-rows: 1
   :widths: 14 36 50

   * - Bit
     - Name in `clause 22 <https://en.wikipedia.org/wiki/Management_Data_Input/Output>`__
     - Function of the :ref:`Linux driver <sources-list>` that writes it
   * - 12
     - Auto-negotiation enable
     - :lx:`yt921x_serdes_config`
   * - 11
     - Power down
     - :lx:`yt921x_phylink_pcs_disable`
   * - 11
     - Power down
     - :lx:`yt921x_phylink_pcs_enable`
   * - 9
     - Restart auto-negotiation
     - :lx:`yt921x_phylink_pcs_enable`
   * - 10
     - Isolate
     - :lx:`yt921x_serdes_config`
   * - 9
     - Restart auto-negotiation
     - :lx:`yt921x_phylink_pcs_an_restart`

.. _phy-polling:

External PHYs and link polling
------------------------------

It is :ev:`inferred` from the name of :reg:`MDIO_POLLING` that the switch can learn the link state
of an external port by polling a PHY on the external master. It is :ev:`not known` how that
polling is set up. The :ev:`confirmed` use of the register is an external port that does not use its SerDes:
:lx:`yt921x_port_up` writes the link state into :reg:`MDIO_POLLING` itself, which is step 4 of
:ref:`ports-xmii`.
