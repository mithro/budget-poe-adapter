.. _bringup:

Reset and bring-up
==================

This page takes the switch from power-on to a known state. The registers are in the
:blk:`system` block.

.. _bringup-probe:

Find the switch
---------------

Read :reg:`CHIP_ID` at PHY address ``0x1d`` and, if the family code is not one of the two known
values, at ``0x00``. On a board that straps a switch ID other than 0, use that ID in every access.
:ref:`access-straps` lists the pins. :lx:`yt921x_chip_detect` of the
:ref:`Linux driver <sources-list>` reads :reg:`CHIP_ID` before the reset, at the one PHY address
that its device tree node gives.

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - :field:`CHIP_ID.MAJOR`
     - Constant
     - Family
   * - ``0x9002``
     - :const:`MAJOR_YT9215`
     - :ref:`YT9215 family <reference-parts>`
   * - ``0x9001``
     - :const:`MAJOR_YT9218`
     - :ref:`YT9218 family <reference-parts>`

:ref:`reference-parts` lists the parts of each family.

.. _bringup-reset:

Reset
-----

.. yt-diagram:: reset-sequence
   :caption: Reset followed by identification.

1. Write :reg:`RST` with only :field:`RST.HW` set.
2. Wait 10 ms (:const:`RST_DELAY_US`).
3. Read :reg:`RST` until the whole register is 0, with the loop of :ref:`access-wait`.
4. Read :reg:`CPU_TAG_TPID` and check for ``0x9988``, the test of :ref:`access-check`.

The four steps are :ev:`confirmed` by :lx:`yt921x_chip_reset` of the
:ref:`Linux driver <sources-list>`, which performs them in this order.

Section 4.1.2.1 of the |ds| calls :field:`RST.HW` CHIP_RESET and lists what it does: all
digital and analog circuits return to their defaults, the lookup and VLAN tables are cleared,
a configuration is loaded again from an EEPROM or from flash where the strap pins ask for it,
and the PHYs restart auto-negotiation. The bit clears itself.

Section 4.1.2.2 calls :field:`RST.SW` SW_RESET and states that it does the same except that
the analog circuits of the PHYs are not reset. The :ref:`Linux driver <sources-list>` does not use
:field:`RST.SW`.

The reset pin is nRESET, pin 89 of the YT9215SCH in table 23 of the |ds|. Section 4.1.1
requires it to be low for at least 10 ms. A board that uses the register reset can leave the
pin on its pull-up resistor.

.. _bringup-identify:

Identify the part
-----------------

Three values together name the part: the family code :field:`CHIP_ID.MAJOR`, the mode
:field:`CHIP_MODE.MODE`, and one byte of the configuration byte store, called the extended
mode. :ref:`reference-parts` has the value of each for every part and
:ref:`reference-parts-ports` the ports each part has. A driver needs the part to know which
of ports 8 and 9 exist and whether they have a SerDes or xMII pins.

The configuration byte store is this manual's name for what the
:ref:`Linux driver <sources-list>` calls EDATA. It is a memory of :const:`EDATA_LEN` (256)
bytes inside the chip. The extended mode is the byte at address ``0xfb``
(:const:`EDATA_EXTMODE`). The Linux driver only reads the store, in :lx:`yt921x_edata_read`,
and no source describes a write.

.. yt-diagram:: edata-sequence
   :caption: Reading one byte of the configuration byte store.

1. Read :reg:`EDATA_DATA` until :field:`EDATA_DATA.STATUS` is
   :val:`EDATA_DATA.STATUS.IDLE`.
2. Write :reg:`EDATA_CTRL` with the byte address in :field:`EDATA_CTRL.ADDR` and
   :val:`EDATA_CTRL.OP.READ` in :field:`EDATA_CTRL.OP`.
3. Read :reg:`EDATA_DATA` until :field:`EDATA_DATA.STATUS` is
   :val:`EDATA_DATA.STATUS.IDLE` again. :field:`EDATA_DATA.DATA` then holds the byte.

The three steps are :ev:`confirmed` by :lx:`yt921x_edata_read`.

.. tab-set::

   .. tab-item:: C
      :sync: c

      From :download:`guide.c <../bindings/c/examples/guide.c>`.

      .. literalinclude:: ../bindings/c/examples/guide.c
           :language: c
           :start-after: /* [bringup] */
           :end-before: /* [bringup end] */

   .. tab-item:: MicroPython
      :sync: micropython

      From :download:`guide.py <../bindings/micropython/examples/guide.py>`.

      .. literalinclude:: ../bindings/micropython/examples/guide.py
           :language: python
           :start-after: # [bringup]
           :end-before: # [bringup end]

The functions ``yt921x_reset()`` and ``yt921x_identify()`` are in
:download:`yt921x.c <../bindings/c/yt921x.c>`.

.. _bringup-sch:

