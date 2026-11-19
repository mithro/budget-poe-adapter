.. _access:

Register access
===============

Every register has a 32-bit address and holds 32 bits. The host reaches the registers through the
MDIO management pins of the switch (MDC and MDIO), using ordinary
`IEEE 802.3 clause 22 <https://en.wikipedia.org/wiki/Management_Data_Input/Output>`__ frames in an
unusual way: one register access takes four MDIO frames.

.. _access-mdio:

The MDIO bus
------------

MDC is a clock driven by the host. MDIO is a data line driven by either side. Table 18, "Management Interface Pins", of the
|ds| gives the MDIO pin of the switch the type open drain, and the note under table 38 gives the
timing with a pull-up resistor of 1 kΩ. Table 18 also gives the pin an internal pull-up
resistor. A board that wants the timing of table 38 adds an external one on MDIO. A
frame is 64 clock cycles: a preamble of 32 ones, then 32 bits that carry a 5-bit PHY address, a
5-bit register number and 16 bits of data.

.. wavedrom::
   :caption: MDIO frames. Bits are sent from left to right; the switch drives the green parts
             and the host drives the others.

   {"signal": [
     {"name": "Field", "period": 0.5, "wave": "=....=.=.=...=...=.=......",
      "data": ["PRE", "ST", "OP", "PHYAD", "REGAD", "TA", "DATA"]},
     {"name": "Bits", "period": 0.5, "wave": "=....=.=.=...=...=.=......",
      "data": ["32", "2", "2", "5", "5", "2", "16"]},
     {},
     {"name": "Write", "period": 0.5, "wave": "=....=.=.=...=...=.=......",
      "data": ["all 1", "01", "01", "address", "number", "10", "highest first"]},
     {"name": "Read", "period": 0.5, "wave": "=....=.=.=...=...z07......",
      "data": ["all 1", "01", "10", "address", "number", "highest first"]}
   ]}

The switch answers on one PHY address, ``0x1d`` or ``0x00``, selected by a
:ref:`strap pin <access-straps>` at power-on. Any MDIO master will do: a hardware MDIO controller,
or two GPIO pins as in the class
:download:`BitBangMDIO <../bindings/micropython/yt921x.py>`.

.. _access-timing:

Timing
~~~~~~

.. wavedrom::
   :caption: MDC and MDIO timing. The switch samples MDIO on the rising edge of MDC and
             changes it after a rising edge.

   {"signal": [
     {"node": "...A.....B"},
     {"node": "......C..D..E"},
     {"name": "MDC", "wave": "0..1..0..1..0.", "node": "...J.....K"},
     {"name": "MDIO, host drives", "wave": "x=...x........", "data": ["valid"]},
     {"node": ".F.G.H"},
     {"name": "MDIO, switch drives", "wave": "7..........7..", "data": ["bit n", "bit n − 1"]},
     {"node": ".........L.M"}
   ],
   "edge": ["A<->B t1", "C<->D t3", "D<->E t2", "F<->G t4", "G<->H t5", "L<->M t6",
            "J-G", "K-L"]}

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
     - none
     - ns
   * - t2
     - MDC high time
     - 80
     - none
     - ns
   * - t3
     - MDC low time
     - 80
     - none
     - ns
   * - t4
     - MDIO setup time before the rising edge of MDC
     - 10
     - none
     - ns
   * - t5
     - MDIO hold time after the rising edge of MDC
     - 10
     - none
     - ns
   * - t6
     - MDIO valid after the rising edge of MDC
     - 5
     - 125
     - ns

The values are those of table 38 of the |ds|, "Slave SMI Timing Parameter". The host drives
MDIO for t4 and t5 and the switch drives it for t6. The note under table 38 states that the
values hold with a 1 kΩ pull-up resistor on MDIO, and that the minimum of t1 and the maximum
of t6 depend on that resistor. The smallest period of 250 ns is a clock of 4 MHz. The
:ref:`bindings <bindings>` have not been run at any clock rate on a YT921x.

.. _access-straps:

Strap pins
----------

Five strap pins, read at power-on or reset, decide how a host reaches the switch. The pin
names, the levels and the internal resistors are those of table 20 of the |ds|,
"Configuration Pins". Table 20 does not give the level of a switch ID pin that stands for 1; it
is :ev:`inferred` that a high pin is a 1 bit.

