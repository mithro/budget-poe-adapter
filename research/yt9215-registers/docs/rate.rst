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

SLOT is :field:`METER_SLOT.SLOT` for all meters and :field:`PORT_SHAPE_SLOT.SLOT` for all
port shapers. The smallest SLOT is 80 (:const:`METER_SLOT_MIN`,
:const:`PORT_SHAPE_SLOT_MIN`). On a YT9215 with its 8 ns period that gives 5.12 µs.

**Rate and burst.** For a meter the rate goes into :field:`METER_CTRL.CIR`, the burst size
into :field:`METER_CTRL.CBS` and the scale into :field:`METER_CTRL.UNIT`; for a shaper they
go into :field:`PORT_SHAPE_CTRL.CIR`, :field:`PORT_SHAPE_CTRL.CBS` and
:field:`PORT_SHAPE_CTRL.UNIT`. The formulas call these fields CIR, CBS and UNIT. UNIT scales
the token size by powers of four so that large rates fit the fields.

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

A meter has two token buckets, committed and excess, colours frames green, yellow or red and
drops the colours selected in :field:`METER_CTRL.DROP`. A frame within the committed rate
(:field:`METER_CTRL.CIR`, burst :field:`METER_CTRL.CBS`) is green, one within the excess rate
(:field:`METER_CTRL.EIR`, burst :field:`METER_CTRL.EBS`) yellow, and the rest red.
:field:`METER_CTRL.RFC2698` chooses between the two-rate algorithm of RFC 2698 and that of
RFC 4115, and :field:`METER_CTRL.COLOR_BLIND` makes the meter ignore a colour the frame
already has. The :ref:`Linux driver <sources-list>` confirms the committed bucket, the
excess burst with an excess rate of 0 and the dropping of red frames; a non-zero excess rate
and the algorithm choice are inferred from the field names. Meters work only while
:field:`FUNC.METER` is set; see :ref:`bringup-features`.

.. yt-bitfield:: METER_CTRL

.. list-table::
   :header-rows: 1
   :widths: 24 30 46

   * - Entry of :reg:`METER_CTRL`
     - Kind
     - Attached by
   * - 0 to 63
     - General
     - :field:`ACL_ACT.METER_ID`
   * - 0 to 63
     - General
     - :field:`VLAN_CTRL.METER_ID`
   * - 64 + port
     - Per-port
     - :reg:`PORT_METER` of the port

There are :const:`METER_NUM` general meters. To limit what a port may receive (the sequence
is confirmed by the :ref:`Linux driver <sources-list>`):

1. Once at start-up, write the slot length to :field:`METER_SLOT.SLOT`; its reset value is
   not known.
2. Write the three words of entry 64 + port of :reg:`METER_CTRL` with the fields of the
   table that follows.
3. Write :reg:`PORT_METER` of the port with the port number in :field:`PORT_METER.ID` and
   :field:`PORT_METER.EN`.

.. list-table::
   :header-rows: 1
   :widths: 44 56

   * - Field
     - Value
   * - :field:`METER_CTRL.CIR`
     - Rate, from :ref:`rate-tokens`
   * - :field:`METER_CTRL.CBS`
     - Burst, from :ref:`rate-tokens`
   * - :field:`METER_CTRL.EBS`
     - Excess burst, computed like the burst
   * - :field:`METER_CTRL.EIR`
     - 0
   * - :field:`METER_CTRL.UNIT`
     - Scale, from :ref:`rate-tokens`
   * - :field:`METER_CTRL.DROP`
     - :val:`METER_CTRL.DROP.R`
   * - :field:`METER_CTRL.TOKEN_OVERFLOW_EN`
     - 1
   * - :field:`METER_CTRL.METER_EN`
     - 1
   * - :field:`METER_CTRL.PKT_MODE`
     - 1 to count packets, 0 to count bytes

With :field:`METER_CTRL.TOKEN_OVERFLOW_EN` set, tokens that no longer fit the committed
bucket fill the excess bucket, so with an excess rate of 0 the excess burst acts as a second
burst allowance, and only red frames are dropped.

In byte mode a meter counts the frame bytes only, unless
:field:`METER_CTRL.BYTE_MODE_INCLUDE_GAP` adds the per-frame overhead in
:field:`PORT_RATE.GAP_VALUE`.

.. _rate-shaper:

Port shapers
------------

A shaper is a single token bucket on the transmit side of a port.

.. yt-bitfield:: PORT_SHAPE_CTRL

Once at start-up, write the slot length to :field:`PORT_SHAPE_SLOT.SLOT`; its reset value is
not known. Then write the two words of :reg:`PORT_SHAPE_CTRL` with :field:`PORT_SHAPE_CTRL.CIR`,
:field:`PORT_SHAPE_CTRL.CBS` and :field:`PORT_SHAPE_CTRL.UNIT` from :ref:`rate-tokens` and
:field:`PORT_SHAPE_CTRL.EN`. Writing zeros turns the shaper off.

:reg:`METER_STAT` and :reg:`PORT_SHAPE_STAT` show the token counts of a meter or shaper; their
layout is not known.
