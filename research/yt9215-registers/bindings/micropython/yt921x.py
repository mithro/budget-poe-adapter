# SPDX-License-Identifier: Apache-2.0
"""Motorcomm YT921x Ethernet switch: register access over MDIO and the basic
operations every driver needs.

Works on MicroPython and CPython. The caller supplies a clause-22 MDIO bus:
any object with ``read(phy, reg)`` and ``write(phy, reg, value)`` methods.
:class:`BitBangMDIO` is such a bus on two GPIO pins.
"""
import time

import yt921x_regs as R

_SMI_DATA = 0x2
_SMI_READ = 0x1
_POLL_INTERVAL_MS = 10
_POLL_TIMEOUT_MS = 100

MBUS_INT = 0  # built-in PHYs and SerDes PCS; address = port number
MBUS_EXT = 1  # PHYs on the external MDIO pins


class YT921xError(Exception):
    """The switch did not answer as expected."""


def _sleep_ms(ms):
    if hasattr(time, "sleep_ms"):
        time.sleep_ms(ms)
    else:
        time.sleep(ms / 1000)


class BitBangMDIO:
    """Clause-22 MDIO master on two ``machine.Pin`` objects.

    ``mdc`` must be an output. ``mdio`` is switched between output and input
    and needs a pull-up resistor on the board.
    """

    def __init__(self, mdc, mdio):
        self.mdc = mdc
        self.mdio = mdio
        mdc.value(0)

    def _out(self, value, bits):
        mdio = self.mdio
        mdc = self.mdc
        for i in range(bits - 1, -1, -1):
            mdio.value((value >> i) & 1)
            mdc.value(1)
            mdc.value(0)

    def _start(self, op, phy, reg):
        self.mdio.init(self.mdio.OUT)
        self._out(0xFFFFFFFF, 32)  # preamble
        self._out((0b01 << 12) | (op << 10) | (phy << 5) | reg, 14)

    def write(self, phy, reg, value):
        self._start(0b01, phy, reg)
        self._out(0b10, 2)  # turnaround
        self._out(value, 16)
        self.mdio.init(self.mdio.IN)

    def read(self, phy, reg):
        self._start(0b10, phy, reg)
        mdio = self.mdio
        mdc = self.mdc
        mdio.init(mdio.IN)
        mdc.value(1)  # turnaround: the switch takes over the line
        mdc.value(0)
        value = 0
        for _ in range(17):  # second turnaround bit, then 16 data bits
            value = (value << 1) | mdio.value()
            mdc.value(1)
            mdc.value(0)
        return value & 0xFFFF


