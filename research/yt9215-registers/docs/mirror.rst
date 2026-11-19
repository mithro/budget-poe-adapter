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
:ref:`Linux driver <sources-list>`. There is one monitor port for the whole switch. 
:lx:`yt921x_mirror_add` refuses a different monitor port while other source ports are set, so
change the monitor port only when no source port is set. It is :ev:`inferred` from the name of
:field:`ACL_ACT.MIRROR_EN` of :ref:`acl-action` that an ACL rule can mirror selected frames to
the same monitor port.
