title: Security Model
summary: Whom the platform trusts, for what, how that trust is proven and what happens when trust is lost – from trust anchors through node trust levels and remote attestation to break-glass and compromise.
group: konzept
order: 90
quelle: Concept 10 (security model)
de: sicherheitsmodell
---

The security model defines **whom** the platform trusts, **for what**, **how this is proven** and **what happens when trust is lost**. Algorithms, key lengths, lifetimes and the PKI hierarchy are covered in the [cryptography concept](cryptography.html); boot paths and the adoption flow in [Boot and adoption](boot-adoption.html). The attacker models come from the [threat model](threat-model.html).

## Key decisions

- **Two separate axes:** the *adoption evidence* describes how certain it is that exactly this device was meant (confirmation code, enrollment token, pre-registration, attestation). The *trust level* describes how well the integrity of the running node is proven with hardware backing. Placement and roles depend **only** on the trust level.
- **Five trust levels T0–T4**, computed rather than claimed: the level drops immediately and rises only after fresh evidence.
- **Levels are placement and role conditions:** control group, key management (KMS), identity service and certificate signing require minimum levels depending on the operating profile.
- **Remote attestation** via TPM quote against signed reference values from the release manifest.
- **Quarantine is a hard, technically enforced state** – not a label.
- **One identity per process boundary:** third-party processes receive their own locally generated service identities, never the node key.
- **Workload identity strictly separated** from the infrastructure, with node-bound issuers.
- **Secrets only on a need-to-have basis and by level**, exclusively encrypted to the node key and only in memory.
- **Operator access via the API**; interactive access only time-limited, justified and recorded.
- **Compromise as a runbook operation** with immediate revocation and targeted rotation.

## Trust anchors

Trust in the platform comes from exactly two sources: from **signatures** that chain back to a defined trust anchor, and from the **authoritative state** of the control plane (Raft, see [Control plane](control-plane.html)).

| Anchor | Held by | Trusted for |
|---|---|---|
| Platform root CA | custodians of recovery shares (k of n) | issuing the region CAs |
| Region and cell CA | `kms` role on control-plane nodes | node and service certificates |
| Workload CA and workload token issuer | control-plane nodes or node-bound | identities of tenant workloads |
| Identity service signing key | `identity` role | tokens for users and service accounts |
| Release signing key | project (offline root) | OS images, agent, boot artifacts, reference values for attestation |
| Secure Boot keys | per installation, or project or operator | boot chain on the device |
| TPM manufacturer CAs | manufacturer | authenticity of a TPM |
| Firmware baseline per device model | operator (confirmed at adoption) | firmware measurements of a device type |
| Passkeys, break-glass material, recovery keys | humans | administration and emergencies |
| Human confirmation (comparison code) | operator at the device | adoption without a hardware anchor |

**Guiding principle:** nothing on the network is trustworthy per se – neither source address, VLAN, DHCP response, gossip message nor kernel parameter. Such information is a hint, not a basis of trust.

### Trust boundaries and principles

The platform distinguishes an **outside world** (LAN, discovery segment, internet), a **tenant domain** (VMs, containers, Kubernetes clusters with their own workload CA) and an **infrastructure domain** (worker nodes and – at the core – the control-plane nodes). Checks happen **always** at ingress (sender-constrained tokens), between agents (mTLS plus permission table), in the state machine (node authorizer), in the KMS (placement evidence) and at the workload↔host boundary.

1. **Nodes are not principals for tenant operations.** They act as system actors with permissions derived from their assignments in the control plane.
2. **Raft is not Byzantine fault tolerant.** The integrity of the control-plane nodes is therefore the most important single assumption; it is secured with the highest available trust level, and **cells are blast-radius boundaries**.
3. **Short lifetimes instead of revocation infrastructure** – but revoking a node takes effect immediately via a replicated revocation list.
4. **Trust falls quickly and rises slowly.** Return from quarantine is never automatic.
5. **Fail closed** for identity and secrets, **static stability** for running workloads: a loss of trust stops workloads only if the policy requires it.
6. **Honest labeling:** what a node merely self-reports is recorded as self-reported and does not justify a high level.

