title: Compliance-Anforderungen
summary: Welche Regelwerke für BYOC gelten, wie der Anforderungskatalog aufgebaut ist, wie sich Pflichten zwischen Plattform, Betreiber und Mandant verteilen und welche Vorrangregeln bei Konflikten greifen.
group: konzept
order: 160
quelle: Konzept 65 (Regelwerks-Analyse und Anforderungskatalog)
---

> **Hinweis:** Diese Seite gibt eine technische Anforderungsanalyse wieder und ist keine Rechtsberatung. Stand der Recherche:
> November 2026. Verbindliche Verwendung setzt den Abgleich mit den Originaldokumenten voraus.

## Kernaussagen

1. **Zertifiziert bzw. testiert wird der Betreiber, nicht die Software.** Die Plattform muss Betreibern ermöglichen, Controls
   wirksam umzusetzen und nachzuweisen. Dafür liefert sie technische Funktionen, sichere Voreinstellungen, eine
   Shared-Responsibility-Matrix und exportierbare Nachweise.
2. **Die Software selbst unterliegt dem EU Cyber Resilience Act (CRA)** – für jeden, der sie im Rahmen einer Geschäftstätigkeit
   in Verkehr bringt. Meldepflichten gelten seit dem 11.09.2026, alle übrigen Pflichten ab dem 11.12.2027. Teile der Plattform
   (OS-Image, Identitätsverwaltung, Hypervisor- und Container-Laufzeit) fallen voraussichtlich unter die „wichtigen Produkte“.
3. **BSI C5:2026** ist veröffentlicht – mit 168 Basiskriterien in 17 Bereichen und neuen Schwerpunkten wie Container-Management,
   Lieferkette/SBOM, Post-Quanten-Kryptografie und Confidential Computing. Ab Mitte 2027 ist es für Prüfungen Pflicht.
4. **Grundschutz++** ist seit dem 26.10.2026 als BSI-Standard 300-1 veröffentlicht. Der Anwenderkatalog mit rund 1.000
   Anforderungen liegt maschinenlesbar im OSCAL-Format vor. Der klassische IT-Grundschutz bleibt für eine mehrjährige
   Übergangszeit nutzbar.
5. **NIS2 gilt in Deutschland seit dem 06.12.2025.** Cloud-Anbieter und Rechenzentrumsbetreiber gehören zu den NIS2-Sektoren;
   für sie konkretisiert eine EU-Durchführungsverordnung die technischen Maßnahmen.
6. **Leitkatalog:** ISO/IEC 27001 Anhang A gibt die Struktur vor, BSI C5:2026 ist die inhaltliche Messlatte, Grundschutz++ die
   maschinenlesbare Detailquelle. Bei Konflikten gilt die strengere Anforderung – solange sie in allen Betriebsgrößen vom
   Homelab bis zum Rechenzentrum konfigurierbar bleibt.

## Regelwerke im Überblick

Die Relevanz wird getrennt bewertet: für die **Software** (Projekt als Hersteller) und für den **Betreiber**.

### Internationale Normen

| Regelwerk | Software | Betreiber | Bedeutung |
|---|---|---|---|
| ISO/IEC 27001:2022 | mittel | hoch | ISMS-Rahmen mit 93 Controls in Anhang A; Strukturgeber des Katalogs |
| ISO/IEC 27002:2022 | hoch | hoch | Umsetzungshinweise zu den Controls |
| ISO/IEC 27017:2026 | hoch | hoch | Cloud-Controls für Anbieter und Kunden: Mandantentrennung, VM-Härtung, Rückgabe von Kunden-Assets |
| ISO/IEC 27018:2025 | mittel | hoch | Schutz personenbezogener Daten in Public Clouds |
| ISO/IEC 27701:2025 | gering | hoch | eigenständiges Datenschutz-Managementsystem |
| ISO 22301 | gering | hoch | Business Continuity; die Plattform liefert Bausteine wie Backup und Wiederanlauf |
| ISO/IEC 20000-1 | gering | mittel | IT-Service-Management |

