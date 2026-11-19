title: Rust Stack and Core Libraries
summary: Architecture decision on the agent's Rust libraries – runtime, APIs, consensus, gossip, TLS, persistence, testing, supply chain, toolchain and licenses.
group: konzept
order: 20
quelle: Concept 03 (ADR Rust stack & core crates)
de: rust-stack
---

> Status: accepted (review 2026-11-12). Version information reflects the state as of November 2026; the project's locked dependency list is authoritative in each case.

## Context

**Rust** is settled as the implementation language. This architecture decision (ADR) defines **which libraries (crates)** form the foundation of the agent. The choice is long-lived: the async runtime, consensus, gossip, persistence and wire formats can only be replaced later with considerable effort.

The constraints follow from the [Vision](vision.html):

| Requirement | Consequence for the stack |
|---|---|
| One **agent** on every node (from a Pi with a small memory budget to a server) | Small memory footprint, a single statically linked binary, no JVM or Python runtime |
| **No central controller**; gossip for membership, Raft per cell | Mature Raft library with membership changes, learners and witness support; SWIM-style gossip up to about 1,000 nodes per cell |
| **API = portal = MCP** at every level | One source of truth (Rust types) → OpenAPI → generated portal client and MCP tools |
| **ARM64 and x86_64** mixed | All dependencies must build for both architectures; cross-compilation |
| **mTLS everywhere**, BSI TR-02102, C5, Cyber Resilience Act | Configurable TLS, in-house PKI, SBOM, vulnerability process |
| **Open source throughout** | OSI licenses only; make copyleft risks visible |
| Distributed logic must be correct | Deterministic simulation (network partitions, clocks, node failures) in CI |

## Decision at a glance

| Area | Decision | Fallback / alternative |
|---|---|---|
| Async runtime | **tokio** | – (de facto standard) |
| HTTP/REST | **axum** with tower, tower-http, hyper | – |
| Internal gRPC | **tonic** + **prost** | – |
| Consensus | **openraft** | raft-rs |
| Gossip / membership | **foca** (SWIM with Lifeguard ideas, I/O-free) | chitchat (Scuttlebutt) |
| TLS / mTLS | **rustls** with **aws-lc-rs** as the only crypto provider | – (`ring` and OpenSSL excluded) |
| Certificates | **rcgen** (generation), **x509-parser** (validation) | x509-cert |
| OpenAPI | **utoipa** (OpenAPI 3.1) | aide |
| JSON Schema | **schemars** | – |
| MCP SDK | **rmcp** (official SDK) | – |
| Local persistence | **redb** (Raft log, state machine, key-value) | SQLite for relational auxiliary data |
| Serialization | **serde**, serde_json, toml; **prost** on the wire; **postcard** for compact internal data | – |
| Netlink / WireGuard | **rtnetlink**; WireGuard via **defguard_wireguard_rs** (kernel WireGuard) | wireguard-uapi |
| Observability | **tracing** + **OpenTelemetry** (OTLP) | – |
| Error handling | **thiserror** in libraries, **anyhow** only in binaries/tests | snafu |
| Configuration | Own lean layer of serde + toml + environment variables | figment, config |
| CLI | **clap** (derive) with shell completions | – |
| Testing | **proptest**, **insta**, **cargo-nextest**, **turmoil** + Raft simulator, **loom** | madsim |
| Supply chain | **cargo-deny**, **cargo-audit**, **cargo-auditable**, **cargo-cyclonedx**, optionally **cargo-vet** | – |
| Cross-build | **cargo-zigbuild** or musl targets | cross |

## Rationale by area

### Runtime, REST and gRPC

**tokio** is the ecosystem standard; axum, tonic, rmcp, openraft and turmoil build on it. On Pi nodes, the number of worker threads is limited. io_uring-based runtimes (thread-per-core) are interesting for a future storage data path, not for the control plane.

**axum** is tower-based and shares its middleware with tonic. It integrates best with utoipa and with the MCP SDK, whose Streamable HTTP server is itself a tower service. actix-web brings its own runtime layer; dropshot (Oxide) is instructive as a model for "API-first with OpenAPI generation", but has a smaller ecosystem.

**tonic** is used for node ↔ node communication: Raft transport, forwarding requests to the control group, role agents. Protobuf schemas are language-neutral and versionable. **gRPC is not a public contract** – externally, the interface remains REST/JSON (see [API-first](api-first.html)).

### Consensus: openraft

| Criterion | openraft | raft-rs |
|---|---|---|
| Architecture | Async, event-driven, traits for storage and network, deterministic simulator | Core state machine only, synchronous, bring your own log/network |
| Features | Joint consensus, learners, leader transfer, pre-vote, lease reads, snapshot streaming | mature, but without I/O |
| Maintenance | very active | hardly any releases anymore |

openraft is tokio-native, ships many building blocks ready to use (membership, learners as a precursor to the witness, snapshots, configurable quorum rules) and includes a deterministic simulator. **Risk:** the chosen major version was brand-new at the time of the decision, and 0.x versions break APIs. Mitigation: Raft is encapsulated behind an in-house consensus crate, the version is pinned and every upgrade is checked beforehand with Jepsen-style simulation tests. How the witness is implemented in two-node operation is described on the [Control plane](control-plane.html) page.

