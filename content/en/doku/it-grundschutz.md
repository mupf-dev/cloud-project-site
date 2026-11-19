title: BSI IT-Grundschutz modeling
summary: How BYOC models the "platform" sub-domain of the information domain from the manufacturer's perspective according to Grundschutz++, maps requirements to components and evidence, and provides operators with a protection requirements template.
group: konzept
order: 170
quelle: Concept 66 (BSI IT-Grundschutz modeling)
de: grundschutz
---

> **Note:** Technical modeling, not legal or audit advice. The modeling is a template; responsibility
> for the operator's own information domain (Informationsverbund) remains with the operator.

## Key decisions

| No. | Decision |
|---|---|
| 1 | **The target is Grundschutz++** (BSI Standard 300-1, user catalog in OSCAL format). The IT-Grundschutz Compendium 2023 (IT-Grundschutz-Kompendium) is supplied only as a *derived view* for operators who still work with it – generated, not maintained by hand. |
| 2 | What is modeled is the **"platform" sub-domain of the information domain (Teil-Informationsverbund) from the manufacturer's perspective**: 13 technical target objects, the node hardware and seven information types. The operator adopts it as a building block of its own information domain and adds location, personnel and organization. |
| 3 | There is **a single, versioned source** for the mapping requirement ↔ Grundschutz++ requirement ↔ target object ↔ responsibility ↔ evidence. All operator artifacts are **generated** from it. |
| 4 | References to Grundschutz++ requirements carry **both keys**: the human-readable ID and the stable UUID. |
| 5 | The continuously updated catalog is **pinned** and shipped with the platform; a regular update run produces a diff report for review. No build loads the catalog live from the network. |
| 6 | For assets without a matching target object category (containers, Kubernetes, KMS, distributed state) the project provides a small **supplementary catalog**. |
| 7 | A **protection requirements template** with assumptions per information type and target object, in three deployment profiles, compatible with both classic BSI IT-Grundschutz and Grundschutz++. |
| 8 | External checking tools (OSCAL validation) run only in CI as a separate process; the OSCAL files are produced by the project's own generator. |

## Who models what?

BSI IT-Grundschutz modeling is the task of the organization that runs an ISMS – that is, the **operator**. The technical part,
however, is the same for all installations, so the project, as manufacturer, does it in advance:

| Level | Who | Result |
|---|---|---|
| Manufacturer template | project | target objects of the platform, mapping to target object categories and requirements, implementation description per component (OSCAL Component Definition), protection requirements assumptions, suggested parameters |
| Operator's information domain | operator | adoption of the template, additions for sites, rooms, personnel, service providers and business processes; protection requirements, requirements package, parameters, implementation status |
| Use by tenants | tenant | for the tenant, the entire platform is **one cloud service**; it models its workloads itself |

For the operator, the components are applications, host systems and networks within its information domain; for the tenant, the platform is
a cloud service. The shared responsibility matrix connects both views (see
[Compliance requirements](compliance-requirements.html)).

### Grundschutz++ in brief

The user catalog comprises around **1,000 requirements** in 20 practices – for example asset management, permissions, detection,
configuration, architecture, development and business continuity management. Each requirement carries a security level (`normal-SdT`, i.e.
normal/state of the art, or `erhöht`, i.e. elevated), its effect on the protection goals, associated threats, target object categories and in some cases parameters that the
operator defines. Around 140 requirements carry the tag **"product description" (Produktbeschreibung)** – exactly the requirements that a
manufacturer can provide as an OSCAL component definition. They form the mandatory scope of BYOC's component
definition.

About a third of the requirements have no target object category; these are mostly ISMS and organizational requirements
that apply to the operator's entire information domain. Here the platform only provides **data sources**: implementation status from the
configuration, recorded exceptions to the secure default, evidence exports for audits, prepared reporting data for incidents, and
protection requirements labels on resources.

Because the catalog is updated continuously – roughly weekly – version pinning and referential integrity checks are
indispensable. Third-party mapping tables are never adopted without review.

## The "platform" information domain

### Scope

| Inside the domain (platform provides, operator runs) | Outside (operator or tenant models it themselves) |
|---|---|
| all technical target objects, the node hardware and the platform's information types | buildings and rooms, personnel, service providers, upstream network and firewall, tenants' guest systems and applications, operators' workstations |

The domain's **external interfaces** are: obtaining releases from the project, federation with identity providers, the operator's
SIEM, the upstream network with DHCP, DNS and NTP, offsite backup, optionally an HSM or external KMS, tenant access via
portal, API and MCP, and out-of-band management.

Build, CI and release infrastructure belong to **the project's** information domain (manufacturer under the CRA). They are modeled as well because
their evidence – SBOM, provenance, test reports – flows as input into the operator's information domain (see
[Release bundle](release-bundle.html)).

### Target objects

