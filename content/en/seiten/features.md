title: Features
summary: Which services, roles and platform capabilities DCP provides – from the node lifecycle through networking, storage and identity to AI inference.
toc: ja
de: funktionen
---
## Services like a hyperscaler

The platform offers core services modeled on the well-known public clouds. All services are
resources of the same API and can therefore be used equally through the portal, the API and MCP.

| Category | Service | Roughly equivalent to |
|---|---|---|
| Compute | Virtual machines (Cloud Hypervisor/KVM) | AWS EC2 · Azure VMs · Compute Engine |
| Compute | Container Instances (MicroVM-isolated) | Fargate · Azure Container Instances · Cloud Run |
| Compute | Managed Kubernetes | EKS · AKS · GKE |
| Storage | Block volumes | EBS · Managed Disks · Persistent Disk |
| Storage | Object storage (S3-compatible) | S3 · Blob Storage · Cloud Storage |
| Storage | File storage (NFS) | EFS · Azure Files · Filestore |
| Network | VPCs, subnets, security groups, load balancers, floating IPs | VPC · VNet · VPC |
| Network | Platform DNS with DNSSEC | Route 53 · Azure DNS · Cloud DNS |
| Identity | Tenants, projects, users, roles, service accounts, API keys | IAM · Entra ID · Cloud IAM |
| Platform | Registry, key management (KMS), monitoring, audit log | ECR · Key Vault · CloudWatch · CloudTrail |
| AI | Model catalog, inference endpoints, AI gateway, vector search | Bedrock · Azure AI Foundry · Vertex AI |

Further services – databases, secrets, queues, serverless functions, GPU/NPU pools – will follow
in later phases. A detailed comparison with AWS, Azure and Google Cloud is available in the
[hyperscaler feature analysis](docs/hyperscaler-analysis.html).

## Three equivalent access paths

Every feature is available through the **REST API (OpenAPI)**, the **web portal** and **MCP** (Model
Context Protocol, for AI assistants and agents) – at every level: platform, tenant, project, resource.
The portal and the MCP tools are derived from the same API schema; a CI check prevents any access
path from gaining features the others lack. In addition there is the command-line tool `cpctl`.
Details: [API-first principle](docs/api-first.html).

```yaml
# Example resource (simplified)
apiVersion: compute.cloud-project.io/v1
kind: VirtualMachine
metadata:
  name: web-01
  parent: cp:global:tenant/acme/project/shop
  labels: { env: prod }
spec:                       # desired state
  machineType: small-2c-4g
  arch: any                 # arm64 | x86_64 | any
  image: cp:global:image/debian-13
  network: { vpc: default, subnet: web }
status:                     # actual state, written only by the system
  phase: Running
```

## Roles

Every node runs the agent `cp-agent`. It takes on additional tasks through **roles**, which are
assigned manually, by rule (for example "all nodes with at least two disks → `storage-block`") or
on the scheduler's recommendation.

| Role | Task |
|---|---|
| `agent` | implicit on every node: lifecycle, local API, portal and MCP, forwarding |
| `control` | control group (Raft) of a cell |
| `witness` | quorum vote only, e.g. on a small Raspberry Pi |
| `boot` | network boot service: proxyDHCP, TFTP/HTTP boot, image cache |
| `dns` | platform DNS: authoritative zones, DNSSEC, virtual IPs |
| `identity` | OIDC/OAuth authorization server, users, tenants, federation |
| `kms` | key management, tenant keys |
| `network-gateway` | north-south traffic, NAT, load balancers, floating IPs |
| `compute-vm` | virtual machines |
| `compute-container` | Container Instances in MicroVMs |
| `kubernetes` | Managed Kubernetes for tenants |
| `storage-block` | block volumes |
| `storage-object` | S3-compatible object storage |
| `observability` | metrics, logs, traces |

## Node lifecycle

A node goes through a clearly defined lifecycle. Unknown hardware **never automatically** gets
access to tenant data – only adoption assigns it an identity.

