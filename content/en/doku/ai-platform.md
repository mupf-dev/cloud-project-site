title: AI-native platform
summary: How DCP manages models, operates inference endpoints, schedules accelerators and delivers AI services through its own AI gateway in a tenant-safe and compliant way.
group: konzept
order: 130
quelle: Concept 113 (AI-Native Platform)
de: ki-plattform
---

## What "AI-native" means

For DCP, "AI-native" means three things:

1. **AI services for tenants** – register models, run them as OpenAI-compatible endpoints, consume them through a gateway with
   keys, budgets and guardrails, and build knowledge bases (RAG). This ranges from the homelab (CPU, Raspberry Pi,
   integrated GPU, small NPUs) to the data center with GPU servers.
2. **The platform as a tool for agents** – every function can be controlled via MCP (see [API-first](api-first.html)).
   Agents are actors in their own right with intersected permissions (see [Identity and permissions](identity.html)).
3. **Compliance by design for AI** – EU AI Act, GDPR, BSI AIC4 and C5: evidence is produced by ongoing operation
   (see [Compliance by design](compliance-by-design.html)).

Out of scope for this concept are AI-assisted platform operations, training large models, end-user products such as
copilots, facial recognition and custom GPU kernels.

The model is the AI offerings of the hyperscalers (catalog, serverless and dedicated endpoints, gateway, guardrails,
knowledge bases, agent runtime). DCP adopts their common pattern: **control, billing and policy belong to the
platform; the inference engines are interchangeable.**

## Key decisions at a glance

| Topic | Decision |
|---|---|
| Resource model | one API group `ai.cloud-project.io/v1alpha1`, fully API-first (API, portal, MCP, CLI) |
| Engines | control in-house, engines external behind a process boundary; llama.cpp first, vLLM for GPU servers |
| Isolation | tenant-dedicated endpoints in MicroVMs with a passed-through accelerator; shared models as a platform service without tenant code |
| Drivers | standard image with open stacks only; proprietary runtimes only as a signed, explicitly enabled operator extension |
| Models | OCI artifacts in the platform registry, signed, with a cache per cell; safe formats only |
| Scaling | scale-to-zero only with a local model cache; the gateway buffers during activation |
| Distributed inference | two stages: engine-native first, own protocol only after measurement |
| AI gateway | own AI gateway developed in Rust – initially as a separate process, later as a library |
| Agents | the platform itself is controllable via MCP, with token exchange and intersected permissions |
| Compliance | AI compliance as a cross-cutting concern: model card, license, provenance, risk class, labeling, evidence |

The decisions were made on 2026-11-14.

## Resource model

All AI resources follow the platform's uniform resource schema (metadata/spec/status, URN, conditions,
long-running operations, see [Control plane](control-plane.html)). Project resources are regional; the operator's catalog
objects live in the global platform scope.

| Kind | Purpose |
|---|---|
| `Model` | logical model: family, tasks (chat, embedding, rerank, speech, OCR, vision), license, provenance, model card, AI Act metadata |
| `ModelVersion` | immutable artifact: OCI reference with digest, format, quantization, context length, memory requirement, engine compatibility, signature status, stage (`draft` to `deprecated`), provenance chain, evaluation results |
| `InferenceEndpoint` | desired service: API kinds, traffic split across revisions, scaling, placement, network |
| `InferenceDeployment` | immutable **revision** of an endpoint (model version, engine, resources, parallelism); canary and rollback via weights |
| `AiGateway` | instance or tenant scope of the AI gateway with ingresses, default policies and logging policy |
| `GatewayRoute` | public model name → targets (internal endpoints, external providers), weights, fallbacks, limits, guardrails, cache |
| `AiBudget` | amount, period, warning thresholds, token limits – attached to a project, service account, key or route |
| `GuardrailPolicy` | ordered filter chain (PII, prompt filter, judge model, topic blocks, AI labeling) with failure behavior |
| `VectorIndex`, `KnowledgeBase` | vector index and knowledge base for RAG |
| `BatchInferenceJob` | batch processing from object storage, uses spare capacity |
| `AcceleratorClass` | operator-defined accelerator class: selector over the inventory, divisibility, price, minimum trust level |

