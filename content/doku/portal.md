title: Portal-Technologie
summary: Architekturentscheidung für das Web-Portal – warum eine Svelte-5-SPA, eingebettet in den Agenten, gegenüber Rust/WASM, React und Server-Rendering gewonnen hat.
group: konzept
order: 120
quelle: Konzept 11 (ADR Portal-Technologie)
---

> Status: **angenommen** am 2026-11-12 nach einem ergebnisoffenen Vergleichsprototyp. Entscheidung: **Svelte 5 + Vite als reine Single-Page-App** (ohne SvelteKit), **Bits UI** für komplexe barrierefreie Bausteine, übrige Komponenten im Eigenbau nach den WAI-ARIA Authoring Practices.

## Kontext

- Auf **jedem Knoten** liefert der Rust-Agent API, Web-Portal und MCP selbst aus. Es gibt keinen zentralen Webserver; das Portal wird als **statische Assets in das Agent-Binary eingebettet** und muss auch von einem Raspberry Pi mit kleinem Speicherbudget ausgeliefert werden können.
- **Paritätsprinzip:** Jede API-Operation ist auch im Portal und im MCP verfügbar. Formulare sollen möglichst **aus dem API-Schema** (OpenAPI 3.1 / JSON Schema) abgeleitet werden, damit neue API-Funktionen ohne Handarbeit erscheinen (siehe [API-first](api-first.html)).
- **Funktionsumfang:** Ersteinrichtungs-Assistent, Knoten- und Hardware-Übersicht mit Adoption, Live-Updates, Mandanten-Self-Service (VMs, Container, Kubernetes, Volumes, Buckets, Netze), serielle Konsole und VNC, Diagramme, Deutsch/Englisch, helles und dunkles Theme sowie **Barrierefreiheit nach BITV 2.0 / WCAG 2.1 AA** für den Behördeneinsatz.
- **Sicherheit:** strikte Content Security Policy ohne Inline-Skripte und ohne `eval`, nachvollziehbare Lieferkette (SBOM). Von Mandanten oder Geräten befüllte Texte werden **nie als HTML** gerendert und sichtbar als Fremdinhalt gekennzeichnet.
- **Bestätigungsseite:** Für Out-of-band-Bestätigungen destruktiver Aktionen und der Adoption rendert die Plattform eine eigene Seite mit Auswirkungsbericht und Passkey-Bestätigung. Sie gehört zum Portal, wird aber ausschließlich von der Plattform befüllt – nie von einem KI-Client.
- Das Leitprinzip „eigene Komponenten in Rust“ gilt für die **Steuerungsebene**. Das Portal ist ein Client der API, keine Steuerungskomponente – die Sprachwahl war daher offen.

## Entscheidungstreiber

| Kriterium | Gewicht | Warum |
|---|---|---|
| Barrierefreiheit (WCAG 2.1 AA / BITV 2.0) | hoch | Pflicht für Behörden; nachträglich teuer |
| Schema-getriebene Formulare / Parität | hoch | Sonst wächst der Portal-Rückstand mit jeder API-Version |
| Komponenten-Ökosystem (Tabellen, Charts, Terminal, VNC, Dialoge) | hoch | Großer Teil der Arbeit |
| Sicherheit und Lieferkette (CSP, SBOM) | hoch | Compliance by Design, Angriffsfläche Browser |
| Reife und Langlebigkeit | hoch | Plattform soll mindestens zehn Jahre gepflegt werden |
| Pool an Beitragenden, Entwicklungstempo | mittel-hoch | Open-Source-Projekt lebt von Beiträgen |
| Typsicherheit gegenüber der API | mittel | Fehlerklasse „Client/Server-Drift“ |
| Bundle-Größe, Einbettung ins Binary | mittel | Binary-Größe, Ladezeit über langsame Links |
| Last auf Pi-Knoten | mittel | nur Auslieferung, Rendering im Browser |
| Internationalisierung, Theming | mittel | Standardanforderung |
| Testbarkeit inkl. automatischer Barrierefreiheitsprüfung | mittel | Regressionstests in der CI |

## Betrachtete Optionen

| Familie | Optionen |
|---|---|
| **A – Rust/WASM** | Leptos (clientseitig, optional mit Server-Rendering), Dioxus, Yew |
| **B – TypeScript-SPA** (statisch gebaut, vom Agenten ausgeliefert) | React, Svelte 5 (mit oder ohne SvelteKit), SolidJS, Vue 3 |
| **C – Server-Rendering in Rust** | HTMX mit serverseitigen HTML-Templates |

### Reifegrad der Rust-Frontends (Stand November 2026)

