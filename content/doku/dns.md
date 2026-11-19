title: Plattform-DNS
summary: Die DNS-Rolle cp-dnsd – autoritative Zonen des Clusters, DNSSEC, wandernde Dienstadressen (VIPs) mit Raft-Leases und die Anbindung an den DNS des Betreibers.
group: konzept
order: 65
quelle: Plattform-DNS-Rolle
---

## Ziel

Ein Cluster von cloud-project verwaltet seine DNS-Einträge **selbst**. Portal und API, Knoten, Boot-Dienst und
Release-Halter ändern sich mit dem Cluster-Zustand – Knoten kommen hinzu, Rollen wandern, Halter fallen aus. Diese
Namen von Hand im DNS des Betreibers nachzupflegen wäre fehleranfällig. Stattdessen gilt:

> Der zentrale DNS des Betreibers zeigt nur noch auf den Cluster; alles darunter beantwortet der Cluster selbst.

Dafür gibt es die Knotenrolle `dns` mit dem Dienst `cp-dnsd`. Sie ist von der VPC-internen Namensauflösung für
Mandanten-Workloads zu unterscheiden, die lokal auf jedem Host beantwortet wird (siehe [Netzwerk](netzwerk.html)).
Mandanten-Zonen im öffentlichen DNS sind eine spätere Ausbaustufe.

## Entscheidungen

| Frage | Entscheidung |
|---|---|
| Umfang | Plattform-Einträge automatisch aus dem Cluster-Zustand, dazu eigene Einträge per API, Kommandozeile, MCP und Portal |
| Anbindung an den zentralen DNS | NS-Delegation **und** bedingte Weiterleitung; zwei feste Dienstadressen (VIPs) je Region, die automatisch auf gesunde `dns`-Knoten wandern |
| Umsetzung | eigener, rein autoritativer Server in Rust; eigene Unit ohne Knotenschlüssel, nur Port 53, harte Grenzen, Fuzzing |
| DNSSEC | je Zone einstellbar (ECDSA P-256, Rotation, DS-Eintrag im Portal); Standard „an“ in den Profilen `standard` und `erhoeht`, „aus“ im Profil `homelab` |

Die Entscheidung für eine Eigenentwicklung folgt dem Grundsatz des Projekts, Kernfunktionen selbst und schlank
umzusetzen (siehe [Vision](vision.html)). Von einer verbreiteten Rust-DNS-Bibliothek wird nur die Kodierung des
Wire-Formats genutzt; Zonenlogik, Signatur, Antwortverhalten und Begrenzungen sind eigener Code.

## Zonen und Einträge

Eine Zone ist eine Ressource `DnsZone` der Plattform. Sie wird wie jede andere Ressource über die API verwaltet –
anlegen, ändern, löschen und eine eigene Aktion zur Schlüsselrotation (siehe [API-first](api-first.html)). Der
Einrichtungsassistent schlägt bei der Initialisierung einer Region eine Zone vor, die sich aus der Portal-Adresse
ableitet, und gibt einen Hinweis, was im zentralen DNS einzutragen ist.

Die Plattform erzeugt in jeder Zone automatisch:

| Name | Inhalt |
|---|---|
| Zonenspitze | SOA und NS-Einträge `ns1`/`ns2` |
| `ns1.<zone>`, `ns2.<zone>` | die beiden Dienstadressen (bei nur einer VIP beide dieselbe) |
| Portal-Name | Adressen der bereiten Knoten, sofern die Portal-Adresse in der Zone liegt |
| `<knoten>.nodes.<zone>` | LAN-Adressen des Knotens |
| `<knoten>.underlay.<zone>` | Underlay-Adresse des Knotens |
| `boot.<zone>` | Knoten mit aktiver Rolle `boot` |
| `releases.<zone>` | aktuelle Halter der Plattform-Releases (siehe [Release-Bündel](release-buendel.html)) |

**Eigene Einträge** kommen aus der Spezifikation der Zone hinzu. Versucht ein eigener Eintrag, einen von der
Plattform verwalteten Namen zu überschreiben, wird er übersprungen; die Zone meldet das als Warnung in ihrem Status.

Der Zonenbau ist eine reine Ableitung: Der Agent berechnet aus dem replizierten Cluster-Zustand die Soll-Zone und
übergibt sie an `cp-dnsd`. Ändert sich der Zustand – ein Knoten wird bereit, eine Rolle wandert –, ändert sich die
Zone automatisch mit. Das folgt dem pegelgesteuerten Reconciler-Muster der Steuerungsebene (siehe
[Steuerungsebene](steuerungsebene.html)).

## Der Dienst `cp-dnsd`

