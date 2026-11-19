#!/usr/bin/env python3
"""Build pd_lldp.c for RV32E, run it in rv32e_emu.py and print what it costs.

    python3 bench.py            print the results
    python3 bench.py --check    also compare them with results.txt

Needs clang and ld.lld (LLVM 18 or newer) on the PATH.
"""

import os
import subprocess
import sys
import tempfile
import zlib

from rv32e_emu import Cpu, Elf, MODELS

HERE = os.path.dirname(os.path.abspath(__file__))
CLOCKS_MHZ = [12.5, 15.625, 20.833, 25, 31.25, 41.667, 62.5, 125]  # 125 MHz divided by 10 to 1
BIT_RATES = [270e3, 300e3, 330e3]
SCRATCH = 0x28000  # free RAM in the emulator for arguments

ENC = [0x1E, 0x09, 0x14, 0x15, 0x0A, 0x0B, 0x0E, 0x0F,
       0x12, 0x13, 0x16, 0x17, 0x1A, 0x1B, 0x1C, 0x1D]
SYNC1, SYNC2, EOP = 0x18, 0x11, 0x0D


def build(tmp):
    common = ["clang", "--target=riscv32-unknown-elf", "-mabi=ilp32e", "-ffreestanding",
              "-fno-builtin", "-nostdlib", "-Wall", "-Wextra", "-Werror", "-c",
              os.path.join(HERE, "pd_lldp.c")]
    obj = os.path.join(tmp, "pd_e.o")
    elf = os.path.join(tmp, "pd_e.elf")
    small = os.path.join(tmp, "pd_ec.o")
    subprocess.run(common + ["-march=rv32e", "-O2", "-o", obj], check=True)
    subprocess.run(["ld.lld", "--no-warnings", "-e", "pd_tx", "-T", os.path.join(HERE, "link.ld"),
                    obj, "-o", elf], check=True)
    subprocess.run(common + ["-march=rv32ec", "-Os", "-o", small], check=True)
    size = subprocess.run(["llvm-size", small], check=True, capture_output=True, text=True)
    text, data, bss = (int(v) for v in size.stdout.splitlines()[1].split()[:3])
    return Elf(elf), (text, data, bss)


# -- reference USB-PD line coding ---------------------------------------------

def pd_bits(message):
    """The bits of a message on the wire, CRC appended, as a list of 0 and 1."""
    body = message + zlib.crc32(message).to_bytes(4, "little")
    symbols = [SYNC1, SYNC1, SYNC1, SYNC2]
    for byte in body:
        symbols += [ENC[byte & 15], ENC[byte >> 4]]
    symbols.append(EOP)
    bits = [i & 1 for i in range(64)]
    for symbol in symbols:
        bits += [(symbol >> i) & 1 for i in range(5)]
    return bits


def bmc_edges(bits, bit_time, start):
    """Edge times of the biphase mark coded bits. The line idles low."""
    edges = []
    for i, bit in enumerate(bits):
        edges.append(start + i * bit_time)
        if bit:
            edges.append(start + (i + 0.5) * bit_time)
    if len(edges) % 2:  # ends high: hold, then go low
        edges.append(start + (len(bits) + 0.5) * bit_time)
    return edges


def decode_edges(edges, bit_time):
    """Decode edge times back to message bytes, or return None."""
    bits, half = [], False
    for a, b in zip(edges, edges[1:]):
        if b - a < 0.75 * bit_time:
            half = not half
            if not half:
                bits.append(1)
        else:
            if half:
                return None
            bits.append(0)
    sop = [(s >> i) & 1 for s in (SYNC1, SYNC1, SYNC1, SYNC2) for i in range(5)]
    for i in range(len(bits) - 20):
        if bits[i:i + 20] == sop:
            bits = bits[i + 20:]
            break
    else:
        return None
    nibbles = []
    for i in range(0, len(bits) - 4, 5):
        symbol = sum(bits[i + j] << j for j in range(5))
        if symbol == EOP:
            break
        if symbol not in ENC:
            return None
        nibbles.append(ENC.index(symbol))
    return bytes(nibbles[i] | (nibbles[i + 1] << 4) for i in range(0, len(nibbles) - 1, 2))


class Wave:
    """A comparator output that the emulated GPIO input reads."""

    def __init__(self, edges_s, clock_hz):
        self.edges = [t * clock_hz for t in edges_s]
        self.index = 0

    def __call__(self, cycle):  # cycles only ever increase
        while self.index < len(self.edges) and self.edges[self.index] <= cycle:
            self.index += 1
        return self.index & 1


# -- measurements --------------------------------------------------------------

def measure(elf, model, name, *args, setup=None):
    cpu = Cpu(elf, model)
    if setup:
        setup(cpu)
    result = cpu.call(name, *args)
    return cpu, result


def halves(clock_hz):
    bit = round(clock_hz / 300e3)
    return bit // 2, bit - bit // 2


REQUEST = bytes([0x82, 0x10, 0x2C, 0xB1, 0x04, 0x13])  # Request, one data object
LONGEST = bytes([0x61, 0x71]) + bytes(range(28))        # header and seven data objects


