.. _fdb:

Forwarding database
===================

The forwarding database maps a MAC address and a filtering ID to destination ports. It has
4096 entries (:const:`FDB_NUM`). The switch fills it by learning; the host reads and changes
it through a command interface, the registers of the :blk:`fdb` block.

.. _fdb-command:

Running a command
-----------------

.. yt-diagram:: fdb-sequence
   :caption: One forwarding database command.

1. Write the input registers :reg:`FDB_IN0`, :reg:`FDB_IN1` and :reg:`FDB_IN2`.
2. Write :reg:`FDB_OP` with the command in :field:`FDB_OP.OP` and :field:`FDB_OP.START` set.
3. Read :reg:`FDB_RESULT` until :field:`FDB_RESULT.DONE` is 1, as in :ref:`access-wait`.
4. Check :field:`FDB_RESULT.NOTFOUND`; for a lookup, read the entry from :reg:`FDB_OUT0`,
   :reg:`FDB_OUT1` and :reg:`FDB_OUT2`.

.. yt-bitfield:: FDB_OP

.. list-table::
   :header-rows: 1
   :widths: 10 18 72

   * - Value
     - Command
     - Effect
   * - 0
     - ``ADD``
     - Write the entry in the input registers, replacing an entry with the same key.
   * - 1
     - ``DEL``
     - Remove the entry with the key in the input registers.
   * - 2
     - ``GET_ONE``
     - Read the entry with that key, or the entry at :field:`FDB_OP.INDEX`.
   * - 3
     - ``GET_NEXT``
     - Read the next entry after :field:`FDB_OP.INDEX` that matches :field:`FDB_OP.NEXT_TYPE`.
   * - 4
     - ``FLUSH``
     - Remove many entries, selected by :field:`FDB_OP.FLUSH`.

.. tab-set::

   .. tab-item:: C
      :sync: c

      .. literalinclude:: ../bindings/c/examples/guide.c
           :language: c
           :start-after: /* [fdb-wait] */
           :end-before: /* [fdb-wait end] */

   .. tab-item:: MicroPython
      :sync: micropython

      .. literalinclude:: ../bindings/micropython/examples/guide.py
           :language: python
           :start-after: # [fdb-wait]
           :end-before: # [fdb-wait end]

.. _fdb-entry:

An entry
--------

An entry is three words. The input registers and the output registers share one layout.

.. yt-bitfield:: FDB_IN0

.. yt-bitfield:: FDB_IN1

.. yt-bitfield:: FDB_IN2

The key is the MAC address, split over :field:`FDB_IN0.ADDR_HI4` and
:field:`FDB_IN1.ADDR_LO2`, and the filtering ID in :field:`FDB_IN1.FID`, for which the Linux
driver uses the VLAN ID. For the address ``02:11:22:33:44:55``, ``ADDR_HI4`` is
``0x02112233`` and ``ADDR_LO2`` is ``0x4455``.

:field:`FDB_IN1.STATUS` tells static from learned entries and carries the age of learned ones.
Write ``STATIC`` (7) for an entry that must stay; ``INVALID`` (0) in a result means the slot
is empty. :field:`FDB_IN2.EGR_PORTS` is the destination port mask: one bit for a unicast
address, several for a multicast group.

.. _fdb-add:

Add a static entry
------------------

.. tab-set::

   .. tab-item:: C
      :sync: c

      .. literalinclude:: ../bindings/c/examples/guide.c
           :language: c
           :start-after: /* [fdb-add] */
           :end-before: /* [fdb-add end] */

   .. tab-item:: MicroPython
      :sync: micropython

      .. literalinclude:: ../bindings/micropython/examples/guide.py
           :language: python
           :start-after: # [fdb-add]
           :end-before: # [fdb-add end]

To add a port to a multicast group, look the entry up first, set the port's bit in the port
mask that comes back and add the entry again. To remove the last port, delete the entry.

.. _fdb-lookup:

Look an address up
------------------

.. tab-set::

   .. tab-item:: C
      :sync: c

      .. literalinclude:: ../bindings/c/examples/guide.c
           :language: c
           :start-after: /* [fdb-get] */
           :end-before: /* [fdb-get end] */

   .. tab-item:: MicroPython
      :sync: micropython

      .. literalinclude:: ../bindings/micropython/examples/guide.py
           :language: python
           :start-after: # [fdb-get]
           :end-before: # [fdb-get end]

.. _fdb-walk:

Walk the table
--------------

To list entries, address them by index: set :field:`FDB_OP.MODE_INDEX` and put the index in
:field:`FDB_OP.INDEX`.

1. Run ``GET_ONE`` with index 0 and handle the entry if its status is not ``INVALID``.
2. Run ``GET_NEXT`` with the index of the last entry seen. :field:`FDB_OP.NEXT_TYPE` selects
   what counts as next; for ``UCAST_PORT`` put the ports of interest in
   :field:`FDB_IN2.EGR_PORTS` first.
3. Take the new index from :field:`FDB_RESULT.INDEX` and repeat until the result is
   ``NOTFOUND`` or the index reaches 4095.

.. warning::

   Never run ``GET_NEXT`` with index 4095. The Linux driver documents that the command then
   never completes and the database stays stuck until the switch is reset.

.. _fdb-flush:

Flush
-----

``FLUSH`` removes learned entries in bulk; with :field:`FDB_OP.FLUSH_STATIC` it removes static
ones as well.

.. list-table::
   :header-rows: 1
   :widths: 14 20 66

   * - Value
     - :field:`FDB_OP.FLUSH`
     - Entries removed
   * - 0
     - ``ALL``
     - Every entry
   * - 1
     - ``PORT``
     - Entries of the ports in :field:`FDB_IN2.EGR_PORTS`
   * - 2
     - ``PORT_VID``
     - Entries of those ports with the filtering ID in :field:`FDB_IN1.FID`
   * - 3
     - ``VID``
     - Entries with the filtering ID in :field:`FDB_IN1.FID`

Flush the entries of a port when its link goes down or its spanning tree state changes, or
set :field:`FDB_HW_FLUSH.ON_LINKDOWN` and let the switch do the first of these.

.. _fdb-ageing:

Ageing
------

:field:`AGEING.INTERVAL` is the ageing time of learned entries in units of 5 seconds, so 60
stands for the usual 300 seconds.
