/* SPDX-License-Identifier: Apache-2.0 */
/*
 * The code examples of the programmer's guide. Each block between a pair of
 * marker comments is shown in the guide; tests/test_guide.c runs every one
 * against the software switch model.
 */
#include "guide.h"

/* [bringup] */
int guide_bringup(struct yt921x *dev, struct yt921x_id *id)
{
	static const uint8_t addrs[] = { 0x1d, 0x00 }; /* set by a strap pin */
	int err = YT921X_ERR_NODEV;

	/* Find the switch: only a YT921x returns a known family code. */
	for (unsigned int i = 0; i < 2; i++) {
		uint32_t chip_id;
		uint32_t major;

		dev->phy_addr = addrs[i];
		err = yt921x_reg_read(dev, YT921X_CHIP_ID, &chip_id);
		if (err)
			return err;
		major = YT921X_FGET(chip_id, YT921X_CHIP_ID_MAJOR);
		err = (major == YT921X_MAJOR_YT9215 || major == YT921X_MAJOR_YT9218) ?
			0 : YT921X_ERR_NODEV;
		if (!err)
			break;
	}
	if (err)
		return err;
	err = yt921x_reset(dev);
	if (err)
		return err;
	return yt921x_identify(dev, id);
}
/* [bringup end] */

/* [init] */
int guide_init(struct yt921x *dev, unsigned int cpu_port)
{
	struct yt921x_id id;
	int err = guide_bringup(dev, &id); /* find, reset, identify */

	if (!err && !id.part)
		err = YT921X_ERR_NODEV; /* a part this code does not know */
	if (!err)
		err = guide_enable_features(dev);
	if (!err)
		err = guide_cpu_port(dev, cpu_port);
	if (!err)
		err = guide_port_force(dev, cpu_port, YT921X_SPEED_V1000, true);
	/* One group of all copper ports; each may also reach the CPU port. */
	if (!err)
		err = guide_port_group(dev, id.part->phy_ports, (uint16_t)(1u << cpu_port));
	return err;
}
/* [init end] */

/* [features] */
int guide_enable_features(struct yt921x *dev)
{
	/* Counters, ACL and meters work only while their bit is set. */
	uint32_t bits = YT921X_FUNC_MIB_M | YT921X_FUNC_ACL_M | YT921X_FUNC_METER_M;

	return yt921x_reg_update(dev, YT921X_FUNC, bits, bits);
}
/* [features end] */

/* [cpu-port] */
int guide_cpu_port(struct yt921x *dev, unsigned int port)
{
	int err;

	/* Frames to and from this port carry the 8-byte CPU tag. */
	err = yt921x_reg_write(dev, YT921X_EXT_CPU_PORT,
			       YT921X_EXT_CPU_PORT_TAG_EN_M | YT921X_EXT_CPU_PORT_PORT_EN_M |
			       YT921X_FPREP(YT921X_EXT_CPU_PORT_PORT, port));
	if (err)
		return err;
	/* Trapped and copied frames go to the external CPU port. */
	return yt921x_reg_write(dev, YT921X_CPU_COPY, YT921X_CPU_COPY_TO_EXT_CPU_M);
}
/* [cpu-port end] */

/* [port-up] */
int guide_port_force(struct yt921x *dev, unsigned int port, unsigned int speed,
		     bool full_duplex)
{
	uint32_t mask = YT921X_PORT_CTRL_SPEED_M | YT921X_PORT_CTRL_DUPLEX_FULL_M |
			YT921X_PORT_CTRL_RX_PAUSE_M | YT921X_PORT_CTRL_TX_PAUSE_M |
			YT921X_PORT_CTRL_RX_MAC_EN_M | YT921X_PORT_CTRL_TX_MAC_EN_M |
			YT921X_PORT_CTRL_LINK_AN_M;
	uint32_t val = YT921X_FPREP(YT921X_PORT_CTRL_SPEED, speed) |
		       YT921X_PORT_CTRL_RX_MAC_EN_M | YT921X_PORT_CTRL_TX_MAC_EN_M;

	if (full_duplex)
		val |= YT921X_PORT_CTRL_DUPLEX_FULL_M;
	return yt921x_reg_update(dev, YT921X_PORT_CTRL(port), mask, val);
}

