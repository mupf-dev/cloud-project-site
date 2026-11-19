title: OS Image (cpOS)
summary: The immutable node operating system – a Debian base built with mkosi, erofs and dm-verity, Unified Kernel Images, Secure and Measured Boot per platform, TPM-bound encryption, A/B updates with a health gate, plus hardening and SBOM.
group: konzept
order: 80
quelle: Concept 09 (OS concept) and description of the OS image pipeline
de: os-image
---

## Overview

Every node of the platform is an **appliance with a single job**: it runs the agent and the role components the agent controls – securely, updatably and without manual work. To do this, the platform ships its own image-based operating system, working name **cpOS**. Five guidelines follow from this:

1. **Immutable and verifiable:** everything executable comes from a signed, integrity-protected image.
2. **Atomically updatable with fallback:** an update is a slot switch, never a package-by-package rebuild.
3. **State clearly separated:** there is exactly one encrypted state partition; everything else is reproducible.
4. **API instead of shell:** configuration, diagnostics and maintenance go through the platform API, not SSH.
5. **Right-sized:** small enough for a Raspberry Pi 4 with 2 GB (and witness nodes on even smaller devices), large enough for data center servers.

### Key decisions

| Topic | Decision |
|---|---|
| Base | own image, built with **mkosi from Debian 13 packages**; building blocks from systemd (UKI, systemd-boot, repart, dm-verity, sysupdate, sysext, cryptenroll) |
| Raspberry Pi | **native Pi bootloader without UEFI**, A/B via the built-in "tryboot" mechanism; kernel and firmware from the Raspberry Pi archive |
| File systems | only `/usr` in the image (erofs with dm-verity, A/B slots); `/` volatile, `/etc` regenerated on every boot; persistence only in one encrypted state partition; **no package manager** |
| Contents | one base image per architecture (amd64, arm64-UEFI, arm64-Pi); role-specific runtimes as **signed system extensions**, versioned in lockstep |
| Operating modes | discovery, installer, initial setup, operation (local or diskless) and rescue are all built from the same build sources |
| Updates | write the inactive slot, reboot, **health gate**; automatic fallback on failure (boot counter or "tryboot" plus watchdog) |
| Rollout | rolling, via the control plane; at most one control-plane member per cell at a time, leader last; automatic updates on by default |
| Hardening | no login, no passwords, no SSH by default; kernel lockdown, mandatory module signing, default-deny firewall, sandboxing per service |
| Secure / Measured Boot | own keys per installation, TPM 2.0-bound disk encryption via **signed PCR policies** |
| Supply chain | SBOM, source bundle and provenance per artifact; reproducible build |

## Choice of base

The criteria were native Pi support, image-based mechanics, an established security team with a long support period, reproducibility, maintenance effort, size and licenses. Rejected were Fedora/CentOS Stream (short cycle, Pi 5 not officially supported), Buildroot (no security team), a Talos-style custom OS (would have to rebuild systemd features), Flatcar and Fedora CoreOS (Pi only via UEFI), NixOS (learning curve, size) and Ubuntu Core (tied to a vendor store). Yocto remains a **fallback option** for very small profiles. A UEFI path for the Pi was rejected because the community firmware is barely maintained anymore.

Only Debian with mkosi combines native Pi support, the systemd image building blocks and an established security team **without the project having to maintain a distribution** – what is maintained is a *recipe*, not packages. Package versions are pinned via timestamped snapshots, and the licensing situation is clear (Debian `main` plus firmware with a redistribution license). Moving to the next Debian release is planned as a regular minor release of the platform.

For amd64 and arm64-UEFI the Debian kernel is used (signed modules, lockdown, security updates by the kernel team); for the Pi, the Raspberry Pi kernel in an LTS line. The C library is glibc, against which the Rust components are built.

## Image structure

### Layers

