title: Funktionsumfang
summary: Welche Dienste, Rollen und Plattformfunktionen cloud-project bereitstellt – vom Knoten-Lebenszyklus über Netz, Speicher und Identität bis zur KI-Inferenz.
toc: ja
---
## Dienste wie bei einem Hyperscaler

Die Plattform bietet Grunddienste, die sich an den bekannten öffentlichen Clouds orientieren. Alle
Dienste sind Ressourcen derselben API und damit gleichermaßen über Portal, API und MCP nutzbar.

| Kategorie | Dienst | Entspricht etwa |
|---|---|---|
| Compute | Virtuelle Maschinen (Cloud Hypervisor/KVM) | AWS EC2 · Azure VMs · Compute Engine |
| Compute | Container Instances (MicroVM-isoliert) | Fargate · Azure Container Instances · Cloud Run |
| Compute | Managed Kubernetes | EKS · AKS · GKE |
| Speicher | Block-Volumes | EBS · Managed Disks · Persistent Disk |
| Speicher | Objektspeicher (S3-kompatibel) | S3 · Blob Storage · Cloud Storage |
| Speicher | Dateispeicher (NFS) | EFS · Azure Files · Filestore |
| Netzwerk | VPCs, Subnetze, Sicherheitsgruppen, Load Balancer, Floating IPs | VPC · VNet · VPC |
| Netzwerk | Plattform-DNS mit DNSSEC | Route 53 · Azure DNS · Cloud DNS |
| Identität | Mandanten, Projekte, Nutzer, Rollen, Dienstkonten, API-Schlüssel | IAM · Entra ID · Cloud IAM |
| Plattform | Registry, Schlüsselverwaltung (KMS), Monitoring, Audit-Log | ECR · Key Vault · CloudWatch · CloudTrail |
| KI | Modellkatalog, Inferenz-Endpunkte, AI-Gateway, Vektorsuche | Bedrock · Azure AI Foundry · Vertex AI |

Weitere Dienste – Datenbanken, Secrets, Warteschlangen, Serverless-Funktionen, GPU/NPU-Pools –
folgen in späteren Phasen. Eine detaillierte Gegenüberstellung mit AWS, Azure und Google Cloud
steht in der [Hyperscaler-Funktionsanalyse](doku/funktionsanalyse.html).

## Drei gleichwertige Zugänge

Jede Funktion ist über **REST-API (OpenAPI)**, **Web-Portal** und **MCP** (Model Context Protocol,
für KI-Assistenten und Agenten) verfügbar – auf jeder Ebene: Plattform, Mandant, Projekt, Ressource.
Portal und MCP-Werkzeuge werden aus demselben API-Schema abgeleitet; eine CI-Prüfung verhindert,
dass ein Zugang Funktionen bekommt, die den anderen fehlen. Dazu kommt das Kommandozeilenwerkzeug
`cpctl`. Details: [API-first-Prinzip](doku/api-first.html).

```yaml
# Beispiel einer Ressource (vereinfacht)
apiVersion: compute.cloud-project.io/v1
kind: VirtualMachine
metadata:
  name: web-01
  parent: cp:global:tenant/acme/project/shop
  labels: { env: prod }
spec:                       # gewünschter Zustand
  machineType: small-2c-4g
  arch: any                 # arm64 | x86_64 | any
  image: cp:global:image/debian-13
  network: { vpc: default, subnet: web }
status:                     # tatsächlicher Zustand, schreibt nur das System
  phase: Running
```

## Rollen

Jeder Knoten trägt den Agenten `cp-agent`. Weitere Aufgaben übernimmt er über **Rollen**, die
manuell, per Regel (etwa „alle Knoten mit mindestens zwei Platten → `storage-block`“) oder auf
Vorschlag des Planers zugewiesen werden.

| Rolle | Aufgabe |
|---|---|
| `agent` | implizit auf jedem Knoten: Lebenszyklus, lokale API, Portal und MCP, Weiterleitung |
| `control` | Steuerungsgruppe (Raft) einer Zelle |
| `witness` | reine Quorum-Stimme, z. B. auf einem kleinen Raspberry Pi |
| `boot` | Netzboot-Dienst: proxyDHCP, TFTP/HTTP-Boot, Image-Cache |
| `dns` | Plattform-DNS: autoritative Zonen, DNSSEC, virtuelle IPs |
| `identity` | OIDC-/OAuth-Autorisierungsserver, Nutzer, Mandanten, Föderation |
| `kms` | Schlüsselverwaltung, Mandantenschlüssel |
| `network-gateway` | Nord-Süd-Verkehr, NAT, Load Balancer, Floating IPs |
| `compute-vm` | virtuelle Maschinen |
| `compute-container` | Container Instances in MicroVMs |
| `kubernetes` | Managed Kubernetes für Mandanten |
| `storage-block` | Block-Volumes |
| `storage-object` | S3-kompatibler Objektspeicher |
| `observability` | Metriken, Logs, Traces |

