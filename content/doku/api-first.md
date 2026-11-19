title: API-first – API, Portal und MCP gleichwertig
summary: Warum jede Funktion zuerst eine API-Operation ist, wie Ressourcen und Operationen aufgebaut sind und wie Portal und MCP daraus abgeleitet und auf Parität geprüft werden.
group: konzept
order: 30
quelle: Konzept 04 (Prinzip API-first)
---

## Grundsatz

> **Jede Funktion der Plattform ist zuerst eine API-Operation. Portal und MCP sind zwei weitere Darstellungen derselben Operation – nie eigene Logik, nie eigener Zustand.**

Das gilt ausnahmslos auf jeder Ebene (siehe Glossar in der [Vision](vision.html)):

| Bereich | Ebenen | Beispiele |
|---|---|---|
| Betreiber | Plattform → Region → Zelle → Knoten | Ersteinrichtung, Adoption, Rollen zuweisen, Drain, Stilllegung, Updates, Zellen anlegen |
| Mandant | Mandant → Projekt → Ressource/Dienst | Nutzer, Rollen, Kontingente, VM, Volume, VPC, Bucket, Kubernetes-Cluster |
| Sonderfälle | Bootstrap, Adoption | erster Knoten ohne Identitätsdienst; Freigabe wartender Hardware |

**Die API ist die einzige Quelle der Wahrheit:**

- Der *gewünschte Zustand* jeder Ressource existiert nur in der API und wird in der Steuerungsgruppe der zuständigen Zelle bzw. Region gespeichert (siehe [Steuerungsebene](steuerungsebene.html)). Portal und MCP halten außer Oberflächen- und Sitzungsdaten keinen eigenen Zustand.
- Das **API-Schema** ist die einzige Definition von Ressourcen, Feldern, Validierung, Berechtigungen und Dokumentation. Portal-Formulare, MCP-Tools, CLI, SDKs und der spätere OpenTofu-Provider werden daraus abgeleitet.
- Es gibt **keinen Seitenkanal**: keine Portal-only-Schalter, keine Konfigurationsdatei auf Knoten, die an der API vorbei wirkt, standardmäßig kein SSH. Auch Notfall- und Diagnosezugriffe sind API-Operationen mit besonderem Audit: befristete, begründete und aufgezeichnete Diagnosesitzungen sowie – nur für die höchste Betreiberstufe – SSH ausschließlich mit kurzlebigen Zertifikaten.

### Begründung

1. **Parität ist sonst nicht haltbar.** Drei handgepflegte Zugänge driften auseinander; aus einem Schema generierte nicht.
2. **Dezentralität.** Ohne zentralen Controller muss jeder Knoten dieselbe Oberfläche ausliefern – das geht nur, wenn sie generisch aus dem Schema entsteht und im Agenten steckt.
3. **Compliance.** Eine einzige Durchsetzungsstelle für Authentifizierung, Autorisierung, Validierung und Audit-Log (ISO 27001 A.8.15/A.8.16, BSI C5 OPS-10 ff., IT-Grundschutz OPS.1.1.5) statt dreier.
4. **Automatisierbarkeit.** Infrastructure as Code, GitOps und KI-Agenten sind Bürger erster Klasse.
5. **Testbarkeit.** Jede Funktion ist ohne Browser testbar; Portal- und MCP-Tests prüfen nur die Abbildung.

## Ressourcenmodell

Das Modell lehnt sich an die Kubernetes API Conventions und die Google AIPs (ressourcenorientiertes Design) an – ohne Kubernetes als Fundament.

### Aufbau einer Ressource

Jede Ressource besteht aus drei Teilen:

- **`metadata`**: Name (vom Nutzer gewählt, eindeutig im Elternelement), unveränderliche `uid` (UUIDv7, nie wiederverwendet), URN, Elternelement, Labels (selektierbar) und Annotationen, `generation` (steigt bei jeder Änderung des Sollzustands), `resourceVersion` für optimistische Nebenläufigkeit, Zeitstempel, Finalizer und Eigentümer.
- **`spec`**: der gewünschte Zustand – schreibt der Nutzer.
- **`status`**: der tatsächliche Zustand – schreibt nur das System, über eine eigene Unterressource, die nur Reconcilern offensteht. `observedGeneration` und `conditions` zeigen, ob der Wunschzustand erreicht ist.

