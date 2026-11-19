title: License and governance
summary: Why the DCP core is licensed under AGPL-3.0-or-later, which licenses apply to SDKs and documentation, how contributions work via DCO, and where the project stands under the Cyber Resilience Act.
group: konzept
order: 150
quelle: Concept 63 (ADR license and governance)
de: lizenz-governance
---

> **Note:** This page summarizes the project's current technical and licensing understanding and is not legal advice.
> The choice of license, the trademark and the CRA role will be reviewed by legal counsel before the first public release.

## Starting point

DCP is written mostly in Rust and integrates numerous third-party components under different licenses.
The goals:

- **Everything open source** – no mandatory "open core" components either (see [Vision](vision.html)).
- Operators – from homelabs through hosting providers and public authorities to corporate IT – should be able to **run the platform freely**.
- **No proprietary cloud fork** should emerge that keeps improvements to itself and sells them as a service.
- High acceptance among public authorities in the EU and among companies; as many external contributions as possible.
- The **EU Cyber Resilience Act (CRA)** is taken into account from the start.

### Licenses of dependencies

The most important third-party components – Cloud Hypervisor, Firecracker, Kata Containers, k3s, zot, Open vSwitch, Cilium – are
licensed under Apache-2.0 or BSD licenses. The Linux kernel (GPL-2.0) and iPXE (GPL-2.0-or-later) are shipped in the OS image and by the
boot role, respectively. The object storage building block Garage is licensed under AGPL-3.0. The policy engine Cedar (Apache-2.0) is
linked directly.

**Key observation:** As long as third-party components run as *separate programs* – across process, network or syscall boundaries –
the project is largely free in its own choice of license. There remain, however, **redistribution obligations** (source code, license texts, NOTICE) for the
shipped OS image. Only **linking** copyleft code would restrict the project's own license – and the project's
process-boundary rule rules that out (see [Rust stack](rust-stack.html)).

## Decision drivers

| Driver | Weight |
|---|---|
| Protection against proprietary forks, especially the **SaaS loophole** (operation as a service without redistribution) | high |
| Acceptance among public authorities and companies, procurability | high |
| Patent protection (explicit patent license, patent retaliation clause) | medium |
| Compatibility with dependencies | high |
| Willingness of individuals and companies to contribute | medium to high |
| Operator freedom: operation without fees or permission, including commercially | must |
| Legal certainty (clarity, track record, EU law) | medium |

## Options evaluated

| License | Type | SaaS loophole closed? | Assessment |
|---|---|---|---|
| Apache-2.0 | permissive | no | standard in cloud native, maximum adoption – but offers no protection against exactly the scenario to be prevented |
| MPL-2.0 | weak copyleft (file level) | no | copyleft only on redistribution and only for modified files |
| GPL-3.0 | strong copyleft | no | pure network operation is not redistribution |
| **AGPL-3.0** | strong copyleft with network clause | **yes** | the only widely proven license that closes the SaaS loophole; common in infrastructure |
| EUPL-1.2 | strong copyleft, EU license | largely | attractive to public authorities, but little case law, no patent retaliation, compatibility clause can weaken protection |

The experience of other projects (Elasticsearch, Redis, HashiCorp) shows that permissive or weak licenses later led
to license changes and rifts with the community there. The price of the AGPL: some companies with internal AGPL bans will
contribute less, and admission to the CNCF is practically ruled out.

### What the AGPL means for operators

- **Unmodified operation** – including commercially, as a hosting provider or as a public authority: no obligations beyond passing on the
  license texts.
- **Your own modifications used by tenants over the network** (API, portal, MCP, S3): users must be offered the source code of the
  modified version.
- **Internal modifications without external users:** no obligation.

To make this effortless, the platform includes a built-in **source code endpoint** – in the API, portal and MCP. It
automatically points to the repository and the exact commit or build of the running version. Operators with their own patches only enter
the address of their fork. Compliance thus becomes a side effect.

## Decision: the license matrix

Adopted on 2026-11-12:

| Component | License | Rationale |
|---|---|---|
| **Core:** agent, control plane, services (VM, container, Kubernetes, storage, network), portal, MCP server, image build | **AGPL-3.0-or-later** | closes the SaaS loophole, patent clause, suitable for public authorities |
| **SDKs, client libraries, CLI, OpenTofu provider, API specifications, MCP schemas** | **Apache-2.0 OR MIT** | clients should be embeddable in any software – including proprietary software |
| **Documentation, concepts, diagrams** | **CC BY 4.0** | free reuse with attribution, e.g. for training courses or public-authority handbooks |
| **Code examples, templates, boot scripts, configuration examples** | **MIT-0** | can be copied without conditions, including into GPL-2.0 contexts |
| **Build tools** | Apache-2.0 OR MIT | same as SDKs |
| **Own kernel modules or eBPF programs** (if needed) | GPL-2.0-only OR BSD-2-Clause | required by the kernel; dual license |
| **Patches to third-party projects** | upstream license | upstream as a rule, no long-lived forks |
| **Logos, product name** | no free license – trademark policy | protection against confusion caused by forks |

**EUPL-1.2** remains an option under review until the first release. The AGPL is the more robust starting point: AGPL code can
incorporate EUPL code, but not the other way around. **"or-later"** allows an upgrade to a future AGPL version without
assignment of rights.

### Technical implementation

- **REUSE specification:** SPDX header in every file, central license directory, automated checks in CI.
- **License allowlist for dependencies** (MIT, Apache-2.0, BSD, ISC, Zlib, Unicode-3.0 and others), checked with `cargo-deny`. SDK crates
  must not pull in copyleft. LGPL libraries are not linked. **MPL-2.0** is allowed only for pure build tools
  that do not end up in the shipped artifact – it remains excluded at runtime.
- **SBOM** (CycloneDX and SPDX) for every release and every OS image – also a CRA requirement (see
  [Release bundle](release-bundle.html)).
- **Source code offer for the OS image:** for every image, a complete source archive or permanent references to identical
  sources.
- The license boundary between core and SDK is visible in the crate layout.

### Special cases

- **Garage** is accessed exclusively as a separate service via the S3 or admin API. Own patches are upstreamed.
- **iPXE** is shipped as a binary, so the license text and source code are included. Scripts are loaded at runtime where possible
  instead of being compiled in.
- **Linux:** the agent uses only syscalls, Netlink and ioctl – no derivative work.
- **Identity:** a dedicated authorization server is part of the core; external identity providers are connected only via OIDC
  federation, so their license is irrelevant (see [Identity and access](identity.html)).

## Contributions, trademark, governance

### DCO instead of CLA

| | DCO | CLA |
|---|---|---|
| Effort for contributors | sign-off in the commit, no contract | contract, often involving the employer |
| Relicensing by the project | not possible (only "or-later" upgrade) | possible – including toward proprietary |
| Community trust | high | lower, especially with copyleft plus CLA |

**Decision: Developer Certificate of Origin (DCO 1.1)**, enforced by a CI check of the sign-off. No CLA. This way the
project credibly commits to **never relicensing as proprietary** – the strongest argument for contributors and a
counterweight to skepticism about the AGPL.

### Trademark

Licenses govern copyright, not trademarks. The product name is the most important means against confusing forks with
proprietary add-ons. A trademark policy is planned: unmodified builds and distributions may use the name,
modified forks only as "based on …", and compatibility claims require passing **conformance tests** (comparable
to Kubernetes Conformance). The alpha name is *Das Cloud Projekt* (short *DCP*); components carry the prefix `cp` (e.g. `cpctl`, `cpOS`, `cp-agent`). Technical identifiers such as API groups keep the spelling `cloud-project` for now.

### Governance model

The organizational setup (legal entity, bodies) has deliberately not been decided yet. A
staged model serves as orientation:

| Phase | Trigger | Model |
|---|---|---|
| Founding | until the first releases | core maintainers; transparent decisions via ADR, public roadmap |
| Opening | several active maintainers from independent organizations or first major production deployment | steering committee with a limited number of seats per organization, working groups (compute, storage, network, security) |
| Neutral entity | trademark, infrastructure and donations require a neutral legal entity | foundation or registered association; the steering committee remains the technical body |

