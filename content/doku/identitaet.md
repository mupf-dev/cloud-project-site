title: Mandanten, Identität und Rechte
summary: Hierarchie aus Plattform, Mandant und Projekt, Identitätsarten, Anmeldung mit Passkeys und OIDC-Föderation, hybrides Rechtemodell aus Beziehungsgraph und Cedar, Mandantentrennung, Kontingente, Lebenszyklus und Rezertifizierung.
group: konzept
order: 70
quelle: Konzept 07 (Mandanten-, Identitäts- und Rechtemodell)
---

## Überblick

Die Plattform ist von Grund auf mandantenfähig. Dieses Konzept legt fest, **wer** in der Plattform handelt (Identitäten), **wie** sich diese Identitäten ausweisen (Authentifizierung), **was** sie dürfen (Autorisierung) und wie Mandanten über alle technischen Schichten hinweg voneinander und vom Betreiber getrennt werden.

### Kernentscheidungen

| Thema | Entscheidung |
|---|---|
| Hierarchie | **Plattform → Mandant → Projekt → Ressource**; der Mandant *ist* die Organisation; optionale Ordner, nicht Teil der URN |
| Identitätsdienst | eigener, schlanker OIDC-/OAuth-2.1-Server in Rust, **Passkeys first**, plus Föderation zu Kunden-IdPs |
| Tokens | kurzlebig, sender-gebunden, **lokal** geprüft; sie tragen **Identität, keine Rechte** |
| Autorisierung | eigener Beziehungsspeicher (Zanzibar-artig) **plus Cedar** als eingebettete Policy-Sprache |
| Betreiber und Mandanten | Betreiberrollen sehen Metadaten, nie Inhalte – außer über einen protokollierten Zugriffsantrag |
| Lebenszyklus | Löschung mit **Krypto-Löschung** und signiertem Löschnachweis; Export jederzeit |

## Hierarchie

Der Vergleich mit AWS, Azure und GCP liefert drei Lehren: Fallen Identitäts- und Isolationsgrenze auseinander, wird das Modell schwer verständlich – daher ist **der Mandant beides**. Hierarchische Leitplanken sind für große Kunden unverzichtbar – daher **Leitplanken auf jeder Ebene**. Namen in Pfaden, die bei Umorganisation brechen, sind teuer – daher sind **Ordner nicht Teil der URN**.

### Ebenen

| Ebene | Zweck | Beispiel-URN |
|---|---|---|
| Plattform | Betreiber, globale Policies, Mandantenverwaltung | `cp:global:platform` |
| Region / Zelle / Knoten | Infrastruktur, nur für den Betreiber | `cp:eu-hl1:cell/c1` |
| **Mandant** | Organisation des Kunden mit eigenem IdP, eigenen Schlüsseln und eigener Abrechnung | `cp:global:tenant/acme` |
| *Ordner (optional)* | Gruppierung von Projekten, Vererbung von Rechten und Leitplanken | eigene Ressource, kein Präfix der Projekt-URN |
| **Projekt** | Ressourcen-, Kontingent- und Rechtegrenze, Standortbindung | `cp:global:tenant/acme/project/shop` |
| Ressource | VM, Volume, Bucket … | `cp:eu-hl1:tenant/acme/project/shop/compute/vm/web-01` |

Projektnamen sind je Mandant eindeutig; das Verschieben eines Projekts zwischen Ordnern ändert nur eine Beziehung, nie die URN. Jedes Projekt trägt eine Liste **erlaubter Regionen** – die Grundlage für Datenresidenz. Eine zusätzliche Ebene „Organisation“ wurde verworfen, weil sie für die große Mehrheit der Nutzer (Homelab, KMU) überflüssig wäre und die Frage aufwirft, welche Ebene die Isolationsgrenze ist. Für Reseller und Hoster ist später eine Gruppierung von Mandanten mit delegierten Betreiber-Teilrechten vorgesehen – ohne Zugriff auf Mandanteninhalte und ohne URN-Änderung. Die URN-Konventionen sind unter [API-first](api-first.html) beschrieben.

## Identitäten

### Principal und Actor