- **Leptos:** stabile Linie 0.8, Version 0.9 in der Beta mit erneuten Breaking Changes; sehr kleiner Kreis von Hauptentwicklern, kein 1.0 in Sicht. Komponentenbibliotheken vorhanden, aber ohne nachgewiesene WCAG-Konformität.
- **Dioxus:** firmengetragen, mit zugänglichen Basiskomponenten („Primitives“), aber ebenfalls vor 1.0, nächste Hauptversion mit Breaking Changes; Fokus zunehmend auf Desktop und Mobile.
- **Yew:** im Wartungsmodus; für ein Neuprojekt nicht mehr empfehlenswert.

**Fazit:** Alle Rust-Frontends sind vor 1.0 und brechen etwa jährlich ihre APIs. Für eine Plattform mit Behördenanspruch und Zehn-Jahres-Horizont ist das ein erhebliches Risiko, das sich bei den jahrelang stabilen Hauptversionen der TypeScript-Frameworks so nicht stellt.

## Bewertung

Skala: ++ sehr gut · + gut · o neutral · − schwach · −− kritisch

| Kriterium | Leptos | Dioxus | React | Svelte | Solid | Vue | HTMX |
|---|---|---|---|---|---|---|---|
| Barrierefreiheit | − | o | ++ | + | + | + | + / − bei dynamischen Widgets |
| Schema-Formulare | − | − | ++ | + | o | + | o |
| Komponenten (Charts, Terminal, VNC) | − | − | ++ | + | o | + | − |
| CSP und Lieferkette | ++ | + | o | o | o | o | ++ |
| Reife, Langlebigkeit | − | − | ++ | + | o | + | + |
| Beitragende, Tempo | − | o | ++ | + | o | + | o |
| Typsicherheit API | ++ | ++ | + | + | + | + | ++ |
| Bundle, Einbettung | o | o/− | + | ++ | ++ | + | ++ |
| Last auf dem Pi | + | + | + | + | + | + | − |
| i18n, Theming | o | o | ++ | + | o | ++ | + |
| Testbarkeit | o | o | ++ | ++ | + | ++ | + |

### Wesentliche Abwägungen

**1. Der Typsicherheitsvorteil von Rust ist kleiner, als er scheint.** Geteilte Rust-Typen sind das stärkste Argument für Leptos oder Dioxus. Da das Portal aber ohnehin aus dem OpenAPI-Schema arbeitet, ist das Schema die eigentliche Vertragsquelle. Ein bei jedem Build generierter, typsicherer TypeScript-Client plus CI-Prüfung fängt Drift ebenso zuverlässig ab. Das generische Formular-Rendering arbeitet zur Laufzeit mit JSON Schema – dort hilft Compile-Time-Typsicherheit in keiner Sprache.

**2. Die schwierigen Widgets sind JavaScript – egal welches Framework.** Terminal-Emulation (serielle Konsole), VNC, Zeitreihendiagramme und ausgereifte zugängliche Datentabellen gibt es nur im JS-Ökosystem. Rust/WASM bräuchte für jedes Brücken – und brächte npm damit trotzdem in die Lieferkette.

**3. Barrierefreiheit ist das härteste Kriterium.** BITV verlangt zugängliche Comboboxen, Dialoge mit Fokusfalle, sortierbare Tabellen, Live-Regionen für Echtzeit-Updates und vollständige Tastaturbedienung. Dafür gibt es im JS-Ökosystem geprüfte Headless-Bibliotheken; im Rust-Ökosystem nur einen jungen Ansatz ohne Audit-Historie. Eigenbau zugänglicher Widgets ist erfahrungsgemäß die teuerste und fehleranfälligste Frontend-Arbeit.

**4. Lieferkette npm vs. cargo.** npm hatte 2025 mehrere großflächige Kompromittierungen. cargo ist nicht immun, hat aber eine flachere Abhängigkeitslandschaft. **Das Risiko bei TypeScript ist real, aber beherrschbar**, weil npm-Pakete nur zur Build-Zeit laufen und nur der geprüfte, gebündelte Output in das Binary gelangt.

**5. Die Pi-Last spricht gegen Server-Rendering.** Alle SPA-Varianten liefern nur vorkomprimierte statische Dateien aus – CPU-Last nahe null. HTMX dagegen rendert jede Ansicht im Agenten und schafft eine **zweite Darstellungsschnittstelle neben der REST-API**. Die API wäre nicht mehr die einzige Wahrheit, was der Parität widerspricht. Für Konsole, VNC und Diagramme bräuchte es trotzdem JavaScript.

**6. Server-Rendering mit Hydration bringt hier keinen Nutzen.** SEO und schneller erster Seitenaufbau sind für ein authentifiziertes Admin-Portal irrelevant; es würde nur Last auf Pi-Knoten verlagern.

