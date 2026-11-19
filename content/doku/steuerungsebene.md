title: Architektur der Steuerungsebene
summary: Agent, Gossip-Mitgliedschaft (SWIM), Raft-Konsens je Zelle, Zwei-Knoten-Betrieb mit Zeuge, Zellen und Regionen, Reconciler, Bootstrap und Ausfallverhalten.
group: konzept
order: 40
quelle: Konzept 05 (Architektur der Steuerungsebene)
---

Die Steuerungsebene ist das Herz von BYOC: Sie hält den gewünschten Zustand aller Ressourcen, entscheidet über Platzierung und Mitgliedschaft und setzt beides auf den Knoten um – **ohne zentralen Controller**. Begriffe wie Knoten, Zelle, Steuerungsgruppe und Zeuge sind in der [Vision](vision.html) erklärt; die gewählten Bibliotheken im [Rust-Stack](rust-stack.html).

## Kernentscheidungen

| # | Entscheidung |
|---|---|
| 1 | **Ein Agent-Prozess je Knoten**, Rollen als Laufzeitmodule. Externe Komponenten (Cloud Hypervisor, Garage, k3s …) laufen als eigene systemd-Units, vom Agenten gesteuert. |
| 2 | **Zwei Ebenen der Wahrheit:** *Raft* (je Zelle) für gewünschten Zustand, Zuweisungen, Leases und relevante Statusübergänge; *Gossip* (SWIM, je Zelle) für Mitgliedschaft, Erreichbarkeit und schnelllebige Metadaten. **Gossip löst nie allein eine destruktive Aktion aus.** |
| 3 | **Steuerungsgruppe wird automatisch gewählt:** 1 → 2 Daten-Knoten + Zeuge → 3 → 5 Voter, nie 7. Neue Mitglieder starten immer als **Learner**; höchstens eine Mitgliedschaftsänderung gleichzeitig. |
| 4 | Der **Zeuge ist ein vollwertiger, aber leichter Voter**, der nie Leader wird. Standard ist der **Blind-Zeuge**, der statt Nutzdaten nur Hashes erhält. |
| 5 | **1-Knoten-Restbetrieb ist nur lesend.** Schreiben wieder erst mit Quorum – oder per lokalem Notfall-Override mit Wiederherstellungsschlüssel und Audit, nie automatisch. |
| 6 | **Zellen-Richtwert ≤ 1.000 Knoten** (Warnschwelle 500; mit Pi-Steuerungsknoten ≤ 100). Regionsdaten liegen in einer eigenen kleinen Raft-Gruppe, die bei nur einer Zelle in die Zellgruppe „kollabiert“. |
| 7 | **Routing per URN:** Region aus der URN, Zelle aus einer versionierten Shard-Karte. |
| 8 | **Reconciler sind level-getrieben, idempotent und gefenct:** Zellen-Controller laufen als Shards mit Leases in Raft; veraltete Schreibzugriffe werden verworfen. |
| 9 | **Statische Stabilität:** Ein Ausfall der Steuerungsebene stoppt keine laufenden Workloads. |

## Der Agent

### Prozessmodell

- **Ein Binary, ein Hauptprozess**, gestartet und überwacht von systemd (Watchdog, automatischer Neustart). Bei einem Panic startet der Agent neu, statt halb defekt weiterzulaufen.
- Raft und Gossip laufen in einer **eigenen, hoch priorisierten Runtime**, damit API-Last (Portal, Watch-Ströme, MCP) Heartbeats und Wahlen nicht verzögert.
- **Rollen** sind Module im selben Prozess und werden per Sollzustand aktiviert. Ausnahme: Der Boot- und Discovery-Dienst läuft als eigener Sandbox-Prozess ohne Zugriff auf den Knotenschlüssel; allgemein laufen Parser an Vertrauensgrenzen ohne diesen Zugriff.
- **Externe Komponenten** laufen nicht als Kindprozesse, sondern als eigenständige systemd-Units mit eigener cgroup und Ressourcenlimits. Ein Agent-Neustart (Update, Absturz) beendet daher keine Workloads.
- Privilegierte Operationen sollen in einem kleinen Hilfsdienst mit festem Befehlssatz gebündelt werden, damit der Hauptprozess mit reduzierten Rechten läuft.

### Komponenten

