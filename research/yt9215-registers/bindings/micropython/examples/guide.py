# SPDX-License-Identifier: Apache-2.0
"""The MicroPython examples of the programmer's guide.

Each block between a pair of marker comments is shown in the guide;
tests/test_guide.py runs every one against the software switch model.
"""
import yt921x
import yt921x_regs as R

# [bus]
def open_switch():
    """Bit-bang MDIO on two GPIO pins; the pin numbers depend on the board."""
    from machine import Pin

    mdio = yt921x.BitBangMDIO(mdc=Pin(2), mdio=Pin(3))
    return bringup(mdio)
# [bus end]


# [bringup]
def bringup(mdio):
    """Find the switch on the bus, reset it and identify the part."""
    for addr in (0x1D, 0x00):  # set by a strap pin
        dev = yt921x.YT921x(mdio, phy_addr=addr)
        major = R.fget(dev.reg_read(R.CHIP_ID), R.CHIP_ID_MAJOR_M, R.CHIP_ID_MAJOR_S)
        if major in (R.MAJOR_YT9215, R.MAJOR_YT9218):
            break
    else:
        raise yt921x.YT921xError("no YT921x on the MDIO bus")
    dev.reset()
    part = dev.identify()[0]
    return dev, part
# [bringup end]


# [init]
def init(mdio, cpu_port_num):
    """Bring the switch up as one group of copper ports with a CPU port."""
    dev, part = bringup(mdio)  # find, reset, identify; raises for an unknown part
    phy_ports = part[4]  # mask of the ports with a built-in PHY
    enable_features(dev)
    cpu_port(dev, cpu_port_num)
    port_force(dev, cpu_port_num, R.SPEED_V1000)
    # One group of all copper ports; each may also reach the CPU port.
    port_group(dev, phy_ports, 1 << cpu_port_num)
    return dev, part
# [init end]


# [features]
def enable_features(dev):
    """The Linux driver sets these bits before it uses counters, ACL and meters."""
    bits = R.FUNC_MIB_M | R.FUNC_ACL_M | R.FUNC_METER_M
    dev.reg_update(R.FUNC, bits, bits)
# [features end]


# [cpu-port]
def cpu_port(dev, port):
    """Frames to and from this port carry the 8-byte CPU tag."""
    dev.reg_write(R.EXT_CPU_PORT,
                  R.EXT_CPU_PORT_TAG_EN_M | R.EXT_CPU_PORT_PORT_EN_M
                  | (port << R.EXT_CPU_PORT_PORT_S))
    dev.reg_write(R.CPU_COPY, R.CPU_COPY_TO_EXT_CPU_M)
# [cpu-port end]


# [port-up]
def port_force(dev, port, speed, full_duplex=True):
    """Force the MAC of a port to a speed (an ``R.SPEED_`` code) and enable it."""
    mask = (R.PORT_CTRL_SPEED_M | R.PORT_CTRL_DUPLEX_FULL_M | R.PORT_CTRL_RX_PAUSE_M
            | R.PORT_CTRL_TX_PAUSE_M | R.PORT_CTRL_RX_MAC_EN_M | R.PORT_CTRL_TX_MAC_EN_M
            | R.PORT_CTRL_LINK_AN_M)
    val = speed << R.PORT_CTRL_SPEED_S
    val |= R.PORT_CTRL_RX_MAC_EN_M | R.PORT_CTRL_TX_MAC_EN_M
    if full_duplex:
        val |= R.PORT_CTRL_DUPLEX_FULL_M
    dev.reg_update(R.PORT_CTRL(port), mask, val)


def port_down(dev, port):
    dev.reg_update(R.PORT_CTRL(port),
                   R.PORT_CTRL_LINK_AN_M | R.PORT_CTRL_RX_MAC_EN_M |
                   R.PORT_CTRL_TX_MAC_EN_M, 0)
# [port-up end]


# [port-status]
def port_status(dev, port):
    """Return ``(link, speed code, full duplex)`` of a port."""
    val = dev.reg_read(R.PORT_STATUS(port))
    return (bool(val & R.PORT_STATUS_LINK_M),
            R.fget(val, R.PORT_STATUS_SPEED_M, R.PORT_STATUS_SPEED_S),
            bool(val & R.PORT_STATUS_DUPLEX_FULL_M))
# [port-status end]


# [isolation]
def port_group(dev, members, cpu_ports):
    """Let the ports in ``members`` (a bit mask) talk to each other and the CPU."""
    all_ports = (1 << R.PORT_NUM) - 1
    for port in range(R.PORT_NUM):
        if members & (1 << port):
            allowed = (members | cpu_ports) & ~(1 << port)
            dev.reg_write(R.PORT_ISOLATION(port), all_ports & ~allowed)