| Layer | Contents | Property |
|---|---|---|
| Boot | UEFI: systemd-boot and Unified Kernel Images (UKI) for slots A and B; Pi: boot slots A/B with kernel, device trees and initramfs | signed |
| `/usr` | base (systemd, agent, privileged helper service, kernel modules, network and crypto tools) plus extensions per role | immutable, erofs + dm-verity, slot A/B |
| volatile | `/`, `/etc`, `/run` | tmpfs, regenerated on every boot |
| State | Raft data, node identity, audit buffer, journal, extension cache, container data | persistent, LUKS2-encrypted |
| Data | volumes of the storage roles | own encryption per volume (see [Storage](storage.html)) |

### Immutable `/usr` with dm-verity

`/usr` is a compressed, reproducibly built **erofs** file system, followed by a verity partition (hash tree) and a signature partition over the root hash, laid out according to the *Discoverable Partitions Specification*. The **root hash** is part of the kernel command line of the signed UKI or the Pi boot image. In the elevated protection profile, the kernel additionally verifies the verity signature against the installation's keys, so that even a tampered boot path cannot mount a foreign `/usr`. Any hash error triggers a reboot; a corrupt slot is thereby detected by the boot counter and discarded.

Because `/` is a tmpfs and `/etc` is generated from signed defaults on every boot, there is **no place where configuration can silently accumulate** – the OS is drift-free.

### Partition layout

**UEFI (amd64, arm64) – GPT, created at installation:**

| Partition | Size (guideline) | Contents |
|---|---|---|
| EFI system partition | 1 GiB | systemd-boot, UKIs for slots A and B, rescue UKI |
| `usr` A + verity + signature | 2.5 GiB + hash tree | base `/usr` version N |
| `usr` B + verity + signature | same as A | version N+1 or N−1, initially empty |
| State (LUKS2 → ext4) | 16–64 GiB | persistent node state |
| Data (optional) | remainder | reserve for storage roles on single-disk nodes |

**Raspberry Pi 4/5:** additionally a small control partition with the A/B selection and a rescue configuration, plus two boot slots each holding a signable boot image (capped at 180 MB, target ≤ 120 MB), followed by the same `usr` slots, state and data partitions as with UEFI. Very small devices for witness nodes use the same layout without a data partition.

### Persistence and configuration

The state partition holds the node identity and certificate (where no TPM is present), the Raft database (only on fsync-capable storage, for control-plane nodes), local node state and audit buffer, a content-addressed artifact cache, active extensions, container data, the persistent journal and the last known valid time.

Configuration is built in four levels, **without a package manager**:

| Level | Source |
|---|---|
| Image defaults | signed `/usr`: units, sysctl profile, base firewall rules, AppArmor profiles, default network |
| Boot hints | kernel command line – hints only, not a basis of trust |
| Node desired state | control plane: roles, network, operating mode, update channel – the agent renders the runtime configuration from it |
| Secrets | adoption package and KMS; TPM-sealed or encrypted on the state partition, **never in the image** |

Humans do not change `/etc` persistently; the agent detects any deviation from the desired state during periodic reconciliation and heals it. Software arrives exclusively via image updates or signed extensions.

### Services

The agent (`cp-agent`) runs as its own user with minimal privileges and strict sandboxing. Privileged operations (network configuration, partitions, extensions, updates, wiping) are handled by a separate helper service (`cp-privd`) with a **fixed, audited command set**, reachable only by the agent. The boot service (`cp-bootd`) runs only on boot nodes, as its own sandboxed process without access to node keys or the KMS. A console display shows the setup token, confirmation code and status – without a login. Role services run with their own users, cgroup limits and sandboxing.

### Base image and extensions

The base image contains the kernel and signed modules, only the firmware actually needed, systemd, the platform services, nftables and WireGuard, crypto and storage tools (cryptsetup, TPM support, wiping tools), chrony with NTS and, on the Pi, the EEPROM tools. Size target: `/usr` uncompressed at most about 600 MB.

Role-specific runtimes come as **system extensions (sysext)**:

| Extension | Contents | Roles |
|---|---|---|
| compute | Cloud Hypervisor, virtiofsd, containerd, a Rust OCI runtime, Kata Containers | VM and container nodes |
| k8s | k3s | Kubernetes |
| garage | Garage object storage (separate process) | object storage |
| sdn | network components | overlay, gateways |
| observability | metrics and log storage | observability |
| debug | diagnostic tools, SSH server for tier-0 access | diagnostic sessions only |