`cp-dnsd` beantwortet DNS-Anfragen über UDP und TCP auf Port 53. Sein Verhalten ist bewusst eng gefasst:

- **Nur autoritativ**, keine Rekursion. Anfragen nach fremden Namen werden abgelehnt.
- **Keine Zonentransfers**; Anfragen vom Typ ANY liefern nur ein einzelnes RRset (RFC 8482); keine Wildcards.
- **EDNS(0)** wird unterstützt; UDP-Antworten sind auf eine konservative Größe begrenzt. Ist eine Antwort zu groß,
  wird sie als abgeschnitten markiert, und der Client wiederholt die Anfrage über TCP.
- **Grenzen:** maximale Anfragegröße, begrenzte Zahl gleichzeitiger TCP-Verbindungen mit Leerlauf-Zeitlimit;
  fehlerhafte oder übergroße Anfragen werden verworfen.

### Prozessgrenze

DNS-Parser verarbeiten Daten aus dem Netz und sind ein klassisches Angriffsziel. Deshalb läuft `cp-dnsd` als
**eigener Dienst mit eigenem Benutzer**: Er hat keinen Zugriff auf den Knotenschlüssel und keinen Zugriff auf die
replizierte Datenbank, besitzt nur das Recht, Port 53 zu binden, und ist zusätzlich durch ein
Mandatory-Access-Control-Profil eingeschränkt. Jeder Parser hat ein eigenes Fuzzing-Ziel. Ein Fehler im
DNS-Server führt damit nicht zur Übernahme des Knotens (siehe [Sicherheitsmodell](sicherheitsmodell.html)).

### Steuerungsschnittstelle

Der Agent spricht mit `cp-dnsd` über einen lokalen Unix-Socket mit einfachem, zeilenbasiertem Nachrichtenformat. Die
Gegenstelle wird über die Prozessidentität des Betriebssystems geprüft – nur der Agent darf Zonen liefern. Über
diesen Kanal kommen:

- die **Soll-Zonen** (Plattform- und eigene Einträge in kanonischer Form),
- **verschlüsselte Schlüsselumschläge** für DNSSEC (siehe unten).

`cp-dnsd` selbst entscheidet nichts über den Cluster; er beantwortet nur, was ihm der Agent als Soll übergibt.

## DNSSEC

Ist DNSSEC für eine Zone eingeschaltet, signiert `cp-dnsd` sie **online** (RFC 4033–4035, RFC 6605):

- **Algorithmus** ausschließlich ECDSA P-256 mit SHA-256 (Algorithmus 13) – kompakt und breit unterstützt.
- **Nichtexistenz** wird über eine NSEC-Kette nachgewiesen. Da die Plattformzonen klein sind und keine
  schützenswerten Namen enthalten, ist das Aufzählen über NSEC unkritisch.
- **Neu signiert** wird bei jeder Änderung der Zone und unabhängig davon regelmäßig (spätestens alle paar Tage), damit
  Signaturen nie ablaufen.
- **Signiert wird genau, was ausgeliefert wird:** Die Datensätze liegen in kanonischer Wire-Form vor (Namen
  unkomprimiert, Kleinbuchstaben), und dieselben Bytes gehen in die Antwort.
- **Rotation** der Zonenschlüssel über eine eigene API-Aktion; den DS-Eintrag für die übergeordnete Zone zeigt das
  Portal an.

### Umgang mit den Zonenschlüsseln

Die privaten Zonenschlüssel werden **in `cp-dnsd` erzeugt** und liegen nur dort, lokal mit restriktiven Rechten –
nie im Agenten. Weil mehrere `dns`-Knoten dieselbe Zone signieren müssen, werden Schlüssel zwischen ihnen verteilt,
aber ausschließlich als **Umschlag**: verschlüsselt an einen Transportschlüssel des empfangenden `cp-dnsd`
(ephemeres ECDH, Schlüsselableitung, authentisierte Verschlüsselung; Zone und Schlüssel sind in die
Authentisierung eingebunden). Dieser Transportschlüssel entsteht bei jedem Start neu und liegt nur im Speicher.
Agent und replizierte Datenbank sehen damit nur Chiffrat. Details zu den Verfahren stehen in
[Kryptografie](kryptografie.html).

## Wandernde Dienstadressen (VIPs)

Damit der zentrale DNS des Betreibers stabile Ziele hat, bekommt jede Region bis zu **zwei feste Dienstadressen**
im LAN. Sie werden nicht fest einem Knoten zugeordnet, sondern **wandern automatisch** auf gesunde `dns`-Knoten –
ähnlich wie bei VRRP, aber als Eigenentwicklung auf Basis der replizierten Steuerungsebene.

