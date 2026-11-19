/* SPDX-License-Identifier: Apache-2.0 */
/*
 * Motorcomm YT921x switch: register access over MDIO and the basic
 * operations every driver needs. Portable C99, no dependencies; the caller
 * supplies clause-22 MDIO read and write functions and a delay.
 */
#ifndef YT921X_H
#define YT921X_H

#include <stdbool.h>
#include <stdint.h>

#include "yt921x_regs.h"

#ifdef __cplusplus
extern "C" {
#endif

/** Errors returned by this library, as negative values. */
enum yt921x_error {
	YT921X_OK = 0,
	YT921X_ERR_TIMEOUT = -1000, /**< The switch did not finish an operation. */
	YT921X_ERR_NODEV = -1001,   /**< No YT921x answered, or an unknown part. */
	YT921X_ERR_RANGE = -1002,   /**< An argument is out of range. */
};

/** Host functions the library calls. A non-zero return value is passed up. */
struct yt921x_bus {
	/** Clause-22 MDIO read of register @p reg of PHY address @p phy. */
	int (*mdio_read)(void *ctx, uint8_t phy, uint8_t reg, uint16_t *val);
	/** Clause-22 MDIO write. */
	int (*mdio_write)(void *ctx, uint8_t phy, uint8_t reg, uint16_t val);
	/** Wait at least @p us microseconds. */
	void (*delay_us)(void *ctx, uint32_t us);
	void *ctx;
};

/** One switch. */
struct yt921x {
	struct yt921x_bus bus;
	uint8_t phy_addr;  /**< MDIO address the switch answers on: 0x1d or 0x00. */
	uint8_t switch_id; /**< Switch ID, 0 to 3; 0 unless several switches share the address. */
};

/** Result of yt921x_identify(). */
struct yt921x_id {
	uint16_t major;   /**< CHIP_ID.MAJOR */
	uint16_t minor;   /**< CHIP_ID.MINOR */
	uint8_t mode;     /**< CHIP_MODE.MODE */
	uint8_t extmode;  /**< Extended mode byte of the configuration byte store. */
	const struct yt921x_part *part; /**< Matching part, or NULL when unknown. */
};

/** One row of the part table. */
struct yt921x_part {
	const char *name;
	uint16_t major;
	uint8_t mode;
	uint8_t extmode;
	uint16_t phy_ports;    /**< Ports with a built-in PHY, one bit per port. */
	uint16_t xmii_ports;   /**< Ports with xMII pins, one bit per port. */
	uint16_t serdes_ports; /**< Ports with a SerDes, one bit per port. */
};

/** Which MDIO master of the switch a PHY sits on. */
enum yt921x_mbus {
	YT921X_MBUS_INT, /**< Built-in PHYs and SerDes PCS; address = port number. */
	YT921X_MBUS_EXT, /**< PHYs on the external MDIO pins. */
};

/* Register access */
int yt921x_reg_read(struct yt921x *dev, uint32_t addr, uint32_t *val);
int yt921x_reg_write(struct yt921x *dev, uint32_t addr, uint32_t val);
int yt921x_reg_update(struct yt921x *dev, uint32_t addr, uint32_t mask, uint32_t val);
int yt921x_reg_read_words(struct yt921x *dev, uint32_t addr, uint32_t *words, unsigned int n);
int yt921x_reg_write_words(struct yt921x *dev, uint32_t addr, const uint32_t *words,
			   unsigned int n);
int yt921x_reg_wait(struct yt921x *dev, uint32_t addr, uint32_t mask, uint32_t want,
		    uint32_t *val);

/* Bring-up */
int yt921x_reset(struct yt921x *dev);
int yt921x_edata_read(struct yt921x *dev, uint8_t addr, uint8_t *val);
int yt921x_identify(struct yt921x *dev, struct yt921x_id *id);

/* PHY registers through the switch */
int yt921x_phy_read(struct yt921x *dev, enum yt921x_mbus bus, uint8_t phy, uint8_t reg,
		    uint16_t *val);
int yt921x_phy_write(struct yt921x *dev, enum yt921x_mbus bus, uint8_t phy, uint8_t reg,
		     uint16_t val);

/* Port counters */
int yt921x_mib_read(struct yt921x *dev, unsigned int port, uint32_t offset,
		    unsigned int words, uint64_t *val);

#ifdef __cplusplus
}
#endif

#endif /* YT921X_H */
