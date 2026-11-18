.. _bringup:

Reset and bring-up
==================

This page takes the switch from power-on to a known state. The registers are in the
:blk:`system` block.

.. _bringup-probe:

Find the switch
---------------

Read :reg:`CHIP_ID` at PHY address ``0x1d`` and, if the family code is not one of the two
known values, at ``0x00``. The read changes nothing in the switch. On a board that straps a
switch ID other than 0, use that ID in every access; :ref:`access-straps` lists the pins.

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - :field:`CHIP_ID.MAJOR`
     - Constant
     - Family
   * - ``0x9002``
     - :const:`MAJOR_YT9215`
     - YT9215 family
   * - ``0x9001``
     - :const:`MAJOR_YT9218`
     - YT9218 family

The YT9215 family is the YT9215, YT9214 and YT9213 parts; :ref:`reference-parts` lists every
part.

.. _bringup-reset:

Reset
-----

.. yt-diagram:: reset-sequence
   :caption: Reset followed by identification.

1. Write :reg:`RST` with only :field:`RST.HW` set. The :ref:`Linux driver <sources-list>` describes this as almost the
   same as a reset through the reset pin. That every register returns to its default is
   inferred from that description.
2. Wait 10 ms (:const:`RST_DELAY_US`), as the :ref:`Linux driver <sources-list>` does before it touches the switch
   again.
3. Read :reg:`RST` until the whole register is 0, as described in :ref:`access-wait`.
4. Read :reg:`CPU_TAG_TPID` and check for ``0x9988``, as described in :ref:`access-check`.

A board can wire a GPIO to the reset pin as well; the register reset makes that optional.
:field:`RST.SW` is a second reset bit that no public driver uses.

.. _bringup-identify:

Identify the part
-----------------

Three values together name the part: the family code :field:`CHIP_ID.MAJOR`, the mode
:field:`CHIP_MODE.MODE`, and one byte of the configuration byte store, called the extended
mode. :ref:`reference-parts` has the value of each for every part and
:ref:`reference-parts-ports` the ports each part has. A driver needs the part to know which
of ports 8 and 9 exist and whether they have a SerDes or xMII pins.

The configuration byte store (this manual's name for what the :ref:`Linux driver <sources-list>` calls EDATA) is a
256-byte (:const:`EDATA_LEN`) memory inside the chip. Only reading it is known. The extended
mode is the byte at address ``0xfb`` (:const:`EDATA_EXTMODE`).

.. yt-diagram:: edata-sequence
   :caption: Reading one byte of the configuration byte store.

1. Read :reg:`EDATA_DATA` until :field:`EDATA_DATA.STATUS` is :val:`EDATA_DATA.STATUS.IDLE`
   (3).
2. Write :reg:`EDATA_CTRL` with the byte address in :field:`EDATA_CTRL.ADDR` and
   :val:`EDATA_CTRL.OP.READ` (5) in :field:`EDATA_CTRL.OP`.
3. Read :reg:`EDATA_DATA` until :field:`EDATA_DATA.STATUS` is IDLE again;
   :field:`EDATA_DATA.DATA` then holds the
   byte.

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

``yt921x_reset()`` and ``yt921x_identify()`` are in
:download:`yt921x.c <../bindings/c/yt921x.c>`.

The YT9215SCH is not in the part table of the :ref:`Linux driver <sources-list>`. It is expected to report the
values of the :chip:`YT9215SC`; this has not been checked on hardware.

.. _bringup-clock:

Core clock
----------

:field:`SYS_CLK.SEL` shows which core clock the part runs from. Only the meters and shapers
need it, because their time slots count core clock periods; :ref:`rate-tokens` uses the
period from this table.

.. list-table::
   :header-rows: 1
   :widths: 25 25 25 25

   * - Family
     - :field:`SYS_CLK.SEL`
     - Core clock
     - Period
   * - YT9215
     - 0
     - 125 MHz
     - 8 ns
   * - YT9218
     - 0
     - 167 MHz
     - 6 ns
   * - YT9215
     - 1
     - 143 MHz
     - 7 ns
   * - YT9218
     - 1
     - 143 MHz
     - 7 ns

.. _bringup-features:

Turn on function blocks
-----------------------

Three function blocks work only while their bit in :reg:`FUNC` is set. The :ref:`Linux driver <sources-list>` sets
each bit before it uses the block; that the bits are clear after reset is inferred from
that.

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

Strap overrides, I/O voltage and temperature
--------------------------------------------

Some settings are sampled from strap pins at power-on. :reg:`PON_STRAP_CAP` shows what was
sampled. To override a strap, write the wanted value to :reg:`PON_STRAP_VAL` and set the same
bit in :reg:`PON_STRAP_FUNC`; :ref:`ports-eee` uses this for Energy Efficient Ethernet, which is the one override the
:ref:`Linux driver <sources-list>` confirms. :reg:`PON_STRAP_CAP` is inferred from its name.

:reg:`IO_LEVEL` sets the signalling voltage of the digital pins and of each xMII interface.
Its field positions differ between the two families, so a driver has to identify the part
first. The fields come from the header of the :ref:`Linux driver <sources-list>`, which does
not write them; :ref:`ports-xmii` shows the one known use.

Set :field:`SENSOR.TEMP` to start the temperature sensor and read :reg:`TEMP` for a raw value.
The conversion to degrees is not known.

:reg:`MAC_ADDR_HI2` and :reg:`MAC_ADDR_LO4` hold the MAC address the switch uses as the source
of frames it generates itself, such as pause frames. This use is inferred from the register
names; no public code writes them.

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
