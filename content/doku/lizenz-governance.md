title: Lizenz und Governance
summary: Warum der Kern von DCP unter AGPL-3.0-or-later steht, welche Lizenzen für SDKs und Doku gelten, wie Beiträge per DCO funktionieren und wie sich das Projekt im Cyber Resilience Act einordnet.
group: konzept
order: 150
quelle: Konzept 63 (ADR Lizenz und Governance)
---

> **Hinweis:** Diese Seite fasst den technischen und lizenzpolitischen Kenntnisstand des Projekts zusammen und ist keine
> Rechtsberatung. Lizenzwahl, Marke und CRA-Rolle werden vor der ersten öffentlichen Veröffentlichung juristisch geprüft.

## Ausgangslage

DCP wird überwiegend in Rust geschrieben und integriert zahlreiche Fremdkomponenten mit unterschiedlichen Lizenzen.
Die Ziele:

- **Alles Open Source** – auch keine „Open-Core“-Zwangskomponenten (siehe [Vision](vision.html)).
- Betreiber – vom Homelab über Hoster und Behörden bis zur Konzern-IT – sollen die Plattform **frei betreiben** können.
- Es soll **kein proprietärer Cloud-Fork** entstehen, der Verbesserungen einbehält und als Dienst verkauft.
- Hohe Akzeptanz bei Behörden in der EU und bei Unternehmen; möglichst viele externe Beiträge.
- Der **EU Cyber Resilience Act (CRA)** wird von Beginn an mitgedacht.

### Lizenzen der Abhängigkeiten

Die wichtigsten Fremdkomponenten – Cloud Hypervisor, Firecracker, Kata Containers, k3s, zot, Open vSwitch, Cilium – stehen
unter Apache-2.0 oder BSD-Lizenzen. Der Linux-Kernel (GPL-2.0) und iPXE (GPL-2.0-or-later) werden im OS-Image bzw. von der
Boot-Rolle ausgeliefert. Der Objektspeicher-Baustein Garage steht unter AGPL-3.0. Die Policy-Engine Cedar (Apache-2.0) wird
direkt gelinkt.

**Kernbeobachtung:** Solange Fremdkomponenten als *separate Programme* laufen – über Prozess-, Netz- oder Syscall-Grenzen –,
ist die eigene Lizenzwahl weitgehend frei. Es bleiben aber **Weitergabepflichten** (Quellcode, Lizenztexte, NOTICE) für das
ausgelieferte OS-Image. Erst das **Linken** von Copyleft-Code würde die eigene Lizenz einschränken – und das schließt die
Prozessgrenzen-Regel des Projekts aus (siehe [Rust-Stack](rust-stack.html)).

## Entscheidungstreiber

| Treiber | Gewicht |
|---|---|
| Schutz vor proprietären Forks, insbesondere der **SaaS-Lücke** (Betrieb als Dienst ohne Weitergabe) | hoch |
| Akzeptanz bei Behörden und Unternehmen, Beschaffbarkeit | hoch |
| Patentschutz (ausdrückliche Patentlizenz, Retorsionsklausel) | mittel |
| Kompatibilität mit den Abhängigkeiten | hoch |
| Beitragsbereitschaft von Einzelpersonen und Firmen | mittel bis hoch |
| Betreiberfreiheit: Betrieb ohne Gebühren und Genehmigung, auch kommerziell | Muss |
| Rechtssicherheit (Verständlichkeit, Erprobtheit, EU-Recht) | mittel |

## Bewertete Optionen

| Lizenz | Typ | SaaS-Lücke geschlossen? | Einordnung |
|---|---|---|---|
| Apache-2.0 | permissiv | nein | Standard in Cloud-native, maximale Verbreitung – schützt aber nicht vor genau dem Szenario, das verhindert werden soll |
| MPL-2.0 | schwaches Copyleft (Dateiebene) | nein | Copyleft nur bei Weitergabe und nur für geänderte Dateien |
| GPL-3.0 | starkes Copyleft | nein | reiner Netzbetrieb ist keine Weitergabe |
| **AGPL-3.0** | starkes Copyleft mit Netzklausel | **ja** | einzige weithin erprobte Lizenz, die die SaaS-Lücke schließt; in Infrastruktur verbreitet |
| EUPL-1.2 | starkes Copyleft, EU-Lizenz | weitgehend | für Behörden attraktiv, aber wenig Rechtsprechung, keine Patent-Retorsion, Kompatibilitätsklausel kann den Schutz abschwächen |

