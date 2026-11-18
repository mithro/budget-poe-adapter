/* SPDX-License-Identifier: Apache-2.0 */
/* Runs every example of the guide (examples/guide.c) against the switch model. */
#include <stdio.h>

#include "guide.h"
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
	static const uint8_t mac[6] = { 0x02, 0x11, 0x22, 0x33, 0x44, 0x55 };
	static const uint8_t other[6] = { 0x02, 0x11, 0x22, 0x33, 0x44, 0x56 };
	struct mock_switch sw;
	struct yt921x dev = { .bus = { mock_mdio_read, mock_mdio_write, mock_delay_us, &sw } };
	struct yt921x_id id;
	uint8_t tag[YT921X_TAG_LEN];
	unsigned int speed, prio;
	uint16_t ports;
	uint64_t rx, tx;
	bool link, full;
	int code;

	/* A switch strapped to address 0 is found on the second try. */
	mock_init(&sw, 0x00, 0x9002, 1, 0);
	CHECK(guide_bringup(&dev, &id) == 0);
	CHECK(dev.phy_addr == 0 && id.part && strcmp(id.part->name, "YT9215SC") == 0);

	/* The whole start-up in one call. */
	CHECK(guide_init(&dev, 8) == 0);
	CHECK(*mock_reg(&sw, YT921X_FUNC) == 0x16);
	CHECK(*mock_reg(&sw, YT921X_EXT_CPU_PORT) == 0xc008);
	CHECK((*mock_reg(&sw, YT921X_PORT_CTRL(8)) & 0xff) == 0x9a);
	CHECK(*mock_reg(&sw, YT921X_PORT_ISOLATION(0)) == (0x7ffu & ~0x11eu));
	*mock_reg(&sw, YT921X_FUNC) = 0;

	CHECK(guide_enable_features(&dev) == 0);
	CHECK(*mock_reg(&sw, YT921X_FUNC) == 0x16);

	CHECK(guide_cpu_port(&dev, 8) == 0);
	CHECK(*mock_reg(&sw, YT921X_EXT_CPU_PORT) == 0xc008);
	CHECK(*mock_reg(&sw, YT921X_CPU_COPY) == 1);

	*mock_reg(&sw, YT921X_PORT_CTRL(8)) = 0x200; /* LINK_AN set */
	CHECK(guide_port_force(&dev, 8, YT921X_SPEED_V1000, true) == 0);
	CHECK(*mock_reg(&sw, YT921X_PORT_CTRL(8)) == 0x9a);
	CHECK(guide_port_down(&dev, 8) == 0);
	CHECK(*mock_reg(&sw, YT921X_PORT_CTRL(8)) == 0x82);

	*mock_reg(&sw, YT921X_PORT_STATUS(2)) = 0x1 << 8 | 0x1 << 7 | 0x1;
	CHECK(guide_port_status(&dev, 2, &link, &speed, &full) == 0);
	CHECK(link && full && speed == YT921X_SPEED_V100);

	/* Ports 0 to 2 form a group, port 8 is the CPU port. */
	CHECK(guide_port_group(&dev, 0x007, 0x100) == 0);
	CHECK(*mock_reg(&sw, YT921X_PORT_ISOLATION(0)) == (0x7ffu & ~0x106u));
	CHECK(*mock_reg(&sw, YT921X_PORT_ISOLATION(2)) == (0x7ffu & ~0x103u));

	CHECK(guide_vlan_write(&dev, 100, 0x107, 0x003) == 0);
	CHECK(*mock_reg(&sw, YT921X_VLAN_CTRL(100)) == 0x107u << 7);
	CHECK(*mock_reg(&sw, YT921X_VLAN_CTRL(100) + 4) == 0x003u << 8);
	CHECK(guide_port_pvid(&dev, 1, 100) == 0);
	CHECK(*mock_reg(&sw, YT921X_PORT_VLAN_CTRL(1)) == 100u << 6);

	CHECK(guide_fdb_add_static(&dev, mac, 100, 0x004) == 0);
	CHECK(guide_fdb_lookup(&dev, mac, 100, &ports) == 0 && ports == 0x004);
	CHECK(guide_fdb_lookup(&dev, other, 100, &ports) == 0 && ports == 0);
	CHECK(guide_fdb_lookup(&dev, mac, 101, &ports) == 0 && ports == 0);

	*mock_reg(&sw, YT921X_MIB_DATA(3) + YT921X_MIB_RX_GOOD_BYTES) = 0x89abcdef;
	*mock_reg(&sw, YT921X_MIB_DATA(3) + YT921X_MIB_RX_GOOD_BYTES + 4) = 0x1;
	*mock_reg(&sw, YT921X_MIB_DATA(3) + YT921X_MIB_TX_GOOD_BYTES) = 42;
	CHECK(guide_port_bytes(&dev, 3, &rx, &tx) == 0);
	CHECK(rx == UINT64_C(0x189abcdef) && tx == 42);

	sw.phy[0][4][1] = 0x796d;
	CHECK(guide_phy_link(&dev, 4, &link) == 0 && link);
	CHECK(guide_phy_link(&dev, 3, &link) == 0 && !link);

	guide_tag_build(tag, 0x005, 3);
	CHECK(tag[0] == 0x99 && tag[1] == 0x88 && tag[2] == 0 && tag[3] == 0);
	CHECK(tag[4] == 0x03 && tag[5] == 0x80 && tag[6] == 0x80 && tag[7] == 0x05);
	tag[4] = 0x80 | 2 << 3 | 5; /* port valid, port 2, priority 5 */
	tag[5] = 0x80 | 0x19 << 1;  /* code valid, unknown unicast */
	CHECK(guide_tag_parse(tag, &prio, &code) == 2 && prio == 5 && code == 0x19);
	tag[0] = 0x81;
	CHECK(guide_tag_parse(tag, &prio, &code) == -1);

	if (failures)
		return 1;
	printf("C guide examples: all checks passed\n");
	return 0;
}
