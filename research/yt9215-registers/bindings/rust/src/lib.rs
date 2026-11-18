// SPDX-License-Identifier: Apache-2.0
//! Motorcomm YT921x Ethernet switch: register definitions and the basic
//! operations every driver needs.
//!
//! The crate is `no_std` and has no dependencies. The caller supplies a
//! clause-22 MDIO bus ([`Mdio`]) and a delay ([`Delay`]).
//!
//! ```
//! use yt921x::{regs, Field};
//!
//! // Address of the control register of port 3 and a field value for it.
//! assert_eq!(regs::port_ctrl(3), 0x8010c);
//! assert_eq!(regs::PORT_CTRL_SPEED.prep(regs::SPEED_V1000), 2);
//! let f: Field = regs::stp_port(10);
//! assert_eq!(f.mask(), 3 << 20);
//! ```
#![no_std]
#![forbid(unsafe_code)]
#![warn(missing_docs)]

pub mod regs;

pub use regs::{Field, Part};

/// A clause-22 MDIO bus master.
pub trait Mdio {
    /// Error of the bus.
    type Error;
    /// Read register `reg` of PHY address `phy`.
    fn read(&mut self, phy: u8, reg: u8) -> Result<u16, Self::Error>;
    /// Write register `reg` of PHY address `phy`.
    fn write(&mut self, phy: u8, reg: u8, val: u16) -> Result<(), Self::Error>;
}

/// A blocking delay.
pub trait Delay {
    /// Wait at least `us` microseconds.
    fn delay_us(&mut self, us: u32);
}

/// Errors of the access layer.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Error<E> {
    /// The MDIO bus failed.
    Bus(E),
    /// The switch did not finish an operation in time.
    Timeout,
    /// No YT921x answered, or the part is not in the part table.
    NoDevice,
    /// An argument is out of range.
    Range,
}

impl<E> From<E> for Error<E> {
    fn from(e: E) -> Self {
        Error::Bus(e)
    }
}

/// Which MDIO master of the switch a PHY sits on.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Mbus {
    /// Built-in PHYs and SerDes PCS; the address equals the port number.
    Internal,
    /// PHYs on the external MDIO pins.
    External,
}

/// What [`Yt921x::identify`] read from the chip.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Id {
    /// `CHIP_ID.MAJOR`
    pub major: u16,
    /// `CHIP_ID.MINOR`
    pub minor: u16,
    /// `CHIP_MODE.MODE`
    pub mode: u8,
    /// Extended mode byte of the configuration byte store.
    pub extmode: u8,
    /// The matching row of [`regs::PARTS`].
    pub part: &'static Part,
}

const SMI_DATA: u8 = 0x2;
const SMI_READ: u8 = 0x1;
const POLL_INTERVAL_US: u32 = 10_000;
const POLL_TIMEOUT_US: u32 = 100_000;

/// One switch on an MDIO bus.
pub struct Yt921x<M, D> {
    mdio: M,
    delay: D,
    phy_addr: u8,
    switch_id: u8,
}

impl<M: Mdio, D: Delay> Yt921x<M, D> {
    /// `phy_addr` is the MDIO address the switch answers on (0x1d or 0x00)
    /// and `switch_id` its switch ID (0 unless several switches share the
    /// address).
    pub fn new(mdio: M, delay: D, phy_addr: u8, switch_id: u8) -> Self {
        Self { mdio, delay, phy_addr, switch_id: switch_id & 3 }
    }

    /// Give the bus and the delay back.
    pub fn release(self) -> (M, D) {
        (self.mdio, self.delay)
    }

    fn smi_addr(&mut self, addr: u32, rw: u8) -> Result<(), Error<M::Error>> {
        let reg = (self.switch_id << 2) | rw;
        self.mdio.write(self.phy_addr, reg, (addr >> 16) as u16)?;
        self.mdio.write(self.phy_addr, reg, addr as u16)?;
        Ok(())
    }