| Target object | Component | Target object category (Grundschutz++) | Compendium 2023 (transition) |
|---|---|---|---|
| Node hardware | servers, notebooks, Raspberry Pi, BMC, TPM, storage media | IT systems, host systems | SYS.1.1 |
| OS image | immutable A/B image with verified root (see [OS image](os-image.html)) | IT systems, host systems | SYS.1.1, SYS.1.3 |
| Agent | `cp-agent` on every node | applications | APP.6 |
| Control plane | Raft per cell, witnesses, gossip, reconcilers (see [Control plane](control-plane.html)) | applications | APP.6, CON.3 |
| Identity service | OIDC/OAuth, passkeys, permission store, Cedar (see [Identity](identity.html)) | applications, directory services, web applications | ORP.4, APP.2.1 |
| API, portal, MCP | management interfaces | web applications, web servers | APP.3.1, APP.3.2 |
| Boot service | network boot, discovery (see [Boot and adoption](boot-adoption.html)) | applications, internal network segments | NET.1.1, NET.3.4 |
| Compute | VMs, microVM containers, Kubernetes | virtualization solutions, host systems | SYS.1.5, SYS.1.6, APP.4.4 |
| Storage | block, object and file storage (see [Storage](storage.html)) | applications, data | SYS.1.8, CON.3, CON.6 |
| Network | encrypted underlay, tenant overlay, gateway, basic services (see [Network](network.html)) | networks, internal network segments, external network connections | NET.1.1, NET.3.x |
| KMS / PKI | key hierarchy, region and cell CA (see [Cryptography](cryptography.html)) | applications | CON.1 |
| Observability | metrics, logs, traces, alerting | applications | OPS.1.1.5, DER.1 |
| Audit log | chained, signed, with tenant view | applications, data | OPS.1.1.5, DER.2.2 |
| Build/CI | signing, SBOM, release channel, vulnerability reports | applications (development) | CON.8, APP.7 |

### Modeling per target object

For every target object, the essential requirements are recorded with **responsibility** and **implementation**.
Responsibility takes one of four values:

| Code | Meaning |
|---|---|
| P | platform or project implements |
| P→B | platform provides the capability and a secure default, operator (Betreiber) applies or configures it |
| B | operator (Betreiber) |
| M | tenant (Mandant) |

An example for the node hardware:

| Requirement | Responsibility | Implementation |
|---|---|---|
| Inventory of systems, detect unauthorized systems | P→B | The agent reports the hardware automatically; nodes that have not been adopted appear visibly as "waiting". |
| Cryptographic hardware storage, storage encryption | P→B | TPM use where available; disk encryption as the default; the node's trust level depends on its equipment (see [Security model](security-model.html)). |
| Authentication at the firmware | B | Operator guide; the platform reports the status where it can be read. |
| Restrict peripherals and removable media | P | USB storage drivers are disabled in the OS image. |
| Controlled deletion on decommissioning | P→B | Hardware-based erasure or crypto-shredding with evidence. |

### Supplementary catalog

For assets without a matching target object category there is a small dedicated OSCAL catalog. The requirements are worded following the
sentence template of Grundschutz++ and reference their origin in the Compendium or in C5. Examples:

- The control plane SHOULD admit only nodes with the minimum trust level of the deployment profile as voting members.
- The control plane SHOULD execute destructive actions only after quorum confirmation.
- The control plane SHOULD replicate tenant objects only to authorized nodes.
- Compute SHOULD start only signed or approved images.
- Managed Kubernetes SHOULD run a separate control plane per tenant.
- Storage SHOULD make released blocks unreadable before reuse.
- The overlay SHOULD prevent traffic between VPCs of different tenants without explicit peering.
- Adoption SHOULD be bound to a key generated on the device; network boot alone does not establish trust.
- The KMS SHOULD support tenant-owned keys and crypto-shredding.
- MCP access SHOULD treat AI agents as actors in their own right and execute destructive actions only after confirmation outside the
  AI client.

## Mapping principle: requirement → component → evidence

Every requirement in the catalog is mapped to at least one Grundschutz++ requirement, one target object, one responsibility and one
**evidence type**. The background is the rule from the requirements catalog: *A requirement counts as implemented only
when the platform delivers automatically generated evidence.*

### Evidence types

| Evidence | Content |
|---|---|
| Audit export | signed export over a time period with hash chain and verification tool |
| Inventory | hardware and software inventory including SBOM per node |
| Configuration | desired-state manifest with change history, active profile, recorded exceptions |
| Permissions | permissions and recertification report |
| Patch level | patch and vulnerability status per node |
| Backup | backup and test restore log |
| Deletion | proof of deletion (crypto-shredding, hardware-based erasure) |
| Crypto inventory | algorithms in use, key metadata, certificates |
| Network | network topology and rule set export |
| Hardening | hardening and drift report, trust level per node, attestation status |
| Release | signature, provenance, SBOM, test, isolation and penetration test reports, machine-readable advisories |
| Documentation | operator handbook, runbooks, policies |

### Examples

