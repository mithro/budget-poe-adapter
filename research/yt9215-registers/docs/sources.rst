.. _sources:

Sources and confidence
======================

Motorcomm publishes no register documentation for these parts. This manual combines three
sources and marks how well each statement is supported.

.. _sources-list:

Sources
-------

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Source
     - Version
   * - `Linux driver <https://github.com/torvalds/linux/tree/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm>`__
     - Commit ``20eef29b7c84`` of the mainline kernel
   * - `Vendor SDK <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/tree/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e>`__
     - Commit ``d2c8d6fc721f`` of a public mirror
   * - :download:`YT9215SCH datasheet <../../../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf>`
     - V1.03

The Linux driver provides the register and field names with their addresses, and working code
that shows how they are used. It is in
`drivers/net/dsa/motorcomm/ <https://github.com/torvalds/linux/tree/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm>`__, with the tag format in
`net/dsa/tag_yt921x.c <https://github.com/torvalds/linux/tree/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/net/dsa/tag_yt921x.c>`__. Where a guide page says a step is
confirmed by the Linux driver, the reference entries of the registers involved link to the
lines of the driver header.

The vendor SDK provides a list of all register tables with field positions, and driver code
that uses them, but no register descriptions. It also contains a small
`MDIO driver for the YT9215RB <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/tree/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/yt9215rb_mdio_driver>`__.

The datasheet provides the pins, the strap pins and the timing of the management interface.
It contains no register addresses.

.. _evidence:

Evidence levels
---------------

Every register and field in the reference has one of three levels.

.. list-table::
   :header-rows: 1
   :widths: 16 84

   * - Level
     - Meaning
   * - driver
     - The Linux driver reads or writes the item. The description follows what the code does.
   * - header
     - The Linux driver header defines the item, with a name and values that leave little
       doubt, but no code uses it.
   * - inferred
     - The description is deduced from the name of the item and from the name the vendor SDK
       gives the same bits. It may be wrong.

.. _sources-sdk:

Comparison with the vendor SDK
------------------------------

The Sources table of each register compares every field with the SDK table at the same
address.

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - SDK comparison
     - Meaning
   * - same bits
     - The SDK has a field with the same position and width.
   * - part of SDK field
     - The field lies inside a wider SDK field.
   * - spans SDK fields
     - The field covers several SDK fields, which are listed one per row.
   * - SDK lists no fields
     - The SDK has the table but describes it as one opaque value.
   * - no SDK table
     - The SDK register list has no table at this address.
   * - not in SDK
     - The SDK has the table but no field at these bits.

What is not known
-----------------

Nothing here has been run on a YT921x by this project; the code is tested against a software
model. The topics of this table are open.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Topic
     - Where it matters
   * - Reset values
     - :ref:`sources-reset`
   * - YT9215SCH identification
     - :ref:`bringup-identify`
   * - Registers beyond the reference
     - :ref:`reference-sdk`
   * - Order of processing stages
     - :ref:`overview-frame-path`
   * - Duration of reset and table commands
     - :ref:`access-wait`
   * - xMII modes other than RGMII
     - :ref:`ports-xmii`
   * - Filtering IDs
     - :field:`VLAN_CTRL.FID`
   * - Shared VLAN learning
     - :field:`VLAN_CTRL.SVLAN_EN`
   * - Scale of the temperature reading
     - :reg:`TEMP`
   * - Clause 45 MDIO
     - :ref:`phy-mbus`
   * - SPI and I2C host interfaces
     - :ref:`access-straps`

The vendor SDK lists more than twice as many tables as this manual describes; the meaning of
the others is known by name only. Functions that exist only there include interrupts, queue
scheduling, storm control, loop detection, IGMP snooping and the handling of reserved
multicast addresses such as spanning tree BPDUs.

.. _sources-reset:

Reset values
~~~~~~~~~~~~

Two reset values are known, both from the Linux driver. Write every other register a function
depends on.

.. list-table::
   :header-rows: 1
   :widths: 60 40

   * - Field
     - Reset value
   * - :field:`CPU_TAG_TPID.TPID`
     - ``0x9988``
   * - :field:`PORT_RATE.GAP_VALUE`
     - ``0x14``