### BSI

| Regelwerk | Software | Betreiber | Bedeutung |
|---|---|---|---|
| BSI C5:2026 | hoch | hoch | Prüfkriterien für Cloud-Anbieter; inhaltliche Messlatte der Plattform |
| BSI C3A | mittel | mittel | Souveränitätskriterien (Datenlokation, Schlüsselhoheit) ohne regulatorische Wirkung – für Behörden und souveräne Hoster ein Verkaufsargument |
| IT-Grundschutz-Kompendium 2023 | mittel | hoch | Bausteine wie Virtualisierung, Containerisierung, Kubernetes, Kryptokonzept |
| Grundschutz++ (Standard 300-1) | hoch | hoch | prozessorientierte Methodik, Anwenderkatalog maschinenlesbar |
| BSI-Standards 200-1 bis 200-4 | gering | hoch | klassische Methodik, Notfallmanagement |
| BSI TR-02102 | hoch | mittel | Kryptografische Verfahren inkl. hybrider Post-Quanten-Verfahren; maßgeblich für die Kryptoauswahl (siehe [Kryptografie](kryptografie.html)) |
| BSI TR-03183 | hoch | gering | Cyber-Resilienz-Anforderungen an Hersteller, insbesondere SBOM |
| BSI-Mindeststandards | mittel | mittel | für Bundeseinrichtungen; Orientierung für Voreinstellungen |

### EU- und deutsches Recht

| Regelwerk | Software | Betreiber | Bedeutung |
|---|---|---|---|
| Cyber Resilience Act | hoch | gering | Produktpflichten, Schwachstellenbehandlung, Meldepflichten (24 h / 72 h) |
| NIS2 mit Durchführungsverordnung | gering | hoch | Risikomanagementmaßnahmen für Cloud- und Rechenzentrumsbetreiber |
| NIS2-Umsetzungsgesetz (BSIG neu) | gering | hoch | Risikomanagement, Meldepflichten, Registrierung, Haftung der Geschäftsleitung |
| DSGVO | mittel | hoch | Privacy by Design/Default, Auftragsverarbeitung, technische und organisatorische Maßnahmen, Löschung, Drittlandtransfer |
| EUCS | gering | gering | nicht verabschiedet; C5-Konformität gilt als guter Vorgriff |
| Souveränitätskriterien (C3A, Sovereign Cloud Stack, Verwaltungscloud) | mittel | mittel | als Gestaltungsprinzip übernommen: vollständig selbst betreibbar, keine Telemetrie an Dritte, Schlüsselhoheit beim Mandanten, steuerbare Datenlokation |

## Aufbau des Anforderungskatalogs

Jede Anforderung hat eine stabile ID der Form `REQ-<Block>-<Nr>`, eine Formulierung als Anforderung an die Plattform, ihre
Quellen (ISO, C5, Grundschutz, Grundschutz++, CRA, NIS2, DSGVO, technische Richtlinien), eine Priorität und die betroffenen
Komponenten.

**Prioritäten:** **MVP** = mit der ersten lauffähigen Fassung erfüllt · **P2** = vor dem ersten Produktivbetrieb im
Rechenzentrum · **P3** = später bzw. optional.

**Komponenten:** Agent, Steuerungsebene, Identität, API/Portal/MCP, Boot, OS-Image, Compute, Speicher, Netz, KMS,
Beobachtbarkeit, Audit-Log, Build/CI.

### Die Blöcke

| Block | Thema | Anzahl |
|---|---|---|
| IAM | Identität und Zugriff | 11 |
| TEN | Mandantentrennung | 7 |
| CRY | Kryptografie und Schlüssel | 8 |
| LOG | Protokollierung und Überwachung | 8 |
| VUL | Schwachstellen- und Patchmanagement | 9 |
| SDL | Sichere Entwicklung und Lieferkette | 11 |
| BCM | Datensicherung und Notfall | 6 |
| DEL | Löschung und Datenschutz | 7 |
| NET | Netzsicherheit | 8 |
| HRD | Härtung | 6 |
| AST | Asset- und Konfigurationsmanagement | 7 |
| PHY | Physische Aspekte (überwiegend Betreiberpflicht) | 4 |
| DOC | Dokumentation und Nachweise | 8 |

