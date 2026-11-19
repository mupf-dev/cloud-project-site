title: Schwachstellenmanagement
summary: Wie cloud-project Sicherheitsmeldungen annimmt, bewertet, behebt und veröffentlicht – einschließlich Fristen, CRA-Meldepflichten, VEX und SBOM.
group: prozess
order: 230
quelle: Prozessbeschreibung Schwachstellenmanagement und Sicherheitsrichtlinie
---

## Grundsatz

cloud-project behandelt Sicherheitsmeldungen nach dem Prinzip der **koordinierten Offenlegung** (Coordinated
Vulnerability Disclosure, CVD): Eine Schwachstelle wird vertraulich gemeldet, im Embargo behoben und dann gemeinsam
mit der Korrektur veröffentlicht.

Grundlage ist der europäische **Cyber Resilience Act** (Verordnung (EU) 2024/2847, CRA), insbesondere Art. 13, 14
und 24 sowie Anhang I Teil II. Das Projekt versteht sich als **Open-Source-Steward** im Sinne von Art. 24, betreibt
den Meldeprozess aber so, **als gälten die Herstellerpflichten nach Art. 14 bereits**. Die abschließende rechtliche
Einstufung ist noch offen.

## Rollen

| Rolle | Aufgabe |
|---|---|
| **PSIRT-Leitung** | verantwortet Triage, Embargo, Advisory und CRA-Meldung; entscheidet über Fristen |
| **Vertretung** | gleiche Befugnisse; Erreichbarkeit rund um die Uhr im Wechsel (wegen der 24-Stunden-Frist) |
| **Fach-Maintainer** | Analyse und Korrektur in der betroffenen Komponente |
| **Release-Verantwortliche** | Sicherheitsrelease, Offline-Signatur, Update-Metadaten (siehe [Release-Signatur](release-signatur.html)) |
| **Meldende** | externe Forschende, Betreiber, Upstream-Projekte |

Das **Vier-Augen-Prinzip** gilt für: Herabstufung eines Schweregrads, VEX-Aussage „nicht betroffen“,
Fristverlängerung und Veröffentlichung.

## Meldewege

**Bitte keine öffentlichen Issues, Pull Requests oder Diskussionen für Sicherheitsprobleme.**

1. **Bevorzugt:** GitHub *Private Vulnerability Reporting* – im Repository des Projekts Reiter „Security“ →
   „Report a vulnerability“. Daraus entsteht ein vertraulicher Entwurf eines GitHub Security Advisory mit privatem
   Fork für die Korrektur.
2. **E-Mail:** Eine Sicherheits-Kontaktadresse mit OpenPGP-Schlüssel **wird vor dem ersten Release festgelegt** und
   dann auch über `/.well-known/security.txt` veröffentlicht.

Hilfreich in einer Meldung sind: betroffene Version oder Commit, Komponente (etwa `cp-agent`, Portal, OS-Image),
Konfiguration, Reproduktionsschritte oder Proof of Concept, erwartete Auswirkung, ob die Lücke bereits ausgenutzt wird
oder öffentlich bekannt ist, und ob und wie Meldende genannt werden möchten.

Neben externen Meldungen fließen weitere Quellen in denselben Prozess:

- automatische Abhängigkeitsprüfungen (Advisory-Datenbanken für Rust- und npm-Abhängigkeiten, täglich und in der CI),
- Abgleich **bereits veröffentlichter** Release-Binaries gegen neue Advisories über die eingebettete
  Abhängigkeitsliste,
- eigene Funde aus Review, Fuzzing und Penetrationstests (wie externe Meldungen, nur ohne Kommunikation mit
  Meldenden),
- Hinweise von Behörden und CSIRTs sowie Kataloge aktiv ausgenutzter Schwachstellen.

## Zusagen und Fristen

| Schritt | Frist |
|---|---|
| Eingangsbestätigung | ≤ 3 Werktage |
| Ersteinschätzung (Gültigkeit, Schweregrad) | ≤ 7 Kalendertage |
| Statusmeldungen an Meldende | mindestens alle 14 Tage |
| Behebung (Ziel) | kritisch ≤ 14 Tage, hoch ≤ 30 Tage, mittel ≤ 90 Tage, niedrig mit regulärem Release |
| Veröffentlichung (Advisory, CVE) | mit der Korrektur, spätestens nach **90 Tagen** Embargo; Verlängerung nur einvernehmlich |
| aktiv ausgenutzte Schwachstelle | Meldung nach CRA Art. 14 binnen 24 Stunden / 72 Stunden / 14 Tagen |

Bei öffentlicher Ausnutzung oder einem Leck während des Embargos wird sofort veröffentlicht, gegebenenfalls mit
Workaround.

## Triage

1. **Eingang bestätigen**, vertraulichen Advisory-Entwurf anlegen, Embargo beginnen, Wünsche der Meldenden (Nennung)
   erfassen.