Ein verkürztes Beispiel:

```yaml
apiVersion: compute.example.com/v1alpha1
kind: VirtualMachine
metadata:
  name: web-01
  urn: cp:eu-hl1:tenant/acme/project/shop/compute/vm/web-01
  labels: { env: prod }
  generation: 7
spec:
  machineType: small-2c-4g
  arch: any            # arm64 | x86_64 | any
  network: { vpc: default, subnet: web }
status:
  phase: Running
  observedGeneration: 7
  conditions:
    - type: Ready
      status: "True"
```

Felder werden im Schema **klassifiziert**: unveränderlich, nur Ausgabe, Pflicht, *sensitiv* (wird nie zurückgegeben oder protokolliert), personenbezogen (für das Löschkonzept), *nicht vertrauenswürdig* (frei befüllbar durch Mandanten oder Geräte – wird normalisiert und nie als Anweisung oder HTML behandelt) sowie die Datenklasse (Metadaten, Inhalt, IAM, Audit, Abrechnung).

Betreiberobjekte (Knoten, Zelle, Rolle, Adoptionsregel) folgen demselben Aufbau wie Mandantenobjekte. Auch ein **Knoten** ist eine Ressource mit `spec` (Rollen, Labels, Wartungsflag) und `status` (Lebenszyklus-Phase, Hardware-Inventar, Gesundheit).

### Ebenen und Ressourcennamen

Jede Ressource hat genau ein Elternelement. Daraus ergeben sich ein hierarchischer Name und eine global eindeutige **URN**:

```text
cp:global:platform
cp:eu-hl1:region
cp:eu-hl1:cell/c1
cp:eu-hl1:node/n-17
cp:eu-hl1:discovery/d-8c1f2a
cp:global:tenant/acme/project/shop
cp:eu-hl1:tenant/acme/project/shop/compute/vm/web-01
```

- In die URN gehört nur, was sich über die Lebensdauer nie ändert. Zelle, Rack oder Standort sind Eigenschaften, nicht Teil der URN; nur die Zelle selbst und untrennbar zellgebundene Objekte tragen `cell/<c>`.
- Das zweite Segment (Region oder `global`) bestimmt das **Routing**: Jeder Knoten leitet daraus ab, welche Region bzw. Zelle zuständig ist.
- Projekte sind global benannt, ihre Ressourcen liegen regional; der Datenstandort wird per Projekt-Richtlinie (erlaubte Regionen) gesteuert.
- Der REST-Pfad ist direkt aus der URN abbildbar.
- Namen folgen den Regeln für DNS-Labels (Kleinbuchstaben, Ziffern, Bindestrich, 1–63 Zeichen).
- **Berechtigungs-Scopes sind dieselben Pfadpräfixe**: Eine Rollenbindung auf ein Projekt gilt für alles darunter (siehe [Identität](identitaet.html)).

### Versionen

API-Gruppen werden unabhängig versioniert. **Bis zum MVP tragen alle Gruppen `v1alpha1`**; der Weg über `v1beta1` zu `v1` folgt danach. Änderungen am Sollzustand werden als Revisionen für Audit und Rollback vorgehalten (Standard 90 Tage).

## Operationen

### Standardmethoden

| Methode | HTTP | Semantik |
|---|---|---|
| Get | `GET /v1/{name}` | einzelne Ressource |
| List | `GET /v1/{parent}/{kind}` | Paginierung, Filter, Sortierung |
| Create | `POST /v1/{parent}/{kind}?id={name}` | Name vom Client, idempotent wiederholbar |
| Update | `PATCH /v1/{name}` | JSON Merge Patch mit `If-Match` |
| Replace | `PUT /v1/{name}` | vollständiger Sollzustand (GitOps/OpenTofu) |
| Delete | `DELETE /v1/{name}` | asynchron mit Finalizern |

