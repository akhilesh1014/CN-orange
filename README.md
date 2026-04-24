# QoS Latency Experiment

A Mininet + Ryu SDN experiment demonstrating how OVS queue-based QoS protects ICMP (ping) latency under TCP flood congestion.

---

## Architecture

```
h1 — s1 — s2 — s3 — h2
               |
              h3
s3 — s4 — s5
```

- **Links:** 1 Mbps, 10ms delay each hop
- **Queue 0 (HIGH):** ICMP + UDP → 950 Kbps guaranteed
- **Queue 1 (LOW):** TCP flood → max 500 Kbps, no guarantees

---

## Prerequisites

- Mininet installed
- Ryu SDN framework (`ryu-manager` available)
- OVS (Open vSwitch) installed
- `qos_controller.py` and `topology.py` in working directory

---

## Setup (run once at the start)

**Terminal 1 — Start Ryu controller**
```bash
ryu-manager qos_controller.py
```

**Terminal 2 — Start Mininet**
```bash
sudo mn -c && sudo mn --controller=remote --custom topology.py --topo=customtopo --link=tc --switch=ovsk,protocols=OpenFlow13
```

**Terminal 3 — Apply OVS queues on backbone ports**
```bash
sudo ovs-vsctl set port s1-eth2 qos=@q1 -- --id=@q1 create qos type=linux-htb queues:0=@hi1 queues:1=@lo1 -- --id=@hi1 create queue other-config:min-rate=950000 other-config:max-rate=1000000 -- --id=@lo1 create queue other-config:min-rate=10000 other-config:max-rate=500000
```
```bash
sudo ovs-vsctl set port s2-eth1 qos=@q2 -- --id=@q2 create qos type=linux-htb queues:0=@hi2 queues:1=@lo2 -- --id=@hi2 create queue other-config:min-rate=950000 other-config:max-rate=1000000 -- --id=@lo2 create queue other-config:min-rate=10000 other-config:max-rate=500000
```
```bash
sudo ovs-vsctl set port s2-eth2 qos=@q3 -- --id=@q3 create qos type=linux-htb queues:0=@hi3 queues:1=@lo3 -- --id=@hi3 create queue other-config:min-rate=950000 other-config:max-rate=1000000 -- --id=@lo3 create queue other-config:min-rate=10000 other-config:max-rate=500000
```
```bash
sudo ovs-vsctl set port s3-eth1 qos=@q4 -- --id=@q4 create qos type=linux-htb queues:0=@hi4 queues:1=@lo4 -- --id=@hi4 create queue other-config:min-rate=950000 other-config:max-rate=1000000 -- --id=@lo4 create queue other-config:min-rate=10000 other-config:max-rate=500000
```
```bash
sudo ovs-vsctl set port s3-eth2 qos=@q5 -- --id=@q5 create qos type=linux-htb queues:0=@hi5 queues:1=@lo5 -- --id=@hi5 create queue other-config:min-rate=950000 other-config:max-rate=1000000 -- --id=@lo5 create queue other-config:min-rate=10000 other-config:max-rate=500000
```

---

## Situation 1 — Baseline (No Congestion)

**Controller:** `qos_controller.py`

Run inside Mininet CLI:
```bash
h1 ping -c 200 -i 0.1 h2
```

Note down `avg` and `max` from the ping summary. Then clean up:
```bash
exit
sudo mn -c
sudo ovs-vsctl --all destroy qos
sudo ovs-vsctl --all destroy queue
```

**Expected:** ~40–50 ms avg (2 hops × 10ms delay + processing overhead)

---

## Situation 2 — QoS ON, Congested

**Controller:** `qos_controller.py` (keep running from Terminal 1)

**Terminal 2 — Restart Mininet**
```bash
sudo mn --controller=remote --custom topology.py --topo=customtopo --link=tc --switch=ovsk,protocols=OpenFlow13
```

**Terminal 3 — Re-apply queues** (same 5 commands as Setup above)

**Mininet CLI — Start flood and record ping**
```bash
h2 iperf -s &
h3 iperf -c h2 -t 60 -P 20 &
```

Wait 5 seconds for congestion to establish, then:
```bash
h1 ping -c 200 -i 0.1 h2
```

Note down `avg` and `max`. Then clean up:
```bash
exit
sudo mn -c
sudo ovs-vsctl --all destroy qos
sudo ovs-vsctl --all destroy queue
```

**Expected:** avg close to Situation 1 — ICMP is in Queue 0, TCP flood is throttled in Queue 1

---

## Situation 3 — QoS OFF, Congested

**Terminal 1 — Stop qos_controller (Ctrl+C), switch to simple switch**
```bash
ryu-manager ryu.app.simple_switch_13
```

**Terminal 2 — Restart Mininet**
```bash
sudo mn --controller=remote --custom topology.py --topo=customtopo --link=tc --switch=ovsk,protocols=OpenFlow13
```

**Terminal 3 — Re-apply queues** (same 5 commands as Setup above)

**Mininet CLI — Start flood and record ping**
```bash
h2 iperf -s &
h3 iperf -c h2 -t 60 -P 20 &
```

Wait 5 seconds, then:
```bash
h1 ping -c 200 -i 0.1 h2
```

Note down `avg` and `max`.

**Expected:** avg clearly higher than Situation 2 — no queue separation, ICMP competes equally with TCP flood

---

## Cleanup

```bash
exit
sudo mn -c
sudo ovs-vsctl --all destroy qos
sudo ovs-vsctl --all destroy queue
```

---

## Expected Results

| Situation | Condition | Expected avg latency |
|-----------|-----------|----------------------|
| S1 | Baseline, no congestion | ~45 ms |
| S2 | QoS ON, TCP flood | ≈ S1 (protected) |
| S3 | QoS OFF, TCP flood | S1 + 30–100 ms spike |

**Conclusion:** S1 ≈ S2 << S3 — QoS controller successfully protects ICMP latency under congestion using 2-queue HTB scheduling.

---

## Queue Design

| Queue | Traffic | Min rate | Max rate |
|-------|---------|----------|----------|
| 0 — HIGH | ICMP, UDP | 950 Kbps | 1 Mbps |
| 1 — LOW  | TCP | 10 Kbps | 500 Kbps |
