title: Release-Signatur
summary: Zwei Signaturwege für Releases, das Format der Update-Metadaten nach dem TUF-Prinzip, die Abläufe und die Reproduzierbarkeit der Builds.
group: prozess
order: 220
quelle: Prozessbeschreibung Release-Signatur, Update-Metadaten und Reproduzierbarkeit
---

## Überblick: zwei Signaturwege

BYOC signiert Releases auf zwei voneinander unabhängigen Wegen. Sie beantworten unterschiedliche Fragen
für unterschiedliche Prüfer.

| Weg | Zweck | Schlüssel | Prüfer |
|---|---|---|---|
| **Sigstore/cosign keyless** | öffentliche Releases; Nachweis „gebaut von genau diesem CI-Workflow“ | kurzlebiges Zertifikat aus der OIDC-Identität des Workflows, Eintrag im öffentlichen Transparenzlog; zusätzlich SLSA-Provenienz | Menschen, Paketierer, Betreiber vor der Installation |
| **Offline-Schlüssel ECDSA P-384** (TUF-Muster) | Update-Kette der Knoten | Root und Targets offline, Snapshot und Timestamp kurzlebig | Agent und Installer auf jedem Knoten – **offline**, ohne Netz und ohne Sigstore |

Die Knoten vertrauen **ausschließlich** dem im OS-Image eingebetteten Root der Update-Kette. Sigstore ist eine
zusätzliche, öffentliche Transparenzschicht, aber keine Laufzeitabhängigkeit: Ein Cluster ohne Internetzugang prüft
Updates genauso streng wie ein vernetzter. In einer späteren Phase kommt ML-DSA-87 als zweite, post-quantensichere
Signatur je Umschlag hinzu (siehe [Kryptografie](kryptografie.html)).

## Update-Metadaten nach dem TUF-Prinzip

Die Update-Kette folgt dem Muster von *The Update Framework* (TUF) mit vier Rollen. Jede Rolle hat eigene
Schlüssel, eigene Schwellwerte und eigene Ablaufzeiten – eine kompromittierte Rolle allein genügt nicht, um Knoten
ein manipuliertes Update unterzuschieben.

| Datei | Rolle | Inhalt | Standard-Ablauf | Schlüssel |
|---|---|---|---|---|
| `root.json` | root | alle öffentlichen Schlüssel, je Rolle Schlüssel-IDs und Schwellwert | 365 Tage | offline, im Echtbetrieb *k* von *n* |
| `targets.json` | targets | Zielname → Länge, SHA-256, SHA-512 | 90 Tage | offline (Release-Schlüssel) |
| `snapshot.json` | snapshot | Verweis auf `targets.json` (Version, Länge, Hashes) | 30 Tage | Release-Infrastruktur |
| `timestamp.json` | timestamp | Verweis auf `snapshot.json` | 7 Tage | Release-Infrastruktur, häufig neu signiert |
| `<n>.root.json` | root | frühere/neue Root-Versionen für die Rotationskette | – | alter **und** neuer Root |

Für Release-Bündel, die offline transportiert werden, können die Metadaten so lange gültig sein wie das
Release-Manifest (siehe [Release-Bündel](release-buendel.html)).

### Umschlag (DSSE)

Jede Metadatei ist ein DSSE-Umschlag (*Dead Simple Signing Envelope*): Typangabe, Base64-kodierte Nutzlast und eine
Liste von Signaturen mit Schlüssel-ID. Signiert wird die *Pre-Authentication Encoding* aus Typ und Nutzlast.
Dadurch entfällt kanonisches JSON: Geprüft werden exakt die signierten Bytes, **erst danach** wird geparst – und
dabei werden unbekannte Felder abgewiesen. Die Schlüssel-ID ist der SHA-256 des öffentlichen Punkts.

```json
{
  "payloadType": "application/vnd.cloud-project.update-metadata+json",
  "payload": "<Base64 der JSON-Nutzlast>",
  "signatures": [ { "keyid": "<hex>", "sig": "<Base64>" } ]
}
```

Zeitangaben sind strikt UTC im Format `YYYY-MM-DDTHH:MM:SSZ`. Die Versionsnummer von targets, snapshot und
timestamp leitet sich standardmäßig aus der Commitzeit ab und ist damit monoton.

### Prüfablauf auf dem Knoten

1. **Root laden** (eingebettet bzw. zuletzt vertraut): muss sich selbst mit Schwellwert signieren; Version nicht
   kleiner als die gespeicherte.
2. **Root-Kette** abarbeiten: jede neue Root-Version genau eine höher und mit dem Schwellwert **des alten und des
   neuen** Roots signiert. Wechseln Timestamp- oder Snapshot-Schlüssel, werden deren gespeicherte Versionen
   zurückgesetzt (Erholung nach einem Fast-Forward-Angriff).
3. **Ablauf des Roots** erst nach der Kette prüfen – so kann auch ein abgelaufener Anker noch rotiert werden.
4. **timestamp:** Signatur, Versionsmonotonie, nicht abgelaufen.
5. **snapshot:** Länge und Hashes laut timestamp, Signatur, passende Version, nicht abgelaufen.
6. **targets:** Länge und Hashes laut snapshot, Signatur, passende Version, nicht abgelaufen.
7. **Artefakt:** Länge, SHA-256 und SHA-512 laut targets.
8. **Versionen dauerhaft speichern**, damit der Rollback-Schutz auch über Neustarts hinweg wirkt.

