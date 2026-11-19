title: Boot und Adoption
summary: Wie Knoten in die Plattform kommen – erster Knoten per USB-Stick, weitere per Netzboot, Boot-Dienst ohne Single Point of Failure, Discovery-Quarantäne, abgesicherte Adoption sowie Ablehnen, Stilllegen und Ersatz.
group: konzept
order: 50
quelle: Konzept 08 (Boot- und Adoptionskonzept)
---

## Überblick

Ein Knoten gelangt auf genau zwei Wegen in die Plattform: Der **erste Knoten** startet vom USB-Stick oder einer SD-Karte und richtet die Plattform ein; **jeder weitere Knoten** bootet über das Netz (oder notfalls ebenfalls vom Stick), wird als unbekannte Hardware entdeckt, landet in einer Quarantäne und wird erst durch eine ausdrückliche **Adoption** zu einem vollwertigen Mitglied.

Ablauf in Kurzform:

1. Start per USB/SD, PXE, UEFI HTTP Boot, Raspberry-Pi-Netboot oder über das BMC eines Servers.
2. Das Discovery-System läuft im Arbeitsspeicher, sammelt ein Hardware-Inventar und meldet sich beim Boot-Dienst – Zustand **„wartend“**, in Quarantäne.
3. Ein Mensch oder eine Regel adoptiert den Knoten.
4. Der Knoten installiert das OS lokal (Standard) oder läuft diskless aus dem Netz, erhält sein Zertifikat, tritt dem Cluster bei und übernimmt Rollen.

### Kernentscheidungen

| Thema | Entscheidung |
|---|---|
| Image | **ein Universal-Image je Architektur** für Ersteinrichtung, Discovery/Installer und Betrieb (siehe [OS-Image](os-image.html)) |
| Boot-Dienst | eigene Rust-Implementierung in einem **Sandbox-Prozess ohne Zugriff auf den Knotenschlüssel**; **proxyDHCP** statt DHCP-Ersatz; aktiv-aktiv auf mindestens zwei Knoten |
| Integrität | alle Boot-Artefakte signiert; mit Secure Boot ein eigener, mit dem Schlüssel der Installation signierter iPXE-Build |
| Quarantäne | zweistufig: optional eigenes VLAN, **immer** kryptografisch |
| Adoption | manuell oder per Regel, abgesichert durch Bestätigungscode, TPM-Attestierung, Einschreibe-Token oder Adoptionsfenster; MAC-Abgleich nie allein |
| Schlüssel | der private Knotenschlüssel **verlässt nie den Knoten**; Zertifikate gelten 7 Tage |

## Der erste Knoten

### Medien

| Plattform | Medium | Bemerkung |
|---|---|---|
| amd64 (Notebook, Mini-PC, Server) | Hybrid-Image für USB-Stick, ISO für virtuelle Medien des BMC | UEFI- und BIOS-bootfähig |
| arm64 mit UEFI | Image bzw. ISO | nur UEFI |
| Raspberry Pi 4/5 | Image für SD-Karte, USB oder NVMe | mit gängigen Imager-Werkzeugen schreibbar |

Dasselbe Image dient später als Rückfallmedium für weitere Knoten: Findet es im Netz bereits einen Boot-Dienst oder eine Plattform-API, bietet es „Dieser Plattform beitreten“ an; eine neue Plattform legt es nur auf ausdrückliche Wahl an der Konsole an. Kopflose Geräte entscheiden automatisch.

### Ablauf der Ersteinrichtung