class YT921x:
    """One switch on an MDIO bus.

    ``phy_addr`` is the MDIO address the switch answers on (0x1d or 0x00) and
    ``switch_id`` its switch ID (0 unless several switches share the address).
    """

    def __init__(self, mdio, phy_addr=0x1D, switch_id=0):
        self.mdio = mdio
        self.phy_addr = phy_addr
        self._id = (switch_id & 3) << 2

    # ---- register access

    def reg_read(self, addr):
        """Read a 32-bit switch register."""
        m = self.mdio
        p = self.phy_addr
        reg = self._id | _SMI_READ
        m.write(p, reg, addr >> 16)
        m.write(p, reg, addr & 0xFFFF)
        reg |= _SMI_DATA
        hi = m.read(p, reg)
        return (hi << 16) | m.read(p, reg)

    def reg_write(self, addr, value):
        """Write a 32-bit switch register."""
        m = self.mdio
        p = self.phy_addr
        reg = self._id
        m.write(p, reg, addr >> 16)
        m.write(p, reg, addr & 0xFFFF)
        reg |= _SMI_DATA
        m.write(p, reg, (value >> 16) & 0xFFFF)
        m.write(p, reg, value & 0xFFFF)

    def reg_update(self, addr, mask, value):
        """Replace the bits in ``mask`` with those of ``value``."""
        old = self.reg_read(addr)
        new = (old & ~mask) | (value & mask)
        if new != old:
            self.reg_write(addr, new)

    def reg_read_words(self, addr, n):
        """Read a register of ``n`` 32-bit words as a list, low word first."""
        return [self.reg_read(addr + 4 * i) for i in range(n)]

    def reg_write_words(self, addr, words):
        """Write a register of several words in rising address order."""
        for i, word in enumerate(words):
            self.reg_write(addr + 4 * i, word)

    def reg_wait(self, addr, mask, want):
        """Poll until ``(register & mask) == want``; return the register value."""
        waited = 0
        while True:
            v = self.reg_read(addr)
            if v & mask == want:
                return v
            if waited >= _POLL_TIMEOUT_MS:
                raise YT921xError("timeout waiting on register 0x%x" % addr)
            _sleep_ms(_POLL_INTERVAL_MS)
            waited += _POLL_INTERVAL_MS

    # ---- bring-up

    def reset(self):
        """Hardware reset, then a check that register access works."""
        self.reg_write(R.RST, R.RST_HW_M)
        _sleep_ms(R.RST_DELAY_US // 1000)
        self.reg_wait(R.RST, 0xFFFFFFFF, 0)
        tpid = R.fget(self.reg_read(R.CPU_TAG_TPID), R.CPU_TAG_TPID_TPID_M, R.CPU_TAG_TPID_TPID_S)
        if tpid != R.CPU_TAG_TPID_TPID_RESET:
            raise YT921xError("no YT921x at MDIO address 0x%x" % self.phy_addr)

    def edata_read(self, addr):
        """Read one byte of the configuration byte store."""
        idle = R.EDATA_DATA_STATUS_IDLE << R.EDATA_DATA_STATUS_S
        self.reg_wait(R.EDATA_DATA, R.EDATA_DATA_STATUS_M, idle)
        self.reg_write(
            R.EDATA_CTRL,
            (addr << R.EDATA_CTRL_ADDR_S) | (R.EDATA_CTRL_OP_READ << R.EDATA_CTRL_OP_S),
        )
        v = self.reg_wait(R.EDATA_DATA, R.EDATA_DATA_STATUS_M, idle)
        return R.fget(v, R.EDATA_DATA_DATA_M, R.EDATA_DATA_DATA_S)

    def identify(self):
        """Return ``(part, major, minor, mode, extmode)``; ``part`` is the
        matching row of ``yt921x_regs.PARTS``."""
        chip_id = self.reg_read(R.CHIP_ID)
        major = R.fget(chip_id, R.CHIP_ID_MAJOR_M, R.CHIP_ID_MAJOR_S)
        minor = R.fget(chip_id, R.CHIP_ID_MINOR_M, R.CHIP_ID_MINOR_S)
        if major not in (R.MAJOR_YT9215, R.MAJOR_YT9218):
            raise YT921xError("unexpected chip ID 0x%08x" % chip_id)
        mode = R.fget(self.reg_read(R.CHIP_MODE), R.CHIP_MODE_MODE_M, R.CHIP_MODE_MODE_S)
        extmode = self.edata_read(R.EDATA_EXTMODE)
        for part in R.PARTS:
            if part[1] == major and part[2] == mode and part[3] == extmode:
                return part, major, minor, mode, extmode
        raise YT921xError("unknown part: mode %d, extended mode %d" % (mode, extmode))

    # ---- PHY registers through the switch

    def _mbus(self, bus, phy, reg, value):
        if not (0 <= phy <= 31 and 0 <= reg <= 31):
            raise ValueError("PHY address and register must be 0 to 31")
        if bus == MBUS_EXT:
            r_op, r_ctrl, r_dout, r_din = (
                R.EXT_MBUS_OP, R.EXT_MBUS_CTRL, R.EXT_MBUS_DOUT, R.EXT_MBUS_DIN)
        else:
            r_op, r_ctrl, r_dout, r_din = (
                R.INT_MBUS_OP, R.INT_MBUS_CTRL, R.INT_MBUS_DOUT, R.INT_MBUS_DIN)
        # Both masters share one register layout.
        self.reg_wait(r_op, R.INT_MBUS_OP_START_M, 0)
        mask = R.INT_MBUS_CTRL_PORT_M | R.INT_MBUS_CTRL_REG_M | R.INT_MBUS_CTRL_OP_M
        op = R.INT_MBUS_CTRL_OP_READ if value is None else R.INT_MBUS_CTRL_OP_WRITE
        ctrl = ((phy << R.INT_MBUS_CTRL_PORT_S) | (reg << R.INT_MBUS_CTRL_REG_S)
                | (op << R.INT_MBUS_CTRL_OP_S))
        if bus == MBUS_EXT:
            mask |= R.EXT_MBUS_CTRL_TYPE_M
            ctrl |= R.EXT_MBUS_CTRL_TYPE_C22 << R.EXT_MBUS_CTRL_TYPE_S
        self.reg_update(r_ctrl, mask, ctrl)
        if value is not None:
            self.reg_write(r_dout, value & 0xFFFF)
        self.reg_write(r_op, R.INT_MBUS_OP_START_M)
        self.reg_wait(r_op, R.INT_MBUS_OP_START_M, 0)
        if value is None:
            return R.fget(self.reg_read(r_din), R.INT_MBUS_DIN_DATA_M, R.INT_MBUS_DIN_DATA_S)
        return None

    def phy_read(self, phy, reg, bus=MBUS_INT):
        """Read a PHY register through one of the switch's MDIO masters."""
        return self._mbus(bus, phy, reg, None)

    def phy_write(self, phy, reg, value, bus=MBUS_INT):
        """Write a PHY register through one of the switch's MDIO masters."""
        self._mbus(bus, phy, reg, value)

    # ---- port counters

    def mib_read(self, port, offset, words=1):
        """Read one port counter. ``offset`` is a ``yt921x_regs.MIB_*``
        constant and ``words`` its size in 32-bit words (1 or 2)."""
        if not 0 <= port < R.PORT_NUM or words not in (1, 2):
            raise ValueError("bad port or counter size")
        w = self.reg_read_words(R.MIB_DATA(port) + offset, words)
        return w[0] | (w[1] << 32 if words == 2 else 0)
