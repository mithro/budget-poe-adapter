/* SPDX-License-Identifier: Apache-2.0 */
/*
 * Motorcomm YT921x switch: register access over MDIO and the basic
 * operations every driver needs.
 */
#include <stddef.h>

#include "yt921x.h"

/* The MDIO register number of a transfer carries three control fields. */
#define SMI_SWITCHID(id) (((id) & 3u) << 2)
#define SMI_DATA 0x2u /* 0: address phase, 1: data phase */
#define SMI_READ 0x1u /* 0: register write, 1: register read */

#define POLL_INTERVAL_US 10000u
#define POLL_TIMEOUT_US 100000u

static const struct yt921x_part parts[] = {
#define X(name, major, mode, extmode, phy, xmii, serdes) \
	{ name, major, mode, extmode, phy, xmii, serdes },
	YT921X_PART_TABLE(X)
#undef X
};

static int smi_addr(struct yt921x *dev, uint32_t addr, unsigned int rw)
{
	uint8_t reg = (uint8_t)(SMI_SWITCHID(dev->switch_id) | rw);
	int res;

	res = dev->bus.mdio_write(dev->bus.ctx, dev->phy_addr, reg, (uint16_t)(addr >> 16));
	if (res)
		return res;
	return dev->bus.mdio_write(dev->bus.ctx, dev->phy_addr, reg, (uint16_t)addr);
}

int yt921x_reg_read(struct yt921x *dev, uint32_t addr, uint32_t *val)
{
	uint8_t reg = (uint8_t)(SMI_SWITCHID(dev->switch_id) | SMI_DATA | SMI_READ);
	uint16_t hi;
	uint16_t lo;
	int res;

	res = smi_addr(dev, addr, SMI_READ);
	if (res)
		return res;
	res = dev->bus.mdio_read(dev->bus.ctx, dev->phy_addr, reg, &hi);
	if (res)
		return res;
	res = dev->bus.mdio_read(dev->bus.ctx, dev->phy_addr, reg, &lo);
	if (res)
		return res;
	*val = ((uint32_t)hi << 16) | lo;
	return 0;
}

int yt921x_reg_write(struct yt921x *dev, uint32_t addr, uint32_t val)
{
	uint8_t reg = (uint8_t)(SMI_SWITCHID(dev->switch_id) | SMI_DATA);
	int res;

	res = smi_addr(dev, addr, 0);
	if (res)
		return res;
	res = dev->bus.mdio_write(dev->bus.ctx, dev->phy_addr, reg, (uint16_t)(val >> 16));
	if (res)
		return res;
	return dev->bus.mdio_write(dev->bus.ctx, dev->phy_addr, reg, (uint16_t)val);
}

int yt921x_reg_update(struct yt921x *dev, uint32_t addr, uint32_t mask, uint32_t val)
{
	uint32_t old;
	uint32_t new;
	int res;

	res = yt921x_reg_read(dev, addr, &old);
	if (res)
		return res;
	new = (old & ~mask) | (val & mask);
	if (new == old)
		return 0;
	return yt921x_reg_write(dev, addr, new);
}

int yt921x_reg_read_words(struct yt921x *dev, uint32_t addr, uint32_t *words, unsigned int n)
{
	for (unsigned int i = 0; i < n; i++) {
		int res = yt921x_reg_read(dev, addr + 4u * i, &words[i]);

		if (res)
			return res;
	}
	return 0;
}

int yt921x_reg_write_words(struct yt921x *dev, uint32_t addr, const uint32_t *words,
			   unsigned int n)
{
	/* Rising address order, as the Linux driver writes table entries. */
	for (unsigned int i = 0; i < n; i++) {
		int res = yt921x_reg_write(dev, addr + 4u * i, words[i]);

		if (res)
			return res;
	}
	return 0;
}

int yt921x_reg_wait(struct yt921x *dev, uint32_t addr, uint32_t mask, uint32_t want,
		    uint32_t *val)
{
	uint32_t v;

	for (uint32_t waited = 0;; waited += POLL_INTERVAL_US) {
		int res = yt921x_reg_read(dev, addr, &v);

		if (res)
			return res;
		if ((v & mask) == want) {
			if (val)
				*val = v;
			return 0;
		}
		if (waited >= POLL_TIMEOUT_US)
			return YT921X_ERR_TIMEOUT;
		dev->bus.delay_us(dev->bus.ctx, POLL_INTERVAL_US);
	}
}

int yt921x_reset(struct yt921x *dev)
{
	uint32_t val;
	int res;

	res = yt921x_reg_write(dev, YT921X_RST, YT921X_RST_HW_M);
	if (res)
		return res;
	dev->bus.delay_us(dev->bus.ctx, YT921X_RST_DELAY_US);
	/* The whole register reads 0 once the reset is complete. */
	res = yt921x_reg_wait(dev, YT921X_RST, 0xffffffffu, 0, NULL);
	if (res)
		return res;
	/* A register with a known reset value proves that access works. */
	res = yt921x_reg_read(dev, YT921X_CPU_TAG_TPID, &val);
	if (res)
		return res;
	if (YT921X_FGET(val, YT921X_CPU_TAG_TPID_TPID) != YT921X_CPU_TAG_TPID_TPID_RESET)
		return YT921X_ERR_NODEV;
	return 0;
}

