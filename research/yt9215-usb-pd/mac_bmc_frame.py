#!/usr/bin/env python3
"""Build the Ethernet frame whose RGMII TXD1 pin carries a USB PD message as BMC.

At 10 Mbit/s an RGMII or MII port sends one nibble every 400 ns. TXD1 carries bit 1 and
then bit 5 of every byte, so two equal bytes hold TXD1 at one level for 1.6 us, which is
one BMC half bit at 312.5 kbit/s. The script

* encodes a PD message (preamble, SOP, 4b5b data, CRC-32, EOP) as BMC half bits,
* writes each half bit as two bytes, 0x22 for high and 0x00 for low,
* ends the message as PD requires: the last bit is closed by an edge, then the line is
  low until it is released,
* appends four bytes chosen so that TXD1 stays low through them and through the frame
  check sequence that the MAC appends, and
* checks the result by replaying the frame nibble by nibble with a decoder that needs
  the closing edge.

Run it without arguments to print a table of frame sizes for the messages a minimal
source sends, for every MessageID. The decoder uses the same symbol tables as the encoder,
so the check covers the frame arithmetic, not the tables.
"""
import zlib

NIBBLE_NS = 400                 # one nibble at 10 Mbit/s
NIBBLES_PER_HALF_BIT = 4        # 1.6 us per BMC half bit
HIGH, LOW = 0x22, 0x00          # bytes that put 1 or 0 on TXD1 for both nibbles

SYM = [0x1E, 0x09, 0x14, 0x15, 0x0A, 0x0B, 0x0E, 0x0F,
       0x12, 0x13, 0x16, 0x17, 0x1A, 0x1B, 0x1C, 0x1D]
SYNC1, SYNC2, EOP = 0x18, 0x11, 0x0D
RST1, RST2 = 0x07, 0x19
GOODCRC, ACCEPT, PS_RDY, SOURCE_CAP = 1, 3, 6, 1
PDO_5V_5A = 0x080191F4          # fixed 5 V, 5 A, unconstrained power


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


def hard_reset_bits():
    """Bits of the Hard Reset ordered set, which has no payload, CRC or EOP."""
    bits = [i & 1 for i in range(64)]
    for s in (RST1, RST1, RST1, RST2):
        bits += [(s >> i) & 1 for i in range(5)]
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
    if not level:                                           # a low last half bit gets a
        out += [1, 1]                                       # high bit time as closing edge
    return out                                              # the low tail follows in the frame


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


def frame_for(bits):
    half_bits = bmc_half_bits(bits)
    body = bytes(b for h in half_bits for b in [HIGH if h else LOW] * 2)
    return body + quiet_tail(body), half_bits


def decode_bits(levels):
    """Recover the PD bits from TXD1 levels sampled once per nibble.

    Only runs that end with an edge count, so the last bit must be closed by an edge.
    """
    runs, last, n = [], 0, 0
    for lv in levels:
        if lv == last:
            n += 1
        else:
            runs.append(n)
            last, n = lv, 1
    assert last == 0, "the line must end low"
    halves = [x / NIBBLES_PER_HALF_BIT for x in runs[1:]]
    assert all(h in (1, 2) for h in halves), "run length"
    bits, i = [], 0
    while i < len(halves):
        if halves[i] == 2:
            bits.append(0)
            i += 1
        else:
            assert halves[i + 1] == 1, "half bit pair"
            bits.append(1)
            i += 2
    return bits


def decode_payload(bits):
    """Header and data objects of an SOP message, after checking SOP, EOP and CRC."""
    bits = bits[64:]
    symbols = [sum(bits[k + j] << j for j in range(5)) for k in range(0, len(bits) - 4, 5)]
    assert symbols[:4] == [SYNC1, SYNC1, SYNC1, SYNC2], "SOP"
    end = symbols.index(EOP)
    nibbles = [SYM.index(x) for x in symbols[4:end]]
    data = bytes(nibbles[k] | nibbles[k + 1] << 4 for k in range(0, len(nibbles), 2))
    assert zlib.crc32(data[:-4]).to_bytes(4, "little") == data[-4:], "CRC"
    return data[:-4]


def header(msg_type, message_id, objects=0):
    """Header of a message from a source and DFP at PD revision 3."""
    return msg_type | 1 << 5 | 2 << 6 | 1 << 8 | message_id << 9 | objects << 12


def check(bits):
    """Frame length in bytes with FCS, after replaying the frame on TXD1."""
    frame, _ = frame_for(bits)
    wire = frame + fcs(frame)
    levels = [0] * 16 + txd1(wire)                # TXD1 is low during preamble and SFD
    got = decode_bits(levels)
    assert got[:len(bits)] == bits and not any(got[len(bits):]), "bits"
    assert not any(txd1(wire[-8:])), "TXD1 must stay low in the tail"
    return len(wire), got


def wire_time(size):
    return "%.0f us" % ((size + 8) * 2 * NIBBLE_NS / 1000)


def main():
    print("BMC bit rate %.1f kbit/s, one nibble every %d ns"
          % (1e6 / (2 * NIBBLES_PER_HALF_BIT * NIBBLE_NS), NIBBLE_NS))
    print("%-22s %8s %8s  %s" % ("Message", "PD bits", "Longest", "Frame bytes with FCS, MessageID 0 to 7"))
    kinds = [("GoodCRC", GOODCRC, ()), ("Accept", ACCEPT, ()), ("PS_RDY", PS_RDY, ()),
             ("Source_Capabilities", SOURCE_CAP, (PDO_5V_5A,))]
    for name, msg_type, objects in kinds:
        sizes = []
        for message_id in range(8):
            h = header(msg_type, message_id, len(objects))
            bits = pd_bits(h, objects)
            size, got = check(bits)
            payload = h.to_bytes(2, "little") + b"".join(o.to_bytes(4, "little") for o in objects)
            assert decode_payload(got) == payload
            sizes.append(size)
        print("%-22s %8d %8s  %s" % (name, len(bits), wire_time(max(sizes)), " ".join(map(str, sizes))))
    bits = hard_reset_bits()
    size, _ = check(bits)
    print("%-22s %8d %8s  %d" % ("Hard Reset", len(bits), wire_time(size), size))
    print("Longest is the time on the wire of the longest frame, with its Ethernet preamble.")
    print("All checks passed.")


if __name__ == "__main__":
    main()
