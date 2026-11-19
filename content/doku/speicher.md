title: Speicher
summary: Block-, Objekt- und Dateispeicher von zwei Knoten bis Tausende – eigener Blockspeicher cp-blk mit Metadaten in der Zell-Raft, Mandantenverschlüsselung am Compute-Knoten und ein Reife-Gate vor Replikation.
group: konzept
order: 85
quelle: Konzept 12 (Speicherkonzept)
---

Das Speicherkonzept beschreibt, wie die Plattform Block-, Objekt- und Dateispeicher bereitstellt – auf zwei Raspberry Pis genauso wie auf tausend Servern. Entschieden am 2026-11-14.

## Kernentscheidungen

- **Blockspeicher eigen in Rust** (`cp-blk`) mit **einem** Datenpfad für alle Größen: Treiber `local` im ersten Release, `replicated` (2–3 Kopien) nach bestandenem Reife-Gate, Erasure Coding später für Kalt- und Objektklassen.
- **Metadaten in der vorhandenen Zell-Raft**, Nutzdaten nie. Kein zweiter Konsensmechanismus.
- **Mandantenverschlüsselung am Compute-Knoten:** Speicherknoten speichern und replizieren nur Chiffrat.
- **Objektspeicher zunächst Garage** hinter einem eigenen S3-Frontend `cp-s3gw`; Versionierung, Object Lock und Bucket-Ereignisse kommen mit einem eigenen Objektspeicher auf der `cp-blk`-Chunk-Schicht, wobei `cp-s3gw` die stabile Schnittstelle bleibt.
- **Dateispeicher** über einen NFS-Server je Share auf einem replizierten Volume, hinter einer schmalen Steuerschnittstelle austauschbar.
- **Ceph nur als optionaler externer Treiber** für Rechenzentren mit vorhandenem Ceph – nicht im Standardpfad.
- **Replikation als Standard:** unter drei Speicher-Hosts zwei Kopien mit Zeuge, ab drei Hosts drei Kopien.

## Anforderungen und Größenklassen

| Klasse | Knoten | Erwartung Block | Erwartung Objekt |
|---|---|---|---|
| G0 Einzelknoten | 1 | lokal, Snapshots, Backup nach extern | einfach |
| G1 Zwei Knoten + Zeuge | 2 | zwei Kopien, Weiterbetrieb bei Ausfall eines Knotens | zweifach |
| G2 Homelab/KMU | 3–10 | drei Kopien über Hosts | dreifach |
| G3 Edge/Standort | 10–100 | drei Kopien über Racks, QoS | dreifach über Zonen |
| G4 Zelle | 100–1.000 | wie G3 plus Rebalancing in großem Maßstab | Cluster je Zelle |
| G5 Region | Tausende | Pools je Zelle, zellübergreifend nur asynchron | Replikation zwischen Zellen |

Harte Anforderungen sind ein eigener Schlüssel je Volume mit Krypto-Löschung, Verschlüsselung ruhender Daten als Standard, kein Single Point of Failure ab drei Knoten, faire IOPS-Verteilung zwischen Mandanten, das knappe Speicherbudget kleiner Geräte und die Prozessgrenzen-Regel für Fremdkomponenten (siehe [Rust-Stack](rust-stack.html)).

## Optionen und Entscheidung

Der ursprüngliche Plan „Ceph ab drei Knoten, leichter Modus darunter“ wurde verworfen. Ceph passt am kleinen Ende nicht auf die Zielhardware (Arbeitsspeicher je Daemon, keine sinnvolle Zwei-Knoten-Betriebsart), bringt einen **zweiten Konsensmechanismus** neben der Plattform-Raft, eigene Identitäten statt X.509 und einen Bruch zwischen „klein“ und „groß“ mit zwei Datenpfaden und Migration beim Wachsen. Seine Reife ist das stärkste Gegenargument – der Preis ist für dieses Produkt aber zu hoch.

