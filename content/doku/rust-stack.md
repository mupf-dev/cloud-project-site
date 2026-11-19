title: Rust-Stack und Kern-Bibliotheken
summary: Architekturentscheidung zu den Rust-Bibliotheken des Agenten – Runtime, APIs, Konsens, Gossip, TLS, Persistenz, Tests, Lieferkette, Toolchain und Lizenzen.
group: konzept
order: 20
quelle: Konzept 03 (ADR Rust-Stack & Kern-Crates)
---

> Status: angenommen (Review 2026-11-12). Versionsangaben spiegeln den Stand vom November 2026 wider; maßgeblich ist jeweils die gesperrte Abhängigkeitsliste des Projekts.

## Kontext

Die Implementierungssprache **Rust** steht fest. Diese Architekturentscheidung (ADR) legt fest, **welche Bibliotheken (Crates)** das Fundament des Agenten bilden. Die Wahl ist langlebig: Async-Runtime, Konsens, Gossip, Persistenz und Wire-Formate lassen sich später nur mit hohem Aufwand austauschen.

Die Randbedingungen ergeben sich aus der [Vision](vision.html):

| Anforderung | Folge für den Stack |
|---|---|
| Ein **Agent** auf jedem Knoten (vom Pi mit kleinem Speicherbudget bis zum Server) | Kleiner Speicher-Footprint, ein statisch gelinktes Binary, keine JVM- oder Python-Laufzeit |
| **Kein zentraler Controller**; Gossip für Mitgliedschaft, Raft je Zelle | Reife Raft-Bibliothek mit Membership-Changes, Learnern und Zeugen-Unterstützung; SWIM-artiges Gossip bis etwa 1.000 Knoten je Zelle |
| **API = Portal = MCP** auf jeder Ebene | Eine Quelle der Wahrheit (Rust-Typen) → OpenAPI → generierter Portal-Client und MCP-Tools |
| **ARM64 und x86_64** gemischt | Alle Abhängigkeiten müssen für beide Architekturen bauen; Cross-Compilation |
| **mTLS überall**, BSI TR-02102, C5, Cyber Resilience Act | Konfigurierbares TLS, eigene PKI, SBOM, Schwachstellenprozess |
| **Open Source durchgehend** | Nur OSI-Lizenzen; Copyleft-Risiken sichtbar machen |
| Verteilte Logik muss korrekt sein | Deterministische Simulation (Netzpartitionen, Uhren, Knotenausfälle) im CI |

## Entscheidung im Überblick

| Bereich | Entscheidung | Fallback / Alternative |
|---|---|---|
| Async-Runtime | **tokio** | – (De-facto-Standard) |
| HTTP/REST | **axum** mit tower, tower-http, hyper | – |
| gRPC intern | **tonic** + **prost** | – |
| Konsens | **openraft** | raft-rs |
| Gossip / Mitgliedschaft | **foca** (SWIM mit Lifeguard-Ideen, I/O-frei) | chitchat (Scuttlebutt) |
| TLS / mTLS | **rustls** mit **aws-lc-rs** als einzigem Kryptoprovider | – (`ring` und OpenSSL ausgeschlossen) |
| Zertifikate | **rcgen** (Erzeugung), **x509-parser** (Prüfung) | x509-cert |
| OpenAPI | **utoipa** (OpenAPI 3.1) | aide |
| JSON-Schema | **schemars** | – |
| MCP-SDK | **rmcp** (offizielles SDK) | – |
| Lokale Persistenz | **redb** (Raft-Log, Zustandsmaschine, Key-Value) | SQLite für relationale Hilfsdaten |
| Serialisierung | **serde**, serde_json, toml; **prost** für die Leitung; **postcard** für kompakte interne Daten | – |
| Netlink / WireGuard | **rtnetlink**; WireGuard über **defguard_wireguard_rs** (Kernel-WireGuard) | wireguard-uapi |
| Observability | **tracing** + **OpenTelemetry** (OTLP) | – |
| Fehlerbehandlung | **thiserror** in Bibliotheken, **anyhow** nur in Binaries/Tests | snafu |
| Konfiguration | Eigene schlanke Schicht aus serde + toml + Umgebungsvariablen | figment, config |
| CLI | **clap** (derive) mit Shell-Completions | – |
| Tests | **proptest**, **insta**, **cargo-nextest**, **turmoil** + Raft-Simulator, **loom** | madsim |
| Lieferkette | **cargo-deny**, **cargo-audit**, **cargo-auditable**, **cargo-cyclonedx**, optional **cargo-vet** | – |
| Cross-Build | **cargo-zigbuild** bzw. musl-Ziele | cross |

