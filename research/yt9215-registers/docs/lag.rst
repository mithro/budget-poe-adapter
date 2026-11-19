.. _lag:

Link aggregation
================

The switch has :const:`LAG_NUM` (2) groups of up to :const:`LAG_PORT_NUM` (4) ports. The
ports of a group act as one logical link. The registers are in the :blk:`lag` block.

The :ref:`set-up sequence <lag-group>` is :ev:`confirmed` by :lx:`yt921x_lag_set` of the
:ref:`Linux driver <sources-list>` and the :ref:`hash bits <lag-hash>` by
:lx:`yt921x_dsa_port_lag_join`, which chooses the bits. It is :ev:`not known` how a group
interacts with :ref:`port isolation <forwarding-isolation>` and with learned addresses. Give all
members of a group the same isolation mask, VLAN membership and spanning tree state.

.. _lag-group:

Set up a group
--------------

1. Write the member ports into the slots :reg:`LAG_MEMBER` of the group, starting at slot 0,
   one port number per slot.
2. Write :reg:`LAG_GROUP` with the member port mask in :field:`LAG_GROUP.PORTS` and the number
   of used slots in :field:`LAG_GROUP.MEMBER_NUM`.

.. yt-bitfield:: LAG_GROUP

The reference entry of :reg:`LAG_MEMBER` gives the address of each slot register. To remove
a port, write the slots and the group again without it. A group with no ports has
:reg:`LAG_GROUP` equal to 0.

.. _lag-hash:

Hash
----

The switch picks the member for a frame by hashing the fields enabled in :reg:`LAG_HASH`. The
register is shared by both groups.

.. yt-bitfield:: LAG_HASH

The field table of :reg:`LAG_HASH` lists the hash inputs. For a layer 2 hash
set :field:`LAG_HASH.MAC_SA` and :field:`LAG_HASH.MAC_DA`.
