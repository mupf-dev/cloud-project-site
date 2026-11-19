title: Hyperscaler feature analysis
summary: Which service categories from AWS, Azure and Google Cloud DCP covers, how they are implemented (in-house development or external component) and in which phase.
group: konzept
order: 140
quelle: Concept 121 (Hyperscaler Feature Analysis)
de: funktionsanalyse
---

## Purpose

The analysis compares the service offerings of AWS, Microsoft Azure and Google Cloud with DCP's plan. It
answers three questions: Which features should the platform eventually offer? How will they be implemented? And when? In total,
around 230 features were examined across three areas: infrastructure; data, AI and integration; and identity, security,
operations and developer tools. The analysis was accepted on 2026-11-12.

The following tables are an **abridged selection** of the most important categories.

### Legend

| Abbreviation | Meaning |
|---|---|
| **MVP** | planned for the first working version (April 2027) |
| **P2** | by release 1.0 (mid-2027) or release 1.x |
| **P3** | afterwards |
| **NO** | deliberately not offered as a platform service |
| **Own** | own Rust implementation |
| **Own+Lib** | own service built on established libraries |
| **External** | off-the-shelf product behind a process boundary, only with justification |

## Ground rule: in-house development preferred

Since 2026-11-12 the rule is: **prefer in-house development where it makes sense.** The platform builds control, policy and workflow
logic itself – this fits the Raft-based state, authorization with Cedar, the parity of API, portal and
MCP, and tenant isolation (see [Rust stack](rust-stack.html) and [API-first](api-first.html)).

Components with a very large maintenance or maturity effort remain **external**, always integrated across a process boundary:

- **Database and protocol engines** (PostgreSQL, MariaDB, Valkey, Kafka, OpenSearch, ClickHouse) – compatibility is the
  point here; a reimplementation would bring no benefit. Guardrail: "no database of our own" (see [Vision](vision.html)).
- **Hypervisor, Kubernetes, container runtime** – security- and kernel-critical, a large investment in maturity.
- **Inference engines** – they depend on GPU kernel ecosystems (see [AI platform](ai-platform.html)).
- **Knowledge bases that need constant upkeep** – the scanners' vulnerability databases, DLP detectors.
- **Python ecosystems** such as Airflow, Spark, Jupyter or fine-tuning frameworks.

Even with external engines: **control, API, tenant isolation, backup and metering are developed in-house.**
An exception to "no database of our own" is block and object storage, which, following a separate decision, are developed in-house
(see [Storage](storage.html)).

All components must have OSI-approved licenses. This excludes, among others, HashiCorp Vault, Packer and
Nomad (BUSL), newer versions of CockroachDB, ScyllaDB and EMQX, MongoDB (SSPL), Redpanda and Restate (see
[License and governance](license-governance.html)).

## Part A – Infrastructure

### Compute

| Feature | AWS / Azure / GCP | Implementation | Priority |
|---|---|---|---|
| Virtual machines | EC2 / Virtual Machines / Compute Engine | Own, hypervisor external | MVP |
| Resizing, hotplug | Resize / VM Sizes / Custom Machine Types | Own | P2 |
| Live migration | internal / Live Migration / Live Migration | Own (orchestration) | P2 |
| Spot and dedicated hosts | Spot, Dedicated Hosts / Spot, Dedicated Host / Spot, Sole-tenant | Own | P2 |
| Autoscaling groups, instance templates | Auto Scaling / Scale Sets / Managed Instance Groups | Own | P2 |
| Images, gallery, versions | AMIs / Compute Gallery / Image Families | Own | MVP / P2 |
| VM snapshots | EBS Snapshots / Restore Points / Machine Images | Own | P2 |
| Affinity / anti-affinity | Placement Groups / Proximity Placement / Placement Policies | Own | near MVP / P2 |
| Availability zones | Availability Zones / Zones / Zones | Own | P2 |
| vTPM, Secure Boot for guests | NitroTPM / Trusted Launch / Shielded VM | Own + swtpm | P2 |
| Confidential computing | SEV-SNP / Confidential VMs / Confidential VMs | Own (attestation) + External | P3 |
| Bare metal for tenants | `*.metal` / BareMetal / Bare Metal Solution | Own (on top of boot and adoption) | P3 |

The hypervisor remains external (Cloud Hypervisor, itself written in Rust); everything above it – lifecycle, placement, images,
metadata – is our own.

### Containers, Kubernetes, serverless