### Beispiele

| ID | Anforderung (gekürzt) | Prio |
|---|---|---|
| REQ-IAM-001 | Jede Aktion an API, Portal und MCP erfordert eine authentisierte Identität; keine anonymen Verwaltungsfunktionen. | MVP |
| REQ-IAM-002 | Lokale Konten mit Passkey als Normalfall, Föderation per OIDC optional je Mandant, SAML später. | MVP |
| REQ-IAM-003 | Mehrfaktor-Authentisierung für Betreiber und Admins erzwingbar (Voreinstellung: an), phishing-resistente Faktoren. | MVP |
| REQ-IAM-006 | Betreiberzugriff auf Mandantendaten technisch gesperrt; nur über einen protokollierten, für den Mandanten sichtbaren Freigabeprozess. | MVP / P2 |
| REQ-IAM-011 | Destruktive und privilegierte Aktionen über MCP werden außerhalb des KI-Clients mit Passkey bestätigt; das Bestätigungstoken ist an alle Parameter gebunden und einmalig. | MVP |
| REQ-TEN-001 | Durchgängige Mandantentrennung auf Steuerungs-, Rechen-, Netz-, Speicher- und Schlüsselebene; die Mandanten-ID wird in jeder Autorisierungsentscheidung geprüft. | MVP |
| REQ-TEN-002 | Mandanten-Workloads laufen in VMs oder MicroVM-isolierten Containern – kein geteilter Kernel zwischen Mandanten. | MVP |
| REQ-TEN-007 | Automatisierte Isolationstests in der CI und vor jedem Release, dazu Pentests gegen Mandantengrenzen. | MVP |
| REQ-CRY-002 | Verschlüsselung in Transit überall: mTLS mit TLS 1.3 zwischen allen Diensten, verschlüsseltes Underlay. | MVP |
| REQ-CRY-004 | KMS mit Schlüsselhierarchie (Root → Mandanten-KEK → Daten-DEK), Rotation, Versionierung und Zweckbindung. | MVP |
| REQ-CRY-006 | Krypto-Agilität und Post-Quanten-Vorbereitung mit hybrider Schlüsseleinigung. | MVP / P2 |
| REQ-LOG-001 | Audit-Log jeder zustandsändernden Operation – identisch für API, Portal und MCP: wer, was, wann, wo, Ergebnis. | MVP |
| REQ-LOG-002 | Audit-Log append-only, kryptografisch verkettet und signiert. | MVP |
| REQ-VUL-002 | CRA-Meldeprozess für aktiv ausgenutzte Schwachstellen: Frühwarnung in 24 h, Meldung in 72 h. | MVP |
| REQ-VUL-005 | Automatische Knoten-Updates per A/B-Image mit gestaffeltem Rollout, Health-Gates und automatischem Rollback. | MVP |
| REQ-SDL-003 | SBOM in CycloneDX oder SPDX für jedes Release und jedes OS-Image. | MVP |
| REQ-SDL-004 | Signierte Builds (MVP), reproduzierbar und mit Provenienznachweis nach SLSA Level 3 (P2). | MVP / P2 |
| REQ-SDL-009 | Security by Default: keine Standardpasswörter, minimale offene Ports, Schutzfunktionen ab Werk aktiv. | MVP |
| REQ-BCM-004 | Hochverfügbarkeit ohne Single Point of Failure ab drei Knoten. | MVP |
| REQ-DEL-001 | Nachweisbares Löschen von Mandantendaten per Krypto-Löschung, mit Löschnachweis. | MVP / P2 |
| REQ-DEL-006 | Privacy by Default: keine Telemetrie an das Projekt oder Dritte ohne ausdrückliches Opt-in. | MVP |
| REQ-NET-002 | Discovery-Quarantäne: unbekannte Hardware ist netztechnisch oder kryptografisch isoliert, bis sie adoptiert wurde. | MVP |
| REQ-HRD-001 | Gehärtetes, unveränderliches OS-Image mit schreibgeschütztem, verifiziertem Root-Dateisystem. | MVP |
| REQ-AST-001 | Automatisches Hardware-Inventar je Knoten. | MVP |
| REQ-DOC-003 | OSCAL-Komponentendefinition der Plattform je Release, damit Betreiber sie direkt in ihr ISMS übernehmen können. | P2 |
| REQ-DOC-004 | Compliance-CI: automatisierte Prüfung sicherer Voreinstellungen gegen die Control-Matrix. | P2 |