Why extensions instead of a monolith: small nodes do not carry hundreds of megabytes of runtimes they never use – less code means less attack surface. Role changes work without reinstallation. Extensions are themselves disk images with dm-verity and a signature, and are tightly bound to the version of the base. Rules: a platform release consists of the base, all extensions and the discovery artifacts with **one** version number and one manifest; extensions are activated at boot, at runtime only when a role is added, and removed only after the node has been drained. Third-party components remain separate processes (see [Rust stack](rust-stack.html), [License governance](license-governance.html)).

## Operating modes

| Operating mode | Artifact | Writes to disk? |
|---|---|---|
| Discovery | small, signed discovery UKI or Pi boot image with the agent in restricted mode | no |
| Installer | like discovery, plus partitioning and wiping tools | yes, after adoption |
| Initial setup | universal USB stick image with discovery UKI and a complete `/usr` slot | only after initialization |
| Local operation | UKI or boot slot A/B | yes (state partition) |
| Diskless operation | UKI and `/usr` image via HTTP | no (optional scratch disk) |
| Rescue | rescue UKI or rescue entry | no |

All artifacts are built from **the same package versions**. How the operating modes are used in the boot flow is described in [Boot and adoption](boot-adoption.html).

**Local installation:** after adoption, the installer checks the manifest signature and minimum version, creates the GPT layout, sets up the encrypted state partition with TPM, network-bound or Pi device-key binding, writes slot A, marks slot B as empty and boots into operation. There the node generates its long-term key, receives its certificate and confirms the boot only after the health gate. The initial-setup node copies its running slot block by block to the target disk – no download at all. Existing data is protected: unless specified otherwise, only an **empty** disk is written; an existing cpOS installation only after confirmation, and foreign data only if the disk is explicitly selected, with its own confirmation and a warning in the dry run.

**Diskless:** the initramfs loads the `/usr` image into RAM via HTTP, verifies it with dm-verity against the root hash from the signed command line and mounts it. An update is simply the next network boot; a rollback means serving the previous version. Diskless requires sufficient RAM; persistent identity exists only with a TPM or Pi device key.

## Updates

### Versions, channels, manifest

The **entire platform release** (agent, base, extensions, discovery) is versioned as `MAJOR.MINOR.PATCH`. PATCH contains **only security and bug fixes**, MINOR features and base changes, MAJOR deliberately incompatible changes with a migration path. There are the channels `stable` (default), `candidate` (pre-release testing) and `edge` (development only), as well as release lines with patch maintenance.

A **signed release manifest** describes the version, channel, a security epoch (downgrading below the epoch is forbidden), the minimum version for a direct update path, all artifacts with hash and verity root hash, references to SBOM, source bundle and provenance, and an expiry date to prevent freezing on an old manifest. Details in [Release bundle](release-bundle.html) and [Release signing](release-signing.html).

### Flow on the node

1. The control plane approves a target version for the node.
2. The agent fetches the manifest and artifacts (content-addressed, also from other nodes) and checks signature, channel, security epoch, minimum version and expiry.
3. Via systemd-sysupdate, the privileged helper service writes the **inactive slot**, the new UKI with boot counter (or Pi slot B) and the required extensions – during normal operation and with throttled I/O.
4. Only now is the node drained (workloads migrate, leader change if needed) and rebooted.
5. The new slot boots; the **health gate** decides.
6. Green: the boot is confirmed ("bless"). Red or hang: the watchdog or boot counter triggers a reboot into the **old slot**, and the node reports "rolled back" along with the reason.

An operator rollback to a version within the same security epoch is allowed; otherwise only with privileged approval. Hardware-backed rollback protection via TPM counters is planned for a later phase; Pis without a TPM do not have this protection – a documented limitation.

### Health gate

Before the boot process completes, the health gate checks within a time limit (default 10 minutes):

1. `/usr` mounted via dm-verity, all extensions active, state partition unlocked.
2. Agent running, watchdog being serviced, certificate valid.
3. Underlay connection to at least one seed, gossip join completed.
4. All role services active.
5. For control-plane nodes: Raft log caught up with the leader, membership unchanged.
6. For boot nodes: boot projection loaded, ports bound.

