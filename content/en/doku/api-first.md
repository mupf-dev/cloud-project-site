title: API-first – API, Portal and MCP as Equals
summary: Why every function is first an API operation, how resources and operations are structured, and how the portal and MCP are derived from them and checked for parity.
group: konzept
order: 30
quelle: Concept 04 (API-first principle)
de: api-first
---

## Principle

> **Every platform function is first and foremost an API operation. The portal and MCP are two further representations of the same operation – never their own logic, never their own state.**

This applies without exception at every level (see the glossary in the [Vision](vision.html)):

| Area | Levels | Examples |
|---|---|---|
| Operator | Platform → region → cell → node | Initial setup, adoption, assigning roles, drain, decommissioning, updates, creating cells |
| Tenant | Tenant → project → resource/service | Users, roles, quotas, VM, volume, VPC, bucket, Kubernetes cluster |
| Special cases | Bootstrap, adoption | First node without an identity service; approval of pending hardware |

**The API is the single source of truth:**

- The *desired state* of every resource exists only in the API and is stored in the control group of the responsible cell or region (see [Control plane](control-plane.html)). Apart from UI and session data, the portal and MCP hold no state of their own.
- The **API schema** is the sole definition of resources, fields, validation, permissions and documentation. Portal forms, MCP tools, the CLI, SDKs and the future OpenTofu provider are derived from it.
- There is **no side channel**: no portal-only switches, no configuration file on nodes that bypasses the API, no SSH by default. Emergency and diagnostic access are also API operations with special auditing: time-limited, justified and recorded diagnostic sessions and – only for the highest operator tier – SSH exclusively with short-lived certificates.

### Rationale

1. **Otherwise parity cannot be maintained.** Three hand-maintained access paths drift apart; ones generated from a single schema do not.
2. **Decentralization.** Without a central controller, every node must serve the same interface – this is only possible if it is generated generically from the schema and embedded in the agent.
3. **Compliance.** A single enforcement point for authentication, authorization, validation and the audit log (ISO 27001 A.8.15/A.8.16, BSI C5 OPS-10 ff., IT-Grundschutz OPS.1.1.5) instead of three.
4. **Automation.** Infrastructure as code, GitOps and AI agents are first-class citizens.
5. **Testability.** Every function can be tested without a browser; portal and MCP tests only verify the mapping.

## Resource model

The model is based on the Kubernetes API Conventions and the Google AIPs (resource-oriented design) – without using Kubernetes as its foundation.

### Structure of a resource

Every resource consists of three parts:

- **`metadata`**: name (chosen by the user, unique within the parent), immutable `uid` (UUIDv7, never reused), URN, parent, labels (selectable) and annotations, `generation` (incremented on every change to the desired state), `resourceVersion` for optimistic concurrency, timestamps, finalizers and owners.
- **`spec`**: the desired state – written by the user.
- **`status`**: the actual state – written only by the system, via a dedicated subresource that is open only to reconcilers. `observedGeneration` and `conditions` show whether the desired state has been reached.

An abbreviated example:

```yaml
apiVersion: compute.example.com/v1alpha1
kind: VirtualMachine
metadata:
  name: web-01
  urn: cp:eu-hl1:tenant/acme/project/shop/compute/vm/web-01
  labels: { env: prod }
  generation: 7
spec:
  machineType: small-2c-4g
  arch: any            # arm64 | x86_64 | any
  network: { vpc: default, subnet: web }
status:
  phase: Running
  observedGeneration: 7
  conditions:
    - type: Ready
      status: "True"
```

Fields are **classified** in the schema: immutable, output only, required, *sensitive* (never returned or logged), personal data (for the data deletion concept), *untrusted* (freely populated by tenants or devices – normalized and never treated as an instruction or HTML) as well as the data class (metadata, content, IAM, audit, billing).

Operator objects (node, cell, role, adoption rule) follow the same structure as tenant objects. A **node**, too, is a resource with a `spec` (roles, labels, maintenance flag) and a `status` (lifecycle phase, hardware inventory, health).

### Levels and resource names

Every resource has exactly one parent. This yields a hierarchical name and a globally unique **URN**:

```text
cp:global:platform
cp:eu-hl1:region
cp:eu-hl1:cell/c1
cp:eu-hl1:node/n-17
cp:eu-hl1:discovery/d-8c1f2a
cp:global:tenant/acme/project/shop
cp:eu-hl1:tenant/acme/project/shop/compute/vm/web-01
```

- The URN contains only what never changes over the resource's lifetime. Cell, rack or site are properties, not part of the URN; only the cell itself and objects inseparably bound to a cell carry `cell/<c>`.
- The second segment (region or `global`) determines **routing**: every node derives from it which region or cell is responsible.
- Projects are named globally, their resources live regionally; data residency is controlled by project policy (permitted regions).
- The REST path can be mapped directly from the URN.
- Names follow the rules for DNS labels (lowercase letters, digits, hyphen, 1–63 characters).
- **Permission scopes are the same path prefixes**: a role binding on a project applies to everything beneath it (see [Identity](identity.html)).

