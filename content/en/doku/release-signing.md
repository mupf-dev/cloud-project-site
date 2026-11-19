title: Release signing
summary: Two signing paths for releases, the format of the update metadata following the TUF approach, the processes and the reproducibility of builds.
group: prozess
order: 220
quelle: Process description release signing, update metadata and reproducibility
de: release-signatur
---

## Overview: two signing paths

BYOC signs releases along two independent paths. They answer different questions for different verifiers.

| Path | Purpose | Keys | Verifier |
|---|---|---|---|
| **Sigstore/cosign keyless** | public releases; evidence of "built by exactly this CI workflow" | short-lived certificate from the workflow's OIDC identity, entry in the public transparency log; plus SLSA provenance | people, packagers, operators before installation |
| **Offline keys ECDSA P-384** (TUF pattern) | update chain of the nodes | root and targets offline, snapshot and timestamp short-lived | agent and installer on every node – **offline**, without network and without Sigstore |

The nodes trust **only** the update-chain root embedded in the OS image. Sigstore is an additional, public
transparency layer, but not a runtime dependency: a cluster without internet access verifies updates just as
strictly as a connected one. In a later phase, ML-DSA-87 will be added as a second, post-quantum signature per
envelope (see [Cryptography](cryptography.html)).

## Update metadata following the TUF approach

The update chain follows the pattern of *The Update Framework* (TUF) with four roles. Each role has its own keys,
its own thresholds and its own expiry times – a single compromised role is not enough to slip a manipulated update
onto nodes.

| File | Role | Content | Default expiry | Keys |
|---|---|---|---|---|
| `root.json` | root | all public keys, key IDs and threshold per role | 365 days | offline, *k* of *n* in production |
| `targets.json` | targets | target name → length, SHA-256, SHA-512 | 90 days | offline (release key) |
| `snapshot.json` | snapshot | reference to `targets.json` (version, length, hashes) | 30 days | release infrastructure |
| `timestamp.json` | timestamp | reference to `snapshot.json` | 7 days | release infrastructure, re-signed frequently |
| `<n>.root.json` | root | previous/new root versions for the rotation chain | – | old **and** new root |

For release bundles transported offline, the metadata can be valid for as long as the release manifest (see
[Release bundle](release-bundle.html)).

### Envelope (DSSE)

Every metadata file is a DSSE envelope (*Dead Simple Signing Envelope*): a type, a Base64-encoded payload and a list
of signatures with key ID. What is signed is the *Pre-Authentication Encoding* of type and payload. This removes the
need for canonical JSON: exactly the signed bytes are verified, and **only then** are they parsed – rejecting unknown
fields in the process. The key ID is the SHA-256 of the public point.

```json
{
  "payloadType": "application/vnd.cloud-project.update-metadata+json",
  "payload": "<Base64 of the JSON payload>",
  "signatures": [ { "keyid": "<hex>", "sig": "<Base64>" } ]
}
```

Timestamps are strictly UTC in the format `YYYY-MM-DDTHH:MM:SSZ`. By default, the version number of targets,
snapshot and timestamp is derived from the commit time and is therefore monotonic.

### Verification on the node

1. **Load the root** (embedded or most recently trusted): it must sign itself with its threshold; its version must
   not be lower than the stored one.
2. **Process the root chain:** each new root version must be exactly one higher and signed with the threshold of
   **both the old and the new** root. If the timestamp or snapshot keys change, their stored versions are reset
   (recovery after a fast-forward attack).
3. **Check root expiry** only after the chain – so that even an expired anchor can still be rotated.
4. **timestamp:** signature, version monotonicity, not expired.
5. **snapshot:** length and hashes as stated in timestamp, signature, matching version, not expired.
6. **targets:** length and hashes as stated in snapshot, signature, matching version, not expired.
7. **Artifact:** length, SHA-256 and SHA-512 as stated in targets.
8. **Persist the versions**, so that rollback protection also holds across restarts.

| Attack | Defense |
|---|---|
| Rollback to old metadata | version monotonicity, persisted |
| Freezing on an old state (freeze) | expiry times, short-lived timestamp |
| Mix-and-match of different states | hash binding timestamp → snapshot → targets |
| Endless data | fixed size limit for metadata files |
| Key compromise | role separation, thresholds, root rotation |
| Duplicate signatures | only distinct keys count toward the threshold |

**Deliberate simplifications compared to TUF 1.0:** no delegated targets, no *consistent snapshot*, DSSE instead of
canonical JSON, key ID over the point bytes. Interoperability with third-party TUF clients is not a goal; the format
is versioned via `spec_version`.

## Processes

### Development and CI

In development and in CI, signing uses an **ephemeral one-time key** that is deleted after the run. The tool refuses
key directories inside the repository, so that no keys are accidentally checked in. Verification uses the same
library as on the nodes.

### Public release

1. A version tag starts the release workflow: build per target platform without cache, checksum list, independent
   rebuild, cosign signatures and SLSA provenance. The result is a release **draft**.
2. **Offline ceremony** on a machine without network, with keys on an encrypted storage medium or later on a hardware
   token or HSM: verify artifacts and Sigstore evidence (the certificate identity must be the project's release
   workflow), compare hashes with the rebuild, then sign the update metadata.
3. The update metadata is attached to the release; the draft is approved under the **four-eyes principle**.
4. The timestamp is re-signed regularly (at least every 7 days); automating this with an online key is an open item.

### Root rotation

A new root generation is signed with the new **and** the old root keys (each with its threshold). Bundles carry the
rotation chain; nodes with an older anchor upgrade through it step by step, and the region updates the trusted root
version. Bundles signed with old keys are rejected afterwards.

## Reproducibility

A dedicated rebuild step copies the working tree into two different temporary directories with different path
lengths, builds independently in each (separate build directory, different clock time, same source time
`SOURCE_DATE_EPOCH`) and compares the SHA-256 of all artifacts – binaries and SBOMs. Only bit-identical results
count as reproducible. During the offline ceremony, the results are additionally compared against the rebuild.

## SBOM

Every build generates an SBOM per component in **CycloneDX 1.5** format and derives **SPDX 2.3** from it – with a
converter of the project's own, to avoid introducing an additional tool supply chain. The SBOM is reproducible as
well: timestamps from the source time, a serial number derived deterministically from the normalized document,
sorted components and dependencies. In addition, the binaries carry their dependency list embedded, so that
installed nodes can also be checked against new advisories after the fact (see
[Vulnerability management](vulnerability-management.html)).

## Security and compliance

- **Integrity and rollback protection** of updates, **signed, reproducible builds with provenance** and
  **SBOM in two formats** are fixed requirements of the project (see [Security model](security-model.html)).
- The only cryptography provider is a vetted library (see [Cryptography](cryptography.html)).
- **Fallback:** without an HSM, offline keys are kept on encrypted storage media, with root keys *k* of *n*
  distributed among separate responsible persons. Without access to Sigstore, nodes keep verifying unchanged, since
  they use only the offline chain.
- **Open:** automation of the timestamp, key ceremony and choice of HSM, second signature with ML-DSA-87.
