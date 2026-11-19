title: Release-Bündel
summary: Format, Prüfung, Import und Verteilung des Release-Bündels, über das ein Plattform-Release in einen Cluster gelangt.
group: prozess
order: 210
quelle: Prozessbeschreibung Release-Bündel und Release-Manifest
---

## Zweck

Ein Plattform-Release – Agent, OS-Basis, Erweiterungen und Boot-Artefakte in einer gemeinsamen Version – gelangt
**ausschließlich per Import** in einen Cluster. Es gibt keinen Online-Abruf aus dem Cluster heraus; der Betreiber
lädt ein Bündel über API, Kommandozeile, MCP oder Portal hoch. Damit funktionieren Updates in abgeschotteten
Umgebungen (Air-Gap) genauso wie in vernetzten, und der Betreiber entscheidet bewusst, welches Release in seine
Region kommt.

Das Transportformat heißt `cp.release-bundle/v1`. Es ist ein einzelnes, **unkomprimiertes tar-Archiv mit fester
Reihenfolge**. Diese Reihenfolge ist der Kern des Designs:

- Der Empfänger prüft Signaturen und Release-Regeln, **bevor** die großen Artefakte ankommen. Ein ungültiges
  Bündel wird nach wenigen Kilobyte abgewiesen.
- Jedes Artefakt wird beim Empfang gehasht – gestreamt, ohne das ganze Bündel zwischenzuspeichern.
- Kompression wird bewusst nicht verwendet: Die Images sind bereits komprimiert bzw. Verity-Abbilder, und
  Kompression würde den wahlfreien Zugriff verhindern, den die Wiederaufnahme abgebrochener Uploads braucht.

Die Signaturkette selbst ist in [Release-Signatur](release-signatur.html) beschrieben; wie ein importiertes Release
auf die Knoten ausgerollt wird, beschreibt [Rollout-Controller](rollout.html).

## Container-Format

Das Archiv ist POSIX-**ustar** (512-Byte-Blöcke, zwei Nullblöcke am Ende). Die strengen Regeln sollen den Parser
klein und angriffsarm halten:

- nur reguläre Dateien; Verzeichniseinträge werden übersprungen,
- jeder Name höchstens einmal,
- keine Links, keine PAX- oder GNU-Langnamen,
- keine Pfade mit `..` oder führendem `/`,
- Größen ab 8 GiB im Base-256-Feld.

| # | Eintrag | Pflicht | Inhalt |
|---|---|---|---|
| 1 | `bundle.json` | ja | Formatkennung und Version (nur Hinweis, maßgeblich ist das Manifest) |
| 2 | `metadata/<n>.root.json` | nein | Root-Rotationskette, aufsteigend nach Root-Version |
| 3 | `metadata/timestamp.json` | ja | signierte Rolle *timestamp* |
| 4 | `metadata/snapshot.json` | ja | signierte Rolle *snapshot* |
| 5 | `metadata/targets.json` | ja | signierte Rolle *targets*: **alle** Artefakte und das Manifest mit Länge, SHA-256 und SHA-512 |
| 6 | `targets/release/manifest.json` | ja | Release-Manifest `cp.release/v1`, selbst ein signiertes Ziel |
| 7 | `targets/<ziel>` | ja¹ | jedes weitere Ziel aus `targets.json`, in beliebiger Reihenfolge |

¹ Ein Ziel darf fehlen, wenn der Empfänger es bereits inhaltsadressiert vorhält (siehe Wiederaufnahme).

Zielnamen bestehen aus Segmenten mit Buchstaben, Ziffern und `._+-`, getrennt durch `/`, etwa
`os/x86-64/uki.efi`. Das Präfix `boot/` kennzeichnet Boot-Artefakte für den Netzboot-Dienst (siehe
[Boot und Adoption](boot-adoption.html)). Weil das Format bewusst schlicht ist, lässt sich ein Bündel auch mit
Standardwerkzeugen (`tar --format=ustar`) in der Reihenfolge der Tabelle erzeugen; das Release-Werkzeug des Projekts
schreibt es gestreamt.

## Release-Manifest `cp.release/v1`

Das Manifest beschreibt das Release fachlich. Es ist selbst ein Ziel der signierten Kette und damit gegen
Austausch, Rollback und Einfrieren geschützt. Beispiel mit Platzhalterwerten:

```json
{
  "apiVersion": "cp.release/v1",
  "version": "1.4.2",
  "channel": "stable",
  "securityEpoch": 7,
  "minVersion": "1.3.0",
  "minAgentProtocol": 12,
  "artifacts": [
    { "name": "usr", "arch": "x86-64", "target": "os/x86-64/usr.raw",
      "sha256": "…", "size": 287309824, "verityRootHash": "…" },
    { "name": "uki", "arch": "x86-64", "target": "os/x86-64/uki.efi",
      "sha256": "…", "size": 61440000 }
  ],
  "sbom": { "cyclonedx": "sha256:…" },
  "sources": { "bundle": "sha256:…" },
  "provenance": { "slsa": "sha256:…" },
  "notBefore": "2026-11-10T00:00:00Z",
  "expires": "2027-05-10T00:00:00Z"
}
```

| Feld | Bedeutung |
|---|---|
| `version` | `MAJOR.MINOR.PATCH` für das gesamte Plattform-Release; PATCH enthält nur Sicherheits- und Fehlerbehebungen |
| `channel` | `stable`, `candidate` (Vorabtest) oder `edge` (nur Entwicklung) |
| `securityEpoch` | steigt bei sicherheitsrelevanten Korrekturen; ein Rückschritt unter die laufende Epoche ist verboten |
| `minVersion` | Mindestversion für einen direkten Update-Pfad |
| `minAgentProtocol` | Mindeststand des Agentenprotokolls für die Versionsverhandlung |
| `artifacts` | Name, Architektur, Zielname im Bündel, SHA-256, Größe, bei Verity-Abbildern der Root-Hash |
| `sbom`, `sources`, `provenance` | Verweise (per Hash) auf SBOM, Quellcode-Archiv und SLSA-Provenienz – ebenfalls Ziele des Bündels |
| `notBefore`, `expires` | Gültigkeitsfenster; schützt davor, Knoten dauerhaft auf einem alten Manifest festzuhalten |

Unbekannte Felder werden abgewiesen. Das Feld `target` verbindet jedes Artefakt mit genau einem signierten Ziel.

## Prüfung

Die Prüfung ist für **alle Bezugswege identisch** – Import über die API, Agent beim Update und Installer. Es gibt
also keinen „bequemeren“ Pfad mit schwächeren Regeln.

1. **Signaturkette** gegen den vertrauten Root-Anker im OS-Image: gegebenenfalls Root-Rotation Schritt für Schritt,
   dann timestamp → snapshot → targets mit Signatur, Versionsbezug, Hash und Ablauf. Die zuletzt vertraute
   Root-Version wird je Region festgehalten (Schutz vor Root-Rollback).
2. **Manifest** ist ein signiertes Ziel (Länge, SHA-256, SHA-512 stimmen).
3. **Release-Regeln:** Format und Version, bekannter Kanal, `notBefore ≤ jetzt < expires`, `securityEpoch`
   mindestens so hoch wie die höchste Epoche, die Knoten gerade ausführen, und `minVersion` höchstens die
   niedrigste laufende Version.
4. **Artefaktliste = signierte Ziele:** Jedes Artefakt entspricht genau einem Ziel gleicher Länge und gleichen
   Hashes, jedes Ziel (außer dem Manifest) genau einem Artefakt.
5. **Jedes empfangene Artefakt** wird gegen Länge, SHA-256 **und** SHA-512 geprüft. Erst danach wird es im Speicher
   sichtbar (temporäre Datei, `fsync`, atomares Umbenennen).

Fehler werden auf die üblichen API-Fehlerklassen abgebildet (siehe [API-first](api-first.html)): Signatur-, Format-
und Hashfehler als ungültiges Argument, Epoche, Mindestversion oder Gültigkeitsfenster als nicht erfüllte
Vorbedingung, dieselbe Version mit anderem Inhalt als Konflikt. Eine konfigurierbare Größengrenze schützt vor
übergroßen Uploads.

## Import, Wiederaufnahme und Deduplizierung