Jede Anfrage trägt zwei Angaben: Der **Principal** ist, in wessen Namen und mit wessen Rechten gehandelt wird; der **Actor** ist, wer technisch handelt (Portal, CLI, KI-Client, Reconciler). Das Audit-Log speichert beides getrennt.

| Typ | Heimat | Anmeldung | Typische Laufzeit |
|---|---|---|---|
| Mensch (Betreiber) | Plattform | Passkey (Pflicht), föderiert optional | Sitzung 8–12 h, Access-Token 10 min |
| Mensch (Mandant) | Mandant | Passkey/MFA lokal **oder** föderiert (OIDC/SAML) | wie oben |
| Gruppe | Mandant / Plattform | lokal oder aus dem IdP bzw. per SCIM synchronisiert | – |
| Dienstkonto | Projekt | Workload-Identität, Föderation, API-Schlüssel | Token 5–60 min, Schlüssel höchstens 1 Jahr |
| Workload (VM, Container, Pod) | Ressource | Plattform-Attestierung über die Platzierung | 5–15 min, automatisch erneuert |
| Knoten | Region | mTLS mit Zertifikat der Zellen-CA | Zertifikat 7 Tage, rotiert |
| KI-Agent (Actor) | MCP-Client bzw. Dienstkonto | OAuth 2.1 | höchstens 1 h |
| Break-Glass | Plattform | Offline-Hardware-Schlüssel + Wiederherstellungsanteile | einmalig, höchstens 4 h |

### Menschen und Gruppen

Nutzer existieren **je Mandant**; dieselbe Person in zwei Mandanten hat zwei Identitäten. Das vermeidet Querbezüge zwischen Mandanten und folgt der Datensparsamkeit. Gruppen sind lokal oder aus dem externen IdP gespiegelt und dürfen verschachtelt werden. Die Pflichtattribute sind minimal; die E-Mail-Adresse ist als personenbezogen markiert, die letzte Anmeldung dient der Inaktivitätsprüfung.

### Dienstkonten und Workload-Identitäten

Workload-Identitäten folgen dem SPIFFE-Modell: Pfade innerhalb einer Vertrauensdomäne spiegeln die URN. Infrastruktur- und Workload-Pfade sind fest an **getrennte Zertifizierungsstellen** gebunden; Workloads erhalten nur das Vertrauensbündel der Workload-CA, und ihre Identitäten werden an Infrastruktur-Schnittstellen grundsätzlich abgelehnt.

- Einer VM, Container Instance oder einem Kubernetes-Cluster wird ein Dienstkonto zugeordnet. Dafür ist ein eigenes Recht („actAs“) nötig – so kann niemand seine Rechte ausweiten, indem er eine VM mit einem mächtigeren Dienstkonto startet.
- **Tokens stellt der Agent des Host-Knotens aus**, der die Workload nachweislich platziert hat – die Platzierung in der Steuerungsebene ist die Attestierung. VMs erhalten sie bevorzugt über virtio-vsock, Container Instances als rotierte Datei, Kubernetes-Cluster über Token-Projektion und OIDC-Föderation.
- Jeder Host signiert mit einem **eigenen, kurzlebigen Ausstellerschlüssel** (24 h), der an die Knotenkennung gebunden ist. Prüfer verlangen, dass dieser Schlüssel zu genau dem Knoten gehört, auf dem die Workload laufen soll. Ein kompromittierter Knoten kann daher keine Tokens für fremde Workloads prägen.
- **Föderation eingehend:** Externe Aussteller (CI-Systeme, fremde Kubernetes-Cluster) werden am Projekt registriert; ihre OIDC-Tokens werden per Token Exchange (RFC 8693) gegen ein kurzlebiges Plattform-Token getauscht, unter Bedingungen auf deren Claims. So braucht Automatisierung keine statischen Geheimnisse.

### Knoten