::: html
<figure class="diagram" role="group" aria-labelledby="lz-cap">
<svg viewBox="0 0 860 330" role="img" aria-labelledby="lz-t lz-d">
<title id="lz-t">State diagram of the node lifecycle</title>
<desc id="lz-d">Discovered, Inventoried, Pending, Adopted, Provisioned, Active. From Active to Maintenance and back, to Degraded and back through self-healing. From any adopted state to Quarantine. From Maintenance or Quarantine to Decommissioned. Pending can also be Rejected.</desc>
<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="arrowhead" d="M0,0 L10,5 L0,10 z"/></marker></defs>
<rect class="box" x="10" y="40" width="110" height="44" rx="8"/><text x="65" y="67" text-anchor="middle">Discovered</text>
<rect class="box" x="150" y="40" width="130" height="44" rx="8"/><text x="215" y="67" text-anchor="middle">Inventoried</text>
<rect class="box4" x="310" y="40" width="110" height="44" rx="8"/><text x="365" y="67" text-anchor="middle">Pending</text>
<rect class="box2" x="450" y="40" width="110" height="44" rx="8"/><text x="505" y="67" text-anchor="middle">Adopted</text>
<rect class="box2" x="590" y="40" width="140" height="44" rx="8"/><text x="660" y="67" text-anchor="middle">Provisioned</text>
<rect class="box3" x="590" y="150" width="140" height="44" rx="8"/><text x="660" y="177" text-anchor="middle" class="b">Active</text>
<rect class="box" x="760" y="150" width="90" height="44" rx="8"/><text x="805" y="177" text-anchor="middle">Maintenance</text>
<rect class="box" x="450" y="150" width="110" height="44" rx="8"/><text x="505" y="177" text-anchor="middle">Degraded</text>
<rect class="box4" x="590" y="260" width="140" height="44" rx="8"/><text x="660" y="287" text-anchor="middle">Quarantine</text>
<rect class="box" x="760" y="260" width="90" height="44" rx="8"/><text x="805" y="287" text-anchor="middle" class="s">Decommissioned</text>
<rect class="box" x="310" y="150" width="110" height="44" rx="8"/><text x="365" y="177" text-anchor="middle">Rejected</text>
<path class="ln" d="M120 62 H148" marker-end="url(#ah)"/>
<path class="ln" d="M280 62 H308" marker-end="url(#ah)"/>
<path class="ln" d="M420 62 H448" marker-end="url(#ah)"/><text x="434" y="32" text-anchor="middle" class="s">Approval</text>
<path class="ln dash" d="M215 40 V20 H505 V38" marker-end="url(#ah)"/><text x="360" y="15" text-anchor="middle" class="s">Auto-adopt rule</text>
<path class="ln" d="M560 62 H588" marker-end="url(#ah)"/>
<path class="ln" d="M660 84 V148" marker-end="url(#ah)"/><text x="666" y="122" class="s">Roles assigned, healthy</text>
<path class="ln" d="M730 165 H758" marker-end="url(#ah)"/><path class="ln" d="M758 182 H732" marker-end="url(#ah)"/>
<path class="ln" d="M590 165 H562" marker-end="url(#ah)"/><path class="ln" d="M562 182 H588" marker-end="url(#ah)"/><text x="575" y="212" text-anchor="middle" class="s">Self-healing</text>
<path class="ln" d="M365 84 V148" marker-end="url(#ah)"/><text x="371" y="122" class="s">Rejection</text>
<path class="ln" d="M660 194 V258" marker-end="url(#ah)"/><text x="666" y="232" class="s">Integrity in doubt</text>
<path class="ln dash" d="M505 194 V282 H588" marker-end="url(#ah)"/>
<path class="ln" d="M730 282 H758" marker-end="url(#ah)"/>
<path class="ln" d="M805 194 V258" marker-end="url(#ah)"/><text x="811" y="232" class="s">Drain</text>
</svg>
<figcaption id="lz-cap">Node lifecycle (simplified). Quarantine can be reached from any adopted state; returning requires fresh attestation and human approval.</figcaption>
</figure>
:::

- **Discover:** A new node boots over the network (PXE/HTTP boot, Raspberry Pi network boot) or from
  a USB stick into an in-memory discovery system. It writes nothing to disks and reports a
  hardware profile.
- **Adopt:** Approval via portal, API or MCP – protected by a confirmation code and, at higher
  expansion stages, additionally by TPM attestation. The node's private key never leaves the node.
- **Provision:** Installation of the signed OS image (or diskless operation), issuance of the node
  certificate, admission to the underlay network and gossip.
- **Operate:** Assign roles, maintenance with drain, self-healing on faults.
- **Retire:** Verifiable erasure, revocation of the certificate, rotation of the gossip keys –
  with proof of erasure for compliance.

More: [Boot and adoption](docs/boot-adoption.html).

## Updates and releases

- **Immutable OS image (cpOS):** `/usr` is read-only and protected by dm-verity, `/` is ephemeral,
  state lives in an encrypted partition.
- **A/B updates with automatic rollback:** The update is written to the inactive slot. The new
  version only takes effect once a **health gate** reports green after the reboot; otherwise the
  node falls back to the old slot on its own after a few attempts.
- **Signed release bundles:** Images, extensions and the agent are delivered as a bundle with a
  manifest, checksums, SBOM and signatures; update metadata follows the principles of TUF
  (The Update Framework) with offline root keys.