Verglichen wurden vier Varianten: Ceph über Prozessgrenze, alles eigen, ein Hybrid „Block eigen, Objekt zunächst Garage“ sowie ein klassischer Hybrid mit eigenem leichten Modus und Ceph darüber. Fremdalternativen wie DRBD/LINSTOR, Longhorn oder SeaweedFS tragen entweder keine zwei Knoten oder brauchen einen zweiten Konsens. **Gewählt wurde der Hybrid:** Er nutzt, was die Plattform ohnehin hat – Raft, Fehlerdomänen, Fencing, Schlüsselverwaltung, PKI, Scheduler –, ersetzt zwei externe Systeme durch einen eigenen Pfad und vermeidet den Umfang der S3-Semantik für den Anfang. Garage verletzt das Prinzip „ein Konsens“ nicht, da es mit CRDT-Metadaten und Quoren arbeitet; sein Layout setzt der Agent aus der Steuerungsebene.

Das Nicht-Ziel „kein eigenes verteiltes Dateisystem“ ist damit präzisiert: Kein eigenes verteiltes **Dateisystem**, keine eigene **Datenbank**, kein Ceph als Pflichtbestandteil – Block- und Objektspeicher auf Basis der Plattform-Raft und der Chunk-Schicht sind Eigenentwicklung.

## Architektur von cp-blk

| Baustein | Ort | Aufgabe |
|---|---|---|
| Speichermodul des Agenten | jeder Knoten | Platteninventar und -adoption, Pool-Mitgliedschaft, Steuerung von `cp-blkd`, Statusmeldung |
| Platzierungs-Controller | Controller der Zelle | Platzierungskarte berechnen, Epochenwechsel bei Ausfall, Rebalancing, Kapazität |
| `cp-blkd` | eigener, isolierter Prozess | Speicher auf der Platte, Replikation, Wiederherstellung, Scrubbing; Client-Teil auf Compute-Knoten |
| `cp-privd` | jeder Knoten | privilegierte Schritte mit festem Befehlsset (Verschlüsselung einrichten, Geräte anlegen) |

`cp-blkd` läuft bewusst außerhalb des Agenten, damit ein Fehler im Datenpfad den Agenten nicht beeinträchtigt.

### Datenmodell und Datenpfad

- Ein **Pool** ist eine Menge von Platten gleicher Medienklasse in einer Zelle mit einer Replikationsregel. **Placement-Groups** sind die Verteilungseinheit.
- Ein **Volume** ist eine Folge von Chunks fester Größe; jeder Chunk wird per Hash einer Placement-Group zugeordnet, diese einer geordneten Menge von Repliken.
- **Die Raft hält** Pools, Abweichungen von der berechneten Platzierung, Epochen, Volume-Metadaten, Snapshot-Bäume und Plattenzustände – auch bei tausend Knoten nur wenige Megabyte. Nutzdaten und Chunk-Indizes liegen nie in der Raft.
- **Schreiben:** Der Client schreibt an die Primärkopie der Placement-Group, diese lokal und parallel an die Repliken; die Quittung kommt erst, wenn die Mindestzahl an Kopien dauerhaft gespeichert ist. Anfragen mit veralteter Epoche werden abgelehnt.
- **Epochenwechsel** erfolgen nur über einen Schreibzugriff des Controllers auf die Raft. Dadurch gibt es **kein Split-Brain**, auch nicht bei zwei Knoten: Ohne Quorum (mit Zeuge) keine neue Epoche.
- Jeder Chunk trägt einen **selbstbeschreibenden Kopf** (Pool, Volume, Index, Epoche, Version, Prüfsumme) – Grundlage der Notfall-Rekonstruktion.
- **Auf dem Compute-Knoten** stellt `cp-blkd` über ublk ein Blockgerät bereit; darüber liegt dm-crypt mit dem Volume-Schlüssel. Hypervisor und Container sehen nur das entschlüsselte Gerät. NBD dient als Rückfall.
- **Transport** über mTLS mit eigenem Dienstzertifikat im Underlay; die Nutzdaten sind dabei bereits Mandanten-Chiffrat (siehe [Netzwerk](netzwerk.html)).

### Treiber

