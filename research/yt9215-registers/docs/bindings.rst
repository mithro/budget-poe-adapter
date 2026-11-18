.. _bindings:

Code bindings
=============

The register map is available as source code for four environments. In each, one file of
register definitions is generated from the same description as this manual
(:doc:`description-files`), and a small hand-written access layer implements the procedures of
:doc:`access`, :doc:`bringup`, :doc:`phy` and :doc:`mib`. All code is under the Apache-2.0
licence.

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Environment
     - Register definitions
     - Access layer
   * - :ref:`C <bindings-c>`
     - :download:`yt921x_regs.h <../bindings/c/yt921x_regs.h>`
     - :download:`yt921x.c <../bindings/c/yt921x.c>`
   * - :ref:`Rust <bindings-rust>`
     - :download:`regs.rs <../bindings/rust/src/regs.rs>`
     - :download:`lib.rs <../bindings/rust/src/lib.rs>`
   * - :ref:`MicroPython <bindings-micropython>`
     - :download:`yt921x_regs.py <../bindings/micropython/yt921x_regs.py>`
     - :download:`yt921x.py <../bindings/micropython/yt921x.py>`
   * - :ref:`Zephyr <bindings-zephyr>`
     - The C header
     - :download:`yt921x_zephyr.c <../bindings/zephyr/drivers/yt921x_zephyr.c>`

.. _bindings-api:

What the access layer does
--------------------------

The same operations exist in every language.

.. list-table::
   :header-rows: 1
   :widths: 30 26 44

   * - Operation
     - C function
     - Procedure
   * - Read a register
     - ``yt921x_reg_read()``
     - :ref:`access-smi`
   * - Write a register
     - ``yt921x_reg_write()``
     - :ref:`access-smi`
   * - Change some bits of a register
     - ``yt921x_reg_update()``
     - :ref:`access-smi`
   * - Read a wide register
     - ``yt921x_reg_read_words()``
     - :ref:`access-wide`
   * - Write a wide register
     - ``yt921x_reg_write_words()``
     - :ref:`access-wide`
   * - Wait for a bit pattern
     - ``yt921x_reg_wait()``
     - :ref:`access-wait`
   * - Reset the switch
     - ``yt921x_reset()``
     - :ref:`bringup-reset`
   * - Read a configuration byte
     - ``yt921x_edata_read()``
     - :ref:`bringup-identify`
   * - Identify the part
     - ``yt921x_identify()``
     - :ref:`bringup-identify`
   * - Read a PHY register
     - ``yt921x_phy_read()``
     - :ref:`phy-mbus`
   * - Write a PHY register
     - ``yt921x_phy_write()``
     - :ref:`phy-mbus`
   * - Read a port counter
     - ``yt921x_mib_read()``
     - :ref:`mib-counters`

The Rust and MicroPython layers use the same names without the ``yt921x_`` prefix, as methods
of ``Yt921x`` and ``YT921x``.

.. _bindings-naming:

Names
-----

A register or field has one name in this manual, and every binding derives its symbols from
that name in a fixed way. The examples are for :reg:`PORT_CTRL`, its field
:field:`PORT_CTRL.SPEED`, the array field :field:`STP.PORT` and the wide field
:field:`VLAN_CTRL.FID`.

.. list-table::
   :header-rows: 1
   :widths: 22 28 24 26

   * - Item
     - C
     - Rust
     - MicroPython
   * - Register address
     - ``YT921X_PORT_CTRL(port)``
     - ``regs::port_ctrl(port)``
     - ``PORT_CTRL(port)``
   * - Register without index
     - ``YT921X_RST``
     - ``regs::RST``
     - ``RST``
   * - Field mask
     - ``YT921X_PORT_CTRL_SPEED_M``
     - ``regs::PORT_CTRL_SPEED.mask()``
     - ``PORT_CTRL_SPEED_M``
   * - Field shift
     - ``YT921X_PORT_CTRL_SPEED_S``
     - ``regs::PORT_CTRL_SPEED.shift()``
     - ``PORT_CTRL_SPEED_S``
   * - Element of an array field
     - ``YT921X_STP_PORT_M(port)``
     - ``regs::stp_port(port)``
     - ``STP_PORT_M(port)``
   * - Position of a wide field
     - ``YT921X_VLAN_CTRL_FID_LSB``
     - ``regs::VLAN_CTRL_FID``
     - ``VLAN_CTRL_FID_LSB``
   * - Value of a field
     - ``YT921X_FDB_OP_OP_ADD``
     - ``regs::FDB_OP_OP_ADD``
     - ``FDB_OP_OP_ADD``
   * - Shared value
     - ``YT921X_SPEED_V1000``
     - ``regs::SPEED_V1000``
     - ``SPEED_V1000``
   * - Counter offset
     - ``YT921X_MIB_RX_BROADCAST``
     - ``regs::MIB_RX_BROADCAST``
     - ``MIB_RX_BROADCAST``
   * - Constant
     - ``YT921X_PORT_NUM``
     - ``regs::PORT_NUM``
     - ``PORT_NUM``

