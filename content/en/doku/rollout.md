title: Rollout Controller
summary: How platform updates reach the nodes in a rolling, quorum-safe way – release plans, ordering and gates, the health gate on the node, pausing and rollback.
group: konzept
order: 82
quelle: Rollout controller
de: rollout
---

## Overview

A platform update replaces the **entire platform release** on every node – agent, OS base, extensions –
via an **A/B slot switch** (see [OS image](os-image.html)). Getting there has three parts:

1. **Import:** the signed release is imported into the region and distributed to at least two holders
   (see [Release bundle](release-bundle.html)).
2. **Rollout controller:** it decides **which node is updated when** – rolling, quorum-safe, pausing
   on errors.
3. **Node side:** the agent and the privileged helper service download, verify and write the inactive slot, reboot
   and confirm the new state only after a green health gate.

The responsibilities are clearly separated: the OS provides the node-local mechanics, the controller the orchestration. The
controller only writes the target version, the maintenance state and a rollout marker on the node object; the agent
only writes the OS status of its own node.

## The controller

The rollout controller runs in the agent on the current **Raft leader** of the control plane (see
[Control plane](control-plane.html)). It is **level-triggered**: each pass derives everything from the
observed state; the status only records the start and time limit of the current step. A leader change
therefore does not interrupt the rollout – the new leader continues it from the same state.

The decision logic is a pure, deterministic function without clock, network or storage. This allows it to be
tested exhaustively in a simulation: model nodes with reboots, downtimes and leader changes; the metrics are
write availability, simultaneously failed voters and the reboot order.

**The leader measures health itself** – based on the replication responses and the lag in the replication log,
never based on the node's self-report.

## Release plan

Before a target version is set, a **plan** can be retrieved (dry run via the API action
`region:planUpdate`). The same plan is checked again when the target version is actually set. It contains:

- the **order** of the nodes,
- whether a **write pause** is needed (small cluster) and how long it is expected to last – estimated from the
  measured reboot duration,
- the **blockers** that prevent a rollout.

| Blocker | Meaning |
|---|---|
| Release not available | still importing, failed, or too few holders |
| Version skew | more than two versions would be in use simultaneously within a cell |
| Minimum version | the lowest running version is below the release's `minVersion` – no direct update path |

A **lower security epoch** is not a blocker in the plan, but requires privileged approval. Like
every platform function, the controls are available via API, command line, MCP and portal (see
[API-first](api-first.html)).

## Ordering and gates

### One node at a time

There is always **exactly one node in progress**. A node counts as in progress as long as its target version differs
from the running one or the rollout marker is set. Only then is the next one released. At most one
node is in the maintenance state at a time.

### Order within the region

The rollout proceeds **cell by cell**, regions one after another. Within a cell:

1. worker nodes and learners,
2. the witness,
3. follower voters one at a time,
4. **the leader last** – before that, it hands leadership over to a healthy, caught-up voter.

### Quorum protection

A voter (and the witness) is only updated when **all other data voters are healthy and caught up** – so the
quorum is stable even without it. For small clusters:

- **a single voter:** the update means a brief write lock; it is only allowed with a warning and explicit
  confirmation.
- **two data voters with a witness:** one data voter after the other, only if the witness is reachable.

### A planned reboot is not an outage

Before the reboot, the controller puts the node into the **maintenance state** (drain): workloads are migrated, live
where possible, otherwise restarted according to the tenant policy; storage roles wait for a healthy
replication state (see [Storage](storage.html)). Nodes in maintenance do not count toward the control plane's
**mass-failure brake** – a planned reboot should not trigger an emergency response. Leases and
fencing remain in effect unchanged.

### Version skew and feature gates

At most two versions run simultaneously within a cell (N and N−1). New formats for the replicated database
or storage may only be written once **all** nodes can read them – otherwise a node running the previous
version could no longer apply the log. This is what **feature gates** are for:

- Each gate names the minimum version from which the format can be read.
- It is only switched on once the rollout is **complete** and the lowest running version has reached this
  minimum version.
- Once switched on, a gate stays on. After that, going back to the previous version is no longer possible;
  a rollback is only possible within the version.