1. Der Betreiber steckt den Stick ein und schaltet das Gerät ein. Es holt sich eine Adresse vom vorhandenen Router und sucht nach einer Plattform.
2. Wird keine gefunden, erzeugt es ein **Einmal-Setup-Token** und einen TLS-Fingerabdruck und zeigt beides an der Konsole an (zusätzlich als Datei auf dem Stick).
3. Mit dem Token öffnet der Betreiber den **Einrichtungsassistenten** in Portal, API oder MCP.
4. Der Assistent erkundet das Netz und schlägt eine Konfiguration vor; anschließend legt die Plattform CA, Plattform, Region und erste Zelle an, startet Raft mit einem Mitglied und aktiviert die Rollen Steuerung, Identität und Boot.
5. Das OS wird auf die gewählte Platte installiert, der Knoten startet neu von der Platte.
6. Der Betreiber erhält einen einmaligen Einladungslink und den Fingerabdruck der Root-CA. Unter der endgültigen Portal-Adresse registriert er den **ersten Admin-Passkey**.

Der Assistent ist die geführte Form einer einzigen API-Operation, damit API und MCP gleichwertig bleiben (siehe [API-first](api-first.html)). Er führt durch Hardware-Eignung, Netzerkundung (vorhandener DHCP, konkurrierende PXE-Dienste, VLANs, DNS, Zeitquellen), Namen, ersten Admin und Portal-Adresse, Installationsziel, Boot-Dienst, Adoptionsrichtlinie (Standard: manuell mit Bestätigungscode) und einen Dry-Run; am Ende werden Wiederherstellungsanteile und Einladungslink einmalig angezeigt. Für die Portal-Adresse stellt die Plattform aus ihrer eigenen CA ein Serverzertifikat aus, dessen Schlüssel den Knoten nie verlässt; es wird automatisch erneuert. Öffentliche Zertifikate sind über einen vorgelagerten Reverse-Proxy möglich.

### Übergang zum Cluster

Bis zum zweiten Knoten ist der erste Knoten bewusst ein Single Point of Failure – das Portal weist darauf hin. Mit dem zweiten geeigneten Knoten verteilt die Rollenregel den Boot-Dienst dorthin und befüllt dessen Artefakt-Cache. Ab drei Knoten überleben Boot, API, Portal und MCP den Ausfall eines Knotens. Der Stick wird nicht mehr gebraucht und bleibt als Rettungsmedium nutzbar.

## Netzboot weiterer Knoten

### proxyDHCP

Im Homelab vergibt meist ein vorhandener Router die Adressen und kennt keine PXE-Optionen. Der Boot-Dienst arbeitet deshalb als **proxyDHCP**: Er beantwortet nur Anfragen mit Boot-Kennung, ohne Adressen zu vergeben; der Client kombiniert die Adresse des echten DHCP-Servers mit den Boot-Angaben des Proxys. Abhängig von der gemeldeten Architektur liefert er:

PXE-Clients (BIOS und UEFI) erhalten iPXE per TFTP, UEFI-HTTP-Clients eine URL zu iPXE, iPXE selbst die URL seines Skripts und der Pi-Bootloader seine spezifische Kennung. Antwortet im Segment bereits ein anderer PXE-Dienst, meldet der Boot-Dienst einen **Konflikt** und bedient standardmäßig nur noch bekannte Clients – eine bestehende PXE-Umgebung bleibt nutzbar. Ein eigener DHCP-Vollmodus ist nur auf einer dedizierten Schnittstelle zulässig, nach Prüfung, dass dort kein anderer DHCP antwortet. Netzboot über IPv6 gehört nicht zum MVP.

### iPXE und UEFI HTTP Boot

iPXE ist die einheitliche zweite Stufe für x86 und arm64-UEFI und wird als eigenständiges Binärartefakt ausgeliefert, nicht gelinkt (siehe [Lizenz-Governance](lizenz-governance.html)).

- **Eigener Build je Installation:** Er wird automatisch bei der Ersteinrichtung und bei jedem Wechsel der Boot-CA reproduzierbar gebaut, enthält die Boot-CA der Installation als Vertrauensanker und prüft jedes nachgeladene Image gegen eine Signatur. Mit Secure Boot ist er mit dem eigenen db-Schlüssel der Installation signiert – eigene Platform-, KEK- und db-Schlüssel statt eines fremden Shims.
- **Upstream-signierter iPXE-Shim:** nur als Rückfall für Geräte, deren Firmware keinen Setup Mode erlaubt; im erhöhten Schutzprofil unzulässig und mit niedrigerer Vertrauensstufe.

