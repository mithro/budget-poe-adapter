#!/usr/bin/env python3
"""Checks of the discrete PoE front end against the 802.3 PD limits, by simulation.

Run:  python3 checks.py            (about one minute on four cores; needs ngspice)
Writes results.md next to this file and exits non-zero when a check fails.
The limits are those of ../README.md, section "Requirements".
"""
import itertools, os, sys
from multiprocessing import Pool
from frontend import circuit, run, ICLASS

HERE = os.path.dirname(os.path.abspath(__file__))
ROWS = []
FAILED = []
DATA = {"static": [], "sequence": [], "latch": [], "idle": None, "power": [], "inrush": []}


def row(group, check, result, limit, ok):
    ROWS.append((group, check, result, limit, "Pass" if ok else "Fail"))
    if not ok:
        FAILED.append(check)
    print(("PASS " if ok else "FAIL ") + f"{group}: {check}: {result} (limit {limit})", flush=True)


def tran(net, pwl, tstop, tstep, cols, rcab=1.0, temp=27, pload=0, pstart=None, tload=1e-3):
    """Transient run. A run that stops early is repeated with other solver settings."""
    for opts, step in (("reltol=1e-4 method=gear", tstep), ("reltol=1e-3 method=gear", tstep / 2),
                       ("reltol=1e-3 method=trap", tstep / 4), ("reltol=3e-3 method=gear cshunt=1e-13", tstep / 4)):
        an = (f"Vpse src pin PWL({pwl})\n.options gmin=1e-12 abstol=1e-11 itl4=300 {opts} temp={temp}\n"
              f".control\ntran {step} {tstop} 0 {step}\nwrdata out.txt {' '.join(cols)}\n.endc")
        vals, data, out = run(net, an, [], rcab=rcab, pload=pload, pstart=pload if pstart is None else pstart,
                              tstep=tload, tstep2=tload + 1e-3)
        if data is not None and data[-1][0] >= tstop * 0.999:
            return [[r[0]] + r[1::2] for r in data]
    print(out[-2000:])
    raise SystemExit("simulation did not finish")


def corner(temp, tolz, vref, bf, tol2):
    """Zener voltages follow temperature: 10 V part +6 mV/K, 22 V part +0.08 %/K."""
    return dict(vz1=(10 + 0.006 * (temp - 27)) * tolz, vref=vref, bf=bf, vz2=22 * tol2 * (1 + 0.0008 * (temp - 27)))


CORNERS = [(t, corner(t, tolz, vref, bf, tol2)) for t, tolz, vref, bf, tol2 in
           itertools.product((0, 70), (0.98, 1.02), (1.2214, 1.2586), (60, 300), (0.95, 1.05))]


# Zener D2 with ten times its 25 °C leakage limit (2 µA at 9 V), at the two transistor gains
LEAKY = [(70, dict(rd2=4.5e6, bf=60, vz1=10 + 0.006 * 43)), (70, dict(rd2=4.5e6, bf=300, vz1=10 + 0.006 * 43))]


def sweep(cls, t2p, temp=27, **kw):
    """Slow ramp of the PSE voltage from 0 to 31 V. Returns (PI voltage, PI current) pairs."""
    d = tran(circuit(cls=cls, t2p=t2p, **kw), "0 0 0.6 31", 0.6, 2.5e-4, ["v(pip,pin)", "i(Vvss)"], temp=temp)
    return [(r[1], -r[2]) for r in d]


def at(d, v):
    return min(d, key=lambda r: abs(r[0] - v))


def detection(d):
    """Slope over 1 V chords from 2.7 V to 10.1 V and the voltage offset, as test 33.1.3 of the UNH-IOL suite."""
    rs, v = [], 2.7
    while v + 1 <= 10.1001:
        a, b = at(d, v), at(d, v + 1)
        rs.append((b[0] - a[0]) / (b[1] - a[1]))
        v += 0.2
    a, b = at(d, 2.7), at(d, 10.1)
    r = (b[0] - a[0]) / (b[1] - a[1])
    return min(rs), max(rs), a[0] - a[1] * r


