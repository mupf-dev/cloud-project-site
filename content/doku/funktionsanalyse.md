title: Hyperscaler-Funktionsanalyse
summary: Welche Dienstkategorien von AWS, Azure und Google Cloud BYOC abbildet, wie sie umgesetzt werden (Eigenentwicklung oder externer Baustein) und in welcher Phase.
group: konzept
order: 140
quelle: Konzept 121 (Hyperscaler-Funktionsanalyse)
---

## Zweck

Die Analyse vergleicht das Dienstangebot von AWS, Microsoft Azure und Google Cloud mit dem Plan von BYOC. Sie
beantwortet drei Fragen: Welche Funktionen soll die Plattform irgendwann bieten? Wie werden sie umgesetzt? Und wann? Insgesamt
wurden rund 230 Funktionen in drei Bereichen betrachtet: Infrastruktur, Daten/KI/Integration sowie Identität, Sicherheit,
Betrieb und Entwicklerwerkzeuge. Die Analyse wurde am 2026-11-12 angenommen.

Die folgenden Tabellen sind eine **gekürzte Auswahl** der wichtigsten Kategorien.

### Legende

| Kürzel | Bedeutung |
|---|---|
| **MVP** | im Plan bis zur ersten lauffähigen Fassung (April 2027) |
| **P2** | bis Release 1.0 (Mitte 2027) bzw. Release 1.x |
| **P3** | danach |
| **NEIN** | bewusst nicht als Plattformdienst |
| **Eigen** | eigene Rust-Implementierung |
| **Eigen+Bib** | eigener Dienst auf etablierten Bibliotheken |
| **Extern** | fertiges Produkt hinter einer Prozessgrenze, nur mit Begründung |

## Grundregel: Eigenentwicklung bevorzugt

Seit dem 2026-11-12 gilt: **Eigenentwicklung vorziehen, wo sinnvoll.** Steuerungs-, Richtlinien- und Workflow-Logik baut die
Plattform selbst – das passt zum Raft-basierten Zustand, zur Autorisierung mit Cedar, zur Gleichwertigkeit von API, Portal und
MCP sowie zur Mandantentrennung (siehe [Rust-Stack](rust-stack.html) und [API-first](api-first.html)).

**Extern** bleiben Komponenten mit sehr großem Pflege- oder Reifeaufwand, immer über eine Prozessgrenze eingebunden:

- **Datenbank- und Protokoll-Engines** (PostgreSQL, MariaDB, Valkey, Kafka, OpenSearch, ClickHouse) – Kompatibilität ist hier
  der Zweck, ein Nachbau brächte keinen Nutzen. Leitplanke: „keine eigene Datenbank“ (siehe [Vision](vision.html)).
- **Hypervisor, Kubernetes, Container-Runtime** – sicherheits- und kernelnah, große Reifeinvestition.
- **Inferenz-Engines** – sie hängen an GPU-Kernel-Ökosystemen (siehe [KI-Plattform](ki-plattform.html)).
- **Wissensbasen, die ständig gepflegt werden müssen** – Schwachstellendatenbanken der Scanner, DLP-Erkenner.
- **Python-Ökosysteme** wie Airflow, Spark, Jupyter oder Fine-Tuning-Frameworks.

Auch bei externen Engines gilt: **Steuerung, API, Mandantentrennung, Backup und Metering sind Eigenentwicklung.**
Eine Ausnahme von „keine eigene Datenbank“ sind Block- und Objektspeicher, die nach einer eigenen Entscheidung selbst entwickelt
werden (siehe [Speicher](speicher.html)).

Alle Komponenten müssen OSI-konforme Lizenzen haben. Deshalb ausgeschlossen sind unter anderem HashiCorp Vault, Packer und
Nomad (BUSL), neuere Versionen von CockroachDB, ScyllaDB und EMQX, MongoDB (SSPL), Redpanda und Restate (siehe
[Lizenz und Governance](lizenz-governance.html)).

## Teil A – Infrastruktur

### Compute