int guide_port_down(struct yt921x *dev, unsigned int port)
{
	return yt921x_reg_update(dev, YT921X_PORT_CTRL(port),
				 YT921X_PORT_CTRL_LINK_AN_M | YT921X_PORT_CTRL_RX_MAC_EN_M |
				 YT921X_PORT_CTRL_TX_MAC_EN_M, 0);
}
/* [port-up end] */

/* [port-status] */
int guide_port_status(struct yt921x *dev, unsigned int port, bool *link,
		      unsigned int *speed, bool *full_duplex)
{
	uint32_t val;
	int err = yt921x_reg_read(dev, YT921X_PORT_STATUS(port), &val);

	if (err)
		return err;
	*link = val & YT921X_PORT_STATUS_LINK_M;
	*speed = YT921X_FGET(val, YT921X_PORT_STATUS_SPEED); /* a YT921X_SPEED_ code */
	*full_duplex = val & YT921X_PORT_STATUS_DUPLEX_FULL_M;
	return 0;
}
/* [port-status end] */

/* [isolation] */
int guide_port_group(struct yt921x *dev, uint16_t members, uint16_t cpu_ports)
{
	const uint16_t all = (1u << YT921X_PORT_NUM) - 1u;

	/* A port may send to the other members of its group and to the CPU. */
	for (unsigned int port = 0; port < YT921X_PORT_NUM; port++) {
		uint16_t allowed;
		int err;

		if (!(members & (1u << port)))
			continue;
		allowed = (uint16_t)((members | cpu_ports) & ~(1u << port));
		err = yt921x_reg_write(dev, YT921X_PORT_ISOLATION(port), all & ~allowed);
		if (err)
			return err;
	}
	return 0;
}
/* [isolation end] */

/* [vlan] */
int guide_vlan_write(struct yt921x *dev, unsigned int vid, uint16_t members,
		     uint16_t untagged)
{
	uint32_t entry[YT921X_VLAN_CTRL_WORDS] = { 0, 0 };

	yt921x_bits_set(entry, YT921X_VLAN_CTRL_PORTS_LSB, YT921X_VLAN_CTRL_PORTS_WIDTH,
			members);
	yt921x_bits_set(entry, YT921X_VLAN_CTRL_UNTAG_PORTS_LSB,
			YT921X_VLAN_CTRL_UNTAG_PORTS_WIDTH, untagged);
	/* The words are written in rising address order, low word first. */
	return yt921x_reg_write_words(dev, YT921X_VLAN_CTRL(vid), entry,
				      YT921X_VLAN_CTRL_WORDS);
}

int guide_port_pvid(struct yt921x *dev, unsigned int port, unsigned int vid)
{
	return yt921x_reg_update(dev, YT921X_PORT_VLAN_CTRL(port),
				 YT921X_PORT_VLAN_CTRL_CVID_M,
				 YT921X_FPREP(YT921X_PORT_VLAN_CTRL_CVID, vid));
}
/* [vlan end] */

/* [fdb-wait] */
static int fdb_run(struct yt921x *dev, uint32_t op, uint32_t *result)
{
	int err = yt921x_reg_write(dev, YT921X_FDB_OP, op | YT921X_FDB_OP_START_M);

	if (err)
		return err;
	return yt921x_reg_wait(dev, YT921X_FDB_RESULT, YT921X_FDB_RESULT_DONE_M,
			       YT921X_FDB_RESULT_DONE_M, result);
}

static int fdb_key(struct yt921x *dev, const uint8_t mac[6], unsigned int fid,
		   uint32_t status)
{
	int err = yt921x_reg_write(dev, YT921X_FDB_IN0,
				   (uint32_t)mac[0] << 24 | (uint32_t)mac[1] << 16 |
				   (uint32_t)mac[2] << 8 | mac[3]);

	if (err)
		return err;
	return yt921x_reg_write(dev, YT921X_FDB_IN1,
				YT921X_FPREP(YT921X_FDB_IN1_STATUS, status) |
				YT921X_FPREP(YT921X_FDB_IN1_FID, fid) |
				(uint32_t)mac[4] << 8 | mac[5]);
}
/* [fdb-wait end] */

/* [fdb-add] */
int guide_fdb_add_static(struct yt921x *dev, const uint8_t mac[6], unsigned int fid,
			 uint16_t ports)
{
	uint32_t result;
	int err = fdb_key(dev, mac, fid, YT921X_FDB_IN1_STATUS_STATIC);

	if (err)
		return err;
	err = yt921x_reg_write(dev, YT921X_FDB_IN2,
			       YT921X_FPREP(YT921X_FDB_IN2_EGR_PORTS, ports));
	if (err)
		return err;
	return fdb_run(dev, YT921X_FPREP(YT921X_FDB_OP_OP, YT921X_FDB_OP_OP_ADD), &result);
}
/* [fdb-add end] */

