.. _fdb:

Forwarding database
===================

The forwarding database maps a MAC address and a filtering ID to destination ports. It has
:const:`FDB_NUM` (4096) entries. The switch fills it by learning. The host reads and changes
it through a command interface, the registers of the :blk:`fdb` block.

.. _fdb-command:

Running a command
-----------------

.. yt-diagram:: fdb-sequence
   :caption: One forwarding database command.

1. Write the input registers :reg:`FDB_IN0`, :reg:`FDB_IN1` and :reg:`FDB_IN2`.
2. Write :reg:`FDB_OP` with the command in :field:`FDB_OP.OP` and :field:`FDB_OP.START` set.
3. Read :reg:`FDB_RESULT` until :field:`FDB_RESULT.DONE` is 1, with the loop of
   :ref:`access-wait`.
4. Check :field:`FDB_RESULT.NOTFOUND`. For a lookup, read the entry from :reg:`FDB_OUT0`,
   :reg:`FDB_OUT1` and :reg:`FDB_OUT2`.

The sequence is :ev:`confirmed` by :lx:`yt921x_fdb_add`, :lx:`yt921x_fdb_wait` and
:lx:`yt921x_fdb_read` of the :ref:`Linux driver <sources-list>`.

.. yt-bitfield:: FDB_OP

.. list-table::
   :header-rows: 1
   :widths: 8 22 22 24 24

   * - Value
     - Command
     - Effect
     - Selector
     - Second selector
   * - 0
     - :val:`FDB_OP.OP.ADD`
     - write one entry
     - :ref:`key <fdb-entry>`
     - :field:`FDB_OP.INDEX`
   * - 1
     - :val:`FDB_OP.OP.DEL`
     - remove one entry
     - :ref:`key <fdb-entry>`
     - none
   * - 2
     - :val:`FDB_OP.OP.GET_ONE`
     - read one entry
     - :ref:`key <fdb-entry>`
     - :field:`FDB_OP.INDEX`
   * - 3
     - :val:`FDB_OP.OP.GET_NEXT`
     - read the next entry
     - :field:`FDB_OP.INDEX`
     - :field:`FDB_OP.NEXT_TYPE`
   * - 4
     - :val:`FDB_OP.OP.FLUSH`
     - remove many entries
     - :field:`FDB_OP.FLUSH`
     - none

It is :ev:`not known` whether :val:`FDB_OP.OP.ADD` by key replaces an entry that has the same
key. It is :ev:`inferred` from the name of :field:`FDB_RESULT.OVERWRITED` that the bit reports
such a replacement, and the :ref:`vendor SDK <sources-list>` function
`fal_tiger_l2_fdb_mcast_addr_add() <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_l2.c#L132>`__
adds by key without a lookup. :lx:`yt921x_fdb_join` looks the entry up first and writes an existing entry back by its
index.
:field:`FDB_OP.MODE_INDEX` decides whether :val:`FDB_OP.OP.GET_ONE` uses the key or the
index.

.. tab-set::

   .. tab-item:: C
      :sync: c

      From :download:`guide.c <../bindings/c/examples/guide.c>`.

      .. literalinclude:: ../bindings/c/examples/guide.c
           :language: c
           :start-after: /* [fdb-wait] */
           :end-before: /* [fdb-wait end] */

   .. tab-item:: MicroPython
      :sync: micropython

      From :download:`guide.py <../bindings/micropython/examples/guide.py>`.

      .. literalinclude:: ../bindings/micropython/examples/guide.py
           :language: python
           :start-after: # [fdb-wait]
           :end-before: # [fdb-wait end]

.. _fdb-entry:

An entry
--------

An entry is three words. The input registers and the output registers share one layout:
:lx:`chip.h` defines the fields of both under the names ``IO0``, ``IO1`` and ``IO2``.

.. yt-bitfield:: FDB_IN0

.. yt-bitfield:: FDB_IN1