Knoten erhalten bei der [Adoption](boot-adoption.html) ein Zertifikat der Zellen-CA mit ihrer unveränderlichen Kennung. Sie sind **keine** Principals für Mandantenoperationen, sondern handeln mit eng begrenzten Rechten für die Reconciler – etwa nur den Status der auf ihnen platzierten Ressourcen schreiben. Ein kompromittierter Knoten betrifft damit höchstens die Mandanten, die auf ihm laufen. Vertrauensstufen und Attestierung beschreibt das [Sicherheitsmodell](sicherheitsmodell.html).

### KI-Agenten über MCP

KI-Agenten sind ein eigener Actor-Typ in zwei Ausprägungen:

1. **Delegiert:** Ein Mensch autorisiert einen MCP-Client (OAuth 2.1 mit PKCE). Das Token trägt den Menschen als Principal und den Agenten als Actor, mit eingeschränkten Scopes (lesen, schreiben, destruktiv).
2. **Autonom:** Ein Dienstkonto mit Actor-Typ „Agent“, etwa ein nächtlicher Kapazitätsplaner. Destruktive Aktionen laufen dann nur über eine Freigabe durch einen Menschen; irreversible Aktionen, privilegierte IAM-Änderungen, die Adoption von Knoten und die Vergabe kritischer Rollen sind für autonome Agenten verboten.

Effektiv gilt die **Schnittmenge** aus Principal-Rechten, Token-Scopes und Agenten-Leitplanken. Leitplanken sind Verbotsregeln auf Plattform- oder Mandantenebene, etwa „KI-Agenten dürfen nie IAM-Rechte vergeben oder Schlüssel löschen“. Ketten-Delegation ist erlaubt, wird aber vollständig auditiert und in der Tiefe begrenzt.

### Break-Glass

Ein Notfallkonto mit Zugang **außerhalb des IdP** (Hardware-Schlüssel im Tresor plus Wiederherstellungsschlüssel, optional auf mehrere Personen verteilt) funktioniert auch bei Totalausfall des Identitätsdienstes. Es gewährt befristet Betreiber-Admin-Rechte, aber **keinen** Zugriff auf Mandanteninhalte; jede Nutzung löst Alarm, Nachbetrachtung und Rotation aus.

## Authentifizierung

### Eigener Identitätsdienst plus Föderation

Zitadel, Keycloak oder Kanidm einzubetten hätte eine zweite zentrale Datenhaltung, teils fehlende Pi-Tauglichkeit, Lizenzrisiken und eine doppelte Pflege des Mandantenmodells bedeutet; reine Föderation würde keinen Betrieb ohne externen IdP erlauben. Gewählt ist die Kombination aus **eigenem, bewusst schmalem Autorisierungsserver** und **Föderation**:

- OIDC/OAuth 2.1 mit Authorization Code + PKCE, Refresh, Client Credentials, Token Exchange, Device Authorization (für die CLI auf Geräten ohne Browser), Discovery, JWKS und Protected Resource Metadata für MCP.
- Lokale Anmeldung standardmäßig **nur mit Passkeys**; Passwörter sind optional und aus.
- **Föderations-Broker** je Mandant zu beliebigen Kunden-IdPs per OIDC oder SAML, mit Gruppenabbildung und SCIM-2.0-Provisionierung.
- **Kein** vollwertiges Kundenidentitätsmanagement mit Registrierungsabläufen oder Social Logins – wer das braucht, föderiert einen spezialisierten IdP. Zitadel, Keycloak oder Kanidm sind dafür erstklassige externe IdPs.

Abgesichert wird der Eigenbau durch die OpenID-Konformitätssuite in der CI, Fuzzing der Parser und ein externes Audit vor der allgemeinen Verfügbarkeit.

### MFA, Passkeys, Step-up

- **Passkeys first** (WebAuthn); für Betreiber und privilegierte Rollen können gerätegebundene, attestierte Schlüssel erzwungen werden.
- MFA ist für alle privilegierten Rollen Pflicht. Bei Föderation prüft die Plattform, ob der externe IdP MFA belegt; fehlt der Nachweis, fordert sie einen eigenen Passkey als zweiten Faktor.
- **Step-up:** Irreversible Aktionen und Änderungen an privilegierten Rollen verlangen eine frische Anmeldung (höchstens 10 Minuten alt), unabhängig vom Kanal. Über MCP bestätigt der Mensch solche Aktionen auf einer **Plattformseite**, die den Auswirkungsbericht selbst darstellt und Passkey-Anwesenheit verlangt. Die Bestätigung ist an alle Parameter gebunden und nur einmal gültig. Mandanten dürfen diese Pflicht verschärfen, nicht abschalten.
- Progressive Sperren nach Fehlversuchen und Benachrichtigung bei neuen Geräten.

