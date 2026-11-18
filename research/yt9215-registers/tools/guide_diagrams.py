"""The diagrams of the guide pages, by the name the yt-diagram directive uses.

Each function takes a link builder (``yt921x_sphinx.Links``) and returns a
``diagrams.Svg``.
"""
import diagrams
import model as M

DIAGRAMS = {}


def diagram(name):
    def deco(fn):
        DIAGRAMS[name] = fn
        return fn
    return deco


@diagram("address-map")
def address_map(ln):
    m = ln.model
    rows, prev = [], None
    for x in m.regions:
        regs = [r for r in m.regs if r["region"] == x["name"]]
        n = len(regs)
        rows.append({"addr": "0x%06x" % x["base"], "name": x["name"], "title": x["title"],
                     "note": "%d register%s described" % (n, "" if n == 1 else "s"),
                     "href": ln.page("reference/regions/" + x["name"].lower().replace("_", "-")),
                     "gap": prev is not None and x["base"] - prev > 0x10000})
        prev = x["base"]
    return diagrams.addrmap("Address regions of the YT921x", rows)


def _box(s, x, y, w, h, title, lines=(), cls="", href=None):
    if href:
        s.open_link(href)
    s.rect(x, y, w, h, "yt-box " + cls, 4)
    top = y + h / 2 - 6.5 * len(lines) + 4
    s.text(x + w / 2, top, title, "yt-b")
    for i, t in enumerate(lines):
        s.text(x + w / 2, top + 14 + 13 * i, t, "yt-s")
    if href:
        s.close_link()


@diagram("system")
def system(ln):
    s = diagrams.Svg(748, 270, "A host microcontroller and the YT921x")
    _box(s, 1, 60, 150, 150, "Host", ["microcontroller", "running the driver"])
    s.rect(270, 1, 290, 268, "yt-box yt-rsv", 6)
    s.text(415, 20, "YT921x", "yt-b")
    _box(s, 290, 40, 250, 54, "Register file", ["32-bit registers, 32-bit addresses"],
         href=ln.page("reference/index"))
    _box(s, 290, 112, 250, 54, "Switch core", ["VLAN, forwarding database, ACL, queues"],
         href=ln.page("overview", "overview-frame-path"))
    _box(s, 290, 184, 250, 66, "MDIO masters", ["internal: built-in PHYs, SerDes PCS",
                                                  "external: PHYs on the MDIO pins"],
         href=ln.page("phy"))
    s.arrow(151, 67, 290, 67)
    s.arrow(290, 67, 151, 67)
    s.text(210, 60, "MDC, MDIO")
    s.text(210, 82, "register access", "yt-s")
    s.arrow(151, 139, 290, 139)
    s.arrow(290, 139, 151, 139)
    s.text(210, 132, "CPU port")
    s.text(210, 154, "Ethernet frames", "yt-s")
    _box(s, 620, 30, 127, 58, "Ports 0 to 7", ["built-in copper PHY"], href=ln.page("ports"))
    _box(s, 620, 106, 127, 58, "Ports 8 and 9", ["SerDes or xMII"],
         href=ln.page("ports", "ports-external"))
    _box(s, 620, 182, 127, 58, "Port 10", ["internal", "microcontroller"])
    for y in (59, 135, 211):
        s.arrow(560, y, 620, y)
        s.arrow(620, y, 560, y)
    return s


@diagram("frame-path")
def frame_path(ln):
    def st(title, lines, page, anchor=None):
        return {"title": title, "lines": lines, "href": ln.page(page, anchor)}
    return diagrams.pipeline("Stages a frame passes through", [
        st("Receive MAC", ["speed, duplex, pause", "frame size"], "ports"),
        st("Tag parsing", ["TPID match", "port VLAN ID"], "vlan", "vlan-aware"),
        st("Ingress VLAN filter", ["membership check"], "vlan", "vlan-filter"),
        st("ACL and meters", ["match, act, police"], "acl"),
        st("Learning", ["source address", "into the database"], "forwarding", "forwarding-learning"),
        st("Destination lookup", ["forwarding database"], "fdb"),
        st("Unknown destination", ["flood, trap or drop"], "forwarding", "forwarding-flood"),
        st("Isolation and STP", ["remove blocked ports"], "forwarding", "forwarding-isolation"),
        st("Link aggregation", ["pick one member"], "lag"),
        st("Priority and queue", ["internal priority"], "qos"),
        st("Egress shaping", ["port rate limit"], "rate", "rate-shaper"),
        st("Transmit MAC", ["VLAN tag or CPU tag"], "vlan", "vlan-egress"),
    ])


