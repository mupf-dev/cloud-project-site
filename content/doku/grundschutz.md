title: Grundschutz-Modellierung
summary: Wie DCP den Teil-Informationsverbund „Plattform“ aus Herstellersicht nach Grundschutz++ modelliert, Anforderungen auf Komponenten und Nachweise abbildet und Betreibern eine Schutzbedarfs-Vorlage liefert.
group: konzept
order: 170
quelle: Konzept 66 (IT-Grundschutz-Modellierung)
---

> **Hinweis:** Technische Modellierung, keine Rechts- oder Auditberatung. Die Modellierung ist eine Vorlage; die Verantwortung
> für den eigenen Informationsverbund bleibt beim Betreiber.

## Kernentscheidungen

| Nr. | Entscheidung |
|---|---|
| 1 | **Ziel ist Grundschutz++** (BSI-Standard 300-1, Anwenderkatalog im OSCAL-Format). Das IT-Grundschutz-Kompendium 2023 wird nur als *abgeleitete Sicht* für Betreiber geliefert, die noch danach arbeiten – erzeugt, nicht von Hand gepflegt. |
| 2 | Modelliert wird der **Teil-Informationsverbund „Plattform“ aus Herstellersicht**: 13 technische Zielobjekte, die Knoten-Hardware und sieben Informationsarten. Der Betreiber übernimmt ihn als Baustein seines eigenen Verbunds und ergänzt Standort, Personal und Organisation. |
| 3 | Es gibt **eine einzige, versionierte Quelle** für die Zuordnung Anforderung ↔ Grundschutz++-Anforderung ↔ Zielobjekt ↔ Verantwortung ↔ Nachweis. Alle Betreiber-Artefakte werden daraus **generiert**. |
| 4 | Referenzen auf Grundschutz++-Anforderungen tragen **beide Schlüssel**: die lesbare ID und die stabile UUID. |
| 5 | Der laufend aktualisierte Katalog wird **festgepinnt** und mitgeliefert; ein regelmäßiger Update-Lauf erzeugt einen Diff-Bericht zur Prüfung. Kein Build lädt den Katalog live aus dem Netz. |
| 6 | Für Assets ohne passende Zielobjektkategorie (Container, Kubernetes, KMS, verteilter Zustand) liefert das Projekt einen kleinen **Ergänzungskatalog**. |
| 7 | Eine **Schutzbedarfs-Vorlage** mit Annahmen je Informationsart und Zielobjekt, in drei Betriebsprofilen, anschlussfähig an klassischen Grundschutz und Grundschutz++. |
| 8 | Externe Prüfwerkzeuge (OSCAL-Validierung) laufen nur in der CI als eigener Prozess; die OSCAL-Dateien erzeugt ein eigener Generator. |

## Wer modelliert was?

Grundschutz-Modellierung ist Aufgabe der Institution, die ein ISMS betreibt – also des **Betreibers**. Der technische Teil ist
aber für alle Installationen gleich, deshalb nimmt ihn das Projekt als Hersteller vorweg:

| Ebene | Wer | Ergebnis |
|---|---|---|
| Hersteller-Vorlage | Projekt | Zielobjekte der Plattform, Zuordnung zu Zielobjektkategorien und Anforderungen, Umsetzungsbeschreibung je Komponente (OSCAL Component Definition), Schutzbedarfs-Annahmen, Parametervorschläge |
| Informationsverbund des Betreibers | Betreiber | Übernahme der Vorlage, Ergänzung um Standorte, Räume, Personal, Dienstleister und Geschäftsprozesse; Schutzbedarf, Anforderungspaket, Parameter, Umsetzungsstatus |
| Nutzung durch Mandanten | Mandant | Für ihn ist die ganze Plattform **ein Cloud-Dienst**; er modelliert seine Workloads selbst |

Für den Betreiber sind die Komponenten Anwendungen, Hostsysteme und Netze in seinem Verbund; für den Mandanten ist die Plattform
ein Cloud-Dienst. Die Shared-Responsibility-Matrix verbindet beide Sichten (siehe
[Compliance-Anforderungen](compliance-anforderungen.html)).

### Grundschutz++ in Kürze