- **Rollout controller:** Updates roll out in waves with a canary stage, maintenance windows and
  `maxUnavailable`. At most one voter per cell is updated at a time, the leader last.
  If a gate fails, the rollout stops.

More: [OS image](docs/os-image.html) · [Rollout](docs/rollout.html) ·
[Release bundle](docs/release-bundle.html) · [Release signing](docs/release-signing.html).

## Platform DNS

The `dns` role (service `cp-dnsd`) answers authoritatively for the names of the platform and the
tenants, signs zones with **DNSSEC**, assigns **virtual IP addresses (VIPs)** for platform services
such as the portal and the API, and protects itself against abuse with rate limiting.
Within tenant networks, every host answers DNS, DHCP and metadata locally – with no central
service in the data path. More: [Platform DNS](docs/dns.html).

## Identity and tenants

- Hierarchy **platform → tenant → project → resource**, optionally with folders inside a tenant.
- A dedicated, lean **OIDC/OAuth 2.1 authorization server** with **passkeys first** and federation
  with existing identity providers (OIDC/SAML).
- Short-lived, sender-constrained tokens that are verified locally on every node. Authorization via
  a Zanzibar-style relationship store plus **Cedar** policies for conditions and guardrails.
- Strict separation between operator and tenant content: operators see metadata; content only
  through a justified, time-limited and logged access request.
- AI agents are a separate actor type; they act with the intersection of user permissions,
  token scope and agent guardrails.
- Tenant deletion with **crypto-shredding** and a signed proof of deletion.

More: [Tenants, identity and permissions](docs/identity.html).

## Storage

- **Block volumes** over a dedicated Rust data path: local (dm-thin + dm-crypt) and replicated
  (two to three copies) – the same path from 2 to thousands of nodes.
- Metadata in the cell's existing Raft group; user data never goes through consensus.
- **Tenant encryption on the compute node:** storage nodes only see ciphertext.
- **Object storage**, S3-compatible, behind a dedicated S3 front end with permission checks and quotas.
- **File storage** via NFS on replicated volumes, in the network of the respective VPC.
- Placement across failure domains; a maturity gate before replicated volumes are used for tenant data.

More: [Storage concept](docs/storage.html).

## Network

- **Underlay:** one WireGuard interface per node, IPv6-only inside; peers come exclusively from the
  replicated state. Additionally, a pre-shared key from a post-quantum scheme.
- **Tenant overlay `cp-vnet`:** its own control logic in the agent, Linux kernel data path (VRF per
  VPC, VXLAN inside the WireGuard tunnel, nftables) – no second consensus database.
- **Security groups** are stateful, with inbound traffic blocked by default.
- **North-south traffic** via the `network-gateway` role: NAT, floating IPs, L4 load balancers;
  advertised via Layer 2 in a homelab and via BGP in a data center.
- Three expansion stages: `flat` (a single LAN), `vlan`, `routed` (L3 to the host).

More: [Network architecture](docs/network.html).

## Security and compliance

- **Chain of trust** from Secure Boot with the installation's own keys through Measured Boot and
  TPM-bound disk encryption to mTLS between all services.
- **Node identity** with short-lived certificates from an internal PKI, trust levels T0–T4,
  remote attestation.
- **Cryptography according to BSI TR-02102**, crypto agility and a roadmap for post-quantum schemes.
- **Complete audit trail** of every change, break-glass procedure with logging.
- **Compliance by design:** 36 architecture guidelines, a requirements catalog drawn from ISO 27001,
  BSI IT-Grundschutz, BSI C5, GDPR, NIS2 and the Cyber Resilience Act; evidence becomes exportable.
- **Supply chain:** reproducible builds, an SBOM per artifact, signed releases, VEX for
  vulnerability assessments.

More: [Security model](docs/security-model.html) ·
[Cryptography](docs/cryptography.html) · [Compliance by design](docs/compliance-by-design.html).

## AI-native platform

- A dedicated API group for **models, model versions, inference endpoints, AI gateways, budgets,
  guardrails, vector indexes** and knowledge bases.
- Inference engines (llama.cpp first, then vLLM) run as signed containers behind a unified
  adapter; dedicated endpoints run in MicroVMs with a passed-through accelerator.
- Two operating models: **dedicated** per tenant or **shared/serverless** with per-token billing –
  without a cross-tenant cache.
- Accelerators (GPU, NPU) as a scheduler resource, scale-to-zero with a local model cache,
  models as signed OCI artifacts with a cache per cell.
- The platform itself can be controlled via **MCP**; tenants' agents use platform tools with
  restricted permissions.
- AI compliance as a cross-cutting concern: model cards, provenance, labeling, logging under the
  EU AI Act, mapping to BSI AIC4.

More: [AI-native platform](docs/ai-platform.html).