### Versions

API groups are versioned independently. **Until the MVP, all groups carry `v1alpha1`**; the path via `v1beta1` to `v1` follows afterwards. Changes to the desired state are retained as revisions for audit and rollback (default 90 days).

## Operations

### Standard methods

| Method | HTTP | Semantics |
|---|---|---|
| Get | `GET /v1/{name}` | single resource |
| List | `GET /v1/{parent}/{kind}` | pagination, filtering, sorting |
| Create | `POST /v1/{parent}/{kind}?id={name}` | name chosen by the client, idempotently retryable |
| Update | `PATCH /v1/{name}` | JSON Merge Patch with `If-Match` |
| Replace | `PUT /v1/{name}` | complete desired state (GitOps/OpenTofu) |
| Delete | `DELETE /v1/{name}` | asynchronous with finalizers |

### Actions

Anything that is not simply setting a field is an **action** with its own verb (`POST /v1/{name}:{verb}`), such as `platform:initialize`, `discovery:adopt`, `node:drain`, `node:decommission`, `cell:split`, `region:rotateCa`, `tenant:suspend` or `vm:start`. Where possible, actions are **backed declaratively**: `node:drain` internally sets the maintenance flag in the desired state – the action is a convenient, auditable declaration of intent, and the reconciler takes care of the rest.

### Long-running operations, watch and events

- Every mutation that does not complete immediately responds with `202 Accepted` and an **Operation** resource with progress and the current step. It can be queried, awaited and canceled, and is itself auditable – in the portal as a task list, in MCP as a task.
- **Watch** delivers a stream of changes (externally as server-sent events, internally as gRPC streaming) with resumption from a known version.

### Idempotency, concurrency and dry run

- All mutating calls accept an `Idempotency-Key`; the portal and MCP **always** set it – important for AI agents that retry calls.
- Optimistic concurrency via `If-Match` → `412 Precondition Failed` on conflict.
- **Dry run for every mutation** (`?validateOnly=true`): validates, checks permissions and quotas, computes the effects ("drain moves 4 VMs and 2 volumes") and changes nothing.

### Error format

All errors are returned as `application/problem+json` per RFC 9457 – with a stable, machine-readable code, localized title and detail (German/English), trace ID, field-level violations and a hint as to whether retrying makes sense. The portal shows field errors at the form field; MCP returns the problem object in structured form so that an AI agent can correct itself. Internal details such as stack traces never end up in error messages.

## Protocols: REST/OpenAPI externally, gRPC internally

| | External (users, portal, MCP, CLI, OpenTofu) | Internal (agent ↔ agent, reconcilers) |
|---|---|---|
| Protocol | HTTPS/JSON, server-sent events for watch | gRPC over mTLS in the WireGuard underlay |
| Description | OpenAPI 3.1 + JSON Schema 2020-12 | Protobuf |
| Authentication | OIDC bearer tokens, API keys, setup token | Node certificates plus the forwarded original token with DPoP proof |

**One source:** resource types are defined **once as Rust types**. OpenAPI, portal forms, MCP tools, the CLI and SDKs are generated from them. Protobuf is used **only** for internal node-to-node communication; API objects are carried in it as a versioned payload, not maintained as a second schema. Protobuf as the source with HTTP transcoding was rejected because the tooling for it in Rust is weak. The REST facade is not a second code path: validation and authorization happen in exactly one place (see [Rust stack](rust-stack.html)).

### Versioning and deprecation

- `alpha` can break without notice and is disabled by default; `beta` has at least six months or two releases of lead time; `v1` permits only backward-compatible changes within the major version.
- GA fields have a **deprecation period of at least 12 months**, announced via `Deprecation` and `Sunset` headers, OpenAPI, the changelog, portal banners and notices in MCP.
- Breaking changes without a version bump fail CI.
- During rolling updates, a new API version is only activated once all members of the control group support it.

## Deriving the portal and MCP from the schema

OpenAPI and JSON Schema are generated from the schema; from these, in turn, the portal, MCP server, CLI, SDKs, OpenTofu provider, documentation and the parity check are derived.

### Schema annotations

The API description carries all the information the portal and MCP need – via project-specific schema extensions: level, display texts (de/en), input type, **effect** (read, create, update, destructive, irreversible), required permission, long-running yes/no, tool assignment, marking of untrusted fields, data class, and step-up and confirmation requirements. From these follow the navigation, form elements, confirmation dialogs and visible buttons in the portal, as well as tool descriptions, tool hints and confirmation requirements in MCP. Exceptions to derivation are only permitted with a justification; security-relevant annotations are enforced by lint.

