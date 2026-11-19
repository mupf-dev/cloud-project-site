title: Control Plane Architecture
summary: Agent, gossip membership (SWIM), Raft consensus per cell, two-node operation with witness, cells and regions, reconcilers, bootstrap and failure behavior.
group: konzept
order: 40
quelle: Concept 05 (Control plane architecture)
de: steuerungsebene
---

The control plane is the heart of BYOC: it holds the desired state of all resources, decides on placement and membership, and enforces both on the nodes – **without a central controller**. Terms such as node, cell, control group and witness are explained in the [Vision](vision.html); the chosen libraries in the [Rust stack](rust-stack.html).

## Core decisions

| # | Decision |
|---|---|
| 1 | **One agent process per node**, roles as runtime modules. External components (Cloud Hypervisor, Garage, k3s …) run as separate systemd units controlled by the agent. |
| 2 | **Two levels of truth:** *Raft* (per cell) for desired state, assignments, leases and relevant status transitions; *gossip* (SWIM, per cell) for membership, reachability and fast-changing metadata. **Gossip never triggers a destructive action on its own.** |
| 3 | **The control group is elected automatically:** 1 → 2 data nodes + witness → 3 → 5 voters, never 7. New members always start as **learners**; at most one membership change at a time. |
| 4 | The **witness is a full but lightweight voter** that never becomes leader. The default is the **blind witness**, which receives only hashes instead of payload data. |
| 5 | **Single-node fallback operation is read-only.** Writes resume only with a quorum – or via a local emergency override with recovery key and audit, never automatically. |
| 6 | **Cell guideline ≤ 1,000 nodes** (warning threshold 500; with Pi control nodes ≤ 100). Region data lives in its own small Raft group, which "collapses" into the cell group when there is only one cell. |
| 7 | **Routing by URN:** region from the URN, cell from a versioned shard map. |
| 8 | **Reconcilers are level-triggered, idempotent and fenced:** cell controllers run as shards with leases in Raft; stale writes are discarded. |
| 9 | **Static stability:** a control plane outage does not stop running workloads. |

## The agent

### Process model

- **One binary, one main process**, started and supervised by systemd (watchdog, automatic restart). On a panic the agent restarts rather than continuing in a half-broken state.
- Raft and gossip run in a **separate, high-priority runtime** so that API load (portal, watch streams, MCP) does not delay heartbeats and elections.
- **Roles** are modules in the same process and are activated via desired state. Exception: the boot and discovery service runs as a separate sandboxed process without access to the node key; in general, parsers at trust boundaries run without such access.
- **External components** do not run as child processes but as independent systemd units with their own cgroup and resource limits. An agent restart (update, crash) therefore does not terminate any workloads.
- Privileged operations are to be bundled in a small helper service with a fixed command set, so that the main process runs with reduced privileges.

### Components

Every agent contains a supervisor, identity and PKI, the WireGuard underlay, gossip membership, an API ingress with router, an RPC server, the node reconciler, audit, time monitoring and update control. Raft consensus additionally runs only on control group members, learners and witnesses; a **full watch cache** is held only by control nodes and learners – worker nodes cache only their own objects and therefore never see other tenants' data. Cell controllers run on nodes that hold a lease for them.

### Resource budgets

Target budgets on a Pi 4: worker node ≤ 96 MB RAM, control node ≤ 384 MB (with **SSD/NVMe mandatory**, no SD card), witness ≤ 48 MB (SD card permitted). This means a Pi 4 with 2 GB may serve as a control node; one with 1 GB only as a worker or witness node.

## Membership via gossip

Gossip follows the SWIM protocol with Lifeguard extensions. **The gossip scope is the cell**; in addition there is a small region pool made up of the control nodes of all cells. There is no region-wide pool of all nodes.

### Joining

| Phase | Mechanism |
|---|---|
| Before adoption | **No gossip.** Discovery via the boot service and discovery API; unknown hardware sees no gossip packets. |
| Adoption | The adoption package contains a one-time provisioning credential, the WireGuard configuration for at least three seed nodes and the cell ID. The node generates its own key and obtains its certificate via CSR. |
| Join | Underlay to the seeds, gossip key via mTLS, announcement to several seeds – after that, all members are known. |
| Restart | New incarnation with the same node ID; seeds from the local cache. |