### Gossip: foca

foca implements SWIM with parts of Lifeguard and incarnation numbers, is **I/O-free** and therefore ideal for deterministic simulation. Transport runs over the authenticated WireGuard underlay. This matches the principle "gossip only for membership, Raft for state". Bootstrapping before the underlay exists (discovery, adoption) deliberately does not use gossip, but the boot service and the adoption API. chitchat remains the fallback in case node metadata is to be distributed via gossip as replicated key-value state.

### TLS, mTLS and PKI

**rustls** is memory-safe and supports TLS 1.3 and hybrid post-quantum key exchange. **aws-lc-rs is the only permitted crypto provider**; `ring` (no PQ key exchange, duplicate maintenance) and OpenSSL (C dependency) are banned by the supply-chain checks. **rcgen** generates the internal PKI: cell CA, node certificates at adoption, short lifetimes, automatic rotation. Private keys are zeroed after use; TPM integration will follow later.

Alignment with BSI TR-02102 is complete: TLS 1.3 only, hybrid key agreement with ML-KEM preferred, secp curves permitted (Brainpool is not available in rustls/aws-lc-rs, which TR-02102 explicitly allows). Algorithms are never hard-coded, but selected via the active crypto profile (see [Cryptography](cryptography.html)).

### OpenAPI and MCP

**utoipa** generates OpenAPI 3.1 from attributes on handlers and types. To keep specification and code from drifting apart, the generated specification is checked in and compared via snapshot test; breaking changes are detected automatically. The generated OpenAPI file is the source for the portal client and the MCP tool catalog.

**rmcp** is the official MCP SDK with the stdio and Streamable HTTP transports. The MCP server runs inside the agent under the same HTTP server, with the same authentication and authorization as the REST API. **MCP tools are not handwritten** but generated from the OpenAPI description – otherwise parity cannot be maintained. Because of its high release frequency, the version is pinned and updated quarterly.

### Persistence and serialization

