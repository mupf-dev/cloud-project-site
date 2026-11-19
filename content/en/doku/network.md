title: Network
summary: Network zones, the encrypted WireGuard underlay, the in-house tenant overlay cp-vnet, workload attachment and north-south traffic with floating IPs, gateways and platform DNS.
group: konzept
order: 60
quelle: Concept 06 (network architecture)
de: netzwerk
---

## Overview

The platform splits its network into two layers: an **underlay** that cryptographically connects all nodes, and a **tenant overlay** in which the tenants' virtual networks (VPCs) run. Everything that flows between nodes – control traffic (Raft, gRPC), gossip, storage replication, live migration **and** the traffic of tenant workloads – runs in the encrypted underlay. On the physical network, only WireGuard UDP, the boot and discovery services, a channel for additional keys and the public entry points (API, portal, MCP, floating IPs) remain visible.

The concept is designed to scale from a homelab with a single router to a data center with a leaf-spine fabric. The protection it provides does **not** depend on the physical build-out: it is always cryptographic and is additionally reinforced physically where the infrastructure allows it.

### Key decisions

| Topic | Decision |
|---|---|
| Zones | seven network zones, mappable to three physical build-out levels `flat`, `vlan`, `routed` |
| Underlay | one kernel WireGuard interface per node, IPv6 only inside (ULA); peers exclusively from the desired state; additional post-quantum PSK |
| Tenant overlay | in-house development `cp-vnet` on the Linux kernel data path (VRF + VXLAN + nftables); not OVN, not Cilium; overlay packets only inside the WireGuard underlay |
| North-south | `network-gateway` role for NAT, floating IPs and L4 load balancers; ownership via Raft lease with fencing |

## Network layers and zones

### Zone model

| Zone | Contents | Protection |
|---|---|---|
| **Z0 Physical / transport** | LAN or data center fabric, carries WireGuard UDP | baseline rule set (only permitted ports), WireGuard cookie against handshake floods |
| **Z1 Boot / discovery** | proxyDHCP, TFTP, boot HTTP, discovery inbox | cryptographic quarantine always, VLAN separation optional or mandatory depending on profile; signed artifacts |
| **Z2 Underlay** (inside WireGuard) | control, gossip, storage replication, live migration, overlay transport | WireGuard (+ PQ PSK) and per-service mTLS or AEAD; adopted nodes only |
| **Z3 Tenant overlay** (VXLAN inside Z2) | VPCs, subnets, VM and container traffic | VRF per VPC, conntrack zones, security groups, anti-spoofing |
| **Z4 North-south / uplink** | floating IPs, NAT gateway, LB VIPs, internet egress | nftables boundary, basic DDoS protection, security group at the destination |
| **Z5 Management** | API, portal, MCP, local node API | TLS 1.3, authentication, permitted source networks, rate limits |
| **Z6 Out-of-band** | BMC/Redfish, serial consoles | never in tenant or internet networks; credentials only as secret references |

**Principle:** a zone is only a zone once its boundary is enforced **and** observable. Every node reports the actual zone assignment of its interfaces; deviations – such as tenant VXLAN on a physical interface or a BMC in the same segment as the uplink – show up as an alert condition and in the topology export.

### Physical build-out levels

| Level | Typical environment | Mapping |
|---|---|---|
| `flat` | homelab: one router with DHCP, simple switch, devices with a single NIC | Z0, Z1, Z4, Z5 share the LAN; Z2/Z3 separated purely cryptographically |
| `vlan` | VLAN-capable switch | untagged access ports = discovery; tagged VLANs for underlay, uplink and management; tagged sub-interfaces only after adoption |
| `routed` | data center, leaf-spine | each host with its own loopback address as WireGuard endpoint, BGP to the top-of-rack switch, boot segment per rack with DHCP relay |

The level is a property of the site; switching from `flat` to `vlan` can be done as a rolling change during operation.

### Embedding the discovery quarantine

Unknown hardware first lands in zone Z1 (see [Boot and adoption](boot-adoption.html)). The boot services are answered by a dedicated sandboxed process (`cp-bootd`) with its own service identity, **without** access to node or WireGuard keys and without access to Z2/Z3. A discovered node has neither WireGuard keys nor a peer entry on any platform node – so it sees neither the underlay nor the tenant networks.