Das vom Boot-Dienst erzeugte **iPXE-Skript** ist der Entscheidungspunkt; es enthält keine Geheimnisse und ist signiert. Bei **UEFI HTTP Boot** lädt die Firmware entweder iPXE (Standard) oder direkt ein signiertes Unified Kernel Image der Discovery-Stufe.

### Raspberry Pi 4/5

Raspberry Pi 4 und 5 booten aus einem Bootloader im EEPROM, der Netboot über TFTP und – mit signierten Images – über HTTP beherrscht; der Pi 5 kann zusätzlich HTTPS mit eigener CA. Fabrikneue Geräte haben das Netz aber nicht in der Bootreihenfolge. Die Plattform liefert daher ein kleines **Vorbereitungs-Image**, das die EEPROM-Konfiguration einmalig schreibt; alternativ bootet der Pi einmal das Universal-Image vom Medium und der Agent stellt das EEPROM nach der Adoption um.

| Variante | Integrität | Einsatz |
|---|---|---|
| TFTP | keine Prüfung durch die Firmware, niedrigste Vertrauensstufe | Einstieg, Kompatibilität |
| **HTTP signiert** (Ziel) | Firmware prüft die Signatur, Pi 5 zusätzlich HTTPS | Homelab und RZ |
| Pi-Secure-Boot | Firmware startet nur signierte Images; Schlüssel fest im OTP – **irreversibel** | nur auf ausdrücklichen Wunsch |
| USB/SD | Image-Signatur | Rückfall |

Weil der Pi seine Seriennummer schon in der ersten Boot-Anfrage nennt, kann der Boot-Dienst den Discovery-Eintrag sehr früh anlegen, und Vorab-Registrierungen greifen sofort.

### Weitere Geräte

- **Arm64-Server mit UEFI** verhalten sich wie x86-UEFI.
- **Notebooks ohne PXE:** ein winziger **Netboot-Stick**, der nur iPXE enthält und alles Weitere aus dem Netz lädt. Ohne Netz zum Boot-Dienst startet das Universal-Image vom Stick und meldet sich über ein geroutetes Netz.
- **Server mit BMC:** Über Redfish liest die Plattform das Inventar, legt automatisch eine Vorab-Registrierung an, setzt einen einmaligen Netzboot und schaltet ein – oder hängt das Universal-ISO als virtuelles Medium ein. Zugangsdaten liegen nur als Secret-Referenz vor, der Zugriff erfolgt ausschließlich aus dem Out-of-Band-Netz.
- **Zeitbudget:** Von „Einschalten“ bis „wartend“ vergehen auf x86 und beim Pi mit HTTP-Boot etwa 0,5 bis 1,5 Minuten, mit TFTP auf dem Pi 1 bis 3 Minuten – Ziel ist höchstens 5 Minuten.

## Der Boot-Dienst

### Komponenten

Alle Bestandteile laufen in einem eigenen Sandbox-Prozess (`cp-bootd`) mit eigenem Benutzer, minimalen Rechten und eigener Dienstidentität – **ohne Zugriff auf den Knotenschlüssel**, Gossip-Geheimnisse oder das KMS. Nur dieser Prozess hält den Schlüssel, mit dem Boot-Skripte signiert werden.

Bestandteile sind proxyDHCP (mit Ratenbegrenzung), ein nur lesender TFTP-Server für Erststufen, ein HTTP(S)-Server für inhaltsadressierte, signierte Artefakte, der Skriptgenerator, der Discovery-Eingang und die **Boot-Projektion** – ein lokaler, replizierter Lesestand „bekannte Hardware → Aktion“ ohne Mandantendaten. Alle Parser sind Fuzzing-Ziele.

