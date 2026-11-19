title: Vision, Begriffe und Abgrenzung
summary: Zielbild, Leitprinzipien, Zielgruppen, Glossar, Knotenlebenszyklus, Rollen, Skalierungsstufen und Abgrenzung von BYOC (Build Your Own Cloud).
group: konzept
order: 10
quelle: Konzept 01 (Vision, Begriffe & Abgrenzung)
---

## Zielbild

**BYOC** (kurz **BYOC**) ist eine **quelloffene, dezentrale Cloud-Plattform**. Sie nimmt beliebige Hardware – vom Raspberry Pi über Notebooks bis zum Rack-Server – per Netzwerkkabel auf und macht daraus eine **mandantenfähige Cloud mit den Grunddiensten eines Hyperscalers**. Der Einsatzbereich reicht vom Homelab mit zwei Knoten bis zum Rechenzentrum mit tausenden Knoten.

Die Kurzform für Außenstehende:

> *Kabel rein – Knoten erscheint – freigeben – Rolle zuweisen – fertig. Alles über Portal, API oder MCP.*

### Was „Hyperscaler-artig“ konkret heißt

| Kategorie | Dienst der Plattform | Entspricht etwa |
|---|---|---|
| Compute | Virtuelle Maschinen | AWS EC2, Azure VMs, GCE |
| Compute | Container Instances | Azure Container Instances, Cloud Run, Fargate |
| Compute | Managed Kubernetes | EKS, AKS, GKE |
| Speicher | Block-Volumes | EBS, Managed Disks, Persistent Disk |
| Speicher | Objektspeicher (S3-kompatibel) | S3, Blob Storage, GCS |
| Netzwerk | VPCs, Subnetze, Security Groups, Load Balancer, Floating IPs | VPC, VNet |
| Identität | Mandanten, Projekte, Nutzer, Rollen, API-Schlüssel | IAM, Entra ID, Cloud IAM |
| Plattform | Registry, KMS, Monitoring, Audit-Log | ECR, KMS, CloudWatch, CloudTrail |

In späteren Ausbaustufen kommen Datenbanken, Secrets, DNS, Queues, Serverless, Dateispeicher und GPU/NPU-Beschleuniger hinzu (siehe [Funktionsanalyse](funktionsanalyse.html) und [KI-Plattform](ki-plattform.html)).

## Leitprinzipien

1. **Dezentral, kein zentraler Controller.** Jeder Knoten trägt den Agenten; Portal, API und MCP laufen auf der Hardware, die sie steuern. Fällt ein Knoten aus, bedient ein anderer.
2. **API-first, drei gleichwertige Zugänge.** Jede Funktion auf jeder Ebene ist über API, Web-Portal und MCP verfügbar – auch Ersteinrichtung und Adoption. Die API ist die einzige Wahrheit (siehe [API-first](api-first.html)).
3. **Zero-Touch nach dem Kabel.** Nach dem Einstecken sind weder Bildschirm noch Tastatur noch SSH nötig. Einzige bewusste Handlung ist die Freigabe (Adoption) – oder eine Auto-Adopt-Regel. Auto-Adopt ist ab Werk ausgeschaltet und dauerhaft nur mit Hardware-Attestierung zulässig.
4. **Skaliert in beide Richtungen.** Zwei Knoten sind ein vollwertiger Betriebsmodus, keine Demo. Wachstum auf tausende Knoten erfolgt über Zellen und Regionen, ohne Neuinstallation.
5. **Heterogen ab Tag 1.** ARM64 und x86_64 gemischt; Knoten mit und ohne BMC, mit wenig und viel RAM.
6. **Deklarativ und selbstheilend.** Der gewünschte Zustand wird beschrieben, Reconciler stellen ihn her.
7. **Unveränderliche Knoten.** Image-basiertes Betriebssystem mit A/B-Updates; keine manuelle Pflege auf Knoten (siehe [OS-Image](os-image.html)).
8. **Secure & Compliant by Design.** mTLS überall, Mandantentrennung auf allen Schichten, Protokollierung jeder Änderung, exportierbare Nachweise für ISO 27001, BSI C5 und IT-Grundschutz (siehe [Compliance by Design](compliance-by-design.html)).
9. **Open Source durchgehend.** Nur quelloffene Abhängigkeiten; eigene Komponenten in Rust (siehe [Rust-Stack](rust-stack.html) und [Lizenz-Governance](lizenz-governance.html)).
10. **Bewährtes integrieren, Fehlendes bauen.** Kein eigener Hypervisor – das Projekt baut die Steuerungsebene, die Automatisierung und die einheitliche Oberfläche.