### Aktionen

Alles, was kein reines Setzen eines Feldes ist, ist eine **Aktion** mit eigenem Verb (`POST /v1/{name}:{verb}`), etwa `platform:initialize`, `discovery:adopt`, `node:drain`, `node:decommission`, `cell:split`, `region:rotateCa`, `tenant:suspend` oder `vm:start`. Aktionen sind, wo möglich, **deklarativ unterlegt**: `node:drain` setzt intern das Wartungsflag im Sollzustand – die Aktion ist eine bequeme, auditierbare Absichtserklärung, den Rest erledigt der Reconciler.

### Lang laufende Operationen, Watch und Events

- Jede Mutation, die nicht sofort fertig ist, antwortet mit `202 Accepted` und einer **Operation**-Ressource mit Fortschritt und aktuellem Schritt. Sie lässt sich abfragen, abwarten und abbrechen und ist selbst auditierbar – im Portal als Aufgabenliste, im MCP als Task.
- **Watch** liefert einen Strom von Änderungen (extern als Server-Sent Events, intern als gRPC-Streaming) mit Wiederaufnahme ab einer bekannten Version.

### Idempotenz, Nebenläufigkeit und Dry-Run

- Alle mutierenden Aufrufe akzeptieren einen `Idempotency-Key`; Portal und MCP setzen ihn **immer** – wichtig bei KI-Agenten, die Aufrufe wiederholen.
- Optimistische Nebenläufigkeit über `If-Match` → `412 Precondition Failed` bei Konflikt.
- **Dry-Run für jede Mutation** (`?validateOnly=true`): validiert, prüft Rechte und Kontingente, berechnet Auswirkungen („Drain verschiebt 4 VMs und 2 Volumes“) und ändert nichts.

### Fehlerformat

Alle Fehler werden als `application/problem+json` nach RFC 9457 geliefert – mit stabilem, maschinenlesbarem Code, lokalisiertem Titel und Detail (Deutsch/Englisch), Trace-ID, feldgenauen Verstößen und einem Hinweis, ob ein Wiederholen sinnvoll ist. Das Portal zeigt Feldfehler am Formularfeld; MCP liefert das Problem-Objekt strukturiert zurück, damit ein KI-Agent sich selbst korrigieren kann. Interne Details wie Stacktraces gelangen nie in Fehlermeldungen.

## Protokolle: REST/OpenAPI nach außen, gRPC intern

| | Extern (Nutzer, Portal, MCP, CLI, OpenTofu) | Intern (Agent ↔ Agent, Reconciler) |
|---|---|---|
| Protokoll | HTTPS/JSON, Server-Sent Events für Watch | gRPC über mTLS im WireGuard-Underlay |
| Beschreibung | OpenAPI 3.1 + JSON Schema 2020-12 | Protobuf |
| Authentifizierung | OIDC-Bearer-Token, API-Schlüssel, Setup-Token | Knotenzertifikate plus weitergereichtes Original-Token mit DPoP-Nachweis |

**Eine Quelle:** Die Ressourcentypen werden **einmal als Rust-Typen** definiert. Daraus entstehen OpenAPI, Portal-Formulare, MCP-Tools, CLI und SDKs. Protobuf dient **nur** der internen Knoten-zu-Knoten-Kommunikation; API-Objekte werden darin als versionierte Nutzlast transportiert, nicht als zweites Schema gepflegt. Verworfen wurde Protobuf als Quelle mit HTTP-Transcoding, weil die Werkzeugkette dafür in Rust schwach ist. Die REST-Fassade ist kein zweiter Codepfad: Validierung und Autorisierung laufen an genau einer Stelle (siehe [Rust-Stack](rust-stack.html)).

### Versionierung und Deprecation

