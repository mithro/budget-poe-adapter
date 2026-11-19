"""A small RV32E instruction-set emulator that counts instructions and cycles.

It runs the uncompressed RV32E build of pd_lldp.c. It is not a model of the
Nuclei N205: the cycle counts come from the two simple pipeline models in
MODELS, which bracket what a 2-stage core is likely to do.
"""

import struct

# Extra cycles on top of one cycle per instruction.
MODELS = {
    "fast": {"taken": 1, "load": 0, "mmio": 0},
    "slow": {"taken": 2, "load": 1, "mmio": 2},
}

MMIO_BASE = 0x40000000
GPIO_IN = MMIO_BASE
GPIO_OUT = MMIO_BASE + 4
CSR_MCYCLE = 0xB00
RETURN_ADDRESS = 0xFFFFFFF0


def sext(value, bits):
    sign = 1 << (bits - 1)
    return (value & (sign - 1)) - (value & sign)


class Elf:
    """The loadable sections and the symbols of a 32-bit little-endian ELF file."""

    def __init__(self, path):
        data = open(path, "rb").read()
        assert data[:6] == b"\x7fELF\x01\x01", "not a 32-bit little-endian ELF file"
        shoff, = struct.unpack_from("<I", data, 0x20)
        shentsize, shnum = struct.unpack_from("<HH", data, 0x2E)
        sections = [struct.unpack_from("<10I", data, shoff + i * shentsize) for i in range(shnum)]
        self.chunks = []
        self.symbols = {}
        for name, kind, flags, addr, offset, size, link, info, align, entsize in sections:
            if flags & 2 and kind == 1:  # SHF_ALLOC and SHT_PROGBITS
                self.chunks.append((addr, data[offset:offset + size]))
            if kind == 2:  # SHT_SYMTAB
                strtab = sections[link]
                for i in range(size // 16):
                    st_name, st_value, st_size, st_info, st_other, st_shndx = struct.unpack_from(
                        "<IIIBBH", data, offset + i * 16)
                    end = data.index(b"\0", strtab[4] + st_name)
                    self.symbols[data[strtab[4] + st_name:end].decode()] = st_value


class Cpu:
    def __init__(self, elf, model, base=0x10000, size=0x20000):
        self.elf = elf
        self.model = MODELS[model]
        self.base = base
        self.mem = bytearray(size)
        for addr, chunk in elf.chunks:
            self.mem[addr - base:addr - base + len(chunk)] = chunk
        self.x = [0] * 16
        self.pc = 0
        self.cycles = 0
        self.instructions = 0
        self.gpio_in = lambda cycle: 0
        self.gpio_writes = []   # (cycle, value)
        self.gpio_reads = []    # cycle of each read
        self.pc_hooks = {}      # address -> function(cpu)

    # -- memory ---------------------------------------------------------------
    def load(self, addr, size):
        if addr >= MMIO_BASE:
            self.cycles += self.model["mmio"]
            if addr == GPIO_IN:
                self.gpio_reads.append(self.cycles)
                return self.gpio_in(self.cycles)
            raise RuntimeError("read of unknown register %#x" % addr)
        self.cycles += self.model["load"]
        off = addr - self.base
        return int.from_bytes(self.mem[off:off + size], "little")

    def store(self, addr, size, value):
        if addr >= MMIO_BASE:
            self.cycles += self.model["mmio"]
            if addr == GPIO_OUT:
                self.gpio_writes.append((self.cycles, value & 1))
                return
            raise RuntimeError("write of unknown register %#x" % addr)
        off = addr - self.base
        self.mem[off:off + size] = (value & ((1 << (8 * size)) - 1)).to_bytes(size, "little")

    def write_bytes(self, addr, data):
        self.mem[addr - self.base:addr - self.base + len(data)] = data

    def read_bytes(self, addr, size):
        return bytes(self.mem[addr - self.base:addr - self.base + size])

    # -- execution ------------------------------------------------------------
    def reg(self, n):
        if n > 15:
            raise RuntimeError("register x%d used: not RV32E code" % n)
        return self.x[n]

    def setreg(self, n, value):
        if n > 15:
            raise RuntimeError("register x%d used: not RV32E code" % n)
        if n:
            self.x[n] = value & 0xFFFFFFFF

    def call(self, name, *args, limit=50_000_000):
        """Call a function by the ilp32e convention and return a0."""
        assert len(args) <= 6
        for i, arg in enumerate(args):
            self.x[10 + i] = arg & 0xFFFFFFFF
        self.x[1] = RETURN_ADDRESS
        self.x[2] = self.base + len(self.mem) - 16
        self.pc = self.elf.symbols[name]
        start = self.instructions
        while self.pc != RETURN_ADDRESS:
            if self.pc in self.pc_hooks:
                self.pc_hooks[self.pc](self)
            self.step()
            if self.instructions - start > limit:
                raise RuntimeError("instruction limit reached in " + name)
        return self.x[10]

    def step(self):
        pc = self.pc
        off = pc - self.base
        inst = int.from_bytes(self.mem[off:off + 4], "little")
        if inst & 3 != 3:
            raise RuntimeError("compressed instruction at %#x" % pc)
        opcode = inst & 0x7F
        rd = (inst >> 7) & 31
        f3 = (inst >> 12) & 7
        rs1 = (inst >> 15) & 31
        rs2 = (inst >> 20) & 31
        f7 = inst >> 25
        imm_i = sext(inst >> 20, 12)
        next_pc = pc + 4
        taken = False
        self.instructions += 1
        self.cycles += 1

        if opcode == 0x37:    # lui
            self.setreg(rd, inst & 0xFFFFF000)
        elif opcode == 0x17:  # auipc
            self.setreg(rd, pc + (inst & 0xFFFFF000))
        elif opcode == 0x6F:  # jal
            imm = sext(((inst >> 31) << 20) | (((inst >> 12) & 0xFF) << 12)
                       | (((inst >> 20) & 1) << 11) | (((inst >> 21) & 0x3FF) << 1), 21)
            self.setreg(rd, next_pc)
            next_pc = pc + imm
            taken = True
        elif opcode == 0x67:  # jalr
            target = (self.reg(rs1) + imm_i) & 0xFFFFFFFE
            self.setreg(rd, next_pc)
            next_pc = target
            taken = True
        elif opcode == 0x63:  # branches
            imm = sext(((inst >> 31) << 12) | (((inst >> 7) & 1) << 11)
                       | (((inst >> 25) & 0x3F) << 5) | (((inst >> 8) & 0xF) << 1), 13)
            a, b = self.reg(rs1), self.reg(rs2)
            sa, sb = sext(a, 32), sext(b, 32)
            taken = {0: a == b, 1: a != b, 4: sa < sb, 5: sa >= sb, 6: a < b, 7: a >= b}[f3]
            if taken:
                next_pc = pc + imm
        elif opcode == 0x03:  # loads
            addr = (self.reg(rs1) + imm_i) & 0xFFFFFFFF
            size = 1 << (f3 & 3)
            value = self.load(addr, size)
            if f3 < 3:
                value = sext(value, 8 * size)
            self.setreg(rd, value)
        elif opcode == 0x23:  # stores
            imm = sext((f7 << 5) | rd, 12)
            self.store((self.reg(rs1) + imm) & 0xFFFFFFFF, 1 << f3, self.reg(rs2))
        elif opcode in (0x13, 0x33):
            a = self.reg(rs1)
            if opcode == 0x13:
                b = imm_i & 0xFFFFFFFF
                sub = False
                arith = f3 == 5 and (inst >> 30) & 1
            else:
                if f7 == 1:
                    raise RuntimeError("M extension instruction at %#x" % pc)
                b = self.reg(rs2)
                sub = f3 == 0 and f7 == 0x20
                arith = f3 == 5 and f7 == 0x20
            sh = b & 31
            if f3 == 0:
                r = a - b if sub else a + b
            elif f3 == 1:
                r = a << sh
            elif f3 == 2:
                r = int(sext(a, 32) < sext(b, 32))
            elif f3 == 3:
                r = int(a < b)
            elif f3 == 4:
                r = a ^ b
            elif f3 == 5:
                r = sext(a, 32) >> sh if arith else a >> sh
            elif f3 == 6:
                r = a | b
            else:
                r = a & b
            self.setreg(rd, r)
        elif opcode == 0x73 and f3 in (1, 2, 3) and (inst >> 20) == CSR_MCYCLE:
            self.setreg(rd, self.cycles)  # reads only; mcycle is never written
        else:
            raise RuntimeError("unsupported instruction %#010x at %#x" % (inst, pc))
        if taken:
            self.cycles += self.model["taken"]
        self.pc = next_pc
