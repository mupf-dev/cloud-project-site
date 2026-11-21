title: Status and roadmap
summary: What BYOC can do today, how that is verified, what is built in-house and what is integrated – and what comes next on the way to the MVP and release 1.0.
toc: ja
de: roadmap
---
## At a glance {#overview}

> **Alpha, before the first release.** Version 0.x, all API groups in `v1alpha1`. BYOC is
> **not suitable for production use**; interfaces and formats may still change.
> BYOC (Build Your Own Cloud) is an alpha name. Dates on this page are planning targets,
> not commitments.

::: html
<ol class="rm-phases" aria-label="Phases of BYOC">
<li class="done"><span class="n">Phase</span><strong>Concept and architecture</strong><span class="status-ok">Completed</span><p>Milestone "Architecture in place" on 2026-11-12.</p></li>
<li class="run"><span class="n">Phase</span><strong>Foundation</strong><span class="status-run">Largely built</span><p>OS image, cluster core, access paths, identity, underlay; updates and DNS in acceptance.</p></li>
<li class="next"><span class="n">Milestone</span><strong>Plug in → node in the cluster</strong><span class="status-run">In progress</span><p>Second node via network boot on real hardware. Planned: Q1 2027.</p></li>
<li><span class="n">Milestone</span><strong>MVP homelab</strong><span class="status-plan">Planned</span><p>Tenants, VMs, containers, Kubernetes, storage, network services. Target: Q2 2027.</p></li>
<li><span class="n">Milestone</span><strong>Release 1.0</strong><span class="status-plan">Planned</span><p>Extended services, AI inference, multiple regions. Target: mid-2027.</p></li>
</ol>
:::

The overview shows the status of each area and how it is built. Select an area to jump to its description.

::: html
<ul class="rm-legend" aria-label="Legend">
<li><span class="status-ok">Done</span><span>implemented and verified in a lab</span></li>
<li><span class="status-review">In acceptance</span><span>implemented, sign-off pending</span></li>
<li><span class="status-run">Partial</span><span>foundation in place, parts still to come</span></li>
<li><span class="status-plan">Planned</span><span>concept decided, implementation to follow</span></li>
<li><span class="kind own">In-house</span><span>built entirely by the project</span></li>
<li><span class="kind lib">In-house + library</span><span>own implementation on proven libraries</span></li>
<li><span class="kind mix">In-house + integrated</span><span>own control logic, existing solution as a separate component</span></li>
<li><span class="kind ext">Integrated</span><span>existing solution, used as is</span></li>
</ul>
<ul class="rm-matrix" aria-label="Status by area">
<li><a href="#os-image">OS image and boot (cpOS)</a><span class="status-ok">Done</span><span class="kind mix">In-house + integrated</span></li>
<li><a href="#network-boot">Network boot service</a><span class="status-ok">Done (lab)</span><span class="kind mix">In-house + integrated</span></li>
<li><a href="#adoption">First node, adoption and installer</a><span class="status-ok">Done</span><span class="kind mix">In-house + integrated</span></li>
<li><a href="#control-plane">Control plane: Raft, gossip, cells</a><span class="status-ok">Done</span><span class="kind lib">In-house + library</span></li>
<li><a href="#node-security">Node identity and cryptography</a><span class="status-ok">Done</span><span class="kind lib">In-house + library</span></li>
<li><a href="#identity">Identity and tenants</a><span class="status-run">Partial</span><span class="kind lib">In-house + library</span></li>
<li><a href="#access">API, portal, MCP and CLI with parity</a><span class="status-ok">Done</span><span class="kind lib">In-house + library</span></li>
<li><a href="#updates">Updates and releases</a><span class="status-review">In acceptance</span><span class="kind mix">In-house + integrated</span></li>
<li><a href="#platform-dns">Platform DNS</a><span class="status-review">In acceptance</span><span class="kind lib">In-house + library</span></li>
<li><a href="#network">Network: WireGuard underlay</a><span class="status-ok">Done</span><span class="kind mix">In-house + integrated</span></li>
<li><a href="#storage">Storage</a><span class="status-plan">Planned</span><span class="kind mix">In-house + integrated</span></li>
<li><a href="#supply-chain">Supply chain and compliance</a><span class="status-ok">Done</span><span class="kind ext">Integrated</span></li>
<li><a href="#test-labs">Test and lab infrastructure</a><span class="status-ok">Done</span><span class="kind mix">In-house + integrated</span></li>
</ul>
:::

## Built in-house – and when not {#in-house}

