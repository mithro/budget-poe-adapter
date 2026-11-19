# Speed and resources of the YT9215 CPU

The adapter firmware runs on the RISC-V CPU inside the YT9215. It has to negotiate PoE
power over LLDP, act as a USB-C PD source, switch ports and power on in the right
order, and manage the switch. This note estimates how fast that CPU is, how much memory
it has to work with, and whether that is enough.

The facts about the CPU, with their sources, are in
[`yt9215-embedded-cpu.md`](yt9215-embedded-cpu.md). This note builds estimates on them.
**Nothing in this note was measured on a YT9215.**

Related notes:

| Topic | Note |
| --- | --- |
| Facts about the CPU | [`yt9215-embedded-cpu.md`](yt9215-embedded-cpu.md) |
| USB-C PD timing | [`usb-c-pd.md`](usb-c-pd.md#5-usb-pd-physical-layer-bmc-on-cc) |
| PoE and LLDP | [`poe.md`](poe.md#45-lldp-data-link-layer-classification) |
| Switch registers | [`yt9215-registers/`](yt9215-registers/README.md) |
| Benchmark files | [`yt9215-cpu-performance/`](yt9215-cpu-performance/README.md) |

## Summary

- **The CPU is very likely fast enough for all four jobs.** The open questions are
  about registers and boot, not about speed.
- **The clock is not published.** It is most likely 125 MHz, the clock of the switch
  core. The estimates here are given for [five candidate clocks](#clock-scenarios)
  from 25 MHz to 125 MHz.
- **Bit-banged USB-PD needs about 31 MHz.** In the [benchmark](#the-benchmark), a
  polling receiver decodes PD messages from 21 MHz to 31 MHz upward, depending on the
  pipeline model. At 125 MHz the GoodCRC reply is ready 16 µs to 23 µs after the
  message ends, against a limit of 195 µs.
- **Four conditions decide bit-banged PD, and none is about CPU speed.** They are
  listed under [conditions](#conditions).
- **LLDP is no load at all.** Parsing a received LLDP frame and building the reply takes
  about 330 instructions, a few times a minute.
- **Memory is ample.** The firmware this adapter needs is estimated at about 12 KB of
  the 64 KB of SRAM when the code runs from flash.
- **Slow code hides in the flash.** Code that is not in the 2 KB cache is fetched from
  the SPI flash at 3 µs to 9 µs per cache line. Time-critical code must sit in SRAM.

| Job | Time scale | Verdict at 125 MHz | Verdict at 31.25 MHz | Detail |
| --- | --- | --- | --- | --- |
| PD transmit | 1.67 µs | Fits | Fits | [Transmit](#transmit) |
| PD receive | 1.67 µs | Fits | Marginal | [Receive](#receive) |
| GoodCRC reply | 195 µs | Fits | Fits | [Turnaround](#goodcrc-turnaround) |
| LLDP | 1 s | Fits | Fits | [LLDP](#lldp) |
| Sequencing | 1 ms | Fits | Fits | [Sequencing](#sequencing-and-switch-management) |
| Switch management | 1 ms | Fits | Fits | [Sequencing](#sequencing-and-switch-management) |

Every "Fits" for PD assumes the [conditions](#conditions) hold.

## Evidence codes

Statements are marked with one of these codes:

- **V** verified: read directly in a cited source.
- **M** measured: a result of the [benchmark](#the-benchmark), which runs in an
  emulator and not on the chip.
- **E** estimate: calculated here from stated assumptions.
- **I** inference: a judgement from other evidence.

## What the estimates rest on

These facts are taken from [`yt9215-embedded-cpu.md`](yt9215-embedded-cpu.md):

| Fact | Value | Detail |
| --- | --- | --- |
| Core | Nuclei N205 | [Identity](yt9215-embedded-cpu.md#identity) |
| Pipeline | 2 stages | [Identity](yt9215-embedded-cpu.md#identity) |
| Instruction set of vendor builds | RV32EC | [Instruction set](yt9215-embedded-cpu.md#instruction-set) |
| Hardware multiplier | Unknown | [Instruction set](yt9215-embedded-cpu.md#instruction-set) |
| SRAM | 64 KB | [Memory](yt9215-embedded-cpu.md#memory) |
| Instruction cache | 2 KB | [Memory](yt9215-embedded-cpu.md#memory) |
| Data cache | None in the N205 | [Identity](yt9215-embedded-cpu.md#identity) |
| SPI flash clock | 31.25 MHz | [Clock](yt9215-embedded-cpu.md#clock) |
| Switch core clock | 125 MHz | [Clock](yt9215-embedded-cpu.md#clock) |
| CPU clock | Unknown | [Clock](yt9215-embedded-cpu.md#clock) |
| Switch register access | One load or store | [Register access](yt9215-embedded-cpu.md#register-access) |
| GPIO registers | Unknown | [Peripherals](yt9215-embedded-cpu.md#peripherals) |
| DMA | None documented | [Peripherals](yt9215-embedded-cpu.md#peripherals) |
| Interrupt controller | Nuclei ECLIC | [Interrupts and timers](yt9215-embedded-cpu.md#interrupts-and-timers) |

This note assumes the worst documented case for the instruction set: RV32EC with no
multiplier and no atomic instructions.

## Clock scenarios

The CPU clock is unknown. The chip has a 25 MHz crystal, a 125 MHz switch core clock
and a 31.25 MHz flash clock, so the candidates are 125 MHz divided by a small number
and the crystal itself [**I**](#evidence-codes). The table gives what each would mean
[**E**](#evidence-codes):

| Clock | Cycle | Cycles per PD half bit | Cycles in 195 µs | Why it is a candidate |
| --- | --- | --- | --- | --- |
| 125 MHz | 8 ns | 208 | 24,375 | Switch core clock |
| 62.5 MHz | 16 ns | 104 | 12,188 | Half the core clock |
| 41.67 MHz | 24 ns | 69 | 8,125 | A third of the core clock |
| 31.25 MHz | 32 ns | 52 | 6,094 | Flash clock |
| 25 MHz | 40 ns | 42 | 4,875 | Crystal |

125 MHz is the most likely [**I**](#evidence-codes):

- The N205 reaches such speeds in other chips. Nuclei's
  [N200 series page](https://www.nucleisys.com/product/200.php) lists the GD32VF103 at
  108 MHz and an Amlogic chip with a customised N205 at 166 MHz
  [**V**](#evidence-codes).
- A switch core that already has a 125 MHz clock tree gains nothing from a second,
  slower one for the CPU.
- An instruction cache in front of a 31.25 MHz flash only pays off if the core is
  much faster than the flash.

The first firmware that runs can settle it by counting `mcycle` between two events a
known time apart, such as two edges of a UART character from a host.

## Instruction throughput

A 2-stage core executes most instructions in one cycle and loses a cycle or two on a
taken branch. The [benchmark](#the-benchmark) runs under a fast and a slow
[pipeline model](#pipeline-models) and needs 1.06 to 1.33 cycles per instruction
[**M**](#evidence-codes). That gives these instruction rates [**E**](#evidence-codes):

| Clock | Instructions per second, slow model | Instructions per second, fast model |
| --- | --- | --- |
| 125 MHz | 94 million | 118 million |
| 62.5 MHz | 47 million | 59 million |
| 31.25 MHz | 23 million | 29 million |
| 25 MHz | 19 million | 24 million |

Published benchmark scores show what the configuration of a small core does to them
[**V**](#evidence-codes):

| Core | Configuration | CoreMark per MHz | Source |
| --- | --- | --- | --- |
| Nuclei N205 | Not stated | 3.35 | [Nuclei slides](https://crvf2019.github.io/pdf/05.pdf) |
| GD32VF103 | RV32IMAC | 3.33 | [GigaDevice](https://www.gigadevice.com/about/news-and-event/news/gigadevice-unveils-the-gd32v-series-with-risc-v-core) |
| lowRISC Ibex "small" | RV32IMC | 2.47 | [Ibex README](https://github.com/lowRISC/ibex/blob/master/README.md) |
| lowRISC Ibex "micro" | RV32EC | 0.904 | [Ibex README](https://github.com/lowRISC/ibex/blob/master/README.md) |

- The same slides give the N205 1.42 DMIPS per MHz [**V**](#evidence-codes).
- Ibex is another 2-stage core. Its RV32EC configuration scores about a third of its
  RV32IMC configuration, mostly because CoreMark multiplies and the smaller
  configuration has to do that in software [**I**](#evidence-codes).
- An N205 without a multiplier would lose in the same way on CoreMark, so a CoreMark
  score between 1 and 3.35 per MHz is possible [**E**](#evidence-codes).
- The adapter firmware hardly multiplies. Its work is table lookups, shifts, compares
  and register writes, for which the instruction rates above hold whatever the
  CoreMark score [**I**](#evidence-codes).
- A 32-bit multiply in software takes at most 260 to 292 cycles in the benchmark
  [**M**](#evidence-codes). That is 2.3 µs at 125 MHz, so an occasional multiply, such
  as scaling a power value, costs nothing that matters.
- FreeRTOS does not need the atomic instructions; it masks interrupts
  [**I**](#evidence-codes).

## Memory and execute in place

The CPU has 64 KB of SRAM, a 2 KB instruction cache and no data cache. Code either runs
in place from the SPI flash (XIP) or is copied to SRAM at boot
([boot modes](yt9215-embedded-cpu.md#boot)).

### Cost of a cache miss

With XIP, an instruction that is not in the cache has to be read from the flash. The
table estimates one cache line refill at the 31.25 MHz flash clock, for the two read
modes the datasheet names and two plausible line sizes [**E**](#evidence-codes):

| Read mode | Line size | Flash clocks | Time | CPU cycles at 125 MHz |
| --- | --- | --- | --- | --- |
| Dual I/O | 16 bytes | 104 | 3.3 µs | 416 |
| Dual I/O | 32 bytes | 168 | 5.4 µs | 672 |
| Single I/O | 16 bytes | 160 | 5.1 µs | 640 |
| Single I/O | 32 bytes | 288 | 9.2 µs | 1,152 |

The assumptions behind the table:

- A single I/O read sends 8 command bits and 24 address bits, then 8 clocks per byte.
- A dual I/O read sends 8 command bits, 24 address bits and 8 dummy clocks, then
  4 clocks per byte.
- The flash controller starts a new read command for every line. A controller that
  keeps reading sequentially would be faster for straight-line code.
- The line size of the cache is not published. Nuclei cores report it in the
  `micfg_info` register
  ([Nuclei ISA specification](https://doc.nucleisys.com/nuclei_spec/isa/core_csr.html))
  [**V**](#evidence-codes).

What follows [**I**](#evidence-codes):

- **One miss costs more than a PD half bit.** A half bit is 1.67 µs. Code that
  transmits or receives PD must never miss, so it must run from SRAM.
- **Cold code is slow whatever the CPU clock.** Straight-line code that misses on
  every line runs at roughly 1 to 2 million instructions per second
  [**E**](#evidence-codes), about one sixtieth of the cached rate at 125 MHz.
- **Loops are fast.** 2 KB holds 700 to 1,000 RV32EC instructions. The whole
  benchmark, which is the PD transmitter, the PD receiver and the LLDP code, is
  1,870 bytes [**M**](#evidence-codes).
- **Twenty misses would use up the GoodCRC budget.** At 5 µs to 9 µs each, 20 to 40
  misses add up to 195 µs. This is the second reason to keep the PD code in SRAM.

### SRAM budget

With XIP, the SRAM holds only data and the code that is placed there on purpose. The
table is an estimate of what the adapter firmware needs [**E**](#evidence-codes):

| Use | Size | Basis |
| --- | --- | --- |
| Frame buffers | 6.1 KB | 4 buffers of 1,536 bytes |
| Task stacks | 4 KB | 4 tasks of 1 KB |
| Time-critical code in SRAM | 2 KB | [Benchmark size](#the-benchmark) |
| PD and LLDP state | 1 KB | Message buffers and counters |
| FreeRTOS kernel data | 1 KB | Task and queue structures |
| Total | 14.1 KB | – |
| Left of 64 KB | 49.9 KB | – |

Notes on the table:

- The vendor SDK sets a minimum of 56 frame buffers of 256 bytes, 14 KB in all
  ([packet path](yt9215-embedded-cpu.md#packet-path)) [**V**](#evidence-codes). The
  adapter firmware only ever handles LLDP frames, so 4 full-size buffers are assumed
  here instead. Whether the unpublished frame driver accepts fewer buffers than its
  minimum is unknown.
- The size of the vendor SDK library is not known, because it does not build without
  the firmware tree that is not public. The adapter needs a small part of it.

### Loading the code into SRAM

If the code is copied to SRAM at boot, code and data share the 64 KB, and nothing ever
misses. The benchmark code suggests that PD, LLDP and sequencing fit in well under
16 KB of code [**E**](#evidence-codes). The copy takes time at power-on
[**E**](#evidence-codes):

| Source | Bus speed | Time for 16 KB | Time for 64 KB |
| --- | --- | --- | --- |
| SPI flash, single I/O | 31.25 MHz | 4 ms | 17 ms |
| I²C EEPROM | 100 kHz | 1.5 s | 5.9 s |
| I²C EEPROM | 400 kHz | 0.4 s | 1.5 s |

The I²C figures count 9 clocks per byte. The datasheet gives the EEPROM load clock as
100 kHz typical and 800 kHz at most [**V**](#evidence-codes). Which of the two boot
modes the boot ROM really offers, and in what image format, is
[unknown](yt9215-embedded-cpu.md#boot).

## Interrupt latency

Nuclei gives ideal latencies for its cores in cycles
([interrupts and timers](yt9215-embedded-cpu.md#interrupts-and-timers))
[**V**](#evidence-codes). In time they are [**E**](#evidence-codes):

| Interrupt mode | Cycles to the handler | Time at 125 MHz | Time at 31.25 MHz |
| --- | --- | --- | --- |
| Vectored | 6 | 48 ns | 192 ns |
| Non-vectored on RV32E | 20 | 160 ns | 640 ns |

- The figures assume the handler is in SRAM or in the cache. A handler fetched from
  the flash adds a [cache miss](#cost-of-a-cache-miss).
- An interrupt handler that time-stamps one edge of the PD signal and queues it has a
  body of 12 instructions [**M**](#evidence-codes). With entry, register saves and
  return it comes to about 40 cycles per edge [**E**](#evidence-codes).
- Edges arrive as little as 1.52 µs apart. That is 190 cycles at 125 MHz and 47 cycles
  at 31.25 MHz, so an interrupt per edge works at 125 MHz and is at its limit at
  31.25 MHz [**E**](#evidence-codes).
- Whether a GPIO edge can raise an interrupt at all is
  [unknown](yt9215-embedded-cpu.md#interrupts-and-timers). If it can, the best use is
  to wake the firmware on the first edge of a message and to
  [poll](#receive) from there. The 64-bit preamble of a PD message lasts 213 µs, so
  nothing is lost while the handler starts.

## Register and GPIO access

- A switch register is one load or one store for the CPU
  ([register access](yt9215-embedded-cpu.md#register-access)) [**V**](#evidence-codes).
  How many cycles the bus between the CPU and the switch core adds is unknown.
- The vendor SDK takes a mutex and walks a table description for each access, which
  costs hundreds of instructions [**I**](#evidence-codes). Firmware that needs a fast
  register access writes the load or store itself.
- The GPIO data registers are [unknown](yt9215-embedded-cpu.md#peripherals). The
  benchmark assumes one load reads the pins and one store writes them, with no extra
  cycles in the fast model and two in the slow model. If a GPIO pin can only be reached
  through something slower, such as an indirect access with a busy flag, the
  [PD verdict](#verdict) does not hold.

## The benchmark

The folder [`yt9215-cpu-performance/`](yt9215-cpu-performance/README.md) holds a
workload model and the tools that measure it:

| File | Contents |
| --- | --- |
| [`pd_lldp.c`](yt9215-cpu-performance/pd_lldp.c) | PD transmit, PD receive, GoodCRC reply, CRC-32, LLDP parse and build |
| [`rv32e_emu.py`](yt9215-cpu-performance/rv32e_emu.py) | RV32E emulator that counts instructions and cycles |
| [`bench.py`](yt9215-cpu-performance/bench.py) | Builds the code, runs it against generated PD waveforms, prints the results |
| [`results.txt`](yt9215-cpu-performance/results.txt) | Output of `bench.py` |
| [`link.ld`](yt9215-cpu-performance/link.ld) | Linker script for the emulator's memory |

How it works:

- The C code is written for a core without a multiplier. It is compiled with clang as
  RV32E for the instruction counts and as RV32EC for the code size.
- The emulator refuses any instruction outside RV32E, so the counts are for the
  instruction set the vendor uses.
- The code reads time from the `mcycle` counter and reaches the PD signal through one
  GPIO input register and one GPIO output register.
- `bench.py` generates the waveform of a PD message at 270, 300 and 330 kbit/s, feeds
  it to the emulated GPIO input, and checks that the code decodes it. It decodes the
  waveform the code transmits in the same way.

<a id="pipeline-models"></a>
The emulator is not a model of the N205. It brackets the core with two pipeline
models:

| Model | Cycles per instruction | Extra for a taken branch | Extra for a memory load | Extra for a GPIO access |
| --- | --- | --- | --- | --- |
| Fast | 1 | 1 | 0 | 0 |
| Slow | 1 | 2 | 1 | 2 |

Limits of the benchmark:

- The cycle counts are as good as the two models. The real core may fall outside them.
- The waveforms have ideal edges. Noise, jitter and the delay of the comparator are
  not modelled.
- The code is plain C at `-O2`, not tuned.
- The code runs with interrupts off and never misses the cache.

Costs that do not depend on the clock [**M**](#evidence-codes):

| Routine | Instructions | Cycles, fast model | Cycles, slow model |
| --- | --- | --- | --- |
| CRC-32 of 6 bytes | 109 | 115 | 139 |
| CRC-32 of 34 bytes | 585 | 619 | 755 |
| Line-code a GoodCRC | 1,598 | 1,794 | 2,123 |
| Line-code the longest message | 4,666 | 5,077 | 6,111 |
| Edge interrupt handler body | 12 | 13 | 16 |
| Parse an LLDPDU of 249 bytes | 226 | 241 | 294 |
| Build an LLDP frame of 60 bytes | 101 | 102 | 118 |
| 32-bit multiply, worst case | 228 | 260 | 292 |

## USB-PD by bit-banging

PD signalling is a 300 kbit/s biphase mark code. The firmware must place and measure
edges that are 1.67 µs apart, and must answer every received message with a GoodCRC
that starts 25 µs to 195 µs after the message ends
([PD physical layer](usb-c-pd.md#5-usb-pd-physical-layer-bmc-on-cc)).

### Transmit

The benchmark toggles the GPIO output and waits for `mcycle` to reach the time of the
next edge. The table gives the worst distance of any edge from its ideal place
[**M**](#evidence-codes):

| Clock | Cycles per bit | Bit rate | Edge error, fast model | Edge error, slow model |
| --- | --- | --- | --- | --- |
| 12.5 MHz | 42 | 297.6 kbit/s | 240 ns | 480 ns |
| 15.625 MHz | 52 | 300.5 kbit/s | 192 ns | 384 ns |
| 20.833 MHz | 69 | 301.9 kbit/s | 120 ns | 312 ns |
| 25 MHz | 83 | 301.2 kbit/s | 80 ns | 260 ns |
| 31.25 MHz | 104 | 300.5 kbit/s | 96 ns | 192 ns |
| 41.667 MHz | 139 | 299.8 kbit/s | 48 ns | 156 ns |
| 62.5 MHz | 208 | 300.5 kbit/s | 48 ns | 96 ns |
| 125 MHz | 417 | 299.8 kbit/s | 20 ns | 52 ns |

- The transmitted message decodes correctly at every clock in the table
  [**M**](#evidence-codes).
- The edge error is one pass of the wait loop. The
  [target](usb-c-pd.md#61-transmit) of about 100 ns is met from 25 MHz in the fast
  model and from 62.5 MHz in the slow model [**M**](#evidence-codes).
- The bit rate is within 1 % of 300 kbit/s at every clock, well inside the 270 to
  330 kbit/s that PD allows.
- A GoodCRC lasts 0.5 ms and the longest message 1.4 ms. Interrupts are off for that
  time.

### Receive

The benchmark polls the GPIO input in a loop. When the level changes it reads
`mcycle`, classifies the gap since the last edge as a half bit or a full bit, and
decodes the line code as the bits arrive. The table gives the length of one pass of
the polling loop, the longest time the code is away from the loop to process a bit,
and whether a message decodes at all of 270, 300 and 330 kbit/s
[**M**](#evidence-codes):

| Clock | Poll period, fast | Poll period, slow | Longest gap, fast | Longest gap, slow | Result, fast | Result, slow |
| --- | --- | --- | --- | --- | --- | --- |
| 12.5 MHz | 0.56 µs | 0.88 µs | 4.08 µs | 2.80 µs | Fails | Fails |
| 15.625 MHz | 0.45 µs | 0.64 µs | 3.26 µs | 3.90 µs | Fails | Fails |
| 20.833 MHz | 0.34 µs | 0.48 µs | 2.45 µs | 3.07 µs | Decodes | Fails |
| 25 MHz | 0.28 µs | 0.40 µs | 2.04 µs | 2.56 µs | Decodes | Fails |
| 31.25 MHz | 0.22 µs | 0.32 µs | 1.63 µs | 2.05 µs | Decodes | Decodes |
| 41.667 MHz | 0.17 µs | 0.24 µs | 1.22 µs | 1.54 µs | Decodes | Decodes |
| 62.5 MHz | 0.11 µs | 0.16 µs | 0.82 µs | 1.02 µs | Decodes | Decodes |
| 125 MHz | 0.06 µs | 0.08 µs | 0.41 µs | 0.51 µs | Decodes | Decodes |

- The polling loop is 7 cycles in the fast model and 10 in the slow model
  [**M**](#evidence-codes).
- At 125 MHz the code samples the line 20 to 28 times per half bit, and its longest
  gap is a third of a half bit. That is a wide margin for real, noisy edges
  [**I**](#evidence-codes).
- At 31.25 MHz the longest gap is as long as a half bit. The message still decodes
  with ideal edges, but there is no margin left, so 31.25 MHz is marked marginal in
  the [summary](#summary) [**I**](#evidence-codes).
- The long gaps are the passes that finish a 5-bit symbol and store a byte. Tuned
  code can shorten them.

### GoodCRC turnaround

After the last edge of a message the benchmark checks the CRC, builds the GoodCRC with
the MessageID of the message, line-codes it and starts to send it. The table gives the
time from the last edge of the received message until the reply is ready to send, for
a Request message and for the longest message of seven data objects
[**M**](#evidence-codes):

| Clock | Request, fast | Request, slow | Longest, fast | Longest, slow |
| --- | --- | --- | --- | --- |
| 20.833 MHz | 96.6 µs | No receive | 117.1 µs | No receive |
| 25 MHz | 80.3 µs | No receive | 97.7 µs | No receive |
| 31.25 MHz | 64.3 µs | 76.3 µs | 78.1 µs | 93.3 µs |
| 41.667 MHz | 48.2 µs | 57.4 µs | 58.7 µs | 70.1 µs |
| 62.5 MHz | 32.2 µs | 38.1 µs | 39.1 µs | 46.6 µs |
| 125 MHz | 16.1 µs | 19.1 µs | 19.6 µs | 23.4 µs |

- Every reply that could be received starts inside the 25 µs to 195 µs window
  [**M**](#evidence-codes). At 125 MHz the code is ready early and waits for the
  25 µs mark.
- Most of the time goes into line-coding the GoodCRC bit by bit. There are only eight
  different GoodCRC messages, one per MessageID, so they can be line-coded once and
  kept in SRAM. The turnaround then shrinks to the CRC check, about 140 to 760
  cycles [**E**](#evidence-codes).

### Conditions

The results above hold only if all of these are true. None is confirmed for the
YT9215:

1. **Fast GPIO registers.** A GPIO pin can be read with one load and written with one
   store, in a few cycles ([register and GPIO access](#register-and-gpio-access)).
2. **A cycle counter.** The `mcycle` register, or a timer of similar resolution, is
   readable ([interrupts and timers](yt9215-embedded-cpu.md#interrupts-and-timers)).
3. **Code in SRAM.** The PD code runs from SRAM, or is otherwise certain never to miss
   the cache ([cost of a cache miss](#cost-of-a-cache-miss)).
4. **Interrupts off.** Nothing interrupts the CPU for up to 1.4 ms while a message is
   on the wire. A FreeRTOS tick that is held off that long is delayed, not lost.
5. **A comparator.** No pin of the chip can read the 1.1 V PD signal, so an external
   comparator turns it into a logic level
   ([receive hardware](usb-c-pd.md#62-receive)).
6. **A clock of 31.25 MHz or more**, and well above that for margin
   ([receive](#receive)).

### Verdict

If the CPU runs at 125 MHz and the [conditions](#conditions) hold, the CPU bit-bangs
USB-PD with a wide margin: 208 cycles per half bit against 7 to 10 cycles per sample,
and a GoodCRC ready eight times faster than required [**M**](#evidence-codes). The CPU
is not the limit. The limits are the GPIO registers, which are unpublished, and the
analogue front end.

While it waits for a message the firmware either polls the line and does nothing
else, or relies on a GPIO edge interrupt that is not confirmed to exist
([interrupt latency](#interrupt-latency)). A PD source mostly waits, so this decides
how the rest of the firmware is scheduled [**I**](#evidence-codes).

## LLDP

- LLDP runs on a time scale of seconds. The default transmit interval of IEEE 802.1AB
  is 30 s and its fast interval is 1 s [**I**](#evidence-codes).
- Parsing a realistic 249-byte LLDPDU from a PoE switch, including the IEEE 802.3
  power TLV, takes 226 instructions. Building the reply frame takes 101
  [**M**](#evidence-codes).
- Even fetched cold from the flash, the two routines together take well under a
  millisecond [**E**](#evidence-codes).
- The switch delivers LLDP frames to the CPU without firmware effort: a per-port
  setting traps them to port 10
  ([packet path](yt9215-embedded-cpu.md#packet-path)) [**V**](#evidence-codes).
- The cost of handing a frame to or from the frame driver is unknown, because the
  driver is not public. Copying a 300-byte frame is about 300 cycles
  [**E**](#evidence-codes).

LLDP is limited by nothing in the CPU. What it needs is the unpublished frame driver,
or the registers behind it.

## Sequencing and switch management

- Turning ports and power outputs on in order is a handful of register stores and
  GPIO writes, on a time scale of milliseconds. Each store is one instruction
  ([register and GPIO access](#register-and-gpio-access)).
- The delays between the steps come from the `mtime` timer through FreeRTOS, whose
  tick is normally 1 ms [**I**](#evidence-codes).
- Polling link state, counters and the chip's temperature sensor is a few register
  loads per second.
- A full switch set-up through the vendor SDK is thousands of register accesses with
  a mutex around each. Run once at boot from the flash, that is still a matter of
  milliseconds [**E**](#evidence-codes).

## What to measure first on real hardware

Each row is one short experiment once any code runs on the CPU, or once a debug port
answers:

| Question | How | Decides |
| --- | --- | --- |
| Which extensions does the core have? | Read `misa` | [Instruction set](yt9215-embedded-cpu.md#instruction-set) |
| How fast is the CPU clock? | Count `mcycle` over a known time | [Clock scenarios](#clock-scenarios) |
| How big is a cache line? | Read `micfg_info` | [Cost of a cache miss](#cost-of-a-cache-miss) |
| How slow is cold code? | Time a long straight-line function twice | [Cost of a cache miss](#cost-of-a-cache-miss) |
| How fast is a GPIO write? | Toggle a pin in a loop and measure the frequency | [Conditions](#conditions) |
| How fast is a GPIO read? | Time a loop of reads with `mcycle` | [Conditions](#conditions) |
| Can a GPIO edge interrupt the CPU? | Find the interrupt source in the ECLIC | [Interrupt latency](#interrupt-latency) |
| How long does a frame take to send? | Time `eth_tx_by_portlist()` with `mcycle` | [LLDP](#lldp) |

## Sources

- Facts about the CPU: [`yt9215-embedded-cpu.md`](yt9215-embedded-cpu.md#sources)
- Nuclei N200 series page: <https://www.nucleisys.com/product/200.php>
- Nuclei ISA specification, interrupts: <https://doc.nucleisys.com/nuclei_spec/isa/interrupt.html>
- Nuclei ISA specification, registers: <https://doc.nucleisys.com/nuclei_spec/isa/core_csr.html>
- Nuclei slides with N205 benchmark scores: <https://crvf2019.github.io/pdf/05.pdf>
- GigaDevice GD32VF103 announcement: <https://www.gigadevice.com/about/news-and-event/news/gigadevice-unveils-the-gd32v-series-with-risc-v-core>
- lowRISC Ibex configurations and scores: <https://github.com/lowRISC/ibex/blob/master/README.md>
- YT9215SCH datasheet V1.03: [`YT9215SCH_Datasheet_V1.03_2025-02-10.pdf`](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf)