def static_point(job):
    cls, t2p, temp, kw = job
    d = sweep(cls, t2p, temp=temp, **kw)
    i = [x[1] for x in d if 14.5 <= x[0] <= 20.5]
    on = min(x[0] for x in d if x[1] > 3e-3) if cls else None
    off = min(x[0] for x in d if x[0] > 20.5 and x[1] < 2.2e-3) if cls else None
    return (min(i), max(i)) + detection(d) + (on, off)


def corner_point(job):
    (name, ev, rcab, expect, kw), vth, bf, temp = job
    ok, _ = sequence(name, ev, rcab, expect, temp=temp, quiet=True, vth=vth, bf=bf,
                     vz1=10 + 0.006 * (temp - 27), vz2=22 * (1 + 0.0008 * (temp - 27)), **kw)
    return None if ok else f"{name}, Vth {vth} V, gain {bf}, {temp} °C"


def check_static():
    variants = ((0, False, "Class 0"), (1, False, "Class 1"), (2, False, "Class 2"), (3, False, "Class 3"),
                (4, False, "Class 4"), (4, True, "Class 4 with two-event block"))
    for cls, t2p, name in variants:
        lo, hi = ICLASS[cls]
        jobs = [(cls, t2p, temp, kw) for temp, kw in ([(27, {})] + CORNERS + LEAKY if cls else [(0, {}), (27, {}), (70, {})])]
        with Pool(os.cpu_count()) as pool:
            res = pool.map(static_point, jobs)
        rmin, rmax = min(r[2] for r in res), max(r[3] for r in res)
        row(name, "Detection slope, 2.7 V to 10.1 V", f"{rmin/1e3:.2f} kΩ to {rmax/1e3:.2f} kΩ", "23.75 kΩ to 26.25 kΩ",
            23750 <= rmin and rmax <= 26250)
        voff = max(r[4] for r in res)
        row(name, "Detection voltage offset", f"{voff:.2f} V", "1.9 V maximum", voff <= 1.9)
        imin, imax = min(r[0] for r in res), max(r[1] for r in res)
        row(name, "Class current, 14.5 V to 20.5 V", f"{imin*1e3:.2f} mA to {imax*1e3:.2f} mA",
            f"{lo*1e3:.0f} mA to {hi*1e3:.0f} mA", lo <= imin and imax <= hi)
        DATA["static"].append(dict(name=name, rmin=rmin, rmax=rmax, voff=voff, imin=imin, imax=imax, lo=lo, hi=hi,
                                   on=(min(r[5] for r in res), max(r[5] for r in res)) if cls else None,
                                   off=(min(r[6] for r in res), max(r[6] for r in res)) if cls else None, runs=len(res)))
        if cls:
            on = (min(r[5] for r in res), max(r[5] for r in res))
            off = (min(r[6] for r in res), max(r[6] for r in res))
            row(name, "Class sink turns on", f"{on[0]:.1f} V to {on[1]:.1f} V", "10.1 V to 14.5 V", 10.1 < on[0] and on[1] < 14.5)
            row(name, "Class sink turns off", f"{off[0]:.1f} V to {off[1]:.1f} V", "20.5 V to 30 V", 20.5 < off[0] and off[1] < 30)


COLS = ["v(pip,pin)", "i(Vvss)", "v(vdd)", "v(vm)", "v(narm)", "v(nh)", "v(t2p,rtn)", "v(vdd,rtn)", "v(rtn)", "v(nhg)"]
DET = [(4, 0.02), (8, 0.02)]


def pwl(events, tr):
    t, pts = 0, ["0 0"]
    for v, dur in events:
        pts.append(f"{t+tr:.6f} {v}")
        t += dur
        pts.append(f"{t:.6f} {v}")
    return " ".join(pts), t


