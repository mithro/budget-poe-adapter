.. _acl:

Access control list
===================

The access control list (ACL) matches frames on header fields and applies an action: drop,
redirect, trap to the CPU, rate limit, change priority or tags. The registers are in the
:blk:`acl` block. The ACL works only while :field:`FUNC.ACL` is set; see
:ref:`bringup-features`.

.. _acl-model:

Blocks, slots, groups and rules
-------------------------------

The ACL memory is divided into blocks, and a block is the unit that is updated at once. Each
block has eight slots. A slot is one 64-bit key (:reg:`ACL_KEY`) with its mask
(:reg:`ACL_MASK`) and matches one set of header fields, chosen by its type. The reference
calls the slot number ``bin``.

A rule is one or more slots of one block that must all match. A rule that needs more fields
than one slot holds, for example both MAC addresses and an IPv4 address, takes several slots.
Every rule of a block has a group number from 0 to 7, and :reg:`ACL_ENTRY` records for each
slot the group it belongs to. The group number also selects the action of the rule: the
96-bit entry of :reg:`ACL_ACT` at index 8 × block + group.

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Item
     - Count
     - Constant
   * - Blocks
     - 48
     - :const:`ACL_BLK_NUM`
   * - Slots per block
     - 8
     - :const:`ACL_ENT_PER_BLK`
   * - Groups per block
     - 8
     - :const:`ACL_ENT_PER_BLK`
   * - Action entries
     - 384
     - :const:`ACL_NUM`

.. _acl-key:

Keys
----

.. yt-bitfield:: ACL_KEY

The upper bits are the same for every slot: :field:`ACL_KEY.TYPE` selects the layout of the
lower 36 bits, :field:`ACL_KEY.SPORTS` the receiving ports the slot applies to and
:field:`ACL_KEY.ORD` the order among matching rules: the rule with the highest ORD wins. The value list
:enum:`acl_type` names the types, and the :reg:`ACL_KEY` reference shows the layout of each.

A bit set in :reg:`ACL_MASK` means the same bit of the key must match; a clear bit is "don't
care". The mask covers only the lower, type-specific bits. :field:`ACL_KEY.TYPE`,
:field:`ACL_KEY.SPORTS`, :field:`ACL_KEY.ORD` and :field:`ACL_KEY.REVERSE` exist in the key
alone and always apply; leave their positions in
the mask at 0.

Types :val:`acl_type.UDF0` to :val:`acl_type.UDF7` match two-byte windows at configurable offsets. :reg:`UDF_CTRL`
sets each window: the header it is counted from (:enum:`udf_type`) and the offset in bytes
from the start of that header. The window is the two bytes at that offset.

.. _acl-action:

Actions
-------

.. yt-bitfield:: ACL_ACT

Each goal needs the fields of its rows set together.

.. list-table::
   :header-rows: 1
   :widths: 26 40 34

   * - Goal
     - Field of :reg:`ACL_ACT`
     - Value
   * - Drop the frame
     - :field:`ACL_ACT.FWD_EN`
     - 1
   * -
     - :field:`ACL_ACT.FWD`
     - :val:`ACL_ACT.FWD.REDIR` (2)
   * -
     - :field:`ACL_ACT.FWD_REDIR_DPORTS`
     - 0
   * - Redirect to ports
     - :field:`ACL_ACT.FWD_EN`
     - 1
   * -
     - :field:`ACL_ACT.FWD`
     - :val:`ACL_ACT.FWD.REDIR` (2)
   * -
     - :field:`ACL_ACT.FWD_REDIR_DPORTS`
     - Mask of the destination ports
   * - Trap to the CPU
     - :field:`ACL_ACT.FWD_EN`
     - 1
   * -
     - :field:`ACL_ACT.FWD`
     - :val:`ACL_ACT.FWD.TRAP` (3)
   * - Mirror
     - :field:`ACL_ACT.MIRROR_EN`
     - 1
   * - Rate limit
     - :field:`ACL_ACT.METER_EN`
     - 1
   * -
     - :field:`ACL_ACT.METER_ID`
     - Number of the meter
   * - Set the priority
     - :field:`ACL_ACT.PRIO_EN`
     - 1
   * -
     - :field:`ACL_ACT.PRIO`
     - Priority, 0 to 7

A mirrored frame goes to the monitor port in :field:`MIRROR.PORT` (:doc:`mirror`). The meter
is set up as in :ref:`rate-meter`. A priority from the ACL counts only if the ACL source is
ranked in :ref:`qos-sources`. Drop as a redirect to no port is the encoding of both the :ref:`Linux driver <sources-list>`
and the :ref:`vendor SDK <sources-list>`.

.. _acl-setup:

One-time setup
--------------

1. Set :field:`FUNC.ACL`.
2. Write ``0x7ff`` to :reg:`ACL_PERMIT_UNMATCH` so that frames that match no rule are
   forwarded normally.
3. Write 0 to :reg:`ACL_PORT`; set a port's bit there when the first rule for that port is
   written.
4. Program the :reg:`UDF_CTRL` windows if rules will use them.

.. _acl-write:

Writing a rule
--------------

A block is changed as a whole: open it, write the new content, and commit. That the switch
keeps using the old content until the commit is inferred from this protocol.

.. yt-diagram:: acl-sequence
   :caption: Writing one rule into a block.

1. Write the three words of the rule's :reg:`ACL_ACT` entry.
2. Write :reg:`ACL_BLK_CMD` with the block number and :field:`ACL_BLK_CMD.MODIFY` set.
3. Write :reg:`ACL_KEY` and :reg:`ACL_MASK` of every slot of the rule, two words each.
4. Write :reg:`ACL_BLK_KEEP` with :field:`ACL_BLK_KEEP.KEEP` set for every slot of the block
   that was not written in step 3, so that the other rules of the block survive.
5. Write :reg:`ACL_ENTRY` of the block with the state of all eight slots:
   :field:`ACL_ENTRY.EN` for each slot in use and in :field:`ACL_ENTRY.GRPID` the group it
   belongs to.
6. Write :reg:`ACL_BLK_CMD` with the block number and :field:`ACL_BLK_CMD.MODIFY` clear to
   commit.

To delete a rule, run the same sequence with zeros for its action, keys and masks and without
its slots in :reg:`ACL_ENTRY`.

The sequence is confirmed by the :ref:`Linux driver <sources-list>`. This manual has no tested example code for
the ACL.
