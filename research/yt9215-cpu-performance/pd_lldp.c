/*
 * Workload model for the YT9215 CPU: the time-critical parts of a bit-banged
 * USB-PD source and of LLDP power negotiation, written the way firmware for an
 * RV32E core without multiplier would write them.
 *
 * Nothing here knows a real YT9215 register. The GPIO data registers and the
 * cycle counter are reached through the three hooks below, which the emulator
 * in rv32e_emu.py provides. Their real addresses and costs are not published.
 */
#include <stdint.h>

#define GPIO_IN  (*(volatile uint32_t *)0x40000000u) /* bit 0: comparator output */
#define GPIO_OUT (*(volatile uint32_t *)0x40000004u) /* bit 0: CC driver */

static inline uint32_t rdcycle(void)
{
	uint32_t v;
	__asm__ volatile("csrr %0, mcycle" : "=r"(v));
	return v;
}

/* ---- CRC-32 as USB-PD uses it, 16-entry table, no multiplier ------------- */

static const uint32_t crc_nibble[16] = {
	0x00000000, 0x1db71064, 0x3b6e20c8, 0x26d930ac,
	0x76dc4190, 0x6b6b51f4, 0x4db26158, 0x5005713c,
	0xedb88320, 0xf00f9344, 0xd6d6a3e8, 0xcb61b38c,
	0x9b64c2b0, 0x86d3d2d4, 0xa00ae278, 0xbdbdf21c,
};

uint32_t pd_crc32(const uint8_t *p, uint32_t n)
{
	uint32_t c = 0xffffffffu;

	while (n--) {
		c ^= *p++;
		c = (c >> 4) ^ crc_nibble[c & 15];
		c = (c >> 4) ^ crc_nibble[c & 15];
	}
	return ~c;
}

/* ---- 4b5b line code -------------------------------------------------------- */

static const uint8_t enc4b5b[16] = {
	0x1e, 0x09, 0x14, 0x15, 0x0a, 0x0b, 0x0e, 0x0f,
	0x12, 0x13, 0x16, 0x17, 0x1a, 0x1b, 0x1c, 0x1d,
};

#define K_SYNC1 0x18
#define K_SYNC2 0x11
#define K_EOP   0x0d
#define SYM_BAD 0xff
#define SYM_EOP 0xfe

/* 5-bit symbol to nibble, SYM_EOP or SYM_BAD */
static const uint8_t dec5b[32] = {
	0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
	0xff, 0x01, 0x04, 0x05, 0xff, 0xfe, 0x06, 0x07,
	0xff, 0xff, 0x08, 0x09, 0x02, 0x03, 0x0a, 0x0b,
	0xff, 0xff, 0x0c, 0x0d, 0x0e, 0x0f, 0x00, 0xff,
};

/* SOP = Sync-1 Sync-1 Sync-1 Sync-2, first transmitted bit in bit 0 */
#define SOP_BITS (K_SYNC1 | (K_SYNC1 << 5) | (K_SYNC1 << 10) | (K_SYNC2 << 15))

/* ---- Transmit --------------------------------------------------------------- */

struct bitbuf {
	uint32_t nbits;
	uint8_t bits[60]; /* 64 preamble + 20 SOP + 34 bytes * 10 + 5 EOP = 429 */
};

static void put_bits(struct bitbuf *b, uint32_t v, uint32_t n)
{
	while (n--) {
		if (v & 1)
			b->bits[b->nbits >> 3] |= (uint8_t)(1u << (b->nbits & 7));
		b->nbits++;
		v >>= 1;
	}
}

/* Line-code a message (header and data objects, CRC appended here). */
void pd_encode(struct bitbuf *b, const uint8_t *msg, uint32_t len)
{
	uint32_t i, crc = pd_crc32(msg, len);

	for (i = 0; i < sizeof(b->bits); i++)
		b->bits[i] = 0;
	b->nbits = 0;
	put_bits(b, 0xaaaaaaaau, 32);
	put_bits(b, 0xaaaaaaaau, 32);
	put_bits(b, SOP_BITS, 20);
	for (i = 0; i < len + 4; i++) {
		uint8_t v = i < len ? msg[i] : (uint8_t)(crc >> (8 * (i - len)));

		put_bits(b, enc4b5b[v & 15], 5);
		put_bits(b, enc4b5b[v >> 4], 5);
	}
	put_bits(b, K_EOP, 5);
}