Details of the adoption flow: [Boot & adoption](boot-adoption.html).

### Failure detection

A node is pinged directly, then indirectly via several other members, then marked as **suspect** and finally as **failed**. Lifeguard reduces false alarms caused by overloaded nodes – important for Pis under load. Detection takes about 5–15 seconds. Crucially: **"failed" via gossip is only a signal, not a decision.**

| Signal | Consequence |
|---|---|
| suspect | display only; the router avoids the node for any reads |
| failed < 5 min | Node is marked unreachable – only after the controller's own health check |
| failed ≥ 5 min and voter | Control group is reconfigured |
| failed ≥ 10 min | Rescheduling only for workloads without local state or with replicated volumes – fencing first |

### Metadata

Gossip carries only **small, fast-changing, loss-tolerant** information: underlay endpoints, actual roles, agent version, rough free capacity, health flags, leader hint and clock offset – at most 512 bytes per node, signed by the originating node. A periodic digest exchange with random peers compensates for lost messages. Everything that must be correct lives in Raft.

### Scaling and partitions

Experience shows that gossip scales to several thousand nodes per pool and does not limit cell size. In a network partition, only the side with the **Raft quorum** can reconfigure, fence and reschedule; the minority becomes read-only, and workloads keep running. A **mass-failure brake** kicks in when more than a third of a cell's nodes drop out within 60 seconds: a network or power event is then assumed – no automatic reconfiguration, no evacuation, alert to the operator.

## State: one Raft group per cell

Every cell has its own Raft group; log and state are stored locally in a crash-safe way. If a voter loses its data, it rejoins as a new member with a **new Raft incarnation** – so no "amnesiac voter" can vote with an old identity.

### Automatic election of the control group

The control group controller always runs on the Raft leader.

**Hard criteria:** at least 2 GB RAM (witness 512 MB); SSD/NVMe with measured low fsync latency; lifecycle state *Active*; matching agent version; wired network and low clock skew; minimum trust level according to the operating profile; minimum uptime. Eligibility data comes **exclusively** from the controller's measurements and from operator labels – a node cannot declare itself "eligible".

**Soft criteria**, weighted:

1. **Spread across failure zones** (site, room, rack, power circuit, switch): no single zone may hold a majority of the voters.
2. **Stability** (availability, flapping, battery operation).
3. **Hardware quality** (fsync latency, RAM, CPU class).
4. **Network latency** to the other voters.
5. **Load** – control and heavy workloads are kept apart.

Changes are made only for a clear improvement (hysteresis), to avoid constant reconfiguration.

| Eligible nodes | Voters | Learners |
|---|---|---|
| 1 | 1 | – |
| 2 without witness | 1 | 1 (hot standby) |
| 2 + witness | 2 data voters + witness | – |
| 3–20 | 3 | 0–1 |
| > 20 or ≥ 3 failure zones | 5 | 1–2 |

Five voters survive two simultaneous failures; seven would increase latency and replication load without being necessary for the failure model. Two data voters **without** a witness are never formed, because any single failure would block the cell.

### Reconfiguration on failure

1. Gossip has reported a voter as failed for five minutes.
2. The leader confirms via a direct health check, checks the mass-failure brake and the stability of the quorum, and selects a candidate – preferably from the same failure zone.
3. The candidate is added as a learner and catches up via snapshot and log.
4. Joint consensus commits the new membership in a single step.

If the old voter returns, it becomes a regular node and can be elected again later.

### What lives in Raft – and what does not?

| Data | Location |
|---|---|
| Desired state and metadata of all resources in the cell | Raft |
| Phase and condition transitions, placement, assigned IPs | Raft (aggregated) |
| Controller leases, fencing epochs, assignments, quota usage | Raft |
| WireGuard keys, certificate serial numbers, revocation list | Raft |
| Audit entries for mutations, long-running operations | Raft |
| Reachability, node metadata | Gossip |
| Metrics, logs, traces | Observability role, not in the control plane |
| Events (human-readable history) | local + aggregation, loss permitted |

**Guiding rule:** anything that justifies a decision (placement, fencing, permissions, quota) is stored in Raft. Anything that is only observed or changes more often than roughly once a minute is not.

The state grows from about 4 MB in a homelab to just under 1 GB at 1,000 nodes; snapshots are compressed, hash-verified and created in the background.

