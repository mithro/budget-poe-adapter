.. _description-files:

Register description files
==========================

The register map exists in three machine-readable forms. One of them is the source of this
manual and of the :doc:`bindings <bindings>`; the other two are generated for tools that read
standard formats.

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - File
     - Format
     - Use
   * - :download:`yt921x.yaml <../yt921x.yaml>`
     - YAML
     - The source: every register, field, value, counter, constant and part, with
       descriptions and references to where each came from
   * - :download:`sdk-tables.yaml <../sdk-tables.yaml>`
     - YAML
     - The register tables of the vendor SDK, names and bit positions only
   * - :download:`yt9215.svd <../svd/yt9215.svd>`
     - CMSIS-SVD
     - YT9215 family, for register viewers and code generators such as ``svd2rust``
   * - :download:`yt9218.svd <../svd/yt9218.svd>`
     - CMSIS-SVD
     - YT9218 family
   * - :download:`yt9215.rdl <../rdl/yt9215.rdl>`
     - SystemRDL 2.0
     - YT9215 family, for the SystemRDL tool chain
   * - :download:`yt9218.rdl <../rdl/yt9218.rdl>`
     - SystemRDL 2.0
     - YT9218 family

There is one SVD and one SystemRDL file per family because :reg:`IO_LEVEL` has a different
layout in each.

.. _description-files-svd:

Notes on the SVD files
----------------------

CMSIS-SVD was made for memory-mapped peripherals of a microcontroller. The files use it as
follows:

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Item of this manual
     - In the SVD file
   * - Address region (:ref:`reference-map`)
     - A peripheral whose base address is the region base
   * - Register with an index
     - A register array (``dim``)
   * - Register wider than 32 bits
     - A cluster with one 32-bit register per word, named ``W0``, ``W1`` and ``W2``
   * - Field that crosses a word boundary
     - Two fields with the suffixes ``_LO`` and ``_HI``
   * - Layout of :reg:`ACL_KEY`
     - An alternate register per layout
   * - Port counters
     - A cluster per port with one register per counter

The addresses are register addresses of the switch as used in :ref:`access-smi`, not memory
addresses of the host. Both files validate against the CMSIS-SVD 1.3 schema.

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
     - Repositories and commits the description was extracted from
   * - ``chips``
     - Parts with their identification values and port lists
   * - ``regions``
     - Address regions
   * - ``blocks``
     - Function blocks
   * - ``constants``
     - Named numbers
   * - ``enums``
     - Value lists shared by several fields
   * - ``registers``
     - Registers with address, index ranges, size, fields and layouts
   * - ``counters``
     - Port counters with their offsets

.. _description-files-regenerate:

Regenerating
------------

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Tool
     - Purpose
   * - :download:`extract.py <../tools/extract.py>`
     - Builds ``yt921x.yaml`` and ``sdk-tables.yaml`` from a checkout of the Linux driver, a
       checkout of the vendor SDK and the hand-written descriptions
   * - :download:`overlay.yaml <../tools/overlay.yaml>`
     - The hand-written part: titles, descriptions, index ranges, parts and corrections
   * - :download:`generate.py <../tools/generate.py>`
     - Writes the bindings, the SVD and the SystemRDL files from ``yt921x.yaml``
   * - :download:`gen_docs.py <../tools/gen_docs.py>`
     - Writes the reference pages of this manual during the Sphinx build
   * - :download:`diagrams.py <../tools/diagrams.py>`
     - Draws the diagrams as SVG
   * - :download:`yt921x_sphinx.py <../tools/yt921x_sphinx.py>`
     - Sphinx extension: the roles and directives of this manual
   * - :download:`test_generated.py <../tests/test_generated.py>`
     - Checks every generated file against the description

.. code-block:: sh

   # after editing tools/overlay.yaml, or to follow a newer Linux driver
   python3 tools/extract.py --linux <linux checkout> --sdk <sdk checkout>
   python3 tools/generate.py
   make check

To change a description, edit ``tools/overlay.yaml`` and run the three commands; never edit a
generated file.
