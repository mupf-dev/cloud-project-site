title: Compliance by Design
summary: Die 36 prüfbaren Architekturleitlinien von cloud-project, die CI-Prüfungen und die Review-Checkliste dazu sowie die Vorlage „Sicherheit & Compliance“, die jede Architekturentscheidung enthalten muss.
group: konzept
order: 180
quelle: Konzept 68 (Compliance by Design)
---

## Wozu Leitlinien?

Der [Anforderungskatalog](compliance-anforderungen.html) legt fest, **was** die Plattform erfüllen muss, die
[Grundschutz-Modellierung](grundschutz.html), **wie** das auf Grundschutz++ abgebildet wird, das
[Bedrohungsmodell](bedrohungsmodell.html), **wogegen** sie sich schützen muss, das Konzept zur [Kryptografie](kryptografie.html)
**mit welchen Verfahren**, und das [Sicherheitsmodell](sicherheitsmodell.html) beschreibt das Gesamtbild. Was dann noch fehlt,
sind **Regeln, die jede einzelne Architekturentscheidung einhalten muss** – damit Compliance aus dem Entwurf folgt und nicht
nachträglich „hineingeprüft“ wird. Das entspricht dem Leitprinzip „Compliance by Design“ aus der [Vision](vision.html) und den
Anforderungen des Cyber Resilience Act an sichere Konzeption.

### Kernaussagen

- Es gibt **36 prüfbare Architekturleitlinien** (CBD-01 bis CBD-36) in neun Gruppen. Jede ist eine MUSS-Regel mit Quelle und
  mindestens einer Prüfart. **Eine Leitlinie ohne Prüfung gibt es nicht.**
- Die Prüfungen sind zu **20 benannten CI-Prüfungen** und einer **Review-Checkliste** gebündelt.
- **Jedes künftige ADR oder Fachkonzept** enthält den Abschnitt „Sicherheit & Compliance“ nach fester Vorlage. Ohne ihn ist ein
  Dokument nicht abnahmefähig.

### Rangfolge

1. **Gesetz** – CRA, NIS2/BSIG, DSGVO; nicht abwägbar.
2. **Konfliktregeln und Anforderungskatalog** (siehe [Compliance-Anforderungen](compliance-anforderungen.html)).
3. **Leitlinien CBD-01 bis CBD-36** (diese Seite).
4. **ADR bzw. Fachkonzept** mit dem Abschnitt „Sicherheit & Compliance“.
5. **Implementierung und Tests** (CI-Prüfungen).
6. **Nachweise**, Release-Bericht, OSCAL-Export.

Das Bedrohungsmodell wirkt auf Leitlinien und ADRs gleichermaßen ein. Eine Leitlinie **darf** in einem ADR unterschritten werden –
aber nur mit einem Eintrag im Abweichungsregister mit Begründung, Kompensation, Freigabe und Frist. Widerspricht ein ADR einer
Leitlinie ohne einen solchen Eintrag, ist es nicht abnahmefähig. Leitlinien ändern sich nur über eine neue Fassung; IDs werden
nie wiederverwendet.

### Prüfarten

| Kürzel | Bedeutung | Wann |
|---|---|---|
| PR | automatische Prüfung, blockiert den Merge | jeder Pull Request |
| N | automatische nächtliche Prüfung; ein Fehlschlag blockiert das nächste Release | nachts |
| R | Release-Gate | je Release |
| REV | Review mit Checkliste; sicherheitskritische Pfade mit zwei Reviewern | je PR bzw. ADR |
| LAB | Prüfung im QEMU- bzw. Hardware-Labor | nachts bzw. vor Phasenabschluss |
| PT | Pentest bzw. externes Audit | vor dem MVP, je Hauptversion |
| DOC | automatische Prüfung der Konzeptdokumente | jeder PR |

## Die Leitlinien

### Grundsätze und Voreinstellungen

| ID | Leitlinie | Prüfung |
|---|---|---|
| CBD-01 | **Secure by Default.** Der Auslieferungszustand ist die sicherste Einstellung, die im Homelab ohne Zusatzhardware betreibbar ist: keine Standardzugangsdaten, kein interaktiver Login, keine aktive Auto-Adoption, strenges Kryptoprofil, alle Sicherheitsfunktionen an. Jede Lockerung ist eine auditierte API-Aktion. | Prüfung der Frischinstallation, REV |
| CBD-02 | **Homelab-Fallback.** Keine Sicherheitsfunktion darf nur mit Rechenzentrumsinfrastruktur sicher sein; jede solche Abhängigkeit hat einen dokumentierten sicheren Fallback – etwa Schlüsselteilung statt HSM. | REV, DOC |
| CBD-03 | **Nachweis gehört zur Funktion.** Eine relevante Funktion gilt erst als umgesetzt, wenn sie einen automatisch erzeugbaren Nachweis liefert – abrufbar über API, Portal und MCP. | PR |
| CBD-04 | **Privacy by Default.** Keine Telemetrie oder sonstige ausgehende Verbindung ohne Opt-in; jede ausgehende Verbindung ist konfiguriert und dokumentiert. | N, LAB |