def sequence(name, events, rcab, expect, tr=2e-4, temp=27, quiet=False, **kw):
    """One PSE sequence into a Class 4 front end with the two-event block and a 3 W converter load."""
    text, T = pwl(events, tr)
    d = tran(circuit(cls=4, t2p=True, load='cp', **kw), text, T, 5e-5, COLS, rcab=rcab, temp=temp, pload=3)
    t2p, ipk, bulk = d[-1][7], max(-r[2] for r in d), d[-1][8]
    mk, cl, t, seen = [], [], 0, False
    for v, dur in events:
        mid = min(d, key=lambda r: abs(r[0] - (t + dur * 0.75)))
        if 14.5 <= v <= 20.5:
            cl.append(-mid[2]); seen = True
        elif 6.9 <= v <= 10 and seen:
            mk.append(-mid[2])
        t += dur
    ok = ((t2p > 2.9) == expect and (t2p > 2.9 or t2p < 0.3) and all(0.25e-3 <= i <= 4e-3 for i in mk)
          and all(36e-3 <= i <= 44e-3 for i in cl) and ipk < 0.4 and bulk > 40)
    if not quiet:
        DATA["sequence"].append(dict(name=name, expect=expect, t2p=t2p > 2.9, mk=mk, ipk=ipk, rcab=rcab, bulk=bulk))
        row("Sequence", name + ": T2P", "High" if t2p > 2.9 else "Low", "High" if expect else "Low", (t2p > 2.9) == expect)
        if mk:
            row("Sequence", name + ": mark current", f"{min(mk)*1e3:.2f} mA to {max(mk)*1e3:.2f} mA", "0.25 mA to 4 mA",
                all(0.25e-3 <= i <= 4e-3 for i in mk))
        row("Sequence", name + ": peak inrush current", f"{ipk*1e3:.0f} mA", "400 mA maximum", ipk < 0.4)
    return ok, d


TWO = lambda vc, tc, vm, tm, vp: DET + [(vc, tc), (vm, tm), (vc, tc), (vm, tm), (vp, 0.25)]
ONE = DET + [(17.5, 0.02)]
SEQS = [
    ("Type 2 PSE with two events at mid values", TWO(17.5, 0.015, 8.5, 0.008, 54), 12.5, True, {}),
    ("Type 2 PSE with two events at the shortest times and lowest voltages", TWO(15.5, 0.006, 7.0, 0.006, 50), 20, True, {}),
    ("Type 2 PSE with two events at the longest times and highest voltages", TWO(20.5, 0.03, 10, 0.012, 57), 0.5, True, {}),
    ("Type 3 PSE with a long first event and three events",
     DET + [(17.5, 0.095), (8.5, 0.008), (17.5, 0.012), (8.5, 0.008), (17.5, 0.012), (8.5, 0.008), (54, 0.25)], 12.5, True, {}),
    ("Type 1 PSE with one event then power", ONE + [(48, 0.25)], 20, False, {}),
    ("Type 1 PSE with one event then 0 V for 20 ms", ONE + [(0, 0.02), (48, 0.25)], 20, False, {}),
    ("Type 1 PSE with one event then 0 V for 3 ms", DET + [(20.5, 0.075), (0, 0.003), (57, 0.25)], 0.5, False, {}),
    ("Type 1 PSE with one event then 0 V for 3 ms and a 1 ms rise", DET + [(20.5, 0.075), (0, 0.003), (57, 0.25)], 0.5, False, dict(tr=1e-3)),
    ("Type 1 PSE with one event then 8 V for 5 ms and a 1 ms rise", ONE + [(8, 0.005), (48, 0.25)], 12.5, False, dict(tr=1e-3)),
    ("Type 1 PSE with 1 µF at its output released for 3 ms and a 1 ms rise", ONE + [(0, 0.003), (48, 0.25)], 12.5, False, dict(tr=1e-3, cpse=1e-6)),
    ("Passive 48 V supply applied at once", [(48, 0.3)], 2, False, {}),
]