| Treiber | Ab | Inhalt |
|---|---|---|
| `local` | erstes Release | Thin-Volumes und -Snapshots auf einem Knoten, Verschlüsselung je Volume |
| `replicated` | nach Reife-Gate | `cp-blk` mit Kopienzahl und Mindestkopien |
| `ec` | später | Erasure Coding als zusätzliche Klasse, Standard für Objekt, Backup und Archiv ab etwa sechs Speicher-Hosts |
| `ceph-rbd` | später, optional | externer Ceph-Cluster des Betreibers, nur Client-Seite |

Alle Treiber teilen API, Snapshots, Backups und Verschlüsselung. Ein Treiberwechsel ist eine Volume-Migration; da die Mandantenschicht über dem Treiber liegt, bleibt das Chiffrat unverändert.

Solange `replicated` das Reife-Gate nicht bestanden hat, nutzen Mandanten-Volumes `local`. Als Ausgleich erhält jedes Volume standardmäßig eine **Snapshot- und Backup-Richtlinie mit Ziel auf einem anderen Knoten** – abwählbar nur ausdrücklich und auditiert. Diese Abweichung ist dokumentiert und befristet.

## API-Ressourcen

Die Speicher-API folgt dem Ressourcenmodell der Plattform (siehe [API-first](api-first.html)):

- **Betreiberseitig:** `Disk` (Platte mit Typ, Größe, Gesundheit, Medienklasse), `StoragePool` (Treiber, Replikationsregel, Fehlerdomäne), `StorageClass` (Pool-Auswahl, QoS, Verschlüsselung – nicht abschaltbar –, erlaubte Datenklassen).
- **Mandantenseitig:** `Volume`, `VolumeAttachment`, `VolumeSnapshot`, `Bucket`, `AccessKey`, `FileShare` sowie Backup-Richtlinien, -Tresore und Wiederherstellungspunkte.
- **Langlaufende Operationen** wie Größenänderung, Klonen, Migration, Snapshot-Wiederherstellung, Platten-Adoption, -Entleerung, -Stilllegung und sicheres Löschen.

Platten- und Pool-Operationen sind Betreiberrechte; Formatierung und Löschung verlangen eine ausdrückliche Bestätigung. API, CLI, MCP und [Portal](portal.html) bieten denselben Funktionsumfang.

## Platzierung über Fehlerdomänen

- Topologie-Labels (Standort, Raum, Rack, Stromkreis, Switch, Host, Platte) bilden einen Baum.
- Die Platzierung nutzt **gewichtetes Rendezvous-Hashing** je Ebene: deterministisch aus Placement-Group, Pool-Epoche und Topologie, sodass jeder Knoten sie nachrechnen kann. Beim Hinzufügen oder Entfernen bewegt sich nur das Nötigste.
- Gibt es zu wenige Domänen, weicht die Platzierung eine Ebene tiefer aus und meldet das sichtbar; zwei Kopien auf derselben Platte gibt es nie.
- **Ungeeignete Medien** wie SD-Karten und USB-Sticks sind erlaubt, aber deutlich gekennzeichnet, niedrig gewichtet und je Fehlerdomäne auf höchstens eine Kopie begrenzt.
- **Lokationsgrenzen:** Pools enden an der Zelle; Richtlinien können Speicher auf Standorte beschränken.
- **Vertrauensstufen:** Da Speicherknoten nur Chiffrat halten, genügt standardmäßig die niedrigste Stufe; maßgeblich ist die Stufe des Compute-Knotens, der den Schlüssel erhält (siehe [Sicherheitsmodell](sicherheitsmodell.html)).

Der Scheduler bindet Workloads mit `local`-Volumes an ihren Knoten und bevorzugt bei `replicated` Knoten mit lokalen Kopien. Vor dem Neustart einer VM auf einem anderen Knoten erhöht der Controller die **Anhängungs-Epoche**, sodass der alte Client nicht mehr schreiben kann.

## Platten-Lebenszyklus

Eine Platte durchläuft die Zustände **entdeckt → vorgeschlagen → in Adoption → aktiv → wird entleert / ausgefallen → stillgelegt → sicher gelöscht**.