int yt921x_edata_read(struct yt921x *dev, uint8_t addr, uint8_t *val)
{
	const uint32_t idle = YT921X_FPREP(YT921X_EDATA_DATA_STATUS, YT921X_EDATA_DATA_STATUS_IDLE);
	uint32_t v;
	int res;

	res = yt921x_reg_wait(dev, YT921X_EDATA_DATA, YT921X_EDATA_DATA_STATUS_M, idle, NULL);
	if (res)
		return res;
	res = yt921x_reg_write(dev, YT921X_EDATA_CTRL,
			       YT921X_FPREP(YT921X_EDATA_CTRL_ADDR, addr) |
			       YT921X_FPREP(YT921X_EDATA_CTRL_OP, YT921X_EDATA_CTRL_OP_READ));
	if (res)
		return res;
	res = yt921x_reg_wait(dev, YT921X_EDATA_DATA, YT921X_EDATA_DATA_STATUS_M, idle, &v);
	if (res)
		return res;
	*val = (uint8_t)YT921X_FGET(v, YT921X_EDATA_DATA_DATA);
	return 0;
}

int yt921x_identify(struct yt921x *dev, struct yt921x_id *id)
{
	uint32_t val;
	int res;

	res = yt921x_reg_read(dev, YT921X_CHIP_ID, &val);
	if (res)
		return res;
	id->major = (uint16_t)YT921X_FGET(val, YT921X_CHIP_ID_MAJOR);
	id->minor = (uint16_t)YT921X_FGET(val, YT921X_CHIP_ID_MINOR);
	if (id->major != YT921X_MAJOR_YT9215 && id->major != YT921X_MAJOR_YT9218)
		return YT921X_ERR_NODEV;
	res = yt921x_reg_read(dev, YT921X_CHIP_MODE, &val);
	if (res)
		return res;
	id->mode = (uint8_t)YT921X_FGET(val, YT921X_CHIP_MODE_MODE);
	res = yt921x_edata_read(dev, YT921X_EDATA_EXTMODE, &id->extmode);
	if (res)
		return res;
	id->part = NULL;
	for (size_t i = 0; i < sizeof(parts) / sizeof(parts[0]); i++) {
		if (parts[i].major == id->major && parts[i].mode == id->mode &&
		    parts[i].extmode == id->extmode) {
			id->part = &parts[i];
			return 0;
		}
	}
	return YT921X_ERR_NODEV;
}

static int mbus_transfer(struct yt921x *dev, enum yt921x_mbus bus, uint8_t phy, uint8_t reg,
			 bool write, uint16_t *val)
{
	const bool ext = bus == YT921X_MBUS_EXT;
	const uint32_t r_op = ext ? YT921X_EXT_MBUS_OP : YT921X_INT_MBUS_OP;
	const uint32_t r_ctrl = ext ? YT921X_EXT_MBUS_CTRL : YT921X_INT_MBUS_CTRL;
	const uint32_t r_dout = ext ? YT921X_EXT_MBUS_DOUT : YT921X_INT_MBUS_DOUT;
	const uint32_t r_din = ext ? YT921X_EXT_MBUS_DIN : YT921X_INT_MBUS_DIN;
	/* Both masters share one register layout. */
	uint32_t mask = YT921X_INT_MBUS_CTRL_PORT_M | YT921X_INT_MBUS_CTRL_REG_M |
			YT921X_INT_MBUS_CTRL_OP_M;
	uint32_t ctrl;
	uint32_t v;
	int res;

	if (phy > 31 || reg > 31)
		return YT921X_ERR_RANGE;
	res = yt921x_reg_wait(dev, r_op, YT921X_INT_MBUS_OP_START_M, 0, NULL);
	if (res)
		return res;
	ctrl = YT921X_FPREP(YT921X_INT_MBUS_CTRL_PORT, phy) |
	       YT921X_FPREP(YT921X_INT_MBUS_CTRL_REG, reg) |
	       YT921X_FPREP(YT921X_INT_MBUS_CTRL_OP,
			    write ? YT921X_INT_MBUS_CTRL_OP_WRITE : YT921X_INT_MBUS_CTRL_OP_READ);
	if (ext) {
		mask |= YT921X_EXT_MBUS_CTRL_TYPE_M;
		ctrl |= YT921X_FPREP(YT921X_EXT_MBUS_CTRL_TYPE, YT921X_EXT_MBUS_CTRL_TYPE_C22);
	}
	res = yt921x_reg_update(dev, r_ctrl, mask, ctrl);
	if (res)
		return res;
	if (write) {
		res = yt921x_reg_write(dev, r_dout, *val);
		if (res)
			return res;
	}
	res = yt921x_reg_write(dev, r_op, YT921X_INT_MBUS_OP_START_M);
	if (res)
		return res;
	res = yt921x_reg_wait(dev, r_op, YT921X_INT_MBUS_OP_START_M, 0, NULL);
	if (res || write)
		return res;
	res = yt921x_reg_read(dev, r_din, &v);
	if (res)
		return res;
	*val = (uint16_t)YT921X_FGET(v, YT921X_INT_MBUS_DIN_DATA);
	return 0;
}

int yt921x_phy_read(struct yt921x *dev, enum yt921x_mbus bus, uint8_t phy, uint8_t reg,
		    uint16_t *val)
{
	return mbus_transfer(dev, bus, phy, reg, false, val);
}

int yt921x_phy_write(struct yt921x *dev, enum yt921x_mbus bus, uint8_t phy, uint8_t reg,
		     uint16_t val)
{
	return mbus_transfer(dev, bus, phy, reg, true, &val);
}

int yt921x_mib_read(struct yt921x *dev, unsigned int port, uint32_t offset,
		    unsigned int words, uint64_t *val)
{
	uint32_t w[2] = { 0, 0 };
	int res;

	if (port >= YT921X_PORT_NUM || words < 1 || words > 2)
		return YT921X_ERR_RANGE;
	/* Low word first; a 64-bit counter has its high word at offset + 4. */
	res = yt921x_reg_read_words(dev, YT921X_MIB_DATA(port) + offset, w, words);
	if (res)
		return res;
	*val = ((uint64_t)w[1] << 32) | w[0];
	return 0;
}
