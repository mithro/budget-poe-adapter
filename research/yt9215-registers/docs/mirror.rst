.. _mirror:

Port mirroring
==============

The switch can copy the frames of chosen ports to one monitor port. The whole function is the
register :reg:`MIRROR` in the :blk:`mirror` block.

.. yt-bitfield:: MIRROR

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Field
     - Content
   * - :field:`MIRROR.PORT`
     - number of the monitor port
   * - :field:`MIRROR.IGR_PORTS`
     - mask of the ports whose received frames are copied
   * - :field:`MIRROR.EGR_PORTS`
     - mask of the ports whose sent frames are copied

The three fields are :ev:`confirmed` by :lx:`yt921x_mirror_add` of the
:ref:`Linux driver <sources-list>`. There is one monitor port for the whole switch. When
adding a source port, keep the monitor port unchanged if other sources are already set, as
:lx:`yt921x_mirror_add` does. An ACL rule can mirror selected frames to the same monitor
port with the field :field:`ACL_ACT.MIRROR_EN` of :ref:`acl-action`.