Jeder Agent enthält Supervisor, Identität und PKI, WireGuard-Underlay, Gossip-Mitgliedschaft, API-Eingang mit Router, RPC-Server, Knoten-Reconciler, Audit, Zeitüberwachung und Update-Steuerung. Nur auf Mitgliedern der Steuerungsgruppe, Learnern und Zeugen läuft zusätzlich der Raft-Konsens; einen **vollständigen Watch-Cache** halten nur Steuerungsknoten und Learner – Arbeitsknoten cachen ausschließlich eigene Objekte und sehen so keine fremden Mandantendaten. Zellen-Controller laufen auf Knoten, die dafür eine Lease halten.

### Ressourcenbudgets

Zielbudgets auf einem Pi 4: Arbeitsknoten ≤ 96 MB RAM, Steuerungsknoten ≤ 384 MB (mit **SSD/NVMe als Pflicht**, keine SD-Karte), Zeuge ≤ 48 MB (SD-Karte zulässig). Ein Pi 4 mit 2 GB darf damit Steuerungsknoten sein; mit 1 GB nur Arbeits- oder Zeugenknoten.

## Mitgliedschaft per Gossip

Gossip folgt dem SWIM-Protokoll mit Lifeguard-Erweiterungen. **Gossip-Bereich ist die Zelle**; zusätzlich gibt es einen kleinen Regions-Pool aus den Steuerungsknoten aller Zellen. Einen regionsweiten Pool aller Knoten gibt es nicht.

### Beitritt

| Phase | Mechanismus |
|---|---|
| Vor der Adoption | **Kein Gossip.** Entdeckung über Boot-Dienst und Discovery-API; unbekannte Hardware sieht keine Gossip-Pakete. |
| Adoption | Das Adoptionspaket enthält ein einmaliges Provisionierungs-Credential, die WireGuard-Konfiguration für mindestens drei Seed-Knoten und die Zell-ID. Der Knoten erzeugt seinen Schlüssel selbst und erhält sein Zertifikat per CSR. |
| Beitritt | Underlay zu den Seeds, Gossip-Schlüssel über mTLS, Ankündigung an mehrere Seeds – danach sind alle Mitglieder bekannt. |
| Neustart | Neue Inkarnation bei gleicher Knoten-ID; Seeds aus dem lokalen Cache. |

Details zum Adoptionsablauf: [Boot & Adoption](boot-adoption.html).

### Fehlererkennung

Ein Knoten wird direkt, dann indirekt über mehrere andere Mitglieder angepingt, dann als **verdächtig** und schließlich als **ausgefallen** geführt. Lifeguard reduziert Fehlalarme durch überlastete Knoten – wichtig für Pis unter Last. Die Erkennung dauert etwa 5–15 Sekunden. Entscheidend: **„Ausgefallen“ per Gossip ist nur ein Signal, keine Entscheidung.**

| Signal | Folge |
|---|---|
| verdächtig | nur Anzeige; Router meidet den Knoten für eventuelle Lesezugriffe |
| ausgefallen < 5 Min. | Knoten wird als nicht erreichbar markiert – erst nach eigenem Health-Check des Controllers |
| ausgefallen ≥ 5 Min. und Voter | Umbesetzung der Steuerungsgruppe |
| ausgefallen ≥ 10 Min. | Neuplatzierung nur für Workloads ohne lokalen Zustand bzw. mit replizierten Volumes – vorher Fencing |

### Metadaten

Gossip trägt nur **kleine, schnelllebige, verlustverträgliche** Informationen: Underlay-Endpunkte, Ist-Rollen, Agent-Version, grobe freie Kapazität, Gesundheits-Flags, Leader-Hinweis und Uhrversatz – höchstens 512 Byte je Knoten, vom Ursprungsknoten signiert. Ein periodischer Digest-Abgleich mit zufälligen Peers gleicht verlorene Nachrichten aus. Alles, was korrekt sein muss, liegt in Raft.

### Skalierung und Partition

Gossip skaliert erfahrungsgemäß auf mehrere tausend Knoten je Pool und begrenzt die Zellgröße nicht. Bei einer Netzpartition kann nur die Seite mit **Raft-Quorum** umbesetzen, fencen und neu platzieren; die Minderheit wird lesend, Workloads laufen weiter. Eine **Massenausfall-Bremse** greift, wenn mehr als ein Drittel der Zellknoten binnen 60 Sekunden wegfällt: Dann wird ein Netz- oder Stromereignis angenommen – keine automatische Umbesetzung, keine Evakuierung, Alarm an den Betreiber.

## Zustand: Raft-Gruppe je Zelle