| Feature | AWS / Azure / GCP | Implementation | Priority |
|---|---|---|---|
| Container instances (MicroVM-isolated) | Fargate / Container Instances / Cloud Run | Own, runtime external | MVP |
| Managed Kubernetes | EKS / AKS / GKE | Own (lifecycle), k3s external | MVP |
| Kubernetes integration (CSI, CCM, CNI) | various | Own | MVP / P2 |
| Node pool autoscaling | Karpenter / Node Auto-Provisioning / NAP | Own | P2 |
| Container registry | ECR / ACR / Artifact Registry | External (zot) | MVP |
| Functions | Lambda / Functions / Cloud Run functions | Own+Lib (wasmtime) | P2 |
| Container serverless | ECS Express Mode / Container Apps / Cloud Run | Own | P2 |
| Scheduled jobs | EventBridge Scheduler / Timer / Cloud Scheduler | Own | P2 |
| Static web hosting | Amplify / Static Web Apps / Firebase Hosting | Own + object storage | P2 |
| Batch | AWS Batch / Azure Batch / Batch | Own | P3 |
| PaaS from source code | Beanstalk / App Service / App Engine | Own + Buildpacks | P3 |
| Service mesh | VPC Lattice / Istio add-on / Cloud Service Mesh | External as add-on | P3 |

### Network

| Feature | AWS / Azure / GCP | Implementation | Priority |
|---|---|---|---|
| VPC, subnets, security groups | VPC / VNet / VPC | Own (nftables) | MVP |
| IPAM, DHCP, internal DNS, NAT, floating IPs | various | Own | MVP |
| L4 load balancer | NLB / Load Balancer / Network LB | Own | MVP |
| Basic DDoS protection | Shield / DDoS Protection / Cloud Armor | Own (nftables/XDP) | MVP / P2 |
| Network ACLs, route tables, peering, IPv6 | various | Own | P2 |
| Site-to-site and client VPN | VPN / VPN Gateway / Cloud VPN | Own (WireGuard) | P2 |
| Private endpoints | PrivateLink / Private Link / Private Service Connect | Own | P2 |
| L7 load balancer with ACME | ALB / Application Gateway / Application LB | Own+Lib | P2 |
| Public/private DNS, DNSSEC | Route 53 / Azure DNS / Cloud DNS | Own+Lib | P2 |
| Flow logs, bandwidth limits | Flow Logs / Network Watcher / Flow Logs | Own | P2 |
| CDN, WAF, central firewall | CloudFront, WAF / Front Door / Cloud CDN, Armor | Own+Lib | P3 |
| Transit hub, dedicated lines, BGP | Transit Gateway / Virtual WAN / NCC | Own | P3 |

Details on the network design: [Network](network.html).

### Storage, edge and hybrid

| Feature | AWS / Azure / GCP | Implementation | Priority |
|---|---|---|---|
| Block volumes, snapshots, encryption with tenant key | EBS / Managed Disks / Persistent Disk | Own | MVP / P2 |
| S3 object storage | S3 / Blob Storage / Cloud Storage | own gateway, engine initially external | MVP |
| Versioning, Object Lock (WORM) | S3 Object Lock / Immutable Storage / Bucket Lock | Own (own object storage) | Release 1.x |
| Lifecycle rules | S3 Lifecycle / Lifecycle Management / OLM | Own | P2 |
| File storage NFS/SMB | EFS, FSx / Azure Files / Filestore | External + Own | P2 |
| Backup service for tenants | AWS Backup / Azure Backup / Backup and DR | Own+Lib | P2 / Release 1.x |
| Archive, cross-region replication | Glacier / Archive Tier / Archive | Own | P3 |
| Platform on-premises at the customer | Outposts / Azure Local / Distributed Cloud | Own (inherent) | MVP / P2 |
| Air-gapped operation | limited / Stack Hub / GDC air-gapped | Own | P2 |
| HPC clusters, RDMA | ParallelCluster, EFA / CycleCloud / Cluster Toolkit | Own + External | P3 |

A decentralized platform that runs at the operator's own site covers scenarios such as Outposts or Azure Local out of the box.

## Part B – Data, AI and integration

Nothing in this area is part of the MVP. Database engines remain external; control (API, lifecycle, backup, metering)
is our own.