- `alpha` kann ohne Frist brechen und ist standardmäßig abgeschaltet; `beta` hat mindestens sechs Monate bzw. zwei Releases Vorlauf; `v1` erlaubt innerhalb der Hauptversion nur rückwärtskompatible Änderungen.
- Für GA-Felder gilt eine **Deprecation-Frist von mindestens 12 Monaten**, angekündigt über `Deprecation`- und `Sunset`-Header, OpenAPI, Changelog, Portal-Banner und Hinweise im MCP.
- Breaking Changes ohne Versionssprung lassen die CI scheitern.
- Bei Rolling Updates wird eine neue API-Version erst aktiviert, wenn alle Mitglieder der Steuerungsgruppe sie unterstützen.

## Ableitung von Portal und MCP aus dem Schema

Aus dem Schema werden OpenAPI und JSON Schema erzeugt; daraus wiederum Portal, MCP-Server, CLI, SDKs, OpenTofu-Provider, Dokumentation und der Paritäts-Check.

### Schema-Annotationen

Die API-Beschreibung trägt alle Informationen, die Portal und MCP brauchen – über projekteigene Schema-Erweiterungen: Ebene, Anzeigetexte (de/en), Eingabeart, **Effekt** (lesen, anlegen, ändern, destruktiv, irreversibel), benötigte Berechtigung, lang laufend ja/nein, Tool-Zuordnung, Kennzeichnung nicht vertrauenswürdiger Felder, Datenklasse sowie Step-up- und Bestätigungspflicht. Daraus ergeben sich Navigation, Formularelemente, Bestätigungsdialoge und sichtbare Schaltflächen im Portal ebenso wie Tool-Beschreibungen, Tool-Hinweise und Bestätigungspflichten im MCP. Ausnahmen von der Ableitung sind nur mit Begründung zulässig; sicherheitsrelevante Annotationen werden per Lint erzwungen.

### Portal

- **Generischer Kern:** Liste, Detail, Formular und Aktionsdialoge werden zur Laufzeit aus OpenAPI und JSON Schema gerendert. Eine neue Ressource erscheint dadurch automatisch im Portal – mit Validierung, Hilfetexten, Rechteprüfung und Dry-Run-Vorschau.
- **Kuratiert, wo sinnvoll:** Für zentrale Abläufe (Ersteinrichtung, Adoption, VPC-Topologie, Knotenkarte) gibt es handgebaute Ansichten. Sie rufen ausschließlich die öffentliche API auf – sie dürfen schöner sein, aber nichts können, was die API nicht kann.
- Das Portal ist eine statische Single-Page-App, im Agenten eingebettet und von **jedem** Knoten ausgeliefert, ohne Backend mit Sonderrechten (Technologie siehe [Portal](portal.html)).

### MCP-Server

Der MCP-Server ist im Agenten eingebaut und auf jedem Knoten über Streamable HTTP erreichbar (zustandslos nach aktueller MCP-Spezifikation); lokal zusätzlich per stdio über die CLI.

**Tool-Schnitt – nicht jeder Endpunkt ein Tool.** Hunderte feingranulare Tools überfordern Sprachmodelle. Stattdessen werden Tools aus den Annotationen gruppiert:

| Tool (Beispiel) | Bündelt |
|---|---|
| `cp_get`, `cp_list`, `cp_search` | alle Lesezugriffe aller Arten |
| `cp_describe_schema` | Schema einer Ressourcenart |
| `cp_apply` | Anlegen, Ändern, Ersetzen beliebiger Arten (mit Dry-Run) |
| `cp_delete` | Löschen (mit Bestätigung) |
| `node_lifecycle` | adoptieren, ablehnen, drainen, stilllegen, neu starten |
| `cluster_topology` | Zelle, Region, Steuerungsgruppe |
| `tenant_admin` | Mandant, Projekt, Nutzer, Rollen, Kontingente |
| `operation_wait` | lang laufende Operationen verfolgen |

