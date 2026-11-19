title: Boot and Adoption
summary: How nodes join the platform – the first node via USB stick, further nodes via network boot, a boot service without a single point of failure, discovery quarantine, secured adoption, plus rejection, decommissioning and replacement.
group: konzept
order: 50
quelle: Concept 08 (boot and adoption concept)
de: boot-adoption
---

## Overview

A node enters the platform in exactly two ways: the **first node** starts from a USB stick or an SD card and sets up the platform; **every further node** boots over the network (or, as a fallback, from the stick as well), is discovered as unknown hardware, lands in quarantine and only becomes a full member through an explicit **adoption**.

The flow in brief:

1. Start via USB/SD, PXE, UEFI HTTP Boot, Raspberry Pi netboot or through a server's BMC.
2. The discovery system runs in memory, collects a hardware inventory and reports to the boot service – state **"pending"**, in quarantine.
3. A human or a rule adopts the node.
4. The node installs the OS locally (default) or runs diskless from the network, receives its certificate, joins the cluster and takes on roles.

### Key decisions

| Topic | Decision |
|---|---|
| Image | **one universal image per architecture** for initial setup, discovery/installer and operation (see [OS image](os-image.html)) |
| Boot service | own Rust implementation in a **sandboxed process without access to the node key**; **proxyDHCP** instead of replacing DHCP; active-active on at least two nodes |
| Integrity | all boot artifacts signed; with Secure Boot, a dedicated iPXE build signed with the installation's own key |
| Quarantine | two-tier: optionally a dedicated VLAN, **always** cryptographic |
| Adoption | manual or rule-based, secured by confirmation code, TPM attestation, enrollment token or adoption window; never MAC matching alone |
| Keys | the node's private key **never leaves the node**; certificates are valid for 7 days |

## The first node

### Media

| Platform | Medium | Notes |
|---|---|---|
| amd64 (notebook, mini PC, server) | hybrid image for USB sticks, ISO for BMC virtual media | bootable via UEFI and BIOS |
| arm64 with UEFI | image or ISO | UEFI only |
| Raspberry Pi 4/5 | image for SD card, USB or NVMe | writable with common imager tools |

The same image later serves as fallback medium for further nodes: if it finds a boot service or platform API on the network, it offers "Join this platform"; it only creates a new platform when that is explicitly chosen at the console. Headless devices decide automatically.

### Initial setup flow

1. The operator plugs in the stick and powers on the device. It obtains an address from the existing router and searches for a platform.
2. If none is found, it generates a **one-time setup token** and a TLS fingerprint and shows both on the console (and additionally as a file on the stick).
3. Using the token, the operator opens the **setup wizard** in the portal, API or MCP.
4. The wizard explores the network and proposes a configuration; the platform then creates the CA, platform, region and first cell, starts Raft with a single member and activates the control, identity and boot roles.
5. The OS is installed on the chosen disk, and the node reboots from disk.
6. The operator receives a one-time invitation link and the root CA fingerprint. At the final portal address, they register the **first admin passkey**.

The wizard is the guided form of a single API operation, so that API and MCP remain on equal footing (see [API-first](api-first.html)). It walks through hardware suitability, network exploration (existing DHCP, competing PXE services, VLANs, DNS, time sources), names, first admin and portal address, installation target, boot service, adoption policy (default: manual with confirmation code) and a dry run; at the end, recovery shares and the invitation link are shown once. For the portal address, the platform issues a server certificate from its own CA whose key never leaves the node; it is renewed automatically. Public certificates are possible via an upstream reverse proxy.

### Transition to a cluster

Until the second node arrives, the first node is deliberately a single point of failure – the portal points this out. With the second suitable node, the role rule distributes the boot service to it and fills its artifact cache. From three nodes on, boot, API, portal and MCP survive the failure of one node. The stick is no longer needed and remains usable as a rescue medium.

## Network boot of further nodes

### proxyDHCP

In a homelab, addresses are usually assigned by an existing router that knows nothing about PXE options. The boot service therefore operates as **proxyDHCP**: it only answers requests carrying a boot identifier, without assigning addresses; the client combines the address from the real DHCP server with the boot information from the proxy. Depending on the reported architecture, it delivers:

