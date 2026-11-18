.. _yt921x:

YT921x switch programmer's guide
================================

The Motorcomm YT921x parts (:chip:`YT9215S`, :chip:`YT9215SC`, YT9215SCH, :chip:`YT9215RB`,
:chip:`YT9214NB`, :chip:`YT9213NB`, :chip:`YT9218N` and :chip:`YT9218MB`) are Gigabit Ethernet
switches with built-in copper PHYs. The YT9215SCH is :ref:`taken to behave <bringup-identify>`
as the :chip:`YT9215SC`. This manual is
for someone who writes a driver for one of them from scratch, for example for Zephyr or
MicroPython: it explains how to reach the registers, how to bring the switch up, how to use
each function, and it lists every known register bit by bit.

The vendor datasheets describe the pins and the electrical side but contain no register
addresses. Everything here is derived from the two public sources that do, the :ref:`Linux driver <sources-list>`
and the :ref:`vendor SDK <sources-list>`; :doc:`sources` says what comes from where and how far each
statement can be trusted.

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
   * - Read and write a register from a microcontroller
     - :doc:`access`
   * - Reset the switch and find out which part it is
     - :doc:`bringup`
   * - Get a port to pass traffic
     - :doc:`ports`
   * - Look a register up
     - :ref:`reference-all`
   * - Start from working code
     - :doc:`bindings`
   * - Load the register map into a tool
     - :doc:`description-files`