Die Erfahrungen anderer Projekte (Elasticsearch, Redis, HashiCorp) zeigen: Permissive oder schwache Lizenzen führten dort später
zu Lizenzwechseln und Brüchen mit der Community. Der Preis der AGPL: Einige Unternehmen mit internen AGPL-Verboten werden
weniger beitragen, und eine Aufnahme in die CNCF ist praktisch ausgeschlossen.

### Was die AGPL für Betreiber bedeutet

- **Unveränderter Betrieb** – auch kommerziell, als Hoster oder als Behörde: keine Pflichten über die Weitergabe der
  Lizenztexte hinaus.
- **Eigene Änderungen, die Mandanten über das Netz nutzen** (API, Portal, MCP, S3): Den Nutzern ist der Quellcode der
  geänderten Fassung anzubieten.
- **Interne Änderungen ohne externe Nutzer:** keine Pflicht.

Damit das ohne Aufwand gelingt, bringt die Plattform einen eingebauten **Quellcode-Endpunkt** mit – in API, Portal und MCP. Er
verweist automatisch auf Repository und exakten Commit bzw. Build der laufenden Version. Betreiber mit eigenen Patches tragen nur
die Adresse ihres Forks ein. Compliance wird so zum Nebeneffekt.

## Entscheidung: die Lizenzmatrix

Angenommen am 2026-11-12:

| Bestandteil | Lizenz | Begründung |
|---|---|---|
| **Kern:** Agent, Steuerungsebene, Dienste (VM, Container, Kubernetes, Speicher, Netz), Portal, MCP-Server, Image-Bau | **AGPL-3.0-or-later** | schließt die SaaS-Lücke, Patentklausel, behördentauglich |
| **SDKs, Client-Bibliotheken, CLI, OpenTofu-Provider, API-Spezifikationen, MCP-Schemata** | **Apache-2.0 OR MIT** | Clients sollen in jede – auch proprietäre – Software eingebaut werden können |
| **Dokumentation, Konzepte, Diagramme** | **CC BY 4.0** | freie Nachnutzung mit Namensnennung, etwa für Schulungen oder Behördenhandbücher |
| **Code-Beispiele, Vorlagen, Boot-Skripte, Konfigurationsbeispiele** | **MIT-0** | bedingungslos kopierbar, auch in GPL-2.0-Kontexte |
| **Build-Werkzeuge** | Apache-2.0 OR MIT | wie SDKs |
| **Eigene Kernel-Module bzw. eBPF-Programme** (falls nötig) | GPL-2.0-only OR BSD-2-Clause | Vorgabe des Kernels; Dual-Lizenz |
| **Patches an Fremdprojekten** | Lizenz des Upstreams | grundsätzlich upstreamen, keine Dauer-Forks |
| **Logos, Produktname** | keine freie Lizenz – Markenrichtlinie | Schutz vor Verwechslung durch Forks |

**EUPL-1.2** bleibt bis zur ersten Veröffentlichung eine Prüfoption. Die AGPL ist der robustere Ausgangspunkt: AGPL-Code kann
EUPL-Code aufnehmen, aber nicht umgekehrt. **„or-later“** ermöglicht ohne Rechteübertragung ein Upgrade auf eine künftige
AGPL-Version.

### Technische Umsetzung

- **REUSE-Spezifikation:** SPDX-Header in jeder Datei, zentraler Lizenzordner, automatische Prüfung in der CI.
- **Lizenz-Allowlist für Abhängigkeiten** (MIT, Apache-2.0, BSD, ISC, Zlib, Unicode-3.0 u. a.), geprüft mit `cargo-deny`. SDK-Crates
  dürfen kein Copyleft ziehen. LGPL-Bibliotheken werden nicht gelinkt. **MPL-2.0** ist nur für reine Build-Werkzeuge erlaubt,
  die nicht im ausgelieferten Artefakt landen – zur Laufzeit bleibt sie ausgeschlossen.
- **SBOM** (CycloneDX und SPDX) für jedes Release und jedes OS-Image – zugleich eine CRA-Anforderung (siehe
  [Release-Bündel](release-buendel.html)).
- **Quellcode-Angebot für das OS-Image:** zu jedem Image ein vollständiges Quellarchiv oder dauerhafte Verweise auf identische
  Quellen.
- Die Lizenzgrenze zwischen Kern und SDK ist an der Crate-Aufteilung erkennbar.

### Sonderfälle

- **Garage** wird ausschließlich als separater Dienst über die S3- bzw. Admin-API angesprochen. Eigene Patches werden upstreamt.
- **iPXE** wird als Binary ausgeliefert, daher liegen Lizenztext und Quellcode bei. Skripte werden möglichst zur Laufzeit geladen
  statt einkompiliert.