.. list-table::
   :header-rows: 1
   :widths: 20 16 32 32

   * - Strap pin
     - Internal resistor
     - Pulled up
     - Pulled down
   * - .. _strap-mid29:

       ``MID29``
     - pull-up
     - PHY address ``0x1d``
     - PHY address ``0x00``
   * - .. _strap-switch-id-1:

       ``SWITCH_ID_1``
     - pull-down
     - Bit 1 of the switch ID is 1
     - Bit 1 of the switch ID is 0
   * - .. _strap-switch-id-0:

       ``SWITCH_ID_0``
     - pull-down
     - Bit 0 of the switch ID is 1
     - Bit 0 of the switch ID is 0
   * - .. _strap-dis-spis:

       ``DIS_SPIS``
     - pull-up
     - SPI host interface off
     - SPI host interface on
   * - .. _strap-smi-sel:

       ``SMI_SEL``
     - pull-up
     - I2C host interface
     - MDIO host interface

:ref:`SMI_SEL <strap-smi-sel>` applies only while :ref:`DIS_SPIS <strap-dis-spis>` is high.
For MDIO, leave :ref:`DIS_SPIS <strap-dis-spis>` high and pull
:ref:`SMI_SEL <strap-smi-sel>` low. A chip with neither pin strapped selects the I2C host
interface.

The levels of :ref:`SMI_SEL <strap-smi-sel>` are those of section 5.5.1 of the |ds|, "Slave
I2C Interface for External CPU". Table 20 of the |ds| gives the pull-up as "EEPROM SMI
interface" and the pull-down as "MII Management interface" and does not name I2C. Section
5.5.2, "Slave SMI Interface for External CPU", says that the pin may be "low or high" for
MDIO, which contradicts both.
The SPI and I2C host interfaces reach the same registers. This manual does not cover them.

.. _access-smi:

Reading and writing a register
------------------------------

The 5-bit register number of each MDIO frame does not name a register. It tells the switch
what the 16 data bits of the frame are:

.. wavedrom::
   :caption: The register number (REGAD) of an MDIO frame to the switch.

   {"reg": [
     {"name": "READ", "bits": 1},
     {"name": "DATA", "bits": 1},
     {"name": "switch ID", "bits": 2},
     {"name": "0", "bits": 1}
   ], "config": {"bits": 5}}

.. list-table::
   :header-rows: 1
   :widths: 10 22 34 34

   * - Bit
     - Name
     - Value 1
     - Value 0
   * - 4
     - none
     - :ev:`not known`
     - always sent
   * - 3
     - Switch ID bit 1
     - :ref:`SWITCH_ID_1 <strap-switch-id-1>` is high
     - :ref:`SWITCH_ID_1 <strap-switch-id-1>` is low
   * - 2
     - Switch ID bit 0
     - :ref:`SWITCH_ID_0 <strap-switch-id-0>` is high
     - :ref:`SWITCH_ID_0 <strap-switch-id-0>` is low
   * - 1
     - DATA
     - half of a register value
     - half of a register address
   * - 0
     - READ
     - register read
     - register write

The switch ID lets up to :const:`SWITCHID_NUM` switches share one PHY address. Table 20
of the |ds| describes the two :ref:`strap pins <access-straps>` as "Switch_ID [1:0] for slave SMI
and slave I2C format". It is :ev:`inferred` that a switch answers only the frames whose switch ID
bits match its strap pins. No source names bit 4, and the
:ref:`Linux driver <sources-list>` always sends it as 0.

An access is two frames that set the address, high half first, and two frames that move the
value, high half first. The READ bit has the same value in all four frames.

.. wavedrom::
   :caption: Register read. The address frames are MDIO writes and the value frames are MDIO
             reads; the switch drives the green parts.

   {"signal": [
     {"name": "MDIO frame", "wave": "=..=..=..=..", "data": ["write", "write", "read", "read"]},
     {"name": "REGAD bit DATA", "wave": "=..=..=..=..", "data": ["0", "0", "1", "1"]},
     {"name": "REGAD bit READ", "wave": "=..=..=..=..", "data": ["1", "1", "1", "1"]},
     {"name": "Frame data", "wave": "=..=..7..7..",
      "data": ["address[31:16]", "address[15:0]", "value[31:16]", "value[15:0]"]}
   ]}

