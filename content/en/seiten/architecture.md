title: Architecture
summary: How BYOC is built – an agent on every node, a control plane with Raft and gossip, cells and regions, networking, the OS image and the update chain.
toc: ja
de: architektur
---
## Layered overview

BYOC has no central controller. **Every node** runs the same agent, `cp-agent`, which serves the
API, the portal and MCP, forwards requests to the responsible place and enforces the desired state
of its node. The desired state is held in a **Raft group per cell**; membership and reachability
spread via **gossip**. Underneath sits the immutable operating system **cpOS**.

::: html
<figure class="diagram" role="group" aria-labelledby="sch-cap">
<svg viewBox="0 0 860 420" role="img" aria-labelledby="sch-t sch-d">
<title id="sch-t">Layer model of BYOC</title>
<desc id="sch-d">At the top, the access paths: portal, REST API and cpctl, MCP. Below that, the cp-agent on every node with API ingress, router, reconcilers, roles and audit. Below that, the control core with Raft per cell and gossip. External components such as the hypervisor and storage run as separate systemd units. At the bottom, cpOS and hardware.</desc>
<rect class="box2" x="20" y="15" width="820" height="60" rx="10"/>
<text x="40" y="38" class="b">Access paths – equal</text>
<rect class="box" x="230" y="27" width="140" height="38" rx="6"/><text x="300" y="51" text-anchor="middle">Web portal</text>
<rect class="box" x="390" y="27" width="180" height="38" rx="6"/><text x="480" y="51" text-anchor="middle">REST API · cpctl · IaC</text>
<rect class="box" x="590" y="27" width="230" height="38" rx="6"/><text x="705" y="51" text-anchor="middle">MCP (AI assistants, agents)</text>
<rect class="box3" x="20" y="95" width="820" height="150" rx="10"/>
<text x="40" y="118" class="b">cp-agent – one process per node</text>
<rect class="box" x="40" y="130" width="180" height="46" rx="6"/><text x="130" y="150" text-anchor="middle">API ingress</text><text x="130" y="166" text-anchor="middle" class="s">AuthN/AuthZ, quotas</text>
<rect class="box" x="235" y="130" width="180" height="46" rx="6"/><text x="325" y="150" text-anchor="middle">Router</text><text x="325" y="166" text-anchor="middle" class="s">URN → region/cell → leader</text>
<rect class="box" x="430" y="130" width="190" height="46" rx="6"/><text x="525" y="150" text-anchor="middle">Reconcilers</text><text x="525" y="166" text-anchor="middle" class="s">cell controllers, nodes</text>
<rect class="box" x="635" y="130" width="185" height="46" rx="6"/><text x="727" y="150" text-anchor="middle">Audit · telemetry</text><text x="727" y="166" text-anchor="middle" class="s">signed, hash-chained</text>
<rect class="box" x="40" y="188" width="380" height="44" rx="6"/><text x="230" y="208" text-anchor="middle">Control core: Raft (state) · gossip (membership)</text><text x="230" y="224" text-anchor="middle" class="s">dedicated runtime, prioritized</text>
<rect class="box" x="430" y="188" width="390" height="44" rx="6"/><text x="625" y="208" text-anchor="middle">Roles as modules</text><text x="625" y="224" text-anchor="middle" class="s">control · boot · dns · identity · compute · storage · gateway …</text>
<rect class="box4" x="20" y="265" width="820" height="56" rx="10"/>
<text x="40" y="288" class="b">Separate processes</text>
<text x="40" y="308" class="s">Sandboxed services without the node key (network boot, DNS) · privileged helper with a fixed command set · hypervisor, storage and network services as systemd units</text>
<rect class="box" x="20" y="340" width="820" height="60" rx="10"/>
<text x="40" y="364" class="b">cpOS + hardware</text>
<text x="40" y="385" class="s">immutable /usr (dm-verity, A/B) · Secure/Measured Boot · TPM2 + LUKS2 · amd64, arm64, Raspberry Pi</text>
<path class="ln" d="M430 75 V93"/><path class="ln" d="M430 245 V263"/><path class="ln" d="M430 321 V338"/>
</svg>
<figcaption id="sch-cap">Layer model. Restarting the agent does not stop any workloads, because external components run as separate systemd units.</figcaption>
</figure>
:::

Key principles:

- **Two levels of truth.** Raft holds the desired state, assignments and leases. Gossip carries
  membership, reachability and short-lived metadata – and **never on its own** triggers a
  destructive action.
- **Static stability.** If the control plane fails, all workloads keep running; nodes continue with
  the last known desired state.
- **Reconcilers are level-triggered, idempotent and safeguarded.** Cell controllers run as shards
  with leases; every write carries an epoch token, and stale writers are rejected.
- **Parsers at trust boundaries** (network boot, DNS, input from devices) run in their own
  sandboxed processes without access to the node key.

Details: [Control plane architecture](docs/control-plane.html) ·
[Rust stack](docs/rust-stack.html).

## Cells and regions

A **cell** is the unit of consensus and fault isolation (guideline value: up to about 1,000 nodes).
Several cells form a **region**; a small region Raft group holds region-wide data.
With only one cell, the two groups coincide. Requests are routed to the right cell using the
resource's **URN** and a versioned shard map.

::: html
<figure class="diagram" role="group" aria-labelledby="zel-cap">
<svg viewBox="0 0 860 300" role="img" aria-labelledby="zel-t zel-d">
<title id="zel-t">Region with several cells</title>
<desc id="zel-d">A region contains a small region Raft group and several cells. Each cell has a control group with three or five voters and many worker nodes, connected via gossip.</desc>
<rect class="box2" x="10" y="10" width="840" height="280" rx="12"/>
<text x="30" y="34" class="b">Region</text>
<rect class="box4" x="300" y="22" width="260" height="40" rx="8"/><text x="430" y="47" text-anchor="middle">Region Raft (tenants, identity, map)</text>
<g>
<rect class="box3" x="30" y="80" width="390" height="190" rx="10"/><text x="50" y="102" class="b">Cell A</text>
<text x="50" y="124" class="s">Control group (Raft, 3 or 5 voters)</text>
<circle class="box2" cx="80" cy="152" r="18"/><text x="80" y="157" text-anchor="middle" class="s">L</text>
<circle class="box2" cx="130" cy="152" r="18"/><circle class="box2" cx="180" cy="152" r="18"/>
<text x="50" y="200" class="s">Worker nodes (gossip/SWIM)</text>
<g class="nodes"><rect class="box" x="50" y="210" width="34" height="26" rx="4"/><rect class="box" x="92" y="210" width="34" height="26" rx="4"/><rect class="box" x="134" y="210" width="34" height="26" rx="4"/><rect class="box" x="176" y="210" width="34" height="26" rx="4"/><rect class="box" x="218" y="210" width="34" height="26" rx="4"/><rect class="box" x="260" y="210" width="34" height="26" rx="4"/><rect class="box" x="302" y="210" width="34" height="26" rx="4"/><rect class="box" x="344" y="210" width="34" height="26" rx="4"/></g>
<path class="ln dash" d="M130 170 V208"/>
</g>
<g>
<rect class="box3" x="440" y="80" width="390" height="190" rx="10"/><text x="460" y="102" class="b">Cell B</text>
<text x="460" y="124" class="s">Control group (Raft, 3 or 5 voters)</text>
<circle class="box2" cx="490" cy="152" r="18"/><text x="490" y="157" text-anchor="middle" class="s">L</text>
<circle class="box2" cx="540" cy="152" r="18"/><circle class="box2" cx="590" cy="152" r="18"/><circle class="box2" cx="640" cy="152" r="18"/><circle class="box2" cx="690" cy="152" r="18"/>
<text x="460" y="200" class="s">Worker nodes (gossip/SWIM)</text>
<rect class="box" x="460" y="210" width="34" height="26" rx="4"/><rect class="box" x="502" y="210" width="34" height="26" rx="4"/><rect class="box" x="544" y="210" width="34" height="26" rx="4"/><rect class="box" x="586" y="210" width="34" height="26" rx="4"/><rect class="box" x="628" y="210" width="34" height="26" rx="4"/><rect class="box" x="670" y="210" width="34" height="26" rx="4"/><rect class="box" x="712" y="210" width="34" height="26" rx="4"/><rect class="box" x="754" y="210" width="34" height="26" rx="4"/>
<path class="ln dash" d="M540 170 V208"/>
</g>
<path class="ln" d="M380 62 L230 80"/><path class="ln" d="M480 62 L630 80"/>
</svg>
<figcaption id="zel-cap">Region with two cells. "L" marks the Raft leader. The failure of a cell affects only that cell.</figcaption>
</figure>
:::

