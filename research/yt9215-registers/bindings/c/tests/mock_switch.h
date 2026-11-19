/* SPDX-License-Identifier: Apache-2.0 */
/*
 * A software model of the YT921x register interface, for tests: the SMI
 * protocol on MDIO, self-clearing reset, the configuration byte store, the
 * MDIO masters with a small PHY register file behind each, and a forwarding
 * database that holds one entry.
 */
#ifndef MOCK_SWITCH_H
#define MOCK_SWITCH_H

#include <stdint.h>
#include <string.h>

#include "yt921x.h"

#define MOCK_REGS 256

struct mock_switch {
	uint8_t phy_addr;
	uint8_t switch_id;
	/* sparse register file */
	uint32_t addr[MOCK_REGS];
	uint32_t val[MOCK_REGS];
	unsigned int used;
	/* SMI state */
	uint32_t smi_addr;
	uint32_t smi_data;
	unsigned int addr_phase;
	unsigned int data_phase;
	/* devices behind the switch */
	uint8_t edata[256];
	uint16_t phy[2][32][32];
	uint32_t fdb[3]; /* the one stored entry, as IN0..IN2 */
	unsigned int reset_polls;
	unsigned int frames;
	unsigned int delays;
};

static inline uint32_t *mock_reg(struct mock_switch *m, uint32_t addr)
{
	for (unsigned int i = 0; i < m->used; i++)
		if (m->addr[i] == addr)
			return &m->val[i];
	m->addr[m->used] = addr;
	m->val[m->used] = 0;
	return &m->val[m->used++];
}

static inline void mock_init(struct mock_switch *m, uint8_t phy_addr, uint16_t major,
			     uint8_t mode, uint8_t extmode)
{
	memset(m, 0, sizeof(*m));
	m->phy_addr = phy_addr;
	*mock_reg(m, YT921X_CHIP_ID) = (uint32_t)major << 16 | 0x0001u;
	*mock_reg(m, YT921X_CHIP_MODE) = mode;
	*mock_reg(m, YT921X_CPU_TAG_TPID) = YT921X_CPU_TAG_TPID_TPID_RESET;
	*mock_reg(m, YT921X_EDATA_DATA) = YT921X_EDATA_DATA_STATUS_IDLE;
	m->edata[YT921X_EDATA_EXTMODE] = extmode;
}

static inline uint32_t mock_read(struct mock_switch *m, uint32_t addr)
{
	if (addr == YT921X_RST && m->reset_polls) {
		/* reset takes two polls to complete */
		if (--m->reset_polls == 0)
			*mock_reg(m, YT921X_RST) = 0;
	}
	return *mock_reg(m, addr);
}

static inline void mock_mbus(struct mock_switch *m, int ext)
{
	uint32_t ctrl = *mock_reg(m, ext ? YT921X_EXT_MBUS_CTRL : YT921X_INT_MBUS_CTRL);
	unsigned int phy = YT921X_FGET(ctrl, YT921X_INT_MBUS_CTRL_PORT);
	unsigned int reg = YT921X_FGET(ctrl, YT921X_INT_MBUS_CTRL_REG);
	unsigned int op = YT921X_FGET(ctrl, YT921X_INT_MBUS_CTRL_OP);

	if (op == YT921X_INT_MBUS_CTRL_OP_WRITE)
		m->phy[ext][phy][reg] =
			(uint16_t)*mock_reg(m, ext ? YT921X_EXT_MBUS_DOUT : YT921X_INT_MBUS_DOUT);
	else if (op == YT921X_INT_MBUS_CTRL_OP_READ)
		*mock_reg(m, ext ? YT921X_EXT_MBUS_DIN : YT921X_INT_MBUS_DIN) =
			m->phy[ext][phy][reg];
}

