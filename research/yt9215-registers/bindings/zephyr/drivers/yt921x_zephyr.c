/* SPDX-License-Identifier: Apache-2.0 */
/*
 * Zephyr device for a Motorcomm YT921x switch on an MDIO bus: connects the
 * portable access library to the Zephyr MDIO API, resets the switch and
 * identifies the part at init.
 */
#define DT_DRV_COMPAT motorcomm_yt921x

#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/mdio.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include <yt921x/yt921x_zephyr.h>

LOG_MODULE_REGISTER(yt921x, CONFIG_YT921X_LOG_LEVEL);

struct yt921x_zephyr_config {
	const struct device *mdio;
	struct gpio_dt_spec reset;
	uint8_t phy_addr;
	uint8_t switch_id;
	bool skip_reset;
};

struct yt921x_zephyr_data {
	struct yt921x dev;
	struct yt921x_id id;
	struct k_mutex lock;
};

static int bus_read(void *ctx, uint8_t phy, uint8_t reg, uint16_t *val)
{
	return mdio_read(ctx, phy, reg, val);
}

static int bus_write(void *ctx, uint8_t phy, uint8_t reg, uint16_t val)
{
	return mdio_write(ctx, phy, reg, val);
}

static void bus_delay_us(void *ctx, uint32_t us)
{
	ARG_UNUSED(ctx);
	k_sleep(K_USEC(us));
}

struct yt921x *yt921x_zephyr_lock(const struct device *dev)
{
	struct yt921x_zephyr_data *data = dev->data;

	k_mutex_lock(&data->lock, K_FOREVER);
	return &data->dev;
}

void yt921x_zephyr_unlock(const struct device *dev)
{
	struct yt921x_zephyr_data *data = dev->data;

	k_mutex_unlock(&data->lock);
}

const struct yt921x_id *yt921x_zephyr_id(const struct device *dev)
{
	const struct yt921x_zephyr_data *data = dev->data;

	return &data->id;
}

static int yt921x_zephyr_init(const struct device *dev)
{
	const struct yt921x_zephyr_config *cfg = dev->config;
	struct yt921x_zephyr_data *data = dev->data;
	int res;

	if (!device_is_ready(cfg->mdio)) {
		LOG_ERR("MDIO bus %s is not ready", cfg->mdio->name);
		return -ENODEV;
	}

	k_mutex_init(&data->lock);
	data->dev.bus.mdio_read = bus_read;
	data->dev.bus.mdio_write = bus_write;
	data->dev.bus.delay_us = bus_delay_us;
	data->dev.bus.ctx = (void *)cfg->mdio;
	data->dev.phy_addr = cfg->phy_addr;
	data->dev.switch_id = cfg->switch_id;

	if (cfg->reset.port != NULL && !cfg->skip_reset) {
		if (!gpio_is_ready_dt(&cfg->reset)) {
			LOG_ERR("reset GPIO is not ready");
			return -ENODEV;
		}
		res = gpio_pin_configure_dt(&cfg->reset, GPIO_OUTPUT_ACTIVE);
		if (res < 0) {
			return res;
		}
		k_sleep(K_MSEC(10));
		gpio_pin_set_dt(&cfg->reset, 0);
		k_sleep(K_MSEC(10));
	}

	if (!cfg->skip_reset) {
		res = yt921x_reset(&data->dev);
		if (res != 0) {
			LOG_ERR("reset failed: %d", res);
			return res < -999 ? -EIO : res;
		}
	}

	res = yt921x_identify(&data->dev, &data->id);
	if (res != 0) {
		LOG_ERR("identification failed: %d", res);
		return res < -999 ? -ENODEV : res;
	}
	LOG_INF("%s: chip ID 0x%04x%04x, mode %u, extended mode %u", data->id.part->name,
		data->id.major, data->id.minor, data->id.mode, data->id.extmode);
	return 0;
}

#define YT921X_ZEPHYR_DEFINE(inst)                                                             \
	static const struct yt921x_zephyr_config yt921x_zephyr_config_##inst = {              \
		.mdio = DEVICE_DT_GET(DT_INST_BUS(inst)),                                      \
		.reset = GPIO_DT_SPEC_INST_GET_OR(inst, reset_gpios, {0}),                    \
		.phy_addr = DT_INST_REG_ADDR(inst),                                            \
		.switch_id = DT_INST_PROP(inst, switch_id),                                    \
		.skip_reset = DT_INST_PROP(inst, skip_reset),                                  \
	};                                                                                     \
	static struct yt921x_zephyr_data yt921x_zephyr_data_##inst;                           \
	DEVICE_DT_INST_DEFINE(inst, yt921x_zephyr_init, NULL, &yt921x_zephyr_data_##inst,     \
			      &yt921x_zephyr_config_##inst, POST_KERNEL,                       \
			      CONFIG_YT921X_INIT_PRIORITY, NULL);

DT_INST_FOREACH_STATUS_OKAY(YT921X_ZEPHYR_DEFINE)
