# SDN QoS Priority Controller

## Overview
This project is about implementing a simple SDN controller using Ryu that prioritizes different types of network traffic. The controller gives higher priority to UDP traffic compared to TCP using OpenFlow rules.

---

## Objective
The goal is to:
- Identify traffic types (UDP, TCP, etc.)
- Assign higher priority to UDP
- Assign lower priority to TCP
- Install flow rules dynamically using SDN

---

## Tools Used
- Python 3.10
- Ryu Controller
- Mininet
- Open vSwitch
- OpenFlow 1.3

---

## Network Topology
A custom topology is created using Mininet Python API.

It consists of:
- 3 Hosts: h1, h2, h3  
- 3 Switches: s1, s2, s3  

Topology structure:

h1 — s1 — s2 — s3 — h3  
         |  
        h2  

---

## How it Works
- When a packet arrives at the switch, it is sent to the controller (if no rule exists)
- The controller checks the protocol:
  - UDP → high priority (100)
  - TCP → low priority (10)
- Based on this, a flow rule is installed in the switch
- Future packets are handled directly by the switch

---

## Flow Rules

| Traffic | Protocol | Priority |
|--------|----------|----------|
| UDP    | 17       | 100      |
| TCP    | 6        | 10       |
| Others | Any      | 1        |
| ARP    | —        | Flood    |

---

## Steps to Run

### 1. Activate virtual environment
```bash
cd ~/CN
source ryu-env/bin/activate
2. Start controller
python -m ryu.cmd.manager qos_controller.py
3. Run Mininet (in new terminal)
sudo mn --custom topology.py --topo customtopo --controller=remote
4. Test connectivity
pingall
5. Start server
h2 iperf -s &
h2 iperf -u -s &
6. Run tests

UDP test:

h1 iperf -u -c h2

TCP test:

h1 iperf -c h2
Output
Ping test shows 0% packet loss
UDP traffic gets higher priority
TCP traffic gets lower priority

Flow rules can be checked using:

sh ovs-ofctl dump-flows s1
Conclusion

This project shows how SDN can be used to control network behavior. By assigning priorities using flow rules, we can manage traffic efficiently. It also demonstrates how flexible SDN is compared to traditional networking.

Files
qos_controller.py → controller logic
topology.py → custom topology
README.md → documentation
Author

Akhilesh Kumar