Jede Zelle hat eine eigene Raft-Gruppe; Log und Zustand werden lokal crash-sicher gespeichert. Verliert ein Voter seine Daten, tritt er mit einer **neuen Raft-Inkarnation** als neues Mitglied bei – so kann kein „Amnesie-Voter“ mit alter Identität abstimmen.

### Automatische Wahl der Steuerungsgruppe

Der Steuerungsgruppen-Controller läuft immer auf dem Raft-Leader.

**Harte Kriterien:** mindestens 2 GB RAM (Zeuge 512 MB); SSD/NVMe mit gemessener niedriger fsync-Latenz; Lebenszyklus *Aktiv*; passende Agent-Version; kabelgebundenes Netz und geringer Zeitversatz; Mindest-Vertrauensstufe gemäß Betriebsprofil; Mindestbetriebszeit. Eignungsdaten stammen **ausschließlich** aus Messungen des Controllers und aus Betreiber-Labels – ein Knoten kann sich nicht selbst „geeignet“ melden.

**Weiche Kriterien**, gewichtet:

1. **Streuung über Ausfallzonen** (Standort, Raum, Rack, Stromkreis, Switch): Keine einzelne Zone darf eine Mehrheit der Voter halten.
2. **Stabilität** (Verfügbarkeit, Flattern, Akkubetrieb).
3. **Hardware-Güte** (fsync-Latenz, RAM, CPU-Klasse).
4. **Netzlatenz** zu den übrigen Votern.
5. **Last** – Steuerung und schwere Workloads werden entzerrt.

Geändert wird nur bei deutlicher Verbesserung (Hysterese), damit keine Dauer-Umbesetzung entsteht.

| Geeignete Knoten | Voter | Learner |
|---|---|---|
| 1 | 1 | – |
| 2 ohne Zeuge | 1 | 1 (Hot Standby) |
| 2 + Zeuge | 2 Daten-Voter + Zeuge | – |
| 3–20 | 3 | 0–1 |
| > 20 oder ≥ 3 Ausfallzonen | 5 | 1–2 |

Fünf Voter überstehen zwei gleichzeitige Ausfälle; sieben würden Latenz und Replikationslast erhöhen, ohne für das Ausfallmodell nötig zu sein. Zwei Daten-Voter **ohne** Zeuge werden nie gebildet, weil jeder Einzelausfall die Zelle blockieren würde.

### Umbesetzung bei Ausfall

1. Gossip meldet einen Voter seit fünf Minuten als ausgefallen.
2. Der Leader bestätigt per direktem Health-Check, prüft die Massenausfall-Bremse und die Stabilität des Quorums und wählt einen Kandidaten – bevorzugt aus derselben Ausfallzone.
3. Der Kandidat wird als Learner aufgenommen und holt per Snapshot und Log auf.
4. Per Joint Consensus wird in einem Schritt die neue Mitgliedschaft festgeschrieben.

Kehrt der alte Voter zurück, wird er regulärer Knoten und kann später wieder gewählt werden.

### Was liegt in Raft – was nicht?

| Daten | Ort |
|---|---|
| Sollzustand und Metadaten aller Ressourcen der Zelle | Raft |
| Phasen- und Condition-Übergänge, Platzierung, zugewiesene IPs | Raft (zusammengefasst) |
| Controller-Leases, Fencing-Epochen, Zuweisungen, Kontingentverbrauch | Raft |
| WireGuard-Schlüssel, Zertifikatsseriennummern, Widerrufsliste | Raft |
| Audit-Einträge zu Mutationen, lang laufende Operationen | Raft |
| Erreichbarkeit, Knoten-Metadaten | Gossip |
| Metriken, Logs, Traces | Observability-Rolle, nicht in der Steuerungsebene |
| Events (menschenlesbare Historie) | lokal + Aggregation, Verlust erlaubt |

**Leitregel:** Was eine Entscheidung begründet (Platzierung, Fencing, Rechte, Kontingent), steht in Raft. Was nur beobachtet wird oder sich öfter als etwa einmal pro Minute ändert, nicht.

Der Zustand wächst von etwa 4 MB im Homelab auf knapp 1 GB bei 1.000 Knoten; Snapshots werden komprimiert, hashgeprüft und im Hintergrund erzeugt.

## Zwei-Knoten-Betrieb mit Zeuge

### Ausgangslage

Die verwendete Raft-Bibliothek kennt nur Voter und Learner, keinen „log-losen“ Zeugen. Ein Voter ganz ohne Log wäre nur mit einer Änderung des Konsensalgorithmus möglich. Deshalb ist der Zeuge ein **vollwertiger Voter mit Einschränkungen**: Er darf nie Kandidat oder Leader werden, wendet keine Einträge an (Null-Zustandsmaschine) und erhält nur Metadaten-Snapshots.