A simplified example of an endpoint:

```yaml
apiVersion: ai.cloud-project.io/v1alpha1
kind: InferenceEndpoint
metadata:
  name: chat
spec:
  apis: [openai.chat, openai.completions]
  traffic:
    - { deployment: r7, percent: 90 }
    - { deployment: r8, percent: 10 }   # Canary
  scaling: { minReplicas: 0, maxReplicas: 4, scaleToZeroAfter: 15m, coldStartTimeout: 120s }
  placement: { arch: any, minTrustLevel: basic, dataClass: standard, spreadBy: zone }
  network: { exposure: private, gateway: default }
  deploymentTemplate:
    engine: { kind: llama-cpp, version: auto }
    resources: { accelerator: { class: igpu-vulkan, count: 1 }, memoryGiB: 12, cpu: 4 }
```

**No separate AI key type.** Callers authenticate with platform identities: workload tokens, API keys of
service accounts, or user tokens. As a convenience, the portal shortcut "Create AI key" creates, in a single step, a
service account with invoke permission on the selected routes plus a budget. Platform workloads use their workload identity
without any stored key at all.

**Permissions and audit.** Calling an endpoint (`invoke`) is a separate data-plane permission, distinct from
management. Deleting production model versions or populated knowledge bases counts as destructive and requires confirmation
outside the calling client. Model output and document content are marked as untrusted: agents receive
them as data, never as instructions, and the portal never renders them as HTML. Prompts and responses are tenant content and
do not belong in the platform audit log; only usage metadata (tokens, model, route, cost, guardrail hits) goes to metering.

## Inference engines

Inference performance comes from hand-optimized kernels for CUDA, ROCm, Vulkan, AVX or NEON, maintained by large
communities. Building our own would make no sense here. **Everything around them is our own:** adapters, endpoint proxy,
scheduler integration, cache and distribution, gateway, metering and compliance.

| Engine | License | Role |
|---|---|---|
| llama.cpp | MIT | **first engine**: broadest hardware support (CPU, Vulkan, CUDA, ROCm), arm64 and amd64, GGUF, also for embeddings and rerankers |
| vLLM | Apache-2.0 | **second engine** for GPU servers: tensor, pipeline, expert and data parallelism |
| ONNX Runtime, whisper.cpp | MIT | for OCR/vision and speech recognition respectively, each as a separate engine process |
| Hailo runtime | partly proprietary | only as an operator extension for edge services (vision, speech, small LLMs) |
| candle and other Rust engines | permissive | not used at present; candidates for later re-evaluation |
| Ollama, TGI | – | not used (duplicate model management or maintenance mode, respectively) |

A CPU benchmark showed a candle-based Rust engine at 44–65% of llama.cpp's decode and 25–47% of its
prefill performance. That is why **all** model types – including embeddings and rerankers – run on external engines.

### Engine adapter contract

Engines run as signed OCI images in the platform's container service, never directly with tenant privileges:

- **Image** from the operator's engine catalog, approved per version, with SBOM and provenance.
- **Model** as a read-only mount from the local cell cache – no download inside the engine process, no egress.
- **Interface:** OpenAI-compatible HTTP on a Unix socket. A dedicated endpoint proxy terminates mTLS or
  workload tokens, enforces concurrency limits, counts tokens and provides scaling signals. Engines never talk directly to
  tenants or the gateway.
- **Mandatory functions** per adapter: launch description, readiness, metrics (queue, running sequences, tokens,
  KV cache utilization), capabilities and graceful shutdown. A new engine needs only an adapter and an image.
- **Sandbox:** dedicated user, seccomp/Landlock, only the required device files, no network other than the socket.

Because engines are run as processes rather than linked, copyleft licenses are unproblematic too. Model weights have
**their own** licenses, some with usage restrictions; the catalog records them as a mandatory field, flags non-OSI licenses and
can block them by policy.