Der Anwenderkatalog umfasst rund **1.000 Anforderungen** in 20 Praktiken – etwa Asset-Management, Berechtigungen, Detektion,
Konfiguration, Architektur, Entwicklung und Notfallmanagement. Jede Anforderung trägt ein Sicherheitsniveau (`normal-SdT` oder
`erhöht`), ihre Wirkung auf die Schutzziele, zugeordnete Gefährdungen, Zielobjektkategorien und teils Parameter, die der
Betreiber festlegt. Rund 140 Anforderungen tragen das Tag **„Produktbeschreibung“** – genau die Anforderungen, die ein
Hersteller als OSCAL-Komponentendefinition bereitstellen kann. Sie bilden den Pflichtumfang der Komponentendefinition von
DCP.

Etwa ein Drittel der Anforderungen hat keine Zielobjektkategorie; das sind überwiegend ISMS- und Organisationsanforderungen,
die für den gesamten Verbund des Betreibers gelten. Hier liefert die Plattform nur **Datenquellen**: Umsetzungsstatus aus der
Konfiguration, erfasste Ausnahmen vom sicheren Standard, Nachweis-Exporte für Audits, vorbereitete Meldedaten bei Vorfällen und
Schutzbedarfs-Labels an Ressourcen.

Weil der Katalog laufend – etwa wöchentlich – aktualisiert wird, sind Versions-Pinning und Prüfungen auf referenzielle
Integrität unverzichtbar. Fremde Zuordnungstabellen werden nie ungeprüft übernommen.

## Der Informationsverbund „Plattform“

### Abgrenzung

| Im Verbund (Plattform liefert, Betreiber betreibt) | Außerhalb (Betreiber bzw. Mandant modelliert selbst) |
|---|---|
| alle technischen Zielobjekte, die Knoten-Hardware und die Informationsarten der Plattform | Gebäude und Räume, Personal, Dienstleister, Upstream-Netz und Firewall, Gastsysteme und Anwendungen der Mandanten, Arbeitsplätze der Betreiber |

**Externe Schnittstellen** des Verbunds sind: Bezug der Releases vom Projekt, Föderation mit Identitätsanbietern, das SIEM des
Betreibers, Upstream-Netz mit DHCP, DNS und NTP, Offsite-Backup, optional HSM bzw. externes KMS, der Mandantenzugang über
Portal, API und MCP sowie die Out-of-Band-Verwaltung.

Build, CI und Release-Infrastruktur gehören zum Verbund **des Projekts** (Hersteller nach CRA). Sie werden mitmodelliert, weil
ihre Nachweise – SBOM, Provenienz, Testberichte – als Eingangsdaten in den Verbund des Betreibers fließen (siehe
[Release-Bündel](release-buendel.html)).

### Zielobjekte

| Zielobjekt | Komponente | Zielobjektkategorie (Grundschutz++) | Kompendium 2023 (Übergang) |
|---|---|---|---|
| Knoten-Hardware | Server, Notebooks, Raspberry Pi, BMC, TPM, Datenträger | IT-Systeme, Hostsysteme | SYS.1.1 |
| OS-Image | unveränderliches A/B-Image mit verifiziertem Root (siehe [OS-Image](os-image.html)) | IT-Systeme, Hostsysteme | SYS.1.1, SYS.1.3 |
| Agent | `cp-agent` auf jedem Knoten | Anwendungen | APP.6 |
| Steuerungsebene | Raft je Zelle, Zeugen, Gossip, Reconciler (siehe [Steuerungsebene](steuerungsebene.html)) | Anwendungen | APP.6, CON.3 |
| Identitätsdienst | OIDC/OAuth, Passkeys, Rechte-Speicher, Cedar (siehe [Identität](identitaet.html)) | Anwendungen, Verzeichnisdienste, Webanwendungen | ORP.4, APP.2.1 |
| API, Portal, MCP | Verwaltungsschnittstellen | Webanwendungen, Webserver | APP.3.1, APP.3.2 |
| Boot-Dienst | Netzboot, Discovery (siehe [Boot und Adoption](boot-adoption.html)) | Anwendungen, interne Netzsegmente | NET.1.1, NET.3.4 |
| Compute | VMs, MicroVM-Container, Kubernetes | Virtualisierungslösungen, Hostsysteme | SYS.1.5, SYS.1.6, APP.4.4 |
| Speicher | Block-, Objekt- und Dateispeicher (siehe [Speicher](speicher.html)) | Anwendungen, Daten | SYS.1.8, CON.3, CON.6 |
| Netz | verschlüsseltes Underlay, Mandanten-Overlay, Gateway, Basisdienste (siehe [Netzwerk](netzwerk.html)) | Netze, interne Netzsegmente, externe Netzanschlüsse | NET.1.1, NET.3.x |
| KMS / PKI | Schlüsselhierarchie, Regions- und Zellen-CA (siehe [Kryptografie](kryptografie.html)) | Anwendungen | CON.1 |
| Beobachtbarkeit | Metriken, Logs, Traces, Alarmierung | Anwendungen | OPS.1.1.5, DER.1 |
| Audit-Log | verkettet, signiert, mit Mandantensicht | Anwendungen, Daten | OPS.1.1.5, DER.2.2 |
| Build/CI | Signatur, SBOM, Release-Kanal, Schwachstellenmeldungen | Anwendungen (Entwicklung) | CON.8, APP.7 |

