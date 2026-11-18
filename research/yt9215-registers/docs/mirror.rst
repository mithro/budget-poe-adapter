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
     - Set to
   * - :field:`MIRROR.PORT`
     - The monitor port number
   * - :field:`MIRROR.IGR_PORTS`
     - Ports whose received frames are copied
   * - :field:`MIRROR.EGR_PORTS`
     - Ports whose sent frames are copied

The three fields are confirmed by the :ref:`Linux driver <sources-list>`. There is one monitor port for the whole
switch. When adding a source port, keep the monitor
port unchanged if other sources are already set. An ACL rule can mirror selected frames to the
same monitor port; see :ref:`acl-action`.