## Accelerators and placement

The node inventory detects accelerators (vendor, model, memory, driver and firmware version, IOMMU group, NUMA node,
PCIe link, divisibility). Device self-reports are treated as untrusted; suitability is decided by a
smoke inference at admission and by operator labels.

| Device | Stack | Assessment |
|---|---|---|
| CPU (AVX2/AVX-512/NEON) | open | baseline, always available; small models, embeddings, batch |
| Integrated GPU (Vulkan) | open | good for the homelab |
| AMD GPU (ROCm) | open | recommended for a fully open stack |
| NVIDIA GPU (CUDA) | proprietary userspace | market standard, only as a signed operator extension |
| NPUs (AMD XDNA, Intel) | partly open | watch, later |
| Hailo modules | proprietary compiler | operator extension for edge services |

**Isolation.** Tenant-dedicated endpoints get an entire device, passed through via VFIO to exactly one MicroVM –
there is no shared kernel between tenants (see [Security model](security-model.html)). Devices without clean
IOMMU separation serve only shared platform services. GPU sharing between tenants via containers is planned only for a later
phase and only with hardware partitioning (MIG); time-slicing without hardware isolation remains
excluded.

**Scheduler requirements:**

1. Accelerators as a hard resource (class, count, minimum memory), bin packing by accelerator memory.
2. **Gang scheduling:** a multi-node deployment is placed in full or not at all.
3. **Topology:** minimum bandwidth, same zone, maximum network hops.
4. **Cache affinity:** nodes with the model in their local cache are preferred.
5. **Priorities:** production before interactive before batch; batch jobs are preemptible.
6. **Quotas** for accelerators and accelerator memory; shared models via token budgets.
7. **Trust level** and data class as for virtual machines.

## Operating models

| | Dedicated | Shared (serverless) | External |
|---|---|---|---|
| Runs the engine | Tenant (platform-controlled) | Operator | Third-party provider |
| Isolation | MicroVM with passed-through device | Operator process with additional rules | Contract/DPA |
| Billing | Device hours | Tokens | Tokens, pass-through billing |
| Models | Any, including own fine-tunes | Operator catalog | Provider catalog |
| Typical use | Data protection, own models | Small teams, embeddings | Frontier models |

Fixed rules apply to shared models: **no cross-tenant prefix or KV cache**, quotas per tenant, no
storage of prompts without consent, memory discarded after the request, engine process without network, sensitive data only on
nodes with a high trust level. All three models run through the same gateway: one key, one budget, one policy.

## Scaling and scale-to-zero

A cold start consists of placement, container start, model loading and warmup – loading dominates. An 8B model (Q4, around
5 GB) loads from local NVMe in a few seconds, but takes around 45 seconds over 1 GbE from the cell cache; a 70B model takes
several minutes over 1 GbE. It follows that:

- Scale-to-zero only when the model is stored **locally** (cache affinity, prewarming at creation).
- The gateway buffers requests during activation and, once the timeout expires, responds with `503` and `Retry-After`.
- The scaling signal is queue length and running sequences per replica, not CPU load.
- Default: in the homelab, sleep after 15 minutes of idle time; in production, at least one replica.

## Model distribution: OCI and signing

- **Format:** a model is an OCI artifact with its own media type; the layers are weights, tokenizer, model card and
  license text. Large files are split into chunks – for parallel transfer and deduplication.
- **Import:** an import job downloads from an explicitly approved source, verifies hashes, generates a **model bill of materials**
  (files, hashes, license, source, revision) and signs it with the platform code-signing key (see
  [Cryptography](cryptography.html)). Vendor signatures are additionally verified where available. Without a valid signature
  there is no placement in regulated profiles; in the homelab there is a warning.
- **Safe formats only:** safetensors and GGUF. Pickle-based formats are rejected at import in **all** profiles.
- **Cache per cell:** every inference node holds a content-addressed, encrypted cache. Nodes transfer models
  among themselves via mTLS with range requests – first from neighbors, then from the registry. Gossip only spreads who
  has which digest.