### Modellierung je Zielobjekt

Für jedes Zielobjekt werden die wesentlichen Anforderungen mit **Verantwortung** und **Umsetzung** festgehalten. Die
Verantwortung hat vier Ausprägungen:

| Kürzel | Bedeutung |
|---|---|
| P | Plattform bzw. Projekt setzt um |
| P→B | Plattform liefert Fähigkeit und sichere Voreinstellung, Betreiber wendet an bzw. konfiguriert |
| B | Betreiber |
| M | Mandant |

Ein Beispiel für die Knoten-Hardware:

| Anforderung | Verantwortung | Umsetzung |
|---|---|---|
| Inventar der Systeme, unautorisierte Systeme aufdecken | P→B | Der Agent meldet die Hardware automatisch; nicht adoptierte Knoten erscheinen sichtbar als „wartend“. |
| Kryptografischer Hardwarespeicher, Speicherverschlüsselung | P→B | TPM-Nutzung, wo vorhanden; Datenträgerverschlüsselung als Voreinstellung; Vertrauensstufe des Knotens je nach Ausstattung (siehe [Sicherheitsmodell](sicherheitsmodell.html)). |
| Authentifizierung an der Firmware | B | Betreiber-Leitfaden; die Plattform meldet den Status, soweit auslesbar. |
| Peripherie und Wechselmedien einschränken | P | Im OS-Image sind USB-Speichertreiber deaktiviert. |
| Geregeltes Löschen bei Stilllegung | P→B | Hardwareseitiges Löschen bzw. Krypto-Löschung mit Nachweis. |

### Ergänzungskatalog

Für Assets ohne passende Zielobjektkategorie gibt es einen kleinen eigenen OSCAL-Katalog. Die Anforderungen sind nach der
Satzschablone von Grundschutz++ formuliert und verweisen auf ihre Herkunft im Kompendium oder in C5. Beispiele:

- Die Steuerungsebene SOLLTE nur Knoten mit der Mindest-Vertrauensstufe des Betriebsprofils als stimmberechtigte Mitglieder
  zulassen.
- Die Steuerungsebene SOLLTE destruktive Aktionen nur nach Quorum-Bestätigung ausführen.
- Die Steuerungsebene SOLLTE Mandantenobjekte nur an berechtigte Knoten replizieren.
- Compute SOLLTE nur signierte bzw. freigegebene Images starten.
- Managed Kubernetes SOLLTE je Mandant eine getrennte Steuerungsebene betreiben.
- Speicher SOLLTE freigegebene Blöcke vor der Wiederverwendung unlesbar machen.
- Das Overlay SOLLTE Verkehr zwischen VPCs verschiedener Mandanten ohne explizites Peering unterbinden.
- Die Adoption SOLLTE an einen auf dem Gerät erzeugten Schlüssel gebunden sein; Netzboot allein begründet kein Vertrauen.
- Das KMS SOLLTE mandanteneigene Schlüssel und Krypto-Löschung unterstützen.
- Der MCP-Zugang SOLLTE KI-Agenten als eigene Akteure behandeln und destruktive Aktionen nur nach Bestätigung außerhalb des
  KI-Clients ausführen.

## Mapping-Prinzip: Anforderung → Komponente → Nachweis

Jede Anforderung des Katalogs wird auf mindestens eine Grundschutz++-Anforderung, ein Zielobjekt, eine Verantwortung und eine
**Nachweisart** abgebildet. Hintergrund ist die Regel aus dem Anforderungskatalog: *Eine Anforderung gilt erst als umgesetzt,
wenn die Plattform einen automatisch erzeugbaren Nachweis liefert.*

### Nachweisarten