### Raft-Lease mit Fencing

Jede VIP gehört zu einem Lease-Objekt in der replizierten Datenbank mit Halter, Fencing-Epoche und
Erneuerungszähler. Jeder Schreibzugriff ist ein Vergleichen-und-Tauschen auf die Revision und damit nur mit
Raft-Quorum möglich.

- Der **Halter** erneuert regelmäßig. Er trägt die VIP nur bis zum Ende seiner zuletzt erfolgreichen Erneuerung
  abzüglich eines Sicherheitsabstands – gemessen mit seiner lokalen monotonen Uhr. Scheitert die Erneuerung,
  etwa wegen Netztrennung oder fehlenden Quorums, **legt er die VIP vorher ab**.
- Ein **anderer Knoten übernimmt** erst, wenn er die unveränderte Revision mindestens eine volle Lease-Dauer lang
  beobachtet hat. So endet der Besitz des alten Halters garantiert vor der Übernahme – ohne synchronisierte Uhren;
  begrenzte Gangabweichungen deckt der Sicherheitsabstand ab. Jede Übernahme erhöht die Epoche.
- **Ohne Quorum** gibt es weder Erneuerung noch Übernahme. Eine Doppelbelegung der Adresse ist damit
  ausgeschlossen.

Dasselbe Lease-Muster nutzt die Plattform auch für andere wandernde Adressen, etwa Floating IPs auf Gateways (siehe
[Netzwerk](netzwerk.html)).

### Adressen setzen und ankündigen

Das Setzen der Adresse auf eine Netzwerkschnittstelle ist eine privilegierte Operation. Der Agent darf das nicht
selbst, sondern beauftragt den privilegierten Hilfsdienst des Knotens über ein festes, kleines Befehlsformat:
zulässige VIPs konfigurieren, eine VIP setzen, eine eigene VIP ablegen, gehaltene VIPs auflisten. Der Hilfsdienst
prüft unabhängig, dass die Adresse in der konfigurierten Liste steht, im Netz einer vorhandenen LAN-Schnittstelle
liegt (nicht Loopback, nicht Underlay) und nicht bereits eine eigene Adresse des Knotens ist. Fremde Adressen kann er
nicht entfernen.

Nach der Übernahme muss das LAN von der neuen Zuordnung erfahren. Statt mit Rohsockets zu arbeiten, sendet der Agent
ein Paket mit der VIP als Absender an eine noch unaufgelöste Adresse im LAN. Das löst ARP bzw. Neighbor
Solicitation mit der VIP als Absender aus und aktualisiert die Nachbartabellen der übrigen Geräte.

## Ratenbegrenzung

Ein autoritativer DNS-Server kann für Reflexionsangriffe missbraucht werden. `cp-dnsd` begrenzt deshalb die
Antwortrate **je Quellnetz** (IPv4 je /24, IPv6 je /56) mit einem Token-Bucket. Oberhalb des Limits werden Antworten
verworfen; jede zweite verworfene UDP-Antwort geht jedoch als leere, abgeschnittene Antwort hinaus. Legitime Clients
weichen dadurch auf TCP aus und werden weiter bedient, während gefälschte Absender keinen Verstärkungseffekt
erzielen. Die Gesamtzahl der verfolgten Quellnetze ist begrenzt; die ältesten Einträge fallen heraus.

## Anbindung an den Betreiber-DNS

Der Betreiber hat zwei Möglichkeiten, die sich auch kombinieren lassen:

1. **NS-Delegation:** Die Zone der Region wird in der übergeordneten Zone an `ns1`/`ns2` delegiert, die auf die beiden
   VIPs zeigen. Mit DNSSEC wird zusätzlich der DS-Eintrag aus dem Portal hinterlegt.
2. **Bedingte Weiterleitung:** Interne Resolver leiten Anfragen für die Zone an die beiden VIPs weiter – praktisch in
   Netzen ohne öffentliche Delegation.

## Status und Betrieb

Die Rolle `dns` wird wie jede andere Knotenrolle vom Rollen-Reconciler gestartet und überwacht. Die Region meldet in
ihrem Status den DNS-Zustand, insbesondere welcher Knoten welche VIP hält. Fällt ein `dns`-Knoten aus, wandert seine
VIP nach Ablauf der Lease auf einen anderen gesunden Knoten; die Zone selbst ist auf allen `dns`-Knoten identisch.
Die Portal-Adresse einer Region kann in einer solchen Zone liegen; was bei deren Änderung zu beachten ist, beschreibt
[Portal-Hostname ändern](portal-hostname.html).