## Begründung je Bereich

### Runtime, REST und gRPC

**tokio** ist der Ökosystem-Standard; axum, tonic, rmcp, openraft und turmoil bauen darauf auf. Auf Pi-Knoten wird die Zahl der Worker-Threads begrenzt. io_uring-basierte Runtimes (thread-per-core) sind für einen späteren Speicher-Datenpfad interessant, nicht für die Steuerungsebene.

**axum** ist tower-basiert und teilt sich die Middleware mit tonic. Es integriert sich am besten mit utoipa und mit dem MCP-SDK, dessen Streamable-HTTP-Server selbst ein tower-Service ist. actix-web bringt eine eigene Runtime-Schicht mit; dropshot (Oxide) ist als Vorbild für „API-first mit OpenAPI-Generierung“ lehrreich, hat aber ein kleineres Ökosystem.

**tonic** wird für die Kommunikation Knoten ↔ Knoten verwendet: Raft-Transport, Weiterleitung von Anfragen an die Steuerungsgruppe, Rollen-Agenten. Protobuf-Schemas sind sprachneutral und versionierbar. **gRPC ist kein öffentlicher Vertrag** – nach außen bleibt REST/JSON (siehe [API-first](api-first.html)).

### Konsens: openraft

| Kriterium | openraft | raft-rs |
|---|---|---|
| Architektur | Async, ereignisgetrieben, Traits für Speicher und Netz, deterministischer Simulator | Nur Kern-Zustandsmaschine, synchron, Log/Netz selbst mitbringen |
| Funktionen | Joint Consensus, Learner, Leader-Transfer, Pre-Vote, Lease-Reads, Snapshot-Streaming | ausgereift, aber ohne I/O |
| Wartung | sehr aktiv | kaum noch Releases |

openraft ist tokio-nativ, bringt viele Bausteine fertig mit (Membership, Learner als Vorstufe des Zeugen, Snapshots, konfigurierbare Quorum-Regeln) und enthält einen deterministischen Simulator. **Risiko:** Die gewählte Hauptversion war bei der Entscheidung brandneu, und 0.x-Versionen brechen APIs. Gegenmaßnahme: Raft wird hinter einer eigenen Konsens-Crate gekapselt, die Version gepinnt und vor jedem Upgrade mit Jepsen-artigen Simulationstests geprüft. Wie der Zeuge im 2-Knoten-Betrieb umgesetzt wird, beschreibt die Seite [Steuerungsebene](steuerungsebene.html).

### Gossip: foca

foca implementiert SWIM mit Teilen von Lifeguard und Inkarnationsnummern, ist **I/O-frei** und damit ideal für deterministische Simulation. Der Transport läuft über das authentisierte WireGuard-Underlay. Das passt zum Grundsatz „Gossip nur für Mitgliedschaft, Raft für Zustand“. Das Bootstrapping vor dem Underlay (Discovery, Adoption) läuft bewusst nicht über Gossip, sondern über Boot-Dienst und Adoptions-API. chitchat bleibt Fallback, falls Knoten-Metadaten als replizierter Key-Value-Zustand per Gossip verteilt werden sollen.

### TLS, mTLS und PKI

**rustls** ist speichersicher, unterstützt TLS 1.3 und hybriden Post-Quanten-Schlüsselaustausch. **aws-lc-rs ist der einzige zulässige Kryptoprovider**; `ring` (kein PQ-Schlüsselaustausch, doppelte Pflege) und OpenSSL (C-Abhängigkeit) sind per Lieferkettenprüfung verboten. **rcgen** erzeugt die interne PKI: Zellen-CA, Knotenzertifikate bei der Adoption, kurze Laufzeiten, automatische Rotation. Private Schlüssel werden nach Gebrauch genullt; eine TPM-Anbindung folgt später.

Der Abgleich mit BSI TR-02102 ist erledigt: TLS 1.3 only, bevorzugt hybride Schlüsseleinigung mit ML-KEM, secp-Kurven zulässig (Brainpool ist in rustls/aws-lc-rs nicht verfügbar, was TR-02102 ausdrücklich erlaubt). Algorithmen werden nie fest im Code gewählt, sondern über das aktive Kryptoprofil (siehe [Kryptografie](kryptografie.html)).

