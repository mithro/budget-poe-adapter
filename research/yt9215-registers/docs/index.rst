.. _yt921x:

YT921x switch programmer's guide
================================

The Motorcomm YT921x parts are Gigabit Ethernet switches with built-in copper PHYs.
:ref:`reference-parts` lists the eight parts this manual covers. The manual is for someone who
writes a driver for one of them from scratch, for example for Zephyr or MicroPython. It
explains how to reach the registers, how to bring the switch up and how to use each function,
and it lists every known register bit by bit.

The |ds| describes the pins and the electrical side and gives the address of one register,
:reg:`RST`. All other register content is derived from the :ref:`Linux driver <sources-list>`
and the :ref:`vendor SDK <sources-list>`. :doc:`sources` lists the sources and defines the
evidence level that every register, field and procedure carries.

.. toctree::
   :maxdepth: 1
   :caption: Guide

   overview
   access
   bringup
   ports
   phy
   cpu-tag
   forwarding
   vlan
   fdb
   mib
   qos
   lag
   acl
   rate
   mirror
   leds

.. toctree::
   :maxdepth: 2
   :caption: Reference

   reference/index

.. toctree::
   :maxdepth: 1
   :caption: Code and files

   bindings
   description-files
   sources

Where to start
--------------

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Goal
     - Read
   * - Understand what the chip contains
     - :doc:`overview`
   * - Access a register from a microcontroller
     - :doc:`access`
   * - Start the switch
     - :doc:`bringup`
   * - Get a port to pass traffic
     - :doc:`ports`
   * - Look a register up
     - :ref:`reference-all`
   * - Start from working code
     - :doc:`bindings`
   * - Load the register map into a tool
     - :doc:`description-files`
