title: Sicherheitsmodell
summary: Wem die Plattform vertraut, wofür, wie dieses Vertrauen nachgewiesen wird und was bei Vertrauensverlust geschieht – von Vertrauensankern über Knotenstufen und Remote Attestation bis zu Break-Glass und Kompromittierung.
group: konzept
order: 90
quelle: Konzept 10 (Sicherheitsmodell)
---

Das Sicherheitsmodell legt fest, **wem** die Plattform vertraut, **wofür**, **wie das nachgewiesen** wird und **was bei Vertrauensverlust passiert**. Algorithmen, Schlüssellängen, Laufzeiten und die PKI-Hierarchie stehen im [Kryptokonzept](kryptografie.html); Boot-Pfade und der Adoptionsablauf in [Boot und Adoption](boot-adoption.html). Die Angreifermodelle stammen aus dem [Bedrohungsmodell](bedrohungsmodell.html).

## Kernentscheidungen

- **Zwei getrennte Achsen:** Der *Adoptionsnachweis* beschreibt, wie sicher feststeht, dass genau dieses Gerät gemeint war (Bestätigungscode, Einschreibe-Token, Vorab-Registrierung, Attestierung). Die *Vertrauensstufe* beschreibt, wie gut die Integrität des laufenden Knotens hardwaregestützt belegt ist. Platzierung und Rollen hängen **nur** an der Vertrauensstufe.
- **Fünf Vertrauensstufen T0–T4**, berechnet statt behauptet: Die Stufe sinkt sofort und steigt nur nach frischem Nachweis.
- **Stufen sind Platzierungs- und Rollenbedingungen:** Steuerungsgruppe, Schlüsselverwaltung (KMS), Identitätsdienst und Zertifikatssignatur verlangen je nach Betriebsprofil Mindeststufen.
- **Remote Attestation** per TPM-Quote gegen signierte Referenzwerte des Release-Manifests.
- **Quarantäne ist ein harter, technisch durchgesetzter Zustand** – kein Etikett.
- **Eine Identität je Prozessgrenze:** Fremdprozesse erhalten eigene, lokal erzeugte Dienstidentitäten, nie den Knotenschlüssel.
- **Workload-Identität strikt getrennt** von der Infrastruktur, mit knotengebundenen Ausstellern.
- **Geheimnisse nur nach Bedarf und Stufe**, ausschließlich verschlüsselt an den Knotenschlüssel und nur im Arbeitsspeicher.
- **Betreiberzugriff über die API**, interaktiver Zugriff nur befristet, begründet und aufgezeichnet.
- **Kompromittierung als Runbook-Operation** mit sofortigem Widerruf und gezielter Rotation.

## Vertrauensanker

Vertrauen entsteht in der Plattform aus genau zwei Quellen: aus **Signaturen**, die auf einen definierten Vertrauensanker zurückführen, und aus dem **autoritativen Zustand** der Steuerungsebene (Raft, siehe [Steuerungsebene](steuerungsebene.html)).

| Anker | Gehalten von | Wofür vertraut |
|---|---|---|
| Plattform-Root-CA | Verwahrer von Wiederherstellungsanteilen (k aus n) | Ausstellung der Regions-CAs |
| Regions- und Zellen-CA | Rolle `kms` auf Steuerungsknoten | Knoten- und Dienstzertifikate |
| Workload-CA und Workload-Token-Aussteller | Steuerungsknoten bzw. knotengebunden | Identitäten von Mandanten-Workloads |
| Signaturschlüssel des Identitätsdienstes | Rolle `identity` | Tokens für Nutzer und Dienstkonten |
| Release-Signaturschlüssel | Projekt (Offline-Root) | OS-Images, Agent, Boot-Artefakte, Referenzwerte für Attestierung |
| Secure-Boot-Schlüssel | je Installation bzw. Projekt oder Betreiber | Boot-Kette auf dem Gerät |
| TPM-Hersteller-CAs | Hersteller | Echtheit eines TPM |
| Firmware-Baseline je Gerätemodell | Betreiber (bestätigt bei Adoption) | Firmware-Messwerte eines Gerätetyps |
| Passkeys, Break-Glass-Material, Wiederherstellungsschlüssel | Menschen | Verwaltung und Notfall |
| Menschliche Bestätigung (Vergleichscode) | Betreiber am Gerät | Adoption ohne Hardwareanker |