def check_sequences():
    for name, ev, rcab, expect, kw in SEQS:
        sequence(name, ev, rcab, expect, **kw)
    # the two-event decision at part corners: MOSFET threshold, transistor gain, temperature
    jobs = [(q, vth, bf, temp) for vth, bf, temp in itertools.product((1.0, 2.5), (60, 300), (0, 70))
            for q in (SEQS[1], SEQS[2], SEQS[6], SEQS[7], SEQS[8], SEQS[9])]
    with Pool(os.cpu_count()) as pool:
        bad = [b for b in pool.map(corner_point, jobs) if b]
    DATA["corners"] = (len(jobs) - len(bad), len(jobs))
    row("Sequence", "Six sequences at eight part corners", f"{len(jobs) - len(bad)} of {len(jobs)} correct", "all", not bad)
    for b in bad:
        print("   corner failed:", b)


def check_inrush():
    """Inrush at the part tolerances that raise it, on the stiffest source: 57 V behind 0.5 Ω."""
    worst = dict(vz3=24 * 0.95, vthp=1.0, parts=dict(C6=47e-6 * 1.2, C5=6.8e-9 * 0.9))
    for label, kw in (("nominal parts", {}), ("C6 +20 %, C5 -10 %, D6 -5 %, Q13 threshold 1.0 V", worst)):
        text, T = pwl(TWO(20.5, 0.03, 10, 0.012, 57), 2e-4)
        d = tran(circuit(cls=4, t2p=True, load='cp', **kw), text, T, 5e-5, COLS, rcab=0.5, pload=3)
        ipk = max(-r[2] for r in d)
        DATA["inrush"].append(ipk)
        row("Inrush", f"Peak inrush current, {label}", f"{ipk*1e3:.0f} mA", "400 mA maximum", ipk < 0.4)


def check_reset_and_idle():
    # mark latch release: one class event, then a slow fall
    for temp in (0, 70):
        d = tran(circuit(cls=4, t2p=True), "0 0 1m 17.5 10m 17.5 11m 9 211m 1", 0.211, 1e-4, ["v(pip,pin)", "v(vm)", "i(Vvss)"], temp=temp)
        rel = max(r[1] for r in d if r[0] > 0.012 and r[2] < 0.5)
        DATA["latch"].append((temp, rel))
        row("Mark latch", f"Release voltage at {temp} °C", f"{rel:.2f} V", "2.81 V to 6.9 V", 2.81 < rel < 6.9)
    # current drawn by the front end alone at 57 V
    d = tran(circuit(cls=4, t2p=True), "0 0 0.2 57 0.4 57", 0.4, 2e-4, ["v(pip,pin)", "i(Vvss)", "v(vdd)"])
    iq = -d[-1][2]
    DATA["idle"] = iq
    # how long T2P stays high after power-up, at the lowest and the highest gate threshold of Q10 and Q11
    DATA["hold"] = []
    for seq, vc, tc, vm, tm, vp, rcab in (("mid", 17.5, 0.015, 8.5, 0.008, 54, 12.5), ("shortest", 15.5, 0.006, 7.0, 0.006, 50, 20)):
        ev = TWO(vc, tc, vm, tm, vp)[:-1] + [(vp, 6.0)]
        for vth in (1.0, 2.5):
            text, T = pwl(ev, 2e-4)
            # the shortest hold: C3 and R23 at their low tolerance (-10 % and -1 %) with the high threshold
            low = dict(parts=dict(C3=220e-9 * 0.9, R23=10e6 * 0.99)) if vth == 2.5 else {}
            d = tran(circuit(cls=4, t2p=True, load='cp', vth=vth, **low), text, T, 2e-4, COLS, rcab=rcab, pload=3)
            t_on = next(r[0] for r in d if r[7] > 2.9)
            t_off = next((r[0] for r in d if r[0] > t_on and r[7] < 2.9), T)
            DATA["hold"].append((seq, vth, t_off - t_on))
            row("Powered", f"T2P stays high, {seq} sequence, gate threshold {vth} V", f"{t_off - t_on:.1f} s", "Information", True)
    row("Powered", "Front end current at 57 V", f"{iq*1e3:.2f} mA", "Information", True)


