+++
title = 'NAT'
date = '2026-11-20T18:23:56Z'
+++

Network address translation (NAT) is a router rewriting the addresses in packets as they pass through it, and remembering each rewrite so it can undo it on the replies. Its common job is letting many hosts with private addresses share one public IPv4 address. A private address, such as `192.168.50.10`, isn't routed on the internet, so a server could receive a packet from it but couldn't reply. The alternative, a public address for every host, ran out with IPv4; IPv6 has enough to make it possible again.

NAT has these parts:

- Source NAT (SNAT): rewrite the source of outgoing packets to the router's address. Masquerade is source NAT to whatever address the outgoing interface has.
- Port translation: rewrite the source port too when two hosts would collide, so one public address carries thousands of connections. Together with source NAT, this is NAPT, what home routers do.
- Destination NAT (DNAT): rewrite the destination of incoming packets, as in port forwarding, Docker's `-p`, and Kubernetes Services.
- Connection tracking: a table of every flow through the router, with its original and translated addresses, which reverses the rewrite on replies.

![Outbound NAT. laptop at 192.168.50.10 and laptop2 at 192.168.50.11 both connect from port 40002 to the router, which has 192.168.50.254 at home and 203.0.113.2 outside. The router forwards both connections to server at 203.0.113.80, one from 203.0.113.2:40002 and one from 203.0.113.2:20358, a new port, since both can't use 40002.](outbound.svg)

The lab is a router container with two networks. Outside is a Docker network, `203.0.113.0/24`, a range reserved for documentation, holding the router at `203.0.113.2` and a server at `203.0.113.80`. Inside, on a bridge in the router's own network namespace, two network namespaces stand in for laptops at `192.168.50.10` and `.11`, routed through the router at `192.168.50.254`. The router runs Linux nftables and conntrack-tools. A web page on the server, and one on the laptop, printed the address each request came from.

## Without NAT

With forwarding on but no NAT rule, the laptop's request to the server timed out. A capture on the server showed the SYN arrive from `192.168.50.10`, and the server answered nothing: it had no route to `192.168.50.0/24`, so `ip route get 192.168.50.10` returned `Network unreachable`. On the internet, a router would usually drop a packet from a private address before it got that far.

## Source NAT

One nftables rule masquerades everything leaving through the outside interface:

```text
table ip lab {
  chain postrouting {
    type nat hook postrouting priority srcnat;
    oifname "eth0" masquerade
  }
}
```

- `postrouting` runs after the routing decision, just before the packet leaves, when the outgoing interface is known.
- `oifname "eth0"` matches packets leaving through the outside interface only, so traffic between laptops stays untouched.
- `masquerade` rewrites the source to the address of that interface, `203.0.113.2`, read when each connection starts.

The laptop's request then got the answer `you are 203.0.113.2:59784`. The server saw only the router; the laptop kept its own source port, 59784, because no other connection used it. The router's connection tracking table held both views of the flow:

{{< parts >}}
conntrack -L | List the kernel's tracked connections.
-p tcp | Only TCP flows.
{{< /parts >}}

```text
tcp 6 119 TIME_WAIT src=192.168.50.10 dst=203.0.113.80 sport=59784 dport=80
                    src=203.0.113.80 dst=203.0.113.2 sport=80 dport=59784 [ASSURED]
```

- The first tuple is the packet as the laptop sent it. The second is the reply as the router expects it, addressed to `203.0.113.2`.
- A reply that matches the second tuple is rewritten back to `192.168.50.10:59784` and forwarded inside.
- `TIME_WAIT` is the TCP state the tracker followed; 119 is the seconds until the entry expires.
- `[ASSURED]` means traffic was seen in both directions, so the entry is kept longest when the table fills.

## Port translation

Both laptops connected to the server from the same port, 40002, at the same time. The server saw `203.0.113.2:40002` for one and `203.0.113.2:20358` for the other. The router keeps a port when it's free and picks another when the public address and port are already taken for that destination:

| Laptop | Sent from | Server saw |
|---|---|---|
| laptop2, `192.168.50.11` | `:40002` | `203.0.113.2:40002` |
| laptop, `192.168.50.10` | `:40002` | `203.0.113.2:20358` |

A connection is unique by its addresses and ports together, so one public address can carry about 64,000 connections to each server address and port, and far more in total.

## Incoming connections

NAT keeps state only for connections started from inside. From the server, `http://203.0.113.2/` reached the router itself, which refused it, and the private address `http://192.168.50.10/` had no route. With no tracked flow and no rule, the router has no inside host to send a packet to, so NAT also works as a filter: the inside can't be reached unless the router is told where to send traffic.

Port forwarding is a destination NAT rule:

```text
chain prerouting {
  type nat hook prerouting priority dstnat;
  iifname "eth0" tcp dport 8080 dnat to 192.168.50.10:80
}
```

- `prerouting` runs as a packet arrives, before routing, so the new destination decides where it goes.
- `dnat to 192.168.50.10:80` rewrites the destination address and port.

The server's request to `203.0.113.2:8080` then reached the laptop's page, which answered `you are 203.0.113.80:45920`: with destination NAT alone, the inside host sees the real client. conntrack recorded `src=203.0.113.80 dst=203.0.113.2 dport=8080` and the expected reply `src=192.168.50.10 sport=80`.

## Timeouts and the table

Every tracked flow expires after it's idle for a while. When an entry expires, the mapping is gone, and the next packet from outside is dropped. Defaults in the lab's kernel:

| Flow | Timeout |
|---|---|
| TCP, established | 432,000 s, 5 days |
| UDP, one direction only so far | 30 s |
| UDP, replies seen | 120 s |
| Table size, `nf_conntrack_max` | 262,144 entries |

- A UDP flow from the laptop to port 5000, with no reply, showed 27 seconds left, and 17 ten seconds later.
- Home and carrier routers often use much shorter timeouts. Long-lived connections send keepalives so the mapping survives idle periods.
- A full table drops new connections. On busy NAT gateways and Kubernetes nodes, this shows up as random connection failures.
- Peer-to-peer programs, such as video calls, use STUN to learn the public address and port their NAT gave them, and send it to the other side.

## Docker port publishing

`docker run -p 8090:80 nginx:alpine` added one rule to the `nat` table's `DOCKER` chain, in the Linux VM that Docker Desktop runs:

```text
-A DOCKER -p tcp -m tcp --dport 8090 -j DNAT --to-destination 172.17.0.3:80
```

`PREROUTING` and `OUTPUT` jump to `DOCKER` for any packet addressed to the host itself, so the rule catches traffic from outside and from the VM. Each Docker network also gets a masquerade rule for traffic leaving it, such as the lab's own `-s 203.0.113.0/24 ! -o br-… -j MASQUERADE`. Docker Desktop then forwards the Mac's `localhost:8090` into the VM, and `curl localhost:8090` on the Mac returned status 200.

Docker's rules also affect containers' own traffic. In an earlier version of this lab, with the laptops as containers on a Docker network, the port-forwarded request reached the laptop from `192.168.50.1`, the Docker bridge, instead of from the server: Docker had masqueraded it a second time. Making the network internal didn't help either: Docker then drops traffic between the network and any address outside it, and the router saw nothing. The laptops moved into the router's own namespace for that reason.

## Kubernetes Services

A Service's cluster IP, such as `10.96.6.249`, belongs to no machine. kube-proxy, in its iptables mode on kind, turns it into destination NAT rules on every node. For a Service `natweb` with two pods:

![How kube-proxy routes a Service. A client pod connects to 10.96.6.249:80. The KUBE-SERVICES chain matches the cluster IP and jumps to the KUBE-SVC chain for Service natweb. With probability 0.5, it jumps to a KUBE-SEP chain that does DNAT to 10.244.1.10:80; otherwise, to one that does DNAT to 10.244.2.15:80.](service.svg)

- `KUBE-SERVICES` matches `-d 10.96.6.249/32 --dport 80` and jumps to the Service's chain.
- The Service's chain picks a pod: the first rule matches with `--probability 0.5`, and the last catches the rest. With three pods it would be 1/3, then 1/2, then the rest, so each gets a third.
- Each pod's chain does `DNAT --to-destination 10.244.1.10:80`. The choice happens on a connection's first packet; conntrack sends the rest to the same pod.
- Traffic from outside the pod range is marked, and `KUBE-POSTROUTING` masquerades marked packets, so replies come back through the same node.

Six requests from a client pod showed in the node's conntrack table as six flows to `dst=10.96.6.249`, with replies expected from `10.244.1.10` four times and `10.244.2.15` twice.

## In a program

A program behind NAT sees only its own private address. In Go, `conn.LocalAddr()` on the laptop reports `192.168.50.10`, while the server's `conn.RemoteAddr()`, or `r.RemoteAddr` in an HTTP handler, holds the router's address, as the lab's page showed with `203.0.113.2`. Behind a proxy or load balancer that also translates, the original client is passed in headers such as `X-Forwarded-For`, which only trusted proxies should be allowed to set. A server that keeps TCP connections idle behind NAT sets keepalives, with `net.Dialer.KeepAlive` or `KeepAliveConfig`, shorter than the shortest NAT timeout on the path. [Addressing and routing]({{< ref "/networking/addressing" >}}) covers private ranges and routing tables, and [Services]({{< ref "/k8s/service" >}}) the objects kube-proxy reads.

References: [RFC 3022: Traditional NAT](https://www.rfc-editor.org/rfc/rfc3022), [RFC 4787: NAT behavior for UDP](https://www.rfc-editor.org/rfc/rfc4787), [RFC 5382: NAT behavior for TCP](https://www.rfc-editor.org/rfc/rfc5382), [RFC 1918: Private address space](https://www.rfc-editor.org/rfc/rfc1918), [RFC 5737: Documentation address blocks](https://www.rfc-editor.org/rfc/rfc5737), [RFC 8489: STUN](https://www.rfc-editor.org/rfc/rfc8489), [nftables: Performing NAT](https://wiki.nftables.org/wiki-nftables/index.php/Performing_Network_Address_Translation_(NAT)), [conntrack(8)](https://manpages.debian.org/conntrack/conntrack.8.en.html), [Netfilter conntrack sysctl](https://docs.kernel.org/networking/nf_conntrack-sysctl.html), [Docker: Packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/), [Virtual IPs and service proxies (Kubernetes docs)](https://kubernetes.io/docs/reference/networking/virtual-ips/)
