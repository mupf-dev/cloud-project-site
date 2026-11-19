title: Contributing and license
summary: How to contribute to BYOC, which licenses cover code and documentation, and how to report vulnerabilities.
toc: ja
de: mitmachen
---
## Contributing

BYOC (Build Your Own Cloud) is set up as a community project. The source code repository will be opened
as soon as the license files, security policy and REUSE compliance are complete. Until then,
we welcome feedback on concepts and architecture.

Especially welcome are:

- **Feedback on the concepts** in the [documentation](docs/index.html) – assumptions,
  gaps, better alternatives.
- **Operational experience** from homelabs, edge sites and data centers:
  hardware, network topologies, requirements from compliance audits.
- **Tests on unusual hardware** (ARM boards, older notebooks, servers with and without BMC),
  as soon as pre-release versions are available.
- **Code** in Rust for the agent, roles and tools, TypeScript for the portal, documentation and
  translations.

## Rules for contributions

- **DCO instead of CLA:** contributions are made under the
  [Developer Certificate of Origin 1.1](https://developercertificate.org/). Every commit carries a
  `Signed-off-by:` line (`git commit -s`). There is no transfer of rights to a company.
- **Quality before speed:** formatting, lints without warnings, tests,
  license and dependency checks, a security audit of the dependencies, SBOM and MSRV check
  run in CI and must be green.
- **No `unsafe`** without a justified entry in a dedicated register; new dependencies only
  centrally in the workspace and after checking license, maintenance status and process boundaries.
- **Every file carries SPDX license information** (REUSE-compliant).
- **Security-critical paths** – PKI, consensus, authorization, boot and discovery, update – require
  two reviews.
- **New features in all three access paths:** whatever works via the API must also work in the portal and via MCP;
  the parity check in CI enforces this.
- **Architecture decisions as ADRs** with the mandatory section "Security &
  Compliance" (see [Compliance by design](docs/compliance-by-design.html)).

```sh
# typical workflow for contributors (once the repository is opened)
cargo xtask setup      # install tools in pinned versions
cargo xtask ci         # run all checks locally
git commit -s -m "Short description"
```

## License {#license}

The license decision is justified in the [ADR License and governance](docs/license-governance.html)
(accepted 2026-11-12).

| Component | License |
|---|---|
| Core: agent, control plane, services, portal, MCP server, image build tools | GNU AGPL-3.0-or-later |
| SDKs, client libraries, CLI, API specifications, MCP schemas | Apache-2.0 OR MIT |
| Documentation, concepts, diagrams (including this website) | CC BY 4.0 |
| Code examples and configuration templates | MIT-0 |
| Logos and product name | not freely licensed, trademark policy |

The AGPL ensures that improvements to the platform benefit the community even when
modified versions are offered as a service over the network. Clients and SDKs are under
permissive licenses so that they can be embedded in any software. The license is
decided, but is subject to a final legal review before the first publication.

## Reporting a vulnerability {#security}

Please **do not use public issues, pull requests or discussions** for security problems.

- **Preferred:** GitHub *Private Vulnerability Reporting* in the project repository ("Security" tab →
  "Report a vulnerability").
- **Alternatively by e-mail:** the address, together with an OpenPGP key, will be defined before the first public
  release and also published at `/.well-known/security.txt`.

| Step | Deadline |
|---|---|
| Acknowledgment of receipt | ≤ 3 business days |
| Initial assessment (CVSS v4.0) | ≤ 7 calendar days |
| Status updates to reporters | at least every 14 days |
| Fix (target) | critical ≤ 14 days, high ≤ 30 days, medium ≤ 90 days |
| Publication | with the fix, at the latest after a 90-day embargo |

Actively exploited vulnerabilities are reported under Art. 14 of the Cyber Resilience Act. The
full process is described under [Vulnerability management](docs/vulnerability-management.html).

## About this website

This site is statically generated – without cookies, tracking, external fonts or third-party
scripts. Search runs entirely in the browser. The content consists of edited versions of the
project documents and is licensed under CC BY 4.0.
The site is available in German and English; where the two differ, the German version prevails.