Weiterführend: [Sicherheitsmodell](sicherheitsmodell.html), [Boot und Adoption](boot-adoption.html),
[OS-Image](os-image.html), [Schwachstellenmanagement](schwachstellenmanagement.html).

## Shared Responsibility

**Grundsatz:** Die Plattform liefert Fähigkeiten, sichere Voreinstellungen und Nachweisdaten. Der Betreiber wendet sie an,
organisiert, entscheidet und verantwortet das ISMS. Der Mandant verantwortet seine Workloads und Daten. Testat oder Zertifikat
erhält immer der Betreiber.

| Thema | Plattform | Betreiber | Mandant |
|---|---|---|---|
| ISMS, Risikomanagement | Vorlagen, Control-Matrix, Grundschutz-Modellierung | **verantwortlich** | eigenes ISMS für seine Nutzung |
| Identität und Zugriff | IAM-Funktionen, MFA, Rollen, Protokollierung, Rezertifizierungsbericht | IdP-Anbindung, Rollenvergabe, Rezertifizierung | eigene Nutzer und Rollen |
| Mandantentrennung | **verantwortlich** für technische Isolation und deren Tests | korrekte Konfiguration, eigener Pentest | – |
| Kryptografie | Implementierung, KMS, Post-Quanten-Agilität, sichere Voreinstellungen | Kryptoprofil wählen, Root-Schlüssel verwahren, Schlüsselzeremonie | optional eigene Schlüssel (BYOK/HYOK) |
| Protokollierung | Erzeugung, Integrität, Export, SIEM-Schnittstellen | SIEM-Betrieb, Auswertung, Aufbewahrung, Meldungen | Auswertung eigener Audit-Trails |
| Schwachstellen und Patches | Produkt-Schwachstellenmanagement nach CRA: Meldewege, Advisories, Updates, SBOM | Updates zeitnah einspielen, Patchstand nachweisen | Gastsysteme, Images, Anwendungen patchen |
| Sichere Entwicklung, Lieferkette | **verantwortlich** | Lieferantenbewertung, eigene Erweiterungen | eigene Software |
| Datensicherung, Notfall | Backup-, Restore- und Replikationsfunktionen, Hochverfügbarkeit, Runbooks | Backup-Konzept, Offsite-Kopie, Restore-Tests, Notfallhandbuch | Backups eigener Daten |
| Löschung, Datenschutz | Krypto-Löschung, Löschnachweise, Export, Datenlokation | AV-Verträge, Verzeichnis, Löschkonzept, Datenträgervernichtung | Rechtsgrundlage, Löschanforderungen |
| Netzsicherheit | Segmentierung, Default-deny, Discovery-Quarantäne | physische Anbindung, Perimeter, vorgelagerter DDoS-Schutz | Security Groups, VPC-Design |
| Härtung | gehärtetes Image, Secure Boot, Drift-Erkennung | Hardware- und Firmware-Auswahl, BMC-Härtung | Härtung der Gastsysteme |
| Physische Sicherheit, Personal | Fehlerdomänen-Modell, Datenträgerverschlüsselung | **verantwortlich** | – |
| Dokumentation, Nachweise | Control-Matrix, OSCAL-Komponentendefinition, Nachweis-Export, Betreiberhandbuch | Systembeschreibung, Audits | – |
| Meldepflichten | CRA (Produktschwachstellen) | NIS2/BSIG (Betriebsvorfälle), DSGVO | DSGVO als Verantwortlicher |