**Leitsatz:** Nichts im Netz ist per se vertrauenswürdig – weder Absenderadresse, VLAN, DHCP-Antwort, Gossip-Nachricht noch Kernel-Parameter. Solche Angaben sind Hinweise, keine Vertrauensgrundlage.

### Vertrauensgrenzen und Grundsätze

Die Plattform unterscheidet eine **Außenwelt** (LAN, Discovery-Segment, Internet), eine **Mandanten-Domäne** (VMs, Container, Kubernetes-Cluster mit eigener Workload-CA) und eine **Infrastruktur-Domäne** (Arbeitsknoten und – als Kern – die Steuerungsknoten). Geprüft wird **immer** am Eingang (Token mit Senderbindung), zwischen Agenten (mTLS plus Rechtetabelle), in der Zustandsmaschine (Knoten-Autorisierer), im KMS (Platzierungsnachweis) und an der Grenze Workload↔Host.

1. **Knoten sind keine Principals für Mandantenoperationen.** Sie handeln als Systemakteure mit Rechten, die sich aus ihren Zuweisungen in der Steuerungsebene ergeben.
2. **Raft ist nicht byzantinisch fehlertolerant.** Die Integrität der Steuerungsknoten ist daher die wichtigste Einzelannahme; sie wird mit der höchsten verfügbaren Vertrauensstufe abgesichert, und **Zellen sind Schadensgrenzen**.
3. **Kurze Laufzeiten statt Widerrufsinfrastruktur** – aber der Widerruf eines Knotens wirkt sofort über eine replizierte Sperrliste.
4. **Vertrauen sinkt schnell und steigt langsam.** Rückkehr aus der Quarantäne ist nie automatisch.
5. **Fail closed** für Identität und Geheimnisse, **statische Stabilität** für laufende Workloads: Ein Vertrauensverlust stoppt Workloads nur, wenn die Richtlinie es verlangt.
6. **Ehrliche Kennzeichnung:** Was ein Knoten nur selbst meldet, wird als selbst gemeldet geführt und begründet keine hohe Stufe.

## Vertrauensstufen für Knoten

| Stufe | Name | Kernkriterium | Typische Geräte |
|---|---|---|---|
| T0 | `none` | nicht adoptiert oder in Quarantäne | Discovery, quarantänisierte Knoten |
| T1 | `basic` | adoptiert, Knotenschlüssel als Datei, Boot-Kette nicht hardwareverifiziert | Raspberry Pi ohne Secure Boot, x86 ohne TPM, verschachtelte VMs |
| T2 | `anchored` | durch die Firmware erzwungene Signaturprüfung der Boot-Kette mit eigenem Schlüssel plus gerätefester Schlüssel für die Datenträgerfreigabe | Pi mit OTP-Secure-Boot, x86 mit eigenem Secure Boot ohne TPM |
| T3 | `tpm` | TPM 2.0 schützt Schlüssel und Datenträger, aber keine gültige Attestierung | Server, Mini-PCs, Notebooks mit TPM |
| T4 | `attested` | wie T3 plus Secure Boot, Measured Boot und frische, erfolgreiche Attestierung | Server mit TPM, Geräte mit Firmware-TPM |

Ergänzende Labels (TPM-Art, Secure-Boot-Modus, Attestierungszustand, Art der Datenträgerentsperrung, Boot-Modus) erlauben feinere Richtlinien. Sonderfälle: Ein Pi mit TPM-Erweiterungsplatine erreicht höchstens T3, weil seine Firmware nicht in das TPM misst. Diskless-Knoten ohne Hardwareanker sind nur auf ausdrücklichen Wunsch zulässig, bleiben T1 und übernehmen nur zustandslose Rollen. VMs als Knoten und externe Zeugen auf fremden Hosts sind fest T1, weil die Plattform fremde Hardware nicht prüfen kann.

### Ermittlung und Dynamik

Ein Vertrauens-Controller der Zelle berechnet die Stufe aus Inventar, Attestierungsergebnissen und Ereignissen und schreibt Änderungen mit Begründung in die Steuerungsebene. **Betreiber können eine Stufe deckeln, nie anheben** – einzige Ausnahme ist eine befristete, begründete und im Vier-Augen-Prinzip freigegebene Vertrauensausnahme, die im Compliance-Export sichtbar ist. Eine Herabstufung wirkt sofort auf neue Entscheidungen (Platzierung, Geheimnisausgabe) und mit einer Frist auf bestehende Zuweisungen.