| Funktion | AWS / Azure / GCP | Umsetzung | Prio |
|---|---|---|---|
| Virtuelle Maschinen | EC2 / Virtual Machines / Compute Engine | Eigen, Hypervisor extern | MVP |
| Größenänderung, Hotplug | Resize / VM Sizes / Custom Machine Types | Eigen | P2 |
| Live-Migration | intern / Live Migration / Live Migration | Eigen (Orchestrierung) | P2 |
| Spot- und dedizierte Hosts | Spot, Dedicated Hosts / Spot, Dedicated Host / Spot, Sole-tenant | Eigen | P2 |
| Autoscaling-Gruppen, Instanz-Vorlagen | Auto Scaling / Scale Sets / Managed Instance Groups | Eigen | P2 |
| Images, Galerie, Versionen | AMIs / Compute Gallery / Image Families | Eigen | MVP / P2 |
| VM-Snapshots | EBS Snapshots / Restore Points / Machine Images | Eigen | P2 |
| Affinität / Anti-Affinität | Placement Groups / Proximity Placement / Placement Policies | Eigen | MVP-nah / P2 |
| Verfügbarkeitszonen | Availability Zones / Zones / Zones | Eigen | P2 |
| vTPM, Secure Boot für Gäste | NitroTPM / Trusted Launch / Shielded VM | Eigen + swtpm | P2 |
| Confidential Computing | SEV-SNP / Confidential VMs / Confidential VMs | Eigen (Attestierung) + Extern | P3 |
| Bare Metal für Mandanten | `*.metal` / BareMetal / Bare Metal Solution | Eigen (auf Boot und Adoption) | P3 |

Der Hypervisor bleibt extern (Cloud Hypervisor, selbst in Rust geschrieben); alles darüber – Lebenszyklus, Platzierung, Images,
Metadaten – ist eigen.

### Container, Kubernetes, Serverless

| Funktion | AWS / Azure / GCP | Umsetzung | Prio |
|---|---|---|---|
| Container Instances (MicroVM-isoliert) | Fargate / Container Instances / Cloud Run | Eigen, Runtime extern | MVP |
| Managed Kubernetes | EKS / AKS / GKE | Eigen (Lebenszyklus), k3s extern | MVP |
| Kubernetes-Integration (CSI, CCM, CNI) | diverse | Eigen | MVP / P2 |
| Knotenpool-Autoscaling | Karpenter / Node Auto-Provisioning / NAP | Eigen | P2 |
| Container-Registry | ECR / ACR / Artifact Registry | Extern (zot) | MVP |
| Functions | Lambda / Functions / Cloud Run functions | Eigen+Bib (wasmtime) | P2 |
| Container-Serverless | ECS Express Mode / Container Apps / Cloud Run | Eigen | P2 |
| Geplante Jobs | EventBridge Scheduler / Timer / Cloud Scheduler | Eigen | P2 |
| Static Web Hosting | Amplify / Static Web Apps / Firebase Hosting | Eigen + Objektspeicher | P2 |
| Batch | AWS Batch / Azure Batch / Batch | Eigen | P3 |
| PaaS aus Quellcode | Beanstalk / App Service / App Engine | Eigen + Buildpacks | P3 |
| Service Mesh | VPC Lattice / Istio-Add-on / Cloud Service Mesh | Extern als Add-on | P3 |

### Netzwerk

| Funktion | AWS / Azure / GCP | Umsetzung | Prio |
|---|---|---|---|
| VPC, Subnetze, Security Groups | VPC / VNet / VPC | Eigen (nftables) | MVP |
| IPAM, DHCP, internes DNS, NAT, Floating IPs | diverse | Eigen | MVP |
| L4-Load-Balancer | NLB / Load Balancer / Network LB | Eigen | MVP |
| DDoS-Grundschutz | Shield / DDoS Protection / Cloud Armor | Eigen (nftables/XDP) | MVP / P2 |
| Netz-ACLs, Routentabellen, Peering, IPv6 | diverse | Eigen | P2 |
| Site-to-Site- und Client-VPN | VPN / VPN Gateway / Cloud VPN | Eigen (WireGuard) | P2 |
| Private Endpoints | PrivateLink / Private Link / Private Service Connect | Eigen | P2 |
| L7-Load-Balancer mit ACME | ALB / Application Gateway / Application LB | Eigen+Bib | P2 |
| DNS öffentlich/privat, DNSSEC | Route 53 / Azure DNS / Cloud DNS | Eigen+Bib | P2 |
| Flow-Logs, Bandbreitenlimits | Flow Logs / Network Watcher / Flow Logs | Eigen | P2 |
| CDN, WAF, zentrale Firewall | CloudFront, WAF / Front Door / Cloud CDN, Armor | Eigen+Bib | P3 |
| Transit-Hub, dedizierte Leitungen, BGP | Transit Gateway / Virtual WAN / NCC | Eigen | P3 |