PXE clients (BIOS and UEFI) receive iPXE via TFTP, UEFI HTTP clients a URL to iPXE, iPXE itself the URL of its script, and the Pi bootloader its specific identifier. If another PXE service already answers in the segment, the boot service reports a **conflict** and by default only serves known clients – an existing PXE environment remains usable. A full DHCP mode of its own is only permitted on a dedicated interface, after verifying that no other DHCP server answers there. Network boot over IPv6 is not part of the MVP.

### iPXE and UEFI HTTP Boot

iPXE is the uniform second stage for x86 and arm64 UEFI and is shipped as a standalone binary artifact, not linked (see [License governance](license-governance.html)).

- **Dedicated build per installation:** it is built reproducibly and automatically during initial setup and on every change of the boot CA, contains the installation's boot CA as trust anchor and verifies every subsequently loaded image against a signature. With Secure Boot, it is signed with the installation's own db key – own platform, KEK and db keys instead of a third-party shim.
- **Upstream-signed iPXE shim:** only as a fallback for devices whose firmware does not allow setup mode; not permitted in the elevated protection profile and assigned a lower trust level.

The **iPXE script** generated by the boot service is the decision point; it contains no secrets and is signed. With **UEFI HTTP Boot**, the firmware loads either iPXE (default) or directly a signed unified kernel image of the discovery stage.

### Raspberry Pi 4/5

Raspberry Pi 4 and 5 boot from a bootloader in EEPROM that supports netboot via TFTP and – with signed images – via HTTP; the Pi 5 can additionally do HTTPS with its own CA. Brand-new devices, however, do not have the network in their boot order. The platform therefore provides a small **preparation image** that writes the EEPROM configuration once; alternatively, the Pi boots the universal image from a medium once and the agent changes the EEPROM after adoption.

| Variant | Integrity | Use |
|---|---|---|
| TFTP | no verification by the firmware, lowest trust level | getting started, compatibility |
| **Signed HTTP** (target) | firmware verifies the signature, Pi 5 additionally HTTPS | homelab and data center |
| Pi Secure Boot | firmware only starts signed images; key fused into OTP – **irreversible** | only on explicit request |
| USB/SD | image signature | fallback |

Because the Pi already sends its serial number in the first boot request, the boot service can create the discovery entry very early, and pre-registrations take effect immediately.

### Other devices

- **Arm64 servers with UEFI** behave like x86 UEFI.
- **Notebooks without PXE:** a tiny **netboot stick** that contains only iPXE and loads everything else from the network. Without a network path to the boot service, the universal image starts from the stick and reports in over a routed network.
- **Servers with a BMC:** via Redfish, the platform reads the inventory, automatically creates a pre-registration, sets a one-time network boot and powers on – or mounts the universal ISO as virtual media. Credentials exist only as a secret reference, and access happens exclusively from the out-of-band network.
- **Time budget:** from "power on" to "pending" takes about 0.5 to 1.5 minutes on x86 and on the Pi with HTTP boot, and 1 to 3 minutes on the Pi with TFTP – the target is at most 5 minutes.

## The boot service

### Components

All components run in a dedicated sandboxed process (`cp-bootd`) with its own user, minimal privileges and its own service identity – **without access to the node key**, gossip secrets or the KMS. Only this process holds the key used to sign boot scripts.

The components are proxyDHCP (with rate limiting), a read-only TFTP server for first stages, an HTTP(S) server for content-addressed, signed artifacts, the script generator, the discovery inbox and the **boot projection** – a local, replicated read view "known hardware → action" without any tenant data. All parsers are fuzzing targets.

### Replication without a single point of failure

- **Active-active:** all boot nodes answer broadcasts; the client takes the first offer. If a node fails mid-boot, the firmware retries; the iPXE script also lists all boot nodes as fallback targets.
- **Placement:** at least two boot nodes in different failure zones with access to the boot segment.
- **State:** decisions only read the boot projection; new discovery entries are written idempotently via the Raft leader.
- **Without quorum:** known nodes keep booting with the last known profile – important, for example, for diskless nodes after a power outage. New reports are buffered; adoptions are not possible without quorum.

### Artifacts and provenance

All artifacts come from **signed release manifests** and are obtained either from the release repository, from other boot nodes over the underlay, or via offline import (air gap). **Every** boot node verifies signature, hash and version monotonicity before serving an artifact. Which version is served is determined by the region's desired state; every artifact comes with an SBOM. Details under [Release bundle](release-bundle.html) and [Release signing](release-signing.html).

### Decision per boot request