### Was jede Stufe darf

Die Mindeststufen hängen am **Betriebsprofil** (`homelab`, `standard-c5`, `erhoeht`), nicht am Krypto-Profil:

| Funktion | `homelab` | `standard-c5` | `erhoeht` |
|---|---|---|---|
| Raft-Voter, `kms`, `identity`, Zellen-CA-Signatur | T1/T2 mit sichtbarer Warnung, wenn keine höhere Alternative existiert | mindestens T3, ab Verfügbarkeit der Attestierung T4 | T4 (bis dahin T3 mit Warnung) |
| alle übrigen Knoten | T1 | T1 nach Rollenregeln | mindestens T3 |

Weitere Regeln: Mandanten-Workloads der Datenklasse `sensitive` laufen nur auf T3 oder höher, die Klasse `attested-only` nur auf T4. Speicherknoten dürfen auch T1 sein, weil sie nur Chiffrat halten (siehe [Speicher](speicher.html)). Bei der Wahl der Steuerungsgruppe ist die Stufe ein hartes Sortierkriterium – die **Streuung über Ausfallzonen hat aber Vorrang**: drei T1-Voter in drei Zonen sind besser als drei T4-Voter in einer Zone. Mandanten-Leitplanken dürfen diese Regeln nur verschärfen. Ein reines Pi-Homelab bleibt voll funktionsfähig, mit sichtbarer Kennzeichnung der Degradation.

Sinkt die Stufe eines Knotens, ersetzt der Steuerungsgruppen-Controller ihn als Voter, das KMS verwirft Klartextschlüssel sofort, schutzbedürftige Workloads werden innerhalb einer Frist migriert, und Geheimnisse mit Mindeststufe werden nicht mehr erneuert. Standard-Workloads bleiben unberührt.

## Knoten-Identität und Lebenszyklus

Die Identität eines Knotens besteht aus einer unveränderlichen **UID** (neu bei jeder Neu-Adoption), einem menschenlesbaren Namen, einer SPIFFE-ID im Zertifikat, dem **auf dem Knoten erzeugten Knotenschlüssel** (im TPM, sonst als Datei auf verschlüsseltem Datenträger), bei TPM-Geräten Endorsement- und Attestierungsschlüssel, einem Underlay-Schlüssel und einem Hardware-Fingerabdruck. Die Knotenzertifikate sind kurzlebig und werden ab der Hälfte ihrer Laufzeit erneuert.

Der Lebenszyklus verläuft von **Discovery** (flüchtiger Schlüssel, keine Vertrauensbasis) über **Adoption** und **Erstzertifizierung** zu laufender **Erneuerung**. War ein Knoten länger offline, folgt eine **Re-Zertifizierung**, deren Nachweis von der Stufe abhängt: Mit TPM genügt der kryptografische Nachweis; Knoten ohne TPM brauchen standardmäßig eine **menschliche Freigabe**. Ein abweichender Hardware-Fingerabdruck führt nie zu einer stillen Neuausstellung, sondern zur Quarantäne – der Betreiber entscheidet über Ersatz oder Bestätigung. Am Ende steht der **Widerruf** mit einem Tombstone, der eine automatische Wiederaufnahme verhindert.
## Remote Attestation

Remote Attestation macht die Stufe T4 möglich. Attestiert wird bei der Adoption, bei jedem Start vor dem Beitritt zum Cluster, bei jeder Zertifikatserneuerung, periodisch, nach jedem Update und auf Anforderung.

Der Ablauf in Kürze:

1. **Einmalig je Adoption:** Der Prüfer validiert das Endorsement-Zertifikat des TPM gegen ein kuratiertes, signiert ausgeliefertes Bündel von Hersteller-CAs. Über Credential Activation wird belegt, dass der Attestierungsschlüssel im selben TPM liegt; der Knotenschlüssel wird als TPM-resident nachgewiesen.
2. **Jede Attestierung:** Der Prüfer sendet eine einmalige Nonce, der Knoten liefert eine signierte TPM-Quote samt Ereignisprotokoll. Geprüft werden Signatur, Nonce, Monotonie der TPM-Zähler und die Übereinstimmung des Protokolls mit den PCR-Werten.
3. **Abgleich gegen eine Richtlinie** aus signierten Referenzwerten des Release-Manifests (Bootloader, Kernel-Image, Kommandozeile mit dm-verity-Root-Hash, erwartete Secure-Boot-Schlüssel) und einer betreiberbestätigten Firmware-Baseline je Gerätemodell.

