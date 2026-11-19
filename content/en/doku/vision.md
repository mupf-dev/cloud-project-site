title: Vision, Terminology and Scope
summary: Target picture, guiding principles, target audiences, glossary, node lifecycle, roles, scaling tiers and scope of BYOC (Build Your Own Cloud).
group: konzept
order: 10
quelle: Concept 01 (Vision, Terminology & Scope)
de: vision
---

## Target picture

**BYOC** (**BYOC** for short) is an **open-source, decentralized cloud platform**. It takes in arbitrary hardware – from a Raspberry Pi to laptops to rack servers – over a network cable and turns it into a **multi-tenant cloud with the core services of a hyperscaler**. It covers everything from a two-node homelab to a data center with thousands of nodes.

The short version for outsiders:

> *Plug in the cable – node appears – approve – assign a role – done. Everything via portal, API or MCP.*

### What "hyperscaler-like" means in concrete terms

| Category | Platform service | Roughly equivalent to |
|---|---|---|
| Compute | Virtual machines | AWS EC2, Azure VMs, GCE |
| Compute | Container Instances | Azure Container Instances, Cloud Run, Fargate |
| Compute | Managed Kubernetes | EKS, AKS, GKE |
| Storage | Block volumes | EBS, Managed Disks, Persistent Disk |
| Storage | Object storage (S3-compatible) | S3, Blob Storage, GCS |
| Network | VPCs, subnets, security groups, load balancers, floating IPs | VPC, VNet |
| Identity | Tenants, projects, users, roles, API keys | IAM, Entra ID, Cloud IAM |
| Platform | Registry, KMS, monitoring, audit log | ECR, KMS, CloudWatch, CloudTrail |

Later expansion stages add databases, secrets, DNS, queues, serverless, file storage and GPU/NPU accelerators (see [Hyperscaler analysis](hyperscaler-analysis.html) and [AI platform](ai-platform.html)).

## Guiding principles

1. **Decentralized, no central controller.** Every node runs the agent; portal, API and MCP run on the hardware they manage. If a node fails, another one takes over.
2. **API-first, three equivalent access paths.** Every function at every level is available via API, web portal and MCP – including initial setup and adoption. The API is the single source of truth (see [API-first](api-first.html)).
3. **Zero-touch after the cable.** Once plugged in, no screen, keyboard or SSH is needed. The only deliberate action is the approval (adoption) – or an auto-adopt rule. Auto-adopt is disabled by default and only permitted permanently with hardware attestation.
4. **Scales in both directions.** Two nodes are a full-fledged operating mode, not a demo. Growth to thousands of nodes happens through cells and regions, without reinstalling.
5. **Heterogeneous from day one.** ARM64 and x86_64 mixed; nodes with and without a BMC, with little and lots of RAM.
6. **Declarative and self-healing.** The desired state is described; reconcilers bring it about.
7. **Immutable nodes.** Image-based operating system with A/B updates; no manual maintenance on nodes (see [OS image](os-image.html)).
8. **Secure & compliant by design.** mTLS everywhere, tenant isolation at every layer, logging of every change, exportable evidence for ISO 27001, BSI C5 and BSI IT-Grundschutz (see [Compliance by design](compliance-by-design.html)).
9. **Open source throughout.** Only open-source dependencies; in-house components in Rust (see [Rust stack](rust-stack.html) and [License governance](license-governance.html)).
10. **Integrate what is proven, build what is missing.** No in-house hypervisor – the project builds the control plane, the automation and the unified interface.

## Target audiences and deployment scenarios

| Tier | Nodes | Typical hardware | Typical operator | Distinctive feature |
|---|---|---|---|---|
| **Homelab** | 2–10 | Pis, old laptops, mini PCs, 1–2 servers | Individual, developer | Two-node operation with witness; coexists with the router's DHCP; single site |
| **Edge / SMB** | 10–100 | Mini PCs, servers | Small company, association, school, branch office | Multiple tenants, first compliance requirements |
| **Data center** | 100–10,000+ | Rack servers with BMC | Hosting provider, public authority, enterprise IT | Cells and regions, multiple sites, operator certification (ISO 27001 / C5) |

The **MVP focuses on the homelab**. However, the architecture must not contain any decision that blocks the path to the data center.

## Terminology (glossary)

### Infrastructure