### Identität, Autorisierung, Mandantentrennung

| ID | Leitlinie | Prüfung |
|---|---|---|
| CBD-05 | **Keine anonyme Verwaltungsfunktion.** Jede API-Operation deklariert ihr benötigtes Recht; Ausnahmen stehen in einer versionierten Liste und liefern keine schützenswerten Daten. | PR, R |
| CBD-06 | **Mandanten-ID in jeder Autorisierungsentscheidung, am Ziel.** Fremde Objekte ergeben „nicht gefunden“; keine mandantenfremden Daten in Fehlern, Listen, Metriken oder Logs. Isolation zusätzlich durch Technik, nicht nur durch Prüfcode. | generierte Zwei-Mandanten-Tests je Operation |
| CBD-07 | **Vertrauen nie aus Netzposition oder Weiterleitung.** Das Ziel prüft das Original-Token selbst; Portal-Sitzungen werden am Eingang in kurzlebige, zielgebundene Tokens getauscht. | Simulation |
| CBD-08 | **Tokens tragen Identität, keine Rechte;** kurzlebig, sender- und zielgebunden, kein Durchreichen. Dauerhafte Geheimnisse nur gehasht und mit Pflicht-Ablauf. | Token-Tests |
| CBD-09 | **Knoten sind keine Principals für Mandantenoperationen;** Rollen und Platzierung folgen der Vertrauensstufe. Eignung nie aus Selbstauskunft; die Stufe sinkt sofort und steigt nur mit frischem Nachweis. | Simulation, REV |
| CBD-10 | **Privilegierte Aktionen** verlangen Step-up, Begründung und – je nach Profil – Vier-Augen-Prinzip; Plattform-Administration und Sicherheitsrolle sind getrennt. | PR |
| CBD-11 | **Betreiber sehen keine Mandanteninhalte** außer über einen genehmigten Zugriffsantrag. Jedes Feld hat eine Datenklasse; Mandanten-Metadaten erscheinen in Betreibersichten pseudonymisiert. Die Grenze wird Mandanten offen beschrieben. | PR, Isolationstests |
| CBD-12 | **Isolation durch Technik:** kein geteilter Kernel zwischen Mandanten, getrennte Kubernetes-Steuerungsebenen, VPC je Projekt in eigener VRF, eingehend default-deny, Datenschlüssel je Volume bzw. Bucket, keine Speicherdeduplizierung zwischen Mandanten. | Isolationstests, LAB, PT |

### KI-Agenten und MCP

| ID | Leitlinie | Prüfung |
|---|---|---|
| CBD-13 | **Agent = eigener Akteur mit Schnittmengen-Rechten.** Effektive Rechte = Principal ∩ Token-Scopes ∩ Agenten-Leitplanken; Standard-Token nur lesend; Principal und Akteur getrennt im Audit. | PR, N |
| CBD-14 | **Destruktive MCP-Aktionen nur mit Bestätigung außerhalb des Clients** – auf einer Plattformseite, die den Auswirkungsbericht selbst anzeigt und Passkey-Präsenz verlangt. Das Bestätigungstoken ist an alle Parameter gebunden und einmalig. | Bestätigungstests |
| CBD-15 | **Fremdgesteuerte Daten sind Daten, keine Anweisungen.** Frei befüllbare Felder von Mandanten oder Geräten sind als nicht vertrauenswürdig markiert, werden normalisiert und im Portal nie als HTML gerendert; Werkzeugbeschreibungen sind statisch und signiert. | PR |

Wie diese Regeln für KI-Dienste konkret wirken, beschreibt die [KI-Plattform](ki-plattform.html).

### Protokollierung, Datenschutz, Nachweise