- **Linux:** Der Agent nutzt nur Syscalls, Netlink und ioctl – keine Ableitung.
- **Identität:** Ein eigener Autorisierungsserver ist Teil des Kerns; externe Identitätsanbieter werden nur per OIDC-Föderation
  angebunden, deren Lizenz ist damit ohne Belang (siehe [Identität und Rechte](identitaet.html)).

## Beiträge, Marke, Governance

### DCO statt CLA

| | DCO | CLA |
|---|---|---|
| Aufwand für Beitragende | Sign-off im Commit, kein Vertrag | Vertrag, oft mit Arbeitgeber |
| Relizenzierung durch das Projekt | nicht möglich (nur „or-later“-Upgrade) | möglich – auch Richtung proprietär |
| Vertrauen der Community | hoch | geringer, besonders bei Copyleft mit CLA |

**Entscheidung: Developer Certificate of Origin (DCO 1.1)**, durchgesetzt per CI-Prüfung des Sign-offs. Kein CLA. Damit
verpflichtet sich das Projekt glaubwürdig, **nie proprietär zu relizenzieren** – für Beitragende das stärkste Argument und ein
Ausgleich für die Skepsis gegenüber der AGPL.

### Marke

Lizenzen regeln das Urheberrecht, nicht die Marke. Der Produktname ist das wichtigste Mittel gegen verwirrende Forks mit
proprietären Zusätzen. Vorgesehen ist eine Markenrichtlinie: Unveränderte Builds und Distributionen dürfen den Namen nennen,
geänderte Forks nur als „based on …“, und Kompatibilitätsaussagen setzen bestandene **Konformitätstests** voraus (vergleichbar
mit der Kubernetes Conformance). Der Alpha-Name lautet *Das Cloud Projekt* (kurz *DCP*); Komponenten tragen das Präfix `cp` (etwa `cpctl`, `cpOS`, `cp-agent`). Technische Bezeichner wie API-Gruppen behalten vorerst die Schreibweise `cloud-project`.

### Governance-Modell

Die organisatorische Ausgestaltung (Rechtsträger, Gremien) ist bewusst noch nicht festgelegt. Als Orientierung dient ein
stufenweises Modell:

| Phase | Auslöser | Modell |
|---|---|---|
| Gründung | bis zu den ersten Releases | Kern-Maintainer; transparente Entscheidungen per ADR, öffentliche Roadmap |
| Öffnung | mehrere aktive Maintainer aus unabhängigen Organisationen oder erster größerer Produktiveinsatz | Steering Committee mit begrenzten Sitzen je Organisation, Fachgruppen (Compute, Speicher, Netz, Sicherheit) |
| Neutraler Träger | Marke, Infrastruktur und Spenden brauchen einen neutralen Rechtsträger | Stiftung oder Verein; das Steering Committee bleibt technisches Gremium |

Als neutraler Träger kommt etwa eine europäische Open-Source-Stiftung in Frage, die bereits Erfahrung mit Copyleft und mit der
Steward-Rolle nach dem CRA hat.

Ein **Code of Conduct** nach dem Contributor Covenant gilt für alle Kanäle, mit vertraulichem Meldeweg.

### Security-Policy

Die Security-Policy ist zugleich Grundlage für den CRA (siehe
[Schwachstellenmanagement](schwachstellenmanagement.html)):

- Vertraulicher Meldeweg, Eingangsbestätigung innerhalb von 72 Stunden, Standard-Embargo von 90 Tagen, bei aktiver Ausnutzung
  kürzer.
- Ein Security-Response-Team mit Vertretungsregel.
- CVE-Vergabe, maschinenlesbare Advisories (CSAF 2.0, OSV) und VEX-Aussagen zu Lücken in Abhängigkeiten.
- Vorab-Benachrichtigung registrierter Betreiber und Distributoren unter Vertraulichkeitsregeln.
- **Lieferkette:** signierte Releases und Images, SLSA-Provenance, reproduzierbare Builds als Ziel, OpenSSF Scorecard (siehe
  [Release-Signatur](release-signatur.html)).
- Veröffentlichte unterstützte Versionen und Support-Zeiträume je Release-Linie.

## Einordnung im Cyber Resilience Act

### Zeitplan

| Datum | Was gilt |
|---|---|
| Dezember 2024 | CRA in Kraft getreten |
| 11.09.2026 | Meldepflichten für Hersteller: aktiv ausgenutzte Schwachstellen und schwerwiegende Vorfälle (Frühwarnung 24 h, Meldung 72 h) |
| 11.12.2027 | volle Anwendung: wesentliche Anforderungen, Konformitätsbewertung, CE-Kennzeichnung, Pflichten der Open-Source-Stewards |