Details zum Netzdesign: [Netzwerk](netzwerk.html).

### Speicher, Edge und Hybrid

| Funktion | AWS / Azure / GCP | Umsetzung | Prio |
|---|---|---|---|
| Block-Volumes, Snapshots, Verschlüsselung mit Mandantenschlüssel | EBS / Managed Disks / Persistent Disk | Eigen | MVP / P2 |
| Objektspeicher S3 | S3 / Blob Storage / Cloud Storage | eigenes Gateway, Engine zunächst extern | MVP |
| Versionierung, Object Lock (WORM) | S3 Object Lock / Immutable Storage / Bucket Lock | Eigen (eigener Objektspeicher) | Release 1.x |
| Lifecycle-Regeln | S3 Lifecycle / Lifecycle Management / OLM | Eigen | P2 |
| Datei-Speicher NFS/SMB | EFS, FSx / Azure Files / Filestore | Extern + Eigen | P2 |
| Backup-Dienst für Mandanten | AWS Backup / Azure Backup / Backup and DR | Eigen+Bib | P2 / Release 1.x |
| Archiv, regionsübergreifende Replikation | Glacier / Archive Tier / Archive | Eigen | P3 |
| Plattform vor Ort beim Kunden | Outposts / Azure Local / Distributed Cloud | Eigen (immanent) | MVP / P2 |
| Air-gapped-Betrieb | eingeschränkt / Stack Hub / GDC air-gapped | Eigen | P2 |
| HPC-Cluster, RDMA | ParallelCluster, EFA / CycleCloud / Cluster Toolkit | Eigen + Extern | P3 |

Eine dezentrale Plattform, die beim Betreiber selbst läuft, deckt Szenarien wie Outposts oder Azure Local von Haus aus ab.

## Teil B – Daten, KI und Integration

Nichts aus diesem Bereich liegt im MVP. Datenbank-Engines bleiben extern; die Steuerung (API, Lebenszyklus, Backup, Metering)
ist eigen.