The part table of the :ref:`Linux driver <sources-list>`, which :lx:`yt921x_chip_detect` searches,
has no entry for the :chip:`YT9215SCH`. No source gives the identification values of that part.
This manual assumes the values of the :chip:`YT9215SC`, because the |ds| gives the YT9215SCH the
package and pin numbers that the :doc:`debug pin note </research/motorcomm-debug-pins>` records
for the YT9215SC. The assumption is :ev:`inferred`.

.. _bringup-clock:

Core clock
----------

:field:`SYS_CLK.SEL` shows which core clock the part runs from. Only the meters and shapers
need it, because their time slots count core clock periods. :ref:`rate-tokens` uses the
period of the :ref:`clock table <bringup-clock-table>`. The periods are those that
:lx:`yt921x_chip_detect` assigns for each value. The frequencies are the names of the values
in :lx:`chip.h:178`.

.. _bringup-clock-table:

.. list-table::
   :header-rows: 1
   :widths: 25 25 25 25

   * - Family
     - :field:`SYS_CLK.SEL`
     - Core clock
     - Period
   * - :ref:`YT9215 <reference-parts>`
     - 0
     - 125 MHz
     - 8 ns
   * - :ref:`YT9218 <reference-parts>`
     - 0
     - 167 MHz
     - 6 ns
   * - :ref:`YT9215 <reference-parts>`
     - 1
     - 143 MHz
     - 7 ns
   * - :ref:`YT9218 <reference-parts>`
     - 1
     - 143 MHz
     - 7 ns

For the values 2 and 3 the function assumes 8 ns. No source names a clock for them.

.. _bringup-features:

Turn on function blocks
-----------------------

Three function blocks work only while their bit in :reg:`FUNC` is set.
:lx:`yt921x_chip_setup` of the :ref:`Linux driver <sources-list>` sets the three bits before
it uses the blocks. It is :ev:`inferred` from that code that the bits are clear after reset.

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Bit
     - Block
     - Guide page
   * - :field:`FUNC.MIB`
     - :blk:`mib`
     - :doc:`mib`
   * - :field:`FUNC.ACL`
     - :blk:`acl`
     - :doc:`acl`
   * - :field:`FUNC.METER`
     - :blk:`meter`
     - :doc:`rate`

.. tab-set::

   .. tab-item:: C
      :sync: c

      From :download:`guide.c <../bindings/c/examples/guide.c>`.

      .. literalinclude:: ../bindings/c/examples/guide.c
           :language: c
           :start-after: /* [features] */
           :end-before: /* [features end] */

   .. tab-item:: MicroPython
      :sync: micropython

      From :download:`guide.py <../bindings/micropython/examples/guide.py>`.

      .. literalinclude:: ../bindings/micropython/examples/guide.py
           :language: python
           :start-after: # [features]
           :end-before: # [features end]

.. _bringup-straps:

Other registers of the system block
-----------------------------------

.. _bringup-strap-override:

Strap overrides
~~~~~~~~~~~~~~~

Some settings are sampled from strap pins at power-on. To override a strap, write the wanted
value to :reg:`PON_STRAP_VAL` and set the same bit in :reg:`PON_STRAP_FUNC`.
:lx:`yt921x_set_eee` does this for Energy Efficient Ethernet, which :ref:`ports-eee`
describes. That override is the only one that is :ev:`confirmed`. It is :ev:`inferred` from
the name of :reg:`PON_STRAP_CAP` that the register shows the sampled levels.

.. _bringup-io-level:

I/O voltage
~~~~~~~~~~~

:reg:`IO_LEVEL` sets the signalling voltage of the digital pins and of each xMII interface.
Its field positions differ between the two families, so a driver has to identify the part
first. The fields have the level :ev:`header`: :lx:`chip.h` defines them and no function of
the :ref:`Linux driver <sources-list>` writes them. :ref:`ports-xmii` shows the one use, in the
:ref:`YT9215RB vendor driver <sources-list>`.

.. _bringup-temp:

Temperature sensor
~~~~~~~~~~~~~~~~~~

Set :field:`SENSOR.TEMP` to start the temperature sensor, as :lx:`yt921x_chip_setup` does,
and read :reg:`TEMP` for a raw value. The conversion to degrees is :ev:`not known`.

.. _bringup-mac:

Switch MAC address
~~~~~~~~~~~~~~~~~~

:reg:`MAC_ADDR_HI2` and :reg:`MAC_ADDR_LO4` hold a MAC address of the switch itself. It is
:ev:`inferred` from the register names that the switch uses it as the source address of
frames it generates, such as pause frames. No function of the :ref:`Linux driver <sources-list>`
writes the two
registers.

.. _bringup-next:

After bring-up
--------------

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - Next task
     - Page
   * - Choose the CPU port and its tagging
     - :doc:`cpu-tag`
   * - Enable the ports
     - :doc:`ports`
   * - Reach the PHYs
     - :doc:`phy`
   * - Separate or bridge ports
     - :doc:`forwarding`