### Portal

- **Generic core:** list, detail, form and action dialogs are rendered at runtime from OpenAPI and JSON Schema. A new resource therefore appears in the portal automatically – with validation, help texts, permission checks and a dry-run preview.
- **Curated where it makes sense:** for key flows (initial setup, adoption, VPC topology, node map) there are hand-built views. They call only the public API – they may look nicer, but cannot do anything the API cannot.
- The portal is a static single-page app, embedded in the agent and served by **every** node, without a backend with special privileges (for the technology, see [Portal](portal.html)).

### MCP server

The MCP server is built into the agent and reachable on every node via Streamable HTTP (stateless per the current MCP specification); locally also via stdio through the CLI.

**Tool design – not every endpoint is a tool.** Hundreds of fine-grained tools overwhelm language models. Instead, tools are grouped based on the annotations:

| Tool (example) | Bundles |
|---|---|
| `cp_get`, `cp_list`, `cp_search` | all reads of all kinds |
| `cp_describe_schema` | schema of a resource kind |
| `cp_apply` | creating, updating, replacing any kind (with dry run) |
| `cp_delete` | deletion (with confirmation) |
| `node_lifecycle` | adopt, reject, drain, decommission, restart |
| `cluster_topology` | cell, region, control group |
| `tenant_admin` | tenant, project, users, roles, quotas |
| `operation_wait` | track long-running operations |

- Every tool has an input and output schema and returns structured data plus a short text summary.
- The tool list is **dynamic**: it contains only tools the token has permissions for; a tenant token does not see node tools.
- **MCP resources** make objects, events, inventory and the audit log available read-only; **MCP prompts** correspond to the portal wizards (e.g. first installation, onboarding a node, creating a project, analyzing an incident).
- Follow-up questions and confirmations use elicitation. Destructive and irreversible actions, privileged IAM changes and adoption require **confirmation on a platform page outside the AI client** (out-of-band).

## Special cases: bootstrap and failure behavior

### The first node

For the first node there is neither an identity service nor a control group – yet setup must still work via all three access paths.

1. The node boots from the USB stick in the **uninitialized** state and offers only a bootstrap subset of the API (platform status, initialization including dry run, hardware info, network test).
2. A **one-time setup token** (128 bits, valid for 24 h, single-use) is displayed, preferably on the local console or HDMI. A token file on the stick is created only after a local action. In addition, the node displays the fingerprint of its provisional TLS certificate.
3. Initialization is possible via API, portal or MCP using this token.
4. It creates the platform, region, cell, internal CA, the first operator admin and a recovery key. The setup channel is secured by the setup token and a confirmation code. At the end, a one-time, short-lived **admin invitation link** is generated, which is used to register the first passkey under the final portal address. Creating and redeeming the invitation are excluded from MCP.
5. After that, the token is consumed and bootstrap mode ends irrevocably. The entire process is recorded as the first entries in the audit log.

### Adopting new hardware

Discovered hardware appears as a `Discovery` resource with an inventory (architecture, CPU, RAM, disks, NICs, serial number, TPM and Secure Boot status). Adoption is the `:adopt` action or an adoption rule – both regular API objects. **Auto-adopt is disabled by default**; permanent rules are only permitted with attested hardware. The flow is described in detail in [Boot & adoption](boot-adoption.html).

### Every node is an entry point

- **Every** node serves the API, portal and MCP. The region's DNS name points to multiple nodes; in a homelab, mDNS also helps.
- The receiving node authenticates the request, determines the responsible cell from the URN and forwards it via gRPC to the Raft leader (writes) or any member (eventually consistent reads). In doing so, it passes on the **original token** together with the DPoP proof; **authorization takes place at the destination**, not on the basis of the forwarding node.
- If the responsible cell fails, other nodes serve cached data marked as stale and reject writes with `503` and `Retry-After` – never silently losing anything.

## Security

### The same check chain for all access paths

Every call – REST from the portal, REST from a script or an MCP tool – passes through the same chain: **authentication → authorization → validation → quota → audit → execution**. Identities are users (OIDC, passkeys), service accounts, API keys and nodes (mTLS certificate). The MCP server is an OAuth 2.1-protected resource server; it only accepts tokens with its own audience (no token passthrough). The portal has no special privileges. Details: [Security model](security-model.html).

### MCP-specific safeguards

| Risk | Measure |
|---|---|
| AI agent acts with full user permissions | Restricted MCP tokens, read-only by default, bound to a project/tenant, short lifetime; operator permissions must be enabled explicitly |
| Prompt injection via data | Third-party-populated fields are normalized and strictly marked as data; tool descriptions are static in the binary |
| Destructive actions, adoption, IAM changes | Mandatory dry run with a **confirmation token** (bound to principal, action, target, version and the hash of all parameters, single-use, valid for 5 minutes) **plus out-of-band confirmation by a human** |
| Mass changes, infinite loops | Rate limits per token and channel, caps per call, deletion protection flag |
| Exfiltration | Output filter for sensitive fields; secrets are never readable via MCP, only references |