.. yt-bitfield:: FDB_IN2

The key is the MAC address, split over :field:`FDB_IN0.ADDR_HI4` and
:field:`FDB_IN1.ADDR_LO2`, and the filtering ID in :field:`FDB_IN1.FID`.
:lx:`yt921x_fdb_in01` writes the VLAN ID as the filtering ID. For the address
``02:11:22:33:44:55``, :field:`FDB_IN0.ADDR_HI4` is ``0x02112233`` and
:field:`FDB_IN1.ADDR_LO2` is ``0x4455``.

:field:`FDB_IN1.STATUS` tells static from learned entries. It is :ev:`inferred` from the value
names :val:`FDB_IN1.STATUS.MIN_TIME` and :val:`FDB_IN1.STATUS.MOVE_AGING_MAX_TIME` that the field also
carries the age of a learned entry. Write :val:`FDB_IN1.STATUS.STATIC` for an entry that must stay. The status
:val:`FDB_OUT1.STATUS.INVALID` in a result means that the entry is empty, which is how
:lx:`yt921x_fdb_read` treats it.
:field:`FDB_IN2.EGR_PORTS` is the destination port mask. :lx:`yt921x_fdb_add` writes the mask
of an entry that does not exist yet, and :lx:`yt921x_fdb_join` adds the bit of one more port to
the mask of an entry that exists. :lx:`yt921x_dsa_port_fdb_add` and
:lx:`yt921x_dsa_port_mdb_add` both call :lx:`yt921x_fdb_join`.

.. _fdb-add:

Add a static entry
------------------

.. tab-set::

   .. tab-item:: C
      :sync: c

      From :download:`guide.c <../bindings/c/examples/guide.c>`.

      .. literalinclude:: ../bindings/c/examples/guide.c
           :language: c
           :start-after: /* [fdb-add] */
           :end-before: /* [fdb-add end] */

   .. tab-item:: MicroPython
      :sync: micropython

      From :download:`guide.py <../bindings/micropython/examples/guide.py>`.

      .. literalinclude:: ../bindings/micropython/examples/guide.py
           :language: python
           :start-after: # [fdb-add]
           :end-before: # [fdb-add end]

To add a port to a multicast group, :ref:`look the entry up <fdb-lookup>`, set the port's bit in
the port mask that comes back and write the entry back at its index: run :val:`FDB_OP.OP.ADD` with
:field:`FDB_OP.MODE_INDEX` set. To remove the last port, delete the entry. :lx:`yt921x_fdb_join`
and :lx:`yt921x_fdb_leave` work in this way through :lx:`yt921x_fdb_add_index_in12`.

.. _fdb-lookup:

Look an address up
------------------

.. tab-set::

   .. tab-item:: C
      :sync: c

      From :download:`guide.c <../bindings/c/examples/guide.c>`.

      .. literalinclude:: ../bindings/c/examples/guide.c
           :language: c
           :start-after: /* [fdb-get] */
           :end-before: /* [fdb-get end] */

   .. tab-item:: MicroPython
      :sync: micropython

      From :download:`guide.py <../bindings/micropython/examples/guide.py>`.

      .. literalinclude:: ../bindings/micropython/examples/guide.py
           :language: python
           :start-after: # [fdb-get]
           :end-before: # [fdb-get end]

.. _fdb-walk:

Walk the database
-----------------

To list entries, address them by index: set :field:`FDB_OP.MODE_INDEX` and put the index in
:field:`FDB_OP.INDEX`.

1. Run :val:`FDB_OP.OP.GET_ONE` with index 0 and handle the entry if its status is not
   :val:`FDB_OUT1.STATUS.INVALID`.
2. Run :val:`FDB_OP.OP.GET_NEXT` with the index of the last
   entry seen. :field:`FDB_OP.NEXT_TYPE` selects what counts as next; for
   :val:`FDB_OP.NEXT_TYPE.UCAST_PORT` put the ports of interest in :field:`FDB_IN2.EGR_PORTS`
   first.