## Zielgruppen und Einsatzszenarien

| Stufe | Knoten | Typische Hardware | Typischer Betreiber | Besonderheit |
|---|---|---|---|---|
| **Homelab** | 2–10 | Pis, alte Notebooks, Mini-PCs, 1–2 Server | Privatperson, Entwickler | 2-Knoten-Betrieb mit Zeuge; koexistiert mit dem DHCP des Routers; ein Standort |
| **Edge / KMU** | 10–100 | Mini-PCs, Server | kleine Firma, Verein, Schule, Außenstelle | mehrere Mandanten, erste Compliance-Anforderungen |
| **Rechenzentrum** | 100–10.000+ | Rack-Server mit BMC | Hoster, Behörde, Konzern-IT | Zellen und Regionen, mehrere Standorte, Zertifizierung des Betreibers (ISO 27001 / C5) |

Der **MVP konzentriert sich auf das Homelab**. Die Architektur darf jedoch keine Entscheidung enthalten, die den Weg ins Rechenzentrum verbaut.

## Begriffe (Glossar)

### Infrastruktur

| Begriff | Bedeutung |
|---|---|
| **Plattform** | Gesamtheit aller Regionen eines Betreibers. |
| **Knoten** (Node) | Ein physisches Gerät, auf dem der Agent läuft; kleinste Einheit. |
| **Agent** | Rust-Dienst auf jedem Knoten: Lebenszyklus, Rollen, lokale API/Portal/MCP, Weiterleitung von Anfragen. |
| **Rolle** | Funktion, die ein Knoten übernimmt (z. B. `boot`, `control`, `compute-vm`). Ein Knoten kann mehrere Rollen haben. Rollen werden zugewiesen, nicht installiert. |
| **Steuerungsgruppe** (Control Group) | Kleine, automatisch gewählte Knotenmenge (3 oder 5) mit Rolle `control`, die den Zustand einer Zelle per Raft-Konsens hält. |
| **Zeugen-Knoten** (Witness) | Leichter Knoten (z. B. ein Pi), der nur abstimmt, damit 2-Knoten-Cluster ein Quorum haben. |
| **Zelle** (Cell) | Ausfall- und Skalierungseinheit mit eigener Steuerungsgruppe (Richtwert: bis etwa 500–1.000 Knoten). Zellen fallen unabhängig voneinander aus. |
| **Region** | Eine oder mehrere Zellen an einem Standort oder Verbund mit gemeinsamem Netz und gemeinsamer Regions-API. |
| **Standort** (Site) | Physischer Ort (Homelab, RZ-Raum). Standorte werden über das WireGuard-Underlay verbunden. |
| **Verbund** (Federation) | Zusammenschluss mehrerer Regionen unter einer globalen Identität und API (spätere Ausbaustufe). |
| **Underlay** | Verschlüsseltes WireGuard-Mesh zwischen Knoten – das Transportnetz der Plattform. |
| **Overlay / VPC** | Virtuelles, mandanteneigenes Netz über dem Underlay (siehe [Netzwerk](netzwerk.html)). |
| **Boot-Dienst** | Rolle `boot`: proxyDHCP, iPXE/UEFI-HTTP-Boot, Pi-Netboot, Image-Auslieferung. Mehrfach vorhanden, nie Single Point of Failure. |

### Organisation und Nutzung