### Tokens

- **Access-Token** als JWT nach RFC 9068, signiert mit ES256 (im kompatiblen Kryptoprofil auch Ed25519), Laufzeit 10 Minuten für Menschen, Zielgruppe ist ein konkreter Endpunkt.
- **Sender-Bindung** mit DPoP für CLI, SDKs und MCP-Clients, mTLS für Workloads; das Portal nutzt eine HttpOnly-Cookie-Sitzung.
- **Keine Rollen, Gruppen oder Rechte im Token** – sie werden bei jeder Anfrage aus dem aktuellen Rechtestand ermittelt. Entzug wirkt sofort, das Token bleibt klein.
- Refresh-Tokens rotieren und sind an die Sitzung gebunden; eine Wiederverwendung widerruft die Sitzung.

**API-Schlüssel** gibt es nur für Dienstkonten, nie für Menschen. Sie tragen ein erkennbares Präfix für Secret-Scanner, werden nur als Hash gespeichert, haben eine Pflicht-Ablaufzeit (Standard 90 Tage, höchstens ein Jahr) und lassen sich auf Scopes, Quellnetze und Projekte einschränken. Empfohlen ist, sie gegen ein kurzlebiges Token zu tauschen; Mandanten können API-Schlüssel per Richtlinie ganz verbieten.

### Dezentrales Verhalten bei Ausfällen

Jeder Knoten hält die öffentlichen Schlüssel aller Aussteller und die Sperrliste lokal repliziert. Ein Eingangsknoten prüft das Token und leitet die Anfrage an die zuständige Zelle weiter; diese **prüft das Original-Token samt DPoP-Nachweis selbst** und vertraut nie einem vom Eingangsknoten erzeugten Nutzerkontext.

| Ausfall | Verhalten |
|---|---|
| Identitätsdienst einer Region nicht erreichbar | bestehende Tokens bleiben bis Ablauf gültig; neue Anmeldungen scheitern mit Hinweis im Portal; Workload-Tokens stellt der Host weiterhin aus |
| Externer IdP eines Mandanten fällt aus | keine neuen föderierten Anmeldungen; bestehende Sitzungen laufen bis zur maximalen Dauer; optional lokale Notfall-Admins des Mandanten |
| Zelle ohne Quorum | Lesen mit Kennzeichnung „veraltet“, Rechteänderungen nicht möglich (fail-closed) |
| Signaturschlüssel kompromittiert | Rotation, alter Schlüssel verschwindet aus dem JWKS; kurze Exposition dank 10-Minuten-Tokens |

Mehrere Identitätsknoten signieren jeweils mit **eigenem** Schlüssel unter einem gemeinsamen Aussteller; alle öffentlichen Schlüssel liegen im replizierten Zustand. So ist kein Schlüsseltransport nötig, und laufende Anmeldungen, Codes und Sitzungen funktionieren über Knotengrenzen hinweg. Der Widerruf von Sitzungen erreicht alle Knoten einer Region in wenigen Sekunden. Beim allerersten Start (ohne IdP) richtet ein Einmal-Token den ersten Betreiber-Admin samt Passkey ein; dieser Bootstrap-Zugang wird nach der ersten erfolgreichen Passkey-Anmeldung automatisch deaktiviert.

## Autorisierung

### Anforderungen

Rollenbasierte Rechte entlang der Hierarchie, **Beziehungen quer zur Hierarchie** (Image-Freigabe an ein anderes Projekt, VPC-Peering, Ordnerzugehörigkeit), Bedingungen (Kanal, Actor-Typ, MFA-Frische, Labels, Uhrzeit), **Leitplanken mit Vorrang von Verboten**, dezentrale Auswertung in unter einer Millisekunde ohne externen Dienst, Erklärbarkeit („Warum darf ich das?“) und Analyse („Wer hat Zugriff auf X?“) – und Konsistenz: Nach einem Rechteentzug darf keine ältere Sicht mehr Zugriff gewähren.

