# BYOC (Build Your Own Cloud) – Projekt-Website

Quellen und Generator der öffentlichen Website von **BYOC** (Build Your Own Cloud, Alpha-Name),
einer quelloffenen, dezentralen und mandantenfähigen Cloud-Plattform in Rust. Komponenten tragen
das Präfix `cp` (`cpctl`, `cpOS`, `cp-agent` …); der Name dieses Repositorys bleibt unverändert.

Die Website ist zweisprachig: **Deutsch** an der Wurzel, **Englisch** unter `en/`. Jede Seite hat
einen Sprachumschalter zur Entsprechungsseite, `hreflang`-Links und ein korrektes `lang`-Attribut;
jede Sprache hat einen eigenen Suchindex (`suche-index.json` bzw. `en/search-index.json`).

Dieses Repository enthält **nur die Website** – keinen Plattform-Quellcode. Die Inhalte sind
aufbereitete Fassungen der Projektdokumente (Konzepte, Architekturentscheidungen, Prozesse).

## Aufbau

| Pfad | Inhalt |
|---|---|
| `content/seiten/*.md` | Hauptseiten: Start, Funktionen, Architektur, Status & Roadmap, Mitmachen, Impressum, Datenschutz |
| `content/doku/*.md` | Dokumentationsseiten (Konzepte und Prozesse) |
| `content/en/seiten/*.md`, `content/en/doku/*.md` | englische Fassungen; Kopffeld `de: <slug>` nennt die deutsche Entsprechung |
| `static/` | Icon und Bilder – werden nach `docs/assets/` kopiert |
| `static/img/portal/` | Portal-Screenshots (WebP, je hell/dunkel und DE/EN; echtes Portal, fiktive Demodaten) – nach `docs/assets/img/` kopiert |
| `build.py` | Angaben der Website für den Generator (nur Python-Standardbibliothek, ab Python 3.9) |
| `check-leaks.py`, `check-leaks.sh` | Prüfung auf verbotene Inhalte |
| `kit/` | Kopie des gemeinsamen Design-Kerns **site-kit** (Generator `sitekit.py`, Prüflogik `leakcheck.py`, Stylesheet-Kern, Skript, Akzent-Theme) – nicht hier bearbeiten, siehe unten |
| `sitekit.json` | Name des Akzent-Themes in site-kit (`byoc`) |
| `tools/INHALTSREGELN.md` | Regeln für Inhalte und das unterstützte Markdown |
| `docs/` | **generierte** Website (wird eingecheckt, von GitHub Pages ausgeliefert) |

Die Seiten verwenden eine kleine Markdown-Teilmenge (Überschriften, optional mit eigener
Sprungmarke `## Titel {#id}`, Absätze, Listen, Tabellen, Zitate, Code-Blöcke, Links). Diagramme und
die Startseite sind Inline-SVG/HTML in Blöcken `::: html … :::`. Es gibt kein externes JavaScript,
keine Webfonts, kein CDN und kein Tracking; hell/dunkel folgt `prefers-color-scheme`, Animationen
entfallen bei `prefers-reduced-motion`. Farben, Radien und Schatten folgen den Design-Tokens des
Portals (Variante „Technisch“).

Kopffeld `wide: ja` hebt die Lesebreite einer Hauptseite auf (z. B. für die Screenshot-Galerie `portal.html`).
Screenshots stehen in `<picture>` mit `<source media="(prefers-color-scheme: dark)">`, mit `width`/`height`,
`loading="lazy"` und Alt-Text in der Seitensprache.

Eine neue Seite braucht beide Sprachen: deutsche Quelle anlegen, englische Fassung mit
`de: <deutscher-slug>` im Kopf ergänzen. Der Build meldet Seiten ohne Gegenstück als Fehler.

## Design-Kern (site-kit)

Gestaltung, Generator und Prüflogik sind für alle Projekt-Websites gleich und kommen aus dem Repo
**site-kit**; `kit/` ist eine eingecheckte Kopie davon. Diese Website bestimmt nur ihre Angaben in
`build.py` (Name, Navigation, Texte, Logo, Umbruchstellen der Kopfzeile), ihre zusätzlichen Muster in
`check-leaks.py` und das Theme in `sitekit.json`. Das Stylesheet entsteht beim Bauen aus
`kit/style.css` + `kit/theme.css`. Kern aktualisieren:

```sh
python3 ../site-kit/sync.py .   # kit/ auf den Stand von site-kit bringen (--check: nur prüfen)
./check-leaks.sh                # neu bauen und prüfen; kit/ und docs/ zusammen committen
```

## Bauen und prüfen

```sh
./check-leaks.sh          # baut nach docs/ und prüft Ausgabe + Quellen; Exit 1 bei Funden
python3 build.py          # nur bauen
python3 -m http.server -d docs 8000   # lokal ansehen: http://localhost:8000/
```

`build.py` prüft nach dem Bauen alle internen Links und Sprungmarken (beide Sprachen) sowie die
Zuordnung DE ↔ EN und bricht bei Fehlern ab.

`check-leaks.py` sucht unter anderem nach Ticketschlüsseln des internen Projektmanagements,
Namen interner Infrastruktur und Hoster, E-Mail-Adressen, Schlüsselmaterial (PEM-Blöcke),
IPv4-Adressen außerhalb der Dokumentationsnetze nach RFC 5737, konkreten IPv6-ULA-Präfixen,
Rust-Code (`fn`, `impl`, `use crate`, Attribute, `struct`) und Pfaden zu `.rs`-Quelldateien.
Interne Namen sind im Skript nur als SHA-256-Hash hinterlegt. Bilder unter `img/` (in `static/` und `docs/`) prüft es zusätzlich: nur WebP, PNG oder SVG, Inhalt passend zur
Endung, keine Metadaten (EXIF, XMP, ICC-Profil, Text-/Zeit-Chunks). Die Kontaktadresse und die
Anbieterdaten sind ausschließlich auf Impressum/Datenschutz bzw. Legal notice/Privacy policy
erlaubt (nicht im Suchindex). Weitere, nicht zu veröffentlichende
Muster können lokal in `.leak-patterns.local` (eine Regex je Zeile, per `.gitignore`
ausgeschlossen) ergänzt werden.

**Vor jedem Commit `./check-leaks.sh` ausführen** – der Lauf muss grün sein.

## Veröffentlichung mit GitHub Pages

Gewählt ist die einfachste Variante ohne Actions-Workflow:

1. Öffentliches Repository anlegen und `main` pushen (inklusive des generierten Ordners `docs/`).
2. *Settings → Pages → Build and deployment → Source: „Deploy from a branch“*,
   Branch **`main`**, Ordner **`/docs`**.
3. Nach Änderungen: `./check-leaks.sh`, dann `docs/` mit committen und pushen.

`docs/.nojekyll` schaltet die Jekyll-Verarbeitung ab, die Seiten werden unverändert ausgeliefert.
Alle Links sind relativ; die Website funktioniert daher unter `https://<owner>.github.io/<repo>/`
ebenso wie unter einer eigenen Domain.

## Lizenz

- **Inhalte der Website** (Texte, Diagramme, `content/`, generiertes `docs/`):
  [CC BY 4.0](LICENSES/CC-BY-4.0.txt) – wie die Dokumentation im Projekt-Repository.
- **Generator, Prüfskript, Stylesheet und Skript** (`build.py`, `check-leaks.*`, `kit/`):
  [AGPL-3.0-or-later](LICENSES/AGPL-3.0-or-later.txt) – wie der Kern des Projekts.

Namensnennung: „cloud-project contributors“ (Urheberbezeichnung wie im Projekt-Repository).