def _mdio_cells(read):
    drive = "yt-ro" if read else ""
    return [
        {"units": 6, "title": "PRE", "sub": "32 ones", "top": "32 bits"},
        {"units": 3, "title": "ST", "sub": "01", "top": "2"},
        {"units": 3, "title": "OP", "sub": "10 read" if read else "01 write", "top": "2"},
        {"units": 5, "title": "PHYAD", "sub": "0x1d or 0x00", "top": "5"},
        {"units": 5, "title": "REGAD", "sub": "see below", "top": "5", "cls": "yt-sp"},
        {"units": 3, "title": "TA", "sub": "Z0" if read else "10", "top": "2", "cls": drive},
        {"units": 13, "title": "DATA", "sub": "driven by the switch" if read else "driven by the host",
         "top": "16 bits, most significant first", "cls": drive},
    ]


@diagram("mdio-frame")
def mdio_frame(ln):
    return diagrams.strip("Clause 22 MDIO write and read frames",
                          [("Write", _mdio_cells(False)), ("Read", _mdio_cells(True))])


@diagram("smi-regad")
def smi_regad(ln):
    return diagrams.bitfield("REGAD field of a frame to the switch", 1, [
        {"name": "0", "lsb": 4, "width": 1, "cls": "yt-rsv"},
        {"name": "switch ID", "lsb": 2, "width": 2},
        {"name": "DATA", "lsb": 1, "width": 1, "cls": "yt-sp"},
        {"name": "READ", "lsb": 0, "width": 1, "cls": "yt-ro"},
    ], bits=5)


def _smi(read):
    op = "MDIO read" if read else "MDIO write"
    rw = "1" if read else "0"
    cls = "yt-ro" if read else ""
    word = "value" if read else "value"
    return [
        ("MDIO frame", [{"units": 1, "title": "MDIO write"}, {"units": 1, "title": "MDIO write"},
                        {"units": 1, "title": op, "cls": cls}, {"units": 1, "title": op, "cls": cls}]),
        ("REGAD", [{"units": 1, "title": "ID, DATA=0, READ=" + rw}] * 2
                  + [{"units": 1, "title": "ID, DATA=1, READ=" + rw, "cls": cls}] * 2),
        ("DATA", [{"units": 1, "title": "address[31:16]"}, {"units": 1, "title": "address[15:0]"},
                  {"units": 1, "title": word + "[31:16]", "cls": cls},
                  {"units": 1, "title": word + "[15:0]", "cls": cls}]),
    ]


@diagram("smi-read")
def smi_read(ln):
    return diagrams.strip("The four MDIO frames of a register read", _smi(True))


@diagram("smi-write")
def smi_write(ln):
    return diagrams.strip("The four MDIO frames of a register write", _smi(False))


@diagram("smi-timing")
def smi_timing(ln):
    return diagrams.smi_timing()


@diagram("reset-sequence")
def reset_sequence(ln):
    return diagrams.sequence("Reset and identification", ["Host", "YT921x"], [
        (0, 1, "write RST = HW (bit 31)"),
        ("note", 0, "wait 10 ms"),
        (0, 1, "read RST"),
        (1, 0, "0 when the reset is complete; else poll again after 10 ms"),
        (0, 1, "read CPU_TAG_TPID"),
        (1, 0, "0x9988: register access works"),
        (0, 1, "read CHIP_ID, CHIP_MODE"),
        (1, 0, "family code and mode"),
        (0, 1, "read byte 0xfb of the configuration byte store"),
        (1, 0, "extended mode: names the part"),
    ])


@diagram("edata-sequence")
def edata_sequence(ln):
    return diagrams.sequence("Reading one configuration byte", ["Host", "YT921x"], [
        (0, 1, "read EDATA_DATA until STATUS = IDLE (3)"),
        (0, 1, "write EDATA_CTRL = ADDR << 8 | OP READ (5)"),
        (0, 1, "read EDATA_DATA until STATUS = IDLE (3)"),
        (1, 0, "DATA (bits 31:24) holds the byte"),
    ])


@diagram("mbus-sequence")
def mbus_sequence(ln):
    return diagrams.sequence("PHY register read through an MDIO master",
                             ["Host", "YT921x", "PHY"], [
        (0, 1, "read MBUS_OP until START = 0"),
        (0, 1, "write MBUS_CTRL: PORT, REG, OP"),
        (0, 1, "write MBUS_OP = START"),
        (1, 2, "clause 22 frame"),
        (2, 1, "16-bit value"),
        (0, 1, "read MBUS_OP until START = 0"),
        (0, 1, "read MBUS_DIN"),
        (1, 0, "DATA: the PHY register value"),
    ])


