/* SPDX-License-Identifier: Apache-2.0 */
/*
 * Print the part the YT921x device found at init and the link state of
 * every port.
 */
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>

#include <yt921x/yt921x_zephyr.h>

static const struct device *const sw = DEVICE_DT_GET(DT_NODELABEL(switch0));

int main(void)
{
	const struct yt921x_id *id;
	struct yt921x *dev;

	if (!device_is_ready(sw)) {
		printk("no YT921x switch answered on the MDIO bus\n");
		return 0;
	}

	id = yt921x_zephyr_id(sw);
	printk("%s, chip ID 0x%04x%04x\n", id->part->name, id->major, id->minor);

	dev = yt921x_zephyr_lock(sw);
	for (unsigned int port = 0; port < YT921X_PORT_NUM; port++) {
		uint32_t status;

		if (yt921x_reg_read(dev, YT921X_PORT_STATUS(port), &status) != 0) {
			break;
		}
		printk("port %u: link %s\n", port,
		       YT921X_FGET(status, YT921X_PORT_STATUS_LINK) ? "up" : "down");
	}
	yt921x_zephyr_unlock(sw);
	return 0;
}
