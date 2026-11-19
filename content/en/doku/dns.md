title: Platform DNS
summary: The DNS role cp-dnsd – authoritative zones of the cluster, DNSSEC, floating service addresses (VIPs) with Raft leases, and integration with the operator's DNS.
group: konzept
order: 65
quelle: Platform DNS role
de: dns
---

## Goal

A DCP cluster manages its DNS records **itself**. Portal and API, nodes, boot service and release holders change with the cluster state – nodes join, roles move, holders fail. Maintaining these names by hand in the operator's DNS would be error-prone. Instead, the rule is:

> The operator's central DNS only points to the cluster; everything below that is answered by the cluster itself.

For this purpose there is the node role `dns` with the service `cp-dnsd`. It is distinct from the VPC-internal name resolution for tenant workloads, which is answered locally on every host (see [Network](network.html)). Tenant zones in public DNS are a later expansion stage.

## Decisions

| Question | Decision |
|---|---|
| Scope | platform records automatically from the cluster state, plus custom records via API, command line, MCP and portal |
| Integration with central DNS | NS delegation **and** conditional forwarding; two fixed service addresses (VIPs) per region that automatically move to healthy `dns` nodes |
| Implementation | own, purely authoritative server in Rust; separate unit without the node key, port 53 only, hard limits, fuzzing |
| DNSSEC | configurable per zone (ECDSA P-256, rotation, DS record in the portal); default "on" in the `standard` and `erhoeht` profiles, "off" in the `homelab` profile |

The decision for an in-house implementation follows the project's principle of implementing core functions itself and keeping them lean (see [Vision](vision.html)). From a widely used Rust DNS library, only the wire format encoding is used; zone logic, signing, response behavior and limits are the project's own code.

## Zones and records

A zone is a platform resource `DnsZone`. Like any other resource it is managed via the API – create, update, delete, plus a dedicated action for key rotation (see [API-first](api-first.html)). When a region is initialized, the setup wizard proposes a zone derived from the portal address and indicates what needs to be entered in the central DNS.

The platform automatically creates in every zone:

| Name | Contents |
|---|---|
| zone apex | SOA and NS records `ns1`/`ns2` |
| `ns1.<zone>`, `ns2.<zone>` | the two service addresses (both the same if there is only one VIP) |
| portal name | addresses of the ready nodes, if the portal address lies within the zone |
| `<node>.nodes.<zone>` | the node's LAN addresses |
| `<node>.underlay.<zone>` | the node's underlay address |
| `boot.<zone>` | nodes with an active `boot` role |
| `releases.<zone>` | current holders of the platform releases (see [Release bundle](release-bundle.html)) |

**Custom records** are added from the zone's specification. If a custom record tries to override a name managed by the platform, it is skipped; the zone reports this as a warning in its status.

Building the zone is a pure derivation: the agent computes the desired zone from the replicated cluster state and hands it to `cp-dnsd`. When the state changes – a node becomes ready, a role moves – the zone changes automatically along with it. This follows the level-triggered reconciler pattern of the control plane (see [Control plane](control-plane.html)).

## The `cp-dnsd` service

`cp-dnsd` answers DNS queries over UDP and TCP on port 53. Its behavior is deliberately narrow:

- **Authoritative only**, no recursion. Queries for foreign names are refused.
- **No zone transfers**; queries of type ANY return only a single RRset (RFC 8482); no wildcards.
- **EDNS(0)** is supported; UDP responses are limited to a conservative size. If a response is too large, it is marked as truncated, and the client retries the query over TCP.
- **Limits:** maximum query size, a limited number of concurrent TCP connections with an idle timeout; malformed or oversized queries are dropped.

### Process boundary

DNS parsers process data from the network and are a classic attack target. That is why `cp-dnsd` runs as a **separate service with its own user**: it has no access to the node key and no access to the replicated database, holds only the privilege to bind port 53, and is additionally restricted by a mandatory access control profile. Each parser has its own fuzzing target. A bug in the DNS server therefore does not lead to a takeover of the node (see [Security model](security-model.html)).

### Control interface

The agent talks to `cp-dnsd` over a local Unix socket with a simple, line-based message format. The peer is verified via the operating system's process identity – only the agent may deliver zones. This channel carries:

- the **desired zones** (platform and custom records in canonical form),
- **encrypted key envelopes** for DNSSEC (see below).

`cp-dnsd` itself decides nothing about the cluster; it only answers what the agent hands it as desired state.