The project's guiding principle: **whatever controls the platform, BYOC builds itself** – in Rust,
fitting the shared Raft state, the permission model and the parity of API, portal and MCP. Existing
solutions are integrated **only with a reason**, where maturity, security or maintenance effort do not
justify building our own: Linux kernel features, the hypervisor, container runtimes, database and
storage engines with a high maintenance burden, and supply-chain checking tools. Integrated components
run behind clear process boundaries. This page names Rust libraries only where they carry significant
weight. The full assessment per feature is in the
[hyperscaler feature analysis](docs/hyperscaler-analysis.html).

## What has been achieved {#achieved}

Everything in this section is implemented and verified at least in an automated lab. Where
verification on real hardware is still pending, this is stated.

### OS image and boot (cpOS) {#os-image}

::: html
<p class="rm-tags"><span class="status-ok">Done</span><span class="kind mix">In-house + integrated</span></p>
:::

An immutable node operating system for amd64 and arm64 (UEFI). `/usr` is read-only and protected
against tampering with dm-verity; there are two slots (A/B) for updates. Kernel, initrd and command
line are packed into a signed unified kernel image, signed with the project's own Secure Boot keys.
The state partition is encrypted with LUKS2 and bound to TPM 2.0; without a TPM only the "homelab"
profile with a passphrase is allowed. After every boot a health gate checks whether the node is
healthy – otherwise the boot loader falls back to the previous slot after three attempts. Out of the
box there is no login, no SSH and no package manager; inbound traffic is denied by default.

- **In-house:** image definition, partition layout, hardening profile, operating modes, health gate.
- **Integrated:** Debian packages, the Linux kernel (dm-verity, dm-crypt/LUKS2, TPM 2.0), systemd
  (systemd-boot, systemd-repart, systemd-sysupdate), mkosi as the build tool, AppArmor, nftables.
- **Verification:** end-to-end boot tests in QEMU for both architectures with an emulated TPM;
  automated hardening checks in the booted image. A first node runs on a used business notebook.
  Raspberry Pi support is prepared but
  not yet tested on real hardware.

More: [OS image](docs/os-image.html).

### Network boot service {#network-boot}

::: html
<p class="rm-tags"><span class="status-ok">Done (lab)</span><span class="kind mix">In-house + integrated</span></p>
:::

The boot service `cp-bootd` runs as a role on cluster nodes and complements the existing DHCP server
instead of replacing it (proxyDHCP). It handles PXE for BIOS and UEFI, UEFI HTTP boot, iPXE and – in
preparation – Raspberry Pi network boot. All artifacts are checked against a signed boot manifest.
Several boot services can run in parallel.

- **In-house:** DHCP and TFTP handling (own lean parsers), boot decisions, manifest.
- **Integrated:** iPXE as the network boot loader (built and signed by the project).
- **Verification:** a QEMU boot lab with two boot services in a simulated home network; fuzz and
  property tests for the parsers. Network boot on real hardware is the next step.

More: [Boot and adoption](docs/boot-adoption.html).

### First node, adoption and installer {#adoption}

::: html
<p class="rm-tags"><span class="status-ok">Done</span><span class="status-review">Refinements in acceptance</span><span class="kind mix">In-house + integrated</span></p>
:::

The first node boots from a USB stick; a setup wizard guides through region, portal address and the
first administrator (invitation plus passkey) via portal, API or MCP. New nodes report as "waiting"
and are approved – manually or by an auto-adopt rule. Roles are assigned declaratively and applied by
a reconciler. The installer writes cpOS to the internal disk following fixed rules: never onto the
boot medium, foreign data only after explicit confirmation, TPM binding and re-signing with the
installation's own key. Nodes can be decommissioned and replaced, even across cell boundaries.

- **In-house:** setup wizard, adoption flow, role model, installer including UEFI boot entries.
- **Integrated:** systemd-repart (partitioning), LUKS2 (encryption).
- **Verification:** QEMU installation from the stick with and without a TPM; container labs for
  adoption and roles; running as the first node on real notebook hardware. Refinements to the setup
  wizard are implemented and in acceptance.

### Control plane: Raft, gossip, cells {#control-plane}

::: html
<p class="rm-tags"><span class="status-ok">Done</span><span class="kind lib">In-house + library</span></p>
:::

`cp-agent` runs on every node. Membership spreads via gossip; the authoritative state lives in one
Raft group per cell. Even two nodes plus a **witness** that holds no payload data are fault tolerant;
the control group is elected automatically. Witnesses write signed checkpoints so that a node that has
been rolled back is detected. The scheduler places workloads by architecture (ARM/x86), resources and
node pools.