.. wavedrom::
   :caption: Register write. All four frames are MDIO writes.

   {"signal": [
     {"name": "MDIO frame", "wave": "=..=..=..=..", "data": ["write", "write", "write", "write"]},
     {"name": "REGAD bit DATA", "wave": "=..=..=..=..", "data": ["0", "0", "1", "1"]},
     {"name": "REGAD bit READ", "wave": "=..=..=..=..", "data": ["0", "0", "0", "0"]},
     {"name": "Frame data", "wave": "=..=..=..=..",
      "data": ["address[31:16]", "address[15:0]", "value[31:16]", "value[15:0]"]}
   ]}

With switch ID 0 the four register numbers are 1, 1, 3, 3 for a read and 0, 0, 2, 2 for a
write. The bits of the register number are defined in :lx:`chip.h:11`, and their use in the
two sequences is :ev:`confirmed` by :lx:`yt921x_reg_mdio_read` and
:lx:`yt921x_reg_mdio_write`.

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

The complete functions are :ref:`yt921x_reg_read() <bindings-api>` and
:ref:`yt921x_reg_write() <bindings-api>` in :download:`yt921x.c <../bindings/c/yt921x.c>`
and :ref:`YT921x.reg_read() <bindings-api>` and
:ref:`YT921x.reg_write() <bindings-api>` in
:download:`yt921x.py <../bindings/micropython/yt921x.py>`.

It is :ev:`inferred` from the frame sequence that the switch keeps the address between
frames, so the four frames of one access must not be mixed with those of another.
:lx:`yt921x_reg_mdio_read` holds the lock of the MDIO bus over all four frames. A driver that can be called from several threads takes one lock
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

Write the words in rising address order, as :lx:`yt921x_regs_write` of the
:ref:`Linux driver <sources-list>` does. It is :ev:`not known` when the switch starts to use
an entry of which only some words are written. To change one field, read all words, change
the field and write all words back.

The :ref:`bindings <bindings-naming>` carry helpers for fields that cross a word boundary.

.. list-table::
   :header-rows: 1
   :widths: 25 25 25 25

   * - Environment
     - Read a field
     - Write a field
     - File
   * - C
     - :download:`yt921x_bits_get() <../bindings/c/yt921x_regs.h>`
     - :download:`yt921x_bits_set() <../bindings/c/yt921x_regs.h>`
     - :download:`yt921x_regs.h <../bindings/c/yt921x_regs.h>`
   * - Rust
     - :download:`Field::get_words() <../bindings/rust/src/regs.rs>`
     - :download:`Field::set_words() <../bindings/rust/src/regs.rs>`
     - :download:`regs.rs <../bindings/rust/src/regs.rs>`
   * - MicroPython
     - :download:`bits_get() <../bindings/micropython/yt921x_regs.py>`
     - :download:`bits_set() <../bindings/micropython/yt921x_regs.py>`
     - :download:`yt921x_regs.py <../bindings/micropython/yt921x_regs.py>`

.. _access-wait:

Waiting for the switch
----------------------

Several functions are commands: the driver writes a start bit and the switch clears it, or
sets a done bit, when it has finished.

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Command
     - Bit to poll
     - Described in
   * - Reset
     - :field:`RST.HW`
     - :ref:`bringup-reset`
   * - Transfer on the internal MDIO master
     - :field:`INT_MBUS_OP.START`
     - :ref:`phy-mbus`
   * - Transfer on the external MDIO master
     - :field:`EXT_MBUS_OP.START`
     - :ref:`phy-mbus`
   * - Forwarding database command
     - :field:`FDB_RESULT.DONE`
     - :ref:`fdb-command`
   * - Read of a configuration byte
     - :field:`EDATA_DATA.STATUS`
     - :ref:`bringup-identify`

:lx:`yt921x_reg_wait` of the :ref:`Linux driver <sources-list>` polls such a bit every 10 ms
and gives up after 100 ms; :lx:`smi.c:11` and :lx:`smi.c:12` define the two times. It is
:ev:`not known` how long a command takes. The function
:ref:`yt921x_reg_wait() <bindings-api>` of :download:`yt921x.c <../bindings/c/yt921x.c>` implements the same
loop.

.. _access-check:

Checking that access works
--------------------------

:reg:`CPU_TAG_TPID` reads ``0x9988`` after reset, which is one of the
:ref:`reset values <sources-reset>` that the :ref:`Linux driver <sources-list>` states. A driver
that reads anything
else is not talking to a YT921x, has the wrong PHY address, or has a wiring fault. A read from
an address nobody answers returns ``0xffff`` in each half, because the pull-up keeps the line
high.