## Knoten-Lebenszyklus

Ein Knoten durchläuft einen klar definierten Lebenszyklus. Unbekannte Hardware erhält **nie
automatisch** Zugriff auf Mandantendaten – erst die Adoption vergibt eine Identität.

::: html
<figure class="diagram" role="group" aria-labelledby="lz-cap">
<svg viewBox="0 0 860 330" role="img" aria-labelledby="lz-t lz-d">
<title id="lz-t">Zustandsdiagramm des Knoten-Lebenszyklus</title>
<desc id="lz-d">Entdeckt, Inventarisiert, Wartend, Adoptiert, Bereitgestellt, Aktiv. Von Aktiv in Wartung und zurück, in Gestört und durch Selbstheilung zurück. Aus jedem adoptierten Zustand in Quarantäne. Aus Wartung oder Quarantäne in Stillgelegt. Wartend kann auch Abgelehnt werden.</desc>
<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="arrowhead" d="M0,0 L10,5 L0,10 z"/></marker></defs>
<rect class="box" x="10" y="40" width="110" height="44" rx="8"/><text x="65" y="67" text-anchor="middle">Entdeckt</text>
<rect class="box" x="150" y="40" width="130" height="44" rx="8"/><text x="215" y="67" text-anchor="middle">Inventarisiert</text>
<rect class="box4" x="310" y="40" width="110" height="44" rx="8"/><text x="365" y="67" text-anchor="middle">Wartend</text>
<rect class="box2" x="450" y="40" width="110" height="44" rx="8"/><text x="505" y="67" text-anchor="middle">Adoptiert</text>
<rect class="box2" x="590" y="40" width="140" height="44" rx="8"/><text x="660" y="67" text-anchor="middle">Bereitgestellt</text>
<rect class="box3" x="590" y="150" width="140" height="44" rx="8"/><text x="660" y="177" text-anchor="middle" class="b">Aktiv</text>
<rect class="box" x="760" y="150" width="90" height="44" rx="8"/><text x="805" y="177" text-anchor="middle">Wartung</text>
<rect class="box" x="450" y="150" width="110" height="44" rx="8"/><text x="505" y="177" text-anchor="middle">Gestört</text>
<rect class="box4" x="590" y="260" width="140" height="44" rx="8"/><text x="660" y="287" text-anchor="middle">Quarantäne</text>
<rect class="box" x="760" y="260" width="90" height="44" rx="8"/><text x="805" y="287" text-anchor="middle">Stillgelegt</text>
<rect class="box" x="310" y="150" width="110" height="44" rx="8"/><text x="365" y="177" text-anchor="middle">Abgelehnt</text>
<path class="ln" d="M120 62 H148" marker-end="url(#ah)"/>
<path class="ln" d="M280 62 H308" marker-end="url(#ah)"/>
<path class="ln" d="M420 62 H448" marker-end="url(#ah)"/><text x="434" y="32" text-anchor="middle" class="s">Freigabe</text>
<path class="ln dash" d="M215 40 V20 H505 V38" marker-end="url(#ah)"/><text x="360" y="15" text-anchor="middle" class="s">Auto-Adopt-Regel</text>
<path class="ln" d="M560 62 H588" marker-end="url(#ah)"/>
<path class="ln" d="M660 84 V148" marker-end="url(#ah)"/><text x="666" y="122" class="s">Rollen zugewiesen, gesund</text>
<path class="ln" d="M730 165 H758" marker-end="url(#ah)"/><path class="ln" d="M758 182 H732" marker-end="url(#ah)"/>
<path class="ln" d="M590 165 H562" marker-end="url(#ah)"/><path class="ln" d="M562 182 H588" marker-end="url(#ah)"/><text x="575" y="212" text-anchor="middle" class="s">Selbstheilung</text>
<path class="ln" d="M365 84 V148" marker-end="url(#ah)"/><text x="371" y="122" class="s">Ablehnung</text>
<path class="ln" d="M660 194 V258" marker-end="url(#ah)"/><text x="666" y="232" class="s">Integrität fraglich</text>
<path class="ln dash" d="M505 194 V282 H588" marker-end="url(#ah)"/>
<path class="ln" d="M730 282 H758" marker-end="url(#ah)"/>
<path class="ln" d="M805 194 V258" marker-end="url(#ah)"/><text x="811" y="232" class="s">Drain</text>
</svg>
<figcaption id="lz-cap">Knoten-Lebenszyklus (vereinfacht). Quarantäne ist aus jedem adoptierten Zustand erreichbar; die Rückkehr erfordert frische Attestierung und menschliche Freigabe.</figcaption>
</figure>
:::