Der Import ist eine Aktion auf der Region (`region:importArtifacts`). Das Bündel wird als tar-Strom übertragen;
für kleine Bündel – etwa über MCP – ist zusätzlich eine JSON-Form mit Base64-Inhalt möglich. Der Import ist keine
privilegierte Aktion, denn die Signaturkette entscheidet, was angenommen wird.

Mit `validateOnly` prüft der Server nur und meldet zusätzlich `missingTargets`, also die Ziele, die er noch nicht
vorhält. Das Ergebnis eines Imports ist `created`, `unchanged`, `validated` oder `incomplete`.

Die **Wiederaufnahme** nach einem Abbruch nutzt die Inhaltsadressierung: Vollständig empfangene Artefakte bleiben
erhalten. Kommandozeile und Portal senden deshalb zuerst nur Metadaten und Manifest als Probelauf und danach ein
Teilbündel mit **ausschließlich den fehlenden** Zielen. Ein erneuter Import desselben Release ist unschädlich
(`unchanged`); gleiche Artefakte in verschiedenen Releases werden nur einmal gespeichert.

## Ablage und Verteilung

Jeder haltende Knoten legt Releases inhaltsadressiert ab: Artefakte und Metadateien als schreibgeschützte Blobs
nach SHA-256, je Version ein Verzeichnis mit den Metadaten, harten Links auf die Artefakte und einem lokalen
Eintrag mit allen Zielen und Hashes. Diese Struktur entspricht dem, was der Netzboot-Dienst erwartet – die
Boot-Artefakte eines Release stehen damit ohne Umkopieren für PXE- und HTTP-Boot bereit. Zusätzlich liefert der
Boot-Dienst alle Ziele geprüfter Releases inhaltsadressiert aus.

- **Halter** sind Knoten mit der Rolle `boot` oder `control`; Soll sind zwei Kopien (bzw. so viele, wie Kandidaten
  vorhanden sind).
- **Replikation** zwischen Haltern läuft über einen internen, gegenseitig authentisierten TLS-Endpunkt mit
  Knotenzertifikaten. Der Empfänger prüft die Kette erneut – er vertraut dem Sender nicht.
- **Ausfall eines Halters** erkennt der Cluster am ausbleibenden Takt; der nächste Kandidat holt das Release nach.
- Der Status der Ressource `Release` nennt die erreichbaren vollständigen Kopien. Der
  [Rollout-Controller](rollout.html) gibt eine Zielversion erst frei, wenn das Release verfügbar ist und genug
  Halter hat.

Knoten holen ihr Update später bei diesen Haltern ab. Eine Peer-to-Peer-Verteilung zwischen beliebigen Knoten ist
für eine spätere Ausbaustufe vorgesehen.

## Bau und Signatur (Ablauf)

Bau und Signatur sind getrennt, damit private Release-Schlüssel nie mit der Build-Umgebung in Berührung kommen:

1. **Bauen:** Binaries und OS-Images je Architektur werden gebaut, SBOM, Quellcode-Archiv und Provenienz erzeugt.
   Ergebnis ist ein unsignierter **Plan**, der das Manifest (exakte Bytes) sowie Länge, SHA-256 und SHA-512 aller
   Ziele enthält.
2. **Offline signieren:** Eine getrennte Signierumgebung erhält nur den Plan, prüft, dass Manifest und Zielliste
   zusammenpassen, und signiert die Update-Metadaten. Die großen Artefakte verlassen die Build-Umgebung dabei nicht;
   ausgetauscht werden nur öffentliche Daten (Plan, signierte Metadaten, Root-Dateien).
3. **Bündel zusammensetzen:** Metadaten, Manifest und Artefakte werden in der festen Reihenfolge gestreamt
   geschrieben.
4. **Prüfen:** Das fertige Bündel durchläuft dieselbe Prüfung wie beim Import; zusätzlich wird kontrolliert, dass der
   im Image eingebettete Vertrauensanker zur verwendeten Root passt.

Zur Gültigkeit: Die Metadaten eines Bündels sind standardmäßig so lange gültig wie das Manifest (`expires`), damit
offline transportierte Bündel importierbar bleiben. Schutz gegen das Einfrieren auf altem Stand bieten `expires` und
`securityEpoch`. Für Test- und Echtbetrieb werden getrennte Roots verwendet; die Root-Rotation ist in
[Release-Signatur](release-signatur.html) beschrieben.
