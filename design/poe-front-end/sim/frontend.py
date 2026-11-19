#!/usr/bin/env python3
"""ngspice model of the discrete PoE front end. See ../README.md.

circuit() builds the netlist from the values in PARTS; run() runs ngspice on it.
The checks are in checks.py and the plots in plots.py.
"""
import os, re, subprocess, sys, tempfile, json

# Component values. Keys are the schematic reference designators.
PARTS = dict(
    R1=24.9e3,    # detection signature
    C1=100e-9,    # detection capacitor
    R2=4.7e3,     # class sink bias
    R3=10e3,      # Q2 base-emitter
    R4=None,      # class programming resistor (set per class)
    R5=1e6, R6=1e6,          # Q3 gate divider
    R7=100e3, R8=100e3,      # Q4 base network (window upper edge)
    R9=220e3, R10=220e3,       # Q5 base network (mark latch trigger)
    R11=22e3, R12=47e3,      # Q6 base network
    R13=10e3,     # mark load
    R14=270e3,    # mark latch hold
    R15=100e3, R16=470e3,     # Q7 base network (class event sense)
    R17=10e3,     # arm capacitor charge
    R18=220e3,    # arm capacitor bleed
    R19=1e6, R30=220e3,      # Q8 base network
    R20=47e3, R21=47e3,      # Q9 base network
    R22=68e3,    # hold capacitor charge
    R23=10e6,     # hold capacitor bleed
    R24=220e3, R25=470e3, R26=100e3,  # T2P level shift
    C2=220e-9,    # arm capacitor
    C3=220e-9,    # hold capacitor
    R27=750e3, R28=2e6,      # hot-swap gate network
    C4=330e-9, C5=6.8e-9,    # hot-swap gate and slew capacitors
    R29=1e3, C7=4.7e-9,      # class loop compensation
    R32=47e3,     # bleed for the leakage of D2
    C6=47e-6,     # bulk capacitor (input of the 5 V converter)
)
# Class programming resistor R4 per class, ohms (None: sink not fitted).
R4_CLASS = {0: None, 1: 140.0, 2: 73.2, 3: 47.5, 4: 31.6}
R4_CLASS4_T2P = 35.7   # Class 4 with the mark and two-event block fitted
ICLASS = {0: (0, 4e-3), 1: (9e-3, 12e-3), 2: (17e-3, 20e-3), 3: (26e-3, 30e-3), 4: (36e-3, 44e-3)}

MODELS = r"""
.model DBR D(IS=2n N=1.75 RS=0.05 BV=1000 CJO=20p TT=1u)
.model DSW D(IS=3n N=1.8 RS=1 BV=100 CJO=2p TT=4n)
.model DSCH D(IS=200n N=1.05 RS=2 BV=40 CJO=10p)
.model DZ10 D(IS=1f N=1 RS=4 BV={vz1} IBV=5m NBV=3 CJO=60p)
.model DZ22 D(IS=1f N=1 RS=15 BV={vz2} IBV=5m NBV=5 CJO=25p)
.model DZ24 D(IS=1f N=1 RS=15 BV={vz3} IBV=5m NBV=5 CJO=25p)
.model DZ12 D(IS=1f N=1 RS=8 BV=12 IBV=5m NBV=4 CJO=45p)
.model DTVS D(IS=1p N=1.5 RS=0.3 BV=67.8 IBV=1m NBV=8 CJO=300p)
.model QN NPN(IS=10f BF={bf} VAF=120 IKF=0.2 RB=20 RC=1 RE=0.2 CJE=15p CJC=4p TF=0.6n BR=4)
.model QNP NPN(IS=50f BF={bf} VAF=100 IKF=1 RB=5 RC=0.3 RE=0.1 CJE=80p CJC=20p TF=1n BR=4)
.model QPP PNP(IS=50f BF={bf} VAF=80 IKF=1 RB=5 RC=0.3 RE=0.1 CJE=80p CJC=25p TF=1.2n BR=4)
.model QP PNP(IS=10f BF={bf} VAF=100 IKF=0.2 RB=20 RC=1 RE=0.2 CJE=15p CJC=6p TF=0.8n BR=4)
.model MSIG VDMOS(VTO={vth} KP=0.25 RD=3 RS=0.5 RG=10 CGS=30p CGDMAX=20p CGDMIN=4p CJO=20p IS=1e-13 RB=1 LAMBDA=0.01)
.model MPWR VDMOS(VTO={vthp} KP=25 RD=60m RS=10m RG=3 CGS=1.2n CGDMAX=400p CGDMIN=25p CJO=300p IS=1e-11 RB=20m LAMBDA=0.005)
* TLV431: REF error drives a transconductance from cathode to anode
.subckt TLV431 k r a
Iref r a 0.15u
Eerr e 0 value={{ v(r,a)-{vref} }}
Rp e f 1k
Cp f 0 30n
Gk k a value={{ 20n + min(max(3*v(f)+0.03*v(e),0),20m)*(0.5+0.5*tanh((v(k,a)-0.9)*20)) }}
.ends
"""