### Varianten

| Variante | Beschreibung | Bewertung |
|---|---|---|
| A – Log-Zeuge | erhält das vollständige Log, wendet es aber nicht an | nur lokal und nur auf vertrauenswürdiger Hardware |
| **B – Blind-Zeuge** | wie A, aber jede Nutzlast wird vor dem Senden durch ihren SHA-256-Hash ersetzt | **Standard für alle Zeugen**, lokal und extern |
| C – Zeuge darf kurz führen | um einen zurückliegenden Daten-Knoten nachzuziehen | nach dem MVP zu prüfen |
| D – log-loser Arbiter | eigene Konsenserweiterung | abgelehnt (Korrektheitsrisiko) |
| E – kein Zeuge | 1 Voter + 1 Learner | Übergangsmodus |

**Warum das sicher ist:** Raft-Sicherheit hängt an Stimme, Log-IDs und persistierter Bestätigung – nicht an der Anwendung der Einträge. Der Zeuge persistiert Log-IDs (bzw. Hashes), stimmt korrekt ab, wird nie Leader und dient nie als Replikations- oder Lesequelle.

**Commit-Regel (entschieden am 2026-11-12):** Solange beide Daten-Knoten gesund sind, wird ein Schreibvorgang dem Client erst bestätigt, wenn **beide** Daten-Knoten ihn haben. Nur nach erkanntem Ausfall eines Daten-Knotens wird ein ausdrücklich ausgerufener, alarmierter und auditierter **Degraded-Modus** mit Zeugenstimme aktiv; die Rückkehr erfolgt automatisch. Im erhöhten Betriebsprofil und bei fremdbetriebenen Zeugen gilt „immer beide“.

**Bewusst akzeptierte Grenze:** Fällt der Daten-Knoten mit dem neuesten Stand dauerhaft aus, kann der Zeuge den anderen nicht nachziehen – die Zelle bleibt schreibgesperrt, bis der Knoten zurückkehrt oder ein Notfall-Override erfolgt.

### Zeuge als Hardware oder extern

Als Zeuge taugt ein Pi Zero 2 W, Pi 3 oder ein anderer Kleinstknoten per Bootstick – möglichst in einer getrennten Ausfallzone –, ein externer Zeuge über WireGuard (z. B. ein VPS oder ein zweites Homelab, mit an die Latenz angepassten Wahl-Timeouts) oder ein Container auf fremder Hardware wie einem NAS. Ein Zeuge kann mehreren Zellen dienen. Ein **geteilter externer Zeuge ist nur als Blind-Zeuge und nur bei einem vertrauenswürdigen Betreiber zulässig**, weil Raft nicht gegen bösartige Teilnehmer schützt.

### Restbetrieb mit einem Knoten

| Lage (Daten-Knoten A, B, Zeuge W) | Verhalten |
|---|---|
| B fällt aus | voll schreibend, Warnung „keine Redundanz“ |
| W fällt aus | voll schreibend, Warnung „Zeuge fehlt“ |
| B und W fallen aus | **nur lesend**; Workloads auf A laufen weiter; Knoten lokal bedienbar |
| Partition A ∣ B+W | B-Seite schreibt, A wird lesend und holt nach der Heilung auf |

Der **Notfall-Override** ist nur lokal auf dem überlebenden Knoten aufrufbar, mit dem bei der Ersteinrichtung erzeugten Wiederherstellungsschlüssel bzw. nach dem Vier-Augen-Prinzip. Ein Dry-Run zeigt die mögliche Verlustspanne; der Betreiber bestätigt, dass die anderen Mitglieder abgeschaltet sind. Der Knoten startet dann mit einer **neuen Zellen-Epoche** als Einzelvoter; alte Mitglieder werden über die Epoche ausgesperrt und müssen neu beitreten. Es gibt **keinen automatischen Override**, auch nicht nach Zeitablauf: Ein Split-Brain mit doppelt vergebenen IPs oder doppelt gestarteten VMs ist schlimmer als eine Schreibsperre.

## Zellen und Regionen

### Zellgröße

Richtwert ist **≤ 1.000 Knoten je Zelle**. Begrenzend sind die Raft-Schreiblast (ein Leader verarbeitet seriell), die Snapshot-Größe, der Watch-Fan-out und vor allem der **Ausfallradius**: Eine Zelle ist die Einheit, die durch Softwarefehler oder fehlerhafte Rollouts ausfallen kann. Kleinere Zellen bedeuten zudem feinere Rollout-Stufen.

