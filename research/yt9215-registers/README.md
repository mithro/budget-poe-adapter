# YT921x switch: programmer's guide, register description and bindings

Material for writing a driver for the Motorcomm YT921x Gigabit Ethernet switches
of the YT9215 and YT9218 families: a manual, a
machine-readable register description, and register definitions with a small access layer
for C, Rust, MicroPython and Zephyr.

The vendor publishes no register documentation. The content is derived from the
[Linux driver](https://github.com/torvalds/linux/tree/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm)
and the [vendor SDK](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/tree/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e).
[`docs/sources.rst`](docs/sources.rst) lists the sources and the evidence behind each
register. No part of the manual or the code has been run on a YT921x.

## Manual

The manual is a Sphinx project and reads best when built. `make docs` builds it, and
[Read the Docs](https://about.readthedocs.com/) builds it with the [`.readthedocs.yaml`](../../.readthedocs.yaml) of this
repository.
[WaveDrom](https://wavedrom.com/) draws the register and timing diagrams during the build, so the build needs
[Node.js](https://nodejs.org/) in addition to the Python packages of [`docs/requirements.txt`](../../docs/requirements.txt).
The pages are also readable as source:

| Page | Topic |
| --- | --- |
| [`docs/index.rst`](docs/index.rst) | Start page |
| [`docs/overview.rst`](docs/overview.rst) | Chip overview |
| [`docs/access.rst`](docs/access.rst) | Register access over MDIO |
| [`docs/bringup.rst`](docs/bringup.rst) | Reset |
| [`docs/ports.rst`](docs/ports.rst) | Port configuration |
| [`docs/phy.rst`](docs/phy.rst) | PHY access through the MDIO masters of the switch |
| [`docs/cpu-tag.rst`](docs/cpu-tag.rst) | CPU port |
| [`docs/forwarding.rst`](docs/forwarding.rst) | Forwarding between ports |
| [`docs/vlan.rst`](docs/vlan.rst) | VLANs |
| [`docs/fdb.rst`](docs/fdb.rst) | Forwarding database |
| [`docs/mib.rst`](docs/mib.rst) | Port counters |
| [`docs/qos.rst`](docs/qos.rst) | Priorities |
| [`docs/lag.rst`](docs/lag.rst) | Link aggregation |
| [`docs/acl.rst`](docs/acl.rst) | Access control list |
| [`docs/rate.rst`](docs/rate.rst) | Rate limiting |
| [`docs/mirror.rst`](docs/mirror.rst) | Port mirroring |
| [`docs/leds.rst`](docs/leds.rst) | LEDs |
| [`docs/bindings.rst`](docs/bindings.rst) | The code bindings |
| [`docs/description-files.rst`](docs/description-files.rst) | Register description files |
| [`docs/sources.rst`](docs/sources.rst) | Sources and evidence |

The register reference (one section per register with address, bit diagram, field table and
sources) is generated during the build by [`tools/gen_docs.py`](tools/gen_docs.py).

## Register description

| File | Format | Content |
| --- | --- | --- |
| [`yt921x.yaml`](yt921x.yaml) | YAML | 101 registers with 467 fields |
| [`sdk-tables.yaml`](sdk-tables.yaml) | YAML | 237 register tables of the [vendor SDK](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/tree/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk) |
| [`svd/yt9215.svd`](svd/yt9215.svd) | [CMSIS-SVD](https://open-cmsis-pack.github.io/svd-spec/main/index.html) | YT9215 family |
| [`svd/yt9218.svd`](svd/yt9218.svd) | [CMSIS-SVD](https://open-cmsis-pack.github.io/svd-spec/main/index.html) | YT9218 family |
| [`rdl/yt9215.rdl`](rdl/yt9215.rdl) | [SystemRDL](https://www.accellera.org/downloads/standards/systemrdl) | YT9215 family |
| [`rdl/yt9218.rdl`](rdl/yt9218.rdl) | [SystemRDL](https://www.accellera.org/downloads/standards/systemrdl) | YT9218 family |

[`yt921x.yaml`](yt921x.yaml) is the source that the SVD files, the SystemRDL files and the bindings are generated from.
[`sdk-tables.yaml`](sdk-tables.yaml) holds names and bit positions only.

## Bindings

| Environment | Register definitions | Access layer | Example |
| --- | --- | --- | --- |
| C | [`yt921x_regs.h`](bindings/c/yt921x_regs.h) | [`yt921x.c`](bindings/c/yt921x.c) | [`guide.c`](bindings/c/examples/guide.c) |
| Rust | [`regs.rs`](bindings/rust/src/regs.rs) | [`lib.rs`](bindings/rust/src/lib.rs) | [`guide.rs`](bindings/rust/examples/guide.rs) |
| MicroPython | [`yt921x_regs.py`](bindings/micropython/yt921x_regs.py) | [`yt921x.py`](bindings/micropython/yt921x.py) | [`guide.py`](bindings/micropython/examples/guide.py) |
| Zephyr | [`yt921x_regs.h`](bindings/c/yt921x_regs.h) | [`yt921x_zephyr.c`](bindings/zephyr/drivers/yt921x_zephyr.c) | [`main.c`](bindings/zephyr/samples/identify/src/main.c) |

## Working on it

[`Makefile`](Makefile) has the commands.

| Command | Effect |
| --- | --- |
| `make generate` | Rewrites the generated files from [`yt921x.yaml`](yt921x.yaml) |
| `make check` | Runs every test |
| `make docs` | Builds the manual |

Descriptions are edited in [`tools/overlay.yaml`](tools/overlay.yaml).
[`tools/extract.py`](tools/extract.py) merges them with the
[Linux driver](https://github.com/torvalds/linux/tree/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm)
and the
[vendor SDK](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/tree/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e).