- Jedes Tool hat Ein- und Ausgabeschema und liefert strukturierte Daten plus kurze Textzusammenfassung.
- Die Tool-Liste ist **dynamisch**: Sie enthält nur Tools, für die das Token Rechte hat; ein Mandanten-Token sieht keine Knoten-Tools.
- **MCP-Ressourcen** machen Objekte, Events, Inventar und Audit-Log lesend einbindbar; **MCP-Prompts** entsprechen den Portal-Assistenten (z. B. Erstinstallation, Knoten aufnehmen, Projekt anlegen, Störung analysieren).
- Rückfragen und Bestätigungen laufen über Elicitation. Destruktive und irreversible Aktionen, privilegierte IAM-Änderungen und Adoption verlangen eine **Bestätigung auf einer Plattformseite außerhalb des KI-Clients** (Out-of-band).

## Sonderfälle: Bootstrap und Ausfallverhalten

### Der erste Knoten

Beim ersten Knoten gibt es weder Identitätsdienst noch Steuerungsgruppe – trotzdem muss die Einrichtung über alle drei Zugänge funktionieren.

1. Der Knoten startet vom USB-Stick im Zustand **nicht initialisiert** und bietet nur eine Bootstrap-Teilmenge der API an (Plattformstatus, Initialisierung inkl. Dry-Run, Hardware-Info, Netzwerktest).
2. Ein **Einmal-Setup-Token** (128 Bit, 24 h gültig, einmal verwendbar) wird bevorzugt auf lokaler Konsole bzw. HDMI angezeigt. Eine Token-Datei auf dem Stick entsteht erst nach einer lokalen Aktion. Zusätzlich zeigt der Knoten den Fingerabdruck seines vorläufigen TLS-Zertifikats an.
3. Die Initialisierung ist per API, Portal oder MCP mit diesem Token möglich.
4. Sie legt Plattform, Region, Zelle, interne CA, den ersten Betreiber-Admin und einen Wiederherstellungsschlüssel an. Abgesichert wird der Einrichtungskanal über Setup-Token und einen Bestätigungscode. Am Ende entsteht ein einmaliger, kurz gültiger **Admin-Einladungslink**, mit dem unter der endgültigen Portal-Adresse der erste Passkey registriert wird. Anlegen und Einlösen der Einladung sind über MCP ausgeschlossen.
5. Danach ist das Token verbraucht und der Bootstrap-Modus endet unwiderruflich. Der gesamte Vorgang steht als erste Einträge im Audit-Log.

### Adoption neuer Hardware

Entdeckte Hardware erscheint als `Discovery`-Ressource mit Inventar (Architektur, CPU, RAM, Disks, NICs, Seriennummer, TPM- und Secure-Boot-Status). Adoption ist die Aktion `:adopt` bzw. eine Adoptionsregel – beides normale API-Objekte. **Auto-Adopt ist ab Werk aus**; dauerhafte Regeln sind nur mit attestierter Hardware zulässig. Details zum Ablauf beschreibt [Boot & Adoption](boot-adoption.html).

### Jeder Knoten ist Eingang

- **Jeder** Knoten liefert API, Portal und MCP aus. Der DNS-Name der Region zeigt auf mehrere Knoten; im Homelab hilft zusätzlich mDNS.
- Der empfangende Knoten authentifiziert die Anfrage, bestimmt anhand der URN die zuständige Zelle und leitet sie per gRPC an den Raft-Leader (Schreiben) oder ein beliebiges Mitglied (eventuell konsistentes Lesen) weiter. Dabei reicht er das **Original-Token** samt DPoP-Nachweis weiter; **autorisiert wird am Zielort**, nicht aufgrund des Weiterleiters.
- Fällt die zuständige Zelle aus, liefern andere Knoten zwischengespeicherte Daten gekennzeichnet als veraltet und lehnen Schreibzugriffe mit `503` und `Retry-After` ab – nie stilles Verlieren.

## Sicherheit

### Gleiche Prüfkette für alle Zugänge