### OpenAPI und MCP

**utoipa** erzeugt OpenAPI 3.1 aus Attributen an Handlern und Typen. Damit Spezifikation und Code nicht auseinanderlaufen, wird die generierte Spezifikation eingecheckt und per Snapshot-Test verglichen; Breaking Changes werden automatisch erkannt. Die generierte OpenAPI-Datei ist Quelle für Portal-Client und MCP-Tool-Katalog.

**rmcp** ist das offizielle MCP-SDK mit den Transporten stdio und Streamable HTTP. Der MCP-Server läuft im Agenten unter demselben HTTP-Server, mit derselben Authentifizierung und Autorisierung wie die REST-API. **MCP-Tools werden nicht handgeschrieben**, sondern aus der OpenAPI-Beschreibung generiert – sonst ist die Parität nicht haltbar. Wegen der hohen Release-Frequenz wird die Version gepinnt und quartalsweise aktualisiert.

### Persistenz und Serialisierung

**redb** dient für Raft-Log, Raft-Zustandsmaschine (Sollzustand der Ressourcen einer Zelle) und lokalen Knotenzustand: reines Rust, ACID, crash-sicher, einfach. SQLite ist zusätzlich für lokale relationale Hilfsdaten zulässig (z. B. Audit-Puffer, Inventarhistorie). sled ist wegen Entwicklungsstillstand ausgeschlossen.

Raft-Log-Einträge überleben Software-Upgrades, daher wird ein evolvierbares Format (Protobuf) bevorzugt. Konfigurationsdateien nutzen TOML; YAML-Bibliotheken für Rust sind derzeit unklar gewartet. bincode ist eingestellt und wird nicht verwendet.

### Netz, Observability, Fehler, Konfiguration, CLI

- **Netz:** rtnetlink für Links, Adressen, Routen und Bridges; defguard_wireguard_rs für das Underlay (Kernel-WireGuard ist im [OS-Image](os-image.html) enthalten). Alles hinter einer Trait-Abstraktion, damit Tests ohne Root-Rechte laufen. Die Overlay-Technik ist nicht Teil dieser Entscheidung (siehe [Netzwerk](netzwerk.html)). Eine LGPL-lizenzierte WireGuard-Bibliothek wurde wegen des Relinkbarkeitsproblems ausgeschlossen.
- **Observability:** `tracing` als einzige Instrumentierungs-API, Export per OpenTelemetry/OTLP. Das **Audit-Log ist getrennt** davon: eigenes, append-only, signiertes Format.
- **Fehler:** typisierte Fehler in allen Bibliotheken; Abbildung auf API-Fehler im Format RFC 9457 an genau einer Stelle.
- **Konfiguration:** Der Agent hat bewusst **wenig lokale Konfiguration** – der Großteil kommt als Sollzustand über API und Raft. Lokal nötig sind nur Bootstrap-Werte. Reihenfolge: Defaults → Konfigurationsdatei → Umgebungsvariablen → Kommandozeile; unbekannte Schlüssel werden abgelehnt.
- **CLI:** Zwei Binaries – der Agent `cp-agent` (Unterbefehle für Betrieb, Bootstrap, Diagnose) und das Nutzer-CLI `cpctl`, das **ausschließlich die öffentliche REST-API** nutzt, über einen aus OpenAPI generierten Client.

### Tests und deterministische Simulation

Verteilte Logik – Gossip-Ereignisse, Raft-Integration, Reconciler, Adoptionsablauf – wird so geschnitten, dass **Uhr, Zufall und Netz injiziert** werden. So läuft eine ganze Zelle unter turmoil mit fester Saat in einem Prozess. Jede gefundene Fehlersaat wird als Regressionstest eingecheckt. Ergänzend: eigenschaftsbasierte Tests (Reconciler, Kontingente, IP-Vergabe), Snapshot-Tests (OpenAPI-Spezifikation, MCP-Katalog, Fehlermeldungen) und erschöpfende Nebenläufigkeitstests.