| Begriff | Bedeutung |
|---|---|
| **Betreiber** (Operator) | Betreibt die Plattform; verwaltet Hardware, Regionen und Mandanten. |
| **Mandant** (Tenant) | Organisatorisch und technisch isolierter Kunde mit eigenen Nutzern, Netzen, Schlüsseln und eigener Abrechnung. |
| **Projekt** | Unterteilung innerhalb eines Mandanten; Grenze für Ressourcen, Kontingente und Rechte. |
| **Ressource** | Alles, was über die API verwaltet wird (Knoten, VM, Volume, VPC, Bucket …). Jede Ressource hat einen gewünschten und einen tatsächlichen Zustand. |
| **Dienst** (Service) | Angebot an Mandanten (VM-Dienst, Objektspeicher …), umgesetzt durch Rollen auf Knoten. |
| **Kontingent** (Quota) | Obergrenze an Ressourcen je Mandant oder Projekt. |
| **Ebene** (Scope) | Ort einer Operation: *Plattform → Region → Zelle → Knoten* (Betreiber) bzw. *Mandant → Projekt → Ressource*. Auf jeder Ebene gilt: API = Portal = MCP. |

Details zum Mandanten- und Rechtemodell beschreibt die Seite [Identität](identitaet.html).

## Knotenlebenszyklus

Jeder Knoten durchläuft einen festen Lebenszyklus, der vollständig über API, Portal oder MCP gesteuert wird:

| Zustand | Bedeutung | Übergang durch |
|---|---|---|
| **Entdeckt** | Gerät hat eine DHCP-/Boot-Anfrage gestellt | Kabel einstecken |
| **Inventarisiert** | Discovery-Image hat gebootet und Hardware gemeldet | automatisch |
| **Wartend** | Kein Auto-Adopt-Treffer; wartet auf Freigabe | automatisch |
| **Adoptiert** | Freigabe erteilt oder Auto-Adopt-Regel hat gegriffen | Portal / API / MCP oder Regel |
| **Abgelehnt** | Freigabe verweigert | Portal / API / MCP |
| **Bereitgestellt** | Identität und Zertifikat vergeben, OS-Image ausgerollt | automatisch |
| **Aktiv** | Rollen zugewiesen und gesund | automatisch |
| **Wartung** | Drain: Workloads werden verschoben | Betreiber |
| **Gestört** | Health-Check fehlgeschlagen; Selbstheilung zurück nach „Aktiv“ | automatisch |
| **Quarantäne** | Integrität fraglich | automatisch, aus jedem adoptierten Zustand |
| **Stillgelegt** | Daten sicher gelöscht, Zertifikat widerrufen | Betreiber |

Wichtige Regeln:

- **Unbekannte Hardware erhält nie automatisch Zugriff auf Mandantendaten.** Discovery läuft in einem isolierten Netz bzw. Modus; erst die Adoption vergibt eine Identität (siehe [Boot & Adoption](boot-adoption.html) und [Sicherheitsmodell](sicherheitsmodell.html)).
- **Quarantäne ist aus jedem adoptierten Zustand direkt erreichbar** (Bereitgestellt, Aktiv, Wartung, Gestört) – nicht nur über „Gestört“. Auslöser sind etwa Attestierungsfehler, Anomalie-Befunde, ein abweichender Hardware-Fingerabdruck oder ein Doppelauftritt derselben Knotenidentität; im letzten Fall werden beide Knoten in Quarantäne genommen.
- Der Weg aus der Quarantäne zurück nach „Aktiv“ erfordert eine **frische Attestierung und eine menschliche Freigabe**.
- **Stilllegung** beinhaltet nachweisbares Löschen (BSI CON.6, ISO 27001 A.7.14) – ein für die Compliance relevanter Schritt.

## Rollenkatalog (initial)

