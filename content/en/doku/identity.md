title: Tenants, Identity and Access
summary: Hierarchy of platform, tenant and project, identity types, sign-in with passkeys and OIDC federation, a hybrid authorization model combining a relationship graph and Cedar, tenant isolation, quotas, lifecycle and recertification.
group: konzept
order: 70
quelle: Concept 07 (tenant, identity and access model)
de: identitaet
---

## Overview

The platform is multi-tenant from the ground up. This concept defines **who** acts in the platform (identities), **how** these identities prove who they are (authentication), **what** they are allowed to do (authorization), and how tenants are isolated from each other and from the operator across all technical layers.

### Key decisions

| Topic | Decision |
|---|---|
| Hierarchy | **platform → tenant → project → resource**; the tenant *is* the organization; optional folders, not part of the URN |
| Identity service | own lean OIDC/OAuth 2.1 server in Rust, **passkeys first**, plus federation with customer IdPs |
| Tokens | short-lived, sender-constrained, validated **locally**; they carry **identity, not permissions** |
| Authorization | own relationship store (Zanzibar-style) **plus Cedar** as an embedded policy language |
| Operator and tenants | operator roles see metadata, never content – except via a logged access request |
| Lifecycle | deletion with **crypto erasure** and a signed deletion certificate; export at any time |

## Hierarchy

The comparison with AWS, Azure and GCP yields three lessons: if the identity boundary and the isolation boundary diverge, the model becomes hard to understand – hence **the tenant is both**. Hierarchical guardrails are indispensable for large customers – hence **guardrails at every level**. Names in paths that break during reorganization are costly – hence **folders are not part of the URN**.

### Levels

| Level | Purpose | Example URN |
|---|---|---|
| Platform | operator, global policies, tenant management | `cp:global:platform` |
| Region / cell / node | infrastructure, operator only | `cp:eu-hl1:cell/c1` |
| **Tenant** | the customer's organization with its own IdP, its own keys and its own billing | `cp:global:tenant/acme` |
| *Folder (optional)* | grouping of projects, inheritance of permissions and guardrails | separate resource, not a prefix of the project URN |
| **Project** | resource, quota and permission boundary, location binding | `cp:global:tenant/acme/project/shop` |
| Resource | VM, volume, bucket … | `cp:eu-hl1:tenant/acme/project/shop/compute/vm/web-01` |

Project names are unique per tenant; moving a project between folders only changes a relationship, never the URN. Every project carries a list of **allowed regions** – the basis for data residency. An additional "organization" level was rejected because it would be superfluous for the vast majority of users (homelab, SMEs) and would raise the question of which level is the isolation boundary. For resellers and hosting providers, a grouping of tenants with delegated partial operator permissions is planned for later – without access to tenant content and without URN changes. The URN conventions are described under [API-first](api-first.html).

## Identities

### Principal and actor

Every request carries two pieces of information: the **principal** is on whose behalf and with whose permissions the action is taken; the **actor** is who technically acts (portal, CLI, AI client, reconciler). The audit log stores both separately.

| Type | Home | Sign-in | Typical lifetime |
|---|---|---|---|
| Human (operator) | platform | passkey (mandatory), optionally federated | session 8–12 h, access token 10 min |
| Human (tenant) | tenant | passkey/MFA locally **or** federated (OIDC/SAML) | as above |
| Group | tenant / platform | local or synchronized from the IdP or via SCIM | – |
| Service account | project | workload identity, federation, API key | token 5–60 min, key at most 1 year |
| Workload (VM, container, pod) | resource | platform attestation via placement | 5–15 min, renewed automatically |
| Node | region | mTLS with a cell CA certificate | certificate 7 days, rotated |
| AI agent (actor) | MCP client or service account | OAuth 2.1 | at most 1 h |
| Break-glass | platform | offline hardware key + recovery shares | one-time, at most 4 h |

### Humans and groups

Users exist **per tenant**; the same person in two tenants has two identities. This avoids cross-references between tenants and follows the principle of data minimization. Groups are local or mirrored from the external IdP and may be nested. The mandatory attributes are minimal; the e-mail address is marked as personal data, and the last sign-in is used for inactivity checks.

### Service accounts and workload identities

Workload identities follow the SPIFFE model: paths within a trust domain mirror the URN. Infrastructure and workload paths are firmly bound to **separate certificate authorities**; workloads only receive the trust bundle of the workload CA, and their identities are always rejected at infrastructure interfaces.