| Funktion | AWS / Azure / GCP | Umsetzung | Prio |
|---|---|---|---|
| Managed PostgreSQL, MySQL/MariaDB | RDS, Aurora / Azure Database / Cloud SQL | Steuerung eigen, Engine extern | P2 |
| In-Memory-Cache | ElastiCache / Managed Redis / Memorystore | Steuerung eigen, Engine extern | P2 |
| Queues, Pub/Sub, Event-Bus, Datenströme | SQS, SNS, Kinesis / Service Bus, Event Hubs / Pub/Sub | Eigen+Bib | P2 |
| Plattform-Ereignisse | EventBridge / Event Grid / Eventarc | Eigen | P2 |
| Workflow-Dienst mit Zeitplaner | Step Functions / Logic Apps / Workflows | Eigen | P2 |
| Benachrichtigungen, E-Mail-Versand | SNS, SES / Communication Services / – | Eigen bzw. Eigen+Bib | P2 |
| Modellkatalog, Model Registry | Bedrock, SageMaker / Foundry / Vertex AI | Eigen | P2 |
| Inferenz-Endpunkte, Batch-Inferenz | Bedrock / Azure OpenAI / Vertex AI | Steuerung eigen, Engine extern | P2 |
| AI-Gateway | Bedrock / API Management AI Gateway / Apigee | Eigen | P2 |
| Guardrails | Bedrock Guardrails / Content Safety / Model Armor | Eigen+Bib | P2 |
| Vektorsuche, RAG | Knowledge Bases / AI Search / Vector Search | Eigen+Bib | P2 |
| Agenten-Laufzeit | AgentCore / Foundry Agent Service / Agent Engine | Eigen | P3 |
| KI-Fertigdienste (Sprache, OCR, Übersetzung, Vision) | Transcribe, Textract / Speech, Document Intelligence / Speech, Document AI | Eigen+Bib | P3 |
| Fine-Tuning, Notebooks, ML-Training | SageMaker / Azure ML / Vertex AI | Extern bzw. Eigen+Bib | P3 |
| NoSQL (Dokument, Key-Value, Wide-Column, Graph, Zeitreihen) | DynamoDB, DocumentDB / Cosmos DB / Firestore, Bigtable | überwiegend Extern | P3 |
| Lakehouse, serverless SQL auf Objektspeicher | Athena, Glue / Fabric / BigQuery, BigLake | Eigen+Bib | P3 |
| Volltextsuche, Data Warehouse, Kafka, Stream-Processing | OpenSearch, Redshift, MSK / AI Search, Fabric, Event Hubs / BigQuery | Extern | P3 |
| API-Management | API Gateway / API Management / Apigee | Eigen+Bib | P3 |
| IoT-Hub mit Gerätezwilling | IoT Core / IoT Hub / – | Eigen+Bib | P3 |

Bemerkenswert: Alle drei Hyperscaler haben 2025 dedizierte Agenten-Dienste eingeführt – das passt zum MCP-first-Ansatz von
BYOC. KI-Fertigdienste entstehen als dünne, stabile APIs über Modellvorlagen auf den Inferenz-Endpunkten, nicht als
eigener Dienst je Modell. Ein IoT-Hub hat hohe Homelab-Relevanz und bietet Differenzierung, da Google seinen Dienst eingestellt hat.

## Teil C – Identität, Sicherheit, Betrieb, Entwickler

### Identität, Governance, Schlüssel

| Funktion | AWS / Azure / GCP | Umsetzung | Prio |
|---|---|---|---|
| SSO, MFA/Passkeys, OIDC-Föderation | Identity Center / Entra ID / Cloud Identity | Eigen+Bib | MVP |
| Nutzer, Gruppen, Dienstkonten, Workload-Identitäten | IAM / Managed Identities / Service Accounts | Eigen | MVP |
| Feingranulare Autorisierung, Leitplanken | IAM Policies, SCPs / RBAC, Azure Policy / IAM Conditions, Org Policy | Eigen+Bib | MVP |
| Audit-Log, sichtbare Betreiberzugriffe | CloudTrail / Activity Log, Customer Lockbox / Audit Logs, Access Transparency | Eigen | MVP |
| Hierarchie, Labels, Kontingente | Organizations / Management Groups / Resource Manager | Eigen | MVP |
| SAML, SCIM, B2B-Gäste, Just-in-Time-Rechte | Identity Center / Entra ID, PIM / PAM | Eigen | P2 |
| Laufende Konfigurations-Compliance | AWS Config / Azure Policy / Security Command Center | Eigen | P2 |
| Plattform-KMS, Krypto-Löschung, SSH-CA | KMS / Key Vault / Cloud KMS | Eigen+Bib | MVP |
| Mandanten-Schlüssel-API, BYOK/HYOK | KMS CMK, XKS / Managed HSM / EKM | Eigen | P2 |
| Secrets Manager | Secrets Manager / Key Vault / Secret Manager | Eigen | P2 |
| Öffentliche Zertifikate, private CA | ACM, Private CA / Key Vault / CAS | Eigen+Bib | P2 |

Siehe auch [Identität und Rechte](identitaet.html) und [Kryptografie](kryptografie.html).

### Sicherheit, Compliance, Betrieb