- **Tenant models** (own fine-tunes) are tenant content, are stored encrypted with the tenant key and can be securely removed
  by crypto-shredding.

## Distributed inference

Which split makes sense depends on the network:

| Method | Network requirement | Suitability over 1 GbE |
|---|---|---|
| Data parallel (replicas) | none | **best choice** as long as the model fits on one node |
| Pipeline (layers across nodes) | activations at stage boundaries, not very latency-sensitive | good |
| Expert (MoE) | all-to-all per MoE layer | medium, depending on the model |
| Tensor | two synchronizations per layer, very latency-sensitive | only within one server or with ≥ 25–100 GbE/RDMA |

**Raspberry Pi clusters** are realistic for small models, embeddings and speech recognition close to the user, for batch and
background tasks, for MoE models with a small active share, and for teaching and research. They are not enough for interactive
large models: decode is memory-bandwidth-bound (an 8B model reaches roughly 2 tokens/s on a Pi 5), prefill is
compute-bound (long prompts take around a minute).

The platform therefore takes a two-stage approach:

- **Stage A:** multi-node deployments exclusively engine-native (vLLM, llama.cpp RPC). The platform provides
  gang scheduling, topology constraints, an isolated, encrypted **engine mesh** per deployment, health checks and
  coordinated shutdown.
- **Stage B:** a custom Rust protocol for pipeline and expert parallelism only if stage A measurably falls short.
  No custom tensor-parallel method.

Traffic in the engine mesh is tenant content, because activations allow inferences about prompts, and is therefore encrypted
(see [Network](network.html)).

## AI gateway

The AI gateway is the common entry point for all AI calls. Its feature set:

- OpenAI-compatible data plane (chat, completions, embeddings, audio, images) plus the Anthropic Messages format.
- Routing to internal endpoints and external providers with weights, priority groups, fallback, retry and circuit breakers.
- Authentication exclusively with platform identities (signed tokens with audience binding, bound keys).
- Limits (requests, tokens, concurrency) and budgets per project, service account, key and route; token metering with prices.
- Guardrails: PII detection, prompt-injection heuristics, judge models, topic blocks.
- Exact and semantic cache, **separated per project**.
- Payload logging only on opt-in; MCP gateway; observability via OpenTelemetry; audit of the configuration.

**The basis is our own AI gateway developed in Rust**, under the same license (AGPL-3.0-or-later, see
[License and governance](license-governance.html)) and with a matching technology stack (see
[Rust stack](rust-stack.html)). Building a new one would have repeated months of work. The gateway already offers tenant structures,
routing, limits, guardrails, an MCP gateway, declarative configuration and very low latency overhead in the
sub-millisecond range.

### Integration variants

| Variant | Description | Status |
|---|---|---|
| **V1 process** | Gateway as a platform service image; a controller translates platform resources into the declarative gateway configuration | first step |
| **V2 library** | Core gateway building blocks as a library within a platform service; configuration directly from platform resources, UI in the portal | target for a later 1.x release |
| V3 rebuild | own gateway inside DCP | rejected (duplicate work) |

In platform operation the **platform is the single source of truth**: the gateway's own management UI is disabled,
local data storage serves only as a cache. Tenants map to organizations, projects to teams, routes to model groups,
and budgets and guardrail policies to the corresponding gateway objects.

The interfaces between platform and gateway are clearly defined: external data-plane authentication against the
platform authorization server, configuration source, provider for internal endpoints with service discovery and cold-start signal,
platform-wide counters for budgets, usage events **without payload** to metering, audit, secrets from the secrets
manager (never in configuration or logs), TLS profile according to the cryptography concept, token exchange to the platform MCP server, and
payload logs only on opt-in in the encrypted tenant bucket.

**Placement:** regional platform service with at least two instances behind the L7 load balancer. Each instance holds a
complete configuration snapshot and continues working with the last known state if the control plane fails. Optionally there is a
project-specific gateway in the tenant VPC. Because prompts pass through in plaintext, the same trust levels apply as for
public ingresses.

