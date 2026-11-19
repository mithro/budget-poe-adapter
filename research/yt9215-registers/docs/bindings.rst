.. _bindings:

Code bindings
=============

The register map is available as source code for four environments. The register
definitions of C, Rust and MicroPython are generated from
:download:`yt921x.yaml <../yt921x.yaml>`, the description that this manual is generated from
and that :doc:`description-files` explains. Zephyr uses the C definitions. A small
hand-written access layer per environment implements the procedures of :doc:`access`,
:doc:`bringup`, :doc:`phy` and :doc:`mib`. Every C, Rust and Python file of the bindings carries an
`Apache-2.0 <https://www.apache.org/licenses/LICENSE-2.0>`__ licence identifier.

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
     - :download:`yt921x_regs.h <../bindings/c/yt921x_regs.h>`
     - :download:`yt921x_zephyr.c <../bindings/zephyr/drivers/yt921x_zephyr.c>`

.. _bindings-api:

What the access layer does
--------------------------

The same operations exist in every language. Each C function of the :ref:`operation table <bindings-api-table>` is a link to
:download:`yt921x.h <../bindings/c/yt921x.h>`, which declares it.

.. _bindings-api-table:

.. list-table::
   :header-rows: 1
   :widths: 30 26 44

   * - Operation
     - C function
     - Procedure
   * - Read a register
     - :download:`yt921x_reg_read() <../bindings/c/yt921x.h>`
     - :ref:`access-smi`
   * - Write a register
     - :download:`yt921x_reg_write() <../bindings/c/yt921x.h>`
     - :ref:`access-smi`
   * - Change some bits of a register
     - :download:`yt921x_reg_update() <../bindings/c/yt921x.h>`
     - :ref:`access-smi`
   * - Read a wide register
     - :download:`yt921x_reg_read_words() <../bindings/c/yt921x.h>`
     - :ref:`access-wide`
   * - Write a wide register
     - :download:`yt921x_reg_write_words() <../bindings/c/yt921x.h>`
     - :ref:`access-wide`
   * - Wait for a bit pattern
     - :download:`yt921x_reg_wait() <../bindings/c/yt921x.h>`
     - :ref:`access-wait`
   * - Reset the switch
     - :download:`yt921x_reset() <../bindings/c/yt921x.h>`
     - :ref:`bringup-reset`
   * - Read a configuration byte
     - :download:`yt921x_edata_read() <../bindings/c/yt921x.h>`
     - :ref:`bringup-identify`
   * - Identify the part
     - :download:`yt921x_identify() <../bindings/c/yt921x.h>`
     - :ref:`bringup-identify`
   * - Read a PHY register
     - :download:`yt921x_phy_read() <../bindings/c/yt921x.h>`
     - :ref:`phy-mbus`
   * - Write a PHY register
     - :download:`yt921x_phy_write() <../bindings/c/yt921x.h>`
     - :ref:`phy-mbus`
   * - Read a port counter
     - :download:`yt921x_mib_read() <../bindings/c/yt921x.h>`
     - :ref:`mib-counters`

The Rust and MicroPython layers use the same names without the ``yt921x_`` prefix. In Rust
they are methods of the type :download:`Yt921x <../bindings/rust/src/lib.rs>`, in MicroPython
methods of the class :download:`YT921x <../bindings/micropython/yt921x.py>`.

.. _bindings-naming:

Names
-----

A register or field has one name in this manual, and every binding derives its symbols from
that name in a fixed way. The examples are for :reg:`PORT_CTRL`, its field
:field:`PORT_CTRL.SPEED`, the array field :field:`STP.PORT`, the wide field
:field:`VLAN_CTRL.FID`, the register :reg:`RST`, the value :val:`FDB_OP.OP.ADD`, the shared value
:val:`speed.V1000`, the counter :counter:`RX_BROADCAST` and the constant :const:`PORT_NUM`.

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

A value name that would start with a digit has a ``V`` in front, as in
:val:`speed.V1000`. Values are plain numbers. The helpers of the three register definition
files shift them into place.