| Funktion | AWS / Azure / GCP | Umsetzung | Prio |
|---|---|---|---|
| Knotenhärtung, Lieferkette (SBOM, Signatur) | Nitro, Signer / – / Shielded VM, Binary Authorization | Eigen+Bib | MVP |
| Nachweis-Sammlung, souveräne Umgebungen | Audit Manager / Compliance Manager / Assured Workloads | Eigen | MVP |
| Sicherheitslage (CSPM), Schwachstellenscan | Security Hub, Inspector / Defender / SCC | Eigen bzw. Extern (Scanner) | P2 |
| Bastion, Zero-Trust-App-Zugang | Session Manager, Verified Access / Bastion / IAP | Eigen | P2 |
| Trust-Portal, Compliance-Bewertung | Artifact / Service Trust Portal / Compliance Reports | Eigen | P2 |
| Plattform-Telemetrie, Betreiber-Alarme | CloudWatch / Azure Monitor / Cloud Monitoring | Erfassung eigen, Speicher extern | MVP |
| Mandanten-Metriken, -Logs, Dashboards, Uptime | CloudWatch / Log Analytics / Cloud Logging | Eigen | P2 |
| Metering | CUR / Cost Exports / Billing Export | Eigen | MVP |
| Kostenanalyse, Budgets, Rechnungen | Cost Explorer / Cost Management / Cloud Billing | Eigen | P2 |
| Automation, Runbooks | Systems Manager / Azure Automation / Workflows | Eigen | P2 |
| Bedrohungserkennung, DLP, Forensik | GuardDuty, Macie / Defender, Purview / SCC | Eigen+Bib bzw. Extern | P3 |
| Disaster Recovery, Chaos-Engineering | Elastic DR, FIS / Site Recovery, Chaos Studio / – | Eigen | P3 |

Ein Alleinstellungsmerkmal im Homelab: Kostenanalyse mit **Energiekosten je Knoten** (Leistungsaufnahme × Strompreis).

### Entwickler und Marketplace

| Funktion | AWS / Azure / GCP | Umsetzung | Prio |
|---|---|---|---|
| CLI, MCP-Zugang für KI-Agenten | AWS CLI / Azure CLI / gcloud | Eigen | MVP |
| OpenTofu-Provider | AWS-, Azure- und Google-Provider | Eigen | P2 |
| Native deklarative Stacks mit Drift-Erkennung | CloudFormation / Bicep, Deployment Stacks / Infrastructure Manager | Eigen | P2 |
| SDKs (Rust, Go, Python, TypeScript), API-Explorer | SDKs / SDKs / Client Libraries | Eigen+Bib | P2 |
| Browser-Shell | CloudShell / Cloud Shell / Cloud Shell | Eigen | P2 |
| Marketplace, Self-Service-Registrierung, Support-Fälle, Status-Seite | Marketplace / Marketplace / Marketplace | Eigen | P2 |
| Pulumi | Pulumi-Provider | über Brücke aus dem OpenTofu-Provider | P3 |

## Wichtigste Lücken bis Release 1.0

Die größten Lücken gegenüber den Hyperscalern, die bis Release 1.0 bzw. 1.x geschlossen werden sollen:

1. **Backup-Dienst für Mandanten** – Richtlinien über Labels, Aufbewahrung, unveränderliche Tresore, Kopie an einen zweiten
   Standort, geführte Wiederherstellung. Im Homelab besonders gefragt.
2. **Mandanten-Observability** – getrennte Metriken und Logs mit Abfrage-API, Alarmregeln als API-Ressourcen, Dashboards im Portal.
3. **L7-Load-Balancer mit ACME-Zertifikaten** – der Einstiegsfall für fast jeden Webdienst; Basis für WAF, CDN, Static Hosting
   und Container-Serverless.
4. **Autoscaling-Gruppen und Container-Serverless** – „n gleiche Instanzen hinter einem Load-Balancer, selbstheilend“.
5. **Laufende Konfigurations-Compliance** – Bewertung des Bestands mit Konformitätspaketen (etwa „BSI-Basis“), Verlauf und
   automatischer Behebung (siehe [Compliance-Anforderungen](compliance-anforderungen.html)).