## Trust levels for nodes

| Level | Name | Core criterion | Typical devices |
|---|---|---|---|
| T0 | `none` | not adopted or in quarantine | discovery, quarantined nodes |
| T1 | `basic` | adopted, node key as a file, boot chain not hardware-verified | Raspberry Pi without Secure Boot, x86 without TPM, nested VMs |
| T2 | `anchored` | firmware-enforced signature verification of the boot chain with own key, plus a device-bound key for disk unlocking | Pi with OTP Secure Boot, x86 with own Secure Boot without TPM |
| T3 | `tpm` | TPM 2.0 protects keys and disks, but no valid attestation | servers, mini PCs, notebooks with TPM |
| T4 | `attested` | like T3 plus Secure Boot, Measured Boot and a fresh, successful attestation | servers with TPM, devices with firmware TPM |

Additional labels (TPM type, Secure Boot mode, attestation state, type of disk unlocking, boot mode) allow finer-grained policies. Special cases: a Pi with a TPM add-on board reaches at most T3, because its firmware does not measure into the TPM. Diskless nodes without a hardware anchor are only permitted on explicit request, remain T1 and take on only stateless roles. VMs as nodes and external witnesses on third-party hosts are fixed at T1, because the platform cannot verify foreign hardware.

### Determination and dynamics

A trust controller in the cell computes the level from inventory, attestation results and events, and writes changes with a justification to the control plane. **Operators can cap a level, never raise it** – the only exception is a time-limited, justified trust exception approved under the four-eyes principle, which is visible in the compliance export. A downgrade takes effect immediately on new decisions (placement, secret issuance) and, after a grace period, on existing assignments.

### What each level may do

The minimum levels depend on the **operating profile** (`homelab`, `standard-c5`, `erhoeht` – elevated), not on the crypto profile:

| Function | `homelab` | `standard-c5` | `erhoeht` |
|---|---|---|---|
| Raft voter, `kms`, `identity`, cell CA signing | T1/T2 with a visible warning if no higher alternative exists | at least T3; T4 once attestation is available | T4 (until then T3 with a warning) |
| all other nodes | T1 | T1 per role rules | at least T3 |

Further rules: tenant workloads of data class `sensitive` run only on T3 or higher, class `attested-only` only on T4. Storage nodes may also be T1, because they only hold ciphertext (see [Storage](storage.html)). When choosing the control group, the level is a hard sorting criterion – but **spreading across failure zones takes precedence**: three T1 voters in three zones are better than three T4 voters in one zone. Tenant guardrails may only tighten these rules. A pure Pi homelab remains fully functional, with the degradation visibly flagged.

If a node's level drops, the control group controller replaces it as a voter, the KMS discards plaintext keys immediately, workloads with protection requirements are migrated within a grace period, and secrets with a minimum level are no longer renewed. Standard workloads remain unaffected.

## Node identity and lifecycle

A node's identity consists of an immutable **UID** (new with every re-adoption), a human-readable name, a SPIFFE ID in the certificate, the **node key generated on the node** (in the TPM, otherwise as a file on an encrypted disk), endorsement and attestation keys on TPM devices, an underlay key and a hardware fingerprint. Node certificates are short-lived and are renewed from half of their lifetime onward.

The lifecycle runs from **discovery** (ephemeral key, no basis of trust) through **adoption** and **initial certification** to ongoing **renewal**. If a node has been offline for a longer time, **re-certification** follows, whose evidence depends on the level: with a TPM, cryptographic evidence suffices; nodes without a TPM need **human approval** by default. A mismatched hardware fingerprint never leads to silent reissuance but to quarantine – the operator decides on replacement or confirmation. At the end comes **revocation** with a tombstone that prevents automatic re-admission.

## Remote attestation

Remote attestation makes level T4 possible. Attestation takes place at adoption, at every boot before joining the cluster, at every certificate renewal, periodically, after every update and on demand.

The flow in brief:

1. **Once per adoption:** the verifier validates the TPM's endorsement certificate against a curated, signed bundle of manufacturer CAs. Credential activation proves that the attestation key resides in the same TPM; the node key is proven to be TPM-resident.
2. **Every attestation:** the verifier sends a one-time nonce, and the node returns a signed TPM quote together with the event log. Checked are the signature, nonce, monotonicity of the TPM counters and that the log matches the PCR values.
3. **Comparison against a policy** made up of signed reference values from the release manifest (bootloader, kernel image, command line with dm-verity root hash, expected Secure Boot keys) and an operator-confirmed firmware baseline per device model.

Verification is **event by event** rather than only on final PCR values – this keeps firmware updates and multiple permitted image versions manageable and deviations explainable. The reference values are read-only and come exclusively from signed manifests (see [OS image](os-image.html) and [Release signing](release-signing.html)). Attestation only decides on level and state; secrets are issued separately and only afterwards. The verifier is in-house Rust code on the control-plane nodes.

Nodes without a TPM report image version, boot path and Secure Boot status signed with their node key. This detects misconfiguration and outdated images, but not an attacker with root privileges – which is why such nodes stay at T1/T2.

### Failure classes

| Class | Examples | Response |
|---|---|---|
| Indication of tampering | invalid quote signature, changed key, log does not match the PCRs, nonce replay, Secure Boot suddenly off | immediate quarantine, high-severity alert |
| Unknown, plausible measurements | new firmware version, image outside the permitted window | downgrade to T3, alert, return after operator approval |
| Missing evidence | verifier unreachable, node offline | downgrade after validity expires, never quarantine |

### Quarantine

Quarantine can be reached directly from any adopted state and takes effect at all levels: instead of a regular certificate, the node receives a short-lived quarantine certificate that only permits diagnostics, attestation and forensic export. It loses any role in the control group, is excluded from gossip (the gossip key is rotated immediately), can be reached in the underlay only by control-plane nodes, receives no keys whatsoever, and workloads with protection requirements are stopped. Exit only via fresh evidence and human approval – or decommissioning.

## Service identities and mTLS

**One identity per process boundary, not per role:** all roles within the agent use the node certificate; which role a node may perform is authorized from the control plane on every call, not from the certificate. In-house service processes outside the agent (such as the boot service `cp-bootd` or the block storage service `cp-blkd`) and third-party components (time service, telemetry, object storage, etc.) receive **their own locally generated keys** with short-lived service certificates whose SPIFFE path lies beneath the host's path. This makes it possible to answer, from the certificate and the control state alone, whether a service is running on the node the role is assigned to. Third-party processes never receive the node key, the gossip secret or KMS access; their keys are kept in unit-specific, ephemeral credential directories.

For every mTLS connection between agents, a dedicated verifier checks in addition to the TLS parameters: the chain up to the cell or region CA of its own region (the workload CA and public CAs are never accepted on infrastructure ports), exactly one matching SAN URI with the current cell epoch, no entry on the revocation list, no quarantine state. **The certificate only says who – never what.** The "what" is governed by an **RPC permission table** declared in code: each method names the permissible caller property (Raft member, leader, placement of the resource, role, state), and tests ensure that no method exists without an entry. Forwarded API requests are authorized at the destination based on the **original token**; the ingress node's signature only proves the path. Network filter rules generated from the control state form a second layer and also restrict components with weak self-authentication to authorized peers.

## Workload identity for tenants

Tenant workloads receive identities from a **dedicated workload CA**; its trust bundle never contains the infrastructure CAs, and workload identities are always rejected on infrastructure interfaces (see [Identity](identity.html)). The "attestation" of a workload is its **placement**: only the host agent on which the workload runs according to the control plane may request an identity for it, and the CA verifies the placement itself before signing. The guest receives the identity exclusively via its own channel (vsock, projected file).

Workload tokens are signed with a **node-bound, short-lived issuer key**. Verifiers require that the key belongs to the node **and** that the workload runs exactly there according to the control plane. A compromised node therefore cannot mint tokens for other workloads. For external federation partners, a token exchange for a centrally signed, short-lived token is available. In a later phase, confidential computing will supplement placement attestation with hardware reports.

## Secret distribution and protection of the control state

Secrets are distributed according to fixed rules:

1. **Need and level** – no secret "just in case". Plaintext KEKs and CA keys only on nodes with the `kms` role; a volume's data keys only to the compute host with a valid attachment, never to storage nodes.
2. **Only in memory**, zeroed after use and without swap.
3. **Gossip never transports secrets.**
4. **Tracking per node:** the control plane records which secrets a node has received – the basis for targeted rotation in case of compromise.
5. **Every issuance is audited.**

The replicated control state is protected in multiple layers: encrypted disks, field-level encryption for key material, full copies only on control-plane nodes, a node authorizer, and hash-chained, signed audit blocks. The certificate signer only issues when all conditions from the control state are met, and limits the issuance rate per node.

## Operator access and break-glass

The OS image has **no interactive login and no SSH access by default**. Operators manage via API, portal and MCP; metadata is visible, tenant content only via an explicit, audited access request. Interactive access to nodes exists in exactly two ways, both privileged, time-limited, justified, recorded and audited:

- **Diagnostic session:** fixed command set of the agent, optionally a shell, at most two hours, four-eyes principle can be enabled by policy; the node is visibly flagged.
- **Tier-0 SSH:** short-lived SSH certificates from a platform-owned CA, only via the management network; the permission is assigned to no one by default and is not included in the administrator role.

Break-glass is divided into **four clearly separated levels**: an emergency account if the identity service fails (hardware key, no access to content), cell recovery on quorum loss (local, with a second person, epoch change), PKI/KMS recovery via a k-of-n key ceremony, and local rescue access that only unlocks data together with the platform. Every use triggers an alert, is followed up with a review and is practiced regularly.

## Auditing of security-relevant events

Security-relevant events are logged signed and chained – even without quorum, in a local, signed buffer that is replayed later. Recorded events include discovery and adoption, every certificate issuance and every revocation, attestation results, level changes, quarantine, key releases, denied authorizations, gossip anomalies, duplicate identities (suspected cloning), key rotations, exceptions, diagnostic sessions, break-glass, boot conflicts and physical events such as chassis intrusions. Frequent routine events are aggregated; critical ones are logged individually and alerted on.

## Handling a compromised node

**Detection:** strong signals – indications of tampering during attestation, or the same node identity from two endpoints at the same time – trigger quarantine automatically. Medium signals (mismatched fingerprint, accumulated authorization denials, unexpected boot path, chassis intrusion) generate a proposal with one-click execution; weak signals only generate alerts.

**Containment as an operation:** quarantine with the reason "suspected compromise" puts the node on the revocation list within seconds, excludes it from gossip, underlay and control group, stops workloads with protection requirements and executes a **rotation plan** derived from the secret tracking. The scope follows the role: for a worker node, its own keys and notifying the affected tenants suffice; for a node with the `kms` or identity role, an emergency rotation of the cell CA, key hierarchy and signing keys follows.

**Recovery:** forensics first, if desired. No "cleaning" on site – the node is decommissioned and can only be re-admitted as a **new identity** after reinstallation. Replicas and the control group recover via the normal controllers; a post-incident review feeds into the detection rules.

**Blast radius as a design goal:** a compromised worker node affects at most the tenants with workloads on it; a voter, the cell; a node with the `kms` or identity role, the region – which is why the highest minimum levels apply to these roles.

The same principle applies to the boot and discovery environment: a non-adopted or foreign device reaches neither the underlay nor mTLS nor gossip, boot artifacts are signed, and adoption requires human confirmation or hardware evidence.

## Implementation phases

| Phase | Scope |
|---|---|
| MVP | levels T0–T3, role and placement matrix, node lifecycle with re-certification, quarantine, RPC permission table, service identities, node-bound workload issuers, secret tracking, diagnostic session and tier-0 SSH, audit catalog, compromise runbook |
| P2 | TPM-resident node keys, remote attestation (T4), firmware baselines, auto-adopt with attestation, countersigning of audit checkpoints by multiple voters, forensic export |
| P3 | confidential computing, manufacturer reference values, runtime measurement, re-encryption after compromise |

Related pages: [Cryptography](cryptography.html) · [Threat model](threat-model.html) · [Boot and adoption](boot-adoption.html) · [Network](network.html) · [Compliance by design](compliance-by-design.html)