| Nachweis | Inhalt |
|---|---|
| Audit-Export | signierter Export über einen Zeitraum mit Hash-Kette und Prüfwerkzeug |
| Inventar | Hardware- und Software-Inventar inkl. SBOM je Knoten |
| Konfiguration | Sollzustands-Manifest mit Änderungshistorie, aktives Profil, erfasste Ausnahmen |
| Rechte | Rechte- und Rezertifizierungsbericht |
| Patchstand | Patch- und Schwachstellenstatus je Knoten |
| Backup | Backup- und Test-Restore-Protokoll |
| Löschung | Löschnachweis (Krypto-Löschung, hardwareseitiges Löschen) |
| Krypto-Inventar | verwendete Verfahren, Schlüssel-Metadaten, Zertifikate |
| Netz | Netztopologie und Regelwerk-Export |
| Härtung | Härtungs- und Drift-Bericht, Vertrauensstufe je Knoten, Attestierungsstatus |
| Release | Signatur, Provenienz, SBOM, Test-, Isolations- und Pentest-Berichte, maschinenlesbare Advisories |
| Dokumentation | Betreiberhandbuch, Runbooks, Richtlinien |

### Beispiele

| Anforderung | Zielobjekt | Verantwortung | Umsetzung | Nachweis |
|---|---|---|---|---|
| REQ-IAM-001 Authentisierung an jeder Schnittstelle | Identität, API | P | Authentisierung überall, dokumentierte Ausnahmen | Konfiguration, Dokumentation |
| REQ-IAM-003 MFA für Admins | Identität, API | P→B | MFA für Admins erzwungen | Rechte, Konfiguration |
| REQ-IAM-004 rollenbasierte Zugriffssteuerung | Identität, Steuerungsebene | P | Rollen mit Cedar-Policies | Rechte |
| REQ-IAM-006 Betreiberzugriff auf Mandantendaten | Identität, KMS, Audit | P | technische Sperre mit Zugriffsantrag | Audit-Export |
| REQ-TEN-007 Trennungstests | Build/CI | P | Isolationstests in der CI | Release |

## Maschinenlesbare Pflege

Die Modellierung wird nicht als Dokument gepflegt, sondern als **strukturierte Daten** im Repository. Die Prinzipien:

- **Eine Quelle:** Zielobjekte, Zuordnungen, Umsetzungstexte, Parametervorschläge und die Schutzbedarfs-Vorlage liegen in
  versionierten, maschinenlesbaren Dateien. Tabellen in Dokumenten werden daraus erzeugt, nicht umgekehrt.
- **Gepinnter Katalog:** Der Grundschutz++-Katalog wird mit Version und Prüfsumme festgehalten und unverändert mitgeliefert.
  Ein regelmäßiger Update-Lauf erzeugt einen Diff (neue oder entfallene IDs, geänderte Texte, Sicherheitsniveaus, Kategorien)
  und markiert betroffene Zuordnungen zur Prüfung. Erst nach Review wird der neue Stand übernommen.
- **Prüfungen in der CI:** Schema-Validierung, Integrität des Pins, referenzielle Integrität jeder zitierten ID, Abdeckung (jede
  Anforderung hat Zielobjekt und Nachweis; jede relevante „Produktbeschreibung“-Anforderung hat einen Status), Erreichbarkeit der
  Nachweise und Übereinstimmung der Voreinstellungen im Code mit den Angaben im Mapping (Policy as Code).
- **Release-Bindung:** Jede Plattformversion nennt den Katalogstand, gegen den ihre Aussagen gelten.

### Was Betreiber je Release erhalten

Signiert und Teil der Release-Nachweise (siehe [Release-Signatur](release-signatur.html)):

| Artefakt | Format | Inhalt |
|---|---|---|
| Komponentendefinition | OSCAL Component Definition | je Zielobjekt die umgesetzten Anforderungen mit Beschreibung, Verantwortung, Status und Nachweisart |
| Anforderungspaket-Vorschlag | OSCAL Profile | Auswahl der Anforderungen je Betriebsprofil, Parametervorschläge |
| Shared-Responsibility-Matrix | Tabelle | Grundlage für komplementäre Kundenkontrollen nach C5 |
| Kompendium-Sicht | Tabelle | Zielobjekt → Baustein → Grundschutz++ → Umsetzung, gekennzeichnet als abgeleitet |
| Schutzbedarfs-Vorlage | Vorlage | zur Übernahme in ISMS-Werkzeuge |

Später liefert die Plattform-API zusätzlich den **Ist-Zustand** der Installation – aktives Betriebs- und Kryptoprofil,
Parameterwerte, erfasste Ausnahmen – als OSCAL-Fragment, gleichwertig über API, Portal und MCP.

## Schutzbedarfs-Annahmen als Vorlage

