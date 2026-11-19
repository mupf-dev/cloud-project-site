title: Compliance by Design
summary: DCP's 36 verifiable architecture guidelines, the CI checks and review checklist that go with them, and the "Security & Compliance" template that every architecture decision must contain.
group: konzept
order: 180
quelle: Concept 68 (Compliance by Design)
de: compliance-by-design
---

## Why guidelines?

The [requirements catalog](compliance-requirements.html) defines **what** the platform must fulfill, the
[BSI IT-Grundschutz modeling](it-grundschutz.html) **how** this maps to Grundschutz++, the
[threat model](threat-model.html) **what** it must protect against, the [cryptography](cryptography.html) concept
**with which mechanisms**, and the [security model](security-model.html) describes the overall picture. What is still missing
are **rules that every single architecture decision must comply with** – so that compliance follows from the design instead of being
"tested in" after the fact. This corresponds to the guiding principle "compliance by design" from the [Vision](vision.html) and to the
Cyber Resilience Act's requirements for secure design.

### Key points

- There are **36 verifiable architecture guidelines** (CBD-01 to CBD-36) in nine groups. Each is a MUST rule with a source and
  at least one check type. **There is no such thing as a guideline without a check.**
- The checks are bundled into **20 named CI checks** and a **review checklist**.
- **Every future ADR or technical concept** contains a "Security & Compliance" section following a fixed template. Without it, a
  document cannot be accepted.

### Order of precedence

1. **Law** – CRA, NIS2/BSIG, GDPR; not open to trade-offs.
2. **Conflict rules and requirements catalog** (see [Compliance requirements](compliance-requirements.html)).
3. **Guidelines CBD-01 to CBD-36** (this page).
4. **ADR or technical concept** with the "Security & Compliance" section.
5. **Implementation and tests** (CI checks).
6. **Evidence**, release report, OSCAL export.

The threat model feeds into guidelines and ADRs alike. An ADR **may** fall short of a guideline –
but only with an entry in the deviation register stating rationale, compensating measures, approval and deadline. If an ADR contradicts a
guideline without such an entry, it cannot be accepted. Guidelines change only through a new version; IDs are
never reused.

### Check types

| Code | Meaning | When |
|---|---|---|
| PR | automated check, blocks the merge | every pull request |
| N | automated nightly check; a failure blocks the next release | nightly |
| R | release gate | per release |
| REV | review with checklist; security-critical paths with two reviewers | per PR or ADR |
| LAB | check in the QEMU or hardware lab | nightly or before completing a phase |
| PT | penetration test or external audit | before the MVP, per major version |
| DOC | automated check of the concept documents | every PR |

## The guidelines

### Principles and defaults

| ID | Guideline | Check |
|---|---|---|
| CBD-01 | **Secure by default.** The shipped state is the most secure setting that can be run in a homelab without additional hardware: no default credentials, no interactive login, no active auto-adoption, strict crypto profile, all security functions on. Every relaxation is an audited API action. | check of a fresh installation, REV |
| CBD-02 | **Homelab fallback.** No security function may be secure only with data center infrastructure; every such dependency has a documented secure fallback – for example key splitting instead of an HSM. | REV, DOC |
| CBD-03 | **Evidence is part of the function.** A relevant function counts as implemented only when it delivers automatically generated evidence – retrievable via API, portal and MCP. | PR |
| CBD-04 | **Privacy by default.** No telemetry or other outbound connection without opt-in; every outbound connection is configured and documented. | N, LAB |

### Identity, authorization, tenant isolation

| ID | Guideline | Check |
|---|---|---|
| CBD-05 | **No anonymous management function.** Every API operation declares the permission it requires; exceptions are kept in a versioned list and return no sensitive data. | PR, R |
| CBD-06 | **Tenant ID in every authorization decision, at the target.** Other tenants' objects yield "not found"; no other tenants' data in errors, lists, metrics or logs. Isolation is additionally enforced by technical means, not just by checking code. | generated two-tenant tests per operation |
| CBD-07 | **Trust never derives from network position or forwarding.** The target verifies the original token itself; portal sessions are exchanged at the entry point for short-lived, audience-bound tokens. | simulation |
| CBD-08 | **Tokens carry identity, not permissions;** short-lived, sender- and audience-bound, no pass-through. Long-lived secrets only hashed and with mandatory expiry. | token tests |
| CBD-09 | **Nodes are not principals for tenant operations;** roles and placement follow the trust level. Eligibility is never based on self-reporting; the level drops immediately and rises only with fresh evidence. | simulation, REV |
| CBD-10 | **Privileged actions** require step-up, a justification and – depending on the profile – the four-eyes principle; platform administration and the security role are separate. | PR |
| CBD-11 | **Operators do not see tenant content** except via an approved access request. Every field has a data class; tenant metadata appears pseudonymized in operator views. The boundary is described openly to tenants. | PR, isolation tests |
| CBD-12 | **Isolation by technical means:** no shared kernel between tenants, separate Kubernetes control planes, one VPC per project in its own VRF, inbound default deny, data keys per volume or bucket, no storage deduplication across tenants. | isolation tests, LAB, PT |

