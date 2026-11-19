# SPDX-License-Identifier: Apache-2.0
"""Runs every example of the guide (examples/guide.py) against the switch model."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "examples"))

import guide  # noqa: E402
import yt921x_regs as R  # noqa: E402
from mock_switch import MockSwitch  # noqa: E402


class GuideExamples(unittest.TestCase):
    def setUp(self):
        self.sw = MockSwitch(phy_addr=0x00, major=0x9002, mode=1)
        self.dev, self.part = guide.bringup(self.sw)

    def test_bringup_finds_address_zero(self):
        self.assertEqual(self.dev.phy_addr, 0)
        self.assertEqual(self.part[0], "YT9215SC")

    def test_init(self):
        sw = MockSwitch(phy_addr=0x1D, major=0x9002, mode=2)
        dev, part = guide.init(sw, 8)
        self.assertEqual(part[0], "YT9215S")
        self.assertEqual(sw.regs[R.FUNC], 0x16)
        self.assertEqual(sw.regs[R.EXT_CPU_PORT], 0xC008)
        self.assertEqual(sw.regs[R.PORT_CTRL(8)] & 0xFF, 0x9A)
        self.assertEqual(sw.regs[R.PORT_ISOLATION(0)], 0x7FF & ~0x11E)

    def test_features_and_cpu_port(self):
        guide.enable_features(self.dev)
        self.assertEqual(self.sw.regs[R.FUNC], 0x16)
        guide.cpu_port(self.dev, 8)
        self.assertEqual(self.sw.regs[R.EXT_CPU_PORT], 0xC008)
        self.assertEqual(self.sw.regs[R.CPU_COPY], 1)

    def test_ports(self):
        self.sw.regs[R.PORT_CTRL(8)] = 0x200
        guide.port_force(self.dev, 8, R.SPEED_V1000)
        self.assertEqual(self.sw.regs[R.PORT_CTRL(8)], 0x9A)
        guide.port_down(self.dev, 8)
        self.assertEqual(self.sw.regs[R.PORT_CTRL(8)], 0x82)
        self.sw.regs[R.PORT_STATUS(2)] = 0x181
        self.assertEqual(guide.port_status(self.dev, 2), (True, R.SPEED_V100, True))

    def test_isolation(self):
        guide.port_group(self.dev, 0x007, 0x100)
        self.assertEqual(self.sw.regs[R.PORT_ISOLATION(0)], 0x7FF & ~0x106)
        self.assertEqual(self.sw.regs[R.PORT_ISOLATION(2)], 0x7FF & ~0x103)

    def test_vlan(self):
        guide.vlan_write(self.dev, 100, 0x107, 0x003)
        self.assertEqual(self.sw.regs[R.VLAN_CTRL(100)], 0x107 << 7)
        self.assertEqual(self.sw.regs[R.VLAN_CTRL(100) + 4], 0x003 << 8)
        guide.port_pvid(self.dev, 1, 100)
        self.assertEqual(self.sw.regs[R.PORT_VLAN_CTRL(1)], 100 << 6)

    def test_fdb(self):
        mac = bytes((0x02, 0x11, 0x22, 0x33, 0x44, 0x55))
        guide.fdb_add_static(self.dev, mac, 100, 0x004)
        self.assertEqual(guide.fdb_lookup(self.dev, mac, 100), 0x004)
        self.assertEqual(guide.fdb_lookup(self.dev, mac, 101), 0)
        self.assertEqual(guide.fdb_lookup(self.dev, mac[:5] + b"\x56", 100), 0)

    def test_counters_and_phy(self):
        self.sw.regs[R.MIB_DATA(3) + R.MIB_RX_GOOD_BYTES] = 0x89ABCDEF
        self.sw.regs[R.MIB_DATA(3) + R.MIB_RX_GOOD_BYTES + 4] = 1
        self.sw.regs[R.MIB_DATA(3) + R.MIB_TX_GOOD_BYTES] = 42
        self.assertEqual(guide.port_bytes(self.dev, 3), (0x189ABCDEF, 42))
        self.sw.phy[(False, 4, 1)] = 0x796D
        self.assertTrue(guide.phy_link(self.dev, 4))
        self.assertFalse(guide.phy_link(self.dev, 3))

    def test_tag(self):
        self.assertEqual(guide.tag_build(0x005, 3), bytes((0x99, 0x88, 0, 0, 0x03, 0x80, 0x80, 0x05)))
        rx = bytes((0x99, 0x88, 0, 0, 0x80 | (2 << 3) | 5, 0x80 | (0x19 << 1), 0, 0))
        self.assertEqual(guide.tag_parse(rx), (2, 5, 0x19))
        self.assertIsNone(guide.tag_parse(b"\x81\x00" + rx[2:]))


if __name__ == "__main__":
    unittest.main()
