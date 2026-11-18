// SPDX-License-Identifier: Apache-2.0
//! Tests of the Rust binding against a software model of the switch.
use std::collections::HashMap;

use yt921x::{regs, Delay, Error, Mbus, Mdio, Yt921x};

/// The register interface of a YT921x: the SMI protocol on MDIO,
/// self-clearing reset, the configuration byte store and the MDIO masters.
#[derive(Default)]
struct MockSwitch {
    phy_addr: u8,
    regs: HashMap<u32, u32>,
    smi_addr: u32,
    smi_data: u32,
    addr_phase: bool,
    data_phase: bool,
    edata: HashMap<u8, u8>,
    phy: HashMap<(bool, u8, u8), u16>,
    reset_polls: u32,
    frames: u32,
}

impl MockSwitch {
    fn new(phy_addr: u8, major: u16, mode: u8, extmode: u8) -> Self {
        let mut m = MockSwitch { phy_addr, ..Default::default() };
        m.regs.insert(regs::CHIP_ID, (major as u32) << 16 | 1);
        m.regs.insert(regs::CHIP_MODE, mode as u32);
        m.regs.insert(regs::CPU_TAG_TPID, regs::CPU_TAG_TPID_TPID_RESET);
        m.regs.insert(regs::EDATA_DATA, regs::EDATA_DATA_STATUS_IDLE);
        m.edata.insert(regs::EDATA_EXTMODE as u8, extmode);
        m
    }

    fn reg(&self, addr: u32) -> u32 {
        *self.regs.get(&addr).unwrap_or(&0)
    }

    fn reg_read(&mut self, addr: u32) -> u32 {
        if addr == regs::RST && self.reset_polls > 0 {
            self.reset_polls -= 1;
            if self.reset_polls == 0 {
                self.regs.insert(regs::RST, 0);
            }
        }
        self.reg(addr)
    }

    fn reg_write(&mut self, addr: u32, val: u32) {
        if addr == regs::RST && val & regs::RST_HW.mask() != 0 {
            self.regs.insert(addr, val);
            self.reset_polls = 2;
        } else if addr == regs::EDATA_CTRL {
            let byte = *self.edata.get(&(regs::EDATA_CTRL_ADDR.get(val) as u8)).unwrap_or(&0);
            self.regs
                .insert(regs::EDATA_DATA, (byte as u32) << 24 | regs::EDATA_DATA_STATUS_IDLE);
        } else if (addr == regs::INT_MBUS_OP || addr == regs::EXT_MBUS_OP) && val & 1 != 0 {
            let ext = addr == regs::EXT_MBUS_OP;
            let (r_ctrl, r_dout, r_din) = if ext {
                (regs::EXT_MBUS_CTRL, regs::EXT_MBUS_DOUT, regs::EXT_MBUS_DIN)
            } else {
                (regs::INT_MBUS_CTRL, regs::INT_MBUS_DOUT, regs::INT_MBUS_DIN)
            };
            let ctrl = self.reg(r_ctrl);
            let key = (
                ext,
                regs::INT_MBUS_CTRL_PORT.get(ctrl) as u8,
                regs::INT_MBUS_CTRL_REG.get(ctrl) as u8,
            );
            if regs::INT_MBUS_CTRL_OP.get(ctrl) == regs::INT_MBUS_CTRL_OP_WRITE {
                let v = self.reg(r_dout) as u16;
                self.phy.insert(key, v);
            } else {
                let v = *self.phy.get(&key).unwrap_or(&0);
                self.regs.insert(r_din, v as u32);
            }
        } else {
            self.regs.insert(addr, val);
        }
    }
}

impl Mdio for &mut MockSwitch {
    type Error = ();

    fn read(&mut self, phy: u8, reg: u8) -> Result<u16, ()> {
        self.frames += 1;
        if phy != self.phy_addr || reg > 15 || reg & 3 != 3 {
            return Ok(0xffff);
        }
        if !self.data_phase {
            self.smi_data = self.reg_read(self.smi_addr);
        }
        let v = if self.data_phase { self.smi_data as u16 } else { (self.smi_data >> 16) as u16 };
        self.data_phase = !self.data_phase;
        Ok(v)
    }

    fn write(&mut self, phy: u8, reg: u8, val: u16) -> Result<(), ()> {
        self.frames += 1;
        if phy != self.phy_addr || reg > 15 {
            return Ok(());
        }
        if reg & 2 == 0 {
            self.smi_addr =
                if self.addr_phase { self.smi_addr | val as u32 } else { (val as u32) << 16 };
            self.addr_phase = !self.addr_phase;
            self.data_phase = false;
        } else if reg & 1 == 0 {
            if !self.data_phase {
                self.smi_data = (val as u32) << 16;
            } else {
                let (a, d) = (self.smi_addr, self.smi_data | val as u32);
                self.reg_write(a, d);
            }
            self.data_phase = !self.data_phase;
        }
        Ok(())
    }
}

struct NoDelay;

impl Delay for NoDelay {
    fn delay_us(&mut self, _us: u32) {}
}