The confirmation logic is an **API function**, not special MCP logic: the portal (dialog) and scripts (token) use the same mechanism. Policies may only tighten confirmation requirements; the out-of-band confirmation for destructive actions and adoption **cannot be disabled**.

Autonomously acting AI agents may never perform irreversible actions, privileged IAM changes or adoptions; destructive actions only via an approval request to a human.

### Audit log

Every mutation (and every read of sensitive kinds) creates an immutable audit entry with time, **principal** (the human) and, separately, **actor** (e.g. an AI client), channel (`api`, `portal`, `mcp`, `cli`, `system`, `bootstrap` – set by the entry point, not forgeable), verb, target, confirmation type, parameter hash, result and change diff. Storage is tamper-proof (hash chain, block signature, regularly anchored outside the cell), separated per tenant and exportable. The audit log is itself a readable API resource.

## Parity rule and CI check

> **Every public API operation (method × resource kind × level) is reachable in the portal and in MCP – or explicitly exempted with a justification.** Goal for the MVP: zero exemptions for mutations.

The check takes place in three stages:

1. **Static comparison on every change request:** all operations in the generated OpenAPI are compared against the MCP and portal manifests. Every operation must be covered or exempted with a justification, destructive operations must be correctly marked in MCP; security and evidence operations may never be exempted. Gaps fail CI.
2. **Runtime comparison (nightly):** in a mixed ARM64/x86 test cluster, every scenario is run three times – via HTTP, via a portal end-to-end test and via an MCP client. Result, error codes, permission behavior and audit entry (identical except for the channel) are compared.
3. **Permission parity:** for a role matrix, it is checked that visible and executable operations match across all three channels – including for AI agents.

In addition, OpenAPI lint, breaking-change checks and generated two-tenant isolation tests run.

## Example: "adopt node" via three access paths

A Pi 5 has been connected via cable, has booted the discovery image and is waiting as `d-8c1f2a`. Goal: adoption into cell `c1` with the role `storage-object`.

### API

First a dry run, then execution with the confirmation token received:

```text
POST /v1/regions/eu-hl1/discoveries/d-8c1f2a:adopt?validateOnly=true
Host: api.example.com
Authorization: Bearer …

{ "nodeName": "n-pi5-04", "cell": "c1", "roles": ["storage-object"],
  "confirmationCode": "3817-5520" }

→ 200 OK
{ "valid": true,
  "effects": [ "Node receives certificate of cell c1",
               "OS image arm64 is rolled out",
               "Role storage-object: 512 GiB NVMe will be formatted" ],
  "confirmationToken": "ct_…" }
```

```text
POST /v1/regions/eu-hl1/discoveries/d-8c1f2a:adopt
Idempotency-Key: 7f0c3a2e-…

{ …same parameters…, "confirmationToken": "ct_…" }

→ 202 Accepted
Location: /v1/regions/eu-hl1/operations/op-0193f1c4
```

The operation is then awaited; the result is the new `Node` resource. Adoption **always** requires confirmation of the device identity – such as a confirmation code read off the device, an enrollment token, pre-registration or attestation – and additionally step-up via API/CLI.

### Portal

A badge reports live: "1 new node waiting". The detail view shows the inventory and notes such as "no TPM". "Adopt" is visible only with the appropriate permission and opens a form generated from the schema (name, cell, suitable roles, confirmation code). An automatic preview (dry run) lists the effects including a formatting warning; confirmation is by passkey, after which a progress indicator tracks the operation until the node is *Active*.

### MCP

User request in the AI client: *"Add the new Pi 5 as object storage in cell c1."*

```yaml
# 1. find pending hardware
tool: cp_list
arguments: { kind: Discovery, parent: "cp:eu-hl1:region", filter: 'status.phase="Waiting"' }
# 2. trigger adoption (marked as destructive because of formatting)
tool: node_lifecycle
arguments: { action: adopt, target: "cp:eu-hl1:discovery/d-8c1f2a",
             nodeName: n-pi5-04, cell: c1, roles: [storage-object] }
# → server performs a dry run and requires confirmation on a platform page
#   (URL elicitation); there the human enters the device code and confirms by passkey.
# 3. track progress
tool: operation_wait
arguments: { operation: "cp:eu-hl1:operation/op-0193f1c4", timeout: 60 }
```

The AI client sees neither the confirmation code nor the confirmation itself. Alternatively, the MCP prompt "Onboard node" guides the user through the same steps.

**Result in all three cases:** the same operation, the same `Node` resource and an audit entry that differs only in the channel and, where applicable, the actor.