| Rolle | Aufgabe | Mindestbedarf (Richtwert) |
|---|---|---|
| `agent` *(implizit, jeder Knoten)* | Lebenszyklus, lokale API/Portal/MCP, Weiterleitung | 512 MB RAM |
| `boot` | proxyDHCP, iPXE/HTTP-Boot, Image-Cache | 1 GB RAM, Platz für Images |
| `control` | Steuerungsgruppe (Raft) einer Zelle | 2 GB RAM, SSD |
| `witness` | Nur Quorum-Stimme | Pi Zero 2 / Pi 3 genügt |
| `identity` | OIDC, Nutzer, Mandanten | 1 GB RAM |
| `network-gateway` | Nord-Süd-Verkehr, Load Balancer, Floating IPs | 2 NICs empfohlen |
| `compute-vm` | VMs (Cloud Hypervisor/KVM) | Virtualisierungserweiterung |
| `compute-container` | Container Instances (MicroVM-isoliert) | KVM empfohlen |
| `kubernetes` | Managed-Kubernetes-Steuerung für Mandanten | 2 GB RAM |
| `storage-block` | Block-Volumes | lokale Disk(s) |
| `storage-object` | S3-kompatibler Objektspeicher | lokale Disk(s) |
| `observability` | Metriken, Logs, Traces | Disk |

Rollen werden manuell, per Regel (z. B. „alle Knoten mit mindestens zwei Disks erhalten `storage-block`“) oder auf Vorschlag des Plattform-Planers zugewiesen – stets über API, Portal oder MCP.

## Skalierungsstufen der Steuerungsebene

Die Richtwerte werden auf der Seite [Steuerungsebene](steuerungsebene.html) ausführlich begründet.

| Knoten | Steuerungsgruppe | Zellen | Bemerkung |
|---|---|---|---|
| 2 | 2 + Zeuge | 1 | Zeuge (Pi oder externer Kleinstknoten) zwingend für das Quorum |
| 3–20 | 3 | 1 | Standard-Homelab |
| 20 – ca. 1.000 | 5 | 1 | Gossip für Mitgliedschaft, Raft nur für Zustand |
| > ca. 1.000 | 5 je Zelle | n | Regions-Ebene koordiniert Zellen; Ausfall einer Zelle betrifft nur sie |
| mehrere Standorte | je Region | n | Verbund mit globaler Identität |

## Abgrenzung zu bestehenden Lösungen

| Lösung | Was sie gut macht | Was für unser Ziel fehlt | Was wir übernehmen |
|---|---|---|---|
| **Canonical MAAS** | Bare-Metal-Provisionierung per PXE, Inventar, BMC | Zentraler Controller, keine Cloud-Dienste, keine Mandanten | Discovery- und Commissioning-Ablauf |
| **Tinkerbell** | Workflow-basiertes Bare-Metal-Provisioning | Zentral, nur Provisioning, kein Endnutzer-Portal | Workflow-Modell, iPXE-Ansätze |
| **Metal³ / Cluster API** | Bare Metal per Kubernetes-API | Setzt bestehenden K8s-Cluster voraus, komplex fürs Homelab | Deklaratives Ressourcenmodell |
| **OpenStack / Sovereign Cloud Stack** | Vollständige IaaS mit Mandanten; SCS mit Fokus auf Souveränität | Sehr komplex, viele zentrale Dienste, ungeeignet für 2 Pis, kein Zero-Touch | Dienstschnitt (Compute/Netz/Volumes/Identität), SCS-Standards als Referenz |
| **Apache CloudStack / OpenNebula** | Schlankere IaaS mit Mandanten | Zentrales Management, Host-Provisioning nicht integriert | Mandanten- und Abrechnungsmodelle |
| **Proxmox VE** | Einfache Virtualisierung, Cluster, Ceph | Keine echte Mandantenfähigkeit, kein Zero-Touch, kein MCP | Bedienbarkeit als Maßstab fürs Homelab |
| **Harvester** | HCI auf Kubernetes, VMs + K8s | Nur x86, hohe Mindestanforderungen | Kombination VM + K8s |
| **Talos / Omni** | Unveränderliches, API-gesteuertes OS | Nur Kubernetes-Knoten, Omni zentral | Image-/A/B-Konzept, API statt SSH |
| **Oxide Control Plane** | Rack-Cloud mit Open-Source-Steuerungsebene in Rust | An eigene Hardware gebunden | Architektur- und Rust-Erfahrungen |
| **Kubernetes allein** | Container-Orchestrierung | Kein Bare-Metal-Lebenszyklus, keine VMs/VPCs/Mandanten-Cloud | Reconciler-Muster |