- A service account is assigned to a VM, container instance or Kubernetes cluster. This requires a dedicated permission ("actAs") – so nobody can escalate their permissions by starting a VM with a more powerful service account.
- **Tokens are issued by the agent of the host node** that verifiably placed the workload – the placement in the control plane is the attestation. VMs preferably receive them via virtio-vsock, container instances as a rotated file, Kubernetes clusters via token projection and OIDC federation.
- Each host signs with its **own short-lived issuer key** (24 h), bound to the node identifier. Verifiers require that this key belongs to exactly the node on which the workload is supposed to run. A compromised node therefore cannot mint tokens for other workloads.
- **Inbound federation:** external issuers (CI systems, third-party Kubernetes clusters) are registered on the project; their OIDC tokens are exchanged via token exchange (RFC 8693) for a short-lived platform token, subject to conditions on their claims. This way, automation needs no static secrets.

### Nodes

During [adoption](boot-adoption.html), nodes receive a cell CA certificate with their immutable identifier. They are **not** principals for tenant operations, but act with narrowly scoped permissions for the reconcilers – for example, only writing the status of the resources placed on them. A compromised node therefore affects at most the tenants running on it. Trust levels and attestation are described in the [Security model](security-model.html).

### AI agents via MCP

AI agents are a separate actor type in two variants:

1. **Delegated:** a human authorizes an MCP client (OAuth 2.1 with PKCE). The token carries the human as principal and the agent as actor, with restricted scopes (read, write, destructive).
2. **Autonomous:** a service account with actor type "agent", for example a nightly capacity planner. Destructive actions then only run after approval by a human; irreversible actions, privileged IAM changes, the adoption of nodes and the assignment of critical roles are forbidden for autonomous agents.

What effectively applies is the **intersection** of principal permissions, token scopes and agent guardrails. Guardrails are deny rules at platform or tenant level, such as "AI agents may never grant IAM permissions or delete keys". Chained delegation is allowed, but is fully audited and limited in depth.

### Break-glass

An emergency account with access **outside the IdP** (hardware key in a safe plus recovery key, optionally split among several people) works even if the identity service fails completely. It grants time-limited operator admin permissions, but **no** access to tenant content; every use triggers an alert, a post-incident review and rotation.

## Authentication

### Own identity service plus federation

Embedding Zitadel, Keycloak or Kanidm would have meant a second central data store, partly missing Pi suitability, license risks and duplicate maintenance of the tenant model; pure federation would not allow operation without an external IdP. The chosen approach combines an **own, deliberately narrow authorization server** with **federation**:

- OIDC/OAuth 2.1 with authorization code + PKCE, refresh, client credentials, token exchange, device authorization (for the CLI on devices without a browser), discovery, JWKS and protected resource metadata for MCP.
- Local sign-in **with passkeys only** by default; passwords are optional and disabled.
- **Federation broker** per tenant to any customer IdP via OIDC or SAML, with group mapping and SCIM 2.0 provisioning.
- **No** full-blown customer identity management with registration flows or social logins – anyone who needs that federates a specialized IdP. Zitadel, Keycloak or Kanidm are first-class external IdPs for this purpose.

The in-house implementation is safeguarded by the OpenID conformance suite in CI, fuzzing of the parsers and an external audit before general availability.

### MFA, passkeys, step-up

- **Passkeys first** (WebAuthn); for operators and privileged roles, device-bound, attested keys can be enforced.
- MFA is mandatory for all privileged roles. With federation, the platform checks whether the external IdP asserts MFA; if that evidence is missing, it requires its own passkey as a second factor.
- **Step-up:** irreversible actions and changes to privileged roles require a fresh sign-in (at most 10 minutes old), regardless of channel. Via MCP, the human confirms such actions on a **platform page** that renders the impact report itself and requires passkey presence. The confirmation is bound to all parameters and valid only once. Tenants may tighten this requirement, but not disable it.
- Progressive lockouts after failed attempts and notification about new devices.

### Tokens

- **Access tokens** as JWT per RFC 9068, signed with ES256 (in the compatible crypto profile also Ed25519), lifetime of 10 minutes for humans, audience is a specific endpoint.
- **Sender constraining** with DPoP for CLI, SDKs and MCP clients, mTLS for workloads; the portal uses an HttpOnly cookie session.
- **No roles, groups or permissions in the token** – they are determined on every request from the current permission state. Revocation takes effect immediately, and the token stays small.
- Refresh tokens rotate and are bound to the session; reuse revokes the session.

**API keys** exist only for service accounts, never for humans. They carry a recognizable prefix for secret scanners, are stored only as a hash, have a mandatory expiration (default 90 days, at most one year) and can be restricted to scopes, source networks and projects. The recommendation is to exchange them for a short-lived token; tenants can forbid API keys entirely by policy.

### Decentralized behavior during outages