2. **Gültigkeit und Geltungsbereich:** reproduzieren, Duplikate und bekannte Probleme prüfen, betroffene Komponente
   bestimmen.
3. **Betroffene Versionen** über die SBOM des jeweiligen Release ermitteln; bei OS-Images über die Image-SBOM.
4. **Bewertung:**
   - **CVSS v4.0** einschließlich der Threat-Metrik *Exploit Maturity*, zusätzlich CVSS v3.1 für die Kompatibilität
     mit verbreiteten Scannern.
   - **EPSS** bei Fremd-CVEs; ab einer Ausnutzungswahrscheinlichkeit von 0,1 oder bei Eintrag in einen Katalog aktiv
     ausgenutzter Schwachstellen mindestens Priorität „hoch“.
   - **Plattformkontext:** Ist die Lücke aus einer Mandanten-Workload erreichbar? Über Netzboot oder Discovery ohne
     Authentisierung? Betrifft sie die Mandantentrennung oder Schlüsselmaterial? Dann wird aufgewertet (siehe
     [Sicherheitsmodell](sicherheitsmodell.html)).
5. **Priorität und Frist festlegen:**

| Priorität | Kriterium (Richtwert) | Ziel für die Korrektur |
|---|---|---|
| P0 kritisch | CVSS ≥ 9,0, aktiv ausgenutzt oder Mandantentrennung gebrochen | ≤ 14 Tage, ggf. sofortige Abhilfe |
| P1 hoch | CVSS 7,0–8,9 oder hohe Ausnutzungswahrscheinlichkeit | ≤ 30 Tage |
| P2 mittel | CVSS 4,0–6,9 | ≤ 90 Tage |
| P3 niedrig | CVSS < 4,0, nur Build-Zeit, nicht ausnutzbar | nächstes reguläres Release bzw. VEX |

6. **Entscheidung „aktiv ausgenutzt?“** mit Belegen, Quelle und Zeitpunkt der Kenntnis dokumentieren – bei „ja“
   startet sofort der CRA-Meldeprozess.

## Behebung und Veröffentlichung

1. Die Korrektur entsteht im **privaten Fork** des Advisory – kein öffentlicher Pull Request während des Embargos –
   mit Regressionstest und Review durch eine zweite Person.
2. Die **CVE-Kennung** wird über GitHub als CNA angefordert; der Advisory-Text nennt betroffene und behobene
   Versionen, CVSS-Vektor, Workarounds und Credits.
3. Ein **Sicherheitsrelease** kann getrennt von Funktionsänderungen erscheinen (PATCH-Version): Build, Nachbau,
   Signaturen und Offline-Signatur der Update-Metadaten, danach gestaffelter Rollout im Cluster (siehe
   [Rollout-Controller](rollout.html)).
4. **Gleichzeitige Veröffentlichung:** GitHub Security Advisory, maschinenlesbares Advisory im Format **CSAF 2.0**,
   aktualisierte VEX-Aussagen, Release-Notes und Benachrichtigung der Betreiber. Später zeigt das Portal zusätzlich
   betroffene Knoten an.
5. Schwachstellen in **Fremdkomponenten** werden an die Upstream-Maintainer gemeldet (CRA Art. 13 Abs. 6); das Projekt
   teilt Korrekturen und gibt eine eigene VEX-Aussage für seine Produkte ab.

## CRA-Meldepflichten

Die Meldepflichten nach Art. 14 gelten für **aktiv ausgenutzte Schwachstellen** im Produkt und für
**schwerwiegende Sicherheitsvorfälle**, die die Sicherheit des Produkts beeinträchtigen. Gemeldet wird über die
**Single Reporting Platform** der ENISA an das als Koordinator benannte CSIRT – für Deutschland das BSI – und
gleichzeitig an die ENISA.

| Frist ab Kenntnis | Aktiv ausgenutzte Schwachstelle | Schwerwiegender Vorfall |
|---|---|---|
| **24 Stunden** | Frühwarnung: Produkt, ggf. betroffene Mitgliedstaaten | Frühwarnung, inkl. Verdacht auf böswillige Ursache |
| **72 Stunden** | Meldung: Art der Ausnutzung, ergriffene und empfohlene Maßnahmen, Sensibilität der Informationen | Meldung: Art des Vorfalls, erste Bewertung, Abhilfemaßnahmen |
| **14 Tage** nach verfügbarer Korrektur | Abschlussbericht: Beschreibung, Schweregrad, Angaben zum Akteur (soweit bekannt), Update bzw. Abhilfe | – |
| **1 Monat** nach der 72-Stunden-Meldung | – | Abschlussbericht |
| auf Anforderung | Zwischenberichte | Zwischenberichte |

Zusätzlich werden **betroffene Nutzer informiert** (Art. 14 Abs. 8) – wo möglich strukturiert und maschinenlesbar
über CSAF und VEX.