@diagram("fdb-sequence")
def fdb_sequence(ln):
    return diagrams.sequence("One forwarding database command", ["Host", "YT921x"], [
        (0, 1, "write FDB_IN0, FDB_IN1, FDB_IN2: the entry or the key"),
        (0, 1, "write FDB_OP = command | START"),
        ("note", 1, "the switch runs the command"),
        (0, 1, "read FDB_RESULT until DONE = 1 (poll every 10 ms, give up after 100 ms)"),
        (1, 0, "NOTFOUND, INDEX"),
        (0, 1, "read FDB_OUT1, FDB_OUT0, FDB_OUT2 (lookups only)"),
        (1, 0, "the entry that was found"),
    ])


@diagram("acl-sequence")
def acl_sequence(ln):
    return diagrams.sequence("Writing one ACL rule", ["Host", "YT921x"], [
        (0, 1, "write ACL_ACT[8 × block + slot]: three words"),
        (0, 1, "write ACL_BLK_CMD = BLKID | MODIFY"),
        ("note", 1, "block is open; lookups still use the old content"),
        (0, 1, "write ACL_KEY and ACL_MASK of each slot of the rule: two words each"),
        (0, 1, "write ACL_BLK_KEEP: KEEP for every slot that is not rewritten"),
        (0, 1, "write ACL_ENTRY[block]: EN and GRPID of every slot"),
        (0, 1, "write ACL_BLK_CMD = BLKID (MODIFY = 0)"),
        ("note", 1, "the block switches to the new content"),
    ])


@diagram("tagged-frame")
def tagged_frame(ln):
    frame = [
        {"units": 6, "title": "Destination", "sub": "6 bytes"},
        {"units": 6, "title": "Source", "sub": "6 bytes"},
        {"units": 8, "title": "CPU tag", "sub": "8 bytes", "cls": "yt-sp"},
        {"units": 3, "title": "Type", "sub": "2 bytes"},
        {"units": 9, "title": "Payload"},
        {"units": 4, "title": "FCS", "sub": "4 bytes"},
    ]
    tag = [
        {"units": 2, "title": "0x9988", "sub": "EtherType", "top": "bytes 0, 1", "cls": "yt-sp"},
        {"units": 2, "title": "word 1", "sub": "VLAN tag", "top": "bytes 2, 3", "cls": "yt-sp"},
        {"units": 2, "title": "word 2", "sub": "port, priority, code", "top": "bytes 4, 5", "cls": "yt-sp"},
        {"units": 2, "title": "word 3", "sub": "destination ports", "top": "bytes 6, 7", "cls": "yt-sp"},
    ]
    return diagrams.strip("Position and content of the CPU tag", [("Frame", frame), ("Tag", tag)])


@diagram("tag-word2")
def tag_word2(ln):
    return diagrams.bitfield("Tag word 2", 1, [
        {"name": "PORT_EN", "lsb": 15, "width": 1, "cls": "yt-ro"},
        {"name": "RX_PORT", "lsb": 11, "width": 4, "cls": "yt-ro"},
        {"name": "PRIO", "lsb": 8, "width": 3},
        {"name": "CODE_EN", "lsb": 7, "width": 1},
        {"name": "CODE", "lsb": 1, "width": 6},
    ], bits=16)


@diagram("tag-word3")
def tag_word3(ln):
    return diagrams.bitfield("Tag word 3", 1, [
        {"name": "PORT_EN", "lsb": 15, "width": 1},
        {"name": "TX_PORTS", "lsb": 0, "width": 11, "ticks": list(range(11))},
    ], bits=16)


@diagram("token-bucket")
def token_bucket(ln):
    s = diagrams.Svg(748, 150, "Token bucket of a meter or shaper")
    _box(s, 1, 40, 170, 60, "Time slot", ["SLOT × 8 core clock periods"],
         href=ln.reg("METER_SLOT"))
    _box(s, 250, 30, 200, 80, "Bucket", ["holds up to CBS tokens", "token size scales with 4^UNIT"],
         cls="yt-sp")
    _box(s, 540, 40, 207, 60, "Frame", ["spends tokens for its length,", "or is coloured or delayed"])
    s.arrow(171, 70, 250, 70)
    s.text(210, 62, "+ CIR")
    s.text(210, 86, "each slot", "yt-s")
    s.arrow(450, 70, 540, 70)
    s.text(495, 62, "tokens")
    return s
