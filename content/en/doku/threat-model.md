title: Threat model
summary: Method and principles of the product risk analysis – STRIDE per trust boundary, assessment and treatment according to BSI Standard 200-3, abstract attacker models, security assumptions and maintenance of the model.
group: konzept
order: 110
quelle: Concept 67 (Threat Model)
de: bedrohungsmodell
---

The threat model is the **project's product risk analysis**. It assesses the software and its intended architecture, not a specific deployment. Operators carry out their own risk analysis for their information domain; the model is structured so that threats, controls and residual risks can be adopted as a **template** into an operator's ISMS. This page summarizes the method and principles; the controls themselves are found in the individual concepts, in particular the [security model](security-model.html) and [cryptography](cryptography.html).

## Method

Threats are identified using **STRIDE per trust boundary** and assessed and treated according to **BSI Standard 200-3**. The procedure:

1. **System model:** assets, data flows and trust boundaries.
2. **Attacker models and assumptions.**
3. **Threat overview:** STRIDE per boundary; each threat is mapped to at least one **elementary threat** of BSI IT-Grundschutz so that operators can import it into their 200-3 or Grundschutz++ tooling.
4. **Risk rating:** likelihood × impact, each gross (without) and net (with controls).
5. **Risk treatment:** avoid, reduce, transfer, accept.
6. **Consolidation** of new controls and remaining risks.
7. **Feedback** into the individual concepts and the development process.

STRIDE maps to the security objectives: *Spoofing* violates authenticity, *Tampering* integrity, *Repudiation* non-repudiation, *Information Disclosure* confidentiality, *Denial of Service* availability and *Elevation of Privilege* authorization. Cross-cutting concerns are software vulnerabilities, products from unreliable sources, operating errors, theft and malware.

### Rating scales

Ratings are made for a **"multi-tenant operation" reference profile** over a typical year of operation. Likelihood ranges in four levels from *rare* (requires rare capabilities or a chain of failures) to *very frequent* (normal operation creates the condition). Impact ranges from *negligible* to *existential* – the latter meaning cross-tenant loss of confidentiality or integrity, or the takeover of a cell, region or PKI. Together they yield one of four risk categories: low, medium, high, very high.

### Acceptance criteria

| Category | Handling |
|---|---|
| low | accepted |
| medium | accepted on condition that the effectiveness of the control is demonstrated (test, pentest) |
| high | release blocker unless explicitly accepted as residual risk |
| very high | never accepted – the architecture is changed |

A net risk only counts as reduced once the control is **implemented and tested**; until then the gross risk applies.

## Trust boundaries

The system model distinguishes thirteen trust boundaries, including: internet and users versus portal and API, AI clients versus the MCP interface, tenant versus tenant, tenant workload versus host, nodes among each other, the control group versus the remaining nodes, witnesses, discovery and boot network, out-of-band management, supply chain versus installation, operator versus tenant content, physical site, and external identity providers. For each boundary it is defined what crosses it and what enforces it.

## Attacker models

Attackers are modeled abstractly by starting position and capabilities:

- **External attacker** with access to public endpoints, from automated scans to targeted attacks.
- **Malicious tenant** with a valid account and arbitrary code in their own workloads.
- **Compromised node** with root privileges and that node's key material.
- **Foreign device in the discovery or home network** on the same network segment.
- **Physical attacker** with brief or permanent access to devices and disks.
- **Malicious operator or insider** – deliberately modeled as strong.
- **Compromised dependency or supply chain.**
- **Compromised or manipulated AI agent**, for example steered via prompt injection.
- **Third-party operator of an external witness.**

In addition, operating errors, hardware and power failures, and software bugs count as threat sources within the meaning of 200-3.

## Security assumptions and non-goals

The model rests on explicitly stated assumptions, including: the cryptographic primitives and random number generator used are secure; CPU, virtualization hardware and IOMMU work as specified; control nodes are physically protected or have TPM, measured boot and disk encryption; at most one voter of a cell is compromised at any one time (the consensus is not Byzantine fault tolerant); people control their authenticators; operators fulfill their obligations under the shared responsibility model; time is authenticated after boot.

**Non-goals** are protection against state-level attackers with hardware implants in new devices, protection of tenant content against operators with physical access without confidential computing, and defense against volumetric DDoS attacks on the internet uplink.

## Principles of risk treatment

- **Avoid** through architecture decisions that eliminate a threat – for example no shared kernel between tenants, no interactive login out of the box, no automatic break-glass, no destructive actions based on gossip messages, no security-critical roles at adoption, no automatic admission of foreign devices.
- **Reduce** through technical controls in the individual concepts.
- **Transfer** to operators (network separation, physical protection, firmware selection) or tenants (guest operating systems, their own applications) according to the shared responsibility model, documented in the operator and tenant handbooks.
- **Accept** only what is at most *medium* after reduction or has been explicitly taken on by the risk owner.

Guiding principles from the analysis: trust must **never arise from network boot**, but only from an adoption process bound to a device key with human confirmation or an allowlist; new nodes start at a lower trust level. Destructive actions by AI agents are confirmed **outside the client**, because prompt injection cannot be fully prevented.

## Maintaining the model

The model is updated when new roles, components or trust boundaries are added, when a third-party component is replaced, after pentest findings and security-relevant vulnerabilities, for new versions of the MCP specification, and at the latest before every minor release. It is maintained in machine-readable form so that CI can check that every threat has a control with a test or a documented acceptance. Every control with a net risk of *medium* receives at least one automated test or a pentest checkpoint.

Related pages: [BSI IT-Grundschutz](it-grundschutz.html) · [Compliance by design](compliance-by-design.html) · [Vulnerability management](vulnerability-management.html)
