title: Compliance requirements
summary: Which regulatory frameworks apply to DCP, how the requirements catalog is structured, how obligations are split between platform, operator and tenant, and which precedence rules apply in case of conflicts.
group: konzept
order: 160
quelle: Concept 65 (analysis of regulatory frameworks and requirements catalog)
de: compliance-anforderungen
---

> **Note:** This page presents a technical requirements analysis and is not legal advice. Research status:
> November 2026. Binding use requires checking against the original documents.

## Key points

1. **It is the operator that gets certified or attested, not the software.** The platform must enable operators to implement controls
   effectively and provide evidence for them. To that end it delivers technical functions, secure defaults, a
   shared responsibility matrix and exportable evidence.
2. **The software itself is subject to the EU Cyber Resilience Act (CRA)** – for anyone who places it on the market in the course of a
   commercial activity. Reporting obligations have applied since 2026-09-11, all other obligations from 2027-12-11. Parts of the platform
   (OS image, identity management, hypervisor and container runtime) are expected to fall under "important products".
3. **BSI C5:2026** has been published – with 168 basic criteria in 17 areas and new focus topics such as container management,
   supply chain/SBOM, post-quantum cryptography and confidential computing. It becomes mandatory for audits from mid-2027.
4. **Grundschutz++** has been published as BSI Standard 300-1 since 2026-10-26. The user catalog with around 1,000
   requirements is available in machine-readable OSCAL format. Classic BSI IT-Grundschutz remains usable for a transition period of
   several years.
5. **NIS2 has applied in Germany since 2025-12-06.** Cloud providers and data center operators are among the NIS2 sectors;
   for them, an EU implementing regulation specifies the technical measures.
6. **Lead catalog:** ISO/IEC 27001 Annex A provides the structure, BSI C5:2026 is the benchmark for content, Grundschutz++ the
   machine-readable source of detail. In case of conflict the stricter requirement applies – as long as it remains configurable for all
   deployment sizes from homelab to data center.

## Overview of regulatory frameworks

Relevance is assessed separately: for the **software** (the project as manufacturer) and for the **operator**.

### International standards

| Framework | Software | Operator | Significance |
|---|---|---|---|
| ISO/IEC 27001:2022 | medium | high | ISMS framework with 93 controls in Annex A; provides the structure of the catalog |
| ISO/IEC 27002:2022 | high | high | implementation guidance for the controls |
| ISO/IEC 27017:2026 | high | high | cloud controls for providers and customers: tenant isolation, VM hardening, return of customer assets |
| ISO/IEC 27018:2025 | medium | high | protection of personal data in public clouds |
| ISO/IEC 27701:2025 | low | high | standalone privacy information management system |
| ISO 22301 | low | high | business continuity; the platform provides building blocks such as backup and recovery |
| ISO/IEC 20000-1 | low | medium | IT service management |

### BSI

| Framework | Software | Operator | Significance |
|---|---|---|---|
| BSI C5:2026 | high | high | audit criteria for cloud providers; the platform's benchmark for content |
| BSI C3A | medium | medium | sovereignty criteria (data location, key sovereignty) without regulatory effect – a selling point for public authorities and sovereign hosting providers |
| IT-Grundschutz Compendium 2023 (IT-Grundschutz-Kompendium) | medium | high | modules such as virtualization, containerization, Kubernetes, cryptography concept |
| Grundschutz++ (Standard 300-1) | high | high | process-oriented methodology, machine-readable user catalog |
| BSI Standards 200-1 to 200-4 | low | high | classic methodology, business continuity management |
| BSI TR-02102 | high | medium | cryptographic mechanisms including hybrid post-quantum schemes; authoritative for the choice of cryptography (see [Cryptography](cryptography.html)) |
| BSI TR-03183 | high | low | cyber resilience requirements for manufacturers, especially SBOM |
| BSI minimum standards (BSI-Mindeststandards) | medium | medium | for federal institutions; orientation for defaults |

### EU and German law

| Framework | Software | Operator | Significance |
|---|---|---|---|
| Cyber Resilience Act | high | low | product obligations, vulnerability handling, reporting obligations (24 h / 72 h) |
| NIS2 with implementing regulation | low | high | risk management measures for cloud and data center operators |
| NIS2 Implementation Act (amended BSI Act, BSIG) | low | high | risk management, reporting obligations, registration, management liability |
| GDPR (DSGVO) | medium | high | privacy by design/default, data processing on behalf, technical and organizational measures, deletion, transfers to third countries |
| EUCS | low | low | not adopted; C5 conformity is considered a good anticipation |
| Sovereignty criteria (C3A, Sovereign Cloud Stack, public administration cloud) | medium | medium | adopted as a design principle: fully self-operable, no telemetry to third parties, key sovereignty with the tenant, controllable data location |

## Structure of the requirements catalog