On the physical interfaces of an adopted node, only the following is allowed inbound: WireGuard UDP, the PSK channel (only from known peers), boot services (only on boot nodes), HTTPS for API/portal/MCP from the permitted source networks, floating IPs (only on gateways) and rate-limited ICMP error messages. Everything else – in particular VXLAN, gossip and gRPC – is dropped.

## WireGuard underlay

### Why WireGuard

Thanks to ChaCha20, kernel WireGuard is fast on Raspberry Pis without AES instructions (roughly gigabit speed), has no negotiation state and comes with roaming and NAT traversal. IPsec is a possible later profile; custom TLS/QUIC tunneling in user space was rejected. The lack of algorithm agility is addressed architecturally: the underlay is encapsulated behind an interface, so an IPsec profile can be introduced without changes to the overlay or control. The cryptographic assessment is on the [Cryptography](cryptography.html) page.

### Interfaces and addressing

- **One WireGuard interface per node** (`cp-ul0`) with one UDP port. A second interface exists only if there is a separate physical storage fabric.
- **Inner addresses IPv6 only (ULA per RFC 4193):** one /48 per platform, one /64 per cell, one /128 per node. The addresses are **derived** deterministically from trust domain, region, cell and node identifier – no address registry is needed, and planning detects conflicts. Advantage: no collision with IPv4 home networks, and the physical network does not need IPv6.
- **Allowed IPs per peer** are exactly its /128. WireGuard thereby authenticates the source address – the basis for gossip and VXLAN being able to trust the sender.
- **Traffic classes** are distinguished by ports and DSCP (control before gossip before overlay before storage before migration), not by separate tunnels. In the MVP, at least control and gossip traffic is prioritized so that storage rebalancing on small nodes does not trigger Raft re-elections.

### Topology within a cell: "intent mesh"

Kernel WireGuard has no notion of "peer on demand". That is not needed either, because the agent knows from the **desired state** whom it has to talk to: control group and seeds, gossip partners, hosts with workloads in the same VPCs, storage partners, gateways and migration targets. Because the gossip protocol (SWIM) probes random members, the underlay within a cell is effectively a **full mesh** (up to just under 1,000 peers per node). Peers only become active when there is traffic, however; configuration changes are applied **incrementally** via netlink, never as a full replacement.

### Between cells, sites and regions

| Relationship | Topology |
|---|---|
| cells of the same region at the same site | direct peers as needed |
| sites within a region | **relay nodes** per site (at least two), direct connections where both sides are reachable |
| regions | relay to relay only, no cross-region full mesh |
| external witness | peer of the control group or of a relay |

Relays route in the kernel: they decrypt, forward and re-encrypt. They therefore see the underlay contents in plaintext. For this reason, the relay function is tied to a **high minimum trust level** of the node (see [Security model](security-model.html)); a downgrade revokes it automatically. Relays that only pass through encrypted packets are planned for a later phase.

Nodes behind NAT establish outbound connections to the relays (keepalive only on those peers). **Endpoints** come from a signed self-description, gossip provides liveness – but **never identity**: the key always comes from the Raft state.

### Key distribution and rotation

| Step | Mechanism |
|---|---|
| Generation | the node generates its key pair locally during adoption; the private key never leaves the node and resides on the encrypted data partition |
| Publication | the node signs its announcement (public key, next key, endpoints, inner address) with its node key; every agent verifies it against the cell registry |
| Distribution | every agent watches the keys of its cell and updates its interface incrementally |
| Revocation | decommissioning or quarantine removes the entry; all peers delete it within a few seconds (target under 5 s) |
| Rotation | every 30 days, staggered – never several nodes of a cell at the same time |

In the MVP, the switchover is **coordinated**: the node announces the next key together with a switchover time; all peers create an entry for the new key in advance and move the address assignment in a single step at that time. The interruption thus shrinks to the clock skew. A full "make before break" with a second interface follows in phase 2. Operators can trigger a rotation via the API action `node:rotateUnderlayKey`.

### Post-quantum additional key