A possible neutral entity would be, for example, a European open source foundation that already has experience with copyleft and with the
steward role under the CRA.

A **Code of Conduct** based on the Contributor Covenant applies to all channels, with a confidential reporting channel.

### Security policy

The security policy also serves as the basis for the CRA (see
[Vulnerability management](vulnerability-management.html)):

- Confidential reporting channel, acknowledgment of receipt within 72 hours, standard embargo of 90 days, shorter in case of active
  exploitation.
- A security response team with a deputy arrangement.
- CVE assignment, machine-readable advisories (CSAF 2.0, OSV) and VEX statements on vulnerabilities in dependencies.
- Advance notification of registered operators and distributors under confidentiality rules.
- **Supply chain:** signed releases and images, SLSA provenance, reproducible builds as a goal, OpenSSF Scorecard (see
  [Release signing](release-signing.html)).
- Published supported versions and support periods per release line.

## Position under the Cyber Resilience Act

### Timeline

| Date | What applies |
|---|---|
| December 2024 | CRA entered into force |
| 2026-09-11 | reporting obligations for manufacturers: actively exploited vulnerabilities and severe incidents (early warning 24 h, notification 72 h) |
| 2027-12-11 | full application: essential requirements, conformity assessment, CE marking, obligations of open source stewards |

Views differ on when the reporting obligation takes effect for open source stewards; most sources name 2027-12-11.
The project sets up its processes as if the obligation already applied – the effort is equivalent to good security practice.

### Roles

| Constellation | CRA role | Consequence |
|---|---|---|
| Community develops without profit motive, without a legal entity | outside the scope | no obligations |
| Legal entity supports development systematically and sustainably, without monetization | **open source steward** | "light" regime, no fines |
| Provider sells a product, distribution, appliance or support beyond cost recovery | **manufacturer** | full regime |
| Hosting provider runs the platform as a service | CRA does not apply to pure service operation; NIS2 instead | operator compliance |
| Public authority runs it internally | neither manufacturer nor steward | BSI IT-Grundschutz or NIS2 |

### Obligations as open source steward

1. A **documented cybersecurity policy** that promotes secure development and the handling of vulnerabilities –
   implemented via the security policy and the security handbook.
2. **Cooperation with market surveillance authorities** on request.
3. **Reporting obligations**, insofar as the project is involved – for example in incidents affecting the project infrastructure (repositories, build,
   release signing).
4. Voluntary: a **security attestation** that makes due diligence easier for manufacturers.

### Later commercial offerings

- **Monetization makes you a manufacturer.** Donations without a profit motive are harmless.
- **Product classes:** the platform contains components of Class I (operating systems, boot managers, identity and
  access management, network management, PKI) and **Class II** (hypervisors, container runtimes). Class II generally requires
  a third-party conformity assessment. For **free and open source** products, however, internal control suffices if the technical
  documentation is **public**. That is why the technical documentation is kept public from the start.
- Manufacturer obligations include security by design, secure defaults, updates, SBOM, vulnerability management,
  support period, declaration of conformity, CE marking, reporting obligations and due diligence for integrated third-party components.
- In addition, the new **Product Liability Directive** applies, under which software is a product.
- **Recommended separation of roles:** the steward is a non-profit entity that sells nothing. Commercial offerings such as support,
  hardened long-term versions or appliances are taken on by separate companies as manufacturers of their respective products. The
  steward processes (SBOM, advisories, public documentation, attestation) are designed so that every manufacturer can use them directly for
  its own conformity.

A warranty disclaimer in the AGPL or Apache license does not override statutory manufacturer obligations.

## Consequences

**Advantages**

- No proprietary cloud fork without disclosure of the source code; improvements flow back.
- Permissive SDKs and clients – no barrier for users, tooling and integrations.
- DCO without CLA is a credible promise against later relicensing.
- The steward role is prepared early; the public documentation takes advantage of the relief for open source products.

**Disadvantages**

- Parts of the industry with AGPL bans participate less.
- A license change after release is hardly possible – this is intentional.
- Operators with their own modifications must maintain the source code offer; the built-in source code endpoint mitigates this.
- Multiple licenses in the repository require discipline (REUSE, license checks, clear crate boundaries).