**Alleinstellung:** Zero-Touch-Hardwareaufnahme, dezentrale Steuerung ohne zentralen Controller, mandantenfähige Hyperscaler-Dienste, API/Portal/MCP auf jeder Ebene, Pi bis Rechenzentrum und Compliance by Design – keine der genannten Lösungen vereint all das.

## Nicht-Ziele

- **Kein eigener Hypervisor, keine eigene Datenbank, kein verteiltes Dateisystem von Null** – bewährte Komponenten wie Cloud Hypervisor werden integriert. Präzisierung vom 2026-11-14: Block- und Objektspeicher auf Basis der Plattform-Raft und einer eigenen Chunk-Schicht sind Eigenentwicklung (Blockreplikation im Primär-Kopie-Verfahren ist kein verteiltes Dateisystem). **Ceph ist kein Pflichtbestandteil**, sondern nur ein optionaler externer Treiber für Rechenzentren mit vorhandenem Ceph (siehe [Speicher](speicher.html)).
- **Keine API-Kompatibilität zu AWS, Azure oder GCP** – Ausnahme ist der S3-kompatible Objektspeicher; Werkzeuganbindung erfolgt über OpenTofu/Terraform-Provider.
- **Kein Netzwerk-Boot über WLAN** – die Aufnahme setzt Ethernet voraus (WLAN-Knoten ggf. später per Bootstick).
- **Keine proprietären Abhängigkeiten**, auch keine „Open Core“-Zwangskomponenten.
- **Keine Kubernetes-Distribution** – Kubernetes ist ein Dienst der Plattform, nicht ihr Fundament.
- **Keine Hardware ohne 64 Bit** – Pi 1, Pi 2 und Pi Zero W sind ausgeschlossen; ein Pi Zero 2 W taugt nur als Zeuge per Bootstick.

## Erfolgskriterien für den MVP

| # | Kriterium | Messgröße |
|---|---|---|
| E1 | Erster Knoten per USB-Stick lauffähig, Einrichtung vollständig über Portal **oder** API **oder** MCP | ≤ 15 Minuten bis das Portal erreichbar ist |
| E2 | Neuer Knoten per Kabel bis „wartend“ | ≤ 5 Minuten (Pi 4/5, x86-Notebook, Server) |
| E3 | 2-Knoten-Cluster mit Zeuge übersteht den Ausfall eines Knotens | Steuerung bleibt verfügbar |
| E4 | Gemischter Cluster ARM64 + x86_64 | VMs und Container werden passend platziert |
| E5 | Zwei Mandanten vollständig getrennt | Netz, Compute, Speicher, Schlüssel; Penetrationstest ohne kritische Befunde |
| E6 | Mandant legt VM, Container Instance, K8s-Cluster, Volume und Bucket selbst an | über alle drei Zugänge |
| E7 | Paritäts-Check | 100 % der API-Operationen in Portal und MCP verfügbar |
| E8 | Kein Single Point of Failure ab 3 Knoten | Boot-Dienst, API, Portal und MCP überleben einen Knotenausfall |
| E9 | Nachweise exportierbar | Control-Matrix für C5, ISO 27001 und Grundschutz (siehe [Grundschutz](grundschutz.html)) |

## Offene Fragen zum Zeitpunkt der Vision

Einige Fragen wurden bewusst in Folgekonzepte verschoben: der endgültige Produktname (bisher Arbeitstitel), der Richtwert für Zellengröße und Steuerungsgruppe ([Steuerungsebene](steuerungsebene.html)), die Overlay-Technik ([Netzwerk](netzwerk.html)), die Basis des OS-Images ([OS-Image](os-image.html)), die Portal-Technologie ([Portal](portal.html)) sowie der Vorrang zwischen C5 und ISO 27001 bei Konflikten ([Compliance-Anforderungen](compliance-anforderungen.html)).