| Term | Meaning |
|---|---|
| **Platform** | All regions of one operator taken together. |
| **Node** | A physical device running the agent; the smallest unit. |
| **Agent** | Rust service on every node: lifecycle, roles, local API/portal/MCP, request forwarding. |
| **Role** | Function a node performs (e.g. `boot`, `control`, `compute-vm`). A node can have multiple roles. Roles are assigned, not installed. |
| **Control group** | Small, automatically elected set of nodes (3 or 5) with the `control` role that holds a cell's state via Raft consensus. |
| **Witness node** | Lightweight node (e.g. a Pi) that only votes, so that two-node clusters have a quorum. |
| **Cell** | Unit of failure and scaling with its own control group (guideline: up to about 500–1,000 nodes). Cells fail independently of one another. |
| **Region** | One or more cells at a site or federation sharing a network and a common region API. |
| **Site** | Physical location (homelab, data center room). Sites are connected via the WireGuard underlay. |
| **Federation** | Combination of several regions under one global identity and API (later expansion stage). |
| **Underlay** | Encrypted WireGuard mesh between nodes – the platform's transport network. |
| **Overlay / VPC** | Virtual, tenant-owned network on top of the underlay (see [Network](network.html)). |
| **Boot service** | Role `boot`: proxyDHCP, iPXE/UEFI HTTP boot, Pi netboot, image delivery. Present multiple times, never a single point of failure. |

### Organization and usage

| Term | Meaning |
|---|---|
| **Operator** | Runs the platform; manages hardware, regions and tenants. |
| **Tenant** | Organizationally and technically isolated customer with its own users, networks, keys and billing. |
| **Project** | Subdivision within a tenant; boundary for resources, quotas and permissions. |
| **Resource** | Anything managed via the API (node, VM, volume, VPC, bucket …). Every resource has a desired and an actual state. |
| **Service** | Offering to tenants (VM service, object storage …), implemented through roles on nodes. |
| **Quota** | Upper limit on resources per tenant or project. |
| **Scope** | Where an operation takes place: *platform → region → cell → node* (operator) or *tenant → project → resource*. At every level: API = portal = MCP. |

The [Identity](identity.html) page describes the tenant and permission model in detail.

## Node lifecycle

Every node goes through a fixed lifecycle that is controlled entirely via API, portal or MCP:

| State | Meaning | Transition triggered by |
|---|---|---|
| **Discovered** | Device has sent a DHCP/boot request | Plugging in the cable |
| **Inventoried** | Discovery image has booted and reported the hardware | automatic |
| **Pending** | No auto-adopt match; waiting for approval | automatic |
| **Adopted** | Approval granted or an auto-adopt rule matched | Portal / API / MCP or rule |
| **Rejected** | Approval denied | Portal / API / MCP |
| **Provisioned** | Identity and certificate issued, OS image rolled out | automatic |
| **Active** | Roles assigned and healthy | automatic |
| **Maintenance** | Drain: workloads are moved elsewhere | Operator |
| **Degraded** | Health check failed; self-healing back to "Active" | automatic |
| **Quarantine** | Integrity in doubt | automatic, from any adopted state |
| **Decommissioned** | Data securely erased, certificate revoked | Operator |

Key rules:

- **Unknown hardware never automatically gets access to tenant data.** Discovery runs in an isolated network or mode; only adoption assigns an identity (see [Boot & adoption](boot-adoption.html) and [Security model](security-model.html)).
- **Quarantine can be reached directly from any adopted state** (Provisioned, Active, Maintenance, Degraded) – not only via "Degraded". Triggers include attestation failures, anomaly findings, a mismatched hardware fingerprint or the same node identity appearing twice; in the latter case both nodes are quarantined.
- The way back from quarantine to "Active" requires **fresh attestation and human approval**.
- **Decommissioning** includes verifiable erasure (BSI CON.6, ISO 27001 A.7.14) – a compliance-relevant step.

## Role catalog (initial)

| Role | Purpose | Minimum requirement (guideline) |
|---|---|---|
| `agent` *(implicit, every node)* | Lifecycle, local API/portal/MCP, forwarding | 512 MB RAM |
| `boot` | proxyDHCP, iPXE/HTTP boot, image cache | 1 GB RAM, space for images |
| `control` | Control group (Raft) of a cell | 2 GB RAM, SSD |
| `witness` | Quorum vote only | Pi Zero 2 / Pi 3 is sufficient |
| `identity` | OIDC, users, tenants | 1 GB RAM |
| `network-gateway` | North-south traffic, load balancers, floating IPs | 2 NICs recommended |
| `compute-vm` | VMs (Cloud Hypervisor/KVM) | Virtualization extensions |
| `compute-container` | Container Instances (MicroVM-isolated) | KVM recommended |
| `kubernetes` | Managed Kubernetes control for tenants | 2 GB RAM |
| `storage-block` | Block volumes | Local disk(s) |
| `storage-object` | S3-compatible object storage | Local disk(s) |
| `observability` | Metrics, logs, traces | Disk |

Roles are assigned manually, by rule (e.g. "all nodes with at least two disks get `storage-block`") or as suggested by the platform planner – always via API, portal or MCP.

## Control plane scaling tiers

The guideline values are explained in detail on the [Control plane](control-plane.html) page.