**UEFI** uses the systemd-boot boot counters (three attempts). The **Pi** boots the new slot once via "tryboot"; if the gate fails or the node hangs, the hardware watchdog triggers a reboot and the firmware automatically boots the old slot. Only when the gate is green is the slot selection rewritten permanently. If even the default slot is unusable, the Pi falls back to a rescue configuration or network boot.

### Rolling updates

The rollout is driven by an update controller in the [control plane](control-plane.html); the OS only provides the node-local mechanics. An update policy defines channel, target version, maintenance window and stages (canary with an observation period, worker nodes with limited simultaneous unavailability, boot nodes one at a time, control-plane nodes one at a time with the leader last). High-severity security patches may be applied outside the maintenance window.

Rules: **quorum is never put at risk** – a control-plane member is only updated when all others are healthy and caught up. With only one control-plane member, an update with a short, announced write pause is allowed (with warning and confirmation). At most two adjacent versions run within a cell; new data formats follow only after a complete rollout. Updates proceed **cell by cell**, and a failure pauses the rollout automatically. Before the reboot, VMs are live-migrated and storage roles wait for healthy replication. Offline environments import releases with the same checks. Details in [Rollout](rollout.html).

Firmware (Pi EEPROM, UEFI) is not part of the A/B slots; Pi EEPROM updates come as a separate signed artifact and are applied individually by policy.

## Secure Boot and Measured Boot

| Platform | Verified chain | Disk key | Trust level |
|---|---|---|---|
| UEFI with **the installation's own keys** | firmware → systemd-boot → signed UKI → dm-verity `/usr` → signed extensions; measurement into TPM PCRs | TPM 2.0 with signed PCR policy | high with TPM (attested only from a later phase), medium without TPM |
| UEFI with vendor keys only | via a signed shim – fallback only, not permitted in the elevated profile | as above | high with TPM, low without TPM |
| UEFI without Secure Boot | no verification by the firmware; dm-verity protects `/usr` at runtime | TPM or network-bound unlock | high with TPM, low without |
| Pi with Pi Secure Boot (irreversible) | boot ROM → signed boot image → dm-verity; no TPM measurement | device key in OTP, optionally network-bound | medium, never attested |
| Pi without Pi Secure Boot | no local verification; signed HTTP network boot possible | network-bound unlock | low |

**Own keys per installation:** during initial setup, every installation generates its own Secure Boot keys (Platform Key, KEK, db) and a boot CA. It verifies the signature of the project release and **re-signs the boot components** – UKI, bootloader, iPXE and the verity signatures. No third-party shim, no MOK management.

**Signed PCR policy:** the state partition is not bound to fixed measurements but to a **key**: every UKI signed by the project unlocks the disk in exactly the intended boot phase – even after an update, without resealing – while a foreign or unsigned one does not. After this phase, the TPM no longer releases the key. Without a TPM, the disk is unlocked over the network via the cell. Reference PCR values are shipped in the manifest with each release and are used for attestation on join. Key management and trust levels are described in [Cryptography](cryptography.html) and [Security model](security-model.html).

## Hardening

### Frame of reference

The hardening profile is mapped to BSI IT-Grundschutz (Linux servers, or the corresponding Grundschutz++ requirements) and the CIS Benchmark for Debian (see [BSI IT-Grundschutz](it-grundschutz.html)). Many controls do not apply by design – there is no package manager, no login, no SSH and no cron. Compliance is checked automatically for each release and can be queried per node.

### Kernel

| Area | Measures |
|---|---|
| Integrity | lockdown, mandatory module signing, signed verity root hashes, no modules from writable paths |
| Memory | initialization on allocation, no slab merging, randomized page order, randomized kernel stack offset |
| Attack surface | debugfs off, strict IOMMU, no vsyscall and no 32-bit emulation on amd64, CPU mitigations never disabled |
| LSM | Landlock, Lockdown, Yama, AppArmor, BPF; Integrity Policy Enforcement as a candidate |
| Elevated profile | dedicated UKI with lockdown "confidentiality", memory wiping on free, panic on oops |

