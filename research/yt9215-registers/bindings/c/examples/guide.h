/* SPDX-License-Identifier: Apache-2.0 */
/* Declarations of the guide examples in guide.c. */
#ifndef GUIDE_H
#define GUIDE_H

#include "yt921x.h"

int guide_bringup(struct yt921x *dev, struct yt921x_id *id);
int guide_init(struct yt921x *dev, unsigned int cpu_port);
int guide_enable_features(struct yt921x *dev);
int guide_cpu_port(struct yt921x *dev, unsigned int port);
int guide_port_force(struct yt921x *dev, unsigned int port, unsigned int speed, bool full_duplex);
int guide_port_down(struct yt921x *dev, unsigned int port);
int guide_port_status(struct yt921x *dev, unsigned int port, bool *link, unsigned int *speed,
		      bool *full_duplex);
int guide_port_group(struct yt921x *dev, uint16_t members, uint16_t cpu_ports);
int guide_vlan_write(struct yt921x *dev, unsigned int vid, uint16_t members, uint16_t untagged);
int guide_port_pvid(struct yt921x *dev, unsigned int port, unsigned int vid);
int guide_fdb_add_static(struct yt921x *dev, const uint8_t mac[6], unsigned int fid,
			 uint16_t ports);
int guide_fdb_lookup(struct yt921x *dev, const uint8_t mac[6], unsigned int fid, uint16_t *ports);
int guide_port_bytes(struct yt921x *dev, unsigned int port, uint64_t *rx, uint64_t *tx);
int guide_phy_link(struct yt921x *dev, unsigned int port, bool *up);
void guide_tag_build(uint8_t tag[YT921X_TAG_LEN], uint16_t dst_ports, unsigned int prio);
int guide_tag_parse(const uint8_t tag[YT921X_TAG_LEN], unsigned int *prio, int *code);

#endif /* GUIDE_H */