**Homelab:** Ohne Compliance-Ziel gelten dieselben Voreinstellungen; Betreiberpflichten werden zu Empfehlungen. Keine
Funktion darf nur mit Rechenzentrumsinfrastruktur (HSM, SIEM, zweiter Standort) sicher sein – jede solche Abhängigkeit braucht
einen sicheren Fallback, etwa Schlüsselteilung nach Shamir statt HSM oder lokalen Log-Speicher statt SIEM.

## Leitkatalog und Vorrangregeln

### Charakter der Regelwerke

| | ISO/IEC 27001/27002/27017 | BSI C5:2026 | Grundschutz++ |
|---|---|---|---|
| Natur | Managementsystem mit generischen Controls („was“) | testierbare Prüfkriterien für Cloud-Anbieter | Methodik mit sehr detaillierten Anforderungen („wie“) |
| Nachweis | Zertifizierung, international verbreitet | Testat; teils gesetzlich gefordert | Zertifizierung auf Basis IT-Grundschutz; Pflicht für Bundesbehörden |
| Granularität | grob | mittel bis fein | sehr fein, maschinenlesbar |

### Leitkatalog

1. **Rückgrat: ISO/IEC 27001 Anhang A** (ergänzt um 27017 für Cloud). Jede Anforderung wird zuerst auf ein Anhang-A-Control
   gemappt – jedes ISMS baut darauf auf.
2. **Inhaltliche Messlatte: BSI C5:2026.** Wo C5 konkreter oder strenger ist – Mandantentrennung, Zugriff auf Kundendaten,
   Produktsicherheit, Transparenz, Container, Post-Quanten-Kryptografie –, bestimmt C5 die Akzeptanzkriterien. Ziel: Ein
   Betreiber soll mit der Plattform alle technischen C5-Basiskriterien erfüllen können.
3. **Detail- und Maschinenquelle: Grundschutz++.** Der Katalog wird direkt importiert und liefert konkrete Prüfpunkte (siehe
   [Grundschutz-Modellierung](grundschutz.html)).
4. **Gesetzliche Untergrenze:** CRA für die Software, NIS2 für Betreiber. Gesetzliche Anforderungen sind nicht abwägbar.

### Konfliktregeln

| Regel | Inhalt |
|---|---|
| K1 – Recht vor Norm | CRA, NIS2/BSIG und DSGVO gehen jeder Norm vor. |
| K2 – Strenger gewinnt | Weichen C5, ISO und Grundschutz++ ab, gilt die strengere Anforderung als Plattform-Voreinstellung – sofern sie konfigurierbar bleibt. |
| K3 – Konfigurierbarkeit statt Zwang | Wo Strenge den Homelab-Betrieb unmöglich macht, wird sie als Profil angeboten, mit dokumentiertem sicheren Fallback. Zwei Achsen: **Betriebsprofil** (`homelab`, `standard-c5`, `erhoeht`) und **Kryptoprofil** (`bsi-strict` als Voreinstellung, `compatible`); die regulierten Betriebsprofile nur mit `bsi-strict`. |
| K4 – Krypto nach BSI | Bei Kryptofragen ist BSI TR-02102 maßgeblich; Abweichungen werden begründet und dokumentiert. |
| K5 – Nachweisbarkeit | Eine Anforderung gilt erst als umgesetzt, wenn die Plattform einen **automatisch erzeugbaren Nachweis** liefert. |
| K6 – Versionsdisziplin | Referenzen tragen ihre Version; neue Fassungen werden als Delta bewertet, Übergangsfristen bestimmen die Priorität. |

Einen echten Vorrangkonflikt zwischen C5 und ISO 27001 gibt es nicht: ISO 27001 ist das Gerüst, C5:2026 die strengere,
cloudspezifische Ausprägung. Wie diese Anforderungen bereits in der Architektur verankert werden, beschreibt
[Compliance by Design](compliance-by-design.html).
