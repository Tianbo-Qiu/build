+++
title = 'DNS'
date = '2026-11-19T04:41:48Z'
+++

DNS (Domain Name System) is the internet's distributed database that turns names, such as `example.com`, into IP addresses and other data. Programs connect by IP address, but people and configuration use names, and the address behind a name changes as servers move. No single server could hold every name, so DNS splits the namespace into zones, each served by its own authoritative servers, and caches answers along the way.

DNS has these parts:

- Domain names: a tree of labels read right to left, from the root `.` through `com` to `example.com` and `www.example.com`.
- Zones: parts of the tree run by one organization, which can delegate subtrees to others.
- Authoritative servers: hold a zone's records and answer for it.
- Recursive resolver: asks the authoritative servers on a client's behalf, from the root down, and caches answers.
- Stub resolver: the small resolver in each host's system library, which sends every question to a recursive resolver.
- Resource records: the data itself, each with a name, a type, a TTL, and a value.

![Resolving www.example.com. The client's stub resolver asks a recursive resolver for the A record of www.example.com. The recursive resolver asks a root server, which refers it to the com servers, a to m.gtld-servers.net. It asks a com server, which refers it to hera and elliott.ns.cloudflare.com. It asks the example.com server at Cloudflare, which answers A 104.20.23.154 and 172.66.147.243 with TTL 300. The resolver returns the answer to the client and caches it for 300 seconds.](lookup.svg)

Examples ran in Alpine containers on Docker with BIND's `dig` 9.20, an unbound 1.25 recursive resolver in a container, and a three-node kind cluster running Kubernetes 1.37.

## Names and zones

- A name is labels separated by dots, each up to 63 bytes, the whole up to 255. A fully qualified name ends with the root's empty label, written as a trailing dot: `www.example.com.`
- Each zone's servers answer for the names in it and delegate subzones with NS records. The root zone delegates `com`; the `com` zone delegates `example.com` to Cloudflare's servers.
- The root zone is served from 13 names, `a` to `m.root-servers.net`, each reached by anycast at many sites worldwide. Resolvers ship with their addresses.
- A query normally travels over UDP port 53. An answer too large for UDP sets the truncated flag, and the client retries over TCP. The lab's queries advertised a UDP buffer of 1,232 bytes, a size chosen so answers fit in one packet without IP fragmentation.

## Resource records

Real answers from `dig`, for `example.com` unless noted:

- A: an IPv4 address, `104.20.23.154`.
- AAAA: an IPv6 address, `2606:4700:10::ac42:93f3`.
- NS: an authoritative server for the zone, `hera.ns.cloudflare.com.`
- SOA: the zone's settings, below.
- CNAME: an alias, meaning look up the other name instead. `www.github.com` has `github.com.`
- MX: mail servers, by preference. `0 .` means the domain accepts no mail.
- TXT: text for policies and ownership checks, `"v=spf1 -all"`.
- PTR: the name for an address. `1.1.1.1` has `one.one.one.one.`
- The SOA record, `elliott.ns.cloudflare.com. dns.cloudflare.com. 2420077714 10000 2400 604800 1800`, holds the zone's primary server, a contact address, the serial number, the refresh, retry, and expiry timers for secondary servers, and how long to cache a "no such name" answer, 1,800 s.
- The TXT record is SPF: no server sends mail for `example.com`. The null MX says the same for receiving.
- A name can have several records of one type, a record set. `example.com` returned two A records, and clients pick among them.
- CNAMEs chain. `www.microsoft.com` pointed to `www.microsoft.com-c-3.edgekey.net`, which pointed to `e13678.dscb.akamaiedge.net`, which had the A record: two aliases into Akamai's network.
- A reverse lookup writes the address backwards under `in-addr.arpa` (`ip6.arpa` for IPv6), so the address owner's zone can hold it.
- SRV records name a service's host and port, such as `_sftp-ssh._tcp`, which the multicast DNS capture below showed.

## Following a lookup

`dig +trace` does a recursive resolver's work itself and prints each step:

{{< parts >}}
dig | Query DNS and print the answer.
+trace | Start at the root and follow each referral down, instead of asking a recursive resolver.
-4 | Use IPv4 only.
www.example.com | The name to resolve.
+ A | The record type. A is the default.
{{< /parts >}}

| Step | Asked | Reply | Time |
|---|---|---|---|
| 1 | Local resolver | The list of root servers | 2 ms |
| 2 | `b.root-servers.net` | Referral: `com` is served by `a`–`m.gtld-servers.net` | 87 ms |
| 3 | `j.gtld-servers.net` | Referral: `example.com` is served by `hera` and `elliott.ns.cloudflare.com` | 294 ms |
| 4 | `hera.ns.cloudflare.com` | The answer: two A records, TTL 300 | 13 ms |

- Each referral comes with the next servers' addresses, called glue, when their names sit inside the zone being delegated.
- A recursive resolver caches each step. The `com` and `example.com` delegations have TTLs of two days, so after the first lookup it asks the `example.com` servers directly.

## Caching and TTLs

Every record carries a TTL (time to live), the number of seconds a resolver may keep it. Lookups through the unbound resolver, with its cache empty:

| Name | First lookup | Repeated |
|---|---|---|
| `example.com` | 181 ms | 0 ms |
| `go.dev` | 710 ms | 0 ms |
| `www.debian.org` | 1,552 ms | 1 ms |

- A cached answer comes with the remaining TTL: `300`, then `297` three seconds later. When it reaches 0, the next lookup asks again.
- Negative answers are cached too, for the time in the zone's SOA record, 1,800 s for `example.com`.
- A record changed at the source is seen by each resolver only when its cached copy expires, so operators lower a TTL before moving a server.
- Public resolvers such as `1.1.1.1` run many separate caches behind one anycast address. Two queries a few seconds apart returned TTLs of 267 and then 295, from different caches.

## On a host

A program calls the system's stub resolver, through functions such as `getaddrinfo`, and the stub reads `/etc/resolv.conf`:

- `nameserver` lists recursive resolvers to ask.
- `search` lists domains appended to short names.
- `options ndots:n` sets how many dots a name needs before it's first tried as is.

The host checks `/etc/hosts` first, by default. Docker gives containers on user-defined networks an embedded resolver at `127.0.0.11`, which answers container names, such as `resolver`, and forwards everything else; on the default network, a container got the host's resolver instead.

## In Kubernetes

Each pod's `/etc/resolv.conf` points at the cluster's DNS Service, CoreDNS:

```text
search default.svc.cluster.local svc.cluster.local cluster.local
nameserver 10.96.0.10
options ndots:5
```

- A Service `web` in namespace `default` has the name `web.default.svc.cluster.local`. The search list lets a pod write `web` for a Service in its own namespace, or `web.other` for one in another.
- `ndots:5` means a name with fewer than five dots is tried with each search domain first. A capture in a pod running `wget http://example.com/` showed eight queries, A and AAAA for each of `example.com.default.svc.cluster.local`, `example.com.svc.cluster.local`, `example.com.cluster.local`, and `example.com`; the first six returned "no such name".
- With a trailing dot, `http://example.com./`, the name is final and skips the search list: two queries.
- CoreDNS's configuration answers `cluster.local` and reverse zones from the Kubernetes API with a TTL of 30 seconds, forwards other names to the node's resolvers, and caches those answers for up to 30 seconds.

## Multicast DNS

Multicast DNS (mDNS) resolves names on one link with no DNS server: a host asks the whole link, and the owner answers. It uses names under `.local`, the multicast group `224.0.0.251` (`ff02::fb` for IPv6), and UDP port 5353. With the Avahi daemon in two containers, `avahi-resolve -n m2.local` from `m1` returned `172.22.0.5`. The capture on m2:

- m1 sent `A (QM)? m2.local.` to `224.0.0.251`, a standard DNS query sent to everyone.
- m2 answered `A 172.22.0.5` to the same group, so every host on the link could cache it.
- At startup, each daemon announced its own records unasked, and also announced a service with PTR, SRV, and TXT records: `m1._sftp-ssh._tcp.local`. Browsing these announcements is DNS-based service discovery (DNS-SD), which printers and AirPlay devices use.

mDNS works only on one link, because routers don't forward link-local multicast, and any host can answer for any name.

## Privacy and security

Plain DNS is neither encrypted nor authenticated. A capture of `dig example.com @1.1.1.1` showed the question `A? example.com.` and both answers in clear text, readable by anyone on the path, and by the resolver.

- DNS over TLS (DoT) sends the same messages inside TLS on port 853. With `kdig +tls`, the capture showed a TCP connection to `1.1.1.1:853` and no query name.
- DNS over HTTPS (DoH) sends them as HTTPS requests on port 443, mixed in with web traffic. curl's `--doh-url https://1.1.1.1/dns-query` resolved `example.org` this way, and the name didn't appear in the DoH traffic.
- But curl's following HTTPS connection to `example.org` carried the name in clear text in its ClientHello, the server name indication. Encrypted DNS hides the lookup, not the connection that follows. TLS Encrypted Client Hello, now an RFC, closes that gap where both sides support it.
- The resolver still sees every name, so encrypted DNS moves trust to the resolver rather than removing it.

DNSSEC authenticates answers instead of hiding them. A zone signs each record set, and the signatures chain up to the root's key, which validating resolvers ship with.

- `dig +dnssec example.com` through unbound returned an RRSIG record with the A records, algorithm 13 (ECDSA P-256 with SHA-256), and the `ad` (authenticated data) flag: the resolver had checked the signature chain.
- `dnssec-failed.org` is a test domain with deliberately broken signatures. Through unbound, it returned `SERVFAIL`. With `+cd` (checking disabled), the same query returned `NOERROR` and an A record: the data existed, but a validating resolver refused it.
- Without DNSSEC, a resolver accepts the first answer that matches its question. Resolvers make forgery harder by picking a random query ID and source port for each query.

## In a program

Go's `net` package resolves names with `net.LookupHost`, `LookupIP`, `LookupCNAME`, `LookupMX`, `LookupTXT`, and `LookupAddr` for reverse lookups, or through a `net.Resolver` with a context for timeouts. `net.Dial("tcp", "example.com:443")` resolves the name and tries the addresses in order. On Linux, Go uses its own resolver, which reads `/etc/resolv.conf` and `/etc/hosts` and follows `ndots` and the search list, and falls back to the system's C library in cases it can't handle; `GODEBUG=netdns=go` or `netdns=cgo` forces one. Neither does DNSSEC validation or encrypted DNS; both rely on the configured resolver. [Addressing and routing]({{< ref "/networking/addressing" >}}) covers the addresses DNS returns, and [TLS]({{< ref "/networking/tls" >}}) the server name indication.

References: [RFC 1034: Domain names, concepts](https://www.rfc-editor.org/rfc/rfc1034), [RFC 1035: Domain names, implementation](https://www.rfc-editor.org/rfc/rfc1035), [RFC 9499: DNS terminology](https://www.rfc-editor.org/rfc/rfc9499), [RFC 3596: AAAA records](https://www.rfc-editor.org/rfc/rfc3596), [RFC 2308: Negative caching](https://www.rfc-editor.org/rfc/rfc2308), [RFC 2782: SRV records](https://www.rfc-editor.org/rfc/rfc2782), [RFC 7505: Null MX](https://www.rfc-editor.org/rfc/rfc7505), [RFC 7208: SPF](https://www.rfc-editor.org/rfc/rfc7208), [Root servers](https://root-servers.org/), [RFC 6762: Multicast DNS](https://www.rfc-editor.org/rfc/rfc6762), [RFC 6763: DNS-based service discovery](https://www.rfc-editor.org/rfc/rfc6763), [RFC 7858: DNS over TLS](https://www.rfc-editor.org/rfc/rfc7858), [RFC 8484: DNS over HTTPS](https://www.rfc-editor.org/rfc/rfc8484), [RFC 9849: TLS Encrypted Client Hello](https://www.rfc-editor.org/rfc/rfc9849), [RFC 4033: DNSSEC introduction](https://www.rfc-editor.org/rfc/rfc4033), [RFC 5452: Resilience against forged answers](https://www.rfc-editor.org/rfc/rfc5452), [DNS for Services and Pods (Kubernetes docs)](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/), [Docker networking: DNS services](https://docs.docker.com/engine/network/#dns-services), [Go net package, name resolution](https://pkg.go.dev/net#hdr-Name_Resolution)
