.. _overview:

Overview of the chip
====================

A YT921x is an Ethernet switch with up to eleven ports, numbered 0 to 10. Software sees it as
a file of 32-bit registers that it reads and writes over the two-wire MDIO management
interface. The :ref:`Linux driver <sources-list>` controls the switch through these registers
alone and loads no firmware.

Sections 5.5.1 and 5.5.3 of the |ds| describe two more host interfaces to the same registers, I2C
and SPI, which strap pins select. This manual covers MDIO only. :ref:`access-straps` names
the pins.

.. yt-diagram:: system
   :caption: A host and the parts of the switch it deals with. The boxes are links.

.. _overview-ports:

Ports
-----

Ports 0 to 7 have a built-in Gigabit copper PHY that also runs at 10 and 100 Mbit/s. The
:ref:`YT9215 family <reference-parts>` has five of them (ports 0 to 4) and the
:ref:`YT9218 family <reference-parts>` eight. Ports 8 and 9 are the external ports. Depending
on the part each has an SGMII-class SerDes, parallel MAC pins or both. This manual calls the
parallel MAC pins xMII; they carry MII, RMII or RGMII. Port 10 leads to a microcontroller
inside the chip, which a host driver leaves alone. :ref:`reference-parts-ports` lists the
ports of every part.

A host that wants to send and receive frames through the switch connects its own Ethernet MAC
to one of the external ports. That port is then the CPU port, and frames on it can carry the
8-byte tag of :doc:`cpu-tag`, which names the port a frame came from or must go to.

A set of ports is always written as a bit mask in which bit *n* stands for port *n*; a mask of
all ports is ``0x7ff``.

.. _overview-frame-path:

The path of a frame
-------------------

The functions of the switch are easiest to learn in the order a frame meets them. Each box
of the diagram is a link to the page that describes the stage.

.. yt-diagram:: frame-path
   :caption: Stages a frame passes through, from the receiving to the sending port.

The order of the stages is :ev:`inferred` from the order in which IEEE 802.1Q describes the
forwarding process, with one exception. A comment in :lx:`yt921x_chip_setup_dsa` states
that port isolation is applied after the destination lookup: a frame whose known destination
is blocked is dropped, not flooded.

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
     - Enable the port MACs
     - :ref:`ports-up`
   * - 6
     - Configure the external ports
     - :ref:`ports-external`
   * - 7
     - Group ports
     - :ref:`forwarding-isolation`
   * - 8
     - Set the handling of unknown destinations
     - :ref:`forwarding-flood`
   * - 9
     - Add VLANs
     - :doc:`vlan`
   * - 10
     - Add static addresses
     - :doc:`fdb`
   * - 11
     - Read counters
     - :doc:`mib`

Steps 1 to 5 and step 7 are needed for any traffic to pass. Step 6 applies to a part that
uses port 8 or port 9, and steps 8 to 11 are needed only for the function they name.

.. _overview-init:

The example is a start-up in code, built from the examples of steps 1 to 5 and step 7. It
finds, resets and identifies the switch, turns on the function blocks, sets up a tagged CPU
port, forces its MAC to 1000 Mbit/s full duplex and puts all copper ports into one group. It
leaves three tasks to the driver.

* Select the interface of the CPU port (:ref:`ports-external`).
* Enable the MAC of each copper port when its link comes up (:ref:`ports-up`).
* Set the handling of unknown destinations (:ref:`forwarding-flood`).

.. tab-set::

   .. tab-item:: C
      :sync: c

      From :download:`guide.c <../bindings/c/examples/guide.c>`.

      .. literalinclude:: ../bindings/c/examples/guide.c
           :language: c
           :start-after: /* [init] */
           :end-before: /* [init end] */

   .. tab-item:: MicroPython
      :sync: micropython

      From :download:`guide.py <../bindings/micropython/examples/guide.py>`.

      .. literalinclude:: ../bindings/micropython/examples/guide.py
           :language: python
           :start-after: # [init]
           :end-before: # [init end]

Table 25 of the |ds| lists the start-up modes that strap pins select. In the modes that
load a configuration from an EEPROM or from flash, the switch is configured without a host.

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
:ref:`Linux driver <sources-list>`, with index letters removed. The reference entry of each
register gives the original Linux name and the :ref:`vendor SDK <sources-list>` name, in the
rows and tables that :ref:`sources-sdk` explains.