| ID | Leitlinie | Prüfung |
|---|---|---|
| CBD-16 | **Jede API-Aktion wird auditiert** – in allen Kanälen identisch; Audit ist Teil der Durchsetzungskette und nicht abschaltbar. | generierter Test je mutierender Operation |
| CBD-17 | **Audit manipulationssicher und außerhalb der Zelle verankert:** Hash-Kette, Signatur, getrennte Ketten je Mandant, externer Anker; Widerrufslisten dürfen nie auf einen älteren Stand zurückfallen. | Manipulationstests |
| CBD-18 | **Keine Geheimnisse in Logs, Traces, Fehlermeldungen, Images oder Repositories.** Geheimnisse nur in Typen ohne Ausgabe und mit sicherem Überschreiben; Images ohne Geheimnisse. | Secret-Scanner, Canary-Test |
| CBD-19 | **Datenminimierung, Personenbezug markiert:** personenbezogene Felder sind gekennzeichnet; Aufbewahrung und Pseudonymisierung je Datenart konfigurierbar. | PR |
| CBD-20 | **Nachweise maschinenlesbar, signiert, kanalgleich**, mit OSCAL-Bezug. | PR, R |

### Kryptografie

| ID | Leitlinie | Prüfung |
|---|---|---|
| CBD-21 | **Krypto nur über Profile.** Kein Algorithmus fest im Code; jedes Chiffrat und jede Signatur trägt Algorithmus, Schlüssel-ID und Version; Regionen dürfen verschärfen, nie lockern. | Lint |
| CBD-22 | **Keine eigene Krypto:** etablierte Bibliotheken mit einem einzigen Provider, Kernel-Krypto, TPM; Zufall nur aus dem Kernel. | Abhängigkeitsprüfung, Testvektoren |
| CBD-23 | **BSI TR-02102 maßgeblich;** Abweichungen nur registriert und befristet. | Handshake-Matrix je Profil |
| CBD-24 | **Quantensichere Vertraulichkeit ab dem MVP:** hybride Post-Quanten-Schlüsseleinigung an allen eigenen TLS-Endpunkten; ruhende Daten mit AES-256. | PR, N |
| CBD-25 | **Verschlüsselung überall:** Steuerungsverkehr nur mTLS im verschlüsselten Underlay, Portal und API nur HTTPS mit HSTS, ruhende Daten standardmäßig verschlüsselt. | Lab-Prüfung |
| CBD-26 | **Schlüssel entstehen am Nutzungsort und verlassen ihn nicht;** Ausstellung per CSR, Fremdprozesse mit eigener Dienstidentität, nie mit dem Knotenschlüssel. | Lint, Simulation |

### Architekturgrenzen und Lieferkette

| ID | Leitlinie | Prüfung |
|---|---|---|
| CBD-27 | **Fremdkomponenten nur über Prozessgrenzen** – nie gelinkt, sondern als eigener Prozess mit eigenem Benutzer, minimalen Rechten und Sandbox (siehe [Rust-Stack](rust-stack.html)). | Abhängigkeitsprüfung, REV |
| CBD-28 | **Minimale, gepinnte, geprüfte Abhängigkeiten;** SBOM und Provenienz je Artefakt; signierte, reproduzierbare Builds (siehe [Release-Bündel](release-buendel.html)). | PR, R |
| CBD-29 | **Least Privilege:** privilegierte Operationen in genau einem Hilfsdienst; Parser an Vertrauensgrenzen in Prozessen ohne Zugriff auf Knotenschlüssel, mit Größenlimits und Fuzzing. | Fuzzing-Register |
| CBD-30 | **Eine Durchsetzungsstelle:** Authentisierung → Autorisierung → Validierung → Kontingent → Audit → Ausführung ist eine Kette für API, Portal, MCP und CLI (siehe [API-first](api-first.html)). | Paritätsprüfung |

### Knoten, Boot, Steuerungsebene

| ID | Leitlinie | Prüfung |
|---|---|---|
| CBD-31 | **Vertrauen entsteht nur durch Adoption,** nie durch Boot oder Netzposition. Adoption ist an einen auf dem Gerät erzeugten Schlüssel gebunden; Auto-Adoption ab Werk aus; kritische Rollen nie bei der Adoption (siehe [Boot und Adoption](boot-adoption.html)). | Simulation, LAB |
| CBD-32 | **Einseitige Signale lösen nie destruktive Aktionen aus.** Fencing, Widerruf oder Löschung brauchen ein Quorum; Sicherheitsentscheidungen schlagen geschlossen fehl, laufende Workloads bleiben stabil (siehe [Steuerungsebene](steuerungsebene.html)). | Simulation |
| CBD-33 | **Abweichungen sind Objekte, keine Kommentare** – auf Herstellerebene im Register, auf Installationsebene als API-Objekt, jeweils mit Begründung, Kompensation, Freigabe und Frist; beide im Compliance-Export. | PR |

### Löschung und Wiederherstellung