| Angriff | Abwehr |
|---|---|
| Rollback auf alte Metadaten | Versionsmonotonie, persistiert |
| Einfrieren auf altem Stand (Freeze) | Ablaufzeiten, kurzlebiger Timestamp |
| Mix-and-Match verschiedener Stände | Hashbindung timestamp → snapshot → targets |
| Endlos-Daten | feste Größengrenze für Metadateien |
| Schlüsselkompromittierung | Rollentrennung, Schwellwerte, Root-Rotation |
| doppelte Signaturen | nur verschiedene Schlüssel zählen zum Schwellwert |

**Bewusste Vereinfachungen gegenüber TUF 1.0:** keine delegierten Targets, kein *consistent snapshot*, DSSE statt
kanonischem JSON, Schlüssel-ID über die Punktbytes. Interoperabilität mit fremden TUF-Clients ist kein Ziel; das
Format ist über `spec_version` versioniert.

## Abläufe

### Entwicklung und CI

In der Entwicklung und in der CI wird mit einem **flüchtigen Einmalschlüssel** signiert, der nach dem Lauf gelöscht
wird. Das Werkzeug verweigert Schlüsselverzeichnisse innerhalb des Repositorys, damit keine Schlüssel versehentlich
eingecheckt werden. Die Prüfung läuft mit derselben Bibliothek wie auf den Knoten.

### Öffentliches Release

1. Ein Versions-Tag startet den Release-Workflow: Build je Zielplattform ohne Cache, Prüfsummenliste, unabhängiger
   Nachbau, cosign-Signaturen und SLSA-Provenienz. Ergebnis ist ein Release-**Entwurf**.
2. **Offline-Zeremonie** auf einem Rechner ohne Netz, Schlüssel auf verschlüsseltem Datenträger bzw. später auf
   Hardware-Token oder HSM: Artefakte und Sigstore-Nachweise prüfen (Zertifikatsidentität muss der Release-Workflow
   des Projekts sein), Hashes mit dem Nachbau vergleichen, dann die Update-Metadaten signieren.
3. Die Update-Metadaten werden dem Release angehängt; der Entwurf wird im **Vier-Augen-Prinzip** freigegeben.
4. Der Timestamp wird regelmäßig (spätestens alle 7 Tage) neu signiert; die Automatisierung mit einem Online-Schlüssel
   ist ein offener Punkt.

### Root-Rotation

Eine neue Root-Generation wird mit den neuen **und** den alten Root-Schlüsseln signiert (jeweils mit Schwellwert).
Bündel tragen die Rotationskette mit; Knoten mit älterem Anker steigen darüber Schritt für Schritt auf, und die Region
schreibt die vertraute Root-Version fort. Mit alten Schlüsseln signierte Bündel werden danach abgewiesen.

## Reproduzierbarkeit

Ein eigener Nachbau-Schritt kopiert den Arbeitsbaum in zwei verschiedene temporäre Verzeichnisse mit
unterschiedlichen Pfadlängen, baut dort jeweils unabhängig (eigenes Build-Verzeichnis, andere Uhrzeit, gleiche
Quellzeit `SOURCE_DATE_EPOCH`) und vergleicht die SHA-256 aller Artefakte – Binaries und SBOMs. Nur bitgleiche
Ergebnisse gelten als reproduzierbar. Bei der Offline-Zeremonie wird zusätzlich gegen den Nachbau verglichen.

## SBOM

Jeder Build erzeugt je Komponente eine SBOM im Format **CycloneDX 1.5** und daraus **SPDX 2.3** – mit einem
projekteigenen Konverter, um keine zusätzliche Werkzeug-Lieferkette einzuführen. Auch die SBOM ist reproduzierbar:
Zeitstempel aus der Quellzeit, Seriennummer deterministisch aus dem normalisierten Dokument, sortierte Komponenten
und Abhängigkeiten. Die Binaries tragen zusätzlich ihre Abhängigkeitsliste eingebettet, sodass sich auch installierte
Knoten nachträglich gegen neue Advisories prüfen lassen (siehe
[Schwachstellenmanagement](schwachstellenmanagement.html)).

## Sicherheit und Compliance

- **Integrität und Rollback-Schutz** der Updates, **signierte, reproduzierbare Builds mit Provenienz** und
  **SBOM in zwei Formaten** sind feste Anforderungen des Projekts (siehe [Sicherheitsmodell](sicherheitsmodell.html)).
- Einziger Kryptografie-Provider ist eine geprüfte Bibliothek (siehe [Kryptografie](kryptografie.html)).
- **Rückfallebene:** Ohne HSM liegen Offline-Schlüssel auf verschlüsselten Datenträgern, Root-Schlüssel *k* von *n*
  auf getrennte Verantwortliche verteilt. Ohne Zugang zu Sigstore prüfen Knoten unverändert weiter, denn sie
  verwenden nur die Offline-Kette.
- **Offen:** Automatisierung des Timestamps, Schlüsselzeremonie und HSM-Wahl, zweite Signatur mit ML-DSA-87.