- **In-house:** cell and witness model, control group election, state machine, scheduler, node
  lifecycle.
- **Libraries (load-bearing):** openraft (Raft consensus), foca (SWIM gossip), redb (local storage).
- **Verification:** deterministic simulation with fixed random seeds (up to 1,000 seeds per scenario
  without invariant violations) and container labs with multi-node clusters.

More: [Control plane](docs/control-plane.html).

### Node identity and cryptography {#node-security}

::: html
<p class="rm-tags"><span class="status-ok">Done</span><span class="kind lib">In-house + library</span></p>
:::

An internal certificate authority issues an identity to every node; nodes talk to each other only via
mutually authenticated TLS. Algorithms follow selectable crypto profiles aligned with BSI TR-02102.
Privileged tasks are handled by a narrow root helper, `cp-privd`, with a fixed set of commands; the
agent itself runs without root privileges.

- **In-house:** PKI workflows, crypto profiles, root helper, central crypto interface.
- **Libraries (load-bearing):** rustls (TLS), aws-lc-rs (cryptography), rcgen (certificates).
- **Verification:** unit and fuzz tests, container labs with mTLS between all nodes.

More: [Security model](docs/security-model.html), [Cryptography](docs/cryptography.html).

### Identity and tenants {#identity}

::: html
<p class="rm-tags"><span class="status-ok">Identity service done</span><span class="status-plan">Tenants planned</span><span class="kind lib">In-house + library</span></p>
:::

A **purpose-built OIDC/OAuth 2.1 authorization server** runs as the `identity` role. Sign-in is by
passkey (WebAuthn) only; on top of that come authorization code with PKCE, device flow for the command
line, token revocation, DPoP and rate limits. Signing keys live only in the separate `cp-identityd`
process. API, portal, `cpctl` and MCP all use the same tokens.

- **In-house:** authorization server, passkey verification, token and session management.
- **Libraries:** aws-lc-rs (signatures) via the central crypto interface.
- **Verification:** container labs with end-to-end sign-in flows; browser tests with a virtual
  passkey against a real agent.