Every requirement has a stable ID of the form `REQ-<Block>-<Nr>`, a wording as a requirement on the platform, its
sources (ISO, C5, BSI IT-Grundschutz, Grundschutz++, CRA, NIS2, GDPR, technical guidelines), a priority and the affected
components.

**Priorities:** **MVP** = met with the first working version · **P2** = before the first production deployment in a
data center · **P3** = later or optional.

**Components:** agent, control plane, identity, API/portal/MCP, boot, OS image, compute, storage, network, KMS,
observability, audit log, build/CI.

### The blocks

| Block | Topic | Count |
|---|---|---|
| IAM | Identity and access | 11 |
| TEN | Tenant isolation | 7 |
| CRY | Cryptography and keys | 8 |
| LOG | Logging and monitoring | 8 |
| VUL | Vulnerability and patch management | 9 |
| SDL | Secure development and supply chain | 11 |
| BCM | Backup and business continuity | 6 |
| DEL | Deletion and data protection | 7 |
| NET | Network security | 8 |
| HRD | Hardening | 6 |
| AST | Asset and configuration management | 7 |
| PHY | Physical aspects (mostly an operator obligation) | 4 |
| DOC | Documentation and evidence | 8 |

### Examples

| ID | Requirement (abridged) | Prio |
|---|---|---|
| REQ-IAM-001 | Every action on the API, portal and MCP requires an authenticated identity; no anonymous management functions. | MVP |
| REQ-IAM-002 | Local accounts with passkey as the default, OIDC federation optional per tenant, SAML later. | MVP |
| REQ-IAM-003 | Multi-factor authentication can be enforced for operators and admins (default: on), phishing-resistant factors. | MVP |
| REQ-IAM-006 | Operator access to tenant data is technically blocked; only possible via a logged approval process visible to the tenant. | MVP / P2 |
| REQ-IAM-011 | Destructive and privileged actions via MCP are confirmed with a passkey outside the AI client; the confirmation token is bound to all parameters and single-use. | MVP |
| REQ-TEN-001 | End-to-end tenant isolation at the control, compute, network, storage and key layers; the tenant ID is checked in every authorization decision. | MVP |
| REQ-TEN-002 | Tenant workloads run in VMs or microVM-isolated containers – no shared kernel between tenants. | MVP |
| REQ-TEN-007 | Automated isolation tests in CI and before every release, plus penetration tests against tenant boundaries. | MVP |
| REQ-CRY-002 | Encryption in transit everywhere: mTLS with TLS 1.3 between all services, encrypted underlay. | MVP |
| REQ-CRY-004 | KMS with key hierarchy (root → tenant KEK → data DEK), rotation, versioning and purpose binding. | MVP |
| REQ-CRY-006 | Crypto agility and post-quantum readiness with hybrid key agreement. | MVP / P2 |
| REQ-LOG-001 | Audit log of every state-changing operation – identical for API, portal and MCP: who, what, when, where, result. | MVP |
| REQ-LOG-002 | Audit log is append-only, cryptographically chained and signed. | MVP |
| REQ-VUL-002 | CRA reporting process for actively exploited vulnerabilities: early warning within 24 h, notification within 72 h. | MVP |
| REQ-VUL-005 | Automatic node updates via A/B image with staged rollout, health gates and automatic rollback. | MVP |
| REQ-SDL-003 | SBOM in CycloneDX or SPDX for every release and every OS image. | MVP |
| REQ-SDL-004 | Signed builds (MVP), reproducible and with provenance attestation per SLSA Level 3 (P2). | MVP / P2 |
| REQ-SDL-009 | Security by default: no default passwords, minimal open ports, protective functions active out of the box. | MVP |
| REQ-BCM-004 | High availability without a single point of failure from three nodes upward. | MVP |
| REQ-DEL-001 | Verifiable deletion of tenant data via crypto-shredding, with proof of deletion. | MVP / P2 |
| REQ-DEL-006 | Privacy by default: no telemetry to the project or third parties without explicit opt-in. | MVP |
| REQ-NET-002 | Discovery quarantine: unknown hardware is isolated at the network or cryptographic level until it has been adopted. | MVP |
| REQ-HRD-001 | Hardened, immutable OS image with a read-only, verified root file system. | MVP |
| REQ-AST-001 | Automatic hardware inventory per node. | MVP |
| REQ-DOC-003 | OSCAL component definition of the platform per release, so operators can import it directly into their ISMS. | P2 |
| REQ-DOC-004 | Compliance CI: automated checking of secure defaults against the control matrix. | P2 |

Further reading: [Security model](security-model.html), [Boot and adoption](boot-adoption.html),
[OS image](os-image.html), [Vulnerability management](vulnerability-management.html).

## Shared responsibility