| Device state | Response |
|---|---|
| unknown | discovery image, create entry "discovered" |
| pending | discovery image again |
| rejected | no offer or local boot; event, optional alert |
| installed node | "boot locally" |
| diskless node | signed OS image from the network |
| reinstallation requested | installer |
| decommissioned | like unknown, with a reference to the former node |

For servers, "network first" is recommended (central control of reinstallation and rescue, fallback to local); for the Pi, "local first, network as fallback", because its bootloader does not understand a "boot locally" command from the network.

## What gets booted

| Mode | Contents | Persistence |
|---|---|---|
| **Discovery / installer** | kernel and initramfs, agent in restricted mode, inventory tools – no SSH, no login | RAM only; writes to disks only after adoption, in installation mode |
| **Diskless** | immutable OS from the network, local state in RAM or on an encrypted scratch disk | persistent identity only with TPM or Pi device key |
| **Local installation** (default) | A/B partitions on disk, encrypted state partition | persistent; mandatory for control and storage roles |

### Hardware profile

The discovery entry contains an inventory: identity (SMBIOS UUID, serial number, manufacturer, model), CPU, RAM and virtualization capability, disks with serial numbers and SMART summary, network interfaces with LLDP neighbor and boot path, firmware versions, security features (Secure Boot, TPM, Pi Secure Boot) and an assessment of role suitability and the expected trust level.

**Device-supplied fields are data, not instructions:** free-text values such as model or firmware strings are marked as untrusted, normalized and only output in structured form via MCP. Suitability and trust level are never derived from self-reported information alone. The **discovery ID** is derived from stable hardware attributes, so reboots do not create duplicates.

### Discovery phases

**Discovered → Inventoried → Pending → Adopting → Adopted.** If a rule matches, the device goes directly from "inventoried" to "adopting". From "pending", a device can be rejected (and later unblocked); entries not seen for more than 30 days are considered orphaned and are cleaned up.

## Discovery quarantine

| Tier | Mechanism | Protection |
|---|---|---|
| **Q1 Network** (where possible) | dedicated boot/discovery VLAN; underlay and management as tagged VLANs that only the adopted node configures | reduces the attack surface, but is **not sufficient on its own** |
| **Q2 Cryptographic** (always) | control, gossip and tenant networks run exclusively in the WireGuard underlay with mTLS | a discovered node has neither a WireGuard key nor a certificate nor a gossip key – no access |

In a flat home network without VLANs, the cryptographic tier carries the requirement alone; from the "Standard/C5" operating profile on, the discovery VLAN is mandatory. In addition: the discovery image opens **no** inbound services. The discovery inbox is not part of the platform API but a small, fixed command set with size and rate limits and a cap on pending entries; every request is signed with the discovery key. Every unknown device is visible in the portal, optionally with an alert. The corresponding network rules are described on the [Network](network.html) page.

## Adoption

### Adoption types

| Type | Use | Minimum safeguard |
|---|---|---|
| **Manual** | homelab, individual devices | confirmation code if no TPM attestation is available |
| **Pre-registration** | data center, batch deliveries (delivery note, Redfish) | serial number **and** TPM EK or BMC origin; MAC alone not permitted |
| **Enrollment token** | notebooks, sites without portal access at the console | time-limited, counting token, stored only as a hash |
| **Adoption window** | "I'm plugging in four Pis now" – **homelab profile only** | time-limited, limited count, notification per adoption |
| **Rule-based (permanent)** | large environments | only with TPM attestation, hence only in a later phase |

A rule object describes attributes (model, memory, serial number list), the required evidence, validity period and maximum count, as well as the target (cell, roles, mode, labels, naming scheme). Creating permanent rules is a privileged operation. **Secure default state:** no active auto-adopt rule, manual adoption with confirmation code. An adoption via MCP **always** requires an additional confirmation on a platform page with passkey presence – this cannot be disabled.

### Protection against rogue nodes and man-in-the-middle

1. **Confirmation code (short authentication string):** the discovery agent and the inbox derive a short code from both public keys and random values – 6 digits by default, longer in the elevated profile. The node shows it on the console, the portal during adoption; the human enters the code read off the device. If it matches, this proves that the device in front of them is exactly this entry and nobody sits in between. On the platform side, an ephemeral one-time key that is never stored is used per report; if the handling node fails, the session is discarded and the device shows a new code.
2. **Headless devices:** code via the serial console, or alternatively enrollment token, pre-registration or adoption window.
3. **TPM attestation:** verification of the endorsement certificate against manufacturer CAs, binding of an attestation key and a PCR quote with nonce. Allows automatic adoption without humans – only in a later phase.
4. **Anomalies:** blocked fingerprints, MAC collisions, key changes during a confirmation or a conspicuously high number of reports trigger events and alerts. If the same identity appears at two endpoints simultaneously, **both** are quarantined (suspected clone).