static inline void wait_until(uint32_t t)
{
	while ((int32_t)(rdcycle() - t) < 0)
		;
}

/*
 * Send a line-coded message. half0 and half1 are the lengths of the two halves
 * of a bit in CPU cycles; they differ by one when the bit time is odd.
 * Interrupts are assumed off. Returns the cycle count of the last edge.
 */
__attribute__((noinline))
uint32_t pd_tx(const struct bitbuf *b, uint32_t t, uint32_t half0, uint32_t half1)
{
	uint32_t i, level = 0;

	for (i = 0; i < b->nbits; i++) {
		uint32_t one = (b->bits[i >> 3] >> (i & 7)) & 1;

		wait_until(t);
		level ^= 1;
		GPIO_OUT = level;
		t += half0;
		if (one) {
			wait_until(t);
			level ^= 1;
			GPIO_OUT = level;
		}
		t += half1;
	}
	wait_until(t);
	if (level) { /* end low: one more half bit high, then low */
		t += half0;
		wait_until(t);
	}
	GPIO_OUT = 0;
	return t;
}

/* ---- Receive by polling --------------------------------------------------- */

struct pd_rx {
	uint32_t len;     /* bytes received, CRC included */
	uint32_t t_last;  /* cycle count of the last edge seen */
	uint8_t data[40];
};

/*
 * Receive one message by polling the comparator output. thr is three quarters
 * of a bit time in cycles: a shorter gap between edges is half a bit.
 * timeout is the idle time in cycles that ends an attempt.
 * Returns 0 for a message with a good CRC, otherwise an error number.
 */
int pd_rx_poll(struct pd_rx *rx, uint32_t thr, uint32_t timeout)
{
	uint32_t level = GPIO_IN & 1;
	uint32_t last = rdcycle();
	uint32_t window = 0;  /* last 20 bits before SOP */
	uint32_t sym = 0, nsym = 0, half = 0, synced = 0;
	uint32_t nib = 0, have_nib = 0;

	rx->len = 0;
	for (;;) {
		uint32_t now, dt, bit, v;

		/* The polling loop: its length is the sampling period. */
		do {
			v = GPIO_IN & 1;
			now = rdcycle();
			if (now - last > timeout)
				return 1;
		} while (v == level);
		level = v;
		dt = now - last;
		last = now;

		if (dt < thr) {
			half ^= 1;
			if (half)
				continue;
			bit = 1;
		} else {
			half = 0;
			bit = 0;
		}

		if (!synced) {
			window = (window >> 1) | (bit << 19);
			if (window == SOP_BITS)
				synced = 1;
			continue;
		}
		sym |= bit << nsym;
		if (++nsym < 5)
			continue;
		v = dec5b[sym];
		sym = 0;
		nsym = 0;
		if (v == SYM_EOP)
			break;
		if (v == SYM_BAD || rx->len >= sizeof(rx->data))
			return 2;
		if (!have_nib) {
			nib = v;
			have_nib = 1;
		} else {
			rx->data[rx->len++] = (uint8_t)(nib | (v << 4));
			have_nib = 0;
		}
	}
	rx->t_last = last;
	if (rx->len < 6)
		return 3;
	/* CRC over message and received CRC leaves a fixed residue. */
	if (pd_crc32(rx->data, rx->len) != 0x2144df1cu)
		return 4;
	return 0;
}

/* ---- GoodCRC turnaround ---------------------------------------------------- */

/*
 * Receive a message and answer it with GoodCRC. gap is the 25 us minimum
 * between messages, in cycles. Returns 0 when a GoodCRC was sent.
 */
int pd_rx_and_ack(uint32_t thr, uint32_t timeout, uint32_t gap,
		  uint32_t half0, uint32_t half1)
{
	static struct pd_rx rx;
	static struct bitbuf bb;
	uint8_t ack[2];
	uint32_t id, start, now;
	int r = pd_rx_poll(&rx, thr, timeout);

	if (r)
		return r;
	id = (rx.data[1] >> 1) & 7;
	/* GoodCRC from a source and DFP, specification revision 3 */
	ack[0] = 0xa1;
	ack[1] = (uint8_t)(0x01 | (id << 1));
	pd_encode(&bb, ack, 2);
	start = rx.t_last + gap;
	now = rdcycle() + 16;
	if ((int32_t)(now - start) > 0) /* already late: start at once */
		start = now;
	pd_tx(&bb, start, half0, half1);
	return 0;
}