def lldpdu():
    def tlv(kind, value):
        return bytes([(kind << 1) | (len(value) >> 8), len(value) & 255]) + value
    out = tlv(1, b"\x04" + bytes(6)) + tlv(2, b"\x05Gi1/0/12") + tlv(3, b"\x00\x78")
    out += tlv(4, b"GigabitEthernet1/0/12") + tlv(5, b"switch.example.net")
    out += tlv(6, b"Example switch software, version 1.2.3 " * 3)
    out += tlv(7, b"\x00\x14\x00\x04") + tlv(8, b"\x05\x01\xc0\x00\x02\x01\x02\x00\x00\x00\x01\x00")
    out += tlv(127, b"\x00\x80\xc2\x01\x00\x01")
    out += tlv(127, b"\x00\x12\x0f\x01\x03\x6c\x00\x00\x1e")
    out += tlv(127, b"\x00\x12\x0f\x02\x0f\x01\x04\x53\x00\xff\x00\xff")
    out += tlv(127, b"\x00\x12\x0f\x04\x05\xf2")
    return out + tlv(0, b"")


def table(header, rows):
    widths = [max(len(str(r[i])) for r in [header] + rows) for i in range(len(header))]
    lines = ["  ".join(str(c).ljust(w) for c, w in zip(header, widths)).rstrip()]
    lines.append("  ".join("-" * w for w in widths))
    lines += ["  ".join(str(c).ljust(w) for c, w in zip(r, widths)).rstrip() for r in rows]
    return "\n".join(lines)