### Replikation ohne Single Point of Failure

- **Aktiv-aktiv:** Alle Boot-Knoten beantworten Broadcasts, der Client nimmt das erste Angebot. Fällt ein Knoten mitten im Boot aus, wiederholt die Firmware; das iPXE-Skript nennt zudem alle Boot-Knoten als Ausweichziele.
- **Platzierung:** mindestens zwei Boot-Knoten in verschiedenen Ausfallzonen mit Zugang zum Boot-Segment.
- **Zustand:** Entscheidungen lesen nur die Boot-Projektion; neue Discovery-Einträge werden idempotent über den Raft-Leader geschrieben.
- **Ohne Quorum:** Bekannte Knoten booten mit dem zuletzt bekannten Profil weiter – wichtig etwa für Diskless-Knoten nach einem Stromausfall. Neue Meldungen werden gepuffert, Adoptionen sind ohne Quorum nicht möglich.

### Artefakte und Herkunft

Alle Artefakte stammen aus **signierten Release-Manifesten** und werden entweder aus dem Release-Repository, von anderen Boot-Knoten über das Underlay oder per Offline-Import (Air-Gap) bezogen. **Jeder** Boot-Knoten prüft Signatur, Hash und Versions-Monotonie, bevor er ein Artefakt ausliefert. Welche Version ausgeliefert wird, bestimmt der Sollzustand der Region; zu jedem Artefakt gehört eine SBOM. Details unter [Release-Bündel](release-buendel.html) und [Release-Signatur](release-signatur.html).

### Entscheidung je Boot-Anfrage

| Zustand des Geräts | Antwort |
|---|---|
| unbekannt | Discovery-Image, Eintrag „entdeckt“ anlegen |
| wartend | erneut Discovery-Image |
| abgelehnt | kein Angebot bzw. lokaler Boot; Ereignis, optional Alarm |
| installierter Knoten | „lokal booten“ |
| Diskless-Knoten | signiertes OS-Image aus dem Netz |
| Neuinstallation angefordert | Installer |
| stillgelegt | wie unbekannt, mit Verweis auf den früheren Knoten |

Für Server empfiehlt sich „Netz zuerst“ (zentrale Steuerung von Neuinstallation und Rettung, Rückfall auf lokal), für den Pi „lokal zuerst, Netz als Rückfall“, weil sein Bootloader keinen Befehl „lokal booten“ aus dem Netz kennt.

## Was gebootet wird

| Betriebsart | Inhalt | Persistenz |
|---|---|---|
| **Discovery / Installer** | Kernel und Initramfs, Agent im eingeschränkten Modus, Inventarwerkzeuge – kein SSH, kein Login | nur RAM; schreibt erst nach der Adoption im Installationsmodus auf Platten |
| **Diskless** | unveränderliches OS aus dem Netz, lokaler Zustand im RAM oder auf verschlüsselter Scratch-Platte | Identität dauerhaft nur mit TPM bzw. Pi-Geräteschlüssel |
| **Lokale Installation** (Standard) | A/B-Partitionen auf Platte, verschlüsselte Zustandspartition | dauerhaft; Pflicht für Steuerungs- und Speicherrollen |

### Hardware-Steckbrief

Der Discovery-Eintrag enthält ein Inventar: Identität (SMBIOS-UUID, Seriennummer, Hersteller, Modell), CPU, RAM und Virtualisierungsfähigkeit, Datenträger mit Seriennummern und SMART-Zusammenfassung, Netzschnittstellen mit LLDP-Nachbar und Boot-Pfad, Firmware-Stände, Sicherheitsmerkmale (Secure Boot, TPM, Pi-Secure-Boot) sowie eine Bewertung der Rolleneignung und der zu erwartenden Vertrauensstufe.

