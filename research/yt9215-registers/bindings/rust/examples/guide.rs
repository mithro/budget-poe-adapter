// SPDX-License-Identifier: Apache-2.0
//! The Rust example of the programmer's guide: the two traits a board has to
//! implement, and bring-up of the switch. `cargo build --examples` compiles
//! it; run on a host it reports that no switch answers.
use yt921x::{regs, Delay, Error, Mdio, Yt921x};

// [bus]
/// The MDIO controller of the board. This one has nothing attached, so every
/// read returns the pulled-up line.
struct BoardMdio;

impl Mdio for BoardMdio {
    type Error = core::convert::Infallible;

    fn read(&mut self, _phy: u8, _reg: u8) -> Result<u16, Self::Error> {
        Ok(0xffff)
    }

    fn write(&mut self, _phy: u8, _reg: u8, _val: u16) -> Result<(), Self::Error> {
        Ok(())
    }
}

struct BoardDelay;

impl Delay for BoardDelay {
    fn delay_us(&mut self, _us: u32) {}
}
// [bus end]

// [bringup]
/// Find the switch, reset it and identify the part.
fn bringup<M: Mdio, D: Delay>(mdio: M, delay: D) -> Result<Yt921x<M, D>, Error<M::Error>> {
    let mut found = None;
    let mut bus = Some((mdio, delay));
    for addr in [0x1d, 0x00] {
        let (mdio, delay) = bus.take().unwrap();
        let mut dev = Yt921x::new(mdio, delay, addr, 0);
        let major = regs::CHIP_ID_MAJOR.get(dev.reg_read(regs::CHIP_ID)?);
        if major == regs::MAJOR_YT9215 as u32 || major == regs::MAJOR_YT9218 as u32 {
            found = Some(dev);
            break;
        }
        bus = Some(dev.release());
    }
    let mut dev = found.ok_or(Error::NoDevice)?;
    dev.reset()?;
    let id = dev.identify()?;
    let _ = id.part.name;
    Ok(dev)
}
// [bringup end]

fn main() {
    match bringup(BoardMdio, BoardDelay) {
        Ok(_) => println!("switch found"),
        Err(e) => println!("no switch: {:?}", e),
    }
}
