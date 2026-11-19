#!/usr/bin/env python3
"""Build the Ethernet frame whose RGMII TXD1 pin carries a USB PD message as BMC.

At 10 Mbit/s an RGMII or MII port sends one nibble every 400 ns. TXD1 carries bit 1 and
then bit 5 of every byte, so two equal bytes hold TXD1 at one level for 1.6 us, which is
one BMC half bit at 312.5 kbit/s. The script

* encodes a PD message (preamble, SOP, 4b5b data, CRC-32, EOP) as BMC half bits,
* writes each half bit as two bytes, 0x22 for high and 0x00 for low,
* appends four bytes chosen so that TXD1 stays low through them and through the frame
  check sequence that the MAC appends, and
* checks the result by replaying the frame nibble by nibble.

Run it without arguments to print the frame for a GoodCRC message and the check results.
"""
import sys
import zlib

NIBBLE_NS = 400                 # one nibble at 10 Mbit/s
NIBBLES_PER_HALF_BIT = 4        # 1.6 us per BMC half bit
HIGH, LOW = 0x22, 0x00          # bytes that put 1 or 0 on TXD1 for both nibbles

SYM = [0x1E, 0x09, 0x14, 0x15, 0x0A, 0x0B, 0x0E, 0x0F,
       0x12, 0x13, 0x16, 0x17, 0x1A, 0x1B, 0x1C, 0x1D]
SYNC1, SYNC2, EOP = 0x18, 0x11, 0x0D
GOODCRC = 1


def pd_bits(header, objects=()):
    """Bits of one SOP message in wire order."""
    payload = header.to_bytes(2, "little") + b"".join(o.to_bytes(4, "little") for o in objects)
    payload += zlib.crc32(payload).to_bytes(4, "little")
    bits = [i & 1 for i in range(64)]                       # preamble 0101...
    symbols = [SYNC1, SYNC1, SYNC1, SYNC2]
    for byte in payload:
        symbols += [SYM[byte & 15], SYM[byte >> 4]]
    symbols.append(EOP)
    for s in symbols:
        bits += [(s >> i) & 1 for i in range(5)]            # LSB first
    return bits


def bmc_half_bits(bits):
    """BMC levels, two per bit. The line is low before the first bit."""
    level, out = 0, []
    for b in bits:
        level ^= 1                                          # edge at every bit start
        out.append(level)
        if b:
            level ^= 1                                      # extra edge in the middle of a 1
        out.append(level)
    if level:                                               # end on a low level
        out += [0, 0]
    return out


def txd1(frame):
    """Levels of TXD1, one per nibble, low nibble first."""
    out = []
    for byte in frame:
        out += [(byte >> 1) & 1, (byte >> 5) & 1]
    return out


def fcs(frame):
    return zlib.crc32(frame).to_bytes(4, "little")


def quiet_tail(body):
    """Four bytes after which TXD1 is low for those bytes and for the FCS.

    The FCS is an affine function of the four bytes over GF(2). The bytes may use the six
    bits that TXD1 does not carry, which leaves 24 unknowns for 8 conditions; Gaussian
    elimination finds a solution.
    """
    free = [(i, b) for i in range(4) for b in (0, 2, 3, 4, 6, 7)]

    def cond(tail):
        f = fcs(body + bytes(tail))
        return [(f[i] >> b) & 1 for i in range(4) for b in (1, 5)]

    base = cond([0, 0, 0, 0])
    cols = []
    for i, b in free:
        tail = [0, 0, 0, 0]
        tail[i] = 1 << b
        cols.append([x ^ y for x, y in zip(cond(tail), base)])
    rows = [[cols[c][r] for c in range(len(free))] + [base[r]] for r in range(8)]
    pivots, r = [], 0
    for c in range(len(free)):
        p = next((k for k in range(r, 8) if rows[k][c]), None)
        if p is None:
            continue
        rows[r], rows[p] = rows[p], rows[r]
        for k in range(8):
            if k != r and rows[k][c]:
                rows[k] = [x ^ y for x, y in zip(rows[k], rows[r])]
        pivots.append(c)
        r += 1
        if r == 8:
            break
    if r < 8:
        raise ValueError("no solution")
    tail = [0, 0, 0, 0]
    for row, c in zip(rows, pivots):
        if row[-1]:
            i, b = free[c]
            tail[i] |= 1 << b
    return bytes(tail)


def frame_for(header, objects=()):
    half_bits = bmc_half_bits(pd_bits(header, objects))
    body = bytes(b for h in half_bits for b in [HIGH if h else LOW] * 2)
    return body + quiet_tail(body), half_bits


def decode(levels):
    """Recover the PD payload from TXD1 levels sampled once per nibble."""
    runs, last, n = [], 0, 0
    for lv in levels:
        if lv == last:
            n += 1
        else:
            runs.append(n)
            last, n = lv, 1
    runs.append(n)                                          # the low tail closes the last bit
    halves = [min(2, round(x / NIBBLES_PER_HALF_BIT)) for x in runs[1:]]
    bits, i = [], 0
    while i < len(halves):
        if halves[i] == 2:
            bits.append(0)
            i += 1
        else:
            bits.append(1)
            i += 2
    bits = bits[64:]
    symbols = [sum(bits[k + j] << j for j in range(5)) for k in range(0, len(bits) - 4, 5)]
    assert symbols[:4] == [SYNC1, SYNC1, SYNC1, SYNC2], "SOP"
    end = symbols.index(EOP)
    nibbles = [SYM.index(s) for s in symbols[4:end]]
    data = bytes(nibbles[k] | nibbles[k + 1] << 4 for k in range(0, len(nibbles), 2))
    assert zlib.crc32(data[:-4]).to_bytes(4, "little") == data[-4:], "CRC"
    return data[:-4]


def main():
    message_id = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    # GoodCRC from a source and DFP at PD revision 3.
    header = GOODCRC | 1 << 5 | 2 << 6 | 1 << 8 | message_id << 9
    frame, half_bits = frame_for(header)
    wire = frame + fcs(frame)
    levels = [0] * 16 + txd1(wire)                # TXD1 is low during preamble and SFD
    assert decode(levels) == header.to_bytes(2, "little")
    tail = txd1(wire[-8:])
    assert not any(tail), "TXD1 must stay low in the tail"
    bits = len(pd_bits(header))
    print("PD header            0x%04x (GoodCRC, MessageID %d)" % (header, message_id))
    print("PD bits on the wire  %d" % bits)
    print("BMC half bits        %d" % len(half_bits))
    print("Frame without FCS    %d bytes" % len(frame))
    print("Tail bytes           %s" % frame[-4:].hex(" "))
    print("FCS from the MAC     %s" % fcs(frame).hex(" "))
    print("Time on the wire     %.1f us" % ((len(wire) + 8) * 2 * NIBBLE_NS / 1000))
    print("BMC bit rate         %.1f kbit/s" % (1e6 / (2 * NIBBLES_PER_HALF_BIT * NIBBLE_NS)))
    print("Checks passed: the frame decodes to the header and TXD1 is low in the tail.")


if __name__ == "__main__":
    main()
