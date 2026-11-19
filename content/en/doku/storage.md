title: Storage
summary: Block, object and file storage from two nodes to thousands – the in-house block storage cp-blk with metadata in the cell Raft, tenant encryption on the compute node and a maturity gate before replication.
group: konzept
order: 85
quelle: Concept 12 (storage concept)
de: speicher
---

The storage concept describes how the platform provides block, object and file storage – on two Raspberry Pis just as on a thousand servers. Decided on 2026-11-14.

## Key decisions

- **Block storage built in-house in Rust** (`cp-blk`) with **one** data path for all sizes: driver `local` in the first release, `replicated` (2–3 copies) after passing the maturity gate, erasure coding later for cold and object classes.
- **Metadata in the existing cell Raft**, payload data never. No second consensus mechanism.
- **Tenant encryption on the compute node:** storage nodes store and replicate only ciphertext.
- **Object storage initially Garage** behind a dedicated S3 front end `cp-s3gw`; versioning, Object Lock and bucket events come with an in-house object store on the `cp-blk` chunk layer, with `cp-s3gw` remaining the stable interface.
- **File storage** via one NFS server per share on a replicated volume, replaceable behind a narrow control interface.
- **Ceph only as an optional external driver** for data centers with existing Ceph – not in the default path.
- **Replication by default:** with fewer than three storage hosts, two copies with a witness; from three hosts, three copies.

## Requirements and size classes

| Class | Nodes | Block expectation | Object expectation |
|---|---|---|---|
| G0 single node | 1 | local, snapshots, external backup | simple |
| G1 two nodes + witness | 2 | two copies, continued operation if one node fails | twofold |
| G2 homelab/SMB | 3–10 | three copies across hosts | threefold |
| G3 edge/site | 10–100 | three copies across racks, QoS | threefold across zones |
| G4 cell | 100–1,000 | like G3 plus rebalancing at large scale | cluster per cell |
| G5 region | thousands | pools per cell, cross-cell only asynchronous | replication between cells |

Hard requirements are a separate key per volume with crypto erase, encryption at rest by default, no single point of failure from three nodes, fair IOPS distribution between tenants, the tight storage budget of small devices and the process-boundary rule for third-party components (see [Rust stack](rust-stack.html)).

## Options and decision

The original plan "Ceph from three nodes, lightweight mode below that" was rejected. At the small end, Ceph does not fit the target hardware (memory per daemon, no sensible two-node mode), brings a **second consensus mechanism** alongside the platform Raft, its own identities instead of X.509, and a break between "small" and "large" with two data paths and a migration when growing. Its maturity is the strongest counterargument – but the price is too high for this product.

Four variants were compared: Ceph across a process boundary, everything in-house, a hybrid "block in-house, object initially Garage", and a classic hybrid with an in-house lightweight mode and Ceph above it. Third-party alternatives such as DRBD/LINSTOR, Longhorn or SeaweedFS either cannot handle two nodes or need a second consensus. **The hybrid was chosen:** it uses what the platform already has – Raft, failure domains, fencing, key management, PKI, scheduler –, replaces two external systems with a single in-house path and avoids the scope of S3 semantics for the start. Garage does not violate the "one consensus" principle, since it works with CRDT metadata and quorums; its layout is set by the agent from the control plane.

The non-goal "no in-house distributed file system" is thereby made precise: no in-house distributed **file system**, no in-house **database**, no Ceph as a mandatory component – block and object storage based on the platform Raft and the chunk layer are in-house developments.

## Architecture of cp-blk

| Component | Location | Task |
|---|---|---|
| Agent storage module | every node | disk inventory and adoption, pool membership, control of `cp-blkd`, status reporting |
| Placement controller | cell controller | compute the placement map, epoch changes on failure, rebalancing, capacity |
| `cp-blkd` | separate, isolated process | on-disk storage, replication, recovery, scrubbing; client part on compute nodes |
| `cp-privd` | every node | privileged steps with a fixed command set (set up encryption, create devices) |

`cp-blkd` deliberately runs outside the agent so that a fault in the data path does not affect the agent.

### Data model and data path

- A **pool** is a set of disks of the same media class in a cell with a replication rule. **Placement groups** are the unit of distribution.
- A **volume** is a sequence of fixed-size chunks; each chunk is assigned to a placement group by hash, and each placement group to an ordered set of replicas.
- **The Raft holds** pools, deviations from the computed placement, epochs, volume metadata, snapshot trees and disk states – only a few megabytes even with a thousand nodes. Payload data and chunk indexes are never stored in the Raft.
- **Writing:** the client writes to the primary copy of the placement group, which writes locally and in parallel to the replicas; the acknowledgment comes only once the minimum number of copies has been durably stored. Requests with a stale epoch are rejected.
- **Epoch changes** happen only through a write by the controller to the Raft. As a result there is **no split brain**, not even with two nodes: without quorum (with a witness), no new epoch.
- Every chunk carries a **self-describing header** (pool, volume, index, epoch, version, checksum) – the basis for emergency reconstruction.
- **On the compute node**, `cp-blkd` provides a block device via ublk; on top of it sits dm-crypt with the volume key. Hypervisor and containers see only the decrypted device. NBD serves as a fallback.
- **Transport** via mTLS with a dedicated service certificate in the underlay; the payload is already tenant ciphertext at that point (see [Network](network.html)).

