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

.. _rate-slot:

Time slot
~~~~~~~~~

Tokens are added once per slot. The slot length is the register value times eight core clock
periods. :ref:`bringup-clock` gives the period.

.. code-block:: text

   slot time = SLOT × 8 × core clock period

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Buckets
     - SLOT field
     - Smallest value
   * - All meters
     - :field:`METER_SLOT.SLOT`
     - :const:`METER_SLOT_MIN` (80)
   * - All port shapers
     - :field:`PORT_SHAPE_SLOT.SLOT`
     - :const:`PORT_SHAPE_SLOT_MIN` (80)

With the 8 ns period of a :ref:`YT9215 family <reference-parts>` part at
:field:`SYS_CLK.SEL` 0, the smallest slot is 5.12 µs. The slot formula and the two limits are
:ev:`confirmed` by :lx:`yt921x_chip_setup_tc` of the :ref:`Linux driver <sources-list>`.

.. _rate-fields:

Rate and burst
~~~~~~~~~~~~~~

The :ref:`formulas <rate-formulas>` use the names CIR, CBS and UNIT for three fields of a
bucket. UNIT scales the token size by powers of four so that large rates fit the fields.

.. list-table::
   :header-rows: 1
   :widths: 20 20 30 30

   * - Name
     - Content
     - Field of a meter
     - Field of a shaper
   * - CIR
     - rate
     - :field:`METER_CTRL.CIR`
     - :field:`PORT_SHAPE_CTRL.CIR`
   * - CBS
     - burst size
     - :field:`METER_CTRL.CBS`
     - :field:`PORT_SHAPE_CTRL.CBS`
   * - UNIT
     - scale
     - :field:`METER_CTRL.UNIT`
     - :field:`PORT_SHAPE_CTRL.UNIT`

.. _rate-formulas:

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

Choose the smallest UNIT for which both values fit their fields, because that gives the
finest resolution. The formulas are those of the functions :lx:`rate2token` and
:lx:`burst2token`, with the exponents written out.

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Constant
     - Value
     - Exponent of
   * - :const:`TOKEN_BYTE_C`
     - 1
     - token size in byte mode
   * - :const:`TOKEN_PKT_C`
     - −6
     - token size in packet mode
   * - :const:`TOKEN_RATE_C`
     - −15
     - rate field

.. _rate-example:

Example
~~~~~~~

100 Mbit/s is 12 500 000 bytes per second, or 64 bytes per 5.12 µs slot.

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - UNIT
     - CIR for 100 Mbit/s
     - Fits the 18-bit field
   * - 0
     - 1 048 576
     - no
   * - 1
     - 262 144
     - no
   * - 2
     - 65 536
     - yes

With UNIT 2, a burst of 65 536 bytes is CBS = 65 536 ÷ 32 = 2048.

.. _rate-meter:

Meters
------

A meter has two token buckets, committed and excess. It colours frames green, yellow or red
and drops the colours selected in :field:`METER_CTRL.DROP`. Meters work only while
:field:`FUNC.METER` is set, which :ref:`bringup-features` describes.

.. list-table::
   :header-rows: 1
   :widths: 20 20 30 30

   * - Colour
     - Frame is within
     - Rate field
     - Burst field
   * - green
     - committed rate
     - :field:`METER_CTRL.CIR`
     - :field:`METER_CTRL.CBS`
   * - yellow
     - excess rate
     - :field:`METER_CTRL.EIR`
     - :field:`METER_CTRL.EBS`
   * - red
     - neither rate
     - none
     - none

:field:`METER_CTRL.RFC2698` chooses between the two-rate algorithm of
`RFC 2698 <https://www.rfc-editor.org/rfc/rfc2698>`__ and that of
`RFC 4115 <https://www.rfc-editor.org/rfc/rfc4115>`__. :field:`METER_CTRL.COLOR_BLIND` makes
the meter ignore a colour the frame already has. Both meanings are :ev:`inferred` from the names
of the fields.