Ab wann die Meldepflicht für Open-Source-Stewards greift, wird unterschiedlich gesehen; überwiegend wird der 11.12.2027 genannt.
Das Projekt setzt seine Prozesse so auf, als gelte die Pflicht bereits – der Aufwand entspricht guter Sicherheitspraxis.

### Rollen

| Konstellation | CRA-Rolle | Folge |
|---|---|---|
| Community entwickelt ohne Gewinnerzielung, ohne juristische Person | außerhalb des Anwendungsbereichs | keine Pflichten |
| Juristische Person unterstützt die Entwicklung systematisch und nachhaltig, ohne Monetarisierung | **Open-Source-Steward** | „leichtes“ Regime, keine Geldbußen |
| Anbieter verkauft Produkt, Distribution, Appliance oder Support über Kostendeckung hinaus | **Hersteller** | volles Regime |
| Hoster betreibt die Plattform als Dienst | CRA greift nicht für reinen Dienstbetrieb; stattdessen NIS2 | Betreiber-Compliance |
| Behörde betreibt intern | weder Hersteller noch Steward | IT-Grundschutz bzw. NIS2 |

### Pflichten als Open-Source-Steward

1. Eine **dokumentierte Cybersicherheitsstrategie**, die sichere Entwicklung und den Umgang mit Schwachstellen fördert –
   umgesetzt über Security-Policy und Sicherheitshandbuch.
2. **Zusammenarbeit mit Marktüberwachungsbehörden** auf Anfrage.
3. **Meldepflichten**, soweit das Projekt beteiligt ist – etwa bei Vorfällen in der Projektinfrastruktur (Repositories, Build,
   Release-Signierung).
4. Freiwillig: eine **Sicherheitsattestierung**, die Herstellern die Sorgfaltsprüfung erleichtert.

### Spätere kommerzielle Angebote

- **Monetarisierung macht zum Hersteller.** Spenden ohne Gewinnerzielungsabsicht sind unschädlich.
- **Produktklassen:** Die Plattform enthält Bestandteile der Klasse I (Betriebssysteme, Bootmanager, Identitäts- und
  Zugriffsverwaltung, Netzwerkmanagement, PKI) und der **Klasse II** (Hypervisoren, Container-Laufzeiten). Klasse II verlangt
  grundsätzlich eine Konformitätsbewertung durch Dritte. Für **freie und quelloffene** Produkte genügt jedoch die interne
  Kontrolle, wenn die technische Dokumentation **öffentlich** ist. Deshalb wird die technische Dokumentation von Anfang an
  öffentlich geführt.
- Herstellerpflichten umfassen Security by Design, sichere Voreinstellungen, Updates, SBOM, Schwachstellenmanagement,
  Support-Zeitraum, Konformitätserklärung, CE-Kennzeichnung, Meldepflichten und Sorgfalt bei integrierten Fremdkomponenten.
- Zusätzlich gilt die neue **Produkthaftungsrichtlinie**, nach der Software ein Produkt ist.
- **Empfohlene Rollentrennung:** Der Steward ist ein gemeinnütziger Träger ohne Verkauf. Kommerzielle Angebote wie Support,
  gehärtete Langzeitversionen oder Appliances übernehmen separate Gesellschaften als Hersteller ihres jeweiligen Produkts. Die
  Steward-Prozesse (SBOM, Advisories, öffentliche Doku, Attestierung) sind so gestaltet, dass jeder Hersteller sie direkt für
  seine eigene Konformität nutzen kann.

Ein Gewährleistungsausschluss in AGPL oder Apache-Lizenz hebt gesetzliche Herstellerpflichten nicht auf.

## Konsequenzen

**Vorteile**

- Kein proprietärer Cloud-Fork ohne Offenlegung des Quellcodes; Verbesserungen fließen zurück.
- Permissive SDKs und Clients – keine Hürde für Anwender, Tooling und Integrationen.
- DCO ohne CLA ist ein glaubwürdiges Versprechen gegen spätere Relizenzierung.
- Die Steward-Rolle ist früh vorbereitet; die öffentliche Doku nutzt die Erleichterung für quelloffene Produkte.

**Nachteile**

- Teile der Industrie mit AGPL-Verboten beteiligen sich weniger.
- Ein Lizenzwechsel nach der Veröffentlichung ist kaum möglich – das ist gewollt.
- Betreiber mit eigenen Änderungen müssen das Quellcode-Angebot pflegen; der eingebaute Quellcode-Endpunkt entschärft das.
- Mehrere Lizenzen im Repository erfordern Disziplin (REUSE, Lizenzprüfung, klare Crate-Grenzen).
