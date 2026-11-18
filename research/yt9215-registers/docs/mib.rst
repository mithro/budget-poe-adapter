.. _mib:

Port counters
=============

Every port counts the frames and bytes it receives and sends. The registers are in the
:blk:`mib` block and the counters are listed in :ref:`reference-counters`.

.. _mib-enable:

Enable
------

The counters run only while :field:`FUNC.MIB` is set; see :ref:`bringup-features`.

.. _mib-counters:

Reading a counter
-----------------

The counters of port *p* start at :reg:`MIB_DATA`, ``0xc0100 + 0x100 × p``. Each counter has a
fixed offset from there, for example :counter:`RX_BROADCAST` at offset 0 and
:counter:`TX_GOOD_BYTES` at ``0x84``.

Most counters are 32 bits wide and wrap around. A driver that needs longer counts reads them
often enough to see every wrap and adds the differences up in software. The byte counters
(:counter:`RX_GOOD_BYTES`, :counter:`RX_BAD_BYTES` and :counter:`TX_GOOD_BYTES`) are 64 bits:
the low word is at the offset and the high word 4 above it. The two words are separate
register reads, so read the low word, then the high word, and repeat if a second read of the
low word is smaller than the first.

.. tab-set::

   .. tab-item:: C
      :sync: c

      .. literalinclude:: ../bindings/c/examples/guide.c
           :language: c
           :start-after: /* [mib] */
           :end-before: /* [mib end] */

   .. tab-item:: MicroPython
      :sync: micropython

      .. literalinclude:: ../bindings/micropython/examples/guide.py
           :language: python
           :start-after: # [mib]
           :end-before: # [mib end]

Reading all 39 counters of one port takes 42 register reads, about 11 ms at an MDC clock of
1 MHz.

.. _mib-clear:

Clearing
--------

.. yt-bitfield:: MIB_CTRL

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Goal
     - Write to :reg:`MIB_CTRL`
   * - Clear the counters of every port
     - :field:`MIB_CTRL.CLEAN` and :field:`MIB_CTRL.ALL_PORT`
   * - Clear the counters of one port
     - :field:`MIB_CTRL.CLEAN`, :field:`MIB_CTRL.ONE_PORT` and the port number in
       :field:`MIB_CTRL.PORT`

The Linux driver defines these bits but does not use them, so the exact behaviour, such as
whether CLEAN clears itself, is not confirmed.
