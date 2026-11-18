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
   :widths: 22 34 44

   * - Source
     - Version
     - Provides
   * - `Linux driver <https://github.com/torvalds/linux/tree/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm>`__
     - Commit ``20eef29b7c84`` of the mainline kernel
     - Register and field names with addresses, and working code that shows how they are used
   * - `Vendor SDK <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/tree/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e>`__
     - Commit ``d2c8d6fc721f`` of a public mirror
     - A list of all register tables with field positions, and driver code that uses them; no
       register descriptions
   * - :download:`YT9215SCH datasheet <../../../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf>`
     - V1.03
     - Pins, straps and the management interface timing; no register addresses

The Linux driver is in ``drivers/net/dsa/motorcomm/`` with the tag format in
``net/dsa/tag_yt921x.c``. Each register in the reference links to the line of the driver
header that defines it and to the SDK table at the same address.

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

.. _sources-unknown:

What is not known
-----------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Topic
     - State
   * - Reset values
     - Unknown except for :reg:`CPU_TAG_TPID`. Write every register a function depends on.
   * - Hardware testing
     - Nothing here has been run on a YT921x by this project. The code is tested against a
       software model.
   * - YT9215SCH identification
     - Assumed to match the :chip:`YT9215SC`.
   * - Registers beyond the reference
     - The :ref:`vendor SDK tables <reference-sdk>` list more than twice as many tables as
       this manual describes; their meaning is known by name only.
   * - Order of processing stages
     - Only partly confirmed; see :ref:`overview-frame-path`.
   * - Command timing
     - How long reset and table commands take is not published; see :ref:`access-wait`.
   * - xMII configuration
     - Public code exists for RGMII only; see :ref:`ports-xmii`.
   * - Filtering IDs
     - :field:`VLAN_CTRL.FID` and :field:`VLAN_CTRL.SVLAN_EN` are not used by any driver.
   * - Temperature
     - The scale of :reg:`TEMP` is unknown.
   * - Clause 45 MDIO
     - The MDIO masters are described for clause 22 only; see :ref:`phy-mbus`.