| Nodes | Control group | Cells | Notes |
|---|---|---|---|
| 2 | 2 + witness | 1 | Witness (e.g. a small Raspberry Pi) mandatory for quorum |
| 3–20 | 3 | 1 | Standard homelab |
| 20 – approx. 1,000 | 5 | 1 | Gossip for membership, Raft only for state |
| > approx. 1,000 | 5 per cell | n | Region level coordinates cells |
| multiple sites | per region | n | Federation with global identity (later phase) |

The control group is formed **automatically** and grows along with the cluster: one node → two data
nodes plus a witness → three → five voters. New members start as learners and are only promoted
once they have caught up; there is only ever one membership change at a time.

## Two nodes with a witness

Two nodes on their own cannot decide which one may keep working during a network partition. A
**witness** – a lightweight voter without user data that never becomes leader itself – provides the
third vote. If one data node fails, the other continues working with the witness. If only one node
is left, the remaining operation is **read-only**; writing without quorum is possible only through
a logged break-glass procedure, never automatically.

::: html
<figure class="diagram" role="group" aria-labelledby="zg-cap">
<svg viewBox="0 0 860 160" role="img" aria-labelledby="zg-t zg-d">
<title id="zg-t">Two-node operation with a witness</title>
<desc id="zg-d">Two data nodes replicate the Raft state. A witness takes part in voting but holds no user data.</desc>
<rect class="box3" x="60" y="40" width="220" height="80" rx="10"/><text x="170" y="74" text-anchor="middle" class="b">Node 1</text><text x="170" y="96" text-anchor="middle" class="s">control · data · voter</text>
<rect class="box3" x="580" y="40" width="220" height="80" rx="10"/><text x="690" y="74" text-anchor="middle" class="b">Node 2</text><text x="690" y="96" text-anchor="middle" class="s">control · data · voter</text>
<rect class="box4" x="355" y="50" width="150" height="60" rx="10"/><text x="430" y="76" text-anchor="middle" class="b">Witness</text><text x="430" y="96" text-anchor="middle" class="s">vote, no user data</text>
<path class="ln" d="M280 70 H353"/><path class="ln" d="M505 70 H578"/>
<path class="ln dash" d="M280 112 C 400 150, 460 150, 580 112"/><text x="430" y="150" text-anchor="middle" class="s">Raft replication of the state</text>
</svg>
<figcaption id="zg-cap">Two nodes plus a witness form a quorum of three votes.</figcaption>
</figure>
:::

## Network

The platform **always separates networks cryptographically** and, where the infrastructure
allows it, additionally physically via VLANs or routed segments.

::: html
<figure class="diagram" role="group" aria-labelledby="net-cap">
<svg viewBox="0 0 860 250" role="img" aria-labelledby="net-t net-d">
<title id="net-t">Underlay and tenant overlay</title>
<desc id="net-d">Physical network at the bottom. Above it, the WireGuard underlay between all nodes, IPv6 inside. Above that, tenant VPCs as VRFs with VXLAN, carried exclusively inside the WireGuard tunnel. North-south traffic via network-gateway nodes.</desc>
<rect class="box" x="20" y="190" width="820" height="44" rx="8"/><text x="430" y="217" text-anchor="middle">Physical network: flat (one LAN) · vlan · routed (L3 to the host, BGP)</text>
<rect class="box2" x="20" y="125" width="820" height="50" rx="8"/><text x="430" y="148" text-anchor="middle" class="b">Underlay: WireGuard per node, IPv6 inside</text><text x="430" y="166" text-anchor="middle" class="s">Peers from Raft (keys) and gossip (endpoints) · additional post-quantum PSK · mTLS for control traffic</text>
<rect class="box3" x="20" y="20" width="250" height="90" rx="8"/><text x="145" y="45" text-anchor="middle" class="b">Tenant A VPC</text><text x="145" y="66" text-anchor="middle" class="s">VRF · VXLAN in the tunnel</text><text x="145" y="84" text-anchor="middle" class="s">Security groups (default-deny)</text>
<rect class="box3" x="290" y="20" width="250" height="90" rx="8"/><text x="415" y="45" text-anchor="middle" class="b">Tenant B VPC</text><text x="415" y="66" text-anchor="middle" class="s">VRF · VXLAN in the tunnel</text><text x="415" y="84" text-anchor="middle" class="s">local DHCP/DNS/metadata per host</text>
<rect class="box4" x="560" y="20" width="280" height="90" rx="8"/><text x="700" y="45" text-anchor="middle" class="b">network-gateway</text><text x="700" y="66" text-anchor="middle" class="s">NAT · floating IPs · L4 load balancer</text><text x="700" y="84" text-anchor="middle" class="s">Advertised via L2 or BGP</text>
<path class="ln" d="M145 110 V123"/><path class="ln" d="M415 110 V123"/><path class="ln" d="M700 110 V123"/>
</svg>
<figcaption id="net-cap">Overlay packets leave a node only encrypted inside the WireGuard underlay.</figcaption>
</figure>
:::

