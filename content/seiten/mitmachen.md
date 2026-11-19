title: Mitmachen und Lizenz
summary: Wie man zu cloud-project beitragen kann, unter welchen Lizenzen Code und Dokumentation stehen und wie Sicherheitslücken gemeldet werden.
toc: ja
---
## Mitmachen

cloud-project ist als Gemeinschaftsprojekt angelegt. Der Quellcode-Repository wird geöffnet,
sobald Lizenzdateien, Sicherheitsrichtlinie und REUSE-Konformität vollständig sind. Bis dahin
freuen wir uns über Rückmeldungen zu Konzepten und Architektur.

Willkommen sind insbesondere:

- **Rückmeldungen zu den Konzepten** in der [Dokumentation](doku/index.html) – Annahmen,
  Lücken, bessere Alternativen.
- **Erfahrungen aus dem Betrieb** von Homelabs, Edge-Standorten und Rechenzentren:
  Hardware, Netztopologien, Anforderungen aus Compliance-Prüfungen.
- **Tests auf ungewöhnlicher Hardware** (ARM-Boards, ältere Notebooks, Server mit und ohne BMC),
  sobald Vorabversionen verfügbar sind.
- **Code** in Rust für Agent, Rollen und Werkzeuge, TypeScript für das Portal, Dokumentation und
  Übersetzungen.

## Regeln für Beiträge

- **DCO statt CLA:** Beiträge stehen unter dem
  [Developer Certificate of Origin 1.1](https://developercertificate.org/). Jeder Commit trägt eine
  `Signed-off-by:`-Zeile (`git commit -s`). Es gibt keine Rechteübertragung an eine Firma.
- **Qualität vor Geschwindigkeit:** Formatierung, Lints ohne Warnungen, Tests,
  Lizenz- und Abhängigkeitsprüfung, Sicherheitsaudit der Abhängigkeiten, SBOM und MSRV-Prüfung
  laufen in der CI und müssen grün sein.
- **Kein `unsafe`** ohne begründeten Eintrag in einem eigenen Register; neue Abhängigkeiten nur
  zentral im Workspace und nach Prüfung von Lizenz, Wartungsstand und Prozessgrenzen.
- **Jede Datei trägt SPDX-Lizenzangaben** (REUSE-konform).
- **Sicherheitskritische Pfade** – PKI, Konsens, Autorisierung, Boot und Discovery, Update – brauchen
  zwei Reviews.
- **Neue Funktionen in allen drei Zugängen:** Was über die API geht, muss auch im Portal und per MCP
  gehen; die Paritätsprüfung in der CI erzwingt das.
- **Architekturentscheidungen als ADR** mit dem verpflichtenden Abschnitt „Sicherheit &
  Compliance“ (siehe [Compliance-by-Design](doku/compliance-by-design.html)).

```sh
# typischer Ablauf für Mitwirkende (nach Freigabe des Repositorys)
cargo xtask setup      # Werkzeuge in festen Versionen installieren
cargo xtask ci         # alle Prüfungen lokal ausführen
git commit -s -m "Kurzbeschreibung"
```

## Lizenz

Die Lizenzentscheidung ist in der [ADR Lizenz und Governance](doku/lizenz-governance.html)
begründet (angenommen 2026-11-12).

| Bestandteil | Lizenz |
|---|---|
| Kern: Agent, Steuerungsebene, Dienste, Portal, MCP-Server, Image-Bau-Werkzeuge | GNU AGPL-3.0-or-later |
| SDKs, Client-Bibliotheken, CLI, API-Spezifikationen, MCP-Schemata | Apache-2.0 OR MIT |
| Dokumentation, Konzepte, Diagramme (auch diese Website) | CC BY 4.0 |
| Code-Beispiele und Konfigurationsvorlagen | MIT-0 |
| Logos und Produktname | nicht frei lizenziert, Markenrichtlinie |

Die AGPL stellt sicher, dass Verbesserungen an der Plattform auch dann der Gemeinschaft zugutekommen,
wenn veränderte Fassungen als Dienst über das Netz angeboten werden. Clients und SDKs stehen unter
freizügigen Lizenzen, damit sie sich in beliebige Software einbauen lassen. Die Lizenz ist
festgelegt, aber bis zur ersten Veröffentlichung juristisch abschließend zu prüfen.

## Sicherheitslücke melden

Bitte **keine öffentlichen Issues, Pull Requests oder Diskussionen** für Sicherheitsprobleme.

- **Bevorzugt:** GitHub *Private Vulnerability Reporting* im Projekt-Repository (Reiter „Security“ →
  „Report a vulnerability“).
- **Alternativ per E-Mail:** die Adresse samt OpenPGP-Schlüssel wird vor dem ersten öffentlichen
  Release festgelegt und auch unter `/.well-known/security.txt` veröffentlicht.

| Schritt | Frist |
|---|---|
| Eingangsbestätigung | ≤ 3 Werktage |
| Ersteinschätzung (CVSS v4.0) | ≤ 7 Kalendertage |
| Statusmeldungen an Meldende | mindestens alle 14 Tage |
| Behebung (Ziel) | kritisch ≤ 14 Tage, hoch ≤ 30 Tage, mittel ≤ 90 Tage |
| Veröffentlichung | mit dem Fix, spätestens nach 90 Tagen Embargo |

Aktiv ausgenutzte Schwachstellen werden nach Art. 14 des Cyber Resilience Act gemeldet. Der
vollständige Ablauf steht unter [Schwachstellenmanagement](doku/schwachstellenmanagement.html).

## Über diese Website

Diese Seite ist statisch erzeugt – ohne Cookies, Tracking, externe Schriften oder Skripte von
Drittanbietern. Die Suche läuft vollständig im Browser. Die Inhalte sind aufbereitete Fassungen der
Projektdokumente und stehen unter CC BY 4.0.