Jeder Aufruf – REST aus dem Portal, REST aus einem Skript oder ein MCP-Tool – durchläuft dieselbe Kette: **Authentifizierung → Autorisierung → Validierung → Kontingent → Audit → Ausführung**. Identitäten sind Nutzer (OIDC, Passkeys), Dienstkonten, API-Schlüssel und Knoten (mTLS-Zertifikat). Der MCP-Server ist ein OAuth-2.1-geschützter Ressourcenserver; er akzeptiert nur Tokens mit seiner eigenen Audience (keine Token-Weitergabe). Das Portal hat keine Sonderrechte. Details: [Sicherheitsmodell](sicherheitsmodell.html).

### MCP-spezifische Schutzmaßnahmen

| Risiko | Maßnahme |
|---|---|
| KI-Agent handelt mit vollen Nutzerrechten | Eingeschränkte MCP-Tokens, standardmäßig nur lesend, an Projekt/Mandant gebunden, kurze Laufzeit; Betreiberrechte explizit freizuschalten |
| Prompt-Injection über Daten | Fremdbefüllte Felder werden normalisiert und strikt als Daten markiert; Tool-Beschreibungen sind statisch im Binary |
| Destruktive Aktionen, Adoption, IAM-Änderungen | Pflicht-Dry-Run mit **Bestätigungstoken** (an Principal, Aktion, Ziel, Version und Hash aller Parameter gebunden, einmalig, 5 Minuten gültig) **plus Out-of-band-Bestätigung durch einen Menschen** |
| Massenänderungen, Endlosschleifen | Rate-Limits je Token und Kanal, Obergrenzen je Aufruf, Löschschutz-Flag |
| Exfiltration | Ausgabefilter für sensitive Felder; Secrets sind über MCP nie lesbar, nur Referenzen |

Die Bestätigungslogik ist eine **API-Funktion**, keine MCP-Sonderlogik: Portal (Dialog) und Skripte (Token) nutzen denselben Mechanismus. Richtlinien dürfen Bestätigungspflichten nur verschärfen; die Out-of-band-Bestätigung für destruktive Aktionen und Adoption ist **nicht abschaltbar**.

Autonom handelnde KI-Agenten dürfen irreversible Aktionen, privilegierte IAM-Änderungen und Adoptionen grundsätzlich nicht ausführen; destruktive Aktionen nur über eine Freigabeanfrage an einen Menschen.

### Audit-Log

Jede Mutation (und jeder Lesezugriff auf sensible Arten) erzeugt einen unveränderlichen Audit-Eintrag mit Zeit, **Principal** (der Mensch) und getrennt davon **Actor** (z. B. ein KI-Client), Kanal (`api`, `portal`, `mcp`, `cli`, `system`, `bootstrap` – vom Eingang gesetzt, nicht fälschbar), Verb, Ziel, Bestätigungsart, Parameter-Hash, Ergebnis und Änderungsdiff. Die Speicherung ist manipulationssicher (Hash-Kette, Blocksignatur, regelmäßig außerhalb der Zelle verankert), je Mandant getrennt und exportierbar. Das Audit-Log ist selbst eine lesbare API-Ressource.

## Paritätsregel und CI-Prüfung

> **Jede öffentliche API-Operation (Methode × Ressourcenart × Ebene) ist im Portal und im MCP erreichbar – oder explizit mit Begründung ausgenommen.** Ziel für den MVP: null Ausnahmen bei Mutationen.

Die Prüfung erfolgt dreistufig:

1. **Statischer Abgleich bei jedem Änderungsantrag:** Alle Operationen der erzeugten OpenAPI werden mit dem MCP- und dem Portal-Manifest verglichen. Jede Operation muss abgedeckt oder begründet ausgenommen sein, destruktive Operationen müssen im MCP korrekt markiert sein; Sicherheits- und Nachweisoperationen dürfen nie ausgenommen werden. Lücken lassen die CI scheitern.
2. **Laufzeit-Abgleich (nächtlich):** In einem gemischten ARM64/x86-Testcluster wird jedes Szenario dreimal ausgeführt – per HTTP, per Portal-End-to-End-Test und per MCP-Client. Verglichen werden Ergebnis, Fehlercodes, Rechteverhalten und Audit-Eintrag (identisch bis auf den Kanal).
3. **Rechte-Parität:** Für eine Rollenmatrix wird geprüft, dass sichtbare und ausführbare Operationen in allen drei Kanälen übereinstimmen – auch für KI-Agenten.