| Requirement | Target object | Responsibility | Implementation | Evidence |
|---|---|---|---|---|
| REQ-IAM-001 Authentication at every interface | identity, API | P | authentication everywhere, documented exceptions | configuration, documentation |
| REQ-IAM-003 MFA for admins | identity, API | P→B | MFA enforced for admins | permissions, configuration |
| REQ-IAM-004 role-based access control | identity, control plane | P | roles with Cedar policies | permissions |
| REQ-IAM-006 operator access to tenant data | identity, KMS, audit | P | technical block with access request | audit export |
| REQ-TEN-007 isolation tests | build/CI | P | isolation tests in CI | release |

## Machine-readable maintenance

The modeling is not maintained as a document but as **structured data** in the repository. The principles:

- **Single source:** target objects, mappings, implementation texts, suggested parameters and the protection requirements template live in
  versioned, machine-readable files. Tables in documents are generated from them, not the other way around.
- **Pinned catalog:** the Grundschutz++ catalog is recorded with version and checksum and shipped unchanged.
  A regular update run produces a diff (new or removed IDs, changed texts, security levels, categories)
  and flags affected mappings for review. Only after review is the new state adopted.
- **Checks in CI:** schema validation, integrity of the pin, referential integrity of every cited ID, coverage (every
  requirement has a target object and evidence; every relevant "product description" requirement has a status), reachability of the
  evidence, and consistency between the defaults in the code and the statements in the mapping (policy as code).
- **Release binding:** every platform version names the catalog state against which its statements apply.

### What operators receive with each release

Signed and part of the release evidence (see [Release signing](release-signing.html)):

| Artifact | Format | Content |
|---|---|---|
| Component definition | OSCAL Component Definition | for each target object, the implemented requirements with description, responsibility, status and evidence type |
| Proposed requirements package | OSCAL Profile | selection of requirements per deployment profile, suggested parameters |
| Shared responsibility matrix | table | basis for complementary customer controls under C5 |
| Compendium view | table | target object → module → Grundschutz++ → implementation, marked as derived |
| Protection requirements template | template | for import into ISMS tools |

Later, the platform API will additionally provide the **actual state** of the installation – active deployment and crypto profile,
parameter values, recorded exceptions – as an OSCAL fragment, equally via API, portal and MCP.

## Protection requirements assumptions as a template

The template connects both methods: the classic one (BSI 200-2) with the categories *normal*, *high* and *very high* per protection goal,
and Grundschutz++ via the security level of the requirements. The bridge: *normal* → only `normal-SdT`; *high* → additionally the
`erhöht` requirements of the affected target objects plus a risk assessment; *very high* → additionally an individual risk analysis.
All values are **manufacturer assumptions** that the operator confirms or changes based on its business processes.

### Information types

| Information type | Examples | Confidentiality | Integrity | Availability |
|---|---|---|---|---|
| Key material | root and KEK keys, CA keys | very high | very high | high |
| Platform state | Raft log, permissions, policies, placement | high | very high | high |
| Identity data | accounts, passkeys, sessions | high | very high | high |
| Audit log | audit events, traces of access requests | high | very high | normal |
| Operational logs | system and network logs, traces | normal to high | high | normal |
| Tenant data | volumes, objects, VM memory | determined by the tenant, assumed at least high | high | high |
| Artifacts | OS images, agent binaries, guest images, SBOM | normal | very high | high |

A tampered image would compromise all nodes – that is why the integrity of artifacts is *very high*. For
tenant data the platform makes no assumption below *high* as long as the tenant specifies nothing.

### Inheritance to target objects

Following the maximum principle, target objects inherit the protection requirements of the information they process. Even in the
standard profile this results in a **risk assessment** and a selection of `erhöht` requirements for the KMS, control plane, identity service, audit log, boot service and OS image. The project provides a prepared
risk assessment for this as part of the [threat model](threat-model.html).

### Deployment profiles

| Profile | Target group | Assumption | Additionally active (selection) |
|---|---|---|---|
| `homelab` | private, lab | everything *normal*, integrity of keys and artifacts *high* | quarantine of new nodes, staged rollout, encryption of data at rest – because possible without extra effort |
| `standard-c5` | hosting providers, companies | assumptions as above | just-in-time administration, key splitting, non-repudiation, automatic configuration management, secure boot (where the hardware supports it), higher minimum trust levels for critical roles |
| `erhoeht` (elevated) | public authorities, critical infrastructure (KRITIS) | tenant data *very high* | dedicated hardware, no overcommitment, physical segmentation, geo-redundancy, HSM instead of key splitting |

The crypto profile (`bsi-strict` or `compatible`) is chosen independently; `standard-c5` and `erhoeht` are permitted only with
`bsi-strict`. Protection requirements labels on resources are mapped to data classes and minimum trust levels for
placement – *high*, for example, to nodes with a TPM, *very high* to attested nodes or dedicated hosts.

### What the operator does with the template

1. Define the scope and business processes.
2. Confirm or adjust the information types; determine the protection requirements of tenant data together with the tenants or via labels.
3. Choose a deployment profile and import the profile export into the ISMS tool.
4. Review the parameters.
5. Model its own parts (buildings, personnel, service providers, upstream network) and complete the risk assessment.
6. Take over the implementation status from the platform export and confirm exceptions.