## Two-node operation with witness

### Starting point

The Raft library used only knows voters and learners, not a "log-less" witness. A voter with no log at all would only be possible by modifying the consensus algorithm. The witness is therefore a **full voter with restrictions**: it may never become a candidate or leader, does not apply entries (null state machine) and receives only metadata snapshots.

### Variants

| Variant | Description | Assessment |
|---|---|---|
| A – log witness | receives the complete log but does not apply it | local only and only on trusted hardware |
| **B – blind witness** | like A, but every payload is replaced by its SHA-256 hash before sending | **default for all witnesses**, local and external |
| C – witness may lead briefly | to bring a lagging data node up to date | to be evaluated after the MVP |
| D – log-less arbiter | custom consensus extension | rejected (correctness risk) |
| E – no witness | 1 voter + 1 learner | transitional mode |

**Why this is safe:** Raft safety depends on the vote, log IDs and persisted acknowledgment – not on applying the entries. The witness persists log IDs (or hashes), votes correctly, never becomes leader and never serves as a replication or read source.

**Commit rule (decided on 2026-11-12):** as long as both data nodes are healthy, a write is acknowledged to the client only once **both** data nodes have it. Only after a data node failure has been detected does an explicitly declared, alerted and audited **degraded mode** with the witness vote become active; the return to normal is automatic. In the elevated operating profile and with witnesses operated by third parties, "always both" applies.

**Deliberately accepted limitation:** if the data node with the most recent state fails permanently, the witness cannot bring the other one up to date – the cell remains write-locked until the node returns or an emergency override is performed.

### Witness as hardware or external

Suitable witnesses are a Pi Zero 2 W, Pi 3 or another micro node via boot stick – ideally in a separate failure zone –, an external witness over WireGuard (e.g. a VPS or a second homelab, with election timeouts adjusted to the latency) or a container on third-party hardware such as a NAS. One witness can serve several cells. A **shared external witness is permitted only as a blind witness and only with a trusted operator**, because Raft does not protect against malicious participants.

### Fallback operation with a single node

| Situation (data nodes A, B, witness W) | Behavior |
|---|---|
| B fails | fully writable, warning "no redundancy" |
| W fails | fully writable, warning "witness missing" |
| B and W fail | **read-only**; workloads on A keep running; node can be operated locally |
| Partition A ∣ B+W | B side writes, A becomes read-only and catches up after healing |

The **emergency override** can only be invoked locally on the surviving node, with the recovery key generated during initial setup or under the four-eyes principle. A dry run shows the potential loss window; the operator confirms that the other members are switched off. The node then starts as a single voter with a **new cell epoch**; old members are locked out via the epoch and must rejoin. There is **no automatic override**, not even after a timeout: a split brain with duplicate IP assignments or VMs started twice is worse than a write lock.

## Cells and regions

### Cell size

The guideline is **≤ 1,000 nodes per cell**. The limiting factors are the Raft write load (a leader processes serially), the snapshot size, the watch fan-out and above all the **blast radius**: a cell is the unit that can fail due to software bugs or faulty rollouts. Smaller cells also mean finer-grained rollout stages.

### Growth

The default is **"fill rather than split"**: when a cell reaches the warning threshold, a new one is created and new nodes and projects are directed there. Actual splitting is the exception: projects are moved individually via coordinated handover (write lock per project only for seconds), and nodes keep their URN in the process.

### Region level

Region-wide data lives in a **separate region Raft group** rather than in a federated directory – for strong consistency of the shard map, unique names and cross-cell quotas. Its voters come from different cells. It contains the cell directory, the shard map (project → home cell), regional IP pools, the region CA, the image catalog as well as the tenant directory and identity.

With **exactly one cell** there is no second Raft instance; the region data lives in its own key space within the cell group. If the region group fails, the cells continue working with the cached shard map and identity; only cross-cell operations fail.

### Routing by URN

1. Region from the URN – requests for other regions are forwarded to their endpoint (federation).
2. Project and node resources: cell from the shard map; region objects: the region group.
3. Writes and strongly consistent reads go to the leader; eventually consistent reads go to the local cache or the nearest member.

If the shard map is stale, the target cell responds with a hint, and the router retries exactly once. It follows leader hints only to current members with a verified mTLS identity. Requests are always forwarded with the **original token**; authorization takes place at the destination (see [API-first](api-first.html)).