A value name that would start with a digit has a ``V`` in front, as in ``V1000``. Values are
plain numbers; shift them into place with the helpers below.

.. list-table::
   :header-rows: 1
   :widths: 30 26 22 22

   * - Helper
     - C
     - Rust
     - MicroPython
   * - Extract a field
     - ``YT921X_FGET(val, F)``
     - ``F.get(val)``
     - ``fget(val, mask, shift)``
   * - Place a value in a field
     - ``YT921X_FPREP(F, x)``
     - ``F.prep(x)``
     - ``fprep(mask, shift, x)``
   * - Extract an array element
     - ``YT921X_FGET_AT(val, F, i)``
     - ``f(i).get(val)``
     - ``fget(val, F_M(i), F_S(i))``
   * - Read a wide field
     - ``yt921x_bits_get()``
     - ``F.get_words()``
     - ``bits_get()``
   * - Write a wide field
     - ``yt921x_bits_set()``
     - ``F.set_words()``
     - ``bits_set()``

.. _bindings-c:

C
-

Portable C99 without dependencies. The caller supplies three functions in a
``struct yt921x_bus``: clause 22 MDIO read, MDIO write and a delay.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - File
     - Contents
   * - :download:`yt921x_regs.h <../bindings/c/yt921x_regs.h>`
     - Generated register definitions
   * - :download:`yt921x.h <../bindings/c/yt921x.h>`
     - Access layer interface
   * - :download:`yt921x.c <../bindings/c/yt921x.c>`
     - Access layer
   * - :download:`guide.c <../bindings/c/examples/guide.c>`
     - The examples of this manual
   * - :download:`guide.h <../bindings/c/examples/guide.h>`
     - Declarations of the examples
   * - :download:`mock_switch.h <../bindings/c/tests/mock_switch.h>`
     - Software model of the switch for tests
   * - :download:`test_yt921x.c <../bindings/c/tests/test_yt921x.c>`
     - Tests of the access layer
   * - :download:`test_guide.c <../bindings/c/tests/test_guide.c>`
     - Tests of the examples

.. literalinclude:: ../bindings/c/yt921x.h
   :language: c
   :start-at: /** Host functions the library calls.
   :end-before: /** Result of yt921x_identify(). */
   :caption: The bus interface, from :download:`yt921x.h <../bindings/c/yt921x.h>`

.. _bindings-rust:

Rust
----

A ``no_std`` crate without dependencies and without ``unsafe``. The board implements the
traits ``Mdio`` and ``Delay``.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - File
     - Contents
   * - :download:`Cargo.toml <../bindings/rust/Cargo.toml>`
     - Crate manifest
   * - :download:`regs.rs <../bindings/rust/src/regs.rs>`
     - Generated register definitions
   * - :download:`lib.rs <../bindings/rust/src/lib.rs>`
     - Access layer
   * - :download:`guide.rs <../bindings/rust/examples/guide.rs>`
     - Example: bus traits and bring-up
   * - :download:`mock.rs <../bindings/rust/tests/mock.rs>`
     - Tests against a software model of the switch

.. literalinclude:: ../bindings/rust/examples/guide.rs
   :language: rust
   :start-after: // [bringup]
   :end-before: // [bringup end]
   :caption: Bring-up, from :download:`guide.rs <../bindings/rust/examples/guide.rs>`

.. _bindings-micropython:

MicroPython
-----------

