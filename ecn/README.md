# Implementing ECN

## Introduction

The objective of this tutorial is to extend basic L3 forwarding with
an implementation of Explicit Congestion Notification (ECN).

ECN allows end-to-end notification of network congestion without
dropping packets.  If an end-host supports ECN, it puts the value of 1
or 2 in the `ipv4.ecn` field.  For such packets, each switch may
change the value to 3 if the queue size is larger than a threshold.
The receiver copies the value to sender, and the sender can lower the
rate.

As before, we have already defined the control plane rules for
routing via P4runtime.
## Step 1: Run P4Runtime
```
python3 mycontroller-triangle.py
```
**The smaller the threshold of the queue, the more likely congestion will occur.**
```
Please input the threshold of the queue: 3

 Monitoring network congestion ...
.
Received response-----
ECN value: 1
Received response-----
ECN value: 1
Received response----
...
```

## Step 2: Run the starter code

Let's compile the `ecn.p4` and bring up a network in Mininet to test its behavior.

1. In your shell, run:
   ```bash
   make
   ```
   This will:
   * compile `ecn.p4`, and
   * start a Mininet instance with three switches (`s1`, `s2`, `s3`) configured
     in a triangle. There are 5 hosts. `h1` and `h11` are connected to `s1`.
     `h2` and `h22` are connected to `s2` and `h3` is connected to `s3`.
   * The hosts are assigned IPs of `10.0.1.1`, `10.0.2.2`, etc
     (`10.0.<Switchid>.<hostID>`).
   * The control plane programs the P4 tables in each switch based on
     `sx-runtime.json`

2. We want to send a low rate traffic from `h1` to `h2` and a high
rate iperf traffic from `h11` to `h22`.  The link between `s1` and
`s2` is common between the flows and is a bottleneck because we
reduced its bandwidth to 512kbps in topology.json.  Therefore, if we
capture packets at `h2`, we should see the right ECN value.

![Setup](setup.png)

3. You should now see a Mininet command prompt. Open four terminals
for `h1`, `h11`, `h2`, `h22`, respectively:
   ```bash
   mininet> xterm h1 h11 h2 h22
   ```
3. In `h2`'s XTerm, start the server that captures packets:
   ```bash
   ./receive.py
   ```
4. in `h22`'s XTerm, start the iperf UDP server:
   ```bash
   iperf -s -u
   ```
5. In `h1`'s XTerm, send one packet per second to `h2` using send.py
say for 30 seconds:
   ```bash
   ./send.py 10.0.2.2 "P4 is cool" 30
   ```
   The message "P4 is cool" should be received in `h2`'s xterm,
6. In `h11`'s XTerm, start iperf client sending for 15 seconds
   ```bash
   iperf -c 10.0.2.22 -t 15 -u
   ```
7. At `h2`, the `ipv4.tos` field (DiffServ+ECN) values change from 1
to 3 as the queue builds up.  `tos` may change back to 1 when iperf
finishes and the queue depletes.
8. type `exit` to close each XTerm window

9. To easily track the `tos` values you may want to redirect the output
of `h2` to a file by running the following for `h2`
   ```bash
   ./receive.py > h2.log
   ```
and just print the `tos` values `grep tos h2.log` in a separate window
```
     tos       = 0x1
     tos       = 0x1
     tos       = 0x1
     tos       = 0x1
     tos       = 0x1
     tos       = 0x1
     tos       = 0x1
     tos       = 0x1
     tos       = 0x1
     tos       = 0x1
     tos       = 0x1
     tos       = 0x1
     tos       = 0x1
     tos       = 0x3
     tos       = 0x3
     tos       = 0x3
     tos       = 0x3
     tos       = 0x3
     tos       = 0x3
     tos       = 0x1
     tos       = 0x1
     tos       = 0x1
     tos       = 0x1
     tos       = 0x1
     tos       = 0x1
```
In p4runtime, the output will be
```
ECN value: 2
Received response-----
ECN value: 2
Received response-----
ECN value: 3
Congestion happens!!
Received response-----
ECN value: 3
Congestion happens!!
Received response-----
ECN value: 3
Congestion happens!!
Received response-----
ECN value: 3
Congestion happens!!
Received response-----
ECN value: 3
Congestion happens!!
Received response-----
ECN value: 3
Congestion happens!!
Received response-----
ECN value: 3
Congestion happens!!
Received response-----
ECN value: 3
Congestion happens!!
Received response-----
ECN value: 3
Congestion happens!!
Received response-----
ECN value: 3
Congestion happens!!
Received response-----
ECN value: 3
Congestion happens!!
Received response-----
ECN value: 3
Congestion happens!!
Received response-----
ECN value: 2
...
```

### Addition functions

- The user can configure the threshold of the queue by themselves. 
- Data plane switches can clone their packets to the control plane, so that the controller can monitor the value of ECN field and report network congestion when the ecn value becomes 3.

#### Cleaning up Mininet

In the latter two cases above, `make` may leave a Mininet instance
running in the background.  Use the following command to clean up
these instances:

```bash
make stop
```
## Relevant Documentation

The documentation for P4_16 and P4Runtime is available [here](https://p4.org/specs/)

All excercises in this repository use the v1model architecture, the documentation for which is available at:
1. The BMv2 Simple Switch target document accessible [here](https://github.com/p4lang/behavioral-model/blob/master/docs/simple_switch.md) talks mainly about the v1model architecture.
2. The include file `v1model.p4` has extensive comments and can be accessed [here](https://github.com/p4lang/p4c/blob/master/p4include/v1model.p4).
