# YT921x switch: programmer's guide, register description and bindings

Everything needed to write a driver for the Motorcomm YT921x Gigabit Ethernet switches
(YT9215S, YT9215SC, YT9215SCH, YT9215RB, YT9214NB, YT9213NB, YT9218N, YT9218MB): a manual, a
machine-readable register description, and register definitions with a small access layer
for C, Rust, MicroPython and Zephyr.

The vendor publishes no register documentation. The content is derived from the Linux
driver and the vendor SDK; [`docs/sources.rst`](docs/sources.rst) explains what comes from
where and how far it can be trusted. Nothing here has been run on a real YT921x.

## Manual

The manual is a Sphinx project and reads best when built (`make docs`, or on Read the Docs with the [`.readthedocs.yaml`](../../.readthedocs.yaml) of this repository).
The pages are also readable as source:

| Page | Topic |
| --- | --- |
| [`docs/index.rst`](docs/index.rst) | Start page |
| [`docs/overview.rst`](docs/overview.rst) | What the chip contains and what a driver has to do |
| [`docs/access.rst`](docs/access.rst) | Register access over MDIO, with timing |
| [`docs/bringup.rst`](docs/bringup.rst) | Reset, identification, function enables |
| [`docs/ports.rst`](docs/ports.rst) | Port MACs, SerDes and xMII ports, frame size |
| [`docs/phy.rst`](docs/phy.rst) | PHY access through the MDIO masters of the switch |
| [`docs/cpu-tag.rst`](docs/cpu-tag.rst) | CPU port and the 8-byte frame tag |
| [`docs/forwarding.rst`](docs/forwarding.rst) | Port isolation, spanning tree, learning, flooding |
| [`docs/vlan.rst`](docs/vlan.rst) | VLANs |
| [`docs/fdb.rst`](docs/fdb.rst) | Forwarding database |
| [`docs/mib.rst`](docs/mib.rst) | Port counters |
| [`docs/qos.rst`](docs/qos.rst) | Priorities |
| [`docs/lag.rst`](docs/lag.rst) | Link aggregation |
| [`docs/acl.rst`](docs/acl.rst) | Access control list |
| [`docs/rate.rst`](docs/rate.rst) | Meters and shapers |
| [`docs/mirror.rst`](docs/mirror.rst) | Port mirroring |
| [`docs/leds.rst`](docs/leds.rst) | LEDs |
| [`docs/bindings.rst`](docs/bindings.rst) | The code bindings |
| [`docs/description-files.rst`](docs/description-files.rst) | The register description files and how to regenerate them |
| [`docs/sources.rst`](docs/sources.rst) | Sources and confidence |

The register reference (one section per register with address, bit diagram, field table and
sources) is generated during the build by [`tools/gen_docs.py`](tools/gen_docs.py).

## Register description

| File | Format |
| --- | --- |
| [`yt921x.yaml`](yt921x.yaml) | The source of everything else: 101 registers, 467 fields |
| [`sdk-tables.yaml`](sdk-tables.yaml) | All 237 register tables of the vendor SDK, names and bits only |
| [`svd/yt9215.svd`](svd/yt9215.svd) | CMSIS-SVD, YT9215 family |
| [`svd/yt9218.svd`](svd/yt9218.svd) | CMSIS-SVD, YT9218 family |
| [`rdl/yt9215.rdl`](rdl/yt9215.rdl) | SystemRDL, YT9215 family |
| [`rdl/yt9218.rdl`](rdl/yt9218.rdl) | SystemRDL, YT9218 family |

## Bindings

| Environment | Register definitions | Access layer | Example |
| --- | --- | --- | --- |
| C | [`yt921x_regs.h`](bindings/c/yt921x_regs.h) | [`yt921x.c`](bindings/c/yt921x.c) | [`guide.c`](bindings/c/examples/guide.c) |
| Rust | [`regs.rs`](bindings/rust/src/regs.rs) | [`lib.rs`](bindings/rust/src/lib.rs) | [`guide.rs`](bindings/rust/examples/guide.rs) |
| MicroPython | [`yt921x_regs.py`](bindings/micropython/yt921x_regs.py) | [`yt921x.py`](bindings/micropython/yt921x.py) | [`guide.py`](bindings/micropython/examples/guide.py) |
| Zephyr | [`yt921x_regs.h`](bindings/c/yt921x_regs.h) | [`yt921x_zephyr.c`](bindings/zephyr/drivers/yt921x_zephyr.c) | [`main.c`](bindings/zephyr/samples/identify/src/main.c) |

## Working on it

[`Makefile`](Makefile) has the commands: `make generate` rewrites the generated files from
[`yt921x.yaml`](yt921x.yaml), `make check` runs every test, `make docs` builds the manual.
Descriptions are edited in [`tools/overlay.yaml`](tools/overlay.yaml) and merged with the
upstream sources by [`tools/extract.py`](tools/extract.py).