6. **Identitätsgebundener Zugang** (Bastion, Zero-Trust) sowie **Zertifikatsdienst und private CA**.
7. **Benachrichtigungs-, E-Mail- und Workflow-Dienst** als gemeinsamer Querschnitt statt Einzellösungen je Komponente.
8. **VPN, Private Endpoints, FinOps, SDKs und Deployment-Stacks.**

Objekt-Versionierung und Object Lock wurden auf Release 1.x verschoben, weil sie einen eigenen Objektspeicher voraussetzen.

## Bewusst nicht (NEIN)

| Funktion | Grund |
|---|---|
| Gateway-Load-Balancer für Inline-Appliances | Appliance-Ökosystem fehlt; über Routentabellen und Firewall-VM abbildbar |
| Offline-Transfer-Appliances | Hardware-Logistik, kein Softwareprodukt |
| Speicher-Gateway / Hybrid-Datei-Sync | die Plattform ist bereits lokal; Sync-Clients sind Mandanten-Software |
| Globaler Anycast-LB | setzt eigenes Anycast-Netz voraus; GeoDNS als späterer Ersatz |
| IoT-Edge-Laufzeit, Digital Twins | anderes Produkt bzw. Nische; Kleingeräte werden als Knoten adoptiert |
| Eigener Hypervisor, eigenes verteiltes Dateisystem, eigene Kubernetes-Distribution | Nicht-Ziele; Sicherheitsreife und Komplexität |
| SQL Server / Oracle managed | proprietäre Lizenzen; als VM-Vorlage selbst betreibbar |
| Daten-Governance-Katalog, Feature Store, Daten-Labeling | Nische; als Marketplace-Vorlage möglich |
| Textanalyse-API | durch LLM-Endpunkte abgedeckt |
| KI-Coding- und Office-Assistenten | Endnutzerprodukte, kein Plattformdienst; Anbindung über das AI-Gateway |
| Gesichtserkennung | Nähe zu verbotenen bzw. Hochrisiko-Praktiken nach AI Act, Datenschutz |
| iPaaS-Konnektoren | Pflegeaufwand für hunderte SaaS-APIs |
| Blockchain, Quantencomputing | keine Nachfrage bzw. kein Souveränitätsgewinn |
| Dediziertes HSM als Mandantendienst | BYOK/HYOK deckt den Bedarf regulierter Mandanten |
| CDK | OpenTofu, Pulumi, native Stacks und SDKs reichen |
| CI/CD, Git-Hosting, Paket-Repositories, Dev-Umgebungen als Dienst | wäre ein zweites Produkt; stattdessen Marketplace-Vorlagen |

**SIEM/SOAR** stand zunächst auf der NEIN-Liste, wurde im Review aber als späteres Paket zurückgeholt: Erkennungsregeln entstehen
eigen auf dem Audit-Stream; Audit-, Flow- und Sicherheitsbefunde werden zusätzlich als Stream exportiert, damit Mandanten ihr
eigenes SIEM anbinden können.

## Ausgewählte Festlegungen für bestehende Bausteine

- **Telemetrie:** Erfassung, Alarmauswertung, Benachrichtigung, Dashboards und das mandantentrennende Abfrage-Gateway sind eigen;
  der Speicher für Metriken und Logs bleibt extern. Grafana ist keine Pflichtkomponente.
- **Secrets Manager:** eigen statt eines zusätzlichen Produkts – Schlüsselhierarchie und Raft-Zustand sind vorhanden, und ein
  zweiter Konsensdienst widerspräche dem Grundsatz „ein Konsensmechanismus“ (siehe [Steuerungsebene](steuerungsebene.html)).
- **Abrechnung:** eigen, da die Metering-Daten ohnehin in der Plattform liegen.
- **Infrastructure as Code:** eigener OpenTofu-Provider, aus der OpenAPI-Beschreibung generiert; Pulumi über eine Brücke statt
  eines zweiten Pakets.
- **Container-Registry:** zot bleibt (Apache-2.0, Prozessgrenze), ergänzt um Image-Scan und Signaturprüfung bei der Zulassung.
- **AI-Gateway:** eigenes, in Rust entwickeltes Gateway (siehe [KI-Plattform](ki-plattform.html)).