**Gerätegelieferte Felder sind Daten, keine Anweisungen:** Freitexte wie Modell oder Firmware-Strings werden als nicht vertrauenswürdig markiert, normalisiert und über MCP nur strukturiert ausgegeben. Eignung und Vertrauensstufe werden nie allein aus der Selbstauskunft abgeleitet. Die **Discovery-ID** wird aus stabilen Hardwaremerkmalen abgeleitet, sodass Neustarts keine Dubletten erzeugen.

### Discovery-Phasen

**Entdeckt → Inventarisiert → Wartend → Adoptierend → Adoptiert.** Greift eine Regel, geht es direkt von „inventarisiert“ zu „adoptierend“. Aus „wartend“ kann ein Gerät abgelehnt (und später wieder entsperrt) werden; Einträge, die über 30 Tage nicht gesehen wurden, gelten als verwaist und werden bereinigt.

## Discovery-Quarantäne

| Stufe | Mechanismus | Schutzwirkung |
|---|---|---|
| **Q1 Netz** (wo möglich) | eigenes Boot-/Discovery-VLAN; Underlay und Management als getaggte VLANs, die erst der adoptierte Knoten konfiguriert | verringert die Angriffsfläche, ist aber **kein alleiniger Schutz** |
| **Q2 Kryptografisch** (immer) | Steuerung, Gossip und Mandantennetze laufen ausschließlich im WireGuard-Underlay mit mTLS | ein entdeckter Knoten besitzt weder WireGuard-Schlüssel noch Zertifikat noch Gossip-Schlüssel – kein Zugang |

Im flachen Heimnetz ohne VLANs trägt die kryptografische Stufe die Anforderung allein; ab dem Betriebsprofil „Standard/C5“ ist das Discovery-VLAN Pflicht. Zusätzlich gilt: Das Discovery-Image öffnet **keine** eingehenden Dienste. Der Discovery-Eingang ist nicht Teil der Plattform-API, sondern ein kleines, festes Befehlsset mit Größen- und Ratenlimits und einer Obergrenze wartender Einträge; jede Anfrage ist mit dem Discovery-Schlüssel signiert. Jedes unbekannte Gerät ist im Portal sichtbar, optional mit Alarm. Die Netzregeln dazu beschreibt die Seite [Netzwerk](netzwerk.html).

## Adoption

### Adoptionsarten

| Art | Einsatz | Mindest-Absicherung |
|---|---|---|
| **Manuell** | Homelab, Einzelgeräte | Bestätigungscode, wenn keine TPM-Attestierung vorliegt |
| **Vorab-Registrierung** | Rechenzentrum, Serienlieferung (Lieferschein, Redfish) | Seriennummer **und** TPM-EK oder BMC-Herkunft; MAC allein unzulässig |
| **Einschreibe-Token** | Notebooks, Standorte ohne Portal-Zugang an der Konsole | befristetes, zählendes Token, nur als Hash gespeichert |
| **Adoptionsfenster** | „Ich stecke jetzt vier Pis an“ – **nur im Homelab-Profil** | befristet, begrenzte Anzahl, Benachrichtigung je Adoption |
| **Regelbasiert (dauerhaft)** | große Umgebungen | nur mit TPM-Attestierung, daher erst in einer späteren Phase |

Ein Regelobjekt beschreibt Merkmale (Modell, Speicher, Seriennummernliste), den verlangten Nachweis, Gültigkeitsdauer und Höchstzahl sowie das Ziel (Zelle, Rollen, Betriebsart, Labels, Namensschema). Dauerhafte Regeln anzulegen ist eine privilegierte Operation. **Sicherer Auslieferungszustand:** keine aktive Auto-Adopt-Regel, manuelle Adoption mit Bestätigungscode. Eine Adoption über MCP verlangt **immer** eine zusätzliche Bestätigung auf einer Plattformseite mit Passkey-Anwesenheit – das ist nicht abschaltbar.

### Schutz gegen fremde Knoten und Mittelsmänner

