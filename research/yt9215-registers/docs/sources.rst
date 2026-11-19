.. _sources:

Sources and evidence
====================

Motorcomm publishes no register documentation for these parts. This manual combines the four
sources of the :ref:`source list <sources-list>` and marks every register, field and
procedure with one of the :ref:`evidence levels <evidence>`.

.. _sources-list:

Sources
-------

.. list-table::
   :header-rows: 1
   :widths: 24 30 18 28

   * - Source
     - Repository
     - Revision
     - Provides
   * - `Linux driver <https://github.com/torvalds/linux/tree/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm>`__
     - `torvalds/linux <https://github.com/torvalds/linux>`__
     - `20eef29b7c84 <https://github.com/torvalds/linux/commit/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca>`__
     - Register names
   * - `Vendor SDK <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/tree/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk>`__
     - `OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk>`__
     - `d2c8d6fc721f <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/commit/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e>`__
     - Bit positions
   * - `YT9215RB vendor driver <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/tree/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/yt9215rb_mdio_driver>`__
     - `OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk>`__
     - `d2c8d6fc721f <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/commit/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e>`__
     - RGMII set-up code
   * - :download:`YT9215SCH datasheet <../../../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf>`
     - none
     - V1.03
     - Pins

The :ref:`Linux driver <sources-list>` is the directory
`drivers/net/dsa/motorcomm <https://github.com/torvalds/linux/tree/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm>`__
of the mainline kernel together with the tag format in :lx:`tag_yt921x.c`. Its headers
(:lx:`chip.h`, :lx:`tc.h`, :lx:`mdio_bus.h`, :lx:`mib.h`, :lx:`leds.h`) define the register
and field names with their addresses. Every function of the driver that this manual names is
a link to its definition at the commit of the :ref:`source list <sources-list>`.

The :ref:`vendor SDK <sources-list>` is the directory
`switch_sdk <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/tree/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk>`__
of a public copy of the Motorcomm SDK. It
holds a list of all register tables with field positions, and driver code that uses them,
but no register descriptions. :ref:`reference-sdk` lists every table.

The :ref:`YT9215RB vendor driver <sources-list>` is the single file
`yt9215rb.c <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/yt9215rb_mdio_driver/yt9215rb.c>`__ in the same repository as the
:ref:`vendor SDK <sources-list>`.

The |ds| gives the pins, the strap pins and the timing of the management interface. The only
register address it contains is that of :reg:`RST`, in its section 4.1.2.

.. _evidence:

Evidence levels
---------------

Every register and field in the :ref:`reference <reference>` has one of the levels
:ref:`driver <evidence-driver>`, :ref:`header <evidence-header>` and
:ref:`inferred <evidence-inferred>` of the :ref:`level table <evidence-table>`. The guide pages
use the words of its column "Word in the guide"; each use of such a word is a link to its row.

.. _evidence-table:

.. list-table::
   :header-rows: 1
   :widths: 14 18 34 34

   * - Level
     - Word in the guide
     - Source of the statement
     - Where the source is cited
   * - .. _evidence-driver:

       driver
     - confirmed
     - Code of the :ref:`Linux driver <sources-list>`
     - Row "First used in" of the register
   * - .. _evidence-header:

       header
     - header
     - Header of the :ref:`Linux driver <sources-list>`
     - Row "Linux name" of the register
   * - .. _evidence-inferred:

       inferred
     - inferred
     - Names in the :ref:`sources <sources-list>`
     - Sentence that makes the statement
   * - .. _evidence-datasheet:

       datasheet
     - datasheet
     - |ds|
     - Sentence that makes the statement
   * - .. _evidence-unknown:

       none
     - not known
     - No source
     - :ref:`sources-open`

The levels describe the :ref:`Linux driver <sources-list>`. Where code of the
:ref:`vendor SDK <sources-list>` states what the Linux driver does not, the sentence names
the SDK function or file as a link to its line, and the level of the field in the reference
stays :ev:`header` or :ev:`inferred`.