**Ablauf in Kurzform:** Kenntniszeitpunkt in UTC festhalten → PSIRT-Leitung oder Vertretung alarmieren →
Frühwarnung binnen 24 Stunden aus einer Vorlage absenden und Eingangsbestätigung ablegen → Meldung nach 72 Stunden
mit Analysestand → Korrektur oder Abhilfe → Abschlussbericht → Nachbereitung mit Aktualisierung des
Bedrohungsmodells. Die Fristen laufen auch an Wochenenden und Feiertagen; deshalb gibt es die Vertretungsregel. Vor dem
ersten öffentlichen Release ist eine Probe-Meldung vorgesehen.

**Abgrenzung:** Betreiber einer Installation melden **Betriebsvorfälle** nach NIS2 bzw. Datenschutzrecht selbst
(geteilte Verantwortung). Das Projekt unterstützt sie dabei mit Advisories, VEX und SBOM.

## VEX

VEX (*Vulnerability Exploitability eXchange*) beschreibt maschinenlesbar, ob ein Produkt von einer bekannten
Schwachstelle tatsächlich betroffen ist. Das Projekt pflegt VEX-Aussagen im Format **OpenVEX** im Repository, jede
Änderung per Pull Request mit Vier-Augen-Review.

- **Status:** `not_affected`, `affected`, `fixed`, `under_investigation`.
- **Pflichtangaben:** `not_affected` nur mit gültiger Begründung oder Auswirkungsbeschreibung, `affected` nur mit
  Handlungsempfehlung. Ein CI-Schritt prüft das und erzeugt eine normalisierte Ausgabe, die dem Release beiliegt.
- **Wirkung in der CI:** Befunde der Abhängigkeitsprüfung werden nur dann akzeptiert, wenn eine VEX-Aussage
  „nicht betroffen“ oder „behoben“ für genau diese Schwachstelle **und** genau dieses Paket vorliegt. Ausnahmen in
  der Rust-Abhängigkeitsprüfung brauchen Begründung und Ablaufdatum und werden zusätzlich als VEX dokumentiert.
- **Ausbau:** CSAF-VEX aus OpenVEX erzeugen, Produktkennungen aus der SBOM übernehmen, VEX im Release signieren und
  im Portal abgleichen.

## SBOM

- Je Release und Komponente gibt es eine SBOM in **CycloneDX 1.5** und **SPDX 2.3**, reproduzierbar erzeugt (siehe
  [Release-Signatur](release-signatur.html)).
- Die Binaries enthalten ihre Abhängigkeitsliste eingebettet; Advisory-Prüfungen funktionieren damit auch direkt an
  installierten Knoten.
- Die npm-Abhängigkeiten des Portals werden über Lockfile-Integrität, Advisory-Prüfung und Lizenzliste abgedeckt.
- Das OS-Image erhält eine eigene SBOM aus der Image-Pipeline (siehe [OS-Image](os-image.html)); das
  [Release-Manifest](release-buendel.html) verweist per Hash darauf.

## Unterstützte Versionen

Das Projekt befindet sich **vor dem ersten Release** (Version 0.x, API `v1alpha1`). Bis dahin erfolgen
Sicherheitskorrekturen auf dem Entwicklungszweig; 0.x-Vorabversionen werden nicht gepflegt. Ab dem ersten stabilen
Release wird ein **Unterstützungszeitraum** veröffentlicht – Ziel nach CRA sind mindestens fünf Jahre
Sicherheitsupdates, getrennt von Funktionsupdates bereitstellbar.

## Geltungsbereich und Safe Harbor

Im Geltungsbereich ist alles im Repository: Agent und Bibliotheken, Portal, MCP-Server, OS-Image- und Boot-Pipeline
sowie Build- und Release-Werkzeuge einschließlich Signatur und Update-Metadaten. Nicht im Geltungsbereich sind
Schwachstellen in Fremdkomponenten ohne Bezug zur Nutzung im Projekt, Social Engineering, physische Angriffe,
Denial-of-Service durch reines Volumen gegen fremde Infrastruktur und reine Scanner-Befunde ohne nachvollziehbare
Auswirkung.

Wer in gutem Glauben und im Rahmen dieser Richtlinie forscht – nur eigene Installationen oder Testumgebungen nutzt,
keine Daten Dritter einsieht, verändert oder löscht, keinen Dienst beeinträchtigt und vertraulich meldet –, gegen den
leitet das Projekt keine rechtlichen Schritte ein und unterstützt solche auch nicht.

## Offene Punkte

Sicherheits-Kontaktadresse mit OpenPGP-Schlüssel und `security.txt`, Besetzung des PSIRT, Registrierung bei der
Single Reporting Platform und Probe-Meldung, Bereitstellung der CSAF-Advisories sowie die rechtliche Prüfung der
CRA-Rolle.