# [isolation end]


# [vlan]
def vlan_write(dev, vid, members, untagged):
    """Write one VLAN table entry; ``members`` and ``untagged`` are port masks."""
    entry = [0] * R.VLAN_CTRL_WORDS
    R.bits_set(entry, R.VLAN_CTRL_PORTS_LSB, R.VLAN_CTRL_PORTS_WIDTH, members)
    R.bits_set(entry, R.VLAN_CTRL_UNTAG_PORTS_LSB, R.VLAN_CTRL_UNTAG_PORTS_WIDTH,
               untagged)
    # The words are written in rising address order, low word first.
    dev.reg_write_words(R.VLAN_CTRL(vid), entry)


def port_pvid(dev, port, vid):
    dev.reg_update(R.PORT_VLAN_CTRL(port), R.PORT_VLAN_CTRL_CVID_M,
                   vid << R.PORT_VLAN_CTRL_CVID_S)
# [vlan end]


# [fdb-wait]
def _fdb_run(dev, op):
    dev.reg_write(R.FDB_OP, (op << R.FDB_OP_OP_S) | R.FDB_OP_START_M)
    return dev.reg_wait(R.FDB_RESULT, R.FDB_RESULT_DONE_M, R.FDB_RESULT_DONE_M)


def _fdb_key(dev, mac, fid, status):
    dev.reg_write(R.FDB_IN0, int.from_bytes(mac[0:4], "big"))
    dev.reg_write(R.FDB_IN1, (status << R.FDB_IN1_STATUS_S) | (fid << R.FDB_IN1_FID_S)
                  | int.from_bytes(mac[4:6], "big"))
# [fdb-wait end]


# [fdb-add]
def fdb_add_static(dev, mac, fid, ports):
    """Add a static entry: frames to ``mac`` in ``fid`` go to the ports in ``ports``."""
    _fdb_key(dev, mac, fid, R.FDB_IN1_STATUS_STATIC)
    dev.reg_write(R.FDB_IN2, ports << R.FDB_IN2_EGR_PORTS_S)
    _fdb_run(dev, R.FDB_OP_OP_ADD)
# [fdb-add end]


# [fdb-get]
def fdb_lookup(dev, mac, fid):
    """Return the destination port mask of an address, or 0 when it is not known."""
    _fdb_key(dev, mac, fid, 0)
    dev.reg_write(R.FDB_IN2, 0)
    if _fdb_run(dev, R.FDB_OP_OP_GET_ONE) & R.FDB_RESULT_NOTFOUND_M:
        return 0
    out1 = dev.reg_read(R.FDB_OUT1)
    status = R.fget(out1, R.FDB_OUT1_STATUS_M, R.FDB_OUT1_STATUS_S)
    if status == R.FDB_OUT1_STATUS_INVALID:
        return 0
    out2 = dev.reg_read(R.FDB_OUT2)
    return R.fget(out2, R.FDB_OUT2_EGR_PORTS_M, R.FDB_OUT2_EGR_PORTS_S)
# [fdb-get end]


# [mib]
def port_bytes(dev, port):
    """Return ``(received, sent)`` byte counts of a port."""
    return (dev.mib_read(port, R.MIB_RX_GOOD_BYTES, 2),
            dev.mib_read(port, R.MIB_TX_GOOD_BYTES, 2))
# [mib end]


# [phy]
def phy_link(dev, port):
    """Link state of a built-in PHY. Register 1 is the basic status register;
    link status latches low, so the second read gives the current state."""
    dev.phy_read(port, 1)
    return bool(dev.phy_read(port, 1) & 0x0004)
# [phy end]


# [tag]
TAG_ETHERTYPE = 0x9988


def tag_build(dst_ports, prio=0):
    """The 8 tag bytes of a frame the host sends to the ports in ``dst_ports``."""
    w2 = (1 << 7) | ((prio & 7) << 8)   # code valid, code 0: forward
    w3 = (1 << 15) | (dst_ports & 0x7FF)  # port mask valid
    return bytes((TAG_ETHERTYPE >> 8, TAG_ETHERTYPE & 0xFF, 0, 0,
                  w2 >> 8, w2 & 0xFF, w3 >> 8, w3 & 0xFF))


def tag_parse(tag):
    """Return ``(source port, priority, code)`` of a received tag, or ``None``.
    ``code`` is ``None`` when the tag carries no reason code."""
    w2 = (tag[4] << 8) | tag[5]
    if (tag[0] << 8) | tag[1] != TAG_ETHERTYPE or not w2 & (1 << 15):
        return None
    code = (w2 >> 1) & 0x3F if w2 & (1 << 7) else None
    return (w2 >> 11) & 0xF, (w2 >> 8) & 7, code
# [tag end]
