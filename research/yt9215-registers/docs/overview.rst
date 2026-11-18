.. _overview:

Overview of the chip
====================

A YT921x is an Ethernet switch with up to eleven ports, numbered 0 to 10. Software sees it as
a file of 32-bit registers that it reads and writes over the two-wire MDIO management
interface. Nothing else is needed to control the switch: there is no firmware to load.

.. yt-diagram:: system
   :caption: A host and the parts of the switch it deals with. The boxes are links.

.. _overview-ports:

Ports
-----

Ports 0 to 7 have a built-in 10/100/1000BASE-T PHY; the YT9215 family has five of them
(ports 0 to 4) and the YT9218 family eight. Ports 8 and 9 are the external ports: depending on
the part each has an SGMII-class SerDes, parallel MAC pins (MII, RMII or RGMII, called xMII in
this manual) or both. Port 10 leads to a microcontroller inside the chip, which a host
driver leaves alone. :ref:`reference-parts-ports` lists the ports of every part.

A host that wants to send and receive frames through the switch connects its own Ethernet MAC
to one of the external ports. That port is then the CPU port, and frames on it can carry an
8-byte tag that names the port a frame came from or must go to; see :doc:`cpu-tag`.

A set of ports is always written as a bit mask in which bit *n* stands for port *n*; a mask of
all ports is ``0x7ff``.

.. _overview-frame-path:

The path of a frame
-------------------

The functions of the switch are easiest to learn in the order a frame meets them. Each box
below is a link to the page that describes the stage.

.. yt-diagram:: frame-path
   :caption: Stages a frame passes through, from the receiving to the sending port.

The order shown is a model to reason with. One point of it is confirmed by the Linux driver:
port isolation is applied after the destination lookup (a frame whose known destination is
blocked is dropped, not flooded).
The rest of the order follows how switches of this kind are usually built and is not
confirmed.

.. _overview-driver:

What a driver has to do
-----------------------

.. list-table::
   :header-rows: 1
   :widths: 6 44 50

   * - Step
     - Task
     - Described in
   * - 1
     - Implement register read and write on top of an MDIO bus
     - :ref:`access-smi`
   * - 2
     - Find the switch, reset it and identify the part
     - :ref:`bringup-reset`
   * - 3
     - Turn on the optional function blocks
     - :ref:`bringup-features`
   * - 4
     - Choose the CPU port and decide whether it carries tags
     - :ref:`cpu-tag`
   * - 5
     - Configure the external ports and enable the port MACs
     - :ref:`ports-up`
   * - 6
     - Group ports and set the handling of unknown destinations
     - :ref:`forwarding-isolation`
   * - 7
     - Add VLANs, static addresses, counters and the rest as needed
     - :doc:`vlan`

Without any register writes the chip already forwards frames between its ports as an
unmanaged switch, in the configuration its strap pins select. A driver only has to do the
steps whose function it needs.

.. _overview-conventions:

Conventions
-----------

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Notation
     - Meaning
   * - :reg:`PORT_CTRL`
     - A register; the name is a link to its description.
   * - :field:`PORT_CTRL.SPEED`
     - A field of a register.
   * - ``PORT_CTRL[port]``
     - A register that exists once per value of the index ``port``.
   * - ``17:6``
     - Bits 17 down to 6; bit 0 is the least significant bit.
   * - ``0x7ff``
     - A hexadecimal number.

Register and field names are the ones the :doc:`bindings <bindings>` use. They follow the
Linux driver, with index letters removed; the :ref:`Sources table <evidence>` of each register
gives the original Linux name and the vendor SDK name.