A **sysctl profile** restricts, among other things, unprivileged eBPF, kexec, ptrace, SysRq and io_uring, disables core dumps and hardens the network stack; deviations required by the overlay and WireGuard are justified. An **audit rule set**, immutable at runtime and based on CIS and ANSSI recommendations, records security-relevant system events.

### User space

- **No logins, root locked, no passwords, no SSH access by default.** SUID/SGID bits are removed.
- Firewall **default-deny** inbound: only boot services (on boot nodes only), API/portal/MCP and WireGuard; control and gossip exclusively via the underlay (see [Network](network.html)).
- Every service with its own user, a read-only system, minimal capabilities, system call and address family filters, and an AppArmor profile in "enforce" mode; the hardening level per service is measured in CI.
- Writable areas are `nosuid`, `nodev` and largely `noexec`; as a rule, the host only executes code from the signed `/usr` and signed extensions.
- USB mass storage is blocked during operation.
- No real-time virus scanner on the host (justified by dm-verity and the absence of write paths for binaries) and **no telemetry** to the project.

### Diagnostic access and rescue

| Path | When | Safeguards |
|---|---|---|
| **Diagnostic session** | the normal case for troubleshooting: fixed command set (journal, service status, network and disk state), optionally a shell | time-limited, justified, privileged, optionally four-eyes; recorded, audited and visibly flagged on the node |
| **Tier-0 SSH** | troubleshooting by a tightly limited group of people | only short-lived SSH certificates (at most 60 minutes) after passkey sign-in, only via underlay/management; a separate permission, assigned to no one by default |
| **Local rescue access** | node does not boot or control plane unreachable | rescue entry at the console, unlocked with the platform's recovery key; followed by re-certification with approval |

None of these paths grants access to tenant content via the API; the fact that a root shell can technically do more is made transparent to tenants (see [Identity and permissions](identity.html)).

**Further base services:** chrony with NTS (devices without a real-time clock start with a lower time bound), hardware random sources in addition to the kernel CSPRNG, a persistent journal forwarded via the agent, and secure wiping methods (NVMe Sanitize, crypto erase, ATA Secure Erase) with signed evidence.

## SBOM, source code, licenses

For the base `/usr` of each architecture, every extension, every discovery and boot artifact and iPXE, a **separate SBOM** (CycloneDX) is generated with the minimum fields per BSI TR-03183-2, which are checked in CI. The SBOM is included in the image and the release manifest; the agent provides it per node and matches it against security advisories.

GPL obligations are met by publishing the **sources together with the binaries** and retaining them at least as long as the image. Proprietary firmware (Pi, network cards) is shipped with its redistribution license and listed in the SBOM and NOTICE. Every build goes through a license scan.

## Build pipeline (abstract)

1. **Pinned inputs:** signed commits with the recipe and agent sources, a fixed Debian snapshot timestamp, a dedicated mirror of the Pi archive and a pinned mkosi version.
2. **Build** in an isolated environment: Rust components are cross-compiled for amd64 and arm64; mkosi builds `/usr`, extensions, discovery, Pi and USB stick images per profile and architecture, plus erofs and dm-verity.
3. **Signing** in a separate signing service.
4. **Verification:** a second build on a different instance with hash comparison of the unsigned artifacts, a virtual test matrix with Secure Boot and a software TPM (boot of every operating mode, update N→N+1, deliberately red health gate, corrupt slot, TPM unlock after update, rollout simulation without quorum loss), tests on real Pi and x86 hardware, and SBOM, vulnerability, license and hardening checks.
5. **Publication** of manifest, artifacts, SBOM, source bundle and provenance.

**Reproducibility** comes from fixed package versions, fixed timestamps, partition UUIDs and verity salt, reproducible Rust builds with a pinned toolchain, and SLSA provenance per artifact (target: SLSA Level 3). In operation, the SBOMs of all maintained release lines are matched daily against security advisories; high-severity hits automatically trigger a PATCH build that moves from `candidate` to `stable` (see [Vulnerability management](vulnerability-management.html)).