    /// Read a 32-bit switch register.
    pub fn reg_read(&mut self, addr: u32) -> Result<u32, Error<M::Error>> {
        self.smi_addr(addr, SMI_READ)?;
        let reg = (self.switch_id << 2) | SMI_DATA | SMI_READ;
        let hi = self.mdio.read(self.phy_addr, reg)? as u32;
        let lo = self.mdio.read(self.phy_addr, reg)? as u32;
        Ok((hi << 16) | lo)
    }

    /// Write a 32-bit switch register.
    pub fn reg_write(&mut self, addr: u32, val: u32) -> Result<(), Error<M::Error>> {
        self.smi_addr(addr, 0)?;
        let reg = (self.switch_id << 2) | SMI_DATA;
        self.mdio.write(self.phy_addr, reg, (val >> 16) as u16)?;
        self.mdio.write(self.phy_addr, reg, val as u16)?;
        Ok(())
    }

    /// Replace the bits in `mask` with those of `val`; writes only on a change.
    pub fn reg_update(&mut self, addr: u32, mask: u32, val: u32) -> Result<(), Error<M::Error>> {
        let old = self.reg_read(addr)?;
        let new = (old & !mask) | (val & mask);
        if new != old {
            self.reg_write(addr, new)?;
        }
        Ok(())
    }

    /// Read a register of several 32-bit words.
    pub fn reg_read_words(&mut self, addr: u32, words: &mut [u32]) -> Result<(), Error<M::Error>> {
        for (i, w) in words.iter_mut().enumerate() {
            *w = self.reg_read(addr + 4 * i as u32)?;
        }
        Ok(())
    }

    /// Write a register of several 32-bit words, in rising address order:
    /// a table entry takes effect with its last word.
    pub fn reg_write_words(&mut self, addr: u32, words: &[u32]) -> Result<(), Error<M::Error>> {
        for (i, w) in words.iter().enumerate() {
            self.reg_write(addr + 4 * i as u32, *w)?;
        }
        Ok(())
    }

    /// Poll until `(register & mask) == want`; returns the register value.
    pub fn reg_wait(&mut self, addr: u32, mask: u32, want: u32) -> Result<u32, Error<M::Error>> {
        let mut waited = 0;
        loop {
            let v = self.reg_read(addr)?;
            if v & mask == want {
                return Ok(v);
            }
            if waited >= POLL_TIMEOUT_US {
                return Err(Error::Timeout);
            }
            self.delay.delay_us(POLL_INTERVAL_US);
            waited += POLL_INTERVAL_US;
        }
    }

    /// Hardware reset, then a check that register access works.
    pub fn reset(&mut self) -> Result<(), Error<M::Error>> {
        self.reg_write(regs::RST, regs::RST_HW.mask())?;
        self.delay.delay_us(regs::RST_DELAY_US as u32);
        self.reg_wait(regs::RST, 0xffff_ffff, 0)?;
        let tpid = self.reg_read(regs::CPU_TAG_TPID)?;
        if regs::CPU_TAG_TPID_TPID.get(tpid) != regs::CPU_TAG_TPID_TPID_RESET {
            return Err(Error::NoDevice);
        }
        Ok(())
    }

    /// Read one byte of the configuration byte store.
    pub fn edata_read(&mut self, addr: u8) -> Result<u8, Error<M::Error>> {
        let status = regs::EDATA_DATA_STATUS;
        let idle = status.prep(regs::EDATA_DATA_STATUS_IDLE);
        self.reg_wait(regs::EDATA_DATA, status.mask(), idle)?;
        self.reg_write(
            regs::EDATA_CTRL,
            regs::EDATA_CTRL_ADDR.prep(addr as u32)
                | regs::EDATA_CTRL_OP.prep(regs::EDATA_CTRL_OP_READ),
        )?;
        let v = self.reg_wait(regs::EDATA_DATA, status.mask(), idle)?;
        Ok(regs::EDATA_DATA_DATA.get(v) as u8)
    }