### Optionen

Verglichen wurden OpenFGA, Cedar, OPA/Rego, SpiceDB und ein eigener Zanzibar-artiger Kern. OpenFGA hat das passendste Modell, aber die falsche Betriebsform: einen separaten Dienst mit eigener Datenbank. Cedar ist als eingebettete Policy-Sprache ideal, modelliert große Beziehungsgraphen aber nicht selbst. Ein reines Eigenbau-Policy-System wäre teuer und für Prüfer schwer nachvollziehbar.

### Gewählt: Beziehungsspeicher plus Cedar

1. **Graph-Auflösung im eigenen Rust-Kern:** Beziehungen werden als Tupel „Objekt#Relation@Subjekt“ gespeichert, etwa Gruppenmitgliedschaften, Ordnerzugehörigkeit oder Freigaben. Rollenbindungen sind spezielle Tupel. Das Typschema wird **aus dem API-Schema abgeleitet**, es gibt keine zweite Modellpflege.
2. **Cedar-Auswertung:** Mit dem gelieferten Ausschnitt (Principal mit Gruppen, Zielressource mit Vorfahren und Labels, effektive Rollen) wertet Cedar eine Policy-Menge aus: generierte Erlaubnisse je Rolle, Verbots-Leitplanken aller Ebenen und optionale Bedingungen an Rollenbindungen.
3. **Ergebnis mit Begründung**, welche Bindung erlaubte oder welche Regel verbot – für das Audit und für die API-Operationen „Rechte testen“ und „Zugriff erklären“.

Die Autorisierung findet **am Zielort** statt: Die zuständige Zelle entscheidet. Jede Zelle hält eine Lesereplik der Rechte der Mandanten, die bei ihr Ressourcen haben. Eingangsknoten nutzen einen Rechte-Cache nur für die Oberfläche (Schaltflächen ausblenden, Werkzeuglisten im MCP), nie für die eigentliche Entscheidung. **Rechteentzüge werden synchron** an alle betroffenen Zellen repliziert, bevor die Operation als erledigt gilt; Gewährungen dürfen asynchron sein. Fällt eine Zelle aus, entscheidet niemand stellvertretend über ihre Ressourcen.

### Rechte und Rollen

Rechte folgen dem Schema `<api-gruppe>.<ressourcen>.<verb>`, etwa `compute.vms.create` oder `iam.roleBindings.create`. Jede API-Operation deklariert genau ein Recht und eine **Datenklasse**: `metadata`, `content` (Volumes, Objekte, Konsolen, Workload-Logs, Secret-Werte), `iam`, `billing` oder `audit`.

| Rolle | Scope | Kern |
|---|---|---|
| Betreiber-Admin | Plattform | Infrastruktur, Knoten, Mandanten, Kontingente – **keine** Inhaltsrechte |
| Betreiber-Leser / -Sicherheit / -Abrechnung | Plattform | Lesen, Audit und Zugriffsanträge, Verbrauch |
| Mandanten-Admin | Mandant | alles im Mandanten inklusive IAM und IdP; MFA Pflicht |
| Projekt-Owner / -Editor / -Viewer | Projekt oder Ordner | abgestufte Rechte; Viewer ohne Inhalt, etwa für KI-Agenten |
| Auditor, Sicherheit, Abrechnung | Mandant | Audit und Berichte, Leitplanken und Rezertifizierung, Verbrauch |
| Dienst-Rollen | Projekt / Ressource | feingranular für Dienstkonten |

Mandanten können **eigene Rollen** aus Rechten bilden, die sie selbst besitzen. Unverträgliche Rollenkombinationen (Funktionstrennung, etwa Admin und Auditor für dieselbe Person) werden gewarnt oder abgelehnt. Neue Mitglieder erhalten keine Standardrolle, Dienstkonten starten ohne Rechte, und statt dauerhafter Admin-Bindungen gibt es **Just-in-Time-Erhöhungen** mit Ablaufzeit und optionaler Genehmigung. Der root-nahe Zugang auf Knoten ist ein eigenes Recht, das in keiner vordefinierten Rolle steckt und nur personenbezogen vergeben wird.