1. **Bestätigungscode (Short Authentication String):** Discovery-Agent und Eingang leiten aus beiden öffentlichen Schlüsseln und Zufallswerten einen kurzen Code ab – standardmäßig 6 Ziffern, im erhöhten Profil länger. Der Knoten zeigt ihn an der Konsole, das Portal bei der Adoption; der Mensch gibt den am Gerät abgelesenen Code ein. Stimmt er, ist belegt, dass das Gerät vor einem genau dieser Eintrag ist und niemand dazwischensitzt. Plattformseitig wird je Meldung ein flüchtiger Einmalschlüssel verwendet, der nie gespeichert wird; fällt der bearbeitende Knoten aus, wird die Sitzung verworfen und das Gerät zeigt einen neuen Code.
2. **Kopflose Geräte:** Code über die serielle Konsole oder alternativ Einschreibe-Token, Vorab-Registrierung oder Adoptionsfenster.
3. **TPM-Attestierung:** Prüfung des Endorsement-Zertifikats gegen Hersteller-CAs, Bindung eines Attestierungsschlüssels und ein PCR-Quote mit Nonce. Erlaubt automatische Adoption ohne Menschen – erst in einer späteren Phase.
4. **Anomalien:** Gesperrte Fingerabdrücke, MAC-Kollisionen, Schlüsselwechsel während einer Bestätigung oder auffällig viele Meldungen lösen Ereignisse und Alarme aus. Tritt dieselbe Identität gleichzeitig an zwei Endpunkten auf, werden **beide** in Quarantäne genommen (Klonverdacht).

### Adoptionsnachweis und Vertrauensstufe

Zwei getrennte Achsen: Der **Adoptionsnachweis** hält einmalig fest, wie sicher belegt ist, dass *dieses* Gerät gemeint war (bestätigt, tokengebunden, vorab registriert oder attestiert). Die **Vertrauensstufe** (T0 bis T4) beschreibt die hardwaregestützte Integrität des laufenden Knotens; sie wird laufend berechnet, sinkt sofort und steigt nur mit frischem Nachweis. **Platzierung und Rollen hängen nur an der Vertrauensstufe.** Details im [Sicherheitsmodell](sicherheitsmodell.html).

### Ablauf einer manuellen Adoption

1. Der neue Knoten bootet das signierte Discovery-Image, erzeugt einen flüchtigen Discovery-Schlüssel, sammelt das Inventar und meldet sich am Eingang. Er zeigt den Bestätigungscode an.
2. Im Portal erscheint „1 Knoten wartet“. Der Betreiber adoptiert ihn mit Name, Zelle, Rollen, Betriebsart und Code.
3. Die Plattform prüft Code und Richtlinie, legt den Knoten an und erzeugt ein **einmaliges, kurzlebiges Provisionierungs-Credential**, verschlüsselt an den bestätigten Discovery-Schlüssel.
4. Der Knoten holt das Adoptionspaket ab (Knoten-URN, Credential, Regions-CA, Boot-Profil) und installiert das OS bzw. startet diskless.
5. Das installierte OS erzeugt seinen **Langzeitschlüssel** (TPM-gebunden, wo vorhanden) und seinen WireGuard-Schlüssel und schickt einen CSR samt Credential.
6. Die Zellen-CA stellt das Knotenzertifikat (7 Tage) aus; der WireGuard-Schlüssel wird im Raft-Zustand veröffentlicht.
7. Erst **danach** erhält der Knoten über mTLS die Gossip-Schlüssel, verschlüsselt an seinen Knotenschlüssel. Er tritt dem Cluster bei und übernimmt seine Rollen.

So entsteht eine lückenlose Kette Discovery-Schlüssel → Bestätigung → Credential → CSR → Zertifikat, gebunden an einen auf dem Gerät erzeugten Schlüssel; **kein privater Schlüssel wird übertragen**. Zertifikate werden ab der Hälfte der Laufzeit erneuert. Der gesamte Vorgang ist eine einzige, nachverfolgbare Operation mit Schritten und Audit-Einträgen. Holt der Knoten das Paket nicht innerhalb von 30 Minuten ab, wird das Credential verworfen und der Eintrag fällt auf „wartend“ zurück.