## Der Vergleichsprototyp

Statt die Technik vorab festzulegen, wurde ein **ergebnisoffener Vergleich** durchgeführt: Svelte und Leptos wurden an denselben, für die Barrierefreiheit kritischen Ansichten gemessen; React blieb Rückfalloption.

| Ansicht | Prüft |
|---|---|
| Knotenübersicht mit Adoption | Tabellen-Barrierefreiheit, Live-Regionen, Dialog-Fokusfalle, Live-Updates, Theme |
| „VM anlegen“ rein aus OpenAPI | Schema-Renderer, Drift-Prüfung, i18n, Formular-Barrierefreiheit |
| VM-Detail mit Konsole, VNC und Zeitreihe | Lazy Loading, strikte CSP, Tastaturbedienbarkeit, Bundle-Budgets |
| Bestätigungsseite | Passkey-Integration, strikte CSP, keine Darstellung von Fremdinhalt als HTML |

Abnahmekriterien waren unter anderem: Einhaltung der Leistungsbudgets, CSP ohne `unsafe-inline` und `unsafe-eval`, null schwerwiegende Befunde der automatischen Barrierefreiheitsprüfung plus manueller Test mit Screenreadern (NVDA, Orca) und reiner Tastatur, Schema-Änderungen erscheinen ohne Portal-Codeänderung im Formular, SBOM-Erzeugung für den Portal-Build sowie gemessene Auslieferung vom Pi.

**Ergebnis:** Die Svelte-Variante kam auf rund **28 KiB initiales JavaScript** (Brotli), lief mit einer **CSP ohne jede Ausnahme** und ohne Befunde der automatischen Barrierefreiheitsprüfung. Die Leptos-Variante war mit rund 191 KiB deutlich größer, benötigte eine CSP-Ausnahme für WebAssembly und hatte eine wesentlich längere Build-Zeit. Weil SvelteKit ein Inline-Bootstrap-Skript erzeugt, fiel die Wahl auf **reines Vite + Svelte** statt SvelteKit.

## Entscheidung

Das Portal ist eine **Svelte-5-Single-Page-App, gebaut mit Vite**, statisch gebündelt, vorkomprimiert und in das Agent-Binary eingebettet. Typsicherheit gegenüber der API entsteht durch Codegenerierung aus OpenAPI; Formulare werden zur Laufzeit aus JSON Schema mit den projekteigenen Schema-Erweiterungen gerendert.

| Baustein | Wahl |
|---|---|
| Framework | Svelte 5 + Vite, reine SPA |
| API-Client | aus OpenAPI generierte Typen + schlanker Fetch-Client |
| Zugängliche Basiskomponenten | Bits UI (headless); Eigenbau nur nach WAI-ARIA-Mustern |
| Styling, Theme | CSS Custom Properties als Design-Tokens; hell, dunkel, hoher Kontrast |
| Schema-Formulare | eigener Renderer für JSON Schema plus Erweiterungen für Widget, Reihenfolge, Übersetzungsschlüssel |
| Tabellen | headless Tabellenbibliothek |
| Diagramme | kleine Zeitreihenbibliothek, komplexe Diagramme bei Bedarf nachgeladen |
| Serielle Konsole, VNC | etablierte JS-Bibliotheken, nachgeladen |
| Live-Updates | Server-Sent Events mit Ankündigung über Live-Regionen; WebSocket nur für Konsole und VNC |
| i18n | Übersetzung zur Build-Zeit; Schlüssel aus der API mitgenutzt |
| Tests | Unit- und Komponententests, End-to-End-Tests mit automatischer Barrierefreiheitsprüfung |

**Warum Svelte statt React?** React hat das stärkste Ökosystem und bleibt Rückfalloption. Svelte gewinnt bei der Bundle-Größe – wichtig, weil jeder Knoten das Portal trägt –, hat deutlich weniger transitive npm-Abhängigkeiten, eine niedrige Einstiegshürde für Rust-Entwickler und eingebaute Barrierefreiheitswarnungen im Compiler.

**Warum nicht Leptos?** Leptos ist der ernsthafteste Rust-Kandidat, und der Vorteil geteilter Typen ist real. Dagegen sprechen der Pre-1.0-Status mit kleinem Maintainerkreis, fehlende geprüfte barrierefreie Komponenten, JS-Brücken für alle Kern-Widgets, größere Bundles und ein kleinerer Pool an Beitragenden. Die Entscheidung wird **Ende 2027 überprüft**. Ein Wechsel bleibt möglich, weil das Portal ausschließlich über die öffentliche API spricht.

