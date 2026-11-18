.. _leds:

LEDs
====

Each port has up to three LEDs (:const:`LED_GROUP_NUM`), called LED 0, 1 and 2. For every LED
the driver picks the conditions that light or blink it, or forces it on or off. The registers
are in the :blk:`led` block.

.. _leds-behaviour:

Behaviour
---------

:reg:`LED0_PORT`, :reg:`LED1_PORT` and :reg:`LED2_PORT` each hold, per port, one bit for every
condition of the matching LED. A LED shows the combination of the conditions whose bits are
set.

.. yt-bitfield:: LED0_PORT

A common choice is link plus activity. To light the LED while the link is up at any speed,
set :field:`LED0_PORT.ACT_1000M`, :field:`LED0_PORT.ACT_100M` and :field:`LED0_PORT.ACT_10M`.
To blink it on traffic, set :field:`LED0_PORT.ACT_TX_BLINK` and
:field:`LED0_PORT.ACT_RX_BLINK`; this pair is confirmed by the :ref:`Linux driver <sources-list>`. For LED 0 of
port 3 that is one write:

.. code-block:: c

   yt921x_reg_write(dev, YT921X_LED0_PORT(3),
                    YT921X_LED0_PORT_ACT_1000M_M | YT921X_LED0_PORT_ACT_100M_M |
                    YT921X_LED0_PORT_ACT_10M_M | YT921X_LED0_PORT_ACT_TX_BLINK_M |
                    YT921X_LED0_PORT_ACT_RX_BLINK_M);

.. _leds-force:

Forcing a LED
-------------

The forced state of all three LEDs of a port is in :reg:`LED2_PORT`.

.. yt-bitfield:: LED2_PORT

.. list-table::
   :header-rows: 1
   :widths: 14 22 64

   * - Value
     - Element *n* of :field:`LED2_PORT.FORCE`
     - LED *n* of the port
   * - 0
     - :val:`LED2_PORT.FORCE.DONTCARE`
     - Follows its behaviour bits
   * - 1
     - :val:`LED2_PORT.FORCE.BLINK`
     - Blinks with the cycle in :ref:`leds-blink`
   * - 2
     - :val:`LED2_PORT.FORCE.ON`
     - On
   * - 3
     - :val:`LED2_PORT.FORCE.OFF`
     - Off

.. _leds-blink:

Blink timing
------------

The blink cycle of a forced LED is 512 ms shifted left by its element of
:field:`LED2_PORT.FORCE_BLINK`: 512 ms, 1024 ms
or 2048 ms for the values 0 to 2. The value 3 selects the alternative cycle of
:field:`LED1_PORT.OTHER_BLINK`, which is 512 ms shifted right and reaches down to 64 ms
(:const:`LED_BLINK_MIN`, :const:`LED_BLINK_DEF`, :const:`LED_BLINK_MAX`).
:field:`LED1_PORT.BLINK_DUTY` sets the on fraction for all LEDs of the port.

.. _leds-output:

Output pins
-----------

:field:`LED_CTRL.MODE` selects how the LED states leave the chip: on parallel pins, one per
LED, or as a serial stream for an external shift register. :reg:`LED_PAR_INV` sets the
polarity of single parallel outputs: with its bit clear a pin is low while the LED is on,
which suits a LED wired active low, and with the bit set the pin is high while the LED is on.
:reg:`LED_PAR_MAP` and :reg:`LED_SER_MAP` choose which LED appears at which pin or stream
position. The :ref:`Linux driver <sources-list>` uses the
behaviour, force and inversion registers; the mapping and serial registers are described from
the definitions in its header.
