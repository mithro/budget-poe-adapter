# SPDX-License-Identifier: Apache-2.0
"""Tests of the MicroPython binding against the software switch model.

Runs under CPython (``python3 -m unittest``) and under MicroPython's unittest.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

import yt921x  # noqa: E402
import yt921x_regs as R  # noqa: E402
from mock_switch import MockPins, MockSwitch  # noqa: E402


class RegisterAccess(unittest.TestCase):
    def setUp(self):
        self.sw = MockSwitch(major=0x9002, mode=2)
        self.dev = yt921x.YT921x(self.sw)

    def test_read_write_update(self):
        self.dev.reg_write(R.PORT_CTRL(3), 0x12345678)
        self.assertEqual(self.sw.frames, 4)
        self.assertEqual(self.sw.regs[0x8010C], 0x12345678)
        self.assertEqual(self.dev.reg_read(R.PORT_CTRL(3)), 0x12345678)
        self.dev.reg_update(R.PORT_CTRL(3), R.PORT_CTRL_SPEED_M,
                            R.SPEED_V1000 << R.PORT_CTRL_SPEED_S)
        self.assertEqual(self.sw.regs[0x8010C], 0x1234567A)

    def test_reset_and_identify(self):
        self.dev.reset()
        part, major, minor, mode, extmode = self.dev.identify()
        self.assertEqual((part[0], major, mode, extmode), ("YT9215S", 0x9002, 2, 0))
        self.assertEqual(part[4], 0x1F)

    def test_wrong_address(self):
        dev = yt921x.YT921x(self.sw, phy_addr=0)
        with self.assertRaises(yt921x.YT921xError):
            dev.reset()

    def test_phy_access(self):
        self.sw.phy[(False, 2, 1)] = 0x796D
        self.assertEqual(self.dev.phy_read(2, 1), 0x796D)
        self.dev.phy_write(4, 0, 0x1200)
        self.assertEqual(self.sw.phy[(False, 4, 0)], 0x1200)
        self.dev.phy_write(7, 9, 0x0300, bus=yt921x.MBUS_EXT)
        self.assertEqual(self.sw.phy[(True, 7, 9)], 0x0300)
        with self.assertRaises(ValueError):
            self.dev.phy_read(32, 0)

    def test_counters_and_wide_registers(self):
        self.sw.regs[R.MIB_DATA(1) + R.MIB_RX_GOOD_BYTES] = 0x89ABCDEF
        self.sw.regs[R.MIB_DATA(1) + R.MIB_RX_GOOD_BYTES + 4] = 0x01234567
        self.assertEqual(self.dev.mib_read(1, R.MIB_RX_GOOD_BYTES, 2), 0x0123456789ABCDEF)
        words = [0] * R.VLAN_CTRL_WORDS
        R.bits_set(words, R.VLAN_CTRL_FID_LSB, R.VLAN_CTRL_FID_WIDTH, 0xABC)
        words[R.VLAN_CTRL_PORTS_W] |= R.VLAN_CTRL_PORTS_M(0) | R.VLAN_CTRL_PORTS_M(8)
        self.assertEqual(words, [(0xABC << 23) & 0xFFFFFFFF | (1 << 7) | (1 << 15), 0xABC >> 9])
        self.assertEqual(R.bits_get(words, R.VLAN_CTRL_FID_LSB, R.VLAN_CTRL_FID_WIDTH), 0xABC)
        self.dev.reg_write_words(R.VLAN_CTRL(100), words)
        self.assertEqual(self.sw.regs[0x188000 + 8 * 100 + 4], 0xABC >> 9)

    def test_address_arithmetic(self):
        self.assertEqual((R.SERDES(8), R.SERDES(9)), (0x8008C, 0x80090))
        self.assertEqual(R.XMII(9), 0x80408)
        self.assertEqual((R.LED_SER_MAP(2, 0), R.LED_SER_MAP(0, 1)), (0xD0104, 0xD0118))
        self.assertEqual(R.ACL_KEY(47, 7), 0x204000 + 0x200 * 7 + 8 * 47)
        self.assertEqual((R.XMII_CTRL_PORT_M(8), R.XMII_CTRL_PORT_M(9)), (2, 1))
        self.assertEqual(R.STP_PORT_FORWARD << R.STP_PORT_S(10), 3 << 20)
        self.assertEqual(R.LED_PAR_INV_INV_M(2, 9), 1 << 29)


class BitBang(unittest.TestCase):
    def test_frames_on_pins(self):
        sw = MockSwitch(major=0x9001, mode=1)
        pins = MockPins(sw)
        dev = yt921x.YT921x(yt921x.BitBangMDIO(pins.mdc, pins.mdio))
        dev.reg_write(R.AGEING, 60)
        self.assertEqual(sw.regs[R.AGEING], 60)
        self.assertEqual(dev.reg_read(R.CHIP_ID) >> 16, 0x9001)
        dev.reset()
        self.assertEqual(dev.identify()[0][0], "YT9218MB")


if __name__ == "__main__":
    unittest.main()
