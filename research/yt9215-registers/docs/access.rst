.. _access:

Register access
===============

Every register has a 32-bit address and holds 32 bits. The host reaches the registers through
the MDIO management pins of the switch (MDC and MDIO), using ordinary IEEE 802.3 clause 22
frames in an unusual way: one register access takes four MDIO frames.

.. _access-mdio:

The MDIO bus
------------

MDC is a clock driven by the host. MDIO is a data line driven by either side; it is open
drain on the switch, so the board needs a pull-up resistor on it. A frame is 64 clock cycles:
a preamble of 32 ones, then 32 bits that carry a 5-bit PHY address, a 5-bit register number
and 16 bits of data.

.. yt-diagram:: mdio-frame
   :caption: Clause 22 MDIO frames. Bits are sent from left to right; green parts are driven
             by the switch.

The switch answers on one PHY address, ``0x1d`` or ``0x00``, selected by a strap pin at
power-on. Any MDIO master will do: a hardware MDIO controller, or two GPIO pins as in
``BitBangMDIO`` of the :ref:`MicroPython binding <bindings-micropython>`.

.. _access-timing:

Timing
~~~~~~

.. yt-diagram:: smi-timing
   :caption: MDC and MDIO timing. The switch samples MDIO on the rising edge of MDC and
             changes it after a rising edge.

.. list-table::
   :header-rows: 1
   :widths: 12 52 12 12 12

   * - Symbol
     - Parameter
     - Minimum
     - Maximum
     - Unit
   * - t1
     - MDC period
     - 250
     -
     - ns
   * - t2
     - MDC high time
     - 80
     -
     - ns
   * - t3
     - MDC low time
     - 80
     -
     - ns
   * - t4
     - MDIO setup time before the rising edge of MDC, host driving
     - 10
     -
     - ns
   * - t5
     - MDIO hold time after the rising edge of MDC, host driving
     - 10
     -
     - ns
   * - t6
     - MDIO valid after the rising edge of MDC, switch driving
     - 5
     - 125
     - ns

The values are those of the slave management interface in table 38 of the
:download:`YT9215SCH datasheet <../../../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf>`.
The datasheet draws MDIO with a 1 kΩ pull-up resistor. The minimum of t1 and the maximum of
t6 depend on that resistor, because the line rises only as fast as the resistor charges it. A clock of 1 MHz or less is a safe choice for a
bit-banged bus.

.. _access-straps:

Strap pins
----------

Five strap pins, read at power-on or reset, decide how a host reaches the switch. The pin
names are those of the :download:`YT9215SCH datasheet <../../../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf>`.

.. list-table::
   :header-rows: 1
   :widths: 24 38 38

   * - Strap pin
     - Pulled up
     - Pulled down
   * - ``MID29``
     - PHY address ``0x1d``
     - PHY address ``0x00``
   * - ``SWITCH_ID_1``
     - Bit 1 of the switch ID is 1
     - Bit 1 of the switch ID is 0
   * - ``SWITCH_ID_0``
     - Bit 0 of the switch ID is 1
     - Bit 0 of the switch ID is 0
   * - ``DIS_SPIS``
     - SPI host interface off; ``SMI_SEL`` applies
     - SPI host interface on
   * - ``SMI_SEL``
     - EEPROM interface
     - MDIO management interface

``MID29``, ``DIS_SPIS`` and ``SMI_SEL`` have internal pull-ups and the switch ID pins internal
pull-downs. The datasheet describes the SPI and I2C host interfaces, which reach the same
registers; this manual does not cover them.

.. _access-smi:

Reading and writing a register
------------------------------

The 5-bit register number of each MDIO frame does not name a register. It tells the switch
what the 16 data bits of the frame are:

.. yt-diagram:: smi-regad
   :caption: The register number (REGAD) of an MDIO frame to the switch.

.. list-table::
   :header-rows: 1
   :widths: 14 20 66

   * - Bits
     - Name
     - Meaning
   * - 4
     - 0
     - Always 0.
   * - 3:2
     - Switch ID
     - Selects one of up to :const:`SWITCHID_NUM` switches that share the PHY address; see
       :ref:`access-straps`.
   * - 1
     - DATA
     - Set when the frame carries half of a register value, clear when it carries half of a
       register address.
   * - 0
     - READ
     - Set for a register read, clear for a register write.

