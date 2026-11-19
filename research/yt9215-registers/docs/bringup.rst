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

Section 4.1.2.2 of the |ds| calls :field:`RST.SW` SW_RESET and states that it does the same except that
the analog circuits of the PHYs are not reset. The :ref:`Linux driver <sources-list>` does not use
:field:`RST.SW`.

The reset pin is nRESET, pin 89 of the :chip:`YT9215SCH` in table 23 of the |ds|. Section 4.1.1
requires it to be low for at least 10 ms. The same section states that the hardware reset is to be
applied after power-on.

.. _bringup-identify:

Identify the part
-----------------

Three values together name the part: the family code :field:`CHIP_ID.MAJOR`, the mode
:field:`CHIP_MODE.MODE`, and one byte of the configuration byte store, called the extended
mode. :ref:`reference-parts` has the value of each for every part and
:ref:`reference-parts-ports` the ports of each part that the
:ref:`Linux driver <sources-list>` identifies. A driver needs the part to know which
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

The functions :ref:`yt921x_reset() <bindings-api>` and
:ref:`yt921x_identify() <bindings-api>` are in
:download:`yt921x.c <../bindings/c/yt921x.c>`.

.. _bringup-sch:

The part table of the :ref:`Linux driver <sources-list>`, which :lx:`yt921x_chip_detect` searches,
has no entry for the :chip:`YT9215SCH`. No source gives the identification values of that part.
This manual assumes the values of the :chip:`YT9215SC`, because the |ds| gives the :chip:`YT9215SCH` the
package and pin numbers that the :doc:`debug pin note </research/motorcomm-debug-pins>` records
for the :chip:`YT9215SC`. Whether the assumption is right is :ev:`not known`.

The :ref:`vendor SDK <sources-list>` function
`fal_tiger_sys_chipInfo_get() <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_sys.c#L79>`__
identifies the parts in a different way from :lx:`yt921x_chip_detect`, which compares the
whole extended mode byte. The SDK function compares each half of the byte on its own. For
the mode of the :chip:`YT9215S` it reports a part YT9215SL when either half is 1; the
:ref:`Linux driver <sources-list>` has no such part. For the mode of the :chip:`YT9215RB` it
reports the :chip:`YT9214NB` when either half is 2 and otherwise the :chip:`YT9213NB` when
either half is 3. It does not use the byte for the other parts, and it calls the :chip:`YT9218MB` YT9218M.
It has no case for the :chip:`YT9215SCH` either.

.. _bringup-clock:

Core clock
----------

:field:`SYS_CLK.SEL` shows which core clock the part runs from. Only the meters and shapers
need it, because their time slots count core clock periods. :ref:`rate-tokens` uses the
period of the :ref:`clock table <bringup-clock-table>`. The periods are those that
:lx:`yt921x_chip_detect` assigns for each value. The frequencies are the names of the values
in :lx:`chip.h:179`. A comment in :lx:`chip.h:178` reads "unknown: 167M"; what it refers to is
:ev:`not known`.

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

For the values 2 and 3 :lx:`yt921x_chip_detect` assumes 8 ns. No source names a clock for them.

.. _bringup-features:

Turn on function blocks
-----------------------

Three function blocks have an enable bit in :reg:`FUNC` that the
:ref:`Linux driver <sources-list>` names. The :ref:`vendor SDK <sources-list>` names a
fourth, `AC_EN <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_struct.c#L16>`__ in bit 3, which this manual does not describe.
:lx:`yt921x_chip_setup` of the :ref:`Linux driver <sources-list>` sets the three bits before
it uses the blocks. It is :ev:`inferred` from that code that a block works only while its bit is
set and that the bits are clear after reset.

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

Some settings are sampled from strap pins at power-on. It is :ev:`inferred` from the register
names that a bit in :reg:`PON_STRAP_FUNC` makes the switch use the same bit of
:reg:`PON_STRAP_VAL` in place of the strap. :lx:`yt921x_set_eee` sets the EEE bit in both
registers to turn Energy Efficient Ethernet on and clears both to turn it off, which
:ref:`ports-eee` describes. Writing both bits alike is the only use that is :ev:`confirmed`. It is :ev:`inferred` from
the name of :reg:`PON_STRAP_CAP` that the register shows the sampled levels.

.. _bringup-io-level:

I/O voltage
~~~~~~~~~~~

:reg:`IO_LEVEL` sets the signalling voltage of the digital pins and of each xMII interface.
Its field positions differ between the two families, so a driver has to identify the part
first. The fields have the level :ev:`header`: :lx:`chip.h` defines them and no function of
the :ref:`Linux driver <sources-list>` writes them. :ref:`ports-xmii` shows the write of the
:ref:`YT9215RB vendor driver <sources-list>`. The :ref:`vendor SDK <sources-list>` function
`fal_tiger_port_dvddio_power_level_set() <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_port.c#L1820>`__
writes the register with the values of :lx:`chip.h`.

.. _bringup-temp:

Temperature sensor
~~~~~~~~~~~~~~~~~~

Set :field:`SENSOR.TEMP` to start the temperature sensor, as :lx:`yt921x_chip_setup` does,
and read :reg:`TEMP`. No function of the :ref:`Linux driver <sources-list>` reads
:reg:`TEMP`. The :ref:`vendor SDK <sources-list>` function
`fal_tiger_sensor_temp_value_get() <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_sensor.c#L44>`__
reads the register and uses bits 15 to 0 as the value *v*. With bit 15 clear it returns
*v* × 100 ÷ 128 as hundredths of a degree Celsius, so that one step of *v* is 1/128 °C. With
bit 15 set it returns the temperature as negative, with the size 51200 − *v* × 100 ÷ 128 in the
same unit. The unit is that of the
`comment on yt_sensor_temp_value_get() <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/yt/yt_sensor.c#L66>`__
in the :ref:`vendor SDK <sources-list>`, "centigrade*100". The conversion is not tested on a
chip.

.. _bringup-mac:

Switch MAC address
~~~~~~~~~~~~~~~~~~

:reg:`MAC_ADDR_HI2` and :reg:`MAC_ADDR_LO4` hold a MAC address of the switch itself. It is
:ev:`inferred` from the register names that the switch uses it as the source address of
frames it generates, such as pause frames. No function of the :ref:`Linux driver <sources-list>`
writes the two
registers.

The sources disagree on the byte order. The names in :lx:`chip.h` read as the first two bytes
of the address in :reg:`MAC_ADDR_HI2` and the last four in :reg:`MAC_ADDR_LO4`, which is
:ev:`inferred`. The :ref:`vendor SDK <sources-list>` names the two bytes of
:reg:`MAC_ADDR_HI2` `MAC_ADDR_BYTE4 <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_struct.c#L72>`__ and
`MAC_ADDR_BYTE5 <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_struct.c#L73>`__
and the four bytes of :reg:`MAC_ADDR_LO4`
`MAC_ADDR_BYTE0 <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_struct.c#L77>`__ to
`MAC_ADDR_BYTE3 <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_struct.c#L80>`__,
and its function
`fal_tiger_sys_mac_get() <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_sys.c#L17>`__
returns them in that order as bytes 0 to 5 of the address. It is :ev:`not known` which is
right.

.. _bringup-next:

After bring-up
--------------

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - Next task
     - Page
   * - Set up the CPU port
     - :doc:`cpu-tag`
   * - Enable the ports
     - :doc:`ports`
   * - Reach the PHYs
     - :doc:`phy`
   * - Group ports
     - :doc:`forwarding`