def circuit(cls=4, t2p=True, vz1=10.0, vz2=22.0, vz3=24.0, vref=1.24, bf=150, vth=1.6, vthp=1.8, load='none',
            parts=None, rd2=45e6, cpse=100e-9):
    p = dict(PARTS)
    if parts:
        p.update(parts)
    p['R4'] = R4_CLASS4_T2P if (cls == 4 and t2p) else R4_CLASS[cls]
    if parts and parts.get('R4'):
        p['R4'] = parts['R4']
    L = [MODELS.format(vz1=vz1, vz2=vz2, vz3=vz3, vref=vref, bf=bf, vth=vth, vthp=vthp)]
    a = L.append
    # PSE side: source, series diode (a PSE cannot sink), cable loop resistance
    a("Dpse src pse DSCH")
    a(f"Cpse pse 0p {cpse}")   # output capacitance of the PSE
    a("Rcab pse pip {rcab}")
    a("V0p 0p pin 0")
    # one bridge (the second bridge is identical and idle)
    a("DB1 pip vdd DBR"); a("DB2 vss0 pin DBR"); a("DB3 pin vdd DBR"); a("DB4 vss0 pip DBR")
    a("Vvss vss0 0 0")       # current meter in the return leg
    a("Rleak pin 0 100meg")
    # detection signature, TVS
    a(f"R1 vdd 0 {p['R1']}"); a(f"C1 vdd 0 {p['C1']}"); a("D1 0 vdd DTVS")
    # class window switch Q3 (N-MOSFET), gate divider, upper edge Q4
    a("M3 css ng 0 MSIG"); a("Rcss css 0 1g"); a("Rcss2 vdd css 1g"); a("Cng ng 0 100p"); a("Ccss css 0 100p")   # stray leakage and capacitance
    a(f"R5 vdd ng {p['R5']}"); a(f"R6 ng 0 {p['R6']}")
    a("D3 nk vdd DZ22"); a(f"R7 nk nkb {p['R7']}"); a(f"R8 nkb 0 {p['R8']}"); a("Q4 ng nkb 0 QN")
    if cls:
        a("D2 na vdd DZ10"); a(f"Rd2 na vdd {rd2}"); a(f"R2 na nb {p['R2']}")   # Rd2: zener leakage, 0.2 uA at 9 V by default
        a(f"R32 na css {p['R32']}")   # carries the zener leakage past Q1
        a("XU1 nb nr css TLV431"); a(f"R29 ns nr {p['R29']}"); a(f"C7 nb nr {p['C7']}")
        a("Q1 nb2 nb ns QN"); a("Q2 ns nb2 vdd QPP"); a(f"R3 vdd nb2 {p['R3']}"); a(f"R4 ns css {p['R4']}")
    if cls and t2p:
        # mark latch
        a(f"R9 na nm {p['R9']}"); a(f"R10 nm css {p['R10']}"); a("Q5 nmc nm css QN")
        a(f"R11 nmc nmb {p['R11']}"); a(f"R12 vdd nmb {p['R12']}"); a("Q6 vm nmb vdd QP")
        a(f"R13 vm css {p['R13']}"); a(f"R14 vm nm {p['R14']}")
        # two-event detector
        a(f"R15 na nsb {p['R15']}"); a(f"R16 nsb css {p['R16']}"); a("Q7 nas nsb css QN")
        a(f"R17 vm nas {p['R17']}"); a("D4 nas narm DSCH"); a(f"C2 narm css {p['C2']}"); a(f"R18 narm css {p['R18']}")
        a("D8 narm vm DSCH"); a(f"R19 narm nab {p['R19']}"); a(f"R30 nab nas {p['R30']}"); a("Q8 npc nab nas QN")
        a(f"R20 npc npb {p['R20']}"); a(f"R21 vm npb {p['R21']}"); a("Q9 nt npb vm QP")
        a(f"R22 nt ntd {p['R22']}"); a("D5 ntd nx DSCH"); a("M10 nx ng nh MSIG")
        a(f"C3 nh 0 {p['C3']}"); a(f"R23 nh 0 {p['R23']}")
        # output: Q11 pulls the level shifter Q12, T2P is referenced to RTN (system ground)
        a("M11 nod nh 0 MSIG"); a(f"R24 nod nqb {p['R24']}"); a(f"R25 v33 nqb {p['R25']}"); a("Q12 t2p nqb v33 QP")
        a(f"R26 t2p rtn {p['R26']}")
        a("B33 v33 rtn V = 3.3*(0.5+0.5*tanh((v(vdd,rtn)-30)*2))")   # 3.3 V rail, present once the bulk capacitor is charged
    # hot swap
    a("D6 nz vdd DZ24"); a(f"R27 nz nhg {p['R27']}"); a(f"R28 nhg 0 {p['R28']}"); a("D7 0 nhg DZ12")
    a(f"C4 nhg 0 {p['C4']}"); a(f"C5 rtn nc5 {p['C5']}"); a("Rc5 nc5 nhg 100")
    a("M13 rtn nhg 0 MPWR")
    a(f"C6 vdd rtn {p['C6']}"); a("Rc6 vdd rtn 1meg")
    if load == 'cp':
        # converter: constant power above its enable threshold (38 V rising, 32.5 V falling)
        a("Ben en 0 V = v(vdd,rtn) > 38 ? 1 : (v(vdd,rtn) < 32.5 ? 0 : v(enh))")
        a("Ren en enh 1k"); a("Cen enh 0 1u")
        # the load is {pstart} W until {tstep} s (switch core only), then {pload} W (all ports and USB-C enabled by firmware)
        a("Vpl pl 0 PWL(0 {pstart} {tstep} {pstart} {tstep2} {pload})")
        a("Bload vdd rtn I = v(enh) > 0.5 ? v(pl)/max(v(vdd,rtn),20) : 0")
    return "\n".join(L)

def run(netlist, analysis, meas, **subs):
    text = "* poe front end\n" + netlist + "\n" + analysis + "\n.end\n"
    for k, v in subs.items():
        text = text.replace("{%s}" % k, str(v))
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "c.cir")
        open(f, "w").write(text)
        r = subprocess.run(["ngspice", "-b", f], capture_output=True, text=True, cwd=d)
        out = r.stdout + r.stderr
        data = None
        if os.path.exists(os.path.join(d, "out.txt")):
            rows = [l.split() for l in open(os.path.join(d, "out.txt")) if l.strip()]
            data = [[float(x) for x in row] for row in rows]
    vals = {}
    for m in meas:
        mm = re.search(r"^%s\s*=\s*([-+0-9.eE]+)" % m, out, re.M | re.I)
        vals[m] = float(mm.group(1)) if mm else None
    return vals, data, out