def run():
    out = []
    with tempfile.TemporaryDirectory() as tmp:
        elf, (text, data, bss) = build(tmp)

    out.append("Code size, RV32EC, clang -Os")
    out.append(table(["section", "bytes"], [["text and constants", text], ["data", data], ["bss", bss]]))

    # 1. Routines whose cost does not depend on the clock.
    rows = []
    for model in MODELS:
        def put(cpu, blob=b""):
            cpu.write_bytes(SCRATCH, blob)

        for label, message in (("CRC-32 of 6 bytes", REQUEST), ("CRC-32 of 34 bytes", LONGEST + bytes(4))):
            cpu, crc = measure(elf, model, "pd_crc32", SCRATCH, len(message), setup=lambda c, m=message: put(c, m))
            assert crc == zlib.crc32(message)
            rows.append([label, model, cpu.instructions, cpu.cycles])

        for label, message in (("Line-code GoodCRC", bytes([0xA1, 0x03])), ("Line-code longest message", LONGEST)):
            cpu, _ = measure(elf, model, "pd_encode", SCRATCH + 0x100, SCRATCH, len(message),
                             setup=lambda c, m=message: put(c, m))
            nbits = int.from_bytes(cpu.read_bytes(SCRATCH + 0x100, 4), "little")
            packed = cpu.read_bytes(SCRATCH + 0x104, 60)
            got = [(packed[i >> 3] >> (i & 7)) & 1 for i in range(nbits)]
            assert got == pd_bits(message), label
            rows.append([label, model, cpu.instructions, cpu.cycles])

        cpu, _ = measure(elf, model, "pd_edge_isr", SCRATCH)
        rows.append(["Edge interrupt handler body", model, cpu.instructions, cpu.cycles])

        du = lldpdu()
        cpu, r = measure(elf, model, "lldp_parse", SCRATCH, len(du), SCRATCH + 0x400, setup=lambda c: put(c, du))
        found = cpu.read_bytes(SCRATCH + 0x400, 6)
        assert r == 0 and found == bytes([1, 0x53, 0xFF, 0x00, 0xFF, 0x00]), found
        rows.append(["Parse LLDPDU of %d bytes" % len(du), model, cpu.instructions, cpu.cycles])

        cpu, n = measure(elf, model, "lldp_build", SCRATCH + 0x100, SCRATCH, 255,
                         setup=lambda c: put(c, bytes([2, 0, 0, 0, 0, 1])))
        frame = cpu.read_bytes(SCRATCH + 0x100, n)
        assert n == 60 and frame[12:14] == b"\x88\xcc"
        cpu2 = Cpu(elf, model)
        cpu2.write_bytes(SCRATCH, frame[14:])
        assert cpu2.call("lldp_parse", SCRATCH, n - 14, SCRATCH + 0x400) == 0
        assert cpu2.read_bytes(SCRATCH + 0x400, 6) == bytes([1, 0x51, 0xFF, 0x00, 0xFF, 0x00])
        rows.append(["Build LLDP frame of %d bytes" % n, model, cpu.instructions, cpu.cycles])

        cpu, r = measure(elf, model, "soft_mul", 0x12345, 0xFFFFFFFF)
        assert r == (0x12345 * 0xFFFFFFFF) & 0xFFFFFFFF
        rows.append(["32-bit multiply, worst case", model, cpu.instructions, cpu.cycles])
    out.append("\nRoutines")
    out.append(table(["routine", "model", "instructions", "cycles"], rows))

    # 2. Transmit a GoodCRC and check the waveform.
    rows = []
    for model in MODELS:
        for mhz in CLOCKS_MHZ:
            clock = mhz * 1e6
            h0, h1 = halves(clock)
            cpu = Cpu(elf, model)
            cpu.write_bytes(SCRATCH, bytes([0xA1, 0x03]))
            cpu.call("pd_encode", SCRATCH + 0x100, SCRATCH, 2)
            cpu.cycles = 0
            cpu.call("pd_tx", SCRATCH + 0x100, 500, h0, h1)
            edges, level = [], 0
            for cycle, value in cpu.gpio_writes:
                if value != level:
                    edges.append(cycle / clock)
                    level = value
            bit_time = (h0 + h1) / clock
            ok = decode_edges(edges, bit_time) == bytes([0xA1, 0x03]) + zlib.crc32(bytes([0xA1, 0x03])).to_bytes(4, "little")
            ideal = bmc_edges(pd_bits(bytes([0xA1, 0x03])), bit_time, edges[0])
            error = max(abs(a - b) for a, b in zip(edges, ideal)) * 1e9 if len(edges) == len(ideal) else float("nan")
            rows.append([mhz, model, h0 + h1, "%.1f" % (1e-3 / bit_time), "%.0f" % error, "yes" if ok else "NO"])
    out.append("\nTransmit GoodCRC by GPIO writes timed against mcycle")
    out.append(table(["clock MHz", "model", "cycles per bit", "kbit/s", "worst edge error ns", "decodes"], rows))

    # 3. Receive a Request by polling, at the three bit rates.
    rows = []
    for model in MODELS:
        for mhz in CLOCKS_MHZ:
            clock = mhz * 1e6
            results, poll, busy = [], 0, 0
            for rate in BIT_RATES:
                wave = Wave(bmc_edges(pd_bits(REQUEST), 1 / rate, 20e-6), clock)
                cpu = Cpu(elf, model)
                cpu.gpio_in = wave
                r = cpu.call("pd_rx_poll", SCRATCH, round(0.75 * clock / 300e3), round(200e-6 * clock))
                data = cpu.read_bytes(SCRATCH + 8, 10)
                good = r == 0 and data == REQUEST + zlib.crc32(REQUEST).to_bytes(4, "little")
                results.append("ok" if good else "FAIL %d" % r)
                gaps = [b - a for a, b in zip(cpu.gpio_reads, cpu.gpio_reads[1:])]
                poll, busy = min(gaps), max(busy, max(gaps))
            rows.append([mhz, model, poll, "%.2f" % (poll / mhz), busy, "%.2f" % (busy / mhz)] + results)
    out.append("\nReceive a Request by polling")
    out.append(table(["clock MHz", "model", "poll cycles", "poll us", "longest gap cycles", "longest gap us",
                      "270k", "300k", "330k"], rows))

    # 4. Receive and answer with GoodCRC.
    rows = []
    for model in MODELS:
        for mhz in CLOCKS_MHZ:
            clock = mhz * 1e6
            h0, h1 = halves(clock)
            for label, message in (("Request", REQUEST), ("longest", LONGEST)):
                in_edges = bmc_edges(pd_bits(message), 1 / 300e3, 20e-6)
                cpu = Cpu(elf, model)
                cpu.gpio_in = Wave(in_edges, clock)
                marks = {}
                cpu.pc_hooks[elf.symbols["pd_tx"]] = lambda c, m=marks: m.setdefault("ready", c.cycles)
                r = cpu.call("pd_rx_and_ack", round(0.75 * clock / 300e3), round(200e-6 * clock),
                             round(25e-6 * clock), h0, h1)
                if r:
                    rows.append([mhz, model, label, "receive failed", "-", "-"])
                    continue
                end = in_edges[-1]
                edges, level = [], 0
                for cycle, value in cpu.gpio_writes:
                    if value != level:
                        edges.append(cycle / clock)
                        level = value
                ack = bytes([0xA1, 0x01 | (((message[1] >> 1) & 7) << 1)])
                ok = decode_edges(edges, (h0 + h1) / clock) == ack + zlib.crc32(ack).to_bytes(4, "little")
                ready = (marks["ready"] / clock - end) * 1e6
                first = (edges[0] - end) * 1e6
                verdict = "yes" if ok and 25 <= first <= 195 else "NO"
                rows.append([mhz, model, label, "%.1f" % ready, "%.1f" % first, verdict])
    out.append("\nGoodCRC turnaround after the last edge of a received message")
    out.append(table(["clock MHz", "model", "message", "reply ready us", "reply starts us", "within 25 to 195 us"], rows))
    return "\n".join(out) + "\n"


def main():
    text = run()
    sys.stdout.write(text)
    if "--check" in sys.argv:
        with open(os.path.join(HERE, "results.txt")) as f:
            if f.read() != text:
                sys.exit("results.txt is out of date: run python3 bench.py > results.txt")


if __name__ == "__main__":
    main()