A statement with the level :ref:`driver <evidence-driver>` follows what the code does. A
:ev:`header` definition that no
code uses carries a name and often a list of values, which is taken at face value. An
:ev:`inferred` statement is a reading of names in the :ref:`Linux driver <sources-list>` or the
:ref:`vendor SDK <sources-list>` and can be wrong. A :ev:`datasheet` statement names the table, figure or section of the |ds| that it rests
on. The reference does not use this level; the notes on the two reset bits of :reg:`RST` cite a
section of the |ds| in addition to their own level.

The level :ref:`driver <evidence-driver>` of a field means that some function of the :ref:`Linux driver <sources-list>`
reads or writes the field. A use is a line of code that names the field or one of its values,
or that moves the bits of the field without a name; a write of 0 to the whole register is not
a use of its fields. The reference names the first such function in the row or column "First used
in", as a link to the line of code. A field that is the only field of its register shares the
level of the register.

.. _sources-sdk:

Comparison with the vendor SDK
------------------------------

The reference compares every field with the :ref:`vendor SDK <sources-list>` table at the same
address. Each register of the reference has the comparison under its heading "Sources of the
fields", in the columns "SDK field" and "SDK comparison". For an
array field whose elements are separated by other bits, the comparison is that of element 0.

.. list-table::
   :header-rows: 1
   :widths: 24 38 38

   * - SDK comparison
     - SDK table at the address
     - SDK field at the bits
   * - .. _sdk-same:

       same bits
     - present
     - identical bits
   * - .. _sdk-part:

       part of SDK field
     - present
     - wider than the field
   * - .. _sdk-spans:

       spans SDK fields
     - present
     - several inside the field
   * - .. _sdk-notin:

       not in SDK
     - present
     - none
   * - .. _sdk-nofields:

       SDK lists no fields
     - present without fields
     - none
   * - .. _sdk-notable:

       no SDK table
     - absent
     - none

A field that spans several SDK fields has one row per SDK field. The row "SDK table" of a
register names the table. Where the :ref:`vendor SDK <sources-list>` has no table at the address but its code uses the
address as a number, the row reads "address constant" and links to that line of the SDK.

.. _sources-open:

Open topics
-----------

No part of this manual and none of its code has been run on a YT921x. The code is tested
against the :ref:`software model <bindings-tests>` only. This manual leaves open the topics of the
:ref:`open-topic table <sources-open-table>`.

.. _sources-open-table:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Topic
     - Section that depends on it
   * - Reset values of most registers
     - :ref:`sources-reset`
   * - :chip:`YT9215SCH` identification
     - :ref:`bringup-identify`
   * - Registers outside the reference
     - :ref:`reference-sdk`
   * - Order of processing stages
     - :ref:`overview-frame-path`
   * - Duration of reset
     - :ref:`access-wait`
   * - Duration of table commands
     - :ref:`access-wait`
   * - MDIO `clause 45 <https://en.wikipedia.org/wiki/Management_Data_Input/Output>`__
     - :ref:`phy-mbus`

The :ref:`vendor SDK <sources-list>` lists 237 tables and the reference describes 101 registers.
This manual does not describe the other tables. :ref:`reference-sdk` lists them by address region.

.. _sources-reset:

Reset values
------------

The :ref:`Linux driver <sources-list>` states the reset values of two fields and the reset
state of a third. A driver writes every other
register that a function depends on before it uses the function.

.. list-table::
   :header-rows: 1
   :widths: 34 16 50

   * - Field
     - Reset value
     - Stated in
   * - :field:`CPU_TAG_TPID.TPID`
     - ``0x9988``
     - :lx:`Definition of the default value <chip.h:41>`
   * - :field:`PORT_RATE.GAP_VALUE`
     - 20
     - :lx:`Comment on the field <tc.h:271>`
   * - :field:`MAC_FRAME.SIZE`
     - 9216
     - :lx:`Comment in yt921x_dsa_port_change_mtu() <chip.c:241>`

The comment on :field:`MAC_FRAME.SIZE` reads "always set to maximum after reset". The value
9216 is :const:`FRAME_SIZE_MAX`, the size from which :lx:`yt921x_dsa_port_max_mtu`
computes the largest MTU, so the reset value of the field is :ev:`inferred`.