3. Take the new index from :field:`FDB_RESULT.INDEX` and repeat until the result is
   :field:`NOTFOUND <FDB_RESULT.NOTFOUND>` or the index reaches 4095 (:const:`FDB_NUM` − 1).

The three steps are :ev:`confirmed` by :lx:`yt921x_fdb_dump`, which reads each entry with
:lx:`yt921x_fdb_read`. That function also stops at a result whose
:field:`FDB_OUT1.STATUS` is :val:`FDB_OUT1.STATUS.INVALID` or whose port mask is 0.

.. warning::

   Never run :val:`FDB_OP.OP.GET_NEXT` with index 4095. A comment in :lx:`chip.c:629`, inside
   :lx:`yt921x_fdb_dump`, states that the command then hangs and the database stays unusable
   until the switch is reset.

.. _fdb-flush:

Flush
-----

:val:`FDB_OP.OP.FLUSH` removes learned entries in bulk. With :field:`FDB_OP.FLUSH_STATIC` it
removes static ones as well. The command and the rows :val:`FDB_OP.FLUSH.PORT` and
:val:`FDB_OP.FLUSH.PORT_VID` of the :ref:`selection table <fdb-flush-table>` are
:ev:`confirmed` by :lx:`yt921x_fdb_flush_raw`. The other two rows have the level
:ev:`header`.

The command works on unicast entries, or on multicast entries when
:field:`FDB_OP.FLUSH_MCAST` is set, so that emptying the database takes one flush of each
kind. No function of the :ref:`Linux driver <sources-list>` sets the field, and the comment
on its definition in :lx:`chip.h:260` reads "ucast / mcast". The
:ref:`vendor SDK <sources-list>` treats the field and :field:`FDB_OP.FLUSH` as one field of
three bits, and its list
`yt_l2_tbl_op_flush_mode_t <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_l2.h#L80>`__
gives the values 0 to 3 to the four scopes for unicast entries and the values 4 to 7 to the
same scopes for multicast entries.

.. _fdb-flush-table:

.. list-table::
   :header-rows: 1
   :widths: 10 24 33 33

   * - Value
     - :field:`FDB_OP.FLUSH`
     - Port filter
     - Filtering ID filter
   * - 0
     - :val:`FDB_OP.FLUSH.ALL`
     - none
     - none
   * - 1
     - :val:`FDB_OP.FLUSH.PORT`
     - :field:`FDB_IN2.EGR_PORTS`
     - none
   * - 2
     - :val:`FDB_OP.FLUSH.PORT_VID`
     - :field:`FDB_IN2.EGR_PORTS`
     - :field:`FDB_IN1.FID`
   * - 3
     - :val:`FDB_OP.FLUSH.VID`
     - none
     - :field:`FDB_IN1.FID`

Flush the entries of a port when its link goes down or its spanning tree state changes.
:field:`FDB_HW_FLUSH.ON_LINKDOWN` lets the switch flush on link-down by itself. The function
`fal_tiger_l2_fdb_addr_flush() <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_l2.c#L385>`__
of the :ref:`vendor SDK <sources-list>` refuses a flush command while
:field:`FDB_HW_FLUSH.ON_LINKDOWN` is set, so use one method or the other. The meaning of the
bit is :ev:`inferred` from its name and from that SDK function. No function of the
:ref:`Linux driver <sources-list>` sets it.

.. _fdb-ageing:

Ageing
------

:field:`AGEING.INTERVAL` is the ageing time of learned entries in units of 5 seconds, so 60
stands for 300 seconds, the default ageing time of `IEEE 802.1Q <https://en.wikipedia.org/wiki/IEEE_802.1Q>`__. The unit is
:ev:`confirmed` by :lx:`yt921x_dsa_set_ageing_time`, whose comment reads "AGEING reg is set in
5s step".
