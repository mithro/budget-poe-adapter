.. _phy:

PHYs and the MDIO masters
=========================

The built-in PHYs are not on the MDIO bus of the host. The switch has two MDIO masters of its
own, and the host reaches PHY registers by asking a master to run a frame. The registers are in
the :blk:`mbus` block.

.. list-table::
   :header-rows: 1
   :widths: 16 34 50

   * - Master
     - Registers
     - Devices
   * - Internal
     - :reg:`INT_MBUS_OP`, :reg:`INT_MBUS_CTRL`, :reg:`INT_MBUS_DOUT`, :reg:`INT_MBUS_DIN`
     - The built-in PHY of port *n* at address *n*, and the PCS of the SerDes of port 8 or 9
       at address 8 or 9.
   * - External
     - :reg:`EXT_MBUS_OP`, :reg:`EXT_MBUS_CTRL`, :reg:`EXT_MBUS_DOUT`, :reg:`EXT_MBUS_DIN`
     - PHYs wired to the MDIO master pins of the switch, at their own addresses.

The two register sets have the same layout.

.. _phy-mbus:

MDIO master transfer
--------------------

.. yt-diagram:: mbus-sequence
   :caption: Reading a PHY register. A write puts the value in DOUT before the start and has
             no DIN step.

1. Read the OP register until :field:`INT_MBUS_OP.START` is 0, in case a transfer is running.
2. Write the CTRL register: PHY address in :field:`INT_MBUS_CTRL.PORT`, register number in
   :field:`INT_MBUS_CTRL.REG`, and READ (2) or WRITE (1) in :field:`INT_MBUS_CTRL.OP`. On the
   external master also write C22 (4) to :field:`EXT_MBUS_CTRL.TYPE`. Change only these
   fields; the rest of the register is not known.
3. For a write, put the value in the DOUT register.
4. Write START to the OP register.
5. Read the OP register until START is 0, as described in :ref:`access-wait`.
6. For a read, take the value from the DIN register.

.. yt-bitfield:: INT_MBUS_CTRL

The positions of the OP and TYPE fields are, in the words of the Linux driver, a guess of its
author. They work for clause 22 transfers. Clause 45 transfers are not described anywhere.

.. tab-set::

   .. tab-item:: C
      :sync: c

      .. literalinclude:: ../bindings/c/examples/guide.c
           :language: c
           :start-after: /* [phy] */
           :end-before: /* [phy end] */

   .. tab-item:: MicroPython
      :sync: micropython

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

The SerDes PCS at address 8 or 9 uses the same register 0 bits: the Linux driver sets or
clears auto-negotiation enable (bit 12), restarts negotiation (bit 9), powers the PCS down
(bit 11) and clears isolate (bit 10) there.

.. _phy-polling:

External PHYs and link polling
------------------------------

The switch can learn the link state of an external port by polling a PHY on the external
master. When there is no such PHY, the driver supplies the link state in
:reg:`MDIO_POLLING`, as in :ref:`ports-xmii`.
