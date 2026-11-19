# SPDX-License-Identifier: Apache-2.0
"""A software model of the YT921x register interface, for tests.

It models the SMI protocol on MDIO, the self-clearing reset, the
configuration byte store, the two MDIO masters and a forwarding database
that holds one entry. ``MockSwitch`` is the
MDIO bus object that :class:`yt921x.YT921x` talks to; ``MockPins`` puts the
same model behind two bit-banged pins.
"""
import yt921x_regs as R


class MockSwitch:
    def __init__(self, phy_addr=0x1D, major=0x9002, mode=1, extmode=0, switch_id=0):
        self.phy_addr = phy_addr
        self.switch_id = switch_id
        self.regs = {
            R.CHIP_ID: (major << 16) | 1,
            R.CHIP_MODE: mode,
            R.CPU_TAG_TPID: R.CPU_TAG_TPID_TPID_RESET,
            R.EDATA_DATA: R.EDATA_DATA_STATUS_IDLE,
        }
        self.edata = {R.EDATA_EXTMODE: extmode}
        self.phy = {}  # (ext, phy, reg) -> value
        self.fdb = None  # the one stored entry, as (IN0, IN1, IN2)
        self.frames = 0
        self._addr = 0
        self._data = 0
        self._addr_phase = 0
        self._data_phase = 0
        self._reset_polls = 0

    # ---- register side

    def reg_read(self, addr):
        if addr == R.RST and self._reset_polls:
            self._reset_polls -= 1
            if not self._reset_polls:
                self.regs[R.RST] = 0
        return self.regs.get(addr, 0)

    def reg_write(self, addr, value):
        if addr == R.RST and value & R.RST_HW_M:
            self.regs[addr] = value
            self._reset_polls = 2
        elif addr == R.FDB_OP and value & R.FDB_OP_START_M:
            self._fdb(value)
        elif addr == R.EDATA_CTRL:
            byte = self.edata.get(R.fget(value, R.EDATA_CTRL_ADDR_M, R.EDATA_CTRL_ADDR_S), 0)
            self.regs[R.EDATA_DATA] = (byte << 24) | R.EDATA_DATA_STATUS_IDLE
        elif addr in (R.INT_MBUS_OP, R.EXT_MBUS_OP) and value & 1:
            ext = addr == R.EXT_MBUS_OP
            ctrl = self.regs.get(R.EXT_MBUS_CTRL if ext else R.INT_MBUS_CTRL, 0)
            key = (ext,
                   R.fget(ctrl, R.INT_MBUS_CTRL_PORT_M, R.INT_MBUS_CTRL_PORT_S),
                   R.fget(ctrl, R.INT_MBUS_CTRL_REG_M, R.INT_MBUS_CTRL_REG_S))
            op = R.fget(ctrl, R.INT_MBUS_CTRL_OP_M, R.INT_MBUS_CTRL_OP_S)
            if op == R.INT_MBUS_CTRL_OP_WRITE:
                self.phy[key] = self.regs.get(R.EXT_MBUS_DOUT if ext else R.INT_MBUS_DOUT, 0)
            else:
                self.regs[R.EXT_MBUS_DIN if ext else R.INT_MBUS_DIN] = self.phy.get(key, 0)
        else:
            self.regs[addr] = value

    def _fdb(self, op):
        key1 = R.FDB_IN1_FID_M | R.FDB_IN1_ADDR_LO2_M
        in0, in1 = self.regs.get(R.FDB_IN0, 0), self.regs.get(R.FDB_IN1, 0)
        result = R.FDB_RESULT_DONE_M
        op = R.fget(op, R.FDB_OP_OP_M, R.FDB_OP_OP_S)
        if op == R.FDB_OP_OP_ADD:
            self.fdb = (in0, in1, self.regs.get(R.FDB_IN2, 0))
        elif op == R.FDB_OP_OP_GET_ONE:
            if self.fdb and self.fdb[0] == in0 and self.fdb[1] & key1 == in1 & key1:
                self.regs[R.FDB_OUT0], self.regs[R.FDB_OUT1], self.regs[R.FDB_OUT2] = self.fdb
            else:
                result |= R.FDB_RESULT_NOTFOUND_M
        else:
            self.fdb = None
        self.regs[R.FDB_RESULT] = result

    # ---- MDIO side

    def _mine(self, phy, reg):
        return phy == self.phy_addr and reg <= 15 and (reg >> 2) & 3 == self.switch_id

    def read(self, phy, reg):
        self.frames += 1
        if not self._mine(phy, reg) or reg & 3 != 3:
            return 0xFFFF
        if not self._data_phase:
            self._data = self.reg_read(self._addr)
        v = self._data & 0xFFFF if self._data_phase else self._data >> 16
        self._data_phase ^= 1
        return v

    def write(self, phy, reg, value):
        self.frames += 1
        if not self._mine(phy, reg):
            return
        if not reg & 2:
            self._addr = (self._addr | value) if self._addr_phase else value << 16
            self._addr_phase ^= 1
            self._data_phase = 0
        elif not reg & 1:
            if not self._data_phase:
                self._data = value << 16
            else:
                self.reg_write(self._addr, self._data | value)
            self._data_phase ^= 1


class MockPin:
    """One of the two pins of :class:`MockPins`."""

    IN = 0
    OUT = 1

    def __init__(self, bus, is_clock):
        self.bus = bus
        self.is_clock = is_clock
        self.mode = self.OUT
        self.level = 1

    def init(self, mode):
        self.mode = mode

    def value(self, v=None):
        if v is None:
            return self.bus.sample() if self.mode == self.IN else self.level
        if self.is_clock and v and not self.level:
            self.bus.rising_edge()
        self.level = v
        return None


class MockPins:
    """Decodes clause-22 frames from MDC and MDIO pin activity and passes them
    to a :class:`MockSwitch`."""

    def __init__(self, switch):
        self.switch = switch
        self.mdc = MockPin(self, True)
        self.mdio = MockPin(self, False)
        self.ones = 0
        self.bits = None  # bits received since the start of frame
        self.reply = None  # bits the switch drives during a read

    def sample(self):
        if self.reply:
            return self.reply[0]
        return 1  # pulled up

    def rising_edge(self):
        if self.reply is not None:
            # the host samples before each rising edge; advance afterwards
            self.reply = self.reply[1:] or None
            return
        bit = self.mdio.level if self.mdio.mode == MockPin.OUT else 1
        if self.bits is None:
            if bit:
                self.ones += 1
            elif self.ones >= 32:
                self.bits = [0]
            return
        self.bits.append(bit)
        n = len(self.bits)
        if n == 14:
            st_op = self.bits[1:4]
            if st_op == [1, 1, 0]:  # start 01, read 10
                phy, reg = self._addr()
                v = self.switch.read(phy, reg)
                # turnaround Z then 0, then data, seen from the host as
                # one ignored bit followed by 17 sampled bits
                self.reply = [1, 0] + [(v >> i) & 1 for i in range(15, -1, -1)]
                self.bits = None
                self.ones = 0
        elif n == 32:
            phy, reg = self._addr()
            v = 0
            for b in self.bits[16:]:
                v = (v << 1) | b
            self.switch.write(phy, reg, v)
            self.bits = None
            self.ones = 0

    def _addr(self):
        phy = reg = 0
        for b in self.bits[4:9]:
            phy = (phy << 1) | b
        for b in self.bits[9:14]:
            reg = (reg << 1) | b
        return phy, reg
