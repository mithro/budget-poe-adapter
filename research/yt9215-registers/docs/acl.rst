.. _acl:

Access control list
===================

The access control list (ACL) matches frames on header fields and applies an action: drop,
redirect, trap to the CPU, rate limit, change priority or tags. The registers are in the
:blk:`acl` block. The ACL works only while :field:`FUNC.ACL` is set; see
:ref:`bringup-features`.

.. _acl-model:

Blocks, slots and rules
-----------------------

.. list-table::
   :header-rows: 1
   :widths: 20 16 64

   * - Item
     - Count
     - Meaning
   * - Block
     - :const:`ACL_BLK_NUM`
     - A unit that is updated at once.
   * - Slot
     - :const:`ACL_ENT_PER_BLK` per block
     - One 64-bit key (:reg:`ACL_KEY`) and mask (:reg:`ACL_MASK`). A slot matches one group of
       header fields, chosen by its type.
   * - Rule
     - Up to 8 per block
     - One or more slots of one block that must all match. :reg:`ACL_ENTRY` groups slots into
       rules.
   * - Action
     - :const:`ACL_NUM`
     - One 96-bit :reg:`ACL_ACT` entry per slot position. A rule uses the entry of the slot
       its group is named after: index 8 × block + group.

A rule that needs more fields than one slot holds, for example both MAC addresses and an IPv4
address, takes several slots of the same block.

.. _acl-key:

Keys
----

.. yt-bitfield:: ACL_KEY

The upper bits are the same for every slot: :field:`ACL_KEY.TYPE` selects the layout of the
lower 36 bits, :field:`ACL_KEY.SPORTS` the receiving ports the slot applies to and
:field:`ACL_KEY.ORD` the order among matching rules, lowest first. The value list
:enum:`acl_type` names the types, and the :reg:`ACL_KEY` reference shows the layout of each.

A bit set in :reg:`ACL_MASK` means the same bit of the key must match; a clear bit is "don't
care". Set the mask bits of TYPE as well, or the slot matches frames regardless of type.

Types ``UDF0`` to ``UDF7`` match two-byte windows at configurable offsets. :reg:`UDF_CTRL`
sets each window: the header it is counted from (:enum:`udf_type`) and the offset in units of
two bytes.

.. _acl-action:

Actions
-------

.. yt-bitfield:: ACL_ACT

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Goal
     - Fields of :reg:`ACL_ACT`
   * - Drop the frame
     - :field:`ACL_ACT.FWD_EN`, :field:`ACL_ACT.FWD` = ``REDIR`` (2) with no destination port
   * - Redirect to ports
     - :field:`ACL_ACT.FWD_EN`, ``REDIR`` and the ports in :field:`ACL_ACT.FWD_REDIR_DPORTS`
   * - Trap to the CPU
     - :field:`ACL_ACT.FWD_EN`, :field:`ACL_ACT.FWD` = ``TRAP`` (3)
   * - Mirror
     - :field:`ACL_ACT.MIRROR_EN`; the monitor port is :field:`MIRROR.PORT`
   * - Rate limit
     - :field:`ACL_ACT.METER_EN` and :field:`ACL_ACT.METER_ID`; see :ref:`rate-meter`
   * - Set the priority
     - :field:`ACL_ACT.PRIO_EN` and :field:`ACL_ACT.PRIO`; needs the ``ACL`` source in
       :ref:`qos-sources`

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

A block is changed as a whole: open it, write the new content, and commit. The switch keeps
using the old content until the commit.

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
6. Write :reg:`ACL_BLK_CMD` with the block number and MODIFY clear to commit.

To delete a rule, run the same sequence with zeros for its action, keys and masks and without
its slots in :reg:`ACL_ENTRY`.

This is the sequence of the Linux driver. This manual has no tested example code for the ACL.