## Mandantentrennung über alle Schichten

Grundsätze: Der **Mandant ist die harte Grenze**, das Projekt die weiche. Jede Anfrage wird am Ziel gegen den Mandanten der Ziel-URN geprüft. Es gilt default-deny, und Isolation entsteht durch Technik (Kryptografie, Kernel- und Hypervisor-Grenzen), nicht nur durch Prüfcode. Fehler, Listen, Metriken und Logs enthalten keine mandantenfremden Daten.

| Schicht | Trennung |
|---|---|
| API / Steuerung | Mandant aus der URN, Autorisierung am Ziel, gefilterte Listen, Rate-Limits und Kontingente je Mandant |
| Identität | Nutzer, Gruppen, IdPs und verifizierte Domains je Mandant |
| Netz | eigene VPCs, keine L2-Nachbarschaft – nicht einmal innerhalb eines VPC (siehe [Netzwerk](netzwerk.html)) |
| Compute | VMs und Container Instances nur MicroVM-isoliert, kein geteilter Kernel zwischen Mandanten; optional exklusive Knoten |
| Speicher | Verschlüsselung je Volume und Bucket mit Mandanten-Schlüsselhierarchie, Namensräume je Mandant (siehe [Speicher](speicher.html)) |
| Schlüssel | je Mandant ein Schlüsselverschlüsselungsschlüssel als Wurzel der Krypto-Löschung, optional BYOK/HYOK (siehe [Kryptografie](kryptografie.html)) |
| Logs / Audit | getrennte Audit-Ketten je Mandant; Workload-Logs sind Mandanteninhalt |

### Betreiber und Mandantendaten

Der Betreiber ist Auftragsverarbeiter. **Kein Betreiber-Recht trägt die Datenklasse `content`**, und eine Plattform-Leitplanke verbietet Inhaltszugriffe ohne gültige Freigabe. Auch Metadaten sind beschränkt: Namen, Labels und Beschreibungen von Mandantenressourcen erscheinen in Betreibersichten standardmäßig pseudonymisiert. Diese Sperre wirkt auf API-Ebene; gegen root- oder physischen Zugriff auf einen Host schützt sie ohne Confidential Computing nicht. Das wird Mandanten offen dargelegt, und interaktive Sitzungen auf Knoten werden aufgezeichnet, auditiert und am Knoten sichtbar markiert.

**Zugriffsanträge (`AccessRequest`):** Braucht der Betreiber Inhaltszugriff – etwa auf die serielle Konsole einer VM –, stellt er einen Antrag mit Begründung, Umfang, Rechtsgrundlage und Dauer. Standardmäßig genehmigen Mandant **und** Betreiber-Sicherheit (Vier-Augen). Bei gesetzlicher Pflicht oder Notfall ohne Mandantenfreigabe sind eine dokumentierte Grundlage, nachträgliche Benachrichtigung und ein Pflicht-Review nötig. Während der Laufzeit entsteht eine eng begrenzte, befristete Bindung; jede Aktion erscheint im **Mandanten-Audit**. Mandanten können zustimmungsbasierte Anträge per Richtlinie ganz ablehnen.

**Leitplanken** gibt es auf jeder Ebene: auf Plattformebene etwa „kein Inhaltszugriff“ oder „MFA-Pflicht für Admins“, auf Mandanten-, Ordner- und Projektebene etwa „keine öffentlichen IPs in Produktion“ oder „KI-Agenten nur lesend“. Leitplanken sind API-Ressourcen, lassen sich vorab validieren und per Analyse auf Widersprüche prüfen.

## Kontingente und Limits