| Feature | AWS / Azure / GCP | Implementation | Priority |
|---|---|---|---|
| Managed PostgreSQL, MySQL/MariaDB | RDS, Aurora / Azure Database / Cloud SQL | Control own, engine external | P2 |
| In-memory cache | ElastiCache / Managed Redis / Memorystore | Control own, engine external | P2 |
| Queues, pub/sub, event bus, data streams | SQS, SNS, Kinesis / Service Bus, Event Hubs / Pub/Sub | Own+Lib | P2 |
| Platform events | EventBridge / Event Grid / Eventarc | Own | P2 |
| Workflow service with scheduler | Step Functions / Logic Apps / Workflows | Own | P2 |
| Notifications, email sending | SNS, SES / Communication Services / – | Own or Own+Lib | P2 |
| Model catalog, model registry | Bedrock, SageMaker / Foundry / Vertex AI | Own | P2 |
| Inference endpoints, batch inference | Bedrock / Azure OpenAI / Vertex AI | Control own, engine external | P2 |
| AI gateway | Bedrock / API Management AI Gateway / Apigee | Own | P2 |
| Guardrails | Bedrock Guardrails / Content Safety / Model Armor | Own+Lib | P2 |
| Vector search, RAG | Knowledge Bases / AI Search / Vector Search | Own+Lib | P2 |
| Agent runtime | AgentCore / Foundry Agent Service / Agent Engine | Own | P3 |
| Prebuilt AI services (speech, OCR, translation, vision) | Transcribe, Textract / Speech, Document Intelligence / Speech, Document AI | Own+Lib | P3 |
| Fine-tuning, notebooks, ML training | SageMaker / Azure ML / Vertex AI | External or Own+Lib | P3 |
| NoSQL (document, key-value, wide-column, graph, time series) | DynamoDB, DocumentDB / Cosmos DB / Firestore, Bigtable | mostly External | P3 |
| Lakehouse, serverless SQL on object storage | Athena, Glue / Fabric / BigQuery, BigLake | Own+Lib | P3 |
| Full-text search, data warehouse, Kafka, stream processing | OpenSearch, Redshift, MSK / AI Search, Fabric, Event Hubs / BigQuery | External | P3 |
| API management | API Gateway / API Management / Apigee | Own+Lib | P3 |
| IoT hub with device twin | IoT Core / IoT Hub / – | Own+Lib | P3 |

Notably, all three hyperscalers introduced dedicated agent services in 2025 – which fits DCP's MCP-first approach.
Prebuilt AI services are built as thin, stable APIs over model templates on the inference endpoints, not as a
separate service per model. An IoT hub is highly relevant for homelabs and offers differentiation, since Google has discontinued its service.

## Part C – Identity, security, operations, developers

### Identity, governance, keys

| Feature | AWS / Azure / GCP | Implementation | Priority |
|---|---|---|---|
| SSO, MFA/passkeys, OIDC federation | Identity Center / Entra ID / Cloud Identity | Own+Lib | MVP |
| Users, groups, service accounts, workload identities | IAM / Managed Identities / Service Accounts | Own | MVP |
| Fine-grained authorization, guardrails | IAM Policies, SCPs / RBAC, Azure Policy / IAM Conditions, Org Policy | Own+Lib | MVP |
| Audit log, visible operator access | CloudTrail / Activity Log, Customer Lockbox / Audit Logs, Access Transparency | Own | MVP |
| Hierarchy, labels, quotas | Organizations / Management Groups / Resource Manager | Own | MVP |
| SAML, SCIM, B2B guests, just-in-time permissions | Identity Center / Entra ID, PIM / PAM | Own | P2 |
| Continuous configuration compliance | AWS Config / Azure Policy / Security Command Center | Own | P2 |
| Platform KMS, crypto-shredding, SSH CA | KMS / Key Vault / Cloud KMS | Own+Lib | MVP |
| Tenant key API, BYOK/HYOK | KMS CMK, XKS / Managed HSM / EKM | Own | P2 |
| Secrets manager | Secrets Manager / Key Vault / Secret Manager | Own | P2 |
| Public certificates, private CA | ACM, Private CA / Key Vault / CAS | Own+Lib | P2 |

See also [Identity and permissions](identity.html) and [Cryptography](cryptography.html).

### Security, compliance, operations

| Feature | AWS / Azure / GCP | Implementation | Priority |
|---|---|---|---|
| Node hardening, supply chain (SBOM, signing) | Nitro, Signer / – / Shielded VM, Binary Authorization | Own+Lib | MVP |
| Evidence collection, sovereign environments | Audit Manager / Compliance Manager / Assured Workloads | Own | MVP |
| Security posture (CSPM), vulnerability scanning | Security Hub, Inspector / Defender / SCC | Own or External (scanner) | P2 |
| Bastion, zero-trust app access | Session Manager, Verified Access / Bastion / IAP | Own | P2 |
| Trust portal, compliance assessment | Artifact / Service Trust Portal / Compliance Reports | Own | P2 |
| Platform telemetry, operator alerts | CloudWatch / Azure Monitor / Cloud Monitoring | Collection own, storage external | MVP |
| Tenant metrics, logs, dashboards, uptime | CloudWatch / Log Analytics / Cloud Logging | Own | P2 |
| Metering | CUR / Cost Exports / Billing Export | Own | MVP |
| Cost analysis, budgets, invoices | Cost Explorer / Cost Management / Cloud Billing | Own | P2 |
| Automation, runbooks | Systems Manager / Azure Automation / Workflows | Own | P2 |
| Threat detection, DLP, forensics | GuardDuty, Macie / Defender, Purview / SCC | Own+Lib or External | P3 |
| Disaster recovery, chaos engineering | Elastic DR, FIS / Site Recovery, Chaos Studio / – | Own | P3 |