Die Vorlage verbindet beide Methoden: Klassisch (BSI 200-2) mit den Kategorien *normal*, *hoch* und *sehr hoch* je Schutzziel,
Grundschutz++ über das Sicherheitsniveau der Anforderungen. Die Brücke: *normal* → nur `normal-SdT`; *hoch* → zusätzlich die
`erhöht`-Anforderungen der betroffenen Zielobjekte plus Risikobetrachtung; *sehr hoch* → zusätzlich individuelle Risikoanalyse.
Alle Werte sind **Annahmen des Herstellers**, die der Betreiber anhand seiner Geschäftsprozesse bestätigt oder ändert.

### Informationsarten

| Informationsart | Beispiele | Vertraulichkeit | Integrität | Verfügbarkeit |
|---|---|---|---|---|
| Schlüsselmaterial | Root- und KEK-Schlüssel, CA-Schlüssel | sehr hoch | sehr hoch | hoch |
| Plattformzustand | Raft-Log, Rechte, Policies, Platzierung | hoch | sehr hoch | hoch |
| Identitätsdaten | Konten, Passkeys, Sitzungen | hoch | sehr hoch | hoch |
| Audit-Log | Audit-Ereignisse, Spuren von Zugriffsanträgen | hoch | sehr hoch | normal |
| Betriebsprotokolle | System- und Netzlogs, Traces | normal bis hoch | hoch | normal |
| Mandantendaten | Volumes, Objekte, VM-Speicher | vom Mandanten bestimmt, Annahme mindestens hoch | hoch | hoch |
| Artefakte | OS-Images, Agent-Binaries, Gast-Images, SBOM | normal | sehr hoch | hoch |

Ein manipuliertes Image würde alle Knoten kompromittieren – deshalb ist die Integrität der Artefakte *sehr hoch*. Für
Mandantendaten trifft die Plattform keine Annahme unter *hoch*, solange der Mandant nichts angibt.

### Vererbung auf Zielobjekte

Nach dem Maximumprinzip erben die Zielobjekte den Schutzbedarf der Informationen, die sie verarbeiten. Bereits im
Standardprofil ergibt sich daraus für KMS, Steuerungsebene, Identitätsdienst, Audit-Log, Boot-Dienst und OS-Image eine
**Risikobetrachtung** und eine Auswahl von `erhöht`-Anforderungen. Das Projekt liefert dafür eine vorbereitete
Risikobetrachtung als Teil des [Bedrohungsmodells](bedrohungsmodell.html).

### Betriebsprofile

| Profil | Zielgruppe | Annahme | Zusätzlich aktiv (Auswahl) |
|---|---|---|---|
| `homelab` | privat, Labor | alles *normal*, Integrität von Schlüsseln und Artefakten *hoch* | Quarantäne neuer Knoten, schrittweiser Rollout, Verschlüsselung ruhender Daten – weil ohne Mehraufwand möglich |
| `standard-c5` | Hoster, Unternehmen | Annahmen wie oben | Just-in-Time-Administration, Schlüsselteilung, Unbestreitbarkeit, automatische Konfigurationsverwaltung, sicherer Boot (wo die Hardware es kann), höhere Mindest-Vertrauensstufen für kritische Rollen |
| `erhoeht` | Behörden, KRITIS | Mandantendaten *sehr hoch* | dedizierte Hardware, keine Überbuchung, physische Segmentierung, Georedundanz, HSM statt Schlüsselteilung |

Das Kryptoprofil (`bsi-strict` oder `compatible`) wird unabhängig gewählt; `standard-c5` und `erhoeht` sind nur mit
`bsi-strict` zulässig. Schutzbedarfs-Labels an Ressourcen werden auf Datenklassen und Mindest-Vertrauensstufen für die
Platzierung abgebildet – *hoch* etwa auf Knoten mit TPM, *sehr hoch* auf attestierte Knoten oder dedizierte Hosts.

### Was der Betreiber mit der Vorlage tut

1. Geltungsbereich und Geschäftsprozesse festlegen.
2. Informationsarten bestätigen oder anpassen; den Schutzbedarf der Mandantendaten gemeinsam mit den Mandanten bzw. über Labels
   festlegen.
3. Betriebsprofil wählen und den Profil-Export in das ISMS-Werkzeug übernehmen.
4. Parameter prüfen.
5. Eigene Anteile modellieren (Gebäude, Personal, Dienstleister, Upstream-Netz) und die Risikobetrachtung abschließen.
6. Umsetzungsstatus aus dem Plattform-Export übernehmen und Ausnahmen bestätigen.