Der Betreiber setzt Kontingente je Mandant (vCPU, RAM, Speicher, öffentliche IPs, GPUs, Projekte), der Mandanten-Admin verteilt sie auf Ordner und Projekte. Hinzu kommen Grenzen für IAM-Objekte und API-Rate-Limits je Principal, Kanal (MCP strenger) und Mandant. Kontingente liegen im Raft-Zustand der Region; Zellen erhalten **vorab zugeteilte Kontingentscheiben**, damit das Anlegen ohne regionsweite Koordination funktioniert. Überschreitungen liefern einen klaren Fehler, ein Dry-Run zeigt die Auswirkung vorab. Erhöhungen werden als Antrag gestellt und vom Betreiber oder automatisch bis zu einer Schwelle genehmigt. Budgets und Warnschwellen sind von harten Kontingenten getrennt.

## Lebenszyklus

Ein Mandant durchläuft die Zustände **Angelegt → Aktiv → (Gesperrt) → Kündigung → Löschung → Gelöscht**.

| Phase | Wirkung |
|---|---|
| Anlage | Mandantenschlüssel, Audit-Kette, Standard-Leitplanken und Einladung des Erst-Admins entstehen automatisch; der Betreiber erhält **keine** Rolle im neuen Mandanten |
| Gesperrt | abgestuft: nur lesen, Workloads angehalten oder Anmeldung nur noch für Export und Audit; Grund im Mandanten-Audit sichtbar |
| Kündigung | Änderungen gesperrt, Export weiter möglich, Wiederherstellung innerhalb der Frist (Standard 30 Tage) |
| Export | jederzeit: Ressourcendefinitionen (wieder einspielbar), IAM-Konfiguration, signiertes Audit-Log, Inhalte in Standardformaten |
| Löschung | Workloads stoppen → Mandantenschlüssel vernichten (**Krypto-Löschung**, auch in Backups wirksam) → physische Freigabe → IAM-Objekte löschen → Audit-Kette abschließen |
| Löschnachweis | signiertes Zertifikat mit Zeitpunkten, vernichteten Schlüsselkennungen und betroffenen Speicherbereichen; Audit-Einträge werden nach Frist pseudonymisiert, nicht gelöscht |

Projekte haben einen vereinfachten Lebenszyklus mit Soft-Delete-Frist und Löschschutz. Nutzer werden per einmaligem Link eingeladen; bei föderierten Nutzern führt der externe IdP – eine Deaktivierung per SCIM entzieht den Zugriff sofort, ohne SCIM sperrt längere Inaktivität das Konto.

## Rezertifizierung und Audit

**Rezertifizierungskampagnen** sind API-Ressourcen je Mandant, Projekt oder Plattform. Privilegierte Rollen und Betreiberrollen werden standardmäßig alle 90 Tage geprüft, übrige alle 180 Tage. Hilfen sind die letzte Nutzung je Bindung, Vorschläge zum Verkleinern von Rollen, verwaiste Dienstkonten und Verstöße gegen die Funktionstrennung. Nicht bestätigte Bindungen werden nach Frist automatisch entfernt; der Ergebnisbericht ist signiert exportierbar. KI-Agenten dürfen Kampagnen vorbereiten, entscheiden aber nur Menschen.

**Audit** erfasst neben allen Änderungen auch Anmeldungen, Step-ups, Token-Ausgaben und -Tausch, IAM-Änderungen mit Begründung, Autorisierungs-Ablehnungen (aggregiert), den vollständigen Verlauf von Zugriffsanträgen, Break-Glass-Nutzung, Diagnosesitzungen und Lebenszyklus-Ereignisse. Audit ist **nicht abschaltbar**; Mandanten können die Aufbewahrung nur verlängern. Der Betreiber sieht das Plattform-Audit, nicht das Mandanten-Audit – außer Einträgen, die sein eigenes Handeln betreffen.

Alle IAM-Objekte sind gewöhnliche API-Ressourcen und in API, Portal und MCP gleichwertig nutzbar (siehe [Portal](portal.html)). Ergänzend gibt es Hilfsoperationen zum Testen von Rechten, zum Erklären einer Entscheidung und zum Auflisten aller Principals mit Zugriff. Die Zuordnung zu ISO 27001, C5 und DSGVO ist unter [Compliance-Anforderungen](compliance-anforderungen.html) und [Compliance by Design](compliance-by-design.html) beschrieben.