- **Entdecken:** Ein neuer Knoten bootet per Netz (PXE/HTTP-Boot, Raspberry-Pi-Netzboot) oder vom
  USB-Stick in ein Discovery-System im Arbeitsspeicher. Es schreibt nichts auf Platten und meldet
  einen Hardware-Steckbrief.
- **Adoptieren:** Freigabe per Portal, API oder MCP – geschützt durch einen Bestätigungscode, ab
  höherer Ausbaustufe zusätzlich durch TPM-Attestierung. Der private Knotenschlüssel verlässt den
  Knoten nie.
- **Bereitstellen:** Installation des signierten OS-Images (oder Diskless-Betrieb), Ausstellung des
  Knotenzertifikats, Aufnahme in Underlay-Netz und Gossip.
- **Betreiben:** Rollen zuweisen, Wartung mit Drain, Selbstheilung bei Störungen.
- **Stilllegen:** nachweisbares Löschen, Widerruf des Zertifikats, Rotation der Gossip-Schlüssel –
  mit Löschnachweis für die Compliance.

Mehr: [Boot und Adoption](doku/boot-adoption.html).

## Updates und Releases

- **Unveränderliches OS-Image (cpOS):** `/usr` ist schreibgeschützt und per dm-verity gesichert, `/`
  ist flüchtig, Zustand liegt in einer verschlüsselten Partition.
- **A/B-Updates mit automatischem Rückfall:** Das Update wird in den inaktiven Slot geschrieben. Erst
  wenn ein **Health-Gate** nach dem Neustart grün meldet, gilt der neue Stand; sonst fällt der
  Knoten nach wenigen Versuchen selbstständig auf den alten Slot zurück.
- **Signierte Release-Bündel:** Images, Erweiterungen und Agent werden als Bündel mit Manifest,
  Prüfsummen, SBOM und Signaturen ausgeliefert; Update-Metadaten folgen dem Prinzip von TUF
  (The Update Framework) mit Offline-Wurzelschlüsseln.
- **Rollout-Controller:** Updates laufen in Wellen mit Kanarienvogel-Stufe, Wartungsfenstern und
  `maxUnavailable`. Höchstens ein Voter je Zelle wird gleichzeitig aktualisiert, der Leader zuletzt.
  Schlägt ein Gate fehl, hält der Rollout an.

Mehr: [OS-Image](doku/os-image.html) · [Rollout](doku/rollout.html) ·
[Release-Bündel](doku/release-buendel.html) · [Release-Signatur](doku/release-signatur.html).

## Plattform-DNS

Die Rolle `dns` (Dienst `cp-dnsd`) beantwortet die Namen der Plattform und der Mandanten
autoritativ, signiert Zonen mit **DNSSEC**, vergibt **virtuelle IP-Adressen (VIPs)** für
Plattformdienste wie Portal und API und schützt sich mit Ratenbegrenzung gegen Missbrauch.
Innerhalb der Mandantennetze beantwortet jeder Host DNS, DHCP und Metadaten lokal – ohne zentralen
Dienst im Datenpfad. Mehr: [Plattform-DNS](doku/dns.html).

## Identität und Mandanten

- Hierarchie **Plattform → Mandant → Projekt → Ressource**, optional Ordner innerhalb eines
  Mandanten.
- Eigener, schlanker **OIDC-/OAuth-2.1-Autorisierungsserver** mit **Passkeys zuerst**, Föderation zu
  bestehenden Identitätsanbietern (OIDC/SAML).
- Kurzlebige, sender-gebundene Tokens, die auf jedem Knoten lokal geprüft werden. Autorisierung über
  einen Beziehungsspeicher im Stil von Zanzibar plus **Cedar**-Richtlinien für Bedingungen und
  Leitplanken.
- Strikte Trennung zwischen Betreiber und Mandanteninhalten: Betreiber sehen Metadaten, Inhalte nur
  über einen begründeten, befristeten und protokollierten Zugriffsantrag.
- KI-Agenten sind ein eigener Akteurstyp; sie handeln mit der Schnittmenge aus Nutzerrechten,
  Token-Umfang und Agenten-Leitplanken.