Two modules that also run under CPython. The bus is any object with ``read(phy, reg)`` and
``write(phy, reg, value)``; ``BitBangMDIO`` provides one on two ``machine.Pin`` objects.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - File
     - Contents
   * - :download:`yt921x_regs.py <../bindings/micropython/yt921x_regs.py>`
     - Generated register definitions
   * - :download:`yt921x.py <../bindings/micropython/yt921x.py>`
     - Access layer and bit-banged MDIO
   * - :download:`guide.py <../bindings/micropython/examples/guide.py>`
     - The examples of this manual
   * - :download:`mock_switch.py <../bindings/micropython/tests/mock_switch.py>`
     - Software model of the switch and of two MDIO pins
   * - :download:`test_yt921x.py <../bindings/micropython/tests/test_yt921x.py>`
     - Tests of the access layer
   * - :download:`test_guide.py <../bindings/micropython/tests/test_guide.py>`
     - Tests of the examples

.. literalinclude:: ../bindings/micropython/examples/guide.py
   :language: python
   :start-after: # [bus]
   :end-before: # [bus end]
   :caption: Opening the switch on two pins, from
             :download:`guide.py <../bindings/micropython/examples/guide.py>`

The register module is large. On a small board, freeze it into the firmware or compile it
with ``mpy-cross``; the constants are declared with ``const()`` so that they cost no RAM.

.. _bindings-zephyr:

Zephyr
------

A Zephyr module that wraps the C binding in a device driver: the switch is a devicetree node
on an MDIO bus, is reset and identified at init, and hands out the C access handle under a
lock.

.. list-table::
   :header-rows: 1
   :widths: 44 56

   * - File
     - Contents
   * - :download:`module.yml <../bindings/zephyr/zephyr/module.yml>`
     - Module description
   * - :download:`CMakeLists.txt <../bindings/zephyr/CMakeLists.txt>`
     - Build rules; compiles the C binding
   * - :download:`Kconfig <../bindings/zephyr/Kconfig>`
     - ``CONFIG_YT921X`` and the init priority
   * - :download:`motorcomm,yt921x.yaml <../bindings/zephyr/dts/bindings/ethernet/motorcomm,yt921x.yaml>`
     - Devicetree binding
   * - :download:`yt921x_zephyr.h <../bindings/zephyr/include/yt921x/yt921x_zephyr.h>`
     - Driver interface
   * - :download:`yt921x_zephyr.c <../bindings/zephyr/drivers/yt921x_zephyr.c>`
     - Driver
   * - :download:`main.c <../bindings/zephyr/samples/identify/src/main.c>`
     - Sample application
   * - :download:`native_sim.overlay <../bindings/zephyr/samples/identify/boards/native_sim.overlay>`
     - Sample devicetree overlay

.. literalinclude:: ../bindings/zephyr/samples/identify/boards/native_sim.overlay
   :language: devicetree
   :start-at: / {
   :caption: The switch on a bit-banged MDIO bus, from
             :download:`native_sim.overlay <../bindings/zephyr/samples/identify/boards/native_sim.overlay>`

.. literalinclude:: ../bindings/zephyr/samples/identify/src/main.c
   :language: c
   :start-at: static const struct device
   :caption: Using the device, from
             :download:`main.c <../bindings/zephyr/samples/identify/src/main.c>`

Add the module to a build with ``-DZEPHYR_EXTRA_MODULES=<path to bindings/zephyr>`` or list it
in the west manifest.

.. _bindings-tests:

How the code is checked
-----------------------

.. list-table::
   :header-rows: 1
   :widths: 22 78

   * - Binding
     - Check
   * - C
     - Compiled with ``gcc -std=c99 -Wall -Wextra -Werror -pedantic``; the access layer and
       every example run against the software model
   * - Rust
     - ``cargo test`` on the host; built for ``thumbv7em-none-eabihf``
   * - MicroPython
     - Run under CPython against the software model, including the bit-banged bus; compiled
       with ``mpy-cross``
   * - Zephyr
     - Sample built for ``native_sim`` and run; it reports that no switch answers
   * - All
     - Every generated address and field position is compared with the description file

None of the code has been run against a real YT921x by this project yet. The software model
implements this manual's understanding of the chip, so the tests show that code and manual
agree with each other, not that both are right. :download:`Makefile <../Makefile>` runs all
checks.