## DNSSEC

If DNSSEC is enabled for a zone, `cp-dnsd` signs it **online** (RFC 4033–4035, RFC 6605):

- **Algorithm:** exclusively ECDSA P-256 with SHA-256 (algorithm 13) – compact and widely supported.
- **Non-existence** is proven via an NSEC chain. Since the platform zones are small and contain no names worth protecting, zone enumeration via NSEC is not a concern.
- **Re-signing** happens on every change to the zone and, independently, at regular intervals (at least every few days), so that signatures never expire.
- **What is signed is exactly what is served:** the records are held in canonical wire form (names uncompressed, lowercase), and the same bytes go into the response.
- **Rotation** of the zone keys via a dedicated API action; the portal displays the DS record for the parent zone.

### Handling the zone keys

The private zone keys are **generated in `cp-dnsd`** and reside only there, locally with restrictive permissions – never in the agent. Because several `dns` nodes must sign the same zone, keys are distributed between them, but exclusively as an **envelope**: encrypted to a transport key of the receiving `cp-dnsd` (ephemeral ECDH, key derivation, authenticated encryption; zone and key are bound into the authentication). This transport key is created anew at every start and is held only in memory. The agent and the replicated database therefore only ever see ciphertext. Details on the procedures are on the [Cryptography](cryptography.html) page.

## Floating service addresses (VIPs)

So that the operator's central DNS has stable targets, each region gets up to **two fixed service addresses** in the LAN. They are not permanently assigned to one node but **move automatically** to healthy `dns` nodes – similar to VRRP, but as an in-house development based on the replicated control plane.

### Raft lease with fencing

Each VIP belongs to a lease object in the replicated database with holder, fencing epoch and renewal counter. Every write is a compare-and-swap on the revision and is therefore only possible with Raft quorum.

- The **holder** renews regularly. It carries the VIP only until the end of its last successful renewal minus a safety margin – measured with its local monotonic clock. If renewal fails, for example because of a network partition or missing quorum, **it releases the VIP beforehand**.
- **Another node takes over** only after it has observed the unchanged revision for at least one full lease duration. This guarantees that the old holder's ownership ends before the takeover – without synchronized clocks; limited clock drift is covered by the safety margin. Every takeover increments the epoch.
- **Without quorum** there is neither renewal nor takeover. The address can therefore never be claimed twice.

The platform uses the same lease pattern for other floating addresses too, such as floating IPs on gateways (see [Network](network.html)).

### Assigning and announcing addresses

Assigning the address to a network interface is a privileged operation. The agent is not allowed to do this itself; instead, it instructs the node's privileged helper service via a fixed, small command format: configure permitted VIPs, assign a VIP, release one of its own VIPs, list held VIPs. The helper service independently checks that the address is on the configured list, lies within the network of an existing LAN interface (not loopback, not underlay) and is not already one of the node's own addresses. It cannot remove foreign addresses.

After the takeover, the LAN must learn about the new assignment. Instead of working with raw sockets, the agent sends a packet with the VIP as source address to a not yet resolved address in the LAN. This triggers ARP or neighbor solicitation with the VIP as sender and updates the neighbor tables of the other devices.

## Rate limiting

An authoritative DNS server can be abused for reflection attacks. `cp-dnsd` therefore limits the response rate **per source network** (IPv4 per /24, IPv6 per /56) with a token bucket. Above the limit, responses are dropped; however, every second dropped UDP response goes out as an empty, truncated response. Legitimate clients thus fall back to TCP and continue to be served, while spoofed senders gain no amplification effect. The total number of tracked source networks is capped; the oldest entries are evicted.

## Integration with the operator's DNS

The operator has two options, which can also be combined:

1. **NS delegation:** the region's zone is delegated in the parent zone to `ns1`/`ns2`, which point to the two VIPs. With DNSSEC, the DS record from the portal is also added.
2. **Conditional forwarding:** internal resolvers forward queries for the zone to the two VIPs – practical in networks without public delegation.

## Status and operation

Like any other node role, the `dns` role is started and monitored by the role reconciler. The region reports the DNS state in its status, in particular which node holds which VIP. If a `dns` node fails, its VIP moves to another healthy node after the lease expires; the zone itself is identical on all `dns` nodes. A region's portal address can lie within such a zone; what to keep in mind when changing it is described in [Changing the portal hostname](portal-hostname.html).
