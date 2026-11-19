title: Release bundle
summary: Format, verification, import and distribution of the release bundle that brings a platform release into a cluster.
group: prozess
order: 210
quelle: Process description release bundle and release manifest
de: release-buendel
---

## Purpose

A platform release – agent, OS base, extensions and boot artifacts under one common version – reaches a cluster
**by import only**. There is no online fetch from inside the cluster; the operator uploads a bundle via the API,
command line, MCP or portal. This way updates work in isolated (air-gapped) environments exactly as they do in
connected ones, and the operator makes a deliberate decision about which release enters their region.

The transport format is called `cp.release-bundle/v1`. It is a single **uncompressed tar archive with a fixed
order**. This order is the core of the design:

- The receiver checks signatures and release rules **before** the large artifacts arrive. An invalid bundle is
  rejected after a few kilobytes.
- Every artifact is hashed on receipt – streamed, without buffering the whole bundle.
- Compression is deliberately not used: the images are already compressed or are verity images, and compression
  would prevent the random access that resuming interrupted uploads requires.

The signature chain itself is described in [Release signing](release-signing.html); how an imported release is
rolled out to the nodes is described in [Rollout controller](rollout.html).

## Container format

The archive is POSIX **ustar** (512-byte blocks, two zero blocks at the end). The strict rules are meant to keep the
parser small and its attack surface low:

- regular files only; directory entries are skipped,
- each name at most once,
- no links, no PAX or GNU long names,
- no paths containing `..` or a leading `/`,
- sizes of 8 GiB and above in the base-256 field.

| # | Entry | Required | Content |
|---|---|---|---|
| 1 | `bundle.json` | yes | format identifier and version (informational only; the manifest is authoritative) |
| 2 | `metadata/<n>.root.json` | no | root rotation chain, in ascending order of root version |
| 3 | `metadata/timestamp.json` | yes | signed role *timestamp* |
| 4 | `metadata/snapshot.json` | yes | signed role *snapshot* |
| 5 | `metadata/targets.json` | yes | signed role *targets*: **all** artifacts and the manifest with length, SHA-256 and SHA-512 |
| 6 | `targets/release/manifest.json` | yes | release manifest `cp.release/v1`, itself a signed target |
| 7 | `targets/<target>` | yes¹ | every further target from `targets.json`, in any order |

¹ A target may be missing if the receiver already holds it content-addressed (see Resuming).

Target names consist of segments of letters, digits and `._+-`, separated by `/`, for example
`os/x86-64/uki.efi`. The prefix `boot/` marks boot artifacts for the network boot service (see
[Boot and adoption](boot-adoption.html)). Because the format is deliberately simple, a bundle can also be created
with standard tools (`tar --format=ustar`) in the order of the table; the project's release tool writes it as a
stream.

## Release manifest `cp.release/v1`

The manifest describes the release in functional terms. It is itself a target of the signed chain and is therefore
protected against substitution, rollback and freezing. Example with placeholder values:

```json
{
  "apiVersion": "cp.release/v1",
  "version": "1.4.2",
  "channel": "stable",
  "securityEpoch": 7,
  "minVersion": "1.3.0",
  "minAgentProtocol": 12,
  "artifacts": [
    { "name": "usr", "arch": "x86-64", "target": "os/x86-64/usr.raw",
      "sha256": "…", "size": 287309824, "verityRootHash": "…" },
    { "name": "uki", "arch": "x86-64", "target": "os/x86-64/uki.efi",
      "sha256": "…", "size": 61440000 }
  ],
  "sbom": { "cyclonedx": "sha256:…" },
  "sources": { "bundle": "sha256:…" },
  "provenance": { "slsa": "sha256:…" },
  "notBefore": "2026-11-10T00:00:00Z",
  "expires": "2027-05-10T00:00:00Z"
}
```

| Field | Meaning |
|---|---|
| `version` | `MAJOR.MINOR.PATCH` for the entire platform release; PATCH contains only security and bug fixes |
| `channel` | `stable`, `candidate` (pre-release testing) or `edge` (development only) |
| `securityEpoch` | increases with security-relevant fixes; going back below the running epoch is forbidden |
| `minVersion` | minimum version for a direct update path |
| `minAgentProtocol` | minimum agent protocol level for version negotiation |
| `artifacts` | name, architecture, target name in the bundle, SHA-256, size, and the root hash for verity images |
| `sbom`, `sources`, `provenance` | references (by hash) to the SBOM, source code archive and SLSA provenance – also targets of the bundle |
| `notBefore`, `expires` | validity window; prevents nodes from being held on an old manifest indefinitely |