WireGuard allows an optional pre-shared key that protects session keys against future quantum attacks. The platform derives these PSKs from **one** long-lived, time-limited **hybrid TLS 1.3 session** (classical + ML-KEM) per peer pair – per two-minute epoch, matching the WireGuard rekey, so running sessions are never interrupted. The channel runs outside the tunnel, is open only to known peers and does not depend on the control plane. So that a longer control outage does not drag the underlay down with it, **expired** node certificates are accepted during a 72-hour grace period with an alert – **revoked** or quarantined nodes never are. Keys and netlink access reside in a privileged helper process; the agent itself only knows the public view.

### Performance and MTU

**Targets** (VM to VM across two hosts): Pi 4 at least 600 Mbit/s, Pi 5 at least 900 Mbit/s, amd64 server at least 5 Gbit/s per peer pair.

| Layer | Overhead | at physical 1,500 | at jumbo 9,000 |
|---|---|---|---|
| WireGuard (worst case IPv6 outer) | 80 bytes | **1,420** | 8,920 |
| VXLAN over inner IPv6 | 70 bytes | **1,350** | 8,850 |
| Kubernetes with flannel VXLAN in the VPC | 50 bytes | 1,300 | 8,800 |

The underlay MTU is fixed regardless of the outer address family, so switching between an IPv4 and IPv6 endpoint changes nothing. The VPC MTU `auto` is the minimum across all participating sites, with a lower bound of 1,280; it is distributed via DHCP or router advertisement. The NAT gateway applies MSS clamping, and ICMP messages for path MTU discovery are never filtered.

## Tenant overlay: choice of technology

The requirements are VPCs with **overlapping** address spaces, security groups, peering, NAT, floating IPs, load balancers and DHCP/DNS/metadata – with a small memory footprint on Raspberry Pi, **a single source of truth** in the platform's own Raft, and static stability during control outages.

### Options

| Criterion | OVN/OVS | Cilium (eBPF) | **Own solution `cp-vnet`** |
|---|---|---|---|
| VPC feature set | very complete | pod network of a Kubernetes cluster; no overlapping tenant address spaces | must be built; the kernel provides all building blocks |
| First-class VMs | yes | only via Kubernetes | yes (TAP directly) |
| Second consensus database | **yes** (own northbound/southbound databases) | without Kubernetes: etcd | **no** |
| Memory per host | several services, not plannable on a Pi | agent typically 100–300 MB | just a module in the existing agent, data path in the kernel |
| Troubleshooting | OpenFlow tables, three databases | Kubernetes knowledge required | standard Linux tools (`ip`, `nft`, `bridge`, `conntrack`) |
| EVPN connectivity in the data center | possible | possible | natural fit: the model matches the Linux EVPN model |
| Maturity | very high | very high | new (own risk) |

### Decision for `cp-vnet`

1. **One source of truth:** OVN brings its own Raft-clustered database; the desired state would have to be mirrored – two consensus systems with independent failure modes and a duplicated backup question.
2. **Resource budget:** a Pi worker node is supposed to host VMs; an additional network stack with its own database cannot be planned for there.
3. **Cilium does not fit VPC semantics** – it remains an option *inside* tenant Kubernetes clusters.
4. **Linux provides the building blocks:** VRF, VXLAN with static tables, nftables with sets, conntrack zones, NAT, flowtables, tc.
5. **Testability:** the controller is pure logic (desired state → netlink/nftables operations) and can be tested in simulation and in network namespaces.

Risks are contained by a strictly limited MVP scope, **structural** isolation (VRF + conntrack zone + anti-spoofing) instead of rules alone, property tests "no packet between VPCs without peering" and a backend interface that keeps OVN open as a later option – then as a cache, not as the source of truth. See also [Rust stack](rust-stack.html).

## `cp-vnet` at a glance

### Data path per host

| Building block | Specification |
|---|---|
| VPC instance | only on hosts with workloads or gateway functions of the VPC: one VRF and one VXLAN device per VPC |
| Routed model | every VM interface is its own L3 link; the host answers ARP/NDP; host routes per workload. **No L2 adjacency** between workloads, no broadcast over the overlay |
| Remote destinations | route, neighbor and FDB entry are set **statically** – no learning, no flooding |
| Encapsulation | VXLAN, only on the WireGuard interface; Geneve remains an option for a later eBPF data path |
| Overlapping addresses | VRF separates routing, a conntrack zone per VPC separates connection state |
| VNI allocation | 24 bits, per region; not reused as long as logs refer to it |
| Anti-spoofing | per interface only assigned MAC/IP addresses; DHCP and RA responses from the VM are dropped |
| Distributed routing | routing between subnets of a VPC on the source host, without detouring via gateways |