#[test]
fn register_access() {
    let mut sw = MockSwitch::new(0x1d, 0x9002, 2, 0);
    {
        let mut dev = Yt921x::new(&mut sw, NoDelay, 0x1d, 0);
        dev.reg_write(regs::port_ctrl(3), 0x1234_5678).unwrap();
        assert_eq!(dev.reg_read(regs::port_ctrl(3)).unwrap(), 0x1234_5678);
        dev.reg_update(
            regs::port_ctrl(3),
            regs::PORT_CTRL_SPEED.mask(),
            regs::PORT_CTRL_SPEED.prep(regs::SPEED_V1000),
        )
        .unwrap();
    }
    assert_eq!(sw.reg(0x8010c), 0x1234_567a);
    // four frames per access: write, read, then read and write of the update
    assert_eq!(sw.frames, 16);
}

#[test]
fn reset_and_identify() {
    let mut sw = MockSwitch::new(0x1d, 0x9002, 2, 0);
    let mut dev = Yt921x::new(&mut sw, NoDelay, 0x1d, 0);
    dev.reset().unwrap();
    let id = dev.identify().unwrap();
    assert_eq!((id.major, id.mode, id.extmode), (0x9002, 2, 0));
    assert_eq!(id.part.name, "YT9215S");
    assert_eq!(id.part.phy_ports, 0x1f);
    assert_eq!(id.part.serdes_ports, 0x100);
}

#[test]
fn wrong_address_is_no_device() {
    let mut sw = MockSwitch::new(0x1d, 0x9002, 2, 0);
    let mut dev = Yt921x::new(&mut sw, NoDelay, 0, 0);
    assert!(dev.reset().is_err());
}

#[test]
fn phy_access() {
    let mut sw = MockSwitch::new(0x1d, 0x9001, 1, 0);
    sw.phy.insert((false, 2, 1), 0x796d);
    {
        let mut dev = Yt921x::new(&mut sw, NoDelay, 0x1d, 0);
        assert_eq!(dev.phy_read(Mbus::Internal, 2, 1).unwrap(), 0x796d);
        dev.phy_write(Mbus::Internal, 4, 0, 0x1200).unwrap();
        dev.phy_write(Mbus::External, 7, 9, 0x0300).unwrap();
        assert_eq!(dev.phy_read(Mbus::Internal, 32, 0), Err(Error::Range));
    }
    assert_eq!(sw.phy[&(false, 4, 0)], 0x1200);
    assert_eq!(sw.phy[&(true, 7, 9)], 0x0300);
    assert_eq!(
        regs::EXT_MBUS_CTRL_TYPE.get(sw.reg(regs::EXT_MBUS_CTRL)),
        regs::EXT_MBUS_CTRL_TYPE_C22
    );
}

#[test]
fn counters_and_wide_registers() {
    let mut sw = MockSwitch::new(0x1d, 0x9002, 1, 0);
    sw.regs.insert(regs::mib_data(1) + regs::MIB_RX_GOOD_BYTES, 0x89ab_cdef);
    sw.regs.insert(regs::mib_data(1) + regs::MIB_RX_GOOD_BYTES + 4, 0x0123_4567);
    let mut words = [0u32; regs::VLAN_CTRL_WORDS];
    regs::VLAN_CTRL_FID.set_words(&mut words, 0xabc);
    words[regs::vlan_ctrl_ports(0).word()] |=
        regs::vlan_ctrl_ports(0).mask() | regs::vlan_ctrl_ports(8).mask();
    assert_eq!(words, [(0xabc << 23) | (1 << 7) | (1 << 15), 0xabc >> 9]);
    assert_eq!(regs::VLAN_CTRL_FID.get_words(&words), 0xabc);
    {
        let mut dev = Yt921x::new(&mut sw, NoDelay, 0x1d, 0);
        assert_eq!(dev.mib_read(1, regs::MIB_RX_GOOD_BYTES, 2).unwrap(), 0x0123_4567_89ab_cdef);
        dev.reg_write_words(regs::vlan_ctrl(100), &words).unwrap();
    }
    assert_eq!(sw.reg(0x188000 + 8 * 100 + 4), 0xabc >> 9);
}

#[test]
fn address_arithmetic() {
    assert_eq!((regs::serdes(8), regs::serdes(9)), (0x8008c, 0x80090));
    assert_eq!(regs::xmii(9), 0x80408);
    assert_eq!((regs::led_ser_map(2, 0), regs::led_ser_map(0, 1)), (0xd0104, 0xd0118));
    assert_eq!(regs::acl_key(47, 7), 0x204000 + 0x200 * 7 + 8 * 47);
    assert_eq!(regs::ipm_pcp(1, 1, 7), 0x180100 + 4 * (16 + 8 + 7));
    assert_eq!((regs::xmii_ctrl_port(8).mask(), regs::xmii_ctrl_port(9).mask()), (2, 1));
    assert_eq!(regs::stp_port(10).prep(regs::STP_PORT_FORWARD), 3 << 20);
    assert_eq!(regs::led_par_inv_inv(2, 9).mask(), 1 << 29);
    assert_eq!(regs::METER_CTRL_CBS.word(), 1);
}
