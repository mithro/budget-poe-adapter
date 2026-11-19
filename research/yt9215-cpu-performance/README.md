# Benchmark for the YT9215 CPU

This folder holds the workload model behind
[Speed and resources of the YT9215 CPU](../yt9215-cpu-performance.md). It measures how
many instructions and cycles the time-critical firmware of the adapter needs on an
RV32E core without a multiplier. It runs in an emulator on a PC. Nothing here runs on
a YT9215.

| File | Contents |
| --- | --- |
| [`pd_lldp.c`](pd_lldp.c) | USB-PD transmit, receive and GoodCRC reply by GPIO; CRC-32; LLDP parse and build |
| [`rv32e_emu.py`](rv32e_emu.py) | RV32E emulator that counts instructions and cycles |
| [`bench.py`](bench.py) | Builds the code, runs every measurement and prints the results |
| [`results.txt`](results.txt) | Output of `bench.py` |
| [`link.ld`](link.ld) | Linker script that places the code in the emulator's memory |

## Running it

The benchmark needs Python 3, clang and ld.lld from LLVM 18 or newer.

```sh
python3 bench.py                # print the results
python3 bench.py > results.txt  # refresh the committed results
python3 bench.py --check        # fail if results.txt is out of date
```

## What it models

- **The CPU.** Instructions are RV32E without compressed encodings, so that the
  emulator stays small. The emulator stops on any instruction outside RV32E, including
  multiply and divide. The code size is taken from a second build as RV32EC at `-Os`.
- **Time.** The code reads the `mcycle` counter. The emulator advances it by one cycle
  per instruction plus the extras of the chosen
  [pipeline model](../yt9215-cpu-performance.md#pipeline-models).
- **The pins.** One register at `0x40000000` reads the comparator output and one at
  `0x40000004` drives the CC line. These addresses are placeholders: the GPIO registers
  of the YT9215 are not published.
- **The PD partner.** `bench.py` has its own line coder and decoder. It generates the
  edges of a message at a chosen bit rate for the code to receive, and decodes the
  edges the code transmits.

## What it does not model

- The pipeline of the Nuclei N205. The two pipeline models are brackets, not a
  description of the core.
- Cache misses. The code is assumed to run from SRAM.
- Interrupts. The code runs with interrupts off.
- Noise, jitter, edge shape and comparator delay on the PD signal.
- The frame driver of the switch. The LLDP routines work on a frame in memory.

## Results

[`results.txt`](results.txt) has five tables: code size, cost of the routines that do
not depend on the clock, transmit accuracy, receive by polling, and GoodCRC turnaround.
The clock-dependent tables cover 125 MHz divided by 1, 2, 3, 4, 5, 6, 8 and 10.
[The note](../yt9215-cpu-performance.md#usb-pd-by-bit-banging) explains what they mean.