| ID | Leitlinie | Prüfung |
|---|---|---|
| CBD-34 | **Löschbar by Design.** Jeder neue Datenspeicher – auch Caches, Snapshots, Backups, Logs – hängt an der Schlüsselhierarchie, sodass Krypto-Löschung wirkt; Lösch- und Stilllegungsnachweise in einem signierten Format. | Integrationstest, REV |
| CBD-35 | **Wiederherstellbarkeit wird geübt:** verschlüsseltes Plattform-Backup, Restore ohne lebende Plattform, automatisierter Test-Restore mit Protokoll, Notfallrotation je Schlüsselklasse. | nächtliche Wiederherstellungsübung |

### Prozess

| ID | Leitlinie | Prüfung |
|---|---|---|
| CBD-36 | **Bedrohungsmodell und Normbezüge leben mit.** Jedes ADR, das Komponenten, Rollen, Vertrauensgrenzen oder Fremdkomponenten ändert, aktualisiert das Bedrohungsmodell im selben Änderungssatz; Normreferenzen tragen ihre Version. | Doku-Prüfung |

## CI-Prüfungen

Die Leitlinien werden durch 20 benannte, automatisierte Prüfungen abgesichert. Die wichtigsten Gruppen:

| Bereich | Was geprüft wird |
|---|---|
| Parität und API-Schema | gleiche Rechte und Funktionen über alle Kanäle; Pflichtangaben je Operation (Recht, Wirkung, Datenklasse, Markierungen für nicht vertrauenswürdige und personenbezogene Felder, Step-up) |
| Mandantentrennung | aus der API-Beschreibung generierte Zwei-Mandanten-Tests je Operation, Analyse der Autorisierungs-Policies |
| Audit | Vollständigkeit des Audit-Eintrags je mutierender Operation |
| Geheimnisse | Scanner, Verbotsregeln, Canary-Lauf, Image-Scan |
| Abhängigkeiten | Lizenzen, Sperrlisten, Quellen, Advisories, Lockfiles |
| Kryptografie | Lint, Handshake-Matrix je Profil, Anteil hybrider Schlüsseleinigung, HSTS |
| Release | SBOM, Signatur, Provenienz, Update-Metadaten, Nachbau |
| Compliance-Mapping | Abdeckung, Katalog-Pin, Abweichungsregister, OSCAL-Validierung |
| Voreinstellungen | Policy-as-Code-Prüfung der Frischinstallation |
| Simulation | Invarianten der Steuerungsebene: Knoten-Autorisierung, keine destruktiven Gossip-Signale, Mindeststufen, Quarantäne, kein privater Schlüssel im Zustand |
| Robustheit | Fuzzing-Register mit nächtlichem Lauf, Regeln für `unsafe` |
| Dokumentation | Pflichtabschnitt „Sicherheit & Compliance“, Existenz zitierter IDs |
| Agenten | Bestätigungs- und Step-up-Tests |
| Datenschutz | Egress-Mitschnitt einer unkonfigurierten Installation |
| Portal | Content Security Policy ohne Inline-Skripte |
| Löschung, Wiederherstellung | Krypto-Löschung ohne Schlüsselrest; Test-Restore einer Testzelle |

Die Leitlinien selbst werden zusätzlich als strukturierte Daten gepflegt; eine Prüfung stellt sicher, dass jede automatisch
geprüfte Leitlinie auf eine existierende CI-Prüfung verweist.

## Review-Checkliste

Für jeden Pull Request mit sicherheitsrelevanter Änderung:

1. Neue oder geänderte Operation: Recht, Wirkung, Datenklasse, Step-up, Bestätigungspflicht deklariert?
2. Mandantenbezug: Prüfung am Ziel, keine fremden Daten in Fehlern, Listen oder Metriken?
3. Neue Eingabe über eine Vertrauensgrenze: Sandbox-Prozess, Limits, Fuzzing-Ziel, Markierung als nicht vertrauenswürdig?
4. Geheimnisse: nur im geschützten Typ, keine Logs, Verteilung nur nach Bedarf und Mindeststufe?
5. Kryptografie: nur über Profil und zentrale Krypto-Bibliothek, Formatversion, Eintrag im Krypto-Inventar?
6. Fremdkomponente: Prozessgrenze, Lizenz, Allowlist, Sandbox, SBOM?
7. Rolle oder Platzierung: Mindest-Vertrauensstufe korrekt, Herabstufung behandelt?
8. Neuer Speicherort: in der Schlüsselhierarchie, mit Löschpfad und Aufbewahrung?
9. Voreinstellung sicher, Homelab-Fallback vorhanden, Lockerung nur als Abweichungsobjekt?
10. Bedrohungsmodell und Compliance-Mapping im selben PR aktualisiert?

