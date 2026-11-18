.. _rate:

Rate limiting
=============

The switch limits rates in two places: meters police frames on receive, and shapers pace what
a port sends. Both are token buckets and share one arithmetic. The registers are in the
:blk:`meter` and :blk:`shape` blocks.

.. _rate-tokens:

Token arithmetic
----------------

.. yt-diagram:: token-bucket
   :caption: A token bucket. Tokens arrive once per time slot; a frame needs tokens for its
             length.

**Time slot.** Tokens are added once per slot. The slot length is the register value times
eight core clock periods; the period is in :ref:`bringup-clock`.

.. code-block:: text

   slot time = SLOT × 8 × core clock period

The smallest SLOT is 80 (:const:`METER_SLOT_MIN`, :const:`PORT_SHAPE_SLOT_MIN`). On a YT9215
with its 8 ns period that gives 5.12 µs. :reg:`METER_SLOT` sets the slot of all meters and
:reg:`PORT_SHAPE_SLOT` that of all port shapers.

**Rate and burst.** UNIT scales the token size by powers of four so that large rates fit
the fields.

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Mode
     - CIR (rate field)
     - CBS (burst field)
   * - Bytes
     - bytes per second × slot time × 2^14 ÷ 4^UNIT
     - bytes ÷ (2 × 4^UNIT)
   * - Packets
     - packets per second × slot time × 2^21 ÷ 4^UNIT
     - packets × 64 ÷ 4^UNIT

Choose the smallest UNIT for which both values fit their fields; that gives the finest
resolution. The exponents come from the constants :const:`TOKEN_BYTE_C`,
:const:`TOKEN_PKT_C` and :const:`TOKEN_RATE_C`.

**Example.** 100 Mbit/s is 12 500 000 bytes per second, or 64 bytes per 5.12 µs slot. With
UNIT 0 the rate value would be 64 × 16384 = 1 048 576, too large for the 18-bit field, and
with UNIT 1 it is 262 144, one too large. UNIT 2 gives CIR = 65 536. A burst of 65 536 bytes
is then CBS = 65 536 ÷ 32 = 2048.

.. _rate-meter:

Meters
------

A meter is a two-rate token bucket (committed and excess) that colours frames green, yellow or
red and drops the colours selected in :field:`METER_CTRL.DROP`. Meters work only while
:field:`FUNC.METER` is set; see :ref:`bringup-features`.

.. yt-bitfield:: METER_CTRL

.. list-table::
   :header-rows: 1
   :widths: 24 30 46

   * - Entry of :reg:`METER_CTRL`
     - Kind
     - Attached by
   * - 0 to 63
     - General (:const:`METER_NUM`)
     - :field:`ACL_ACT.METER_ID` or :field:`VLAN_CTRL.METER_ID`
   * - 64 + port
     - Per-port
     - :reg:`PORT_METER` of the port

To limit what a port may receive, as the Linux driver does:

1. Write the three words of ``METER_CTRL[64 + port]``: :field:`METER_CTRL.CIR`,
   :field:`METER_CTRL.CBS` and :field:`METER_CTRL.UNIT` from the arithmetic above,
   :field:`METER_CTRL.DROP` = ``R`` (drop red frames), :field:`METER_CTRL.TOKEN_OVERFLOW_EN`
   and :field:`METER_CTRL.METER_EN`. Set :field:`METER_CTRL.PKT_MODE` to count packets.
2. Write :reg:`PORT_METER` of the port with the port number in :field:`PORT_METER.ID` and
   :field:`PORT_METER.EN`.

In byte mode a meter counts the frame bytes only, unless
:field:`METER_CTRL.BYTE_MODE_INCLUDE_GAP` adds the per-frame overhead in
:field:`PORT_RATE.GAP_VALUE`.

.. _rate-shaper:

Port shapers
------------

A shaper is a single token bucket on the transmit side of a port.

.. yt-bitfield:: PORT_SHAPE_CTRL

Write the two words of :reg:`PORT_SHAPE_CTRL` with :field:`PORT_SHAPE_CTRL.CIR`,
:field:`PORT_SHAPE_CTRL.CBS` and :field:`PORT_SHAPE_CTRL.UNIT` from the arithmetic above and
:field:`PORT_SHAPE_CTRL.EN`. Writing zeros turns the shaper off.

:reg:`METER_STAT` and :reg:`PORT_SHAPE_STAT` show the token counts of a meter or shaper; their
layout is not known.
