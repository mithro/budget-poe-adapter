/* SPDX-License-Identifier: Apache-2.0 */
/* Tests of the C binding against the software switch model. */
#include <stdio.h>

#include "mock_switch.h"

static int failures;

#define CHECK(cond) \
	do { \
		if (!(cond)) { \
			printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond); \
			failures++; \
		} \
	} while (0)

int main(void)
{
	struct mock_switch sw;
	struct yt921x dev = {
		.bus = { mock_mdio_read, mock_mdio_write, mock_delay_us, &sw },
		.phy_addr = 0x1d,
		.switch_id = 0,
	};
	struct yt921x_id id;
	uint32_t val;
	uint32_t words[3];
	uint16_t v16;
	uint64_t v64;

	mock_init(&sw, 0x1d, 0x9002, 2, 0);

	/* Register access: four MDIO frames per access. */
	CHECK(yt921x_reg_write(&dev, YT921X_PORT_CTRL(3), 0x12345678) == 0);
	CHECK(sw.frames == 4);
	CHECK(*mock_reg(&sw, 0x8010c) == 0x12345678);
	CHECK(yt921x_reg_read(&dev, YT921X_PORT_CTRL(3), &val) == 0 && val == 0x12345678);
	CHECK(sw.frames == 8);
	CHECK(yt921x_reg_update(&dev, YT921X_PORT_CTRL(3), YT921X_PORT_CTRL_SPEED_M,
				YT921X_FPREP(YT921X_PORT_CTRL_SPEED, YT921X_SPEED_V1000)) == 0);
	CHECK(*mock_reg(&sw, 0x8010c) == 0x1234567a);

	/* Reset and identification. */
	CHECK(yt921x_reset(&dev) == 0);
	CHECK(sw.delays >= 1);
	CHECK(yt921x_identify(&dev, &id) == 0);
	CHECK(id.major == 0x9002 && id.mode == 2 && id.extmode == 0);
	CHECK(id.part && strcmp(id.part->name, "YT9215S") == 0);
	CHECK(id.part && id.part->phy_ports == 0x1f && id.part->serdes_ports == 0x100);

	/* A switch on another address does not answer. */
	dev.phy_addr = 0;
	CHECK(yt921x_reset(&dev) != 0);
	dev.phy_addr = 0x1d;

	/* PHY access through both MDIO masters. */
	sw.phy[0][2][1] = 0x796d;
	CHECK(yt921x_phy_read(&dev, YT921X_MBUS_INT, 2, 1, &v16) == 0 && v16 == 0x796d);
	CHECK(yt921x_phy_write(&dev, YT921X_MBUS_INT, 4, 0, 0x1200) == 0);
	CHECK(sw.phy[0][4][0] == 0x1200);
	CHECK(yt921x_phy_write(&dev, YT921X_MBUS_EXT, 7, 9, 0x0300) == 0);
	CHECK(sw.phy[1][7][9] == 0x0300);
	CHECK(YT921X_FGET(*mock_reg(&sw, YT921X_EXT_MBUS_CTRL), YT921X_EXT_MBUS_CTRL_TYPE) ==
	      YT921X_EXT_MBUS_CTRL_TYPE_C22);
	CHECK(yt921x_phy_read(&dev, YT921X_MBUS_INT, 32, 0, &v16) == YT921X_ERR_RANGE);

	/* Counters: 32-bit and 64-bit. */
	*mock_reg(&sw, YT921X_MIB_DATA(1) + YT921X_MIB_RX_GOOD_BYTES) = 0x89abcdef;
	*mock_reg(&sw, YT921X_MIB_DATA(1) + YT921X_MIB_RX_GOOD_BYTES + 4) = 0x01234567;
	CHECK(yt921x_mib_read(&dev, 1, YT921X_MIB_RX_GOOD_BYTES, 2, &v64) == 0);
	CHECK(v64 == UINT64_C(0x0123456789abcdef));

	/* Multi-word registers and fields that cross a word boundary. */
	memset(words, 0, sizeof(words));
	yt921x_bits_set(words, YT921X_VLAN_CTRL_FID_LSB, YT921X_VLAN_CTRL_FID_WIDTH, 0xabc);
	words[YT921X_VLAN_CTRL_PORTS_W] |= YT921X_VLAN_CTRL_PORTS_M(0) | YT921X_VLAN_CTRL_PORTS_M(8);
	CHECK(words[0] == ((0xabcu << 23) | (1u << 7) | (1u << 15)));
	CHECK(words[1] == (0xabcu >> 9));
	CHECK(yt921x_bits_get(words, YT921X_VLAN_CTRL_FID_LSB, YT921X_VLAN_CTRL_FID_WIDTH) == 0xabc);
	CHECK(yt921x_reg_write_words(&dev, YT921X_VLAN_CTRL(100), words, YT921X_VLAN_CTRL_WORDS) == 0);
	CHECK(*mock_reg(&sw, 0x188000 + 8 * 100 + 4) == (0xabcu >> 9));

	/* Address arithmetic of the less regular registers. */
	CHECK(YT921X_SERDES(8) == 0x8008c && YT921X_SERDES(9) == 0x80090);
	CHECK(YT921X_XMII(9) == 0x80408);
	CHECK(YT921X_LED_SER_MAP(2, 0) == 0xd0104 && YT921X_LED_SER_MAP(0, 1) == 0xd0118);
	CHECK(YT921X_ACL_KEY(47, 7) == 0x204000 + 0x200 * 7 + 8 * 47);
	CHECK(YT921X_IPM_PCP(1, 1, 7) == 0x180100 + 4 * (16 + 8 + 7));
	CHECK(YT921X_XMII_CTRL_PORT_M(8) == 2 && YT921X_XMII_CTRL_PORT_M(9) == 1);
	CHECK(YT921X_SERDES_CTRL_PORT_M(8) == 1 && YT921X_SERDES_CTRL_PORT_M(9) == 2);
	CHECK(YT921X_FPREP_AT(YT921X_STP_PORT, 10, YT921X_STP_PORT_FORWARD) == 3u << 20);
	CHECK(YT921X_LED_PAR_INV_INV_M(2, 9) == 1u << 29);

	if (failures) {
		printf("%d check(s) failed\n", failures);
		return 1;
	}
	printf("C binding: all checks passed\n");
	return 0;
}