### Adoption evidence and trust level

Two separate axes: the **adoption evidence** records once how reliably it is established that *this* device was the intended one (confirmed, token-bound, pre-registered or attested). The **trust level** (T0 to T4) describes the hardware-backed integrity of the running node; it is computed continuously, drops immediately and only rises with fresh evidence. **Placement and roles depend only on the trust level.** Details in the [Security model](security-model.html).

### Flow of a manual adoption

1. The new node boots the signed discovery image, generates an ephemeral discovery key, collects the inventory and reports to the inbox. It displays the confirmation code.
2. "1 node pending" appears in the portal. The operator adopts it with name, cell, roles, mode and code.
3. The platform checks code and policy, creates the node and generates a **one-time, short-lived provisioning credential**, encrypted to the confirmed discovery key.
4. The node fetches the adoption package (node URN, credential, region CA, boot profile) and installs the OS or starts diskless.
5. The installed OS generates its **long-term key** (TPM-bound where available) and its WireGuard key and sends a CSR together with the credential.
6. The cell CA issues the node certificate (7 days); the WireGuard key is published in the Raft state.
7. Only **then** does the node receive the gossip keys over mTLS, encrypted to its node key. It joins the cluster and takes on its roles.

This creates an unbroken chain discovery key → confirmation → credential → CSR → certificate, bound to a key generated on the device; **no private key is transmitted**. Certificates are renewed once half their lifetime has passed. The entire process is a single, traceable operation with steps and audit entries. If the node does not fetch the package within 30 minutes, the credential is discarded and the entry falls back to "pending".

**Diskless without a hardware anchor** must be confirmed again after every reboot and only receives the lowest trust level – suitable for stateless roles without sensitive tenant data.

### Roles after adoption

Roles from the adoption are activated after joining. The critical roles **control, witness, boot, identity and KMS are never assigned during adoption**, but only via role rules of the control group, subject to the minimum trust levels. Roles that format disks require a confirmation.

## Rejection, decommissioning, re-adoption, replacement

- **Rejection:** blocked hardware no longer receives a discovery image from the boot service; reports are discarded and counted. The block can be lifted. Rejection is non-destructive; the device was never written to.
- **Decommissioning:** after a pre-check of the impact, a control member is replaced first, then workloads and replicas are moved and all disks securely erased (NVMe Sanitize, ATA Secure Erase or crypto erase). The node delivers a **signed erasure certificate** per disk. Afterwards, the certificate is revoked, the WireGuard peer removed and – mandatorily – the **cell's gossip keys rotated**. If the node is defective and unreachable, revocation and rotation happen immediately; the operator confirms physical destruction afterwards, otherwise the entry remains flagged as open in the inventory.
- **Re-adoption:** a decommissioned device reappears as a discovery with a reference to the former node. Auto-adopt rules do **not** apply to it by default – protection against unintentionally reintegrating stolen or returned hardware. A re-adoption always creates a new identifier.
- **Reinstallation without identity change:** in case of a damaged OS or a switch between local and diskless, the installer boots from the network; the node authenticates via the re-certification path and keeps its identifier and URN, and the old certificate is revoked.
- **Replacement of defective hardware:** the old node is decommissioned, and a new node with a new identifier takes over name, labels, roles, cell and location; storage roles rebuild their replicas. If only the disks are moved into a new device, re-certification deliberately fails because the hardware fingerprint no longer matches.

## API overview

Resources are `Discovery` (with the actions `adopt`, `reject`, `unblock`), `AdoptionRule`, `EnrollmentToken` and `BmcEndpoint`; in addition there are the node actions `decommission`, `reprovision`, `replace` and a reboot with one-time network boot, confirmation of physical erasure, boot settings per region and node, offline import of artifacts and the network exploration for initial setup. All actions are long-running operations with pre-check, idempotency key and audit, and are available on equal footing in the API, [portal](portal.html) and MCP; destructive actions are marked accordingly in MCP.