Details: [Network architecture](docs/network.html) · [Platform DNS](docs/dns.html).

## Boot and trust chain

Every boot starts from signed specifications. The chain is implemented differently on UEFI systems
and on the Raspberry Pi, but follows the same principle.

::: html
<figure class="diagram" role="group" aria-labelledby="boot-cap">
<svg viewBox="0 0 860 150" role="img" aria-labelledby="boot-t boot-d">
<title id="boot-t">Boot and trust chain on UEFI systems</title>
<desc id="boot-d">Firmware with Secure Boot, signed bootloader, signed Unified Kernel Image, read-only /usr via dm-verity, state partition unlocked via TPM, cp-agent, health gate.</desc>
<defs><marker id="ah2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path class="arrowhead" d="M0,0 L10,5 L0,10 z"/></marker></defs>
<rect class="box" x="10" y="40" width="110" height="60" rx="8"/><text x="65" y="66" text-anchor="middle">Firmware</text><text x="65" y="84" text-anchor="middle" class="s">Secure Boot</text>
<rect class="box" x="135" y="40" width="110" height="60" rx="8"/><text x="190" y="66" text-anchor="middle">Bootloader</text><text x="190" y="84" text-anchor="middle" class="s">signed</text>
<rect class="box2" x="260" y="40" width="110" height="60" rx="8"/><text x="315" y="66" text-anchor="middle">UKI</text><text x="315" y="84" text-anchor="middle" class="s">Kernel+Initrd+Cmdline</text>
<rect class="box2" x="385" y="40" width="110" height="60" rx="8"/><text x="440" y="66" text-anchor="middle">/usr</text><text x="440" y="84" text-anchor="middle" class="s">dm-verity, A/B</text>
<rect class="box2" x="510" y="40" width="110" height="60" rx="8"/><text x="565" y="66" text-anchor="middle">State</text><text x="565" y="84" text-anchor="middle" class="s">LUKS2 + TPM2</text>
<rect class="box3" x="635" y="40" width="100" height="60" rx="8"/><text x="685" y="66" text-anchor="middle">cp-agent</text><text x="685" y="84" text-anchor="middle" class="s">hardened</text>
<rect class="box3" x="750" y="40" width="100" height="60" rx="8"/><text x="800" y="66" text-anchor="middle">Health gate</text><text x="800" y="84" text-anchor="middle" class="s">boot valid</text>
<path class="ln" d="M120 70 H133" marker-end="url(#ah2)"/><path class="ln" d="M245 70 H258" marker-end="url(#ah2)"/><path class="ln" d="M370 70 H383" marker-end="url(#ah2)"/><path class="ln" d="M495 70 H508" marker-end="url(#ah2)"/><path class="ln" d="M620 70 H633" marker-end="url(#ah2)"/><path class="ln" d="M735 70 H748" marker-end="url(#ah2)"/>
<text x="430" y="130" text-anchor="middle" class="s">Measurements (PCRs) feed into the TPM policy; only an unmodified, signed system unlocks the state partition.</text>
</svg>
<figcaption id="boot-cap">Boot and trust chain (UEFI). The Raspberry Pi uses its native bootloader with its own A/B mechanism.</figcaption>
</figure>
:::

`/` is an ephemeral tmpfs, and `/etc` is generated from the signed specifications on every boot.
Persistence exists only in the encrypted state partition. Role-specific runtimes
(hypervisor, storage, Kubernetes) are added as signed system extensions.
Details: [OS image](docs/os-image.html) · [Boot and adoption](docs/boot-adoption.html) ·
[Security model](docs/security-model.html).