A unique selling point in the homelab: cost analysis with **energy cost per node** (power draw × electricity price).

### Developers and marketplace

| Feature | AWS / Azure / GCP | Implementation | Priority |
|---|---|---|---|
| CLI, MCP access for AI agents | AWS CLI / Azure CLI / gcloud | Own | MVP |
| OpenTofu provider | AWS, Azure and Google providers | Own | P2 |
| Native declarative stacks with drift detection | CloudFormation / Bicep, Deployment Stacks / Infrastructure Manager | Own | P2 |
| SDKs (Rust, Go, Python, TypeScript), API explorer | SDKs / SDKs / Client Libraries | Own+Lib | P2 |
| Browser shell | CloudShell / Cloud Shell / Cloud Shell | Own | P2 |
| Marketplace, self-service sign-up, support cases, status page | Marketplace / Marketplace / Marketplace | Own | P2 |
| Pulumi | Pulumi provider | via a bridge from the OpenTofu provider | P3 |

## Key gaps up to release 1.0

The largest gaps compared with the hyperscalers, to be closed by release 1.0 or 1.x:

1. **Backup service for tenants** – policies via labels, retention, immutable vaults, copy to a second
   site, guided restore. Particularly in demand in the homelab.
2. **Tenant observability** – separate metrics and logs with a query API, alert rules as API resources, dashboards in the portal.
3. **L7 load balancer with ACME certificates** – the entry-level case for almost every web service; the basis for WAF, CDN, static hosting
   and container serverless.
4. **Autoscaling groups and container serverless** – "n identical instances behind a load balancer, self-healing".
5. **Continuous configuration compliance** – assessment of the inventory with conformance packs (such as "BSI baseline"), history and
   automatic remediation (see [Compliance requirements](compliance-requirements.html)).
6. **Identity-bound access** (bastion, zero trust) as well as a **certificate service and private CA**.
7. **Notification, email and workflow service** as a shared cross-cutting capability instead of individual solutions per component.
8. **VPN, private endpoints, FinOps, SDKs and deployment stacks.**

Object versioning and Object Lock were moved to release 1.x because they require an in-house object storage.

## Deliberately not (NO)

| Feature | Reason |
|---|---|
| Gateway load balancer for inline appliances | No appliance ecosystem; can be modeled with route tables and a firewall VM |
| Offline transfer appliances | Hardware logistics, not a software product |
| Storage gateway / hybrid file sync | The platform is already local; sync clients are tenant software |
| Global anycast LB | Requires its own anycast network; GeoDNS as a later substitute |
| IoT edge runtime, digital twins | A different product or a niche; small devices are adopted as nodes |
| Own hypervisor, own distributed file system, own Kubernetes distribution | Non-goals; security maturity and complexity |
| Managed SQL Server / Oracle | Proprietary licenses; can be self-operated as a VM template |
| Data governance catalog, feature store, data labeling | Niche; possible as a marketplace template |
| Text analytics API | Covered by LLM endpoints |
| AI coding and office assistants | End-user products, not a platform service; integration via the AI gateway |
| Facial recognition | Proximity to prohibited or high-risk practices under the AI Act, data protection |
| iPaaS connectors | Maintenance effort for hundreds of SaaS APIs |
| Blockchain, quantum computing | No demand or no sovereignty gain |
| Dedicated HSM as a tenant service | BYOK/HYOK covers the needs of regulated tenants |
| CDK | OpenTofu, Pulumi, native stacks and SDKs are sufficient |
| CI/CD, Git hosting, package repositories, dev environments as a service | Would be a second product; marketplace templates instead |

**SIEM/SOAR** was initially on the NO list but was brought back in the review as a later package: detection rules are built
in-house on the audit stream; audit, flow and security findings are additionally exported as a stream so that tenants can connect their
own SIEM.

## Selected decisions for existing building blocks

- **Telemetry:** collection, alert evaluation, notification, dashboards and the tenant-isolating query gateway are our own;
  storage for metrics and logs remains external. Grafana is not a mandatory component.
- **Secrets manager:** our own instead of an additional product – the key hierarchy and Raft state already exist, and a
  second consensus service would contradict the principle of "one consensus mechanism" (see [Control plane](control-plane.html)).
- **Billing:** our own, since the metering data already lives in the platform.
- **Infrastructure as code:** own OpenTofu provider, generated from the OpenAPI description; Pulumi via a bridge instead of
  a second package.
- **Container registry:** zot stays (Apache-2.0, process boundary), supplemented with image scanning and signature verification at admission.
- **AI gateway:** our own gateway developed in Rust (see [AI platform](ai-platform.html)).