- **Still open:** tenants, projects, groups, permission model and quotas – see
  [Towards the MVP](#mvp).

More: [Identity and permissions](docs/identity.html).

### API, portal, MCP and CLI with parity {#access}

::: html
<p class="rm-tags"><span class="status-ok">Done</span><span class="kind lib">In-house + library</span></p>
:::

Every agent serves the resource API (REST, OpenAPI) and forwards requests to the responsible node.
The `cpctl` command line and the MCP server for AI agents are derived from the same schema. The web
portal is served by the node itself, shows changes live and is reachable via several nodes. A parity
check in CI ensures that every mutating operation is available in all access paths.

- **In-house:** resource model, API, forwarding, `cpctl`, MCP tools, portal, parity check.
- **Libraries (load-bearing):** axum/hyper (HTTP), rmcp (MCP protocol), Svelte and Vite (portal).
- **Verification:** container labs, browser tests of the portal, parity check in every CI run.

More: [API-first](docs/api-first.html), [Portal](docs/portal.html).

### Updates and releases {#updates}

::: html
<p class="rm-tags"><span class="status-review">In acceptance</span><span class="kind mix">In-house + integrated</span></p>
:::

A release is a signed bundle of OS image, services and SBOM. The signature chain follows the TUF
pattern (several roles, root rotation, rollback protection). Releases are **imported** rather than
fetched online, and at least two nodes hold them for distribution. Nodes write the new release into
the free A/B slot and reboot; the health gate confirms it, or an automatic fallback follows. An update
controller rolls out node by node, protects the Raft quorum, updates the leader last and pauses on
errors. A plan preview shows the order and impact beforehand.

- **In-house:** release format, verification of the signature chain following the TUF specification,
  import and distribution, update controller.
- **Integrated:** systemd-sysupdate (writing the A/B slot), systemd-boot (boot counting, fallback).
- **Verification:** QEMU labs for import, node update and rollout. End-to-end acceptance with rollout
  and rollback, plus a real update on hardware, come next.

More: [Release bundle](docs/release-bundle.html), [Rollout](docs/rollout.html).

### Platform DNS {#platform-dns}

::: html
<p class="rm-tags"><span class="status-review">In acceptance</span><span class="kind lib">In-house + library</span></p>
:::

The cluster manages its own DNS zone: `cp-dnsd` answers authoritatively from the Raft state, with
DNSSEC if desired. Two fixed virtual IP addresses are assigned via a Raft lease (VRRP-like, built
in-house). The existing DNS server on the network only needs a forwarder or a delegation to these
addresses.

- **In-house:** DNS server logic, zone building, DNSSEC signing, assignment of the virtual addresses.
- **Library:** hickory-proto – only for the DNS wire format.
- **Verification:** container lab with a multi-node cluster. Failover of the virtual addresses will be
  measured in the two-node hardware test.

More: [Platform DNS](docs/dns.html).

### Network: WireGuard underlay {#network}

::: html
<p class="rm-tags"><span class="status-ok">Underlay done</span><span class="status-plan">Tenant overlay planned</span><span class="kind mix">In-house + integrated</span></p>
:::

Every node builds its encrypted underlay on its own, with no configuration by the operator: a key per
node, signed announcements via the cluster state, full mesh per site, relays between sites and for
nodes behind NAT, key rotation without dropping connections. In addition, a pre-shared key derived
from a hybrid key exchange (classical plus ML-KEM) protects against later decryption by quantum
computers.

- **In-house:** topology planning, key distribution and rotation, netlink control via the root helper.
- **Integrated:** WireGuard in the Linux kernel.
- **Verification:** container labs with multi-node clusters and simulation of the topology.

More: [Network](docs/network.html).

### Storage {#storage}

::: html
<p class="rm-tags"><span class="status-plan">Concept decided, implementation planned</span><span class="kind mix">In-house + integrated</span></p>
:::

The storage concept is decided: a **purpose-built block store**, `cp-blk`, for 2 to more than 1,000
nodes (local first, replicated only after a maturity gate), and S3-compatible object storage with
Garage behind a purpose-built S3 front end. So far, only the nodes' encrypted state partition is
implemented.

More: [Storage](docs/storage.html).

### Supply chain and compliance {#supply-chain}

::: html
<p class="rm-tags"><span class="status-ok">Done</span><span class="kind ext">Integrated</span><span class="kind own">Own rules</span></p>
:::

Every CI run checks formatting, lints, tests, licenses and sources of dependencies, security
advisories, REUSE compliance and the parity and compliance rules. SBOMs (CycloneDX and SPDX) and VEX
documents are produced for binaries and the OS image; releases carry signatures and provenance
attestations. Reproducible builds have been demonstrated for x86_64 and aarch64. A vulnerability
process with coordinated disclosure is in place. Requirements from BSI IT-Grundschutz and ISO
standards are mapped to components – this is preparation, not certification.

- **Integrated:** cargo-deny, cargo-audit, the REUSE tool, cargo-cyclonedx, cosign, OpenSCAP.
- **In-house:** policy-as-code rules, parity and compliance checks, SBOM generation for the OS image.

More: [Compliance by design](docs/compliance-by-design.html),
[Vulnerability management](docs/vulnerability-management.html).

### Test and lab infrastructure {#test-labs}

::: html
<p class="rm-tags"><span class="status-ok">Done</span><span class="kind mix">In-house + integrated</span></p>
:::

- **Deterministic simulation** of the cluster with fixed seeds; a run can be repeated exactly and
  reports the first diverging step (in-house, on the turmoil library).
- **Container labs** with multi-node clusters; every lab is checked against a target table and is
  part of acceptance (in-house).
- **End-to-end labs in QEMU** with UEFI firmware and an emulated TPM for boot, installation, network
  boot and updates (integrated: QEMU, OVMF, swtpm).
- **Browser tests** of the portal with a virtual passkey (integrated: Playwright).
- **Real hardware:** a used business notebook as the first node. More notebooks and Raspberry Pi
  will follow.

## Next steps {#next-steps}

Short term, up to the milestone **"Plug in → node in the cluster"** (planned: Q1 2027):

::: html
<ul class="rm-plan">
<li><strong>Update acceptance</strong><span class="status-plan">Up next</span><p>Rollout and rollback in QEMU labs, then a real update on the notebook first node.</p></li>
<li><strong>Installer via network boot</strong><span class="status-plan">Planned</span><p>The PXE path: network boot, discovery, approval and installation without a USB stick.</p></li>
<li><strong>Second node via network boot</strong><span class="status-plan">Planned</span><p>A second notebook boots over the cable, is adopted and installed; failover of the DNS addresses is measured along the way.</p></li>
<li><strong>Milestone "Plug in → node in the cluster"</strong><span class="status-plan">Planned · Q1 2027</span><p>A new node is adopted and installed through nothing but a network cable – verified on real hardware.</p></li>
<li><strong>Unlocking without a TPM</strong><span class="status-plan">Planned</span><p>Nodes without a TPM unlock their state partition via trusted cluster nodes on the network instead of a passphrase.</p></li>
<li><strong>Remaining foundation work</strong><span class="status-plan">Planned</span><p>Certificate revocation in the handshake, firewall rules generated by the agent, measuring the root helpers in the image.</p></li>
</ul>
:::

## Towards the MVP {#mvp}

Target: Q2 2027. The MVP is a complete small cloud for the homelab: tenants create resources on their
own – via portal, API and MCP.

::: html
<ul class="rm-plan">
<li><strong>Tenants and permissions</strong><span class="kind lib">In-house + library</span><p>Tenants, projects, users, groups, API keys, quotas, audit log. Permissions as an in-house relationship store plus a policy language.</p><p class="with"><b>Integrated:</b> Cedar (policies)</p></li>
<li><strong>Sign-in to VMs and containers</strong><span class="kind own">In-house</span><p>Log in with the platform identity right into the guest OS; roles become permissions inside the guest.</p></li>
<li><strong>Tenant networks</strong><span class="kind mix">In-house + integrated</span><p>VPCs and subnets as an overlay inside the encrypted underlay, IPAM, DHCP, internal DNS, security groups, NAT, floating IPs, load balancers.</p><p class="with"><b>Integrated:</b> Linux kernel (VRF, VXLAN, nftables)</p></li>
<li><strong>Virtual machines</strong><span class="kind mix">In-house + integrated</span><p>Lifecycle, images, cloud-init, console in the portal – own control logic on top of a proven hypervisor.</p><p class="with"><b>Integrated:</b> Cloud Hypervisor</p></li>
<li><strong>Container instances and registry</strong><span class="kind mix">In-house + integrated</span><p>Individual containers with microVM isolation, one registry per tenant.</p><p class="with"><b>Integrated:</b> container runtime and microVM (candidates: containerd, youki, Kata Containers), zot</p></li>
<li><strong>Managed Kubernetes</strong><span class="kind mix">In-house + integrated</span><p>Kubernetes clusters per tenant; BYOC itself handles creation, upgrades and node pools.</p><p class="with"><b>Integrated:</b> k3s</p></li>
<li><strong>Block volumes (local)</strong><span class="kind mix">In-house + integrated</span><p>Purpose-built block store <code>cp-blk</code> with snapshots and per-tenant encryption.</p><p class="with"><b>Integrated:</b> Linux kernel (dm-thin, dm-crypt)</p></li>
<li><strong>Object storage (S3)</strong><span class="kind mix">In-house + integrated</span><p>Buckets per tenant behind a purpose-built S3 front end with permission checks.</p><p class="with"><b>Integrated:</b> Garage</p></li>
<li><strong>Key management</strong><span class="kind own">In-house</span><p>Key hierarchy per tenant and encryption of data at rest.</p></li>
<li><strong>Observability</strong><span class="kind mix">In-house + integrated</span><p>Collection, alerts and dashboards in the portal are built in-house; data is stored in proven time-series and log stores.</p><p class="with"><b>Integrated:</b> VictoriaMetrics, log store (under evaluation)</p></li>
<li><strong>Operations</strong><span class="kind own">In-house</span><p>Backup and restore of the control plane, business continuity and recovery concept, usage metering, update policies and maintenance windows.</p></li>
<li><strong>Security evidence</strong><span class="kind mix">In-house + integrated</span><p>Control matrix and evidence export for operators, external penetration test before the MVP.</p></li>
</ul>
:::

## Towards release 1.0 {#release-1}

Target: mid-2027. After the MVP come the extended services, AI inference and operation across
multiple sites.

::: html
<ul class="rm-plan">
<li><strong>Replicated block storage</strong><span class="kind own">In-house</span><p><code>cp-blk</code> replicated across nodes – only after a maturity gate with simulation, fault injection, long-running tests and external review.</p></li>
<li><strong>File storage (NFS)</strong><span class="kind mix">In-house + integrated</span><p>Shares per tenant on replicated volumes; management and tenant isolation built in-house.</p><p class="with"><b>Integrated:</b> NFS-Ganesha</p></li>
<li><strong>AI inference</strong><span class="kind mix">In-house + integrated</span><p>Detecting and allocating accelerators, model registry, OpenAI-compatible inference endpoints, distributed inference, in-house AI gateway.</p><p class="with"><b>Integrated:</b> llama.cpp, vLLM (inference engines)</p></li>
<li><strong>Databases and messaging</strong><span class="kind mix">In-house + integrated</span><p>Managed databases and queues; lifecycle, backup and permissions built in-house.</p><p class="with"><b>Integrated:</b> PostgreSQL, MariaDB, Valkey, NATS</p></li>
<li><strong>Secrets and certificates</strong><span class="kind own">In-house</span><p>Secrets service, private CA and certificate service for tenants – on the existing Raft state instead of a second consensus system.</p></li>
<li><strong>DNS as a service</strong><span class="kind lib">In-house + library</span><p>Public and private zones for tenants, building on the platform DNS.</p><p class="with"><b>Library:</b> hickory-proto</p></li>
<li><strong>Serverless functions</strong><span class="kind lib">In-house + library</span><p>Functions as WebAssembly with event triggers and scale-to-zero.</p><p class="with"><b>Library:</b> wasmtime</p></li>
<li><strong>L7 load balancer</strong><span class="kind lib">In-house + library</span><p>HTTP routing with TLS termination and automatic ACME certificates.</p><p class="with"><b>Library:</b> Pingora</p></li>
<li><strong>Infrastructure as code and SDKs</strong><span class="kind own">In-house</span><p>OpenTofu provider and SDKs generated from the API schema.</p></li>
<li><strong>Multiple regions and data centers</strong><span class="kind mix">In-house + integrated</span><p>Federation, global API, scale tests with more than 1,000 nodes, hardware management via Redfish/IPMI, BGP connectivity, disaster recovery.</p><p class="with"><b>Integrated:</b> routing daemon for BGP (to be selected)</p></li>
<li><strong>Tenant services for operations and security</strong><span class="kind own">In-house</span><p>Backup service, tenant observability, policy compliance, zero-trust access, platform status.</p></li>
<li><strong>Billing and ecosystem</strong><span class="kind own">In-house</span><p>Billing based on usage metering, self-service sign-up, template marketplace, upgrade and support policy.</p></li>
</ul>
:::

**After that (release 1.x):** autoscaling groups, container serverless, VPN and private endpoints, a
purpose-built object store with versioning and object lock, erasure coding and archive classes,
hardware attestation as a prerequisite for permanent auto-adopt rules, and a topology model for racks.
After the MVP, the API groups move from `v1alpha1` via `v1beta1` to `v1`.

## Quality gates {#quality-gates}

- **Phase 1 gate:** fault tolerance (two nodes plus witness, no single point of failure from three
  nodes up) is demonstrated in a **deterministic simulation** with 10,000 random seeds without
  invariant violations and on **real hardware**. The simulation already runs with up to 1,000 seeds
  per scenario; the full run and the hardware proof are still pending.
- **Before every phase gate:** tests on real hardware (Raspberry Pi, notebooks, servers).
- **Before every minor release:** Jepsen-style consistency checks.
- **Before tenant data on replicated volumes:** maturity gate with simulation, fault injection,
  long-running tests, recovery test and external review.

## Success criteria for the MVP {#mvp-criteria}

| # | Criterion |
|---|---|
| E1 | First node via USB stick; setup via portal, API or MCP – at most 15 minutes to the portal |
| E2 | New node via cable to the "waiting" state in at most 5 minutes (Raspberry Pi 4/5, x86 notebook, server) |
| E3 | Two nodes plus witness survive the failure of one node |
| E4 | Mixed cluster of ARM64 and x86_64 with matching placement |
| E5 | Two tenants fully isolated (network, compute, storage, keys); penetration test without critical findings |
| E6 | A tenant creates a VM, container instance, Kubernetes cluster, volume and bucket on their own – via all three access paths |
| E7 | Parity check 100% fulfilled – goal: no exceptions for mutating operations |
| E8 | No single point of failure from three nodes up: boot, API, portal and MCP survive a node failure |
| E9 | Evidence exportable (control matrix for BSI C5, ISO 27001, BSI IT-Grundschutz) |
| E10 | Single-node operation: one mini PC or notebook with all roles runs VMs and containers – updates with a maintenance window, external backup, grow later without reinstalling |

## Non-goals {#non-goals}

BYOC builds **no hypervisor of its own**, **no distributed file system from scratch**, and
does **not use Kubernetes as the foundation** of the platform. Proven open-source components
are integrated behind clear process boundaries. More on this in
[Vision, terminology and scope](docs/vision.html).
