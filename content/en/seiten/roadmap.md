title: Status and roadmap
summary: Where BYOC stands, in which order features are being built and how the MVP is measured.
toc: ja
de: roadmap
---
## Current status

> **Before the first release.** Version 0.x, all API groups in `v1alpha1`. Not yet suitable for
> production use. BYOC (Build Your Own Cloud) is an alpha name.

- <span class="status-ok">Completed:</span> architecture and concepts – milestone
  "Architecture in place" on 2026-11-12. License decision (AGPL-3.0-or-later for the core) on
  2026-11-12, decisions on the storage concept on 2026-11-14.
- <span class="status-run">In progress – Phase 1 "Foundation":</span> agent and control plane
  (Raft per cell, gossip, witness), resource API with REST, MCP and command line, portal,
  internal PKI, identity service, network boot and adoption, installer, OS image cpOS for amd64 and
  arm64 with A/B updates, signed release bundles, rollout controller and platform DNS.
- <span class="status-plan">Planned:</span> the further phases below – in this order, without
  fixed dates.

## Phases

The numbering follows the role catalog of the vision concept; listed are the phases to which roles and services are assigned there.

| Phase | Focus | Roles and services |
|---|---|---|
| 1 | Foundation | agent, control group (`control`), witness (`witness`), API/portal/MCP, security foundations |
| 3 | Boot and adoption | network boot service (`boot`), discovery quarantine, installation, updates |
| 4 | Identity and tenants | role `identity`, passkeys, federation, permission model, quotas |
| 5 | Network | tenant overlay, security groups, `network-gateway` with NAT, floating IPs, load balancers |
| 6 | Compute | virtual machines, container instances, managed Kubernetes |
| 7 | Storage | block volumes, S3-compatible object storage |
| 8 | Observability | metrics, logs, traces, role `observability` |
| 9 | Advanced services | databases, secrets, DNS service for tenants, queues, serverless, file storage, GPU/NPU, OpenTofu provider, AI inference |
| 10 | Federation | multiple regions and sites, global identity and API |

After the MVP come further stages such as hardware attestation as a prerequisite for permanent
auto-adopt rules, replicated block volumes once they pass a maturity gate, a topology model for
racks, and erasure coding for object and archive classes. After the MVP, the API groups move from
`v1alpha1` via `v1beta1` to `v1`.

## Quality gates

- **Phase 1 gate:** fault tolerance (two nodes plus witness, no single point of failure from three
  nodes up) is demonstrated both in a **deterministic simulation** with 10,000 random seeds without
  invariant violations and on **real hardware**.
- **Before every phase gate:** tests on real hardware (Raspberry Pi, notebooks, servers).
- **Before every minor release:** Jepsen-style consistency checks.
- **Before tenant data on replicated volumes:** maturity gate with simulation, fault injection,
  long-running tests, recovery test and external review.

## Success criteria for the MVP

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

## Non-goals

BYOC builds **no hypervisor of its own**, **no distributed file system from scratch**, and
does **not use Kubernetes as the foundation** of the platform. Proven open-source components
are integrated behind clear process boundaries. More on this in
[Vision, terminology and scope](docs/vision.html).