    /// Read the identification registers and look the part up.
    pub fn identify(&mut self) -> Result<Id, Error<M::Error>> {
        let id = self.reg_read(regs::CHIP_ID)?;
        let major = regs::CHIP_ID_MAJOR.get(id) as u16;
        let minor = regs::CHIP_ID_MINOR.get(id) as u16;
        if major as i32 != regs::MAJOR_YT9215 && major as i32 != regs::MAJOR_YT9218 {
            return Err(Error::NoDevice);
        }
        let mode = regs::CHIP_MODE_MODE.get(self.reg_read(regs::CHIP_MODE)?) as u8;
        let extmode = self.edata_read(regs::EDATA_EXTMODE as u8)?;
        for part in regs::PARTS.iter() {
            if part.major == major && part.mode == mode && part.extmode == extmode {
                return Ok(Id { major, minor, mode, extmode, part });
            }
        }
        Err(Error::NoDevice)
    }

    fn mbus(
        &mut self,
        bus: Mbus,
        phy: u8,
        reg: u8,
        write: Option<u16>,
    ) -> Result<u16, Error<M::Error>> {
        if phy > 31 || reg > 31 {
            return Err(Error::Range);
        }
        let ext = bus == Mbus::External;
        let (r_op, r_ctrl, r_dout, r_din) = if ext {
            (regs::EXT_MBUS_OP, regs::EXT_MBUS_CTRL, regs::EXT_MBUS_DOUT, regs::EXT_MBUS_DIN)
        } else {
            (regs::INT_MBUS_OP, regs::INT_MBUS_CTRL, regs::INT_MBUS_DOUT, regs::INT_MBUS_DIN)
        };
        // Both masters share one register layout.
        let start = regs::INT_MBUS_OP_START.mask();
        self.reg_wait(r_op, start, 0)?;
        let mut mask = regs::INT_MBUS_CTRL_PORT.mask()
            | regs::INT_MBUS_CTRL_REG.mask()
            | regs::INT_MBUS_CTRL_OP.mask();
        let op = if write.is_some() {
            regs::INT_MBUS_CTRL_OP_WRITE
        } else {
            regs::INT_MBUS_CTRL_OP_READ
        };
        let mut ctrl = regs::INT_MBUS_CTRL_PORT.prep(phy as u32)
            | regs::INT_MBUS_CTRL_REG.prep(reg as u32)
            | regs::INT_MBUS_CTRL_OP.prep(op);
        if ext {
            mask |= regs::EXT_MBUS_CTRL_TYPE.mask();
            ctrl |= regs::EXT_MBUS_CTRL_TYPE.prep(regs::EXT_MBUS_CTRL_TYPE_C22);
        }
        self.reg_update(r_ctrl, mask, ctrl)?;
        if let Some(val) = write {
            self.reg_write(r_dout, val as u32)?;
        }
        self.reg_write(r_op, start)?;
        self.reg_wait(r_op, start, 0)?;
        if write.is_some() {
            return Ok(0);
        }
        Ok(regs::INT_MBUS_DIN_DATA.get(self.reg_read(r_din)?) as u16)
    }

    /// Read a PHY register through one of the switch's MDIO masters.
    pub fn phy_read(&mut self, bus: Mbus, phy: u8, reg: u8) -> Result<u16, Error<M::Error>> {
        self.mbus(bus, phy, reg, None)
    }

    /// Write a PHY register through one of the switch's MDIO masters.
    pub fn phy_write(
        &mut self,
        bus: Mbus,
        phy: u8,
        reg: u8,
        val: u16,
    ) -> Result<(), Error<M::Error>> {
        self.mbus(bus, phy, reg, Some(val)).map(|_| ())
    }

    /// Read one port counter. `offset` is a `regs::MIB_*` constant and
    /// `words` its size in 32-bit words (1 or 2).
    pub fn mib_read(
        &mut self,
        port: u32,
        offset: u32,
        words: usize,
    ) -> Result<u64, Error<M::Error>> {
        if port >= regs::PORT_NUM as u32 || !(1..=2).contains(&words) {
            return Err(Error::Range);
        }
        let mut w = [0u32; 2];
        self.reg_read_words(regs::mib_data(port) + offset, &mut w[..words])?;
        Ok(((w[1] as u64) << 32) | w[0] as u64)
    }
}