Every node holds the public keys of all issuers and the revocation list, replicated locally. An ingress node validates the token and forwards the request to the responsible cell; that cell **validates the original token including the DPoP proof itself** and never trusts a user context created by the ingress node.

| Outage | Behavior |
|---|---|
| A region's identity service unreachable | existing tokens remain valid until they expire; new sign-ins fail with a notice in the portal; the host continues to issue workload tokens |
| A tenant's external IdP fails | no new federated sign-ins; existing sessions run until their maximum duration; optionally local emergency admins of the tenant |
| Cell without quorum | reads marked as "stale", permission changes not possible (fail-closed) |
| Signing key compromised | rotation, the old key disappears from the JWKS; short exposure thanks to 10-minute tokens |

Multiple identity nodes each sign with their **own** key under a common issuer; all public keys reside in the replicated state. This way, no key transport is needed, and ongoing sign-ins, codes and sessions work across node boundaries. Session revocation reaches all nodes of a region within a few seconds. At the very first start (without an IdP), a one-time token sets up the first operator admin including a passkey; this bootstrap access is automatically disabled after the first successful passkey sign-in.

## Authorization

### Requirements

Role-based permissions along the hierarchy, **relationships across the hierarchy** (sharing an image with another project, VPC peering, folder membership), conditions (channel, actor type, MFA freshness, labels, time of day), **guardrails where denials take precedence**, decentralized evaluation in under a millisecond without an external service, explainability ("Why am I allowed to do this?") and analysis ("Who has access to X?") – and consistency: after a permission is revoked, no older view may grant access anymore.

### Options

OpenFGA, Cedar, OPA/Rego, SpiceDB and an own Zanzibar-style core were compared. OpenFGA has the most suitable model, but the wrong operational form: a separate service with its own database. Cedar is ideal as an embedded policy language, but does not itself model large relationship graphs. A purely home-grown policy system would be expensive and hard for auditors to follow.

### Chosen: relationship store plus Cedar

1. **Graph resolution in the own Rust core:** relationships are stored as tuples "object#relation@subject", such as group memberships, folder membership or shares. Role bindings are special tuples. The type schema is **derived from the API schema**; there is no second model to maintain.
2. **Cedar evaluation:** using the supplied slice (principal with groups, target resource with ancestors and labels, effective roles), Cedar evaluates a policy set: generated permits per role, deny guardrails from all levels and optional conditions on role bindings.
3. **Result with justification** stating which binding allowed or which rule denied – for the audit and for the API operations "test permissions" and "explain access".

Authorization takes place **at the destination**: the responsible cell decides. Each cell holds a read replica of the permissions of the tenants that have resources in it. Ingress nodes use a permission cache only for the user interface (hiding buttons, tool lists in MCP), never for the actual decision. **Permission revocations are replicated synchronously** to all affected cells before the operation counts as complete; grants may be asynchronous. If a cell fails, nobody decides about its resources on its behalf.

### Permissions and roles

Permissions follow the scheme `<api-group>.<resources>.<verb>`, for example `compute.vms.create` or `iam.roleBindings.create`. Every API operation declares exactly one permission and one **data class**: `metadata`, `content` (volumes, objects, consoles, workload logs, secret values), `iam`, `billing` or `audit`.

| Role | Scope | Core |
|---|---|---|
| Operator admin | platform | infrastructure, nodes, tenants, quotas – **no** content permissions |
| Operator reader / security / billing | platform | reading, audit and access requests, consumption |
| Tenant admin | tenant | everything in the tenant including IAM and IdP; MFA mandatory |
| Project owner / editor / viewer | project or folder | graded permissions; viewer without content, e.g. for AI agents |
| Auditor, security, billing | tenant | audit and reports, guardrails and recertification, consumption |
| Service roles | project / resource | fine-grained for service accounts |

Tenants can build **custom roles** from permissions they themselves hold. Incompatible role combinations (separation of duties, e.g. admin and auditor for the same person) trigger a warning or are rejected. New members receive no default role, service accounts start without permissions, and instead of permanent admin bindings there are **just-in-time elevations** with an expiration and optional approval. Root-level access on nodes is a separate permission that is not contained in any predefined role and is only granted to named individuals.

## Tenant isolation across all layers

Principles: the **tenant is the hard boundary**, the project the soft one. Every request is checked at the destination against the tenant of the target URN. Default-deny applies, and isolation results from technology (cryptography, kernel and hypervisor boundaries), not just from checking code. Errors, lists, metrics and logs contain no data belonging to other tenants.