**Principle:** The platform provides capabilities, secure defaults and evidence data. The operator applies them,
organizes, decides and is accountable for the ISMS. The tenant is responsible for its workloads and data. The attestation or certificate
is always issued to the operator.

| Topic | Platform | Operator | Tenant |
|---|---|---|---|
| ISMS, risk management | templates, control matrix, BSI IT-Grundschutz modeling | **responsible** | own ISMS for its usage |
| Identity and access | IAM functions, MFA, roles, logging, recertification report | IdP integration, role assignment, recertification | own users and roles |
| Tenant isolation | **responsible** for technical isolation and its testing | correct configuration, own penetration test | – |
| Cryptography | implementation, KMS, post-quantum agility, secure defaults | choose crypto profile, safeguard root keys, key ceremony | optionally own keys (BYOK/HYOK) |
| Logging | generation, integrity, export, SIEM interfaces | SIEM operation, analysis, retention, notifications | analysis of own audit trails |
| Vulnerabilities and patches | product vulnerability management under the CRA: reporting channels, advisories, updates, SBOM | apply updates promptly, provide evidence of patch level | patch guest systems, images, applications |
| Secure development, supply chain | **responsible** | supplier assessment, own extensions | own software |
| Backup, business continuity | backup, restore and replication functions, high availability, runbooks | backup concept, offsite copy, restore tests, emergency manual | backups of own data |
| Deletion, data protection | crypto-shredding, proofs of deletion, export, data location | data processing agreements, records of processing, deletion concept, media destruction | legal basis, deletion requests |
| Network security | segmentation, default deny, discovery quarantine | physical connectivity, perimeter, upstream DDoS protection | security groups, VPC design |
| Hardening | hardened image, Secure Boot, drift detection | hardware and firmware selection, BMC hardening | hardening of guest systems |
| Physical security, personnel | failure domain model, disk encryption | **responsible** | – |
| Documentation, evidence | control matrix, OSCAL component definition, evidence export, operator handbook | system description, audits | – |
| Reporting obligations | CRA (product vulnerabilities) | NIS2/BSIG (operational incidents), GDPR | GDPR as controller |

**Homelab:** Without a compliance goal the same defaults apply; operator obligations become recommendations. No
function may be secure only with data center infrastructure (HSM, SIEM, second site) – every such dependency needs
a secure fallback, for example Shamir secret sharing instead of an HSM, or local log storage instead of a SIEM.

## Lead catalog and precedence rules

### Nature of the frameworks

| | ISO/IEC 27001/27002/27017 | BSI C5:2026 | Grundschutz++ |
|---|---|---|---|
| Nature | management system with generic controls ("what") | auditable criteria for cloud providers | methodology with very detailed requirements ("how") |
| Evidence | certification, internationally widespread | attestation; partly required by law | certification based on BSI IT-Grundschutz; mandatory for federal authorities |
| Granularity | coarse | medium to fine | very fine, machine-readable |

### Lead catalog

1. **Backbone: ISO/IEC 27001 Annex A** (supplemented by 27017 for cloud). Every requirement is first mapped to an Annex A control
   – every ISMS builds on it.
2. **Benchmark for content: BSI C5:2026.** Where C5 is more specific or stricter – tenant isolation, access to customer data,
   product security, transparency, containers, post-quantum cryptography – C5 determines the acceptance criteria. Goal: an
   operator should be able to meet all technical C5 basic criteria with the platform.
3. **Source of detail and machine-readable data: Grundschutz++.** The catalog is imported directly and provides concrete check items (see
   [BSI IT-Grundschutz modeling](it-grundschutz.html)).
4. **Legal minimum:** CRA for the software, NIS2 for operators. Legal requirements are not open to trade-offs.

### Conflict rules

| Rule | Content |
|---|---|
| K1 – Law before standards | CRA, NIS2/BSIG and GDPR take precedence over any standard. |
| K2 – Stricter wins | If C5, ISO and Grundschutz++ differ, the stricter requirement applies as the platform default – provided it remains configurable. |
| K3 – Configurability instead of coercion | Where strictness makes homelab operation impossible, it is offered as a profile, with a documented secure fallback. Two axes: **deployment profile** (`homelab`, `standard-c5`, `erhoeht` – "elevated") and **crypto profile** (`bsi-strict` as default, `compatible`); the regulated deployment profiles only with `bsi-strict`. |
| K4 – Cryptography per BSI | For cryptographic questions BSI TR-02102 is authoritative; deviations are justified and documented. |
| K5 – Verifiability | A requirement counts as implemented only when the platform delivers **automatically generated evidence**. |
| K6 – Version discipline | References carry their version; new editions are assessed as a delta, transition periods determine the priority. |

There is no real precedence conflict between C5 and ISO 27001: ISO 27001 is the framework, C5:2026 the stricter,
cloud-specific refinement. How these requirements are already anchored in the architecture is described in
[Compliance by design](compliance-by-design.html).