static inline void mock_fdb(struct mock_switch *m, uint32_t op)
{
	const uint32_t key1 = YT921X_FDB_IN1_FID_M | YT921X_FDB_IN1_ADDR_LO2_M;
	uint32_t in0 = *mock_reg(m, YT921X_FDB_IN0);
	uint32_t in1 = *mock_reg(m, YT921X_FDB_IN1);
	uint32_t result = YT921X_FDB_RESULT_DONE_M;

	switch (YT921X_FGET(op, YT921X_FDB_OP_OP)) {
	case YT921X_FDB_OP_OP_ADD:
		m->fdb[0] = in0;
		m->fdb[1] = in1;
		m->fdb[2] = *mock_reg(m, YT921X_FDB_IN2);
		break;
	case YT921X_FDB_OP_OP_GET_ONE:
		if (YT921X_FGET(m->fdb[1], YT921X_FDB_IN1_STATUS) && m->fdb[0] == in0 &&
		    (m->fdb[1] & key1) == (in1 & key1)) {
			*mock_reg(m, YT921X_FDB_OUT0) = m->fdb[0];
			*mock_reg(m, YT921X_FDB_OUT1) = m->fdb[1];
			*mock_reg(m, YT921X_FDB_OUT2) = m->fdb[2];
		} else {
			result |= YT921X_FDB_RESULT_NOTFOUND_M;
		}
		break;
	default:
		memset(m->fdb, 0, sizeof(m->fdb));
	}
	*mock_reg(m, YT921X_FDB_RESULT) = result;
}

static inline void mock_write(struct mock_switch *m, uint32_t addr, uint32_t val)
{
	if (addr == YT921X_FDB_OP && (val & YT921X_FDB_OP_START_M)) {
		mock_fdb(m, val);
		return;
	}
	if (addr == YT921X_RST && (val & YT921X_RST_HW_M)) {
		*mock_reg(m, addr) = val;
		m->reset_polls = 2;
		return;
	}
	if (addr == YT921X_EDATA_CTRL) {
		*mock_reg(m, YT921X_EDATA_DATA) =
			(uint32_t)m->edata[YT921X_FGET(val, YT921X_EDATA_CTRL_ADDR)] << 24 |
			YT921X_EDATA_DATA_STATUS_IDLE;
		return;
	}
	if ((addr == YT921X_INT_MBUS_OP || addr == YT921X_EXT_MBUS_OP) && (val & 1u)) {
		mock_mbus(m, addr == YT921X_EXT_MBUS_OP);
		return; /* START reads back 0: transfer complete */
	}
	*mock_reg(m, addr) = val;
}

/* The MDIO side: what the switch does with each clause-22 frame. */
static inline int mock_mdio(struct mock_switch *m, uint8_t phy, uint8_t reg, int read,
			    uint16_t *val)
{
	m->frames++;
	if (phy != m->phy_addr || ((reg >> 2) & 3u) != m->switch_id || reg > 15) {
		if (read)
			*val = 0xffff;
		return 0;
	}
	if (!(reg & 2u)) { /* address phase: always MDIO writes */
		if (read)
			return 0;
		m->smi_addr = m->addr_phase ? (m->smi_addr | *val) : (uint32_t)*val << 16;
		m->addr_phase ^= 1u;
		m->data_phase = 0;
		return 0;
	}
	if (reg & 1u) { /* data phase of a register read */
		if (!read)
			return 0;
		if (!m->data_phase)
			m->smi_data = mock_read(m, m->smi_addr);
		*val = m->data_phase ? (uint16_t)m->smi_data : (uint16_t)(m->smi_data >> 16);
	} else { /* data phase of a register write */
		if (read)
			return 0;
		if (!m->data_phase)
			m->smi_data = (uint32_t)*val << 16;
		else
			mock_write(m, m->smi_addr, m->smi_data | *val);
	}
	m->data_phase ^= 1u;
	return 0;
}

static inline int mock_mdio_read(void *ctx, uint8_t phy, uint8_t reg, uint16_t *val)
{
	return mock_mdio(ctx, phy, reg, 1, val);
}

static inline int mock_mdio_write(void *ctx, uint8_t phy, uint8_t reg, uint16_t val)
{
	return mock_mdio(ctx, phy, reg, 0, &val);
}

static inline void mock_delay_us(void *ctx, uint32_t us)
{
	(void)us;
	((struct mock_switch *)ctx)->delays++;
}

#endif /* MOCK_SWITCH_H */
