.. _lag:

Link aggregation
================

Two groups of up to four ports each (:const:`LAG_NUM`, :const:`LAG_PORT_NUM`) can act as one
logical link. The registers are in the :blk:`lag` block. The set-up sequence and the hash
bits are confirmed by the :ref:`Linux driver <sources-list>`. How a group interacts with
:ref:`port isolation <forwarding-isolation>` and with learned addresses is not known; give
all members of a group the same isolation mask, VLAN membership and spanning tree state.

.. _lag-group:

Set up a group
--------------

1. Write the member ports into the slots :reg:`LAG_MEMBER` of the group, starting at slot 0,
   one port number per slot.
2. Write :reg:`LAG_GROUP` with the member port mask in :field:`LAG_GROUP.PORTS` and the number
   of used slots in :field:`LAG_GROUP.MEMBER_NUM`.

.. yt-bitfield:: LAG_GROUP

The slot register of group *g*, slot *s* is at ``0x1805b0 + 16 × g + 4 × s``. To remove a
port, write the slots and the group again without it; a group with no ports has
:reg:`LAG_GROUP` equal to 0.

.. _lag-hash:

Hash
----

The switch picks the member for a frame by hashing the fields enabled in :reg:`LAG_HASH`. The
register is shared by both groups.

.. yt-bitfield:: LAG_HASH

For a layer 2 hash set :field:`LAG_HASH.MAC_SA` and :field:`LAG_HASH.MAC_DA`; add the IP and
layer 4 bits for a layer 3 and 4 hash.
