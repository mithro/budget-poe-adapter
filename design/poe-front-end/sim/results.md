---
orphan: true
---

# Simulation results of the PoE front end

Written by [`checks.py`](checks.py). The tables are explained in the
[Simulation section of the design note](../README.md#simulation).

| Variant | Slope minimum (kΩ) | Slope maximum (kΩ) | Voltage offset (V) | Runs | Verdict |
| --- | --- | --- | --- | --- | --- |
| Class 0 | 25.14 | 25.87 | 0.91 | 3 | Pass |
| Class 1 | 24.73 | 25.51 | 0.92 | 35 | Pass |
| Class 2 | 24.73 | 25.51 | 0.92 | 35 | Pass |
| Class 3 | 24.73 | 25.51 | 0.92 | 35 | Pass |
| Class 4 | 24.73 | 25.51 | 0.92 | 35 | Pass |
| Class 4 with two-event block | 24.72 | 25.51 | 0.92 | 35 | Pass |

| Variant | Current minimum (mA) | Current maximum (mA) | Limit minimum (mA) | Limit maximum (mA) | Verdict |
| --- | --- | --- | --- | --- | --- |
| Class 0 | 0.54 | 0.79 | 0 | 4 | Pass |
| Class 1 | 9.59 | 11.56 | 9 | 12 | Pass |
| Class 2 | 17.53 | 19.75 | 17 | 20 | Pass |
| Class 3 | 26.53 | 29.04 | 26 | 30 | Pass |
| Class 4 | 39.45 | 42.36 | 36 | 44 | Pass |
| Class 4 with two-event block | 38.13 | 42.67 | 36 | 44 | Pass |

| Variant | Turn-on minimum (V) | Turn-on maximum (V) | Turn-off minimum (V) | Turn-off maximum (V) | Verdict |
| --- | --- | --- | --- | --- | --- |
| Class 1 | 11.6 | 12.1 | 22.5 | 25.2 | Pass |
| Class 2 | 11.4 | 11.9 | 22.5 | 25.3 | Pass |
| Class 3 | 11.3 | 11.8 | 22.6 | 25.4 | Pass |
| Class 4 | 11.2 | 11.8 | 22.7 | 25.5 | Pass |
| Class 4 with two-event block | 11.3 | 11.8 | 22.7 | 25.5 | Pass |

| Sequence | Cable loop (Ω) | T2P expected | T2P simulated | Mark current minimum (mA) | Mark current maximum (mA) | Peak inrush current (mA) | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Type 2 PSE with two events at mid values | 12.5 | High | High | 1.37 | 1.37 | 210 | Pass |
| Type 2 PSE with two events at the shortest times and lowest voltages | 20 | High | High | 1.06 | 1.10 | 171 | Pass |
| Type 2 PSE with two events at the longest times and highest voltages | 0.5 | High | High | 1.63 | 1.66 | 250 | Pass |
| Type 3 PSE with a long first event and three events | 12.5 | High | High | 1.36 | 1.37 | 210 | Pass |
| Type 1 PSE with one event then power | 20 | Low | Low | – | – | 155 | Pass |
| Type 1 PSE with one event then 0 V for 20 ms | 20 | Low | Low | – | – | 155 | Pass |
| Type 1 PSE with one event then 0 V for 3 ms | 0.5 | Low | Low | – | – | 250 | Pass |
| Type 1 PSE with one event then 0 V for 3 ms and a 1 ms rise | 0.5 | Low | Low | – | – | 250 | Pass |
| Type 1 PSE with one event then 8 V for 5 ms and a 1 ms rise | 12.5 | Low | Low | 1.35 | 1.35 | 168 | Pass |
| Type 1 PSE with 1 µF at its output released for 3 ms and a 1 ms rise | 12.5 | Low | Low | – | – | 168 | Pass |
| Passive 48 V supply applied at once | 2 | Low | Low | – | – | 187 | Pass |

| Quantity | Value | Unit | Limit minimum | Limit maximum | Verdict |
| --- | --- | --- | --- | --- | --- |
| Sequence runs decided correctly at the part corners | 48 | of 48 | 48 | 48 | Pass |
| Mark latch release voltage at 0 °C | 4.14 | V | 2.81 | 6.9 | Pass |
| Mark latch release voltage at 70 °C | 3.83 | V | 2.81 | 6.9 | Pass |
| Front end current at 57 V | 2.69 | mA | – | – | Information |
| Peak inrush current with nominal parts | 250 | mA | – | 400 | Pass |
| Peak inrush current at the part tolerances that raise it | 326 | mA | – | 400 | Pass |
| T2P stays high after the mid sequence with a gate threshold of 1.0 V | 5.1 | s | – | – | Information |
| T2P stays high after the mid sequence with a gate threshold of 2.5 V | 1.8 | s | – | – | Information |
| T2P stays high after the shortest sequence with a gate threshold of 1.0 V | 4.0 | s | – | – | Information |
| T2P stays high after the shortest sequence with a gate threshold of 2.5 V | 1.3 | s | – | – | Information |

| Case | PSE voltage (V) | Runs at that voltage | Converter stops at (V) | Restarts | Cycling from (V) | Cycling to (V) | Q13 drop (mV) | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12.5 W converter load on a 20 Ω loop | 44 | Yes | 34.3 | Yes | 39.7 | 43.1 | 29 | Pass |
| 24.5 W converter load on a 12.5 Ω loop | 50 | Yes | 34.4 | Yes | 39.8 | 45.8 | 48 | Pass |