## Reconciler model

| Type | Where | What |
|---|---|---|
| **Cell controllers** | on nodes holding a lease | cell-wide decisions: placement, IP allocation, quotas, role rules, node health, fencing, update staging |
| **Node reconcilers** | every node for itself | start roles, start VMs/containers, attach volumes, network configuration; report status |
| Control group controller | always on the Raft leader | Raft membership |

- **Leases and fencing:** each controller type is divided into shards, which are distributed to eligible nodes via rendezvous hashing. Leases live in Raft; only the leader judges their expiry, using a monotonic clock. Every write carries the lease epoch – so a "zombie controller" after a partition can no longer have any effect.
- **Node reconcilers** need no lease, but may only write their own node object and the status of objects assigned to them.
- **Level-triggered and idempotent:** reconcilers always compare desired with actual state; events are merely triggers, and there are regular full resyncs in addition. External resources carry the `uid` of the API resource; writes are conditional; errors become visible as conditions.
- **Fencing before rescheduling:** before a VM with a network volume starts on another node, the old node must verifiably be stopped – by acknowledgment, BMC power-off or expiry of a self-fencing deadline. VMs are never moved automatically without proven fencing.
- **Roles** `control` and `witness` are derived: they mirror the Raft membership, which only the control group controller changes. The operator only sets preferences.
- A **scheduler** filters nodes by architecture, capacity, trust level and affinity, scores them by strategy (bin-packing or spreading) and offers a dry run with a rationale per node.

## Bootstrap flow

1. The operator initializes the first node (setup token). It creates the CA, platform, region and cell and starts as a single-node Raft.
2. The second node is adopted (with a confirmation code), receives its certificate, underlay access and gossip key, and joins as a **learner** – warning "witness missing".
3. A witness device is adopted **without a role**, or an external witness is registered; the controller turns it into the witness: **2 data voters + witness** survive a failure.
4. With the third eligible node, the witness is removed (3 voters); it remains on standby and steps in if the cell drops back to two eligible nodes.
5. Beyond 20 nodes or three failure zones, the control group grows to 5 voters.

Roles such as `witness` and `control` are never assigned at adoption. An ineligible third node (e.g. a Pi 4 with 1 GB) does not change "2 + witness".

## Failure and fault scenarios (selection)

| Scenario | Behavior | Effect for users |
|---|---|---|
| Worker node fails | marked unreachable; after a grace period, eligible workloads are rescheduled after fencing | Control fully available |
| Follower voter fails | Quorum remains, reconfiguration via learner | none |
| Leader fails | New election within a few seconds, controllers and leases move along | Writes briefly delayed; retry via idempotency key |
| Network partition | Majority normal, minority read-only | Write errors on the minority side |
| Site failure | with spread across three sites the cell survives; with two sites a witness at a third location is mandatory | depends on topology |
| Cell failure | Other cells unaffected, workloads keep running | only projects in that cell |
| Region group fails | Cells continue working with caches | cross-cell operations restricted |
| Total power failure | Cold start from disk; startup phase without evacuation | normal after startup |
| Rolling update | New formats only active once all voters support them; leader last | none |

## Control plane security

- **mTLS between all agents** with certificates from the cell CA (intermediate CA under the region CA), short lifetimes and automatic rotation; in addition, everything runs inside the WireGuard underlay.
- **Re-certification after a long offline period** without re-adoption, provided the key and hardware fingerprint are unchanged; otherwise quarantine.
- **Gossip** runs only inside the underlay and is additionally sealed with a rotating cell key; metadata is signed by its originator.
- **Node authorization** in the state machine: worker nodes may not change desired state and cannot see other tenants' objects.
- **Control nodes are crown jewels** and preferably secured with TPM and attestation. Raft is not Byzantine fault-tolerant; cell boundaries limit the damage.

The overall model is described in [Security model](security-model.html) and [Threat model](threat-model.html).

## Test concept

Distributed correctness is ensured through deterministic simulation of entire cells, an invariant checker, model checking of critical flows, chaos and linearizability tests, and a hardware lab. MVP acceptance criterion: "2 nodes + witness survive a failure" and "no single point of failure from 3 nodes upward" are demonstrated in simulation (10,000 seeds without an invariant violation) **and** on real hardware.