def check_power():
    # turn-on with 3 W (switch core only), load step to full power at 0.2 s, then a brown-out and recovery.
    # converter model: enable at 38 V, disable at 32.5 V across the bulk capacitor
    for name, rcab, pload in (("12.5 W converter load on a 20 Ω loop", 20, 12.5), ("24.5 W converter load on a 12.5 Ω loop", 12.5, 24.5)):
        vmin = 44 if rcab == 20 else 50
        text = f"0 0 0.001 17.5 0.02 17.5 0.0202 {vmin} 0.3 {vmin} 0.7 26 1.1 {vmin+7} 1.3 {vmin+7}"
        pts = [float(x) for x in text.split()]
        vpse = lambda t: next(v0 + (v1 - v0) * (t - t0) / (t1 - t0) for t0, v0, t1, v1 in
                              zip(pts[0::2], pts[1::2], pts[2::2], pts[3::2]) if t0 <= t <= t1)
        d = tran(circuit(cls=4, t2p=True, load='cp'), text, 1.3, 1e-4,
                 ["v(pip,pin)", "i(Vvss)", "v(vdd,rtn)", "v(rtn)", "v(enh)"], rcab=rcab, pload=pload, pstart=3, tload=0.2)
        run_ = [r for r in d if r[5] > 0.5]
        first_on = run_[0][1]
        falling = [r for r in d if 0.3 < r[0] < 0.7]
        off = next(r for r in falling if r[5] < 0.5)
        stay = [r[5] for r in d if 0.25 < r[0] < 0.3]
        edges = [a for a, b in zip(d, d[1:]) if (a[5] > 0.5) != (b[5] > 0.5)]
        steady = sum(1 for a in edges if a[0] < 0.3)
        cyc = [vpse(a[0]) for a in edges if a[0] >= 0.3]
        drop = max(r[4] for r in d if 0.25 < r[0] < 0.3)
        DATA["power"].append(dict(name=name, rcab=rcab, pload=pload, vmin=vmin, stay=min(stay) > 0.5, off=off[1], steady=steady,
                                  restart=d[-1][5] > 0.5, cyc=(min(cyc), max(cyc)), drop=drop))
        row("Power", f"{name}: runs at the lowest PSE voltage", "Yes" if min(stay) > 0.5 else "No", "Yes", min(stay) > 0.5)
        row("Power", f"{name}: converter stops at a PI voltage of", f"{off[1]:.1f} V", "30 V to 36 V", 30 <= off[1] < 36)
        row("Power", f"{name}: converter state changes at a valid PSE voltage", str(steady), "1", steady == 1)
        row("Power", f"{name}: converter restarts when the PSE voltage returns", "Yes" if d[-1][5] > 0.5 else "No", "Yes", d[-1][5] > 0.5)
        row("Power", f"{name}: PSE voltage span with on-off cycling", f"{min(cyc):.1f} V to {max(cyc):.1f} V", "Information", True)
        row("Power", f"{name}: hot-swap MOSFET drop while running", f"{drop*1e3:.0f} mV", "Information", True)