### AI agents and MCP

| ID | Guideline | Check |
|---|---|---|
| CBD-13 | **An agent is an actor in its own right with intersected permissions.** Effective permissions = principal ∩ token scopes ∩ agent guardrails; default token is read-only; principal and actor are recorded separately in the audit log. | PR, N |
| CBD-14 | **Destructive MCP actions only with confirmation outside the client** – on a platform page that displays the impact report itself and requires passkey presence. The confirmation token is bound to all parameters and single-use. | confirmation tests |
| CBD-15 | **Externally controlled data is data, not instructions.** Free-form fields filled by tenants or devices are marked as untrusted, normalized and never rendered as HTML in the portal; tool descriptions are static and signed. | PR |

How these rules apply concretely to AI services is described in [AI platform](ai-platform.html).

### Logging, data protection, evidence

| ID | Guideline | Check |
|---|---|---|
| CBD-16 | **Every API action is audited** – identically across all channels; auditing is part of the enforcement chain and cannot be switched off. | generated test per mutating operation |
| CBD-17 | **Audit log tamper-proof and anchored outside the cell:** hash chain, signature, separate chains per tenant, external anchor; revocation lists must never fall back to an older state. | tampering tests |
| CBD-18 | **No secrets in logs, traces, error messages, images or repositories.** Secrets only in types without output and with secure zeroization; images contain no secrets. | secret scanner, canary test |
| CBD-19 | **Data minimization, personal data marked:** personal data fields are labeled; retention and pseudonymization configurable per data type. | PR |
| CBD-20 | **Evidence machine-readable, signed, identical across channels**, with an OSCAL reference. | PR, R |

### Cryptography

| ID | Guideline | Check |
|---|---|---|
| CBD-21 | **Cryptography only via profiles.** No algorithm hard-coded; every ciphertext and every signature carries algorithm, key ID and version; regions may tighten, never relax. | lint |
| CBD-22 | **No homegrown cryptography:** established libraries with a single provider, kernel crypto, TPM; randomness only from the kernel. | dependency check, test vectors |
| CBD-23 | **BSI TR-02102 is authoritative;** deviations only when registered and time-limited. | handshake matrix per profile |
| CBD-24 | **Quantum-safe confidentiality from the MVP:** hybrid post-quantum key agreement on all of the project's own TLS endpoints; data at rest with AES-256. | PR, N |
| CBD-25 | **Encryption everywhere:** control traffic only mTLS within the encrypted underlay, portal and API only HTTPS with HSTS, data at rest encrypted by default. | lab check |
| CBD-26 | **Keys are created where they are used and never leave that place;** issuance via CSR, third-party processes with their own service identity, never with the node key. | lint, simulation |

### Architecture boundaries and supply chain

| ID | Guideline | Check |
|---|---|---|
| CBD-27 | **Third-party components only across process boundaries** – never linked, but run as a separate process with its own user, minimal privileges and a sandbox (see [Rust stack](rust-stack.html)). | dependency check, REV |
| CBD-28 | **Minimal, pinned, reviewed dependencies;** SBOM and provenance per artifact; signed, reproducible builds (see [Release bundle](release-bundle.html)). | PR, R |
| CBD-29 | **Least privilege:** privileged operations in exactly one helper service; parsers at trust boundaries in processes without access to node keys, with size limits and fuzzing. | fuzzing register |
| CBD-30 | **A single enforcement point:** authentication → authorization → validation → quota → audit → execution is one chain for API, portal, MCP and CLI (see [API-first](api-first.html)). | parity check |

### Nodes, boot, control plane

| ID | Guideline | Check |
|---|---|---|
| CBD-31 | **Trust arises only through adoption,** never through boot or network position. Adoption is bound to a key generated on the device; auto-adoption is off by default; critical roles are never assigned at adoption (see [Boot and adoption](boot-adoption.html)). | simulation, LAB |
| CBD-32 | **One-sided signals never trigger destructive actions.** Fencing, revocation or deletion require a quorum; security decisions fail closed, running workloads remain stable (see [Control plane](control-plane.html)). | simulation |
| CBD-33 | **Deviations are objects, not comments** – at manufacturer level in the register, at installation level as an API object, each with rationale, compensating measures, approval and deadline; both included in the compliance export. | PR |

### Deletion and recovery

| ID | Guideline | Check |
|---|---|---|
| CBD-34 | **Deletable by design.** Every new data store – including caches, snapshots, backups, logs – is attached to the key hierarchy so that crypto-shredding takes effect; proofs of deletion and decommissioning in a signed format. | integration test, REV |
| CBD-35 | **Recoverability is practiced:** encrypted platform backup, restore without a live platform, automated test restore with a log, emergency rotation per key class. | nightly recovery drill |

### Process

| ID | Guideline | Check |
|---|---|---|
| CBD-36 | **Threat model and standards references evolve along with the design.** Every ADR that changes components, roles, trust boundaries or third-party components updates the threat model in the same change set; standards references carry their version. | documentation check |

## CI checks