| Layer | Isolation |
|---|---|
| API / control | tenant from the URN, authorization at the destination, filtered lists, rate limits and quotas per tenant |
| Identity | users, groups, IdPs and verified domains per tenant |
| Network | own VPCs, no L2 adjacency – not even within a VPC (see [Network](network.html)) |
| Compute | VMs and container instances only with MicroVM isolation, no shared kernel between tenants; optionally dedicated nodes |
| Storage | encryption per volume and bucket with a tenant key hierarchy, namespaces per tenant (see [Storage](storage.html)) |
| Keys | one key encryption key per tenant as the root of crypto erasure, optionally BYOK/HYOK (see [Cryptography](cryptography.html)) |
| Logs / audit | separate audit chains per tenant; workload logs are tenant content |

### Operator and tenant data

The operator is a data processor. **No operator permission carries the data class `content`**, and a platform guardrail forbids content access without a valid approval. Metadata is restricted too: names, labels and descriptions of tenant resources appear pseudonymized in operator views by default. This restriction is enforced at the API level; without confidential computing it does not protect against root or physical access to a host. This is disclosed openly to tenants, and interactive sessions on nodes are recorded, audited and visibly flagged on the node.

**Access requests (`AccessRequest`):** if the operator needs content access – for example to a VM's serial console – they file a request with justification, scope, legal basis and duration. By default, the tenant **and** operator security must approve (four-eyes principle). In case of a legal obligation or an emergency without tenant approval, a documented basis, subsequent notification and a mandatory review are required. For the duration, a narrowly scoped, time-limited binding is created; every action appears in the **tenant audit**. Tenants can reject consent-based requests entirely by policy.

**Guardrails** exist at every level: at platform level, for example, "no content access" or "MFA mandatory for admins"; at tenant, folder and project level, for example, "no public IPs in production" or "AI agents read-only". Guardrails are API resources, can be validated in advance and checked for contradictions through analysis.

## Quotas and limits

The operator sets quotas per tenant (vCPU, RAM, storage, public IPs, GPUs, projects), and the tenant admin distributes them across folders and projects. In addition, there are limits for IAM objects and API rate limits per principal, channel (stricter for MCP) and tenant. Quotas reside in the region's Raft state; cells receive **pre-allocated quota slices** so that resources can be created without region-wide coordination. Exceeding a quota returns a clear error, and a dry run shows the impact in advance. Increases are filed as a request and approved by the operator or automatically up to a threshold. Budgets and warning thresholds are separate from hard quotas.

## Lifecycle

A tenant passes through the states **Provisioned → Active → (Suspended) → Terminating → Deleting → Deleted**.

| Phase | Effect |
|---|---|
| Provisioning | tenant key, audit chain, default guardrails and the invitation of the first admin are created automatically; the operator receives **no** role in the new tenant |
| Suspended | graded: read-only, workloads stopped, or sign-in only for export and audit; reason visible in the tenant audit |
| Termination | changes locked, export still possible, restoration within the grace period (default 30 days) |
| Export | at any time: resource definitions (re-importable), IAM configuration, signed audit log, content in standard formats |
| Deletion | stop workloads → destroy tenant key (**crypto erasure**, also effective in backups) → physical release → delete IAM objects → close audit chain |
| Deletion certificate | signed certificate with timestamps, destroyed key identifiers and affected storage areas; audit entries are pseudonymized after a retention period, not deleted |

Projects have a simplified lifecycle with a soft-delete period and deletion protection. Users are invited via a one-time link; for federated users, the external IdP is authoritative – deactivation via SCIM revokes access immediately, and without SCIM, prolonged inactivity locks the account.

## Recertification and audit

**Recertification campaigns** are API resources per tenant, project or platform. Privileged roles and operator roles are reviewed every 90 days by default, all others every 180 days. Aids include the last use per binding, suggestions for shrinking roles, orphaned service accounts and separation-of-duties violations. Unconfirmed bindings are removed automatically after a deadline; the result report can be exported in signed form. AI agents may prepare campaigns, but only humans decide.

In addition to all changes, the **audit** records sign-ins, step-ups, token issuance and exchange, IAM changes with justification, authorization denials (aggregated), the full history of access requests, break-glass use, diagnostic sessions and lifecycle events. Audit **cannot be disabled**; tenants can only extend retention. The operator sees the platform audit, not the tenant audit – except for entries concerning the operator's own actions.

All IAM objects are ordinary API resources and can be used on equal footing in the API, portal and MCP (see [Portal](portal.html)). In addition, there are helper operations for testing permissions, explaining a decision and listing all principals with access. The mapping to ISO 27001, C5 and GDPR is described under [Compliance requirements](compliance-requirements.html) and [Compliance by design](compliance-by-design.html).
