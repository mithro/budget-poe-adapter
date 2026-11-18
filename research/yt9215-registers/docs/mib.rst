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
the low word is at the offset and the high word at the offset plus 4. The two words are separate
register reads, low word first, so a carry between the two reads can make one sample wrong
by 2\ :sup:`32`. The bindings read each word once, as the :ref:`Linux driver <sources-list>` does; a driver that
cannot accept that reads the low word again and repeats if it is smaller than before.

.. tab-set::

   .. tab-item:: C
      :sync: c

      From :download:`guide.c <../bindings/c/examples/guide.c>`.

      .. literalinclude:: ../bindings/c/examples/guide.c
           :language: c
           :start-after: /* [mib] */
           :end-before: /* [mib end] */

   .. tab-item:: MicroPython
      :sync: micropython

      From :download:`guide.py <../bindings/micropython/examples/guide.py>`.

      .. literalinclude:: ../bindings/micropython/examples/guide.py
           :language: python
           :start-after: # [mib]
           :end-before: # [mib end]

Reading all 39 counters of one port takes 42 register reads, about 11 ms at an MDC clock of
1 MHz.

The counter names follow the :ref:`Linux driver <sources-list>`. The
`vendor driver <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/yt9215rb_mdio_driver/yt9215rb.c#L171>`__ names three offsets differently,
so treat the meaning of these three as uncertain.

.. list-table::
   :header-rows: 1
   :widths: 16 42 42

   * - Offset
     - Name here
     - :ref:`Vendor driver <sources-list>` name
   * - ``0x4c``
     - :counter:`RX_OVERSIZE_ERR`
     - ``RxOverFlow``
   * - ``0x60``
     - :counter:`TX_UNDERSIZE_ERR`
     - ``TxUnderRun``
   * - ``0x9c``
     - :counter:`TX_PKT`
     - ``TxExcDefer``

.. _mib-clear:

Clearing
--------

.. yt-bitfield:: MIB_CTRL

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Goal
     - First write to :reg:`MIB_CTRL`
     - Second write to :reg:`MIB_CTRL`
   * - Clear the counters of every port
     - ``0``
     - ``0x40000000`` (:field:`MIB_CTRL.CLEAN`)
   * - Clear the counters of one port
     - :field:`MIB_CTRL.ONE_PORT` with the port number in :field:`MIB_CTRL.PORT`
     - The same value with :field:`MIB_CTRL.CLEAN` added

A clear takes two writes: the first selects the ports with :field:`MIB_CTRL.CLEAN` at 0, the
second sets CLEAN. This is the sequence of the
`vendor SDK <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_stat.c#L52>`__; the :ref:`Linux driver <sources-list>` defines
the bits but does not use them. Whether CLEAN clears itself is not known, which is why the
first write puts it back to 0.