## Flow on the node

The node follows a fixed contract that it derives from its target version and its state:

| Node sees | Node does | reports |
|---|---|---|
| target version = running version | nothing, finish any open phase | `Running` |
| new target version W | download release from the holders, verify, write inactive slot – during operation, throttled | `Staging` → `Staged` or `Failed` with reason |
| `Staged`, maintenance and rollout approval for W | reboot into the new slot | `Rebooting` beforehand |
| after boot W is running, health gate green | confirm the new slot (*bless*) | `Running` (W), previous version recorded |
| after boot the old version is running | – | `RolledBack` with reason from the journal |
| `RolledBack` or `Failed` for W | **no** new attempt | unchanged |

Download, verification and slot writing run without interrupting operation; the node is only affected from the
drain onward.

### Verification and writing

The agent places the release in a staging area and instructs the privileged helper service via a
fixed, small message format. The agent only specifies the **version** and the **verification timestamp**; paths, file names,
partitions and commands are determined by the helper service itself.

The helper service **does not trust the agent**: it re-verifies the signature chain against the root in the image, checks the
manifest against the release rules (see [Release signing](release-signing.html)) and copies only the artifacts
for its architecture into its own source – checking length, SHA-256 and SHA-512 while copying. Later
changes in the staging area then no longer have any effect. The actual writing is done by `systemd-sysupdate` with this
local source in its own isolated unit; it protects the running version and gives the new
boot image a **boot counter**.

### Security epoch on the node

In addition to the manifest check, the helper service records the verified security epoch per version and, as a
lower bound, the highest epoch of a **confirmed** boot. Writing below this lower bound and booting a
slot below it are refused. A rollback to the previous slot is therefore only possible within the same epoch.

## Health gate

After the reboot, the **health gate** decides whether the new slot is confirmed. It uses systemd's *Automatic Boot
Assessment*: only when the gate is green is the boot counter removed. Checks run with a time limit
(default ten minutes; exceeding it counts as red):

1. The verity-protected `/usr` is mounted, all system extensions are active, the state area is
   unlocked.
2. The agent is running, servicing its watchdog and holds a valid certificate.
3. The underlay to at least one seed is up, the gossip join has completed (see [Network](network.html)).
4. All role units are active, role reconciliation runs without errors.
5. For control-plane nodes: the replication log has caught up with the leader, the node has its previous role again.
6. For boot nodes: boot data loaded, ports bound.

For this, the agent regularly writes a small, atomically replaced report with a timestamp, running version,
overall result and individual checks. The gate itself runs without network access, requires a fresh report and additionally
checks the role units itself.

## Abort and rollback

**On the node:** if the gate is red or the boot hangs, the watchdog triggers a reboot. The boot counter of the
new slot is then used up, and the node automatically boots the **old** slot. On Raspberry Pi hardware,
the firmware's one-time *tryboot* mechanism performs the same task. The node reports `RolledBack` with the
reason from the journal of the failed attempt.

**In the controller:** if a node reports `RolledBack` or `Failed`, or a step times out,
the controller **pauses** the rollout: it sets the condition `RolloutPaused`, creates an audit entry and an alert, and
releases no further nodes. The affected node does not try again. A failure on the first node
thus stops the entire rollout before it spreads.

**By the operator:** a rollback via the `node:rollback` action is possible as long as the target version has the same
security epoch and the previous slot still exists; otherwise only with privileged approval. Going back
further is only possible by reinstalling the node. A node can also be pinned to its version
and released again.

## Expansion stages

The current core comprises a target version per region and node, rolling one node at a time, quorum protection, leader last,
rollback via the health gate, pausing on errors and operator rollback. Also planned are
update policies with **stages** – for example a single canary node with an observation period, then
worker nodes in a limited proportion, boot nodes one at a time, control-plane nodes one at a time with the leader last –,
**maintenance windows**, automatic updates on by default with the option to apply urgent security patches outside the
window as well, and distribution of releases between arbitrary nodes (peer-to-peer). How
security releases and rollout work together is described in [Vulnerability management](vulnerability-management.html).
