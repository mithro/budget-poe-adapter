.. _leds:

LEDs
====

Each port has up to :const:`LED_GROUP_NUM` (3) LEDs, numbered 0 to 2. The registers call the
number of an LED its group, and the index ``grp`` of an array field is that number. For every
LED the driver picks the conditions that light or blink it, or forces it on or off. The
registers are in the :blk:`led` block.

.. _leds-behaviour:

Behaviour
---------

:reg:`LED0_PORT`, :reg:`LED1_PORT` and :reg:`LED2_PORT` each hold, per port, one bit for every
condition of the matching LED. An LED shows the combination of the conditions whose bits are
set.

.. yt-bitfield:: LED0_PORT

The :ref:`link and activity table <leds-link-table>` gives the bits for an LED that shows link
and activity. Write all five bits in one write to :reg:`LED0_PORT` of the port. The five bits are
:ev:`confirmed` by :lx:`yt921x_led_trigger_set` of the :ref:`Linux driver <sources-list>`.

.. _leds-link-table:

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - Wanted behaviour
     - Field to set
   * - On while the link is up at 1000 Mbit/s
     - :field:`LED0_PORT.ACT_1000M`
   * - On while the link is up at 100 Mbit/s
     - :field:`LED0_PORT.ACT_100M`
   * - On while the link is up at 10 Mbit/s
     - :field:`LED0_PORT.ACT_10M`
   * - Blink on sent frames
     - :field:`LED0_PORT.ACT_TX_BLINK`
   * - Blink on received frames
     - :field:`LED0_PORT.ACT_RX_BLINK`

.. _leds-force:

Forcing an LED
--------------

The forced state of all three LEDs of a port is in :reg:`LED2_PORT`.
:lx:`yt921x_led_force_set` writes the values :val:`LED2_PORT.FORCE.ON` and
:val:`LED2_PORT.FORCE.OFF`.

.. yt-bitfield:: LED2_PORT

.. list-table::
   :header-rows: 1
   :widths: 14 22 64

   * - Value
     - Element *n* of :field:`LED2_PORT.FORCE`
     - State of LED *n* of the port
   * - 0
     - :val:`LED2_PORT.FORCE.DONTCARE`
     - :ref:`behaviour bits <leds-behaviour>`
   * - 1
     - :val:`LED2_PORT.FORCE.BLINK`
     - :ref:`blinking <leds-blink>`
   * - 2
     - :val:`LED2_PORT.FORCE.ON`
     - on
   * - 3
     - :val:`LED2_PORT.FORCE.OFF`
     - off

.. _leds-blink:

Blink timing
------------

The blink cycle of a forced LED depends on its element of :field:`LED2_PORT.FORCE_BLINK`.

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - :field:`LED2_PORT.FORCE_BLINK`
     - Cycle
     - Constant
   * - 0
     - 512 ms
     - :const:`LED_BLINK_DEF`
   * - 1
     - 1024 ms
     - none
   * - 2
     - 2048 ms
     - :const:`LED_BLINK_MAX`
   * - 3
     - cycle of :field:`LED1_PORT.OTHER_BLINK`
     - none

The cycle of :field:`LED1_PORT.OTHER_BLINK` is 512 ms shifted right by the field value, so its
shortest cycle is 64 ms (:const:`LED_BLINK_MIN`). :field:`LED1_PORT.BLINK_DUTY` sets the on
fraction for all LEDs of the port, which is :ev:`confirmed` by :lx:`yt921x_led_blink_set`. The shift rule of :field:`LED1_PORT.OTHER_BLINK` is the comment
on the field in :lx:`leds.h:29`, and the shift rule of :field:`LED2_PORT.FORCE_BLINK` is the
comment in :lx:`leds.h:47`. :lx:`yt921x_led_blink_set` writes the three fields.

.. _leds-output:

Output pins
-----------

:field:`LED_CTRL.MODE` selects how the LED states leave the chip: on parallel pins, one per
LED, or as a serial stream for an external shift register. :reg:`LED_PAR_INV` sets the
polarity of single parallel outputs. :reg:`LED_PAR_MAP` and :reg:`LED_SER_MAP` choose which
LED appears at which pin or stream position.

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Bit of the LED in :reg:`LED_PAR_INV`
     - Pin while the LED is on
     - LED wiring it suits
   * - 0
     - low
     - active low
   * - 1
     - high
     - active high

:lx:`yt921x_led_setup` writes :reg:`LED_PAR_INV`. The registers :reg:`LED_CTRL`,
:reg:`LED_PAR_MAP`, :reg:`LED_SER_CTRL` and :reg:`LED_SER_MAP` have the level :ev:`header`:
:lx:`leds.h` defines them and no function of the :ref:`Linux driver <sources-list>` uses them.