Geprüft wird **Ereignis für Ereignis** statt nur über PCR-Endwerte – so bleiben Firmware-Updates und mehrere zulässige Image-Versionen handhabbar und Abweichungen erklärbar. Die Referenzwerte sind schreibgeschützt und stammen ausschließlich aus signierten Manifesten (siehe [OS-Image](os-image.html) und [Release-Signatur](release-signatur.html)). Attestierung entscheidet nur über Stufe und Zustand; Geheimnisse werden getrennt und erst danach ausgegeben. Der Prüfer ist eigener Rust-Code auf den Steuerungsknoten.

Knoten ohne TPM melden Image-Version, Boot-Pfad und Secure-Boot-Status signiert mit ihrem Knotenschlüssel. Das erkennt Fehlkonfiguration und veraltete Images, aber keinen Angreifer mit Root-Rechten – deshalb bleibt es bei T1/T2.

### Fehlerklassen

| Klasse | Beispiele | Reaktion |
|---|---|---|
| Manipulationsindiz | ungültige Quote-Signatur, gewechselter Schlüssel, Protokoll passt nicht zu den PCRs, Nonce-Wiederholung, Secure Boot plötzlich aus | sofortige Quarantäne, hoher Alarm |
| Unbekannte, plausible Messwerte | neue Firmware-Version, Image außerhalb des zulässigen Fensters | Herabstufung auf T3, Alarm, Rückkehr nach Betreiberfreigabe |
| Fehlender Nachweis | Prüfer nicht erreichbar, Knoten offline | nach Ablauf der Gültigkeit Herabstufung, nie Quarantäne |

### Quarantäne

Quarantäne ist aus jedem adoptierten Zustand direkt erreichbar und wirkt auf allen Ebenen: Der Knoten erhält statt eines regulären Zertifikats ein kurzlebiges Quarantäne-Zertifikat, das nur Diagnose, Attestierung und Forensik-Export erlaubt. Er verliert jede Rolle in der Steuerungsgruppe, wird aus dem Gossip ausgeschlossen (der Gossip-Schlüssel wird sofort rotiert), im Underlay nur noch von Steuerungsknoten erreicht, erhält keinerlei Schlüssel mehr, und schutzbedürftige Workloads werden gestoppt. Austritt nur per frischem Nachweis und menschlicher Freigabe – oder Stilllegung.

## Dienstidentitäten und mTLS

**Eine Identität je Prozessgrenze, nicht je Rolle:** Alle Rollen innerhalb des Agenten nutzen das Knotenzertifikat; welche Rolle ein Knoten ausüben darf, wird bei jedem Aufruf aus der Steuerungsebene autorisiert, nicht aus dem Zertifikat. Eigene Dienstprozesse außerhalb des Agenten (etwa der Boot-Dienst `cp-bootd` oder der Blockspeicher-Dienst `cp-blkd`) und Fremdkomponenten (Zeitdienst, Telemetrie, Objektspeicher u. a.) erhalten **eigene, lokal erzeugte Schlüssel** mit kurzlebigen Dienstzertifikaten, deren SPIFFE-Pfad unter dem Pfad des Hosts liegt. So lässt sich allein aus Zertifikat und Steuerungszustand beantworten, ob ein Dienst auf dem Knoten läuft, dem die Rolle zugewiesen ist. Fremdprozesse erhalten nie den Knotenschlüssel, das Gossip-Geheimnis oder KMS-Zugriff; ihre Schlüssel liegen in unit-eigenen, flüchtigen Credential-Verzeichnissen.

Bei jeder mTLS-Verbindung zwischen Agenten prüft ein eigener Verifier zusätzlich zu den TLS-Parametern: Kette bis zur Zellen- bzw. Regions-CA der eigenen Region (Workload-CA und öffentliche CAs werden auf Infrastruktur-Ports nie akzeptiert), genau eine passende SAN-URI mit aktueller Zellen-Epoche, kein Eintrag auf der Sperrliste, kein Quarantänezustand. **Das Zertifikat sagt nur, wer – nie, was.** Das „Was“ regelt eine im Code deklarierte **RPC-Rechtetabelle**: Jede Methode nennt die zulässige Aufrufer-Eigenschaft (Raft-Mitglied, Leader, Platzierung der Ressource, Rolle, Zustand), und Tests stellen sicher, dass keine Methode ohne Eintrag existiert. Weitergeleitete API-Anfragen werden am Ziel anhand des **Original-Tokens** autorisiert; die Signatur des Eingangsknotens belegt nur den Weg. Netzfilterregeln, die aus dem Steuerungszustand erzeugt werden, bilden eine zweite Schicht und begrenzen auch Komponenten mit schwacher Eigenauthentisierung auf autorisierte Gesprächspartner.