- **Adoption** nur für leere oder ausdrücklich freigegebene Platten, mit Warnung bei ungeeigneten Medien.
- **Ersatz:** Eine neue Platte wird als neue Ressource adoptiert; der Wiederaufbau verteilt sich auf viele Quellen.
- **Gesundheit:** SMART-Abfragen, tägliches leichtes und regelmäßiges tiefes Scrubbing mit Vergleich der Kopien, Verschleißüberwachung – bei Erreichen von Schwellwerten wird die Entleerung vorgeschlagen.
- **Sicheres Löschen:** Mandantendaten durch Krypto-Löschung; stillgelegte Platten durch Löschen des Verschlüsselungs-Headers und Hardware-Sanitize, mit signiertem Löschnachweis.

## Sicherheit

| Thema | Umsetzung |
|---|---|
| Plattformschicht | LUKS2 auf jeder Speicherplatte, Schlüssel TPM-versiegelt oder netzgebunden |
| Mandantenschicht | eigener Schlüssel je Volume, Verschlüsselung auf dem Compute-Knoten, gewrappt unter dem Mandantenschlüssel |
| Schlüsselfreigabe | nur an Knoten mit gültiger Anhängungs-Epoche und ausreichender Vertrauensstufe; Speicherknoten erhalten nie Mandantenschlüssel |
| Mandantentrennung | zufällige Volume-Kennungen; jeder Aufruf an `cp-blkd` trägt Epoche und Zertifikat des Aufrufers, autorisiert aus der Steuerungsebene |
| Integrität | Prüfsummen gegen Medienfehler; eine authentisierte Verschlüsselung für erhöhten Schutzbedarf ist als spätere Option vorgesehen |
| Objekt | Das S3-Frontend leitet je Objekt einen Schlüssel aus dem Bucket-Schlüssel ab; Garage speichert keine Schlüssel |

Details der Verfahren und der Schlüsselhierarchie stehen in der [Kryptografie](kryptografie.html).

## Haltbarkeit und Reife-Gate

Rechnerisch ist schon zweifache Replikation bei unabhängigen Ausfällen sehr haltbar. In der Praxis dominieren aber **korrelierte Fehler** und **Softwarefehler** – für einen Eigenbau ist die Korrektheit des Codes das eigentliche Risiko. Deshalb gilt vor Mandantendaten auf `replicated` ein **Reife-Gate**:

- deterministische Simulation mit Partitionen, Neustarts, Epochenwechseln und Uhrenabweichungen, geprüft auf Linearisierbarkeit;
- reale Fehlerinjektion über Wochen ohne Datenverlust;
- Crash-Konsistenz-Tests mit Stromabriss;
- **Notfall-Rekonstruktion** der Volumes allein aus den selbstbeschreibenden Chunks, ohne Raft;
- Upgrade- und Downgrade-Tests;
- externes Design- und Code-Review durch Speicherexperten.

**Wiederherstellung:** Crash-konsistente Snapshots, Mandanten-Backups mit Änderungsverfolgung als verschlüsselte, deduplizierte Sicherung in S3, Plattform-Backups der Metadaten (ohne Nutzdaten) und asynchroner Snapshot-Versand zwischen Zellen für Desaster-Szenarien. Unveränderliche Sicherungen folgen mit dem eigenen Objektspeicher.

### Erkenntnisse aus Messungen

Erste Messungen stützen die Entscheidung qualitativ: Synchrone Replikation kostet kaum mehr als ein lokales Schreiben mit Synchronisierung – die Latenz bestimmt das **Medium**, weshalb die Medienwahl wichtiger ist als der Replikationsgrad. Erasure Coding ist auf ARM beim Kodieren günstig, beim Rekonstruieren aber teuer und kommt daher erst später und nur auf leistungsfähigen Knoten. Hardwarebeschleunigte Prüfsummen sind deutlich schneller als kryptografische Hashes und genügen gegen Medienfehler. AES-Verschlüsselung reicht auf Geräten mit Krypto-Erweiterung bequem aus; Geräte ohne diese Erweiterung sind der Engpass und werden vor einer Freigabe für Compute mit Volumes auf echter Hardware nachgemessen.