### Control flow

1. A user creates a subnet or a VM via API, portal or MCP (see [API-first](api-first.html)).
2. The cell's network controller assigns IP and MAC and binds the interface to a host.
3. That host's agent creates VRF, VXLAN, TAP and rules and reports "ready".
4. The agents of all other hosts in the VPC receive the new endpoint via a filtered watch and set route, neighbor, FDB and security group sets.

The **source of truth** (desired state and bindings) lives in the Raft of the project's home cell; gossip is deliberately not used for the overlay. A host only sees the VPCs it participates in. If the agent or Raft fails, routes and rules remain in effect in the kernel; after a restart, the agent reconciles actual and desired state and writes only the differences. Target: a new VM within the cell is reachable in under 2 s. Details on the control plane under [Control plane](control-plane.html).

### Security groups

Security groups are stateful and **default-deny inbound**. Outbound, the default group allows everything; from the "Standard/C5" operating profile on, the operator can enforce outbound "deny" as a guardrail. Rules reference CIDRs, other security groups or prefix lists; memberships are maintained as nftables sets, so changes are only set updates. Enforcement happens **twice** – inbound at the destination host and outbound at the source host – so that a compromised host can only bypass its own rules. Dropped packets flow into the flow logs, rate-limited. Stateless network ACLs at subnet level follow in phase 2.

### DHCP, DNS, metadata

| Service | Implementation |
|---|---|
| DHCPv4/v6, router advertisement | answered locally per interface, static assignment from the desired state; no DHCP traffic in the overlay |
| DNS | one resolver address per VPC, answered by the local host: internal zone plus forwarding to the outside with DNSSEC validation |
| Metadata / workload identity | preferably via virtio-vsock; the link-local address only with a mandatory token; responses only for the requesting interface |

Because these parsers process data from the workload boundary, they do **not** run in the agent's main process but in a sandboxed helper process without access to the node key, with minimal privileges, size limits and a separate fuzzing target for each. Workload identities are still issued by the agent (see [Identity and access](identity.html)).

## Workload attachment

- **VMs (Cloud Hypervisor):** the agent creates the TAP interface, attaches it to the VRF and hands it over via file descriptor to the unprivileged hypervisor process. Multiple interfaces per VM are allowed. For **live migration**, the destination host sets up VRF and TAP in advance; the switchover is a binding change plus gratuitous ARP, with a target interruption of under 1 s.
- **Container instances (Kata):** a platform CNI plugin (`cp-cni`) creates the namespace and veth pair and attaches the host side to the VRF like a TAP. The container instance is thus a normal interface in the VPC.
- **Managed Kubernetes (k3s):** tenant clusters run on VMs in the tenant VPC. In the MVP, the cluster uses flannel (VXLAN in VXLAN, pod MTU 1,300); from phase 2 on, a VPC-native CNI with alias IP ranges and no double encapsulation follows. Kubernetes services of type `LoadBalancer` are mapped to platform load balancers.

## North-south traffic

### The `network-gateway` role

| Function | Implementation | Phase |
|---|---|---|
| NAT gateway | SNAT on gateway nodes participating in the VPC | MVP |
| Floating IP | 1:1 NAT on the owning gateway | MVP |
| L4 load balancer | nftables DNAT with hash distribution, health checks by the agent | MVP (external), phase 2 (internal, distributed) |
| L7 load balancer, TLS termination | as a separate service behind a process boundary | phase 3 |
| Underlay relay | optional on gateways (the higher trust level then applies) | MVP for multiple sites |

Each region has at least two gateway nodes in different failure zones; single-node installations take on the role without redundancy and with a warning. Because gateways see tenants' north-south traffic in plaintext, a minimum trust level applies to them as well.

### Floating IPs and ownership

