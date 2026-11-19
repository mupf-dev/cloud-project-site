# Inhaltsregeln für content/doku/*.md (und content/en/doku/*.md)

Diese Seiten sind **öffentlich**. Sie sind aufbereitete Fassungen der internen Konzeptdokumente,
keine Kopien.

## Format (vom Generator `build.py` unterstützt)

Kopfbereich, dann eine Zeile `---`:

```
title: Netzwerk
summary: Ein Satz, der die Seite beschreibt (für Übersicht und Suche).
group: konzept        # konzept | prozess
order: 60             # Sortierung in der Übersicht
quelle: Konzept 06    # neutrale Quellenangabe, ohne Ticketschlüssel
---
```

Danach Markdown-Teilmenge:

- Überschriften `##` und `###` (kein `#` – der Titel kommt aus dem Kopf), `####` sparsam
- Absätze, `**fett**`, `*kursiv*`, `` `code` ``, Links `[Text](ziel)` – intern nur auf andere
  Doku-Seiten als `dateiname.html` (ohne Pfad) oder auf `../funktionen.html`, `../architektur.html`
- Listen mit `- ` und `1. ` (eine Verschachtelungsebene mit zwei Leerzeichen Einrückung ist ok)
- Tabellen mit `| a | b |` und Trennzeile `|---|---|`
- Zitate/Hinweise mit `> `
- Codeblöcke mit ``` nur für kurze Konfig-/CLI-Beispiele (`sh`, `yaml`, `toml`, `json`, `text`)

## Englische Fassungen

- Ablage unter `content/en/seiten/` bzw. `content/en/doku/` mit englischem Dateinamen
  (z. B. `netzwerk.md` → `network.md`), Kopffeld `de: netzwerk` zusätzlich.
- `group`, `order`, `toc`, `noindex`, `hero` unverändert übernehmen; Links auf englische Slugs
  (Hauptseiten verlinken Doku als `docs/<slug>.html`).
- Projektname: BYOC bzw. „BYOC“ wird nicht übersetzt.

## Inhalt

- Deutsch (bzw. Englisch in `content/en/`), sachlich, verständlich für Fachpublikum (Betreiber, Entwickler). Kernentscheidungen,
  Begründungen, Abläufe und Begriffe erhalten; Details, die nur intern relevant sind, weglassen.
- Umfang je Seite etwa 800–2500 Wörter. Lieber gut strukturiert als vollständig.

## Strikt verboten (wird von `check-leaks.sh` geprüft)

- Ticketschlüssel des internen Projektmanagements – entfernen oder neutral umschreiben („siehe Konzept Netzwerk“,
  „ein späteres Arbeitspaket“). Verweise auf andere Konzepte als Link auf die passende Doku-Seite.
- Interne Infrastruktur: interne Domains, Projektmanagement-Werkzeug, Build-Server und Hoster,
  Lab-Zugänge, reale IP-Adressen, Hostnamen, E-Mail-Adressen, Personen-
  oder Accountnamen, Schlüssel, Fingerprints, PEM-Blöcke.
  Beispieladressen nur aus 192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24, 2001:db8::/32 oder
  `example.org`/`example.com`.
- Implementierungscode: keine Rust-/TS-/Shell-Skript-Auszüge, keine Funktions-/Typdefinitionen
  (`fn`, `impl`, `struct`, `use crate`, `pub `, `async fn`). Keine Pfade zu `.rs`-Dateien,
  keine langen Dateipfadlisten der Implementierung. Crate-/Binärnamen wie `cp-agent`, `cp-dnsd`
  im Fließtext sind ok.
- Interne Sprintberichte nicht verwenden.
- Offene Sicherheitslücken, Abweichungslisten (compliance/mapping/abweichungen.toml), detaillierte
  Angriffspfade, Restrisiko-Listen, konkrete Schwachstellen.
- Nutzer-/Personenbezüge („der Nutzer hat entschieden“ → „entschieden am 2026-11-14“ ist ok,
  Datum ist erlaubt).