Ergänzend laufen OpenAPI-Lint, Breaking-Change-Prüfung und generierte Zwei-Mandanten-Isolationstests.

## Beispiel: „Knoten adoptieren“ in drei Zugängen

Ein Pi 5 wurde per Kabel angeschlossen, hat das Discovery-Image gebootet und wartet als `d-8c1f2a`. Ziel: Adoption in Zelle `c1` mit Rolle `storage-object`.

### API

Erst ein Dry-Run, dann die Ausführung mit dem erhaltenen Bestätigungstoken:

```text
POST /v1/regions/eu-hl1/discoveries/d-8c1f2a:adopt?validateOnly=true
Host: api.example.com
Authorization: Bearer …

{ "nodeName": "n-pi5-04", "cell": "c1", "roles": ["storage-object"],
  "confirmationCode": "3817-5520" }

→ 200 OK
{ "valid": true,
  "effects": [ "Knoten erhält Zertifikat der Zelle c1",
               "OS-Image arm64 wird ausgerollt",
               "Rolle storage-object: 512 GiB NVMe werden formatiert" ],
  "confirmationToken": "ct_…" }
```

```text
POST /v1/regions/eu-hl1/discoveries/d-8c1f2a:adopt
Idempotency-Key: 7f0c3a2e-…

{ …gleiche Parameter…, "confirmationToken": "ct_…" }

→ 202 Accepted
Location: /v1/regions/eu-hl1/operations/op-0193f1c4
```

Anschließend wird die Operation abgewartet; Ergebnis ist die neue `Node`-Ressource. Adoption verlangt **immer** eine Bestätigung der Geräteidentität – etwa einen am Gerät abgelesenen Bestätigungscode, ein Einschreibe-Token, eine Vorab-Registrierung oder Attestierung –, über API/CLI zusätzlich Step-up.

### Portal

Ein Badge meldet live „1 neuer Knoten wartet“. Die Detailansicht zeigt Inventar und Hinweise wie „kein TPM“. „Adoptieren“ ist nur mit passendem Recht sichtbar und öffnet ein aus dem Schema erzeugtes Formular (Name, Zelle, passende Rollen, Bestätigungscode). Eine automatische Vorschau (Dry-Run) listet die Auswirkungen inklusive Formatierungswarnung; bestätigt wird per Passkey, danach zeigt eine Fortschrittsanzeige die Operation, bis der Knoten *Aktiv* ist.

### MCP

Nutzeranfrage im KI-Client: *„Nimm den neuen Pi 5 als Objektspeicher in Zelle c1 auf.“*

```yaml
# 1. wartende Hardware suchen
tool: cp_list
arguments: { kind: Discovery, parent: "cp:eu-hl1:region", filter: 'status.phase="Waiting"' }
# 2. Adoption anstoßen (als destruktiv markiert wegen Formatierung)
tool: node_lifecycle
arguments: { action: adopt, target: "cp:eu-hl1:discovery/d-8c1f2a",
             nodeName: n-pi5-04, cell: c1, roles: [storage-object] }
# → Server macht Dry-Run und verlangt Bestätigung auf einer Plattformseite
#   (URL-Elicitation); dort gibt der Mensch den Gerätecode ein und bestätigt per Passkey.
# 3. Fortschritt verfolgen
tool: operation_wait
arguments: { operation: "cp:eu-hl1:operation/op-0193f1c4", timeout: 60 }
```

Der KI-Client sieht weder den Bestätigungscode noch die Bestätigung selbst. Alternativ führt der MCP-Prompt „Knoten aufnehmen“ geführt durch dieselben Schritte.

**Ergebnis in allen drei Fällen:** dieselbe Operation, dieselbe `Node`-Ressource und ein Audit-Eintrag, der sich nur im Kanal und gegebenenfalls im Actor unterscheidet.