An access is two frames that set the address, high half first, and two frames that move the
value, high half first. The READ bit has the same value in all four frames.

.. yt-diagram:: smi-read
   :caption: Register read. The address frames are MDIO writes; the value frames are MDIO reads.

.. yt-diagram:: smi-write
   :caption: Register write. All four frames are MDIO writes.

With switch ID 0 the four register numbers are 1, 1, 3, 3 for a read and 0, 0, 2, 2 for a
write.

.. tab-set::

   .. tab-item:: C
      :sync: c

      .. code-block:: c

         /* read */
         mdio_write(phy, 1, addr >> 16);
         mdio_write(phy, 1, addr & 0xffff);
         hi = mdio_read(phy, 3);
         lo = mdio_read(phy, 3);
         value = (uint32_t)hi << 16 | lo;

         /* write */
         mdio_write(phy, 0, addr >> 16);
         mdio_write(phy, 0, addr & 0xffff);
         mdio_write(phy, 2, value >> 16);
         mdio_write(phy, 2, value & 0xffff);

   .. tab-item:: MicroPython
      :sync: micropython

      .. code-block:: python

         # read
         mdio.write(phy, 1, addr >> 16)
         mdio.write(phy, 1, addr & 0xFFFF)
         hi = mdio.read(phy, 3)
         lo = mdio.read(phy, 3)
         value = (hi << 16) | lo

         # write
         mdio.write(phy, 0, addr >> 16)
         mdio.write(phy, 0, addr & 0xFFFF)
         mdio.write(phy, 2, value >> 16)
         mdio.write(phy, 2, value & 0xFFFF)

The complete functions are ``yt921x_reg_read()`` and ``yt921x_reg_write()`` in
:download:`yt921x.c <../bindings/c/yt921x.c>` and ``YT921x.reg_read()`` and
``YT921x.reg_write()`` in :download:`yt921x.py <../bindings/micropython/yt921x.py>`.

The switch keeps the address between frames, so the four frames of one access must not be
mixed with those of another. A driver that can be called from several threads takes one lock
around the whole access, and around every command sequence that spans several registers
(:ref:`access-wait`).

One access is 256 MDC cycles. At 1 MHz that is about 0.26 ms, and writing all
4096 entries of the VLAN table takes about two seconds (two accesses per entry).

.. _access-wide:

Registers wider than 32 bits
----------------------------

Some table entries are 64 or 96 bits wide, for example :reg:`VLAN_CTRL` and :reg:`ACL_ACT`.
Such a register occupies two or three consecutive 32-bit words; the word at the register
address holds bits 31 to 0, the next word (address + 4) bits 63 to 32, and so on. The
reference numbers the bits of the whole register, so a field can cross a word boundary, as
:field:`VLAN_CTRL.FID` does.

Write the words in rising address order, as the :ref:`Linux driver <sources-list>` does. That a table entry takes
effect only when its last word is written, so that the switch never uses a half-written
entry, is inferred from that order and is not confirmed. To change one field, read all words,
change the field and write all words back.

The bindings carry helpers for this: ``yt921x_bits_get()`` and ``yt921x_bits_set()`` in C,
``Field::get_words()`` and ``Field::set_words()`` in Rust and ``bits_get()`` and ``bits_set()`` in
MicroPython; :ref:`bindings-naming` lists them.

.. _access-wait:

Waiting for the switch
----------------------

Several functions are commands: the driver writes a start bit and the switch clears it, or
sets a done bit, when it has finished. The reset (:field:`RST.HW`), the MDIO masters
(:field:`INT_MBUS_OP.START`), the forwarding database (:field:`FDB_RESULT.DONE`) and the
configuration byte store (:field:`EDATA_DATA.STATUS`) work this way.

The :ref:`Linux driver <sources-list>` polls such a bit every 10 ms and gives up after 100 ms. Those numbers are a
safe starting point; none of the public sources states how long a command really takes.
``yt921x_reg_wait()`` in the bindings implements the loop.

.. _access-check:

Checking that access works
--------------------------

:reg:`CPU_TAG_TPID` reads ``0x9988`` after reset on every part. A driver that reads anything
else is not talking to a YT921x, has the wrong PHY address, or has a wiring fault. A read from
an address nobody answers returns ``0xffff`` in each half, because the pull-up keeps the line
high.