## RAG and vector search – guardrails

- The pipeline is **our own**: sources from buckets → parser (external, as a process) → chunking → embedding via an
  inference endpoint → index → query API and OpenAI-compatible integration via the gateway.
- Index: embedded for small installations, Qdrant as a separate process for large ones, pgvector via the database service;
  hybrid search with BM25.
- **Document-level permissions:** every query filters by the permissions of the calling principal. Without this
  filtering, RAG would become a channel for data exfiltration.
- Indexes and embeddings are tenant content; deleting a source removes chunks and vectors, with evidence.

## MCP and agents

- **Platform via MCP:** all AI resources automatically appear as MCP tools. Agents can import models,
  create endpoints and set budgets – with intersected permissions and confirmation of destructive actions.
- **Tenant agents via the gateway:** the MCP gateway bundles the tenants' MCP servers and the platform MCP server.
  Instead of passing tokens through, token exchange (RFC 8693) issues a new token with an actor chain and restricted scopes.
  Every tool call is logged with principal and actor and counted against limits.
- **Agent runtime** (later phase) builds on the gateway, workload identity, containers and functions; its memory consists of
  knowledge bases and object storage.
- **Prompt injection:** model output and retrieved documents are untrusted. Destructive platform actions by an
  agent remain tied to confirmation outside the client – the most effective countermeasure against indirect
  prompt injection (see [Threat model](threat-model.html)).

## Tenant isolation and data protection

| Topic | Decision |
|---|---|
| Prompts and responses | Tenant content; no storage without opt-in; operator access only via an approved access request |
| Usage metadata | Billing data and metadata; principals pseudonymized in operator views |
| KV/prefix cache | never cross-tenant; gateway cache separated per project |
| Tenant models | own repository, tenant key, crypto-shredding |
| External providers | outbound connection explicitly approved; data location per route, non-EU can be blocked by policy |
| Training on tenant data | **never** by the platform; fine-tuning only as a tenant job |
| Deletion | deleting an endpoint or project removes cache, logs and indexes, with evidence |
| GDPR Art. 22/35 | the platform provides building blocks; the data protection impact assessment remains with the controller |

## EU AI Act and BSI AIC4

**Roles.** Whoever operates DCP normally provides infrastructure and is neither a provider of an AI system nor
of a general-purpose AI model (GPAI). They become a provider only when they make a model or system available under their own
name. Tenants are deployers or providers of their AI systems; the platform must **enable** them to fulfill their obligations.
The legal classification must be assessed case by case.

| Obligation (AI Act) | Platform building block |
|---|---|
| Prohibited practices, AI literacy | Catalog policy blocks templates for prohibited purposes; intended and excluded uses per model; notices in the portal |
| GPAI obligations | AI Act status per model (GPAI, systemic risk, reference to provider documentation); provenance chain of fine-tunes |
| Transparency (Art. 50) | "AI notice" guardrail building block, machine-readable labeling of synthetic content |
| High risk | initially purpose with risk class per endpoint; full support (mandatory logs, human oversight, metrics, documentation export) as a separate package in a later phase |

**BSI AIC4** presupposes C5. The platform contributes guardrails, model signing and provenance, and isolation
(security & robustness), evaluation runs per model version (performance), SLOs, fallback and canary (reliability),
model bill of materials and provenance chain (data quality), model cards and source citations in RAG (explainability), and
evaluation sets for bias. In addition, ISO/IEC 42001 and 23894 serve as organizational standards on the operator side, and the OWASP Top 10
for LLM Applications as an audit catalog.

**Evidence** is machine-readable and signed: model bill of materials and signature per model version, catalog export (license,
provenance, GPAI status), endpoint register (purpose, risk class, guardrails, data location), usage reports without
content, deletion certificates and an OSCAL component definition "AI Services" with AIC4 and AI Act mapping (see
[Compliance requirements](compliance-requirements.html)).