/* [fdb-get] */
int guide_fdb_lookup(struct yt921x *dev, const uint8_t mac[6], unsigned int fid,
		     uint16_t *ports)
{
	uint32_t result, out1, out2;
	int err = fdb_key(dev, mac, fid, 0);

	*ports = 0;
	if (err)
		return err;
	err = yt921x_reg_write(dev, YT921X_FDB_IN2, 0);
	if (err)
		return err;
	err = fdb_run(dev, YT921X_FPREP(YT921X_FDB_OP_OP, YT921X_FDB_OP_OP_GET_ONE), &result);
	if (err || (result & YT921X_FDB_RESULT_NOTFOUND_M))
		return err;
	err = yt921x_reg_read(dev, YT921X_FDB_OUT1, &out1);
	if (err || YT921X_FGET(out1, YT921X_FDB_OUT1_STATUS) == YT921X_FDB_OUT1_STATUS_INVALID)
		return err;
	err = yt921x_reg_read(dev, YT921X_FDB_OUT2, &out2);
	if (err)
		return err;
	*ports = (uint16_t)YT921X_FGET(out2, YT921X_FDB_OUT2_EGR_PORTS);
	return 0;
}
/* [fdb-get end] */

/* [mib] */
int guide_port_bytes(struct yt921x *dev, unsigned int port, uint64_t *rx, uint64_t *tx)
{
	int err = yt921x_mib_read(dev, port, YT921X_MIB_RX_GOOD_BYTES, 2, rx);

	if (err)
		return err;
	return yt921x_mib_read(dev, port, YT921X_MIB_TX_GOOD_BYTES, 2, tx);
}
/* [mib end] */

/* [phy] */
int guide_phy_link(struct yt921x *dev, unsigned int port, bool *up)
{
	uint16_t bmsr;
	int err;

	/* Register 1 is the basic status register; link status latches low,
	 * so read it twice to get the current state. */
	err = yt921x_phy_read(dev, YT921X_MBUS_INT, (uint8_t)port, 1, &bmsr);
	if (!err)
		err = yt921x_phy_read(dev, YT921X_MBUS_INT, (uint8_t)port, 1, &bmsr);
	if (err)
		return err;
	*up = bmsr & 0x0004u;
	return 0;
}
/* [phy end] */

/* [tag] */
#define TAG_ETHERTYPE 0x9988u
#define TAG_PORT_EN (1u << 15)
#define TAG_RX_PORT(w) (((w) >> 11) & 0xfu)
#define TAG_PRIO(w) (((w) >> 8) & 0x7u)
#define TAG_CODE_EN (1u << 7)
#define TAG_CODE(w) (((w) >> 1) & 0x3fu)

/* Fill the 8 tag bytes of a frame that the host sends to the ports in dst_ports. */
void guide_tag_build(uint8_t tag[YT921X_TAG_LEN], uint16_t dst_ports, unsigned int prio)
{
	uint16_t w2 = (uint16_t)(TAG_CODE_EN | (prio & 7u) << 8); /* code 0: forward */
	uint16_t w3 = (uint16_t)(TAG_PORT_EN | (dst_ports & 0x7ffu));

	tag[0] = TAG_ETHERTYPE >> 8;
	tag[1] = TAG_ETHERTYPE & 0xff;
	tag[2] = 0;
	tag[3] = 0;
	tag[4] = (uint8_t)(w2 >> 8);
	tag[5] = (uint8_t)w2;
	tag[6] = (uint8_t)(w3 >> 8);
	tag[7] = (uint8_t)w3;
}

/* Read the tag of a received frame. Returns the source port, or -1. */
int guide_tag_parse(const uint8_t tag[YT921X_TAG_LEN], unsigned int *prio, int *code)
{
	uint16_t w2 = (uint16_t)(tag[4] << 8 | tag[5]);

	if ((tag[0] << 8 | tag[1]) != TAG_ETHERTYPE || !(w2 & TAG_PORT_EN))
		return -1;
	*prio = TAG_PRIO(w2);
	*code = (w2 & TAG_CODE_EN) ? (int)TAG_CODE(w2) : -1;
	return (int)TAG_RX_PORT(w2);
}
/* [tag end] */