| Nodes | Control group | Cells | Remark |
|---|---|---|---|
| 2 | 2 + witness | 1 | Witness (Pi or external micro node) mandatory for quorum |
| 3–20 | 3 | 1 | Standard homelab |
| 20 – approx. 1,000 | 5 | 1 | Gossip for membership, Raft only for state |
| > approx. 1,000 | 5 per cell | n | Region level coordinates cells; failure of a cell affects only that cell |
| multiple sites | per region | n | Federation with global identity |

## Comparison with existing solutions

| Solution | What it does well | What is missing for our goal | What we adopt |
|---|---|---|---|
| **Canonical MAAS** | Bare-metal provisioning via PXE, inventory, BMC | Central controller, no cloud services, no tenants | Discovery and commissioning flow |
| **Tinkerbell** | Workflow-based bare-metal provisioning | Centralized, provisioning only, no end-user portal | Workflow model, iPXE approaches |
| **Metal³ / Cluster API** | Bare metal via the Kubernetes API | Requires an existing K8s cluster, complex for a homelab | Declarative resource model |
| **OpenStack / Sovereign Cloud Stack** | Complete IaaS with tenants; SCS focused on sovereignty | Very complex, many central services, unsuitable for 2 Pis, no zero-touch | Service split (compute/network/volumes/identity), SCS standards as reference |
| **Apache CloudStack / OpenNebula** | Leaner IaaS with tenants | Central management, host provisioning not integrated | Tenant and billing models |
| **Proxmox VE** | Simple virtualization, clustering, Ceph | No real multi-tenancy, no zero-touch, no MCP | Usability as the benchmark for the homelab |
| **Harvester** | HCI on Kubernetes, VMs + K8s | x86 only, high minimum requirements | Combination of VM + K8s |
| **Talos / Omni** | Immutable, API-driven OS | Kubernetes nodes only, Omni is centralized | Image/A/B concept, API instead of SSH |
| **Oxide Control Plane** | Rack cloud with an open-source control plane in Rust | Tied to its own hardware | Architecture and Rust experience |
| **Kubernetes alone** | Container orchestration | No bare-metal lifecycle, no VMs/VPCs/multi-tenant cloud | Reconciler pattern |

**Unique selling point:** zero-touch hardware onboarding, decentralized control without a central controller, multi-tenant hyperscaler services, API/portal/MCP at every level, from a Pi to the data center, and compliance by design – none of the solutions listed combines all of this.

## Non-goals

- **No in-house hypervisor, no in-house database, no distributed file system from scratch** – proven components such as Cloud Hypervisor are integrated. Clarification from 2026-11-14: block and object storage based on the platform Raft and an in-house chunk layer are in-house developments (block replication using a primary-copy scheme is not a distributed file system). **Ceph is not a mandatory component**, only an optional external driver for data centers that already run Ceph (see [Storage](storage.html)).
- **No API compatibility with AWS, Azure or GCP** – the exception is the S3-compatible object storage; tooling integration is via OpenTofu/Terraform providers.
- **No network boot over Wi-Fi** – onboarding requires Ethernet (Wi-Fi nodes possibly later via a boot stick).
- **No proprietary dependencies**, not even mandatory "open core" components.
- **No Kubernetes distribution** – Kubernetes is a service of the platform, not its foundation.
- **No hardware without 64-bit support** – Pi 1, Pi 2 and Pi Zero W are excluded; a Pi Zero 2 W is only suitable as a witness via boot stick.

## MVP success criteria

| # | Criterion | Metric |
|---|---|---|
| E1 | First node running from a USB stick, setup done entirely via portal **or** API **or** MCP | ≤ 15 minutes until the portal is reachable |
| E2 | New node via cable to "pending" | ≤ 5 minutes (Pi 4/5, x86 laptop, server) |
| E3 | Two-node cluster with witness survives the failure of one node | Control remains available |
| E4 | Mixed ARM64 + x86_64 cluster | VMs and containers are placed appropriately |
| E5 | Two tenants fully isolated | Network, compute, storage, keys; penetration test without critical findings |
| E6 | Tenant creates VM, Container Instance, K8s cluster, volume and bucket on their own | via all three access paths |
| E7 | Parity check | 100 % of API operations available in portal and MCP |
| E8 | No single point of failure from 3 nodes upward | Boot service, API, portal and MCP survive a node failure |
| E9 | Evidence exportable | Control matrix for C5, ISO 27001 and IT-Grundschutz (see [IT-Grundschutz](it-grundschutz.html)) |

## Open questions at the time of the vision

Some questions were deliberately deferred to follow-up concepts: the final product name (so far a working title), the guideline for cell size and control group size ([Control plane](control-plane.html)), the overlay technology ([Network](network.html)), the basis of the OS image ([OS image](os-image.html)), the portal technology ([Portal](portal.html)) and which of C5 and ISO 27001 takes precedence in case of conflict ([Compliance requirements](compliance-requirements.html)).
