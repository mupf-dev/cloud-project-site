title: Cryptography
summary: Principles of the cryptography concept – alignment with BSI TR-02102, two crypto profiles, a PKI with short lifetimes, two-layer encryption of data at rest and a roadmap to post-quantum cryptography.
group: konzept
order: 100
quelle: Concept 102 (Cryptography Concept)
de: kryptografie
---

The cryptography concept describes the **product-side part** of a cryptography concept as defined by BSI IT-Grundschutz (module CON.1): algorithms, defaults, key lifecycle and evidence functions for all platform components. The organizational parts – choice of profile, key ceremony, custody of recovery shares – are supplied by the operator. Cryptography *inside* tenant workloads is the tenant's responsibility; the platform provides keys, certificates and randomness for it. Who is entrusted with which key is governed by the [security model](security-model.html).

## Principles

1. **No home-grown crypto primitives** – only vetted libraries (rustls with aws-lc-rs in userland, kernel cryptography, TPM).
2. **BSI TR-02102 is authoritative.** Deviations are justified per finding, documented and assessed by the operator.
3. **Security level of at least 120 bits**; AES-256 for long-term confidentiality.
4. **Quantum safety for confidentiality first** (protection against "harvest now, decrypt later"), then for signatures.
5. **Short lifetimes instead of revocation infrastructure**, wherever possible.
6. **Purpose binding:** one key, one purpose – enforced through context labels during derivation and wrapping.
7. **Crypto agility:** algorithms are never hard-wired into a data format; every ciphertext carries its algorithm, key ID and version.
8. **Fail closed:** an agent refuses connections if its crypto profile cannot be satisfied – except for explicitly approved exceptions.
9. **Symmetric wherever possible:** the key hierarchy, backups and archives use only AES-256 and SHA-2-based schemes and are therefore already quantum-resistant today.

## Normative basis

The basis is the technical guideline **BSI TR-02102** in its current version. Particularly relevant for the concept:

- **TLS 1.3** is the target protocol; TLS 1.2 is only permitted as a transitional measure.
- Purely classical key agreement is recommended only until the end of 2031; after that only **hybrid with post-quantum schemes** (ML-KEM).
- Purely classical signatures are planned until the end of 2035; candidate post-quantum signatures are ML-DSA, SLH-DSA and hash-based schemes.
- For IPsec, the guideline covers only IKEv2. WireGuard, used as the underlay, is not covered there; the platform adds a post-quantum layer to it. Deviations are documented and assessed by the operator.

## Crypto profiles

The platform has two centrally configurable profiles. The active profile is a platform resource, applies at every level, and is enforced by every agent and reported as actual state. Regions may tighten it, never loosen it.

| | `bsi-strict` (default) | `compatible` (e.g. homelab) |
|---|---|---|
| Transport | TLS 1.3 without 0-RTT | additionally TLS 1.2 at the public ingress for legacy clients |
| Key agreement | hybrid, preferably `SecP256r1MLKEM768` | hybrid, preferably `X25519MLKEM768` |
| Signatures | ECDSA P-384 (CA) and P-256 (end-entity certificates) | additionally Ed25519 |
| Symmetric | AES-256-GCM, AES-256-XTS | additionally ChaCha20-Poly1305 for devices without AES acceleration |
| Underlay | WireGuard with mandatory PQ layer | PQ layer on by default, can be disabled with a warning |

**Hybrid post-quantum key agreement is the default in both profiles from the first release.** Both profiles prohibit outdated schemes such as TLS up to 1.1, short RSA keys, SHA-1/MD5 for security purposes, CBC modes in TLS, and 0-RTT. The `compatible` profile is a deliberate decision that is visible in the compliance report. Profile changes run as a staged rollout: first accept the new schemes, then switch off the old ones.

Individual nodes can be granted a **time-limited, justified and approved exception**, for example a device without AES acceleration. Such nodes are automatically excluded from the placement of workloads with protection requirements and appear in the compliance export.

## PKI

The internal PKI is hierarchical: **platform root CA → region CA → cell CA → node and service certificates**. Alongside it are a dedicated **workload CA** for tenant workloads and a separate CA (public via ACME or provided by the operator) for public endpoints.

- **Separate trust domains:** infrastructure mTLS trusts only cell and region CAs, never the workload CA. A tenant workload can therefore never identify itself as a node.
- **Short lifetimes:** node certificates are valid for days, service certificates for hours, workload certificates for minutes. Renewal starts at half the lifetime.
- **Revocation:** instead of OCSP or public revocation lists, short lifetimes suffice. Only for nodes is there additionally a replicated, signed and versioned revocation list that takes effect immediately and cannot be rolled back.
- **Root key:** during initialization, the root key is split into **k-of-n recovery shares** (Shamir). In the `bsi-strict` profile the online copy is deleted once the region CA has been issued; the root can then only be reconstructed through a ceremony under the four-eyes principle.
- CA keys are stored wrapped in the key management service; signing happens only on control nodes.

Keys are preferably held in the **TPM 2.0**. Devices without a TPM unlock their disk via a **network-bound threshold release** by the cell.

## Data at rest and key hierarchy

Data at rest is encrypted in **two layers**:

1. **Platform layer:** every node disk is encrypted with LUKS2 (AES-256-XTS) – protection against theft and device returns.
2. **Tenant layer:** every volume, every bucket and every backup has its own data encryption key (DEK). Block storage is encrypted on the compute host, so storage nodes only ever see ciphertext (see [Storage](storage.html)).

The key hierarchy is **platform root key → region KEK → tenant KEK → DEK**. Wrapping uses AES-256-GCM; the additional authenticated data binds each wrapped key to object, purpose, tenant and KEK version, so it cannot be unwrapped for anything else. Plaintext keys exist only in the memory of the key management service or, briefly, on the authorized host. A host receives a DEK only for resources verifiably placed on it; operator roles never receive tenant DEKs. **Crypto-shredding** by destroying a key renders data, including backups, unreadable and is documented with a signed deletion certificate. Tenant-owned keys from external KMS/HSM (BYOK/HYOK) will follow in a later phase.

## Crypto agility and PQC roadmap

Agility is built in: the profile is configuration, all in-house formats are versioned, algorithm changes run as an expand/contract rollout, and agents report the schemes actually negotiated – old schemes are switched off only once the migration is complete. Where no standard for composite signatures exists, dual signatures are used, both of which must be valid. Every use of cryptography is recorded in a machine-readable **cryptographic inventory (CycloneDX CBOM)** and checked against the profile in CI.

| When | Step |
|---|---|
| First release | Hybrid key agreement at all endpoints, PQ layer in the underlay, cryptographic inventory, profiles, AES-256 for data at rest |
| Following phase | ML-DSA dual signatures for updates, audit and deletion certificates; tenant-owned keys |
| After inclusion in TR-02102 | ML-DSA in the internal PKI, initially in parallel with the classical chain |
| By end of 2030 | Internal PKI fully post-quantum capable |
| End of 2031 | No more purely classical key agreement |
| End of 2035 | No more purely classical signatures (as far as hardware boot chains allow) |

The inventory, roadmap, hybrid schemes and annual review also form the basis for a PQC strategy as expected by current cloud audit catalogs (see [Compliance requirements](compliance-requirements.html)).