/* ---- Receive from an edge interrupt -------------------------------------- */

/* The work of a GPIO edge interrupt handler: time-stamp the edge and queue it. */
struct edge_fifo {
	uint32_t last;
	uint32_t wr;
	uint16_t dt[64];
};

void pd_edge_isr(struct edge_fifo *f)
{
	uint32_t now = rdcycle();

	f->dt[f->wr & 63] = (uint16_t)(now - f->last);
	f->wr++;
	f->last = now;
}

/* ---- LLDP ----------------------------------------------------------------- */

struct lldp_power {
	uint8_t found;
	uint8_t type_source_prio;
	uint16_t pd_requested;   /* units of 0.1 W */
	uint16_t pse_allocated;  /* units of 0.1 W */
};

/*
 * Walk the TLVs of a received LLDPDU (the bytes after the EtherType) and pick
 * out the IEEE 802.3 Power via MDI TLV with the 802.3at extension.
 */
int lldp_parse(const uint8_t *p, uint32_t len, struct lldp_power *out)
{
	uint32_t off = 0;

	out->found = 0;
	while (off + 2 <= len) {
		uint32_t hdr = ((uint32_t)p[off] << 8) | p[off + 1];
		uint32_t type = hdr >> 9, tl = hdr & 0x1ff;
		const uint8_t *v = p + off + 2;

		off += 2 + tl;
		if (off > len)
			return -1;
		if (type == 0)
			return 0;
		if (type == 127 && tl >= 12 &&
		    v[0] == 0x00 && v[1] == 0x12 && v[2] == 0x0f && v[3] == 2) {
			out->found = 1;
			out->type_source_prio = v[7];
			out->pd_requested = (uint16_t)((v[8] << 8) | v[9]);
			out->pse_allocated = (uint16_t)((v[10] << 8) | v[11]);
		}
	}
	return -1;
}

static uint8_t *tlv(uint8_t *p, uint32_t type, const uint8_t *v, uint32_t n)
{
	*p++ = (uint8_t)((type << 1) | (n >> 8));
	*p++ = (uint8_t)n;
	while (n--)
		*p++ = *v++;
	return p;
}

/*
 * Build a complete LLDP frame of a powered device that requests power.
 * Returns the frame length without FCS.
 */
uint32_t lldp_build(uint8_t *frame, const uint8_t *mac, uint32_t request)
{
	static const uint8_t dst[6] = { 0x01, 0x80, 0xc2, 0x00, 0x00, 0x0e };
	uint8_t v[16], *p = frame;
	uint32_t i;

	for (i = 0; i < 6; i++)
		*p++ = dst[i];
	for (i = 0; i < 6; i++)
		*p++ = mac[i];
	*p++ = 0x88;
	*p++ = 0xcc;

	v[0] = 4; /* chassis ID: MAC address */
	for (i = 0; i < 6; i++)
		v[1 + i] = mac[i];
	p = tlv(p, 1, v, 7);
	v[0] = 3; /* port ID: MAC address */
	p = tlv(p, 2, v, 7);
	v[0] = 0;
	v[1] = 120; /* time to live */
	p = tlv(p, 3, v, 2);

	v[0] = 0x00; /* IEEE 802.3 */
	v[1] = 0x12;
	v[2] = 0x0f;
	v[3] = 2;    /* Power via MDI */
	v[4] = 0x00; /* MDI power support: a PD */
	v[5] = 1;    /* PSE power pair */
	v[6] = 0;    /* power class */
	v[7] = 0x51; /* type 2 PD, source PSE, priority low */
	v[8] = (uint8_t)(request >> 8);
	v[9] = (uint8_t)request;
	v[10] = v[8];
	v[11] = v[9];
	p = tlv(p, 127, v, 12);
	p = tlv(p, 0, v, 0);
	while (p - frame < 60)
		*p++ = 0;
	return (uint32_t)(p - frame);
}

/* ---- 32-bit multiply without the M extension ------------------------------ */

uint32_t soft_mul(uint32_t a, uint32_t b)
{
	uint32_t r = 0;

	while (b) {
		if (b & 1)
			r += a;
		a <<= 1;
		b >>= 1;
	}
	return r;
}