**Diskless ohne Hardwareanker** muss nach jedem Neustart erneut bestätigt werden und erhält nur die niedrigste Vertrauensstufe – geeignet für zustandslose Rollen ohne sensible Mandantendaten.

### Rollen nach der Adoption

Rollen aus der Adoption werden nach dem Beitritt aktiviert. Die kritischen Rollen **Steuerung, Zeuge, Boot, Identität und KMS werden nie bei der Adoption vergeben**, sondern nur über Rollenregeln der Steuerungsgruppe unter Einhaltung der Mindest-Vertrauensstufen. Rollen, die Datenträger formatieren, verlangen eine Bestätigung.

## Ablehnen, Stilllegen, Neu-Adoption, Ersatz

- **Ablehnen:** Gesperrte Hardware erhält vom Boot-Dienst kein Discovery-Image mehr; Meldungen werden verworfen und gezählt. Die Sperre lässt sich aufheben. Ablehnen ist nicht destruktiv, das Gerät wurde nie beschrieben.
- **Stilllegen:** Nach einer Vorabprüfung der Auswirkungen wird ein Steuerungsmitglied zuerst ersetzt, dann werden Workloads und Replikate verschoben und alle Datenträger sicher gelöscht (NVMe Sanitize, ATA Secure Erase oder Krypto-Löschung). Der Knoten liefert einen **signierten Löschnachweis** je Platte. Danach werden Zertifikat widerrufen, WireGuard-Peer entfernt und – zwingend – die **Gossip-Schlüssel der Zelle rotiert**. Ist der Knoten defekt und nicht erreichbar, laufen Widerruf und Rotation sofort; die physische Vernichtung bestätigt der Betreiber nachträglich, sonst bleibt der Eintrag im Inventar offen markiert.
- **Neu-Adoption:** Ein stillgelegtes Gerät erscheint wieder als Discovery mit Verweis auf den früheren Knoten. Auto-Adopt-Regeln greifen darauf standardmäßig **nicht** – Schutz vor dem ungewollten Wiedereingliedern gestohlener oder zurückgekehrter Hardware. Eine Neu-Adoption erzeugt immer eine neue Kennung.
- **Neuinstallation ohne Identitätswechsel:** Bei beschädigtem OS oder Wechsel zwischen lokal und diskless bootet der Installer aus dem Netz; der Knoten weist sich über den Re-Zertifizierungspfad aus und behält Kennung und URN, das alte Zertifikat wird widerrufen.
- **Ersatz defekter Hardware:** Der alte Knoten wird stillgelegt, ein neuer Knoten mit neuer Kennung übernimmt Name, Labels, Rollen, Zelle und Standort; Speicherrollen bauen ihre Replikate neu auf. Werden nur Platten in ein neues Gerät umgezogen, scheitert die Re-Zertifizierung bewusst, weil der Hardware-Fingerabdruck nicht mehr passt.

## API-Übersicht

Ressourcen sind `Discovery` (mit den Aktionen `adopt`, `reject`, `unblock`), `AdoptionRule`, `EnrollmentToken` und `BmcEndpoint`; dazu kommen die Knotenaktionen `decommission`, `reprovision`, `replace` und ein Neustart mit einmaligem Netzboot, die Bestätigung physischer Löschung, Boot-Einstellungen je Region und Knoten, der Offline-Import von Artefakten und die Netzerkundung der Ersteinrichtung. Alle Aktionen sind langlaufende Operationen mit Vorabprüfung, Idempotenzschlüssel und Audit und stehen gleichwertig in API, [Portal](portal.html) und MCP zur Verfügung; destruktive Aktionen sind im MCP entsprechend gekennzeichnet.