:lx:`yt921x_meter_config` :ev:`confirms <confirmed>` the committed bucket, the excess burst
with an excess rate of 0 and the dropping of red frames. A non-zero excess rate and the
algorithm choice are :ev:`inferred` from the field names in :lx:`tc.h`.

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

There are :const:`METER_NUM` general meters. Three steps limit what a port may receive.

1. Once at start-up, write the slot length to :field:`METER_SLOT.SLOT`. Its reset value is
   :ev:`not known`.
2. Write the three words of entry 64 + port of :reg:`METER_CTRL` with the fields of the
   :ref:`meter field table <rate-meter-fields>`.
3. Write :reg:`PORT_METER` of the port with the port number in :field:`PORT_METER.ID` and
   :field:`PORT_METER.EN`.

Step 1 is :ev:`confirmed` by :lx:`yt921x_chip_setup_tc`, step 2 by :lx:`yt921x_meter_config`
and step 3 by :lx:`yt921x_dsa_port_policer_add`.

.. _rate-meter-fields:

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Field
     - Value
     - Computed with
   * - :field:`METER_CTRL.CIR`
     - rate
     - :ref:`CIR formula <rate-formulas>`
   * - :field:`METER_CTRL.CBS`
     - burst
     - :ref:`CBS formula <rate-formulas>`
   * - :field:`METER_CTRL.EBS`
     - excess burst
     - :ref:`CBS formula <rate-formulas>`
   * - :field:`METER_CTRL.EIR`
     - 0
     - none
   * - :field:`METER_CTRL.UNIT`
     - scale
     - :ref:`formulas <rate-formulas>`
   * - :field:`METER_CTRL.DROP`
     - :val:`METER_CTRL.DROP.R`
     - none
   * - :field:`METER_CTRL.TOKEN_OVERFLOW_EN`
     - 1
     - none
   * - :field:`METER_CTRL.METER_EN`
     - 1
     - none
   * - :field:`METER_CTRL.PKT_MODE`
     - 1 for packets
     - none
   * - :field:`METER_CTRL.PKT_MODE`
     - 0 for bytes
     - none

The comment on :field:`METER_CTRL.TOKEN_OVERFLOW_EN` in :lx:`tc.h:280` reads "RFC4115: yellow
use unused green bw". With the bit set, tokens that the full committed bucket cannot take
fill the excess bucket. With an excess rate of 0 the excess burst then acts as a second burst
allowance, and only red frames are dropped.

In byte mode a meter counts the frame bytes only, unless
:field:`METER_CTRL.BYTE_MODE_INCLUDE_GAP` adds the per-frame overhead in
:field:`PORT_RATE.GAP_VALUE`. The comment on the bit in :lx:`tc.h:290` reads "+GAP_VALUE bytes
each packet"; the bit is a :ev:`header` definition.

.. _rate-shaper:

Port shapers
------------

A shaper is a single token bucket on the transmit side of a port.

.. yt-bitfield:: PORT_SHAPE_CTRL

1. Once at start-up, write the slot length to :field:`PORT_SHAPE_SLOT.SLOT`. Its reset value
   is :ev:`not known`.
2. Write the two words of :reg:`PORT_SHAPE_CTRL` with :field:`PORT_SHAPE_CTRL.CIR`,
   :field:`PORT_SHAPE_CTRL.CBS` and :field:`PORT_SHAPE_CTRL.UNIT` from the
   :ref:`formulas <rate-formulas>`, and with :field:`PORT_SHAPE_CTRL.EN` set.

Writing zeros to :reg:`PORT_SHAPE_CTRL` turns the shaper off. Step 1 is :ev:`confirmed` by
:lx:`yt921x_chip_setup_tc` and step 2 by :lx:`yt921x_dsa_port_setup_tc_tbf_port`.

.. _rate-stat:

Token counts
------------

It is :ev:`inferred` from the names of :reg:`METER_STAT` and :reg:`PORT_SHAPE_STAT` that the
two registers show the token counts of a meter and of a shaper. Their layout is
:ev:`not known`.
