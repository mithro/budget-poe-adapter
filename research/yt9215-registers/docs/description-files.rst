.. _description-files:

Register description files
==========================

The register map exists in three machine-readable forms. The YAML form is the source of this
manual and of the :doc:`bindings <bindings>`. The CMSIS-SVD and SystemRDL forms are generated
from it for tools that read those formats.

.. list-table::
   :header-rows: 1
   :widths: 28 18 24 30

   * - File
     - Format
     - Family
     - Content
   * - :download:`yt921x.yaml <../yt921x.yaml>`
     - YAML
     - both
     - Registers of this manual
   * - :download:`sdk-tables.yaml <../sdk-tables.yaml>`
     - YAML
     - both
     - Tables of the :ref:`vendor SDK <sources-list>`
   * - :download:`yt9215.svd <../svd/yt9215.svd>`
     - CMSIS-SVD 1.3
     - :ref:`YT9215 <reference-parts>`
     - Registers of this manual
   * - :download:`yt9218.svd <../svd/yt9218.svd>`
     - CMSIS-SVD 1.3
     - :ref:`YT9218 <reference-parts>`
     - Registers of this manual
   * - :download:`yt9215.rdl <../rdl/yt9215.rdl>`
     - SystemRDL 2.0
     - :ref:`YT9215 <reference-parts>`
     - Registers of this manual
   * - :download:`yt9218.rdl <../rdl/yt9218.rdl>`
     - SystemRDL 2.0
     - :ref:`YT9218 <reference-parts>`
     - Registers of this manual

Every other file is generated from :download:`yt921x.yaml <../yt921x.yaml>`.
:download:`sdk-tables.yaml <../sdk-tables.yaml>` holds table names and bit positions only.
There is one SVD and one SystemRDL file per family because :reg:`IO_LEVEL` has a different
layout in each.

.. _description-files-svd:

How the SVD files represent the registers
-----------------------------------------

CMSIS-SVD was made for memory-mapped peripherals of a microcontroller. The
:ref:`mapping table <description-files-svd-map>` shows which SVD element stands for each item
of this manual.

.. _description-files-svd-map:

.. list-table::
   :header-rows: 1
   :widths: 30 20 26 24

   * - Item of this manual
     - Example
     - SVD element
     - Names in the SVD file
   * - :ref:`Address region <reference-map>`
     - :doc:`GLOBAL <reference/regions/global>`
     - peripheral
     - region name
   * - Register with an index
     - :reg:`PORT_CTRL`
     - register array
     - register name
   * - :ref:`Register wider than 32 bits <access-wide>`
     - :reg:`ACL_ACT`
     - cluster of 32-bit registers
     - ``W0`` to ``W2``
   * - Field that crosses a word boundary
     - :field:`VLAN_CTRL.FID`
     - two fields
     - suffix ``_LO`` or ``_HI``
   * - Layout of :reg:`ACL_KEY`
     - :reg:`ACL_KEY`
     - alternate register
     - register name with layout name
   * - :ref:`Port counters <reference-counters>`
     - :counter:`RX_BROADCAST`
     - cluster per port
     - counter name

The addresses are register addresses of the switch as used in :ref:`access-smi`, not memory
addresses of the host. Both files validate against the
:download:`CMSIS-SVD 1.3 schema <../tools/schema/CMSIS-SVD.xsd>`.

.. _description-files-yaml:

Structure of the YAML source
----------------------------

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Key
     - Contents
   * - ``device``
     - Name and word sizes
   * - ``sources``
     - Repository and commit of each source
   * - ``linux_functions``
     - File and line of each function of the Linux driver
   * - ``chips``
     - Parts with their identification values
   * - ``regions``
     - Address regions
   * - ``blocks``
     - Function blocks
   * - ``constants``
     - Named numbers
   * - ``enums``
     - Value lists shared by several fields
   * - ``registers``
     - Registers with their fields
   * - ``counters``
     - Port counters with their offsets

.. _description-files-regenerate:

Regenerating
------------

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - File
     - Purpose
   * - :download:`extract.py <../tools/extract.py>`
     - Writes the two YAML files
   * - :download:`overlay.yaml <../tools/overlay.yaml>`
     - Holds the hand-written descriptions
   * - :download:`model.py <../tools/model.py>`
     - Loads the YAML source for the other tools
   * - :download:`generate.py <../tools/generate.py>`
     - Runs the five ``gen_`` writers of the next rows
   * - :download:`gen_c.py <../tools/gen_c.py>`
     - Writes the C header
   * - :download:`gen_rust.py <../tools/gen_rust.py>`
     - Writes the Rust module
   * - :download:`gen_py.py <../tools/gen_py.py>`
     - Writes the MicroPython module
   * - :download:`gen_svd.py <../tools/gen_svd.py>`
     - Writes the SVD files
   * - :download:`gen_rdl.py <../tools/gen_rdl.py>`
     - Writes the SystemRDL files
   * - :download:`gen_docs.py <../tools/gen_docs.py>`
     - Writes the reference pages of this manual during the Sphinx build
   * - :download:`diagrams.py <../tools/diagrams.py>`
     - Draws diagrams as SVG
   * - :download:`guide_diagrams.py <../tools/guide_diagrams.py>`
     - Holds the content of the guide's diagrams
   * - :download:`yt921x_sphinx.py <../tools/yt921x_sphinx.py>`
     - Provides the Sphinx roles and directives of this manual
   * - :download:`test_generated.py <../tests/test_generated.py>`
     - Checks every generated file against the description

:download:`extract.py <../tools/extract.py>` reads the headers and the code of the
:ref:`Linux driver <sources-list>`, the table list of the :ref:`vendor SDK <sources-list>`
and :download:`overlay.yaml <../tools/overlay.yaml>`. It writes
:download:`yt921x.yaml <../yt921x.yaml>` and
:download:`sdk-tables.yaml <../sdk-tables.yaml>`.

.. _description-files-commands:

.. code-block:: sh

   # after editing tools/overlay.yaml, or to follow another commit of the Linux driver
   python3 tools/extract.py --linux <driver directory> --linux-sha <commit> \
       --sdk <sdk checkout> --sdk-sha <commit>
   python3 tools/generate.py
   make check

To change a description, edit :download:`overlay.yaml <../tools/overlay.yaml>` and run the
:ref:`three commands <description-files-commands>`. Never edit a generated file.
