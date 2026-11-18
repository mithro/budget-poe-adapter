.. _phy:

PHYs and the MDIO masters
=========================

The built-in PHYs are not on the MDIO bus of the host. The switch has two MDIO masters of its
own, and the host reaches PHY registers by asking a master to run a frame. The registers are in
the :blk:`mbus` block.

The internal master reaches the built-in PHY of port *n* at address *n*, and the PCS of the
SerDes of port 8 or 9 at address 8 or 9. The external master reaches PHYs wired to the MDIO
master pins of the switch, at their own addresses. Each master has four registers, and the
two sets have the same layout.

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Role
     - Internal master
     - External master
   * - Start and busy bit
     - :reg:`INT_MBUS_OP`
     - :reg:`EXT_MBUS_OP`
   * - Address and operation
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
   :caption: Reading a PHY register. A write puts the value in DOUT before the start and has
             no DIN step.

The steps name the registers of the internal master; use the matching register of the table
for the external one.

1. Read :reg:`INT_MBUS_OP` until :field:`INT_MBUS_OP.START` is 0, in case a transfer is
   running.
2. Write :reg:`INT_MBUS_CTRL`: PHY address in :field:`INT_MBUS_CTRL.PORT`, register number in
   :field:`INT_MBUS_CTRL.REG`, and :val:`INT_MBUS_CTRL.OP.READ` (2) or
   :val:`INT_MBUS_CTRL.OP.WRITE` (1) in :field:`INT_MBUS_CTRL.OP`. On the external master
   also write :val:`EXT_MBUS_CTRL.TYPE.C22` (4) to :field:`EXT_MBUS_CTRL.TYPE`. Change only
   these fields; the rest of the register is not known.
3. For a write, put the value in :reg:`INT_MBUS_DOUT`.
4. Write :field:`INT_MBUS_OP.START` to :reg:`INT_MBUS_OP`.
5. Read :reg:`INT_MBUS_OP` until :field:`INT_MBUS_OP.START` is 0, as described in
   :ref:`access-wait`.
6. For a read, take the value from :reg:`INT_MBUS_DIN`.

.. yt-bitfield:: INT_MBUS_CTRL

The positions of :field:`INT_MBUS_CTRL.OP` and :field:`EXT_MBUS_CTRL.TYPE` are, in the words
of the :ref:`Linux driver <sources-list>`, a guess of its author. They work for clause 22 transfers. Clause 45 transfers are not described anywhere.

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

``yt921x_phy_read()`` and ``yt921x_phy_write()`` in
:download:`yt921x.c <../bindings/c/yt921x.c>` implement the sequence for both masters.

.. _phy-registers:

PHY registers
-------------

The built-in PHYs follow IEEE 802.3 clause 22: register 0 is basic control, 1 basic status,
2 and 3 the PHY identifier, 4 and 5 the auto-negotiation advertisement and link partner
ability, 9 and 10 the 1000BASE-T control and status. A generic PHY driver, such as the one
Zephyr or Linux provides, works on them once it is given this transfer as its bus. Vendor
specific PHY registers are outside the scope of this manual.

The SerDes PCS at address 8 or 9 uses the same register 0 bits: the :ref:`Linux driver <sources-list>` sets or
clears auto-negotiation enable (bit 12), restarts negotiation (bit 9), powers the PCS down
(bit 11) and clears isolate (bit 10) there.

.. _phy-polling:

External PHYs and link polling
------------------------------

The switch can learn the link state of an external port by polling a PHY on the external
master. How that polling is set up is not known: no public code does it. The known use of
:reg:`MDIO_POLLING` is the opposite case, a port without a PHY, where the driver writes the
link state into the register itself, as in :ref:`ports-xmii`.