### Wachstum

Standard ist **„Füllen statt Spalten“**: Erreicht eine Zelle die Warnschwelle, wird eine neue angelegt, und neue Knoten und Projekte werden dorthin gelenkt. Echtes Spalten ist die Ausnahme: Projekte werden einzeln per koordinierter Übergabe verschoben (Schreibsperre je Projekt nur Sekunden), Knoten behalten dabei ihre URN.

### Regions-Ebene

Regionsweite Daten liegen in einer **eigenen Regions-Raft-Gruppe** statt in einem föderierten Verzeichnis – wegen starker Konsistenz bei Shard-Karte, eindeutigen Namen und zellübergreifenden Kontingenten. Ihre Voter stammen aus verschiedenen Zellen. Sie enthält Zellverzeichnis, Shard-Karte (Projekt → Heimatzelle), regionale IP-Pools, Regions-CA, Image-Katalog sowie Mandantenverzeichnis und Identität.

Bei **genau einer Zelle** gibt es keine zweite Raft-Instanz; die Regionsdaten liegen in einem eigenen Schlüsselraum der Zellgruppe. Fällt die Regions-Gruppe aus, arbeiten die Zellen mit gecachter Shard-Karte und Identität weiter; nur zellübergreifende Operationen scheitern.

### Routing per URN

1. Region aus der URN – fremde Regionen werden an deren Endpunkt weitergeleitet (Verbund).
2. Projekt- und Knotenressourcen: Zelle aus der Shard-Karte; Regionsobjekte: Regions-Gruppe.
3. Schreiben und stark konsistentes Lesen gehen an den Leader, eventuell konsistentes Lesen an den lokalen Cache oder das nächste Mitglied.

Ist die Shard-Karte veraltet, antwortet die Zielzelle mit einem Hinweis, und der Router versucht es genau einmal neu. Leader-Hinweisen folgt er nur zu aktuellen Mitgliedern mit geprüfter mTLS-Identität. Weitergeleitet wird stets mit dem **Original-Token**; autorisiert wird am Ziel (siehe [API-first](api-first.html)).

## Reconciler-Modell

| Art | Wo | Was |
|---|---|---|
| **Zellen-Controller** | auf Knoten mit Lease | zellweite Entscheidungen: Platzierung, IP-Vergabe, Kontingente, Rollenregeln, Knotengesundheit, Fencing, Update-Staffelung |
| **Knoten-Reconciler** | jeder Knoten für sich selbst | Rollen starten, VMs/Container starten, Volumes anbinden, Netzkonfiguration; Status melden |
| Steuerungsgruppen-Controller | immer auf dem Raft-Leader | Raft-Mitgliedschaft |

- **Leases und Fencing:** Jeder Controller-Typ ist in Shards aufgeteilt, die per Rendezvous-Hashing auf geeignete Knoten verteilt werden. Leases liegen in Raft; ihren Ablauf beurteilt nur der Leader mit monotoner Uhr. Jeder Schreibzugriff trägt die Lease-Epoche – ein „Zombie-Controller“ nach einer Partition kann so nichts mehr bewirken.
- **Knoten-Reconciler** brauchen keine Lease, dürfen aber nur ihr eigenes Knotenobjekt und den Status ihnen zugewiesener Objekte schreiben.
- **Level-getrieben und idempotent:** Reconciler vergleichen stets Soll mit Ist; Ereignisse sind nur Auslöser, zusätzlich gibt es regelmäßige Vollabgleiche. Externe Ressourcen tragen die `uid` der API-Ressource; Schreibzugriffe sind bedingt; Fehler werden als Conditions sichtbar.
- **Fencing vor Neuplatzierung:** Bevor eine VM mit Netzwerk-Volume auf einem anderen Knoten startet, muss der alte Knoten nachweislich gestoppt sein – per Bestätigung, BMC-Abschaltung oder Ablauf einer Selbst-Fencing-Frist. VMs werden ohne nachgewiesenes Fencing nie automatisch verschoben.
- **Rollen** `control` und `witness` sind abgeleitet: Sie spiegeln die Raft-Mitgliedschaft, die allein der Steuerungsgruppen-Controller ändert. Der Betreiber setzt nur Präferenzen.
- Ein **Scheduler** filtert Knoten nach Architektur, Kapazität, Vertrauensstufe und Affinität, bewertet sie nach Strategie (Verdichten oder Streuen) und bietet einen Dry-Run mit Begründung je Knoten.

