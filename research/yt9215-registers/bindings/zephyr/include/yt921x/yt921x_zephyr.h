/* SPDX-License-Identifier: Apache-2.0 */
/*
 * Zephyr device for a Motorcomm YT921x switch on an MDIO bus.
 */
#ifndef YT921X_ZEPHYR_H
#define YT921X_ZEPHYR_H

#include <zephyr/device.h>

#include "yt921x.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Take the lock of the switch device and return its register access handle.
 *
 * Every yt921x_*() call of the portable library takes this handle. One
 * register access is four MDIO frames and most operations are several
 * accesses, so hold the lock for the whole operation.
 */
struct yt921x *yt921x_zephyr_lock(const struct device *dev);

/** Release the lock taken with yt921x_zephyr_lock(). */
void yt921x_zephyr_unlock(const struct device *dev);

/** Part identification read at init. */
const struct yt921x_id *yt921x_zephyr_id(const struct device *dev);

#ifdef __cplusplus
}
#endif

#endif /* YT921X_ZEPHYR_H */