Sicherheitskritische Pfade – PKI, Konsens, Autorisierung, Identität, Boot und Discovery, Update, Kryptografie, KMS, Audit,
MCP-Bestätigung, Attestierung – brauchen zwei Reviewer.

## ADR-Vorlage „Sicherheit & Compliance“

Jedes neue ADR und Fachkonzept enthält einen Abschnitt „Sicherheit & Compliance“ mit elf Unterabschnitten. Eine **Kurzform**
(nur S3, S4 und S9 plus Begründung „keine neue Angriffsfläche“) ist erlaubt, wenn keine neue Komponente, Rolle,
Vertrauensgrenze, Fremdkomponente, Datenart oder kein neuer Speicherort eingeführt wird.

| Abschnitt | Inhalt |
|---|---|
| S1 Schutzobjekte und Datenklassen | Schutzobjekte mit Informationsart, Datenklasse, Schutzbedarf (Vertraulichkeit, Integrität, Verfügbarkeit) und Ort |
| S2 Vertrauensgrenzen und Bedrohungen | berührte oder neue Vertrauensgrenzen, Datenflüsse, Bedrohungen mit Bewertung vor und nach Maßnahmen, Test-ID; Parser und Fuzzing-Ziele; Mindest-Vertrauensstufe neuer Rollen |
| S3 Leitlinien-Konformität | je Leitlinie CBD-01 bis CBD-36: erfüllt durch welchen Abschnitt, nicht anwendbar (mit Grund) oder Abweichung (mit Register-ID) |
| S4 Anforderungs-Mapping | betroffene Anforderungen mit Erfüllungsgrad und Priorität; neue Anforderungskandidaten |
| S5 Normbezug | Grundschutz++-Anforderungen mit ID und UUID, Zielobjekt, weitere Normen (C5, ISO, CRA, TR-02102) |
| S6 Shared Responsibility | je Funktion: Verantwortung, Voreinstellung je Betriebsprofil, Betreiber- und Mandantenaufgabe, Homelab-Fallback |
| S7 Kryptografie | neue Einträge im Krypto-Inventar und ihre Wirkung je Kryptoprofil; Schlüssel-Lebenszyklus |
| S8 Fremdkomponenten und Lieferkette | Version, Quelle, Lizenz, Grenze, Sandbox, Dienstidentität, SBOM, Signatur |
| S9 Nachweis | was nachgewiesen wird, Nachweisart, API-Operation, automatischer Test, Aufnahme in den Compliance-Export |
| S10 Datenschutz, Aufbewahrung, Löschung | personenbezogene Felder, Zweck, Aufbewahrung; neue Speicherorte und Löschpfad |
| S11 Offene Sicherheitsfragen | offene Fragen mit Zuständigkeit für die Klärung |

### Definition of Done für ADRs

| Nr. | Kriterium |
|---|---|
| D1 | Abschnitt „Sicherheit & Compliance“ vollständig oder begründete Kurzform |
| D2 | Alle Leitlinien in S3 bewertet; jede Abweichung hat eine Register-ID |
| D3 | Jede neue Bedrohung hat eine Maßnahme mit Test-ID oder ein ausdrücklich akzeptiertes Restrisiko; ein verbleibendes „hoch“ blockiert das Release |
| D4 | Jede in S4 genannte Anforderung existiert; Prioritätsabweichungen sind als Änderungsantrag formuliert |
| D5 | Shared Responsibility mit Homelab-Fallback je Funktion |
| D6 | Offene Entscheidungen ausdrücklich markiert, nicht vorweggenommen |
| D7 | Widersprüche zu angenommenen Dokumenten als Änderungsvorschlag benannt, nicht stillschweigend überschrieben |

## Pflege

- **Verantwortung:** eine Rolle „Compliance-Verantwortliche(r) des Projekts“, zugleich zuständig für den Katalog-Diff der
  Grundschutz-Modellierung.
- **Anlässe für eine Überarbeitung:** neue Fassung des Anforderungskatalogs, neue Regelwerksstände (etwa C5:2026, TR-02102,
  harmonisierte CRA-Normen), Befunde aus Pentests und Audits, wiederholte Abweichungen von derselben Leitlinie – mindestens aber
  vor jedem Minor-Release, gemeinsam mit dem Bedrohungsmodell.
- **Änderungsweg:** neue Fassung mit Änderungshistorie; IDs werden nie wiederverwendet.