.. list-table::
   :header-rows: 1
   :widths: 30 26 22 22

   * - Helper
     - C
     - Rust
     - MicroPython
   * - Extract a field
     - :download:`YT921X_FGET(val, F) <../bindings/c/yt921x_regs.h>`
     - :download:`F.get(val) <../bindings/rust/src/regs.rs>`
     - :download:`fget(val, mask, shift) <../bindings/micropython/yt921x_regs.py>`
   * - Place a value in a field
     - :download:`YT921X_FPREP(F, x) <../bindings/c/yt921x_regs.h>`
     - :download:`F.prep(x) <../bindings/rust/src/regs.rs>`
     - :download:`fprep(mask, shift, x) <../bindings/micropython/yt921x_regs.py>`
   * - Extract an array element
     - :download:`YT921X_FGET_AT(val, F, i) <../bindings/c/yt921x_regs.h>`
     - :download:`f(i).get(val) <../bindings/rust/src/regs.rs>`
     - :download:`fget(val, F_M(i), F_S(i)) <../bindings/micropython/yt921x_regs.py>`
   * - Read a wide field
     - :download:`yt921x_bits_get() <../bindings/c/yt921x_regs.h>`
     - :download:`F.get_words() <../bindings/rust/src/regs.rs>`
     - :download:`bits_get() <../bindings/micropython/yt921x_regs.py>`
   * - Write a wide field
     - :download:`yt921x_bits_set() <../bindings/c/yt921x_regs.h>`
     - :download:`F.set_words() <../bindings/rust/src/regs.rs>`
     - :download:`bits_set() <../bindings/micropython/yt921x_regs.py>`

.. _bindings-c:

C
-

Portable `C99 <https://en.wikipedia.org/wiki/C99>`__ without dependencies. The caller supplies three functions in the structure
:download:`struct yt921x_bus <../bindings/c/yt921x.h>`: `clause 22 <https://en.wikipedia.org/wiki/Management_Data_Input/Output>`__ MDIO read,
MDIO write and a delay.

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
traits :download:`Mdio <../bindings/rust/src/lib.rs>` and
:download:`Delay <../bindings/rust/src/lib.rs>`.

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
     - Bring-up example
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

Two modules that also run under CPython. The bus is any object with the methods
``read(phy, reg)`` and ``write(phy, reg, value)``. The class
:download:`BitBangMDIO <../bindings/micropython/yt921x.py>` provides one on two
``machine.Pin`` objects.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - File
     - Contents
   * - :download:`yt921x_regs.py <../bindings/micropython/yt921x_regs.py>`
     - Generated register definitions
   * - :download:`yt921x.py <../bindings/micropython/yt921x.py>`
     - Access layer
   * - :download:`guide.py <../bindings/micropython/examples/guide.py>`
     - The examples of this manual
   * - :download:`mock_switch.py <../bindings/micropython/tests/mock_switch.py>`
     - Software model of the switch
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
     - Build rules
   * - :download:`Kconfig <../bindings/zephyr/Kconfig>`
     - Configuration options
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

The module is the directory
`bindings/zephyr <https://github.com/mithro/budget-poe-adapter/tree/main/research/yt9215-registers/bindings/zephyr>`__.
Add it to a build by passing its path in the CMake variable ``ZEPHYR_EXTRA_MODULES``, or list
it in the west manifest. The option
:download:`CONFIG_YT921X <../bindings/zephyr/Kconfig>` enables the driver.

.. _bindings-tests:

How the code is checked
-----------------------

.. list-table::
   :header-rows: 1
   :widths: 22 78

   * - Binding
     - Check
   * - C
     - Compiled with ``gcc -std=c99 -Wall -Wextra -Werror -pedantic``
   * - C
     - Access layer run against the software model
   * - C
     - Every example run against the software model
   * - Rust
     - ``cargo test`` on the host
   * - Rust
     - Built for ``thumbv7em-none-eabihf``
   * - MicroPython
     - Run under CPython against the software model
   * - All
     - Generated values compared with the description file

None of the code has been run against a YT921x. The software model is
:download:`mock_switch.h <../bindings/c/tests/mock_switch.h>` for C,
:download:`mock.rs <../bindings/rust/tests/mock.rs>` for Rust and
:download:`mock_switch.py <../bindings/micropython/tests/mock_switch.py>` for MicroPython.
Each implements the behaviour that this manual describes, so the tests show that code and
manual agree with each other, not that both are right. The description file
is :download:`yt921x.yaml <../yt921x.yaml>`. :download:`Makefile <../Makefile>` runs all
checks with the command ``make check``. Where the tool ``mpy-cross`` is installed, the command
also compiles the MicroPython modules with it. No check builds the Zephyr module.