## Workload-Identität für Mandanten

Mandanten-Workloads erhalten Identitäten aus einer **eigenen Workload-CA**; ihr Vertrauensbündel enthält nie die Infrastruktur-CAs, und Workload-Identitäten werden auf Infrastruktur-Schnittstellen grundsätzlich abgelehnt (siehe [Identität](identitaet.html)). Die „Attestierung“ einer Workload ist ihre **Platzierung**: Nur der Host-Agent, auf dem die Workload laut Steuerungsebene läuft, darf eine Identität für sie anfordern, und die CA prüft die Platzierung selbst, bevor sie signiert. Der Gast erhält die Identität ausschließlich über seinen eigenen Kanal (vsock, projizierte Datei).

Workload-Tokens werden mit einem **knotengebundenen, kurzlebigen Ausstellerschlüssel** signiert. Prüfer verlangen, dass der Schlüssel zum Knoten gehört **und** die Workload laut Steuerungsebene genau dort läuft. Ein kompromittierter Knoten kann so keine Tokens für fremde Workloads prägen. Für externe Föderationspartner steht ein Token-Austausch gegen ein zentral signiertes, kurzlebiges Token bereit. Confidential Computing wird in einer späteren Phase die Platzierungsattestierung durch Hardware-Berichte ergänzen.

## Geheimnisverteilung und Schutz des Steuerungszustands

Geheimnisse werden nach festen Regeln verteilt:

1. **Bedarf und Stufe** – kein Geheimnis „für alle Fälle“. Klartext-KEKs und CA-Schlüssel nur auf Knoten mit der Rolle `kms`, Datenschlüssel eines Volumes nur an den Compute-Host mit gültiger Anhängung, nie an Speicherknoten.
2. **Nur im Arbeitsspeicher**, mit Nullung nach Gebrauch und ohne Swap.
3. **Gossip transportiert nie Geheimnisse.**
4. **Zuordnung je Knoten:** Die Steuerungsebene führt, welche Geheimnisse ein Knoten erhalten hat – Grundlage der gezielten Rotation bei Kompromittierung.
5. **Jede Ausgabe ist auditiert.**

Der replizierte Steuerungszustand ist mehrschichtig geschützt: verschlüsselte Datenträger, Feldverschlüsselung für Schlüsselmaterial, vollständige Kopien nur auf Steuerungsknoten, ein Knoten-Autorisierer und hash-verkettete, signierte Audit-Blöcke. Der Zertifikats-Signer stellt nur aus, wenn alle Bedingungen aus dem Steuerungszustand erfüllt sind, und begrenzt die Ausstellungsrate je Knoten.

## Betreiberzugriff und Break-Glass

Das OS-Image hat **keinen interaktiven Login und ab Werk keinen SSH-Zugang**. Betreiber verwalten über API, Portal und MCP; Metadaten sind sichtbar, Mandanteninhalte nur über einen expliziten, auditierten Zugriffsantrag. Interaktiver Zugriff auf Knoten gibt es auf genau zwei Wegen, beide privilegiert, befristet, begründet, aufgezeichnet und auditiert:

- **Diagnosesitzung:** festes Befehlsset des Agenten, optional eine Shell, höchstens zwei Stunden, Vier-Augen-Prinzip per Richtlinie zuschaltbar; der Knoten wird sichtbar gekennzeichnet.
- **Tier-0-SSH:** kurzlebige SSH-Zertifikate einer plattformeigenen CA, nur über das Management-Netz; das Recht ist ab Werk niemandem zugewiesen und nicht in der Administratorrolle enthalten.

Break-Glass ist in **vier klar getrennte Stufen** gegliedert: Notfall-Konto bei Ausfall des Identitätsdienstes (Hardwareschlüssel, kein Inhaltszugriff), Zellen-Wiederherstellung bei Quorumverlust (lokal, mit zweiter Person, Epochenwechsel), PKI-/KMS-Wiederherstellung per Schlüsselzeremonie k aus n, und ein lokaler Rettungszugang, der Daten nur mit der Plattform freigibt. Jede Nutzung löst Alarm aus, wird nachbereitet und regelmäßig geübt.