### Drivers

| Driver | From | Contents |
|---|---|---|
| `local` | first release | thin volumes and snapshots on one node, encryption per volume |
| `replicated` | after maturity gate | `cp-blk` with copy count and minimum copies |
| `ec` | later | erasure coding as an additional class, default for object, backup and archive from about six storage hosts |
| `ceph-rbd` | later, optional | the operator's external Ceph cluster, client side only |

All drivers share the API, snapshots, backups and encryption. A driver change is a volume migration; since the tenant layer sits above the driver, the ciphertext remains unchanged.

As long as `replicated` has not passed the maturity gate, tenant volumes use `local`. To compensate, every volume gets a **snapshot and backup policy targeting another node** by default – it can only be opted out of explicitly, and opting out is audited. This deviation is documented and time-limited.

## API resources

The storage API follows the platform's resource model (see [API-first](api-first.html)):

- **Operator side:** `Disk` (disk with type, size, health, media class), `StoragePool` (driver, replication rule, failure domain), `StorageClass` (pool selection, QoS, encryption – cannot be disabled –, permitted data classes).
- **Tenant side:** `Volume`, `VolumeAttachment`, `VolumeSnapshot`, `Bucket`, `AccessKey`, `FileShare`, as well as backup policies, vaults and recovery points.
- **Long-running operations** such as resizing, cloning, migration, snapshot restore, disk adoption, draining, decommissioning and secure wiping.

Disk and pool operations are operator permissions; formatting and wiping require explicit confirmation. API, CLI, MCP and [portal](portal.html) offer the same functionality.

## Placement across failure domains

- Topology labels (site, room, rack, power circuit, switch, host, disk) form a tree.
- Placement uses **weighted rendezvous hashing** per level: deterministic from placement group, pool epoch and topology, so that every node can recompute it. When adding or removing, only what is necessary moves.
- If there are too few domains, placement falls back one level lower and reports this visibly; two copies on the same disk never happen.
- **Unsuitable media** such as SD cards and USB sticks are allowed, but clearly flagged, given a low weight and limited to at most one copy per failure domain.
- **Location boundaries:** pools end at the cell; policies can restrict storage to specific sites.
- **Trust levels:** since storage nodes only hold ciphertext, the lowest level suffices by default; what matters is the level of the compute node that receives the key (see [Security model](security-model.html)).

The scheduler binds workloads with `local` volumes to their node and, for `replicated`, prefers nodes with local copies. Before a VM is restarted on another node, the controller increments the **attachment epoch** so that the old client can no longer write.

## Disk lifecycle

A disk passes through the states **discovered → proposed → adopting → active → draining / failed → decommissioned → securely wiped**.

- **Adoption** only for empty or explicitly approved disks, with a warning for unsuitable media.
- **Replacement:** a new disk is adopted as a new resource; the rebuild is spread across many sources.
- **Health:** SMART queries, daily light and regular deep scrubbing with comparison of copies, wear monitoring – when thresholds are reached, draining is proposed.
- **Secure wiping:** tenant data by crypto erase; decommissioned disks by wiping the encryption header and hardware sanitize, with signed wipe evidence.

## Security

| Topic | Implementation |
|---|---|
| Platform layer | LUKS2 on every storage disk, key TPM-sealed or network-bound |
| Tenant layer | separate key per volume, encryption on the compute node, wrapped under the tenant key |
| Key release | only to nodes with a valid attachment epoch and sufficient trust level; storage nodes never receive tenant keys |
| Tenant isolation | random volume identifiers; every call to `cp-blkd` carries the caller's epoch and certificate, authorized from the control plane |
| Integrity | checksums against media errors; authenticated encryption for elevated protection requirements is planned as a later option |
| Object | the S3 front end derives a key per object from the bucket key; Garage stores no keys |

Details of the methods and the key hierarchy are in [Cryptography](cryptography.html).

## Durability and maturity gate

Mathematically, even twofold replication is very durable for independent failures. In practice, however, **correlated failures** and **software bugs** dominate – for an in-house build, the correctness of the code is the real risk. Therefore a **maturity gate** applies before tenant data goes on `replicated`:

- deterministic simulation with partitions, restarts, epoch changes and clock skew, checked for linearizability;
- real fault injection over weeks without data loss;
- crash-consistency tests with power loss;
- **emergency reconstruction** of volumes solely from the self-describing chunks, without Raft;
- upgrade and downgrade tests;
- external design and code review by storage experts.

**Recovery:** crash-consistent snapshots, tenant backups with change tracking as encrypted, deduplicated backups in S3, platform backups of the metadata (without payload data) and asynchronous snapshot shipping between cells for disaster scenarios. Immutable backups follow with the in-house object store.

### Findings from measurements

Initial measurements support the decision qualitatively: synchronous replication costs hardly more than a local write with sync – latency is determined by the **medium**, which is why the choice of media matters more than the replication factor. Erasure coding is cheap to encode on ARM but expensive to reconstruct, and therefore comes only later and only on powerful nodes. Hardware-accelerated checksums are significantly faster than cryptographic hashes and suffice against media errors. AES encryption is comfortably fast enough on devices with crypto extensions; devices without these extensions are the bottleneck and will be re-measured on real hardware before being approved for compute with volumes.