- Mandanten-Löschung mit **Krypto-Löschung** und signiertem Löschnachweis.

Mehr: [Mandanten, Identität und Rechte](doku/identitaet.html).

## Speicher

- **Block-Volumes** über einen eigenen Rust-Datenpfad: lokal (dm-thin + dm-crypt) und repliziert
  (zwei bis drei Kopien) – derselbe Pfad von 2 bis zu tausenden Knoten.
- Metadaten in der vorhandenen Raft-Gruppe der Zelle, Nutzdaten nie im Konsens.
- **Mandantenverschlüsselung am Compute-Knoten:** Speicherknoten sehen nur Chiffrat.
- **Objektspeicher** S3-kompatibel hinter einem eigenen S3-Frontend mit Rechteprüfung und Quoten.
- **Dateispeicher** per NFS auf replizierten Volumes, im Netz des jeweiligen VPC.
- Platzierung über Fehlerdomänen, Reife-Gate vor dem Einsatz replizierter Volumes für Mandantendaten.

Mehr: [Speicherkonzept](doku/speicher.html).

## Netzwerk

- **Underlay:** ein WireGuard-Interface je Knoten, innen IPv6-only; Peers kommen ausschließlich aus
  dem replizierten Zustand. Zusätzlich ein Pre-Shared-Key aus einem Post-Quanten-Verfahren.
- **Mandanten-Overlay `cp-vnet`:** eigene Steuerung im Agenten, Linux-Kernel-Datenpfad (VRF je VPC,
  VXLAN im WireGuard-Tunnel, nftables) – keine zweite Konsensdatenbank.
- **Sicherheitsgruppen** zustandsbehaftet, eingehend standardmäßig gesperrt.
- **Nord-Süd-Verkehr** über die Rolle `network-gateway`: NAT, Floating IPs, L4-Load-Balancer; im
  Homelab per Layer-2-Bekanntgabe, im Rechenzentrum per BGP.
- Drei Ausbaustufen: `flat` (ein LAN), `vlan`, `routed` (L3 bis zum Host).

Mehr: [Netzwerkarchitektur](doku/netzwerk.html).

## Sicherheit und Compliance

- **Vertrauenskette** vom Secure Boot mit eigenen Schlüsseln der Installation über Measured Boot und
  TPM-gebundene Plattenverschlüsselung bis zu mTLS zwischen allen Diensten.
- **Knotenidentität** mit kurzlebigen Zertifikaten aus einer internen PKI, Vertrauensstufen T0–T4,
  Remote Attestation.
- **Kryptografie nach BSI TR-02102**, Krypto-Agilität und Fahrplan für Post-Quanten-Verfahren.
- **Lückenloses Audit** jeder Änderung, Break-Glass-Verfahren mit Protokollierung.
- **Compliance-by-Design:** 36 Architekturleitlinien, Anforderungskatalog aus ISO 27001, BSI
  IT-Grundschutz, BSI C5, DSGVO, NIS2 und Cyber Resilience Act; Nachweise werden exportierbar.
- **Lieferkette:** reproduzierbare Builds, SBOM je Artefakt, signierte Releases, VEX für
  Schwachstellenbewertungen.

Mehr: [Sicherheitsmodell](doku/sicherheitsmodell.html) ·
[Kryptografie](doku/kryptografie.html) · [Compliance-by-Design](doku/compliance-by-design.html).

## KI-native Plattform

- Eigene API-Gruppe für **Modelle, Modellversionen, Inferenz-Endpunkte, AI-Gateways, Budgets,
  Guardrails, Vektorindizes** und Wissensbasen.
- Inferenz-Engines (zunächst llama.cpp, dann vLLM) laufen als signierte Container hinter einem
  einheitlichen Adapter; dedizierte Endpunkte in MicroVMs mit durchgereichtem Beschleuniger.
- Zwei Betriebsmodelle: **dediziert** je Mandant oder **geteilt/serverless** mit Abrechnung je
  Token – ohne mandantenübergreifenden Cache.
- Beschleuniger (GPU, NPU) als Scheduler-Ressource, Scale-to-zero mit lokalem Modell-Cache,
  Modelle als signierte OCI-Artefakte mit Cache je Zelle.
- Die Plattform selbst ist per **MCP** steuerbar; Agenten der Mandanten nutzen Plattform-Werkzeuge
  mit eingeschränkten Rechten.
- KI-Compliance als Querschnitt: Modellkarten, Herkunft, Kennzeichnung, Protokollierung nach EU AI Act,
  Abbildung auf BSI AIC4.

Mehr: [KI-native Plattform](doku/ki-plattform.html).