## Audit sicherheitsrelevanter Ereignisse

Sicherheitsrelevante Ereignisse werden signiert und verkettet protokolliert – auch ohne Quorum in einem lokalen, signierten Puffer, der später nachgetragen wird. Erfasst werden unter anderem Discovery und Adoption, jede Zertifikatsausstellung und jeder Widerruf, Attestierungsergebnisse, Stufenänderungen, Quarantäne, Schlüsselfreigaben, abgelehnte Autorisierungen, Gossip-Anomalien, doppelte Identitäten (Klonverdacht), Schlüsselrotationen, Ausnahmen, Diagnosesitzungen, Break-Glass, Boot-Konflikte und physische Ereignisse wie Gehäuseöffnungen. Häufige Routineereignisse werden aggregiert, kritische einzeln protokolliert und alarmiert.

## Umgang mit einem kompromittierten Knoten

**Erkennung:** Starke Signale – Manipulationsindizien bei der Attestierung oder dieselbe Knotenidentität gleichzeitig von zwei Endpunkten – lösen die Quarantäne automatisch aus. Mittlere Signale (abweichender Fingerabdruck, gehäufte Autorisierungsablehnungen, unerwarteter Boot-Pfad, Gehäuseöffnung) erzeugen einen Vorschlag mit Ein-Klick-Ausführung, schwache nur Alarme.

**Eindämmung als Operation:** Quarantäne mit Grund „Verdacht auf Kompromittierung“ setzt den Knoten binnen Sekunden auf die Sperrliste, schließt ihn aus Gossip, Underlay und Steuerungsgruppe aus, stoppt schutzbedürftige Workloads und führt einen **Rotationsplan** aus, der sich aus der Geheimnis-Zuordnung ergibt. Der Umfang folgt der Rolle: Für einen Arbeitsknoten genügen eigene Schlüssel und die Benachrichtigung betroffener Mandanten; für einen Knoten mit `kms`- oder Identitätsrolle folgt eine Notfallrotation von Zellen-CA, Schlüsselhierarchie und Signaturschlüsseln.

**Wiederherstellung:** Forensik zuerst, wenn gewünscht. Kein „Säubern“ vor Ort – der Knoten wird stillgelegt und kann nur als **neue Identität** nach Neuinstallation wieder aufgenommen werden. Replikate und Steuerungsgruppe stellen sich über die normalen Controller wieder her; eine Nachbetrachtung fließt in die Erkennungsregeln ein.

**Schadensgrenzen als Entwurfsziel:** Ein kompromittierter Arbeitsknoten betrifft höchstens die Mandanten mit Workloads auf ihm; ein Voter die Zelle; ein Knoten mit `kms`- oder Identitätsrolle die Region – deshalb gelten für diese Rollen die höchsten Mindeststufen.

Für die Boot- und Discovery-Umgebung gilt dasselbe Prinzip: Ein nicht adoptiertes oder fremdes Gerät erreicht weder Underlay noch mTLS noch Gossip, Boot-Artefakte sind signiert, und Adoption setzt eine menschliche Bestätigung oder einen Hardwarenachweis voraus.

## Umsetzungsphasen

| Phase | Umfang |
|---|---|
| MVP | Stufen T0–T3, Rollen- und Platzierungsmatrix, Knotenlebenszyklus mit Re-Zertifizierung, Quarantäne, RPC-Rechtetabelle, Dienstidentitäten, knotengebundene Workload-Aussteller, Geheimnis-Zuordnung, Diagnosesitzung und Tier-0-SSH, Audit-Katalog, Kompromittierungs-Runbook |
| P2 | TPM-residente Knotenschlüssel, Remote Attestation (T4), Firmware-Baselines, Auto-Adopt mit Attestierung, Gegenzeichnung von Audit-Prüfpunkten durch mehrere Voter, Forensik-Export |
| P3 | Confidential Computing, Hersteller-Referenzwerte, Laufzeitmessung, Neuverschlüsselung nach Kompromittierung |

Verwandte Seiten: [Kryptografie](kryptografie.html) · [Bedrohungsmodell](bedrohungsmodell.html) · [Boot und Adoption](boot-adoption.html) · [Netzwerk](netzwerk.html) · [Compliance by Design](compliance-by-design.html)
