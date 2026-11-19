# Speed and resources of the YT9215 CPU

The adapter firmware runs on the RISC-V CPU inside the YT9215. The jobs considered here
are LLDP for PoE power, a USB-C PD source, switching ports and power on in the right
order, and managing the switch. This note estimates how fast that CPU is, how much
memory it has to work with, and whether that is enough.

The facts about the CPU, with their sources, are in
[`yt9215-embedded-cpu.md`](yt9215-embedded-cpu.md). This note builds estimates on them.
**No figure in this note is a measurement on a YT9215.**

Related notes:

| Topic | Note |
| --- | --- |
| Facts about the CPU | [`yt9215-embedded-cpu.md`](yt9215-embedded-cpu.md) |
| USB-C PD timing | [`usb-c-pd.md`](usb-c-pd.md#5-usb-pd-physical-layer-bmc-on-cc) |
| PoE and LLDP | [`poe.md`](poe.md#45-lldp-data-link-layer-classification) |
| Switch registers | [`yt9215-registers/`](yt9215-registers/README.md) |
| Benchmark files | [`yt9215-cpu-performance/`](yt9215-cpu-performance/README.md) |

## Summary

- **At every candidate clock the CPU is fast enough for LLDP, sequencing and switch
  management.** It is fast enough for bit-banged PD if the clock is 31.25 MHz or more
  and the [conditions](#conditions) hold.
- **The clock is not published.** It is most likely 125 MHz, the clock of the switch
  core. The estimates here are given for [five candidate clocks](#clock-scenarios)
  from 25 MHz to 125 MHz.
- **Bit-banged USB-PD needs about 31 MHz.** In the [benchmark](#the-benchmark), a
  polling receiver decodes PD messages from 21 MHz to 31 MHz upward, depending on the
  pipeline model. At 125 MHz the GoodCRC reply is ready 16 µs to 23 µs after the
  message ends, against a limit of 195 µs.
- **Seven conditions decide bit-banged PD, and only one of them is about CPU speed.**
  They are listed under [conditions](#conditions).
- **LLDP takes about 330 instructions.** That is the cost of parsing a received LLDP
  frame and building the reply, about twice a minute at the default interval of 30 s.
- **The firmware needs about a quarter of the SRAM.** The adapter firmware is estimated
  at about 14 KB of the 64 KB of SRAM when the code runs from flash.
- **Code that runs from flash can be slow.** Code that is not in the 2 KB cache is
  fetched from the SPI flash at about 3 µs to 9 µs per cache line. Time-critical code
  must sit in SRAM.

| Job | Time scale | Verdict at 125 MHz | Verdict at 31.25 MHz | Detail |
| --- | --- | --- | --- | --- |
| PD transmit | 1.67 µs | Fits | Marginal | [Transmit](#transmit) |
| PD receive | 1.67 µs | Fits | Marginal | [Receive](#receive) |
| GoodCRC reply | 195 µs | Fits | Fits | [Turnaround](#goodcrc-turnaround) |
| LLDP | 1 s | Fits | Fits | [LLDP](#lldp) |
| Sequencing | 1 ms | Fits | Fits | [Sequencing](#sequencing-and-switch-management) |
| Switch management | 1 ms | Fits | Fits | [Sequencing](#sequencing-and-switch-management) |

Every verdict for PD assumes the [conditions](#conditions) hold.

<a id="evidence-codes"></a>
## Evidence marks

Statements are marked with one of these words:

| Mark | Meaning |
| --- | --- |
| Verified | Read directly in a cited source |
| Measured | A result of the emulated [benchmark](#the-benchmark) |
| Estimated | Calculated here from stated assumptions |
| Inferred | A judgement from other evidence |

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
and a 31.25 MHz flash clock, so the candidates are 125 MHz divided by 1 to 5,
where the last is also the crystal frequency ([inferred](#evidence-codes)). The table gives what each would
mean ([estimated](#evidence-codes)):

| Clock | Cycle | Cycles per PD half bit | Cycles in 195 µs | Why it is a candidate |
| --- | --- | --- | --- | --- |
| 125 MHz | 8 ns | 208 | 24,375 | Switch core clock |
| 62.5 MHz | 16 ns | 104 | 12,188 | Half the core clock |
| 41.67 MHz | 24 ns | 69 | 8,125 | A third of the core clock |
| 31.25 MHz | 32 ns | 52 | 6,094 | Flash clock |
| 25 MHz | 40 ns | 42 | 4,875 | Crystal |

125 MHz is the most likely ([inferred](#evidence-codes)):

- The N205 reaches such speeds in other chips. Nuclei's
  [N200 series page](https://www.nucleisys.com/product/200.php) lists the GD32VF103 at
  108 MHz and an Amlogic chip with a customised N205 at 166 MHz
  ([verified](#evidence-codes)).
- A switch core that already has a 125 MHz clock tree gains nothing from a second,
  slower one for the CPU.

The `SYS_CLK` register has a second setting of 143 MHz, which the Linux driver and the
vendor SDK both decode as a 7 ns cycle ([clock](yt9215-embedded-cpu.md#clock)). Setting
0, 125 MHz, is the one both name for the YT9215. No source says which setting a
YT9215 uses in practice. A CPU on 143 MHz would be 14 % faster than the 125 MHz row.

The first firmware that runs can settle the clock by counting `mcycle` between two
events a known time apart, such as two edges of a UART character from a host.

## Instruction throughput

A 2-stage core executes most instructions in one cycle and loses a cycle or two on a
taken branch. The [benchmark](#the-benchmark) runs under a fast and a slow
[pipeline model](#pipeline-models). Its routines need 1.01 to 1.14 cycles per
instruction in the fast model and 1.17 to 1.33 in the slow model
([measured](#evidence-codes)). The two ends of that range give these instruction rates
([estimated](#evidence-codes)):

| Clock | Instructions per second at 1.33 cycles each | Instructions per second at 1.01 cycles each |
| --- | --- | --- |
| 125 MHz | 94 million | 124 million |
| 62.5 MHz | 47 million | 62 million |
| 41.67 MHz | 31 million | 41 million |
| 31.25 MHz | 23 million | 31 million |
| 25 MHz | 19 million | 25 million |

Published benchmark scores show what the configuration of a small core does to them
([verified](#evidence-codes)):

| Core | Configuration | CoreMark per MHz | Source |
| --- | --- | --- | --- |
| Nuclei N205 | Not stated | 3.35 | [Nuclei slides](https://crvf2019.github.io/pdf/05.pdf) |
| GD32VF103 | Not stated | 3.33 | [GigaDevice](https://www.gigadevice.com/about/news-and-event/news/gigadevice-unveils-the-gd32v-series-with-risc-v-core) |
| lowRISC Ibex "small" | RV32IMC | 2.47 | [Ibex README](https://github.com/lowRISC/ibex/blob/master/README.md) |
| lowRISC Ibex "micro" | RV32EC | 0.904 | [Ibex README](https://github.com/lowRISC/ibex/blob/master/README.md) |

- The same slides give the N205 1.42 DMIPS per MHz ([verified](#evidence-codes)).
- The GD32VF103 has an N205 core
  ([Nuclei SDK build system](https://doc.nucleisys.com/nuclei_sdk/develop/buildsystem.html))
  ([verified](#evidence-codes)).
- Ibex is another 2-stage core. Its RV32EC configuration scores about a third of its
  RV32IMC configuration. The likely main reason is that CoreMark multiplies and the
  smaller configuration has to do that in software ([inferred](#evidence-codes)).
- An N205 without a multiplier would lose in the same way on CoreMark, so a CoreMark
  score between 1 and 3.35 per MHz is possible ([estimated](#evidence-codes)).
- The adapter firmware rarely multiplies. Its work is table lookups, shifts, compares
  and register writes, for which the instruction rates above hold whatever the
  CoreMark score ([inferred](#evidence-codes)).
- A 32-bit multiply in software takes at most 260 to 292 cycles in the benchmark
  ([measured](#evidence-codes)). That is 2.1 µs to 2.3 µs at 125 MHz. Scaling a power
  value once per negotiation is the kind of multiply the firmware does.
- FreeRTOS does not need the atomic instructions; it masks interrupts
  ([inferred](#evidence-codes)).

## Memory and execute in place

The CPU has 64 KB of SRAM, a 2 KB instruction cache and no data cache. Code either runs
in place from the SPI flash (XIP) or is copied to SRAM at boot
([boot modes](yt9215-embedded-cpu.md#boot)).

### Cost of a cache miss

With XIP, an instruction that is not in the cache has to be read from the flash. The
table estimates one cache line refill at the 31.25 MHz flash clock, for three common
read commands of SPI NOR flash and two plausible line sizes
([estimated](#evidence-codes)):

| Read command | Line size | Flash clocks | Time | CPU cycles at 125 MHz |
| --- | --- | --- | --- | --- |
| Dual I/O read | 16 bytes | 88 | 2.8 µs | 352 |
| Dual I/O read | 32 bytes | 152 | 4.9 µs | 608 |
| Dual output read | 16 bytes | 104 | 3.3 µs | 416 |
| Dual output read | 32 bytes | 168 | 5.4 µs | 672 |
| Single I/O read | 16 bytes | 160 | 5.1 µs | 640 |
| Single I/O read | 32 bytes | 288 | 9.2 µs | 1,152 |

The assumptions behind the table:

- A single I/O read sends 8 command bits and 24 address bits, then 8 clocks per byte.
- A dual output read sends 8 command bits, 24 address bits and 8 dummy clocks, then
  4 clocks per byte.
- A dual I/O read sends 8 command bits, the address on two lines in 12 clocks and
  4 mode clocks, then 4 clocks per byte.
- The datasheet names a serial I/O mode and a dual I/O mode of the flash interface and
  does not name the read commands, so all three are shown.
- The flash controller starts a new read command for every line. A controller that
  keeps reading sequentially would be faster for straight-line code.
- The line size of the cache is not published. Nuclei cores report it in the
  `micfg_info` register
  ([Nuclei ISA specification](https://doc.nucleisys.com/nuclei_spec/isa/core_csr.html))
  ([verified](#evidence-codes)).

What follows ([inferred](#evidence-codes)):

- **One miss costs more than a PD half bit.** A half bit is 1.67 µs. Code that
  transmits or receives PD must never miss, so it must run from SRAM.
- **Cold code is slow whatever the CPU clock.** Straight-line code that misses on
  every line runs at roughly 1 to 2 million instructions per second
  ([estimated](#evidence-codes)), against 94 to 124 million when cached at 125 MHz.
  The estimate takes 3 bytes as the average size of an RV32EC instruction.
- **Loops are fast.** At 3 bytes each, 2 KB holds about 680 instructions. The whole
  benchmark, which is the PD transmitter, the PD receiver and the LLDP code, is
  1,898 bytes built for size and 2,310 bytes built for speed
  ([measured](#evidence-codes)).
- **Misses would use up the GoodCRC budget.** At 2.8 µs to 9.2 µs each, 21 to 70
  misses add up to 195 µs. This is the second reason to keep the PD code in SRAM.

### SRAM budget

With XIP, the SRAM holds only data and the code that is placed there on purpose. The
table is an estimate of what the adapter firmware needs ([estimated](#evidence-codes)):

| Use | Size | Basis |
| --- | --- | --- |
| Frame buffers | 6.0 KB | 4 buffers of 1,536 bytes |
| Task stacks | 4.0 KB | 4 tasks of 1 KB |
| Time-critical code in SRAM | 2.3 KB | [Benchmark size](#the-benchmark) built for speed |
| PD and LLDP state | 1.0 KB | Message buffers and counters |
| FreeRTOS kernel data | 1.0 KB | Task and queue structures |
| Total | 14.3 KB | – |
| Left of 64 KB | 49.7 KB | – |

Notes on the table:

- The vendor SDK sets a minimum of 56 frame buffers of 256 bytes, 14 KB in all
  ([packet path](yt9215-embedded-cpu.md#packet-path)) ([verified](#evidence-codes)).
  The adapter firmware only ever handles LLDP frames, so 4 full-size buffers are
  assumed here instead. Whether the unpublished frame driver accepts fewer buffers
  than its minimum is unknown. With the SDK minimum the total is 22.3 KB.
- The size of the vendor SDK library is not known, because it does not build without
  the firmware tree that is not public. The adapter firmware calls only its port
  control, LLDP trap and frame functions.

### Loading the code into SRAM

If the code is copied to SRAM at boot, code and data share the 64 KB, and nothing ever
misses. The benchmark code is 2.3 KB, and the assumption here is that PD, LLDP and
sequencing with a small kernel fit in 16 KB of code ([estimated](#evidence-codes)).
The copy takes time at power-on ([estimated](#evidence-codes)):

| Source | Mode | Bus speed | Time for 16 KB | Time for 64 KB |
| --- | --- | --- | --- | --- |
| SPI flash | Single I/O | 31.25 MHz | 4 ms | 17 ms |
| I²C EEPROM | – | 100 kHz | 1.5 s | 5.9 s |
| I²C EEPROM | – | 800 kHz | 0.2 s | 0.7 s |

The I²C figures count 9 clocks per byte. The datasheet gives the EEPROM load clock as
100 kHz typical and 800 kHz at most
([Table 36](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=54))
([verified](#evidence-codes)). Which of the two boot modes the boot ROM really offers,
and in what image format, is [unknown](yt9215-embedded-cpu.md#getting-code-onto-the-cpu).

## Interrupt latency

Nuclei gives ideal latencies for its cores in cycles
([interrupts and timers](yt9215-embedded-cpu.md#interrupts-and-timers))
([verified](#evidence-codes)). In time they are ([estimated](#evidence-codes)):

| Interrupt mode | Cycles to the handler | Time at 125 MHz | Time at 31.25 MHz |
| --- | --- | --- | --- |
| Vectored | 6 | 48 ns | 192 ns |
| Non-vectored on RV32E | 20 | 160 ns | 640 ns |

- The figures assume the handler is in SRAM or in the cache. A handler fetched from
  the flash adds a [cache miss](#cost-of-a-cache-miss).
- An interrupt handler that time-stamps one edge of the PD signal and queues it has a
  body of 12 instructions ([measured](#evidence-codes)). With entry, register saves and
  return it comes to about 40 cycles per edge ([estimated](#evidence-codes)).
- Edges arrive as little as 1.52 µs apart. That is 189 cycles at 125 MHz and 47 cycles
  at 31.25 MHz, so an interrupt per edge works at 125 MHz and is at its limit at
  31.25 MHz ([estimated](#evidence-codes)).
- Whether a GPIO edge can raise an interrupt at all is
  [unknown](yt9215-embedded-cpu.md#interrupts-and-timers). If it can, the best use is
  to wake the firmware on the first edge of a message and to
  [poll](#receive) from there. The 64-bit preamble of a PD message lasts 213 µs at
  300 kbit/s and 194 µs at 330 kbit/s, which leaves the handler that long to start
  before the first data bit.

## Register and GPIO access

- A switch register is one load or one store for the CPU
  ([register access](yt9215-embedded-cpu.md#register-access))
  ([verified](#evidence-codes)). How many cycles the bus between the CPU and the switch
  core adds is unknown.
- The vendor SDK takes a mutex and walks a table description for each access, which
  is estimated at hundreds of instructions ([inferred](#evidence-codes)). Firmware that
  needs a fast register access writes the load or store itself.
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
| [`pd_lldp.c`](yt9215-cpu-performance/pd_lldp.c) | Workload in C |
| [`rv32e_emu.py`](yt9215-cpu-performance/rv32e_emu.py) | RV32E emulator |
| [`bench.py`](yt9215-cpu-performance/bench.py) | Benchmark driver |
| [`results.txt`](yt9215-cpu-performance/results.txt) | Output of `bench.py` |
| [`link.ld`](yt9215-cpu-performance/link.ld) | Linker script |

How it works:

- The workload is PD transmit, PD receive, the GoodCRC reply, the PD CRC-32, an LLDP
  parser and an LLDP frame builder. It is written for a core without a multiplier.
- It is compiled with clang as RV32E at `-O2` for the instruction counts, and as RV32EC
  at `-Os` and at `-O2` for the code size.
- The emulator counts instructions and cycles. It refuses any instruction outside
  RV32E, so the counts are for RV32E. The vendor's RV32EC build may differ by a few
  instructions.
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
- A store to memory and a shift cost no extra cycle in either model.
- Code in SRAM is fetched with no wait cycles. Whether the 64 KB SRAM is a local
  memory of the core or sits on a slower bus is not published. Wait cycles on fetches
  would add to every figure.
- The waveforms have ideal edges. Noise, jitter and the delay of the comparator are
  not modelled.
- The code is plain C at `-O2`, not tuned.
- The code runs with interrupts off and never misses the cache.
- Transmit is tested with the eight GoodCRC messages. Receive is tested with six
  messages: a Request, the longest message of seven data objects, and four messages
  of random content.
- The turnaround is measured at 300 kbit/s only.
- The receiver decodes messages that start with SOP. It does not recognise the
  [Hard Reset](usb-c-pd.md#52-framing) ordered set.
- The LLDP parser reads the 12-byte IEEE 802.3at form of the power TLV. The 29-byte
  IEEE 802.3bt form is not modelled.

Costs that do not depend on the clock ([measured](#evidence-codes)):

| Routine | Instructions | Cycles, fast model | Cycles, slow model |
| --- | --- | --- | --- |
| CRC-32 of 6 bytes | 109 | 115 | 139 |
| CRC-32 of 34 bytes | 585 | 619 | 755 |
| Line-code a GoodCRC | 1,598 | 1,794 | 2,123 |
| Line-code the longest message | 4,666 | 5,077 | 6,111 |
| Edge interrupt handler body | 12 | 13 | 16 |
| Parse an LLDPDU of 249 bytes | 226 | 241 | 294 |
| Build an LLDP frame of 60 bytes | 102 | 103 | 119 |
| 32-bit multiply, worst case | 228 | 260 | 292 |

## USB-PD by bit-banging

PD signalling is a 300 kbit/s biphase mark code. The firmware must place and measure
edges that are 1.67 µs apart, and must answer every received message with a GoodCRC
that starts 25 µs to 195 µs after the message ends
([PD physical layer](usb-c-pd.md#5-usb-pd-physical-layer-bmc-on-cc)).

### Transmit

The benchmark toggles the GPIO output and waits for `mcycle` to reach the time of the
next edge. The table gives the worst distance of any edge from its ideal place over
the eight GoodCRC messages ([measured](#evidence-codes)). The ideal places are counted
from the first transmitted edge at the bit rate in the table, so the figure is the
jitter of the edges and not an error of the bit rate:

| Clock | Cycles per bit | Bit rate | Edge error, fast model | Edge error, slow model |
| --- | --- | --- | --- | --- |
| 12.5 MHz | 42 | 297.6 kbit/s | 320 ns | 480 ns |
| 15.625 MHz | 52 | 300.5 kbit/s | 256 ns | 384 ns |
| 20.833 MHz | 69 | 301.9 kbit/s | 144 ns | 312 ns |
| 25 MHz | 83 | 301.2 kbit/s | 120 ns | 260 ns |
| 31.25 MHz | 104 | 300.5 kbit/s | 128 ns | 192 ns |
| 41.667 MHz | 139 | 299.8 kbit/s | 72 ns | 156 ns |
| 62.5 MHz | 208 | 300.5 kbit/s | 64 ns | 96 ns |
| 125 MHz | 417 | 299.8 kbit/s | 24 ns | 52 ns |

- All eight messages decode correctly at every clock in the table
  ([measured](#evidence-codes)).
- The edge error comes from the length of one pass of the wait loop. The
  [target](usb-c-pd.md#61-transmit) of about 100 ns is met from 41.667 MHz in the fast
  model and from 62.5 MHz in the slow model ([measured](#evidence-codes)). At
  31.25 MHz the error is 128 ns to 192 ns, so transmit is marked marginal in the
  [summary](#summary).
- The bit rate is within 1 % of 300 kbit/s at every clock. PD allows 270 to
  330 kbit/s.
- A GoodCRC lasts 0.5 ms and the longest message 1.4 ms. Interrupts are off for that
  time.
- After its own message the source waits for the GoodCRC of the sink, for up to
  1.1 ms ([message layer](usb-c-pd.md#53-message-layer-essentials)). The firmware
  [polls](#receive) during that wait.
- A Hard Reset is sent with the same routine. It is a preamble and four symbols.

### Receive

The benchmark polls the GPIO input in a loop. When the level changes it reads
`mcycle`, classifies the gap since the last edge as a half bit or a full bit, and
decodes the line code as the bits arrive. The table gives the usual length of one pass
of the polling loop, the longest time the code is away from the loop to process a bit,
and whether the six test messages decode at all of 270, 300 and 330 kbit/s
([measured](#evidence-codes)). Where the messages do not decode there are no figures:

| Clock | Poll period, fast | Poll period, slow | Longest gap, fast | Longest gap, slow | Result, fast | Result, slow |
| --- | --- | --- | --- | --- | --- | --- |
| 12.5 MHz | – | – | – | – | Fails | Fails |
| 15.625 MHz | – | – | – | – | Fails | Fails |
| 20.833 MHz | 0.38 µs | – | 2.45 µs | – | Decodes | Fails |
| 25 MHz | 0.32 µs | – | 2.04 µs | – | Decodes | Fails |
| 31.25 MHz | 0.26 µs | 0.35 µs | 1.63 µs | 2.05 µs | Decodes | Decodes |
| 41.667 MHz | 0.19 µs | 0.26 µs | 1.22 µs | 1.54 µs | Decodes | Decodes |
| 62.5 MHz | 0.13 µs | 0.18 µs | 0.82 µs | 1.02 µs | Decodes | Decodes |
| 125 MHz | 0.06 µs | 0.09 µs | 0.41 µs | 0.51 µs | Decodes | Decodes |

- The usual pass of the polling loop is 8 cycles in the fast model and 11 in the slow
  model. The longest gap is 51 and 64 cycles ([measured](#evidence-codes)).
- At 125 MHz and 300 kbit/s the code samples the line 19 to 26 times per half bit.
  Its longest gap is 0.22 to 0.34 of a half bit across the three bit rates. Real edges have noise and jitter that the
  benchmark does not model. This sampling rate leaves room for a filter that asks for
  several equal samples before it accepts an edge ([inferred](#evidence-codes)).
- At 31.25 MHz the longest gap at 300 kbit/s is 0.98 of a half bit in the fast model
  and 1.23 in the slow model. The messages still decode
  with ideal edges, but there is no margin left, so 31.25 MHz is marked marginal in
  the [summary](#summary) ([inferred](#evidence-codes)).
- The long gaps are the passes that finish a 5-bit symbol and store a byte. Tuned
  code can shorten them.
- A receiver for real use must also recognise a
  [Hard Reset](usb-c-pd.md#53-message-layer-essentials). That is one more comparison
  of the four start symbols and is not in the benchmark.

### GoodCRC turnaround

After the last bit of a message the benchmark checks the CRC, builds the GoodCRC with
the MessageID of the message, line-codes it and starts to send it. The table gives the
time from the end of the last bit of the received message until the reply is ready to
send, for a Request message and for the longest message of seven data objects, at
300 kbit/s ([measured](#evidence-codes)):

| Clock | Request, fast | Request, slow | Longest, fast | Longest, slow |
| --- | --- | --- | --- | --- |
| 20.833 MHz | 96.3 µs | No receive | 117.2 µs | No receive |
| 25 MHz | 80.4 µs | No receive | 97.7 µs | No receive |
| 31.25 MHz | 64.4 µs | 76.5 µs | 78.2 µs | 93.2 µs |
| 41.667 MHz | 48.3 µs | 57.4 µs | 58.6 µs | 69.9 µs |
| 62.5 MHz | 32.2 µs | 38.2 µs | 39.1 µs | 46.7 µs |
| 125 MHz | 16.1 µs | 19.1 µs | 19.6 µs | 23.4 µs |

- Every reply that could be received starts inside the 25 µs to 195 µs window
  ([measured](#evidence-codes)). At 125 MHz the code is ready early and waits for the
  25 µs mark.
- Most of the time goes into line-coding the GoodCRC bit by bit. There are only eight
  different GoodCRC messages, one per MessageID, so they can be line-coded once and
  kept in SRAM. The turnaround then shrinks to the CRC check, which is 115 to 755
  cycles for messages of 6 to 34 bytes ([measured](#evidence-codes)).

### Conditions

The results above hold only if all of these are true. None is confirmed for the
YT9215:

1. **Fast GPIO registers.** A GPIO pin can be read with one load and written with one
   store, with 0 to 2 extra cycles as the [pipeline models](#pipeline-models) assume
   ([register and GPIO access](#register-and-gpio-access)).
2. **A cycle counter.** The `mcycle` register, or a timer of similar resolution, is
   readable and is not stopped through `mcountinhibit`
   ([interrupts and timers](yt9215-embedded-cpu.md#interrupts-and-timers)).
3. **Code in SRAM.** The PD code runs from SRAM, or is otherwise certain never to miss
   the cache ([cost of a cache miss](#cost-of-a-cache-miss)).
4. **Interrupts off.** Nothing interrupts the CPU from the first edge of a message to
   the end of its GoodCRC. For the longest message that is about 2.1 ms: 1.4 ms of
   message, up to 0.2 ms of gap and 0.5 ms of GoodCRC. With the usual FreeRTOS tick of
   1 ms, two or three ticks fall into that time and all but one are lost, so the firmware must
   take its time from `mtime` and not from a count of ticks
   ([inferred](#evidence-codes)).
5. **A comparator.** No pin of the chip reads the 1.1 V PD signal reliably. The input
   high threshold is 2.0 V for a pin on a 3.3 V supply
   ([Table 31](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=51))
   and 1.2 V for a pin on a 1.8 V supply
   ([Table 31, continued](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=52))
   ([verified](#evidence-codes)). An external comparator turns the signal into a logic
   level ([receive hardware](usb-c-pd.md#62-receive)). Attach detection needs a second
   comparator with a threshold near 2.6 V, read on a GPIO pin on a time scale of
   milliseconds ([other analogue needs](usb-c-pd.md#63-other-analog-needs)).
6. **A transmit pin that can be released.** The transmitter must stop driving the line
   within 23 µs of the end of a message
   ([signalling](usb-c-pd.md#51-signalling)). That needs a GPIO direction register
   that is as fast as the data register, or an analogue switch on a second GPIO pin.
7. **A clock of 31.25 MHz or more.** At 62.5 MHz and 300 kbit/s the longest gap of the
   receiver is 0.5 to 0.6 of a half bit ([receive](#receive)).

### Verdict

If the CPU runs at 125 MHz and the [conditions](#conditions) hold, the CPU bit-bangs
USB-PD with a wide margin: 208 cycles per half bit at 300 kbit/s against 8 to 11 cycles per sample,
and a GoodCRC ready eight times faster than required ([measured](#evidence-codes)).
The CPU is not the limit. The limits are the GPIO registers, which are unpublished,
and the analogue front end.

While it waits for a message the firmware either polls the line and does nothing
else, or relies on a GPIO edge interrupt that is not confirmed to exist
([interrupt latency](#interrupt-latency)). A PD source mostly waits, so this decides
how the rest of the firmware is scheduled ([inferred](#evidence-codes)).

## LLDP

- LLDP runs on a time scale of seconds. The default transmit interval of IEEE 802.1AB
  is 30 s and its fast interval is 1 s.
- Parsing a realistic 249-byte LLDPDU from a PoE switch, including the IEEE 802.3
  power TLV, takes 226 instructions. Building the reply frame takes 102
  ([measured](#evidence-codes)).
- Fetched cold from the flash at 1 million instructions per second, the two routines
  together take a third of a millisecond ([estimated](#evidence-codes)).
- The switch delivers LLDP frames to the CPU without firmware effort: a per-port
  setting traps them to port 10
  ([packet path](yt9215-embedded-cpu.md#packet-path)) ([verified](#evidence-codes)).
- The cost of handing a frame to or from the frame driver is unknown, because the
  driver is not public. Copying a 300-byte frame at 4 cycles per pass of the copy loop
  is about 300 cycles a word at a time and about 1,200 cycles a byte at a time
  ([estimated](#evidence-codes)).

LLDP is limited by nothing in the CPU. What it needs is the unpublished frame driver,
or the registers behind it.

## Sequencing and switch management

- Turning ports and power outputs on in order is fewer than ten register stores and
  GPIO writes per step, on a time scale of milliseconds. Each store is one instruction
  ([register and GPIO access](#register-and-gpio-access)).
- The delays between the steps come from the `mtime` timer through FreeRTOS, whose
  tick is normally 1 ms ([inferred](#evidence-codes)).
- Polling link state, counters and the chip's temperature sensor once a second is
  under 100 register loads per second ([estimated](#evidence-codes)).
- A full switch set-up through the vendor SDK is assumed here to be 3,000 register
  accesses of 300 instructions each, about a million instructions. That is about
  10 ms when the code is cached and up to a second if every cache line misses
  ([estimated](#evidence-codes)). It runs once at boot.

## What to measure first on real hardware

Each row is one short experiment once any code runs on the CPU, or once a debug port
answers:

| Question | How | Decides |
| --- | --- | --- |
| Which extensions does the core have? | Read `misa` | [Instruction set](yt9215-embedded-cpu.md#instruction-set) |
| How fast is the CPU clock? | Count `mcycle` over a known time | [Clock scenarios](#clock-scenarios) |
| How big is a cache line? | Read `micfg_info` | [Cost of a cache miss](#cost-of-a-cache-miss) |
| How slow is cold code? | Time a long straight-line function twice | [Cost of a cache miss](#cost-of-a-cache-miss) |
| Does code in SRAM run at full speed? | Time one loop in SRAM and the same loop in the cache | [The benchmark](#the-benchmark) |
| How fast is a GPIO write? | Toggle a pin in a loop and measure the frequency | [Conditions](#conditions) |
| How fast is a GPIO read? | Time a loop of reads with `mcycle` | [Conditions](#conditions) |
| Can a GPIO edge interrupt the CPU? | Find the interrupt source in the ECLIC | [Interrupt latency](#interrupt-latency) |
| How long does a frame take to send? | Time [`eth_tx_by_portlist()`](yt9215-embedded-cpu.md#packet-path) with `mcycle` | [LLDP](#lldp) |

## Sources

- Facts about the CPU: [`yt9215-embedded-cpu.md`](yt9215-embedded-cpu.md#sources)
- Nuclei N200 series page: <https://www.nucleisys.com/product/200.php>
- Nuclei ISA specification, interrupts: <https://doc.nucleisys.com/nuclei_spec/isa/interrupt.html>
- Nuclei ISA specification, registers: <https://doc.nucleisys.com/nuclei_spec/isa/core_csr.html>
- Nuclei SDK build system: <https://doc.nucleisys.com/nuclei_sdk/develop/buildsystem.html>
- Nuclei slides with N205 benchmark scores: <https://crvf2019.github.io/pdf/05.pdf>
- GigaDevice GD32VF103 announcement: <https://www.gigadevice.com/about/news-and-event/news/gigadevice-unveils-the-gd32v-series-with-risc-v-core>
- lowRISC Ibex configurations and scores: <https://github.com/lowRISC/ibex/blob/master/README.md>
- YT9215SCH datasheet V1.03: [`YT9215SCH_Datasheet_V1.03_2025-02-10.pdf`](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf)