## Release and update chain

::: html
<figure class="diagram" role="group" aria-labelledby="upd-cap">
<svg viewBox="0 0 860 210" role="img" aria-labelledby="upd-t upd-d">
<title id="upd-t">The path of an update</title>
<desc id="upd-d">Reproducible build, offline signing, release bundle, import and verification in the platform, rollout controller in waves, node writes the inactive slot, reboot, health gate. On failure, automatic rollback to the old slot and the rollout halts.</desc>
<defs><marker id="ah3" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path class="arrowhead" d="M0,0 L10,5 L0,10 z"/></marker></defs>
<rect class="box" x="10" y="30" width="120" height="60" rx="8"/><text x="70" y="56" text-anchor="middle">Build</text><text x="70" y="74" text-anchor="middle" class="s">reproducible, SBOM</text>
<rect class="box" x="150" y="30" width="120" height="60" rx="8"/><text x="210" y="56" text-anchor="middle">Signing</text><text x="210" y="74" text-anchor="middle" class="s">offline, TUF roles</text>
<rect class="box2" x="290" y="30" width="120" height="60" rx="8"/><text x="350" y="56" text-anchor="middle">Release bundle</text><text x="350" y="74" text-anchor="middle" class="s">manifest + artifacts</text>
<rect class="box2" x="430" y="30" width="120" height="60" rx="8"/><text x="490" y="56" text-anchor="middle">Import</text><text x="490" y="74" text-anchor="middle" class="s">verification, dedup</text>
<rect class="box3" x="570" y="30" width="130" height="60" rx="8"/><text x="635" y="56" text-anchor="middle">Rollout</text><text x="635" y="74" text-anchor="middle" class="s">waves, gates</text>
<rect class="box3" x="720" y="30" width="130" height="60" rx="8"/><text x="785" y="56" text-anchor="middle">Node</text><text x="785" y="74" text-anchor="middle" class="s">inactive slot</text>
<path class="ln" d="M130 60 H148" marker-end="url(#ah3)"/><path class="ln" d="M270 60 H288" marker-end="url(#ah3)"/><path class="ln" d="M410 60 H428" marker-end="url(#ah3)"/><path class="ln" d="M550 60 H568" marker-end="url(#ah3)"/><path class="ln" d="M700 60 H718" marker-end="url(#ah3)"/>
<rect class="box3" x="720" y="130" width="130" height="50" rx="8"/><text x="785" y="152" text-anchor="middle">Health gate green</text><text x="785" y="168" text-anchor="middle" class="s">new version applies</text>
<rect class="box4" x="520" y="130" width="180" height="50" rx="8"/><text x="610" y="152" text-anchor="middle">Gate red</text><text x="610" y="168" text-anchor="middle" class="s">rollback, rollout halts</text>
<path class="ln" d="M785 90 V128" marker-end="url(#ah3)"/><path class="ln dash" d="M760 90 L690 128" marker-end="url(#ah3)"/>
</svg>
<figcaption id="upd-cap">Release and update chain. The agent, the installer and the import verify a bundle by the same rules.</figcaption>
</figure>
:::

Details: [Rollout controller](docs/rollout.html) · [Release bundle](docs/release-bundle.html) ·
[Release signing](docs/release-signing.html).

## Technology decisions

| Area | Decision |
|---|---|
| Language | Rust (Edition 2024), `unsafe` forbidden in principle, exceptions only when registered |
| Runtime | tokio, axum (REST, SSE, MCP), tonic/gRPC internally with mTLS |
| Consensus / membership | openraft per cell, SWIM gossip (foca) |
| Local storage | redb (embedded) |
| Authorization | dedicated relationship store + Cedar policies |
| Virtualization | Cloud Hypervisor/KVM, MicroVMs for containers |
| Object storage | Garage behind a dedicated S3 front end |
| OS image | mkosi from Debian 13 packages, systemd building blocks (UKI, repart, sysupdate, sysext) |
| Portal | Single-page app with Svelte 5 and Vite, types and forms generated from the API schema |
| Architectures | amd64 and arm64 (incl. Raspberry Pi 4/5), cross-compilation |

Rationale: [ADR Rust stack](docs/rust-stack.html) · [ADR portal technology](docs/portal.html).