**Pflicht** sind außerdem Fuzzing für jeden Parser an einer Vertrauensgrenze (Netboot- und Discovery-Anfragen, Zertifikate, API-/MCP-Eingaben, gRPC, Metadaten) mit nächtlichem Lauf und ein Verbot von `unsafe`-Code als Crate-Standard; Ausnahmen werden begründet und registriert.

### Lieferkette und Cyber Resilience Act

| Werkzeug | Zweck | Zeitpunkt |
|---|---|---|
| cargo-deny | Lizenz-Whitelist, verbotene Crates, erlaubte C-Bindings, Quellen, Advisories | jeder Pull-Request |
| cargo-audit | RustSec-Advisories, auch gegen ausgelieferte Binaries | jeder Pull-Request und täglich |
| cargo-auditable | Abhängigkeitsliste ins Binary einbetten | jeder Release-Build |
| cargo-cyclonedx | SBOM (CycloneDX) je Binary | jedes Release |
| cargo-vet | Audits von Abhängigkeiten | ab öffentlichen Releases |
| cargo-semver-checks | API-Kompatibilität veröffentlichter Bibliotheken | Release |

Zusätzlich: gesperrte Abhängigkeiten, reproduzierbare Builds, signierte Artefakte, Update-Metadaten nach dem TUF-Muster und angestrebte SLSA-Provenienz (siehe [Release-Signatur](release-signatur.html) und [Schwachstellenmanagement](schwachstellenmanagement.html)).

## Workspace-Struktur

Der Workspace trennt Binaries (Agent, Nutzer-CLI, Simulationsumgebung) von Bibliotheks-Crates mit klarer Verantwortung: Ressourcenmodell und Typen, REST-API, MCP-Server, generierter Client, interner RPC, Konsens, Mitgliedschaft, Speicherschicht, PKI, Netz, Reconciler-Framework, Rollen, Audit-Log, Telemetrie, Konfiguration und Testhilfen.

Leitlinien:

- **Ein Agent-Binary für alle Rollen** – ein Image, ein Update-Pfad. Rollen sind Laufzeitmodule und lassen sich für Minimal-Builds (z. B. reiner Zeuge auf einem Pi Zero 2 W) abschalten.
- **Strikte Schichtung:** Das Typen-Crate hängt von nichts Projektinternem ab; Rollen kennen nur Schnittstellen, nicht die Konsens- oder Gossip-Bibliothek direkt.
- **Externe Komponenten nur über Prozessgrenze:** Cloud Hypervisor, k3s, Garage und ein optionaler Ceph-Treiber werden als Prozesse über API/CLI gesteuert, nie als Bibliothek eingebunden. Jeder solche Prozess läuft mit eigenem Benutzer, minimalen Capabilities, systemd-Sandboxing, seccomp/Landlock und eigener Dienstidentität. Das verhindert Lizenzvermischung und schafft saubere Update-Grenzen.

## Edition, MSRV und Toolchain-Politik

- **Edition 2024** für alle Crates.
- **Build-Toolchain gepinnt**; Anhebung bewusst per Änderungsantrag, höchstens alle sechs Wochen und frühestens zwei Wochen nach einem Stable-Release.
- **MSRV 1.95** zum Start, getrieben durch die WireGuard-Bibliothek. Danach gilt: MSRV höchstens „Stable minus vier Releases“ (etwa sechs Monate), geprüft per CI; MSRV-bewusste Abhängigkeitsauflösung ist aktiv.
- Die MSRV ist vor allem ein Signal an Paketierer; ausgeliefert werden ohnehin eigene Binaries.

## Cross-Compilation ARM64/AMD64

Ziele sind Linux auf `aarch64` und `x86_64` (glibc), für den Agenten im unveränderlichen OS optional vollständig statisch mit musl.

| Werkzeug | Bewertung |
|---|---|
| **cargo-zigbuild** | Zig als Linker/C-Compiler, glibc-Version wählbar, kein Container nötig – primäre Wahl |
| cross | Container-basiert, robust für exotische C-Abhängigkeiten – nur Fallback |
| Native Builds | auf ARM64- bzw. x86-Runnern in der CI |

Simulationstests sind architekturunabhängig; Netlink- und KVM-Integrationstests laufen auf echter Hardware (Pi 4/5, x86-Knoten). C-Abhängigkeiten werden minimiert und über eine Allowlist kontrolliert.