The guidelines are backed by 20 named, automated checks. The most important groups:

| Area | What is checked |
|---|---|
| Parity and API schema | same permissions and functions across all channels; mandatory declarations per operation (permission, effect, data class, markers for untrusted and personal data fields, step-up) |
| Tenant isolation | two-tenant tests per operation generated from the API description, analysis of the authorization policies |
| Audit | completeness of the audit entry per mutating operation |
| Secrets | scanner, deny rules, canary run, image scan |
| Dependencies | licenses, deny lists, sources, advisories, lockfiles |
| Cryptography | lint, handshake matrix per profile, share of hybrid key agreement, HSTS |
| Release | SBOM, signature, provenance, update metadata, rebuild |
| Compliance mapping | coverage, catalog pin, deviation register, OSCAL validation |
| Defaults | policy-as-code check of a fresh installation |
| Simulation | control plane invariants: node authorization, no destructive gossip signals, minimum levels, quarantine, no private key in the state |
| Robustness | fuzzing register with nightly run, rules for `unsafe` |
| Documentation | mandatory "Security & Compliance" section, existence of cited IDs |
| Agents | confirmation and step-up tests |
| Data protection | egress capture of an unconfigured installation |
| Portal | Content Security Policy without inline scripts |
| Deletion, recovery | crypto-shredding with no key remnants; test restore of a test cell |

The guidelines themselves are also maintained as structured data; a check ensures that every automatically
checked guideline references an existing CI check.

## Review checklist

For every pull request with a security-relevant change:

1. New or changed operation: are permission, effect, data class, step-up and confirmation requirement declared?
2. Tenant scope: check at the target, no other tenants' data in errors, lists or metrics?
3. New input across a trust boundary: sandbox process, limits, fuzzing target, marked as untrusted?
4. Secrets: only in the protected type, no logs, distribution only as needed and subject to the minimum level?
5. Cryptography: only via a profile and the central crypto library, format version, entry in the crypto inventory?
6. Third-party component: process boundary, license, allowlist, sandbox, SBOM?
7. Role or placement: minimum trust level correct, downgrade handled?
8. New storage location: in the key hierarchy, with deletion path and retention?
9. Default secure, homelab fallback present, relaxation only as a deviation object?
10. Threat model and compliance mapping updated in the same PR?

Security-critical paths – PKI, consensus, authorization, identity, boot and discovery, update, cryptography, KMS, audit,
MCP confirmation, attestation – require two reviewers.

## ADR template "Security & Compliance"

Every new ADR and technical concept contains a "Security & Compliance" section with eleven subsections. A **short form**
(only S3, S4 and S9 plus the rationale "no new attack surface") is allowed if no new component, role,
trust boundary, third-party component, data type or storage location is introduced.

| Section | Content |
|---|---|
| S1 Assets and data classes | assets to be protected with information type, data class, protection requirements (confidentiality, integrity, availability) and location |
| S2 Trust boundaries and threats | affected or new trust boundaries, data flows, threats with rating before and after measures, test ID; parsers and fuzzing targets; minimum trust level of new roles |
| S3 Guideline conformance | for each guideline CBD-01 to CBD-36: met by which section, not applicable (with reason) or deviation (with register ID) |
| S4 Requirements mapping | affected requirements with degree of fulfillment and priority; candidate new requirements |
| S5 Standards references | Grundschutz++ requirements with ID and UUID, target object, other standards (C5, ISO, CRA, TR-02102) |
| S6 Shared responsibility | per function: responsibility, default per deployment profile, operator and tenant tasks, homelab fallback |
| S7 Cryptography | new entries in the crypto inventory and their effect per crypto profile; key lifecycle |
| S8 Third-party components and supply chain | version, source, license, boundary, sandbox, service identity, SBOM, signature |
| S9 Evidence | what is evidenced, evidence type, API operation, automated test, inclusion in the compliance export |
| S10 Data protection, retention, deletion | personal data fields, purpose, retention; new storage locations and deletion path |
| S11 Open security questions | open questions with an owner responsible for resolving them |

### Definition of Done for ADRs

| No. | Criterion |
|---|---|
| D1 | "Security & Compliance" section complete, or a justified short form |
| D2 | All guidelines assessed in S3; every deviation has a register ID |
| D3 | Every new threat has a measure with a test ID or an explicitly accepted residual risk; a remaining "high" blocks the release |
| D4 | Every requirement named in S4 exists; priority deviations are formulated as a change request |
| D5 | Shared responsibility with a homelab fallback per function |
| D6 | Open decisions explicitly marked, not preempted |
| D7 | Contradictions with adopted documents named as a change proposal, not silently overridden |

## Maintenance

- **Responsibility:** a "project compliance officer" role, also responsible for the catalog diff of the
  BSI IT-Grundschutz modeling.
- **Triggers for a revision:** a new version of the requirements catalog, new editions of regulatory frameworks (such as C5:2026, TR-02102,
  harmonized CRA standards), findings from penetration tests and audits, repeated deviations from the same guideline – but at least
  before every minor release, together with the threat model.
- **Change process:** new version with change history; IDs are never reused.