Floating IPs exist only explicitly and come from regional pools allocated to projects by quota. Each floating IP belongs to exactly one gateway; ownership is a **Raft lease with a fencing epoch**. If a gateway is confirmed to have failed, another one takes over after the lease expires and announces the address. **Without Raft quorum there is no reassignment** – this rules out the same address being claimed twice. A VRRP-style local election between gateways was deliberately rejected.

### Homelab and data center

- **Homelab (`l2announce`):** floating IPs come from a LAN range that the operator excludes from DHCP on the home router; the setup wizard checks via ARP whether addresses are in use. The owning gateway answers ARP/NDP and sends gratuitous ARP or unsolicited neighbor advertisements on takeover. Port forwarding on the home router remains the operator's task; the portal displays it. In the MVP, VPCs use IPv6 ULA only; public IPv6 follows in phase 2.
- **Data center (BGP/EVPN):** gateways announce host routes via BGP to the top-of-rack switch, with ECMP for load balancer VIPs. Later, EVPN can extend the VPC VXLANs into the fabric, because `cp-vnet` uses exactly the Linux EVPN model. Routing daemons run only behind a process boundary.

### Platform DNS

The platform manages its own DNS records itself; the operator's central DNS only points to the cluster.

Platform records (portal/API, nodes, boot service, SOA/NS) are created automatically from the cluster state; custom records are added via API, CLI, MCP and portal. Integration uses NS delegation **and** conditional forwarding to **two fixed VIPs per region**, which automatically move to healthy nodes with the `dns` role – using the same lease-and-fencing pattern as floating IPs. The authoritative server `cp-dnsd` is an in-house development and runs as a separate service without the node key, with rate limits and fuzzing; DNSSEC is configurable per zone (on by default, off in the homelab profile). More on the [Platform DNS](dns.html) page.

**DDoS protection:** in the MVP, there are baseline settings in the gateway kernel (SYN cookies, connection limits per floating IP and source); later come bandwidth limits per tenant, black-holing via BGP, detection of **outbound** attacks via flow logs and an XDP early-drop filter.

## Failure and observability

| Scenario | Behavior |
|---|---|
| Agent crashes | WireGuard configuration and data path remain in the kernel; DHCP/DNS locally unavailable until restart (seconds) – hence a DHCP lease time of at least 1 h |
| Cell's Raft quorum missing | existing VPCs, security groups and floating IPs keep running; changes are rejected |
| Network partition | minority side: local traffic keeps flowing, no floating IP takeover without quorum |
| Gateway fails | floating IPs and NAT move to another gateway after the lease expires; existing NAT connections are dropped in the MVP |
| Compromised host | revocation removes it from all peers within seconds; it only sees the traffic of the workloads that ran on it |

**Observability:** flow logs belong to the **tenant**; the operator only sees aggregated, pseudonymized statistics, and tenant details only via a logged access request. In addition, there are underlay metrics, a drift counter (actual versus desired) and a topology export for auditors.

**API resources:** tenants work with `Vpc`, `Subnet`, `SecurityGroup`, `NetworkInterface`, `NatGateway`, `FloatingIp` and `LoadBalancer`, later with peering, route tables and flow log configuration. Peering between tenants requires **acceptance on both sides**; creating floating IPs is a separate permission because it creates public reachability.

## Phases

| Phase | Contents |
|---|---|
| **MVP** | underlay with intent mesh and relays, coordinated key rotation, PQ PSK; `cp-vnet` with VPC, subnet (IPv4, optionally IPv6 ULA), security group, interface, NAT gateway, floating IP in L2 mode, external L4 load balancer; local DHCP/DNS/metadata; container instances; k3s with flannel; logical zones |
| **Phase 2** | physical VLAN zones, public IPv6, peering, route tables, network ACLs, flow logs, internal distributed load balancer, VPC-native CNI, bandwidth limits, BGP, DNSSEC/DoT for resolvers, topology export, uninterrupted key rotation |
| **Phase 3** | EVPN, cross-cell VPCs, direct NAT traversal, ciphertext-only relays, eBPF/XDP acceleration, conntrack synchronization, optional OVN backend, IPsec underlay profile |

Testing takes place in network namespaces in CI, in virtual environments with more than 100 nodes, on real Pi hardware and through an external penetration test of tenant isolation. Further background: [Security model](security-model.html), [Threat model](threat-model.html), [Storage](storage.html).