### Verworfene Optionen

- **Yew:** Wartungsmodus, schwächstes Ökosystem.
- **Dioxus:** vor 1.0, Fokus auf Multi-Plattform statt Web-Admin-Oberfläche, größere Bundles.
- **Leptos mit Server-Rendering:** Last auf dem Pi, kein Nutzen für ein authentifiziertes Portal.
- **SolidJS:** technisch hervorragend, aber kleinerer Pool und weniger reife Formular- und Barrierefreiheitsbibliotheken.
- **Vue 3:** solide, aber gegenüber Svelte größere Bundles und gegenüber React kleineres Barrierefreiheits-Ökosystem.
- **HTMX mit Templates:** zweiter Render-Pfad neben der API, Last auf Knoten; allenfalls als Notfallseite ohne JavaScript denkbar.

## Konsequenzen

**Positiv:**

- Zugriff auf ausgereifte, zugängliche Komponenten – ein BITV/WCAG-Nachweis wird realistisch.
- Großer Pool an Beitragenden; Frontend-Entwickler müssen kein Rust lernen.
- Das Portal ist ein **reiner API-Client** und erzwingt damit Parität technisch: Was das Portal kann, kann auch die API.
- Kleine Bundles, keine Render-Last auf Knoten; das Portal funktioniert identisch von jedem Knoten aus.

**Aufwand und Pflichtmaßnahmen:**

- **Zweite Toolchain** im Build. Der Portal-Build läuft als eigener CI-Schritt; sein Artefakt wird versioniert in den Rust-Build eingespeist. Rust-Beitragende können mit vorgebautem Artefakt oder Platzhalter-Portal ohne Node bauen.
- **npm-Lieferkette aktiv managen:** gesperrte Abhängigkeiten, Installationsskripte standardmäßig aus, Mindestalter für neue Paketversionen gegen frisch kompromittierte Releases, begrenztes Abhängigkeitsbudget mit Review jeder neuen Abhängigkeit, SBOM für npm und cargo (die Portal-SBOM ist Teil der Agent-SBOM), Schwachstellenscans in der CI und ein reproduzierbarer Portal-Build.
- **Content Security Policy als Muss**, automatisch geprüft: nur eigene Quellen für Skripte und Verbindungen, keine Objekte, keine Einbettung in fremde Frames, kein `unsafe-inline`, kein `unsafe-eval`, keine Mandanten-HTML.
- Typen werden nicht geteilt, sondern generiert – OpenAPI ist die Quelle, Codegenerierung läuft in der CI.
- Das Binary wächst um etwa 1–3 MB. Der Agent liefert die vorkomprimierten Dateien direkt aus, ohne Komprimierung zur Laufzeit, mit Langzeit-Caching für Dateien mit Hash im Namen.

### Leistungsbudgets (verbindlich ab MVP)

| Größe | Budget |
|---|---|
| Initiales JavaScript (Brotli) | ≤ 120 KB |
| Initiales CSS (Brotli) | ≤ 30 KB |
| Nachgeladene Teile für Konsole, VNC, Diagramme | je ≤ 250 KB |
| Zeit bis zur Bedienbarkeit über eine 10-Mbit-Leitung | ≤ 2 s |
| CPU-Last des Agenten auf einem Pi 4 | vernachlässigbar |
| Schwerwiegende Barrierefreiheitsbefunde (automatisch, alle Ansichten) | 0 |

## Anmeldung und Knotenwechsel

Alle Knoten einer Region stehen hinter einem gemeinsamen regionalen DNS-Namen und damit demselben Origin. Die Sitzung läuft über ein Cookie dieses Origins (HttpOnly, Secure, SameSite=Strict, kurze Laufzeit); am Eingangsknoten wird es in kurzlebige, an die Zielzelle gebundene Tokens getauscht. Ein Wechsel zwischen Regionen ohne Neuanmeldung ist noch offen (siehe [Identität](identitaet.html)).

## Offene Punkte

- Vokabular der Schema-Erweiterungen und Abgrenzung zu handgebauten Ansichten wie Dashboard und Konsole.
- Verhalten bei gemischten Versionen während eines Rolling Updates (Feature-Erkennung, Kompatibilitätsfenster).
- Formaler BITV-Test vor einem ersten Behördenpiloten und Erklärung zur Barrierefreiheit (siehe [Compliance-Anforderungen](compliance-anforderungen.html)).
- Gegebenenfalls eine minimale Notfallseite ohne JavaScript für Status und Ersteinrichtung – als Ergänzung, nicht als zweites Portal.
- Weitere Sprachen über Deutsch und Englisch hinaus und ein Übersetzungs-Workflow.