**redb** is used for the Raft log, the Raft state machine (desired state of a cell's resources) and local node state: pure Rust, ACID, crash-safe, simple. SQLite is additionally permitted for local relational auxiliary data (e.g. audit buffer, inventory history). sled is excluded because its development has stalled.

Raft log entries survive software upgrades, so an evolvable format (Protobuf) is preferred. Configuration files use TOML; the maintenance status of YAML libraries for Rust is currently unclear. bincode has been discontinued and is not used.

### Network, observability, errors, configuration, CLI

- **Network:** rtnetlink for links, addresses, routes and bridges; defguard_wireguard_rs for the underlay (kernel WireGuard is included in the [OS image](os-image.html)). Everything sits behind a trait abstraction so that tests run without root privileges. The overlay technology is not part of this decision (see [Network](network.html)). An LGPL-licensed WireGuard library was excluded because of the relinking problem.
- **Observability:** `tracing` as the sole instrumentation API, exported via OpenTelemetry/OTLP. The **audit log is separate** from this: its own append-only, signed format.
- **Errors:** typed errors in all libraries; mapping to API errors in RFC 9457 format in exactly one place.
- **Configuration:** the agent deliberately has **little local configuration** – most of it arrives as desired state via the API and Raft. Only bootstrap values are needed locally. Order of precedence: defaults → configuration file → environment variables → command line; unknown keys are rejected.
- **CLI:** two binaries – the agent `cp-agent` (subcommands for operation, bootstrap, diagnostics) and the user CLI `cpctl`, which uses **only the public REST API**, via a client generated from OpenAPI.

### Testing and deterministic simulation

Distributed logic – gossip events, Raft integration, reconcilers, the adoption flow – is structured so that **clock, randomness and network are injected**. This way an entire cell runs under turmoil with a fixed seed in a single process. Every failing seed found is checked in as a regression test. In addition: property-based tests (reconcilers, quotas, IP allocation), snapshot tests (OpenAPI specification, MCP catalog, error messages) and exhaustive concurrency tests.

Also **mandatory** are fuzzing for every parser at a trust boundary (netboot and discovery requests, certificates, API/MCP input, gRPC, metadata) with a nightly run, and a ban on `unsafe` code as the crate default; exceptions are justified and registered.

### Supply chain and Cyber Resilience Act

| Tool | Purpose | When |
|---|---|---|
| cargo-deny | License allowlist, banned crates, permitted C bindings, sources, advisories | every pull request |
| cargo-audit | RustSec advisories, also against shipped binaries | every pull request and daily |
| cargo-auditable | Embed the dependency list in the binary | every release build |
| cargo-cyclonedx | SBOM (CycloneDX) per binary | every release |
| cargo-vet | Audits of dependencies | from public releases onward |
| cargo-semver-checks | API compatibility of published libraries | release |

In addition: locked dependencies, reproducible builds, signed artifacts, update metadata following the TUF pattern and targeted SLSA provenance (see [Release signing](release-signing.html) and [Vulnerability management](vulnerability-management.html)).

## Workspace structure

The workspace separates binaries (agent, user CLI, simulation environment) from library crates with clear responsibilities: resource model and types, REST API, MCP server, generated client, internal RPC, consensus, membership, storage layer, PKI, network, reconciler framework, roles, audit log, telemetry, configuration and test helpers.

Guidelines:

- **One agent binary for all roles** – one image, one update path. Roles are runtime modules and can be disabled for minimal builds (e.g. a pure witness on a Pi Zero 2 W).
- **Strict layering:** the types crate depends on nothing internal to the project; roles know only interfaces, not the consensus or gossip library directly.
- **External components only across a process boundary:** Cloud Hypervisor, k3s, Garage and an optional Ceph driver are controlled as processes via API/CLI, never linked in as libraries. Each such process runs with its own user, minimal capabilities, systemd sandboxing, seccomp/Landlock and its own service identity. This prevents license mixing and creates clean update boundaries.

## Edition, MSRV and toolchain policy

- **Edition 2024** for all crates.
- **Build toolchain pinned**; bumps happen deliberately via change request, at most every six weeks and no earlier than two weeks after a stable release.
- **MSRV 1.95** at launch, driven by the WireGuard library. After that: MSRV at most "stable minus four releases" (about six months), checked in CI; MSRV-aware dependency resolution is enabled.
- The MSRV is primarily a signal to packagers; the project ships its own binaries anyway.

## Cross-compilation ARM64/AMD64

Targets are Linux on `aarch64` and `x86_64` (glibc); for the agent in the immutable OS, optionally fully static with musl.

| Tool | Assessment |
|---|---|
| **cargo-zigbuild** | Zig as linker/C compiler, selectable glibc version, no container needed – primary choice |
| cross | Container-based, robust for exotic C dependencies – fallback only |
| Native builds | on ARM64 and x86 runners in CI |

Simulation tests are architecture-independent; netlink and KVM integration tests run on real hardware (Pi 4/5, x86 nodes). C dependencies are minimized and controlled via an allowlist.

The release profile uses maximum optimization with link-time optimization, overflow checks even in release builds, and abort on panic: a panic should restart the agent via systemd rather than letting it keep running in a half-broken state. There is a size-optimized profile for witness and Pi Zero builds.

## License compatibility of the dependencies

The project license itself is decided under [License governance](license-governance.html). The risks of the chosen stack:

| License class | Affected | Risk | Measure |
|---|---|---|---|
| MIT / Apache-2.0 / ISC / BSD | Most of the stack | low; Apache-2.0 is incompatible with GPL-2.0-only | Collect NOTICE files per release |
| MPL-2.0 (weak, file-level copyleft) | foca, among others | Changes to their files must be disclosed | Use unmodified, upstream patches, allow explicitly |
| LGPL | a WireGuard library | Relinkability hardly achievable with static linking | excluded |
| AGPL (external) | Garage | Only across a process boundary → no derivative work; source offer when shipped in the image | Never as a library; source offer in the release process |
| C libraries | aws-lc, SQLite | uncritical, ship license texts | License report per release |
| Unmaintained | sled, bincode, YAML library, figment | Missing security updates (CRA) | Listed as banned |

## Rationale for the overall decision

1. **Ecosystem coherence:** tokio, tower and hyper connect REST, gRPC, MCP, Raft and simulation – one runtime, one middleware world, one TLS stack.
2. **Provable correctness without a central component:** consensus and gossip are decoupled from I/O or come with simulators. This is a prerequisite for the promises "2 nodes + witness survive a failure" and "no single point of failure from 3 nodes upward".
3. **Pi-capable:** pure Rust for persistence, gossip and consensus, few C dependencies, a single static binary.
4. **API-first technically enforced:** OpenAPI is produced from the same types from which the portal client and MCP tools are generated.
5. **Compliance:** memory-safe TLS, internal PKI, SBOM, advisory and license checks deliver evidence for CRA and C5 automatically.
6. **Maintenance status:** all selected libraries were active in 2026; the excluded ones are effectively unmaintained.

## Consequences

**Positive:** one binary, one runtime, one TLS stack; cross-build for both architectures without containers; deterministic simulation from the start; SBOM, license and advisory checks in every build.

**Negative / risks:**

- Several core dependencies are still 0.x and regularly break APIs → encapsulation in in-house crates, central version management, fixed upgrade windows.
- Gossip security depends on the underlay; there is no gossip before it is established, so the bootstrap path must work without it.
- The MSRV excludes older distribution toolchains (uncritical, since the project uses its own toolchain).
- The fast release pace of the MCP SDK and the MCP specification requires ongoing maintenance.
- Release builds with full link-time optimization are slow; development builds remain fast.

## Open points at the time of the decision

- Implementation of the witness in openraft (full voter with log, or log-less witness) – resolved in the [Control plane](control-plane.html) concept.
- Final choice between foca and chitchat – depends on whether SWIM broadcasts are sufficient for node metadata; load test with 1,000 simulated nodes.
- Allocator for musl builds (mimalloc or jemalloc).
