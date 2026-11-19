.. _mib:

Port counters
=============

Every port counts the frames and bytes it receives and sends. The registers are in the
:blk:`mib` block and the counters are listed in :ref:`reference-counters`.

.. _mib-enable:

Enable
------

The counters run only while :field:`FUNC.MIB` is set, which :ref:`bringup-features`
describes.

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
by 2\ :sup:`32`. The :ref:`bindings <bindings-api>` read each word once, as
:lx:`yt921x_mib_read` of the :ref:`Linux driver <sources-list>` does. A driver that cannot
accept that reads the low word again and repeats if it is smaller than before.

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

The counter names follow :lx:`mib.h` of the :ref:`Linux driver <sources-list>`. The counter table
of the
`YT9215RB vendor driver <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/yt9215rb_mdio_driver/yt9215rb.c#L171>`__
names the offset ``0x4c`` "RxOverFlow", where the Linux name is :counter:`RX_OVERSIZE_ERR`. The
header
`yt_stat.h <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/include/yt_stat.h>`__
of the :ref:`vendor SDK <sources-list>` agrees with the Linux name, so this manual uses the Linux
names.

Other names of that table differ from the Linux names too, among them "TxUnderRun" at the
offset ``0x60``, where the Linux name is :counter:`TX_UNDERSIZE_ERR`, and "TxExcDefer" at the
offset ``0x9c``, where the Linux name is :counter:`TX_PKT`. Both of these entries are commented
out.

.. _mib-clear:

Clearing
--------

.. yt-bitfield:: MIB_CTRL

.. list-table::
   :header-rows: 1
   :widths: 32 12 18 20 18

   * - Goal
     - Write
     - :field:`MIB_CTRL.CLEAN`
     - :field:`MIB_CTRL.ONE_PORT`
     - :field:`MIB_CTRL.PORT`
   * - Clear the counters of every port
     - first
     - 0
     - 0
     - 0
   * - Clear the counters of every port
     - second
     - 1
     - 0
     - 0
   * - Clear the counters of one port
     - first
     - 0
     - 1
     - port number
   * - Clear the counters of one port
     - second
     - 1
     - 1
     - port number

A clear takes two writes to :reg:`MIB_CTRL`. The first selects the ports with
:field:`MIB_CTRL.CLEAN` at 0 and the second sets :field:`MIB_CTRL.CLEAN`. The sequence for one
port is that of the function
`fal_tiger_stat_mib_clear() <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_stat.c#L52>`__
of the :ref:`vendor SDK <sources-list>`, and the sequence for every port is that of
`fal_tiger_stat_mib_clear_all() <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_stat.c#L69>`__.
:lx:`mib.h` defines the fields of :reg:`MIB_CTRL` and no function of the
:ref:`Linux driver <sources-list>` uses them, so their meanings are :ev:`inferred` from their
names and from the two SDK functions.

It is :ev:`not known` whether :field:`MIB_CTRL.CLEAN` clears itself, which is why the first write
puts it back to 0. The function
`fal_tiger_stat_mib_clear_all() <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_stat.c#L69>`__ leaves
:field:`MIB_CTRL.ALL_PORT` at 0 for a clear of every port, and the effect of that bit is
:ev:`not known`.