Das Release-Profil setzt auf maximale Optimierung mit Link-Time-Optimization, Überlaufprüfungen auch im Release und Abbruch bei Panic: Ein Panic soll den Agenten über systemd neu starten statt ihn halb defekt weiterlaufen zu lassen. Für Zeugen- und Pi-Zero-Builds gibt es ein größenoptimiertes Profil.

## Lizenzkompatibilität der Abhängigkeiten

Die Projektlizenz selbst wird in der [Lizenz-Governance](lizenz-governance.html) entschieden. Hier die Risiken des gewählten Stacks:

| Lizenzklasse | Betroffene | Risiko | Maßnahme |
|---|---|---|---|
| MIT / Apache-2.0 / ISC / BSD | Großteil des Stacks | gering; Apache-2.0 ist mit GPL-2.0-only inkompatibel | NOTICE-Dateien je Release sammeln |
| MPL-2.0 (schwaches, dateibezogenes Copyleft) | foca u. a. | Änderungen an deren Dateien müssen offengelegt werden | unverändert nutzen, Patches upstream, explizit erlauben |
| LGPL | eine WireGuard-Bibliothek | Relinkbarkeit bei statischem Linken kaum erfüllbar | ausgeschlossen |
| AGPL (extern) | Garage | nur über Prozessgrenze → keine abgeleitete Arbeit; Quellangebot bei Auslieferung im Image | nie als Bibliothek; Quellangebot im Release-Prozess |
| C-Bibliotheken | aws-lc, SQLite | unkritisch, Lizenztexte mitliefern | Lizenzbericht je Release |
| Unmaintained | sled, bincode, YAML-Bibliothek, figment | fehlende Sicherheitsupdates (CRA) | als verboten geführt |

## Begründung der Gesamtentscheidung

1. **Ökosystem-Kohärenz:** tokio, tower und hyper verbinden REST, gRPC, MCP, Raft und Simulation – eine Runtime, eine Middleware-Welt, ein TLS-Stack.
2. **Beweisbare Korrektheit ohne zentrale Komponente:** Konsens und Gossip sind I/O-entkoppelt bzw. bringen Simulatoren mit. Das ist Voraussetzung für die Zusagen „2 Knoten + Zeuge übersteht Ausfall“ und „kein Single Point of Failure ab 3 Knoten“.
3. **Pi-tauglich:** Reines Rust bei Persistenz, Gossip und Konsens, wenige C-Abhängigkeiten, ein statisches Binary.
4. **API-first technisch abgesichert:** OpenAPI entsteht aus denselben Typen, aus denen Portal-Client und MCP-Tools generiert werden.
5. **Compliance:** speichersicheres TLS, interne PKI, SBOM, Advisory- und Lizenzprüfung liefern Nachweise für CRA und C5 automatisch.
6. **Wartungsstand:** Alle gewählten Bibliotheken waren 2026 aktiv; die ausgeschlossenen sind faktisch unmaintained.

## Konsequenzen

**Positiv:** ein Binary, eine Runtime, ein TLS-Stack; Cross-Build beider Architekturen ohne Container; deterministische Simulation von Anfang an; SBOM-, Lizenz- und Advisory-Prüfung in jedem Build.

**Negativ / Risiken:**

- Mehrere Kernabhängigkeiten sind noch 0.x und brechen regelmäßig APIs → Kapselung in eigenen Crates, zentrale Versionspflege, feste Upgrade-Fenster.
- Gossip-Sicherheit hängt am Underlay; vor dessen Aufbau gibt es kein Gossip, der Bootstrap-Pfad muss ohne auskommen.
- Die MSRV schließt ältere Distributions-Toolchains aus (unkritisch, da eigene Toolchain).
- Das schnelle Release-Tempo des MCP-SDK und der MCP-Spezifikation erfordert laufende Pflege.
- Release-Builds mit voller Link-Time-Optimization sind langsam; Entwicklungs-Builds bleiben schnell.

## Offene Punkte zum Entscheidungszeitpunkt

- Umsetzung des Zeugen in openraft (voller Voter mit Log oder log-loser Zeuge) – geklärt im Konzept [Steuerungsebene](steuerungsebene.html).
- foca oder chitchat endgültig – abhängig davon, ob SWIM-Broadcasts für Knoten-Metadaten genügen; Lasttest mit 1.000 simulierten Knoten.
- Allokator für musl-Builds (mimalloc oder jemalloc).