Unknown fields are rejected. The `target` field binds each artifact to exactly one signed target.

## Verification

Verification is **identical for all delivery paths** – import via the API, the agent during an update, and the
installer. So there is no "more convenient" path with weaker rules.

1. **Signature chain** against the trusted root anchor in the OS image: root rotation step by step if needed,
   then timestamp → snapshot → targets with signature, version reference, hash and expiry. The most recently
   trusted root version is recorded per region (protection against root rollback).
2. **Manifest** is a signed target (length, SHA-256 and SHA-512 match).
3. **Release rules:** format and version, known channel, `notBefore ≤ now < expires`, `securityEpoch` at least
   as high as the highest epoch currently running on nodes, and `minVersion` at most the lowest running version.
4. **Artifact list = signed targets:** every artifact corresponds to exactly one target with the same length and
   the same hashes, and every target (except the manifest) to exactly one artifact.
5. **Every received artifact** is checked against length, SHA-256 **and** SHA-512. Only then does it become visible
   in storage (temporary file, `fsync`, atomic rename).

Errors are mapped to the usual API error classes (see [API-first](api-first.html)): signature, format and hash
errors as an invalid argument; epoch, minimum version or validity window as a failed precondition; the same
version with different content as a conflict. A configurable size limit protects against oversized uploads.

## Import, resuming and deduplication

Import is an action on the region (`region:importArtifacts`). The bundle is transferred as a tar stream; for small
bundles – for example via MCP – a JSON form with Base64 content is also available. Import is not a privileged
action, because the signature chain decides what is accepted.

With `validateOnly`, the server only verifies and additionally reports `missingTargets`, i.e. the targets it does
not yet hold. The result of an import is `created`, `unchanged`, `validated` or `incomplete`.

**Resuming** after an interruption relies on content addressing: fully received artifacts are kept. The command
line and the portal therefore first send only the metadata and manifest as a dry run, and then a partial bundle
containing **only the missing** targets. Importing the same release again is harmless (`unchanged`); identical
artifacts in different releases are stored only once.

## Storage and distribution

Every holding node stores releases content-addressed: artifacts and metadata files as read-only blobs keyed by
SHA-256, and per version a directory with the metadata, hard links to the artifacts and a local entry listing all
targets and hashes. This structure matches what the network boot service expects – a release's boot artifacts are
thus available for PXE and HTTP boot without copying. In addition, the boot service serves all targets of verified
releases content-addressed.

- **Holders** are nodes with the role `boot` or `control`; the target is two copies (or as many as there are
  candidates).
- **Replication** between holders runs over an internal, mutually authenticated TLS endpoint using node
  certificates. The receiver verifies the chain again – it does not trust the sender.
- **Failure of a holder** is detected by the cluster through the missing heartbeat; the next candidate fetches the
  release.
- The status of the `Release` resource lists the reachable complete copies. The
  [rollout controller](rollout.html) releases a target version only once the release is available and has enough
  holders.

Nodes later fetch their update from these holders. Peer-to-peer distribution between arbitrary nodes is planned for
a later stage.

## Build and signing (process)

Build and signing are separate, so that private release keys never come into contact with the build environment:

1. **Build:** binaries and OS images are built per architecture; SBOM, source code archive and provenance are
   generated. The result is an unsigned **plan** containing the manifest (exact bytes) as well as the length,
   SHA-256 and SHA-512 of all targets.
2. **Sign offline:** a separate signing environment receives only the plan, checks that the manifest and target
   list match, and signs the update metadata. The large artifacts do not leave the build environment; only public
   data (plan, signed metadata, root files) is exchanged.
3. **Assemble the bundle:** metadata, manifest and artifacts are written as a stream in the fixed order.
4. **Verify:** the finished bundle goes through the same verification as on import; in addition, it is checked that
   the trust anchor embedded in the image matches the root used.

On validity: by default, a bundle's metadata is valid for as long as the manifest (`expires`), so that bundles
transported offline remain importable. Protection against being frozen on an old state is provided by `expires` and
`securityEpoch`. Separate roots are used for test and production; root rotation is described in
[Release signing](release-signing.html).