def write_results():
    v = lambda ok: "Pass" if ok else "Fail"
    yn = lambda b: "Yes" if b else "No"
    hl = lambda b: "High" if b else "Low"
    L = []
    L += ["| Variant | Slope minimum (kΩ) | Slope maximum (kΩ) | Voltage offset (V) | Runs | Verdict |", "| --- | --- | --- | --- | --- | --- |"]
    for r in DATA["static"]:
        ok = 23750 <= r["rmin"] and r["rmax"] <= 26250 and r["voff"] <= 1.9
        L.append(f"| {r['name']} | {r['rmin']/1e3:.2f} | {r['rmax']/1e3:.2f} | {r['voff']:.2f} | {r['runs']} | {v(ok)} |")
    L += ["", "| Variant | Current minimum (mA) | Current maximum (mA) | Limit minimum (mA) | Limit maximum (mA) | Verdict |", "| --- | --- | --- | --- | --- | --- |"]
    for r in DATA["static"]:
        ok = r["lo"] <= r["imin"] and r["imax"] <= r["hi"]
        L.append(f"| {r['name']} | {r['imin']*1e3:.2f} | {r['imax']*1e3:.2f} | {r['lo']*1e3:.0f} | {r['hi']*1e3:.0f} | {v(ok)} |")
    L += ["", "| Variant | Turn-on minimum (V) | Turn-on maximum (V) | Turn-off minimum (V) | Turn-off maximum (V) | Verdict |", "| --- | --- | --- | --- | --- | --- |"]
    for r in DATA["static"]:
        if r["on"]:
            ok = 10.1 < r["on"][0] and r["on"][1] < 14.5 and 20.5 < r["off"][0] and r["off"][1] < 30
            L.append(f"| {r['name']} | {r['on'][0]:.1f} | {r['on'][1]:.1f} | {r['off'][0]:.1f} | {r['off'][1]:.1f} | {v(ok)} |")
    L += ["", "| Sequence | Cable loop (Ω) | T2P expected | T2P simulated | Mark current minimum (mA) | Mark current maximum (mA) | Peak inrush current (mA) | Verdict |",
          "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in DATA["sequence"]:
        ok = r["t2p"] == r["expect"] and all(0.25e-3 <= i <= 4e-3 for i in r["mk"]) and r["ipk"] < 0.4
        mk = (f"{min(r['mk'])*1e3:.2f}", f"{max(r['mk'])*1e3:.2f}") if r["mk"] else ("–", "–")
        L.append(f"| {r['name']} | {r['rcab']} | {hl(r['expect'])} | {hl(r['t2p'])} | {mk[0]} | {mk[1]} | {r['ipk']*1e3:.0f} | {v(ok)} |")
    L += ["", "| Quantity | Value | Unit | Limit minimum | Limit maximum | Verdict |", "| --- | --- | --- | --- | --- | --- |"]
    L.append(f"| Sequence runs decided correctly at the part corners | {DATA['corners'][0]} | of {DATA['corners'][1]} | {DATA['corners'][1]} | {DATA['corners'][1]} | {v(DATA['corners'][0] == DATA['corners'][1])} |")
    for temp, rel in DATA["latch"]:
        L.append(f"| Mark latch release voltage at {temp} °C | {rel:.2f} | V | 2.81 | 6.9 | {v(2.81 < rel < 6.9)} |")
    L.append(f"| Front end current at 57 V | {DATA['idle']*1e3:.2f} | mA | – | – | Information |")
    L.append(f"| Peak inrush current with nominal parts | {DATA['inrush'][0]*1e3:.0f} | mA | – | 400 | {v(DATA['inrush'][0] < 0.4)} |")
    L.append(f"| Peak inrush current at the part tolerances that raise it | {DATA['inrush'][1]*1e3:.0f} | mA | – | 400 | {v(DATA['inrush'][1] < 0.4)} |")
    for seq, vth, hold in DATA["hold"]:
        L.append(f"| T2P stays high after the {seq} sequence with a gate threshold of {vth} V | {hold:.1f} | s | – | – | Information |")
    L += ["", "| Case | PSE voltage (V) | Runs at that voltage | Converter stops at (V) | Restarts | Cycling from (V) | Cycling to (V) | Q13 drop (mV) | Verdict |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in DATA["power"]:
        ok = r["stay"] and 30 <= r["off"] < 36 and r["steady"] == 1 and r["restart"]
        L.append(f"| {r['name']} | {r['vmin']} | {yn(r['stay'])} | {r['off']:.1f} | {yn(r['restart'])} | {r['cyc'][0]:.1f} | {r['cyc'][1]:.1f} | {r['drop']*1e3:.0f} | {v(ok)} |")
    head = ("---\norphan: true\n---\n\n# Simulation results of the PoE front end\n\n"
            "Written by [`checks.py`](checks.py). The tables are explained in the\n"
            "[Simulation section of the design note](../README.md#simulation).\n\n")
    open(os.path.join(HERE, "results.md"), "w").write(head + "\n".join(L) + "\n")


if __name__ == "__main__":
    check_static()
    check_sequences()
    check_inrush()
    check_reset_and_idle()
    check_power()
    write_results()
    print("failed:", FAILED)
    sys.exit(1 if FAILED else 0)