## Bootstrap-Ablauf

1. Der Betreiber initialisiert den ersten Knoten (Setup-Token). Dieser legt CA, Plattform, Region und Zelle an und startet als Einzelknoten-Raft.
2. Der zweite Knoten wird adoptiert (mit Bestätigungscode), erhält Zertifikat, Underlay-Zugang und Gossip-Schlüssel und tritt als **Learner** bei – Warnung „Zeuge fehlt“.
3. Ein Zeugengerät wird **ohne Rolle** adoptiert oder ein externer Zeuge registriert; der Controller macht daraus den Zeugen: **2 Daten-Voter + Zeuge** übersteht einen Ausfall.
4. Mit dem dritten geeigneten Knoten wird der Zeuge entfernt (3 Voter); er bleibt als Standby und springt ein, falls die Zelle wieder auf zwei geeignete Knoten fällt.
5. Ab mehr als 20 Knoten oder drei Ausfallzonen wächst die Steuerungsgruppe auf 5 Voter.

Rollen wie `witness` und `control` werden nie bei der Adoption vergeben. Ein ungeeigneter dritter Knoten (z. B. Pi 4 mit 1 GB) ändert nichts an „2 + Zeuge“.

## Ausfall- und Fehlerszenarien (Auswahl)

| Szenario | Verhalten | Wirkung für Nutzer |
|---|---|---|
| Arbeitsknoten fällt aus | als nicht erreichbar markiert; nach Frist Neuplatzierung geeigneter Workloads nach Fencing | Steuerung voll verfügbar |
| Follower-Voter fällt aus | Quorum bleibt, Umbesetzung über Learner | keine |
| Leader fällt aus | Neuwahl in wenigen Sekunden, Controller und Leases wandern mit | Schreiben kurz verzögert; Wiederholung per Idempotency-Key |
| Netzpartition | Mehrheit normal, Minderheit lesend | Schreibfehler auf der Minderheitsseite |
| Standortausfall | bei Streuung auf drei Standorte überlebt die Zelle; bei zwei Standorten ist ein Zeuge am dritten Ort Pflicht | je nach Topologie |
| Zellausfall | andere Zellen unberührt, Workloads laufen weiter | nur Projekte dieser Zelle |
| Regions-Gruppe fällt aus | Zellen arbeiten mit Caches weiter | zellübergreifende Operationen eingeschränkt |
| Stromausfall gesamt | Kaltstart aus Disk; Anlaufphase ohne Evakuierung | nach Hochlauf normal |
| Rolling Update | neue Formate erst aktiv, wenn alle Voter sie unterstützen; Leader zuletzt | keine |

## Sicherheit der Steuerungsebene

- **mTLS zwischen allen Agenten** mit Zertifikaten der Zellen-CA (Zwischen-CA unter der Regions-CA), kurzer Laufzeit und automatischer Rotation; zusätzlich läuft alles im WireGuard-Underlay.
- **Re-Zertifizierung nach langer Offline-Zeit** ohne Neu-Adoption, sofern Schlüssel und Hardware-Fingerabdruck unverändert sind; sonst Quarantäne.
- **Gossip** läuft nur im Underlay und ist zusätzlich mit einem rotierenden Zellenschlüssel versiegelt; Metadaten sind vom Ursprung signiert.
- **Knoten-Autorisierung** in der Zustandsmaschine: Arbeitsknoten dürfen keinen Sollzustand ändern und sehen keine fremden Mandantenobjekte.
- **Steuerungsknoten sind Kronjuwelen** und bevorzugt mit TPM und Attestierung abgesichert. Raft ist nicht byzantinisch fehlertolerant; Zellgrenzen begrenzen den Schaden.

Das übergreifende Modell beschreiben [Sicherheitsmodell](sicherheitsmodell.html) und [Bedrohungsmodell](bedrohungsmodell.html).

## Testkonzept

Verteilte Korrektheit wird durch deterministische Simulation ganzer Zellen, einen Invarianten-Checker, Modellprüfung kritischer Abläufe, Chaos- und Linearisierbarkeitstests sowie ein Hardware-Labor abgesichert. Abnahmekriterium für den MVP: „2 Knoten + Zeuge übersteht Ausfall“ und „kein Single Point of Failure ab 3 Knoten“ sind in der Simulation (10.000 Saaten ohne Invariantenverletzung) **und** auf echter Hardware nachgewiesen.
