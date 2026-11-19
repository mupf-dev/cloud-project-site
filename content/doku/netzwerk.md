title: Netzwerk
summary: Netzzonen, verschlüsseltes WireGuard-Underlay, das eigene Mandanten-Overlay cp-vnet, Anbindung der Workloads und Nord-Süd-Verkehr mit Floating IPs, Gateways und Plattform-DNS.
group: konzept
order: 60
quelle: Konzept 06 (Netzwerkarchitektur)
---

## Überblick

Die Plattform trennt ihr Netz in zwei Schichten: ein **Underlay**, das alle Knoten kryptografisch miteinander verbindet, und ein **Mandanten-Overlay**, in dem die virtuellen Netze (VPCs) der Mandanten laufen. Alles, was zwischen Knoten fließt – Steuerungsverkehr (Raft, gRPC), Gossip, Speicher-Replikation, Livemigration **und** der Verkehr der Mandanten-Workloads – läuft im verschlüsselten Underlay. Auf dem physischen Netz sind nur noch WireGuard-UDP, die Boot- und Discovery-Dienste, ein Kanal für Zusatzschlüssel und die öffentlichen Eingänge (API, Portal, MCP, Floating IPs) sichtbar.

Das Konzept ist so geschnitten, dass es vom Homelab mit einem einzigen Router bis zum Rechenzentrum mit Leaf-Spine-Fabric trägt. Die Schutzwirkung hängt dabei **nicht** von der physischen Ausbaustufe ab: Sie ist immer kryptografisch und wird dort, wo die Infrastruktur es erlaubt, zusätzlich physisch verstärkt.

### Kernentscheidungen

| Thema | Entscheidung |
|---|---|
| Zonen | sieben Netzzonen, abbildbar auf drei physische Ausbaustufen `flat`, `vlan`, `routed` |
| Underlay | ein Kernel-WireGuard-Interface je Knoten, innen nur IPv6 (ULA); Peers ausschließlich aus dem Sollzustand; zusätzlicher Post-Quanten-PSK |
| Mandanten-Overlay | Eigenentwicklung `cp-vnet` auf dem Linux-Kernel-Datenpfad (VRF + VXLAN + nftables); nicht OVN, nicht Cilium; Overlay-Pakete nur im WireGuard-Underlay |
| Nord-Süd | Rolle `network-gateway` für NAT, Floating IPs und L4-Load-Balancer; Besitz per Raft-Lease mit Fencing |

## Netzebenen und Zonen

### Zonenmodell

| Zone | Inhalt | Schutz |
|---|---|---|
| **Z0 Physisch / Transport** | LAN oder RZ-Fabric, trägt WireGuard-UDP | Grundregelwerk (nur erlaubte Ports), WireGuard-Cookie gegen Handshake-Fluten |
| **Z1 Boot / Discovery** | proxyDHCP, TFTP, Boot-HTTP, Discovery-Eingang | kryptografische Quarantäne immer, VLAN-Trennung optional bzw. je Profil Pflicht; signierte Artefakte |
| **Z2 Underlay** (in WireGuard) | Steuerung, Gossip, Storage-Replikation, Livemigration, Overlay-Transport | WireGuard (+ PQ-PSK) und je Dienst mTLS bzw. AEAD; nur adoptierte Knoten |
| **Z3 Mandanten-Overlay** (VXLAN in Z2) | VPCs, Subnetze, VM- und Container-Verkehr | VRF je VPC, conntrack-Zonen, Security Groups, Anti-Spoofing |
| **Z4 Nord-Süd / Uplink** | Floating IPs, NAT-Gateway, LB-VIPs, Internetausgang | nftables-Grenze, DDoS-Grundschutz, Security Group am Ziel |
| **Z5 Management** | API, Portal, MCP, lokale Knoten-API | TLS 1.3, Authentisierung, erlaubte Quellnetze, Rate-Limits |
| **Z6 Out-of-Band** | BMC/Redfish, serielle Konsolen | nie im Mandanten- oder Internetnetz; Zugangsdaten nur als Secret-Referenz |

**Grundsatz:** Eine Zone ist erst eine Zone, wenn ihre Grenze durchgesetzt **und** beobachtbar ist. Jeder Knoten meldet die tatsächliche Zonenzuordnung seiner Schnittstellen; Abweichungen – etwa Mandanten-VXLAN auf einer physischen Schnittstelle oder ein BMC im selben Segment wie der Uplink – erscheinen als Alarmbedingung und im Topologie-Export.

### Physische Ausbaustufen

| Stufe | Typische Umgebung | Abbildung |
|---|---|---|
| `flat` | Homelab: ein Router mit DHCP, einfacher Switch, Geräte mit einer NIC | Z0, Z1, Z4, Z5 teilen sich das LAN; Z2/Z3 rein kryptografisch getrennt |
| `vlan` | VLAN-fähiger Switch | Zugangsports untagged = Discovery; getaggte VLANs für Underlay, Uplink und Management; getaggte Sub-Interfaces erst nach der Adoption |
| `routed` | Rechenzentrum, Leaf-Spine | jeder Host mit eigener Loopback-Adresse als WireGuard-Endpunkt, BGP zum Top-of-Rack-Switch, Boot-Segment je Rack mit DHCP-Relay |

Die Stufe ist eine Eigenschaft des Standorts; ein Wechsel von `flat` auf `vlan` ist rollierend im laufenden Betrieb möglich.

### Einbettung der Discovery-Quarantäne

Unbekannte Hardware landet zunächst in Zone Z1 (siehe [Boot und Adoption](boot-adoption.html)). Die Boot-Dienste beantwortet ein eigener Sandbox-Prozess (`cp-bootd`) mit eigener Dienstidentität, **ohne** Zugriff auf Knoten- oder WireGuard-Schlüssel und ohne Zugang zu Z2/Z3. Ein entdeckter Knoten besitzt weder WireGuard-Schlüssel noch einen Peer-Eintrag bei irgendeinem Plattformknoten – er sieht deshalb weder das Underlay noch die Mandantennetze.

Auf den physischen Schnittstellen eines adoptierten Knotens ist eingehend nur Folgendes erlaubt: WireGuard-UDP, der PSK-Kanal (nur von bekannten Peers), Boot-Dienste (nur auf Boot-Knoten), HTTPS für API/Portal/MCP aus den freigegebenen Quellnetzen, Floating IPs (nur auf Gateways) und ratenbegrenzte ICMP-Fehlermeldungen. Alles andere – insbesondere VXLAN, Gossip und gRPC – wird verworfen.

## WireGuard-Underlay

### Warum WireGuard

Kernel-WireGuard ist auf Raspberry Pis ohne AES-Befehle dank ChaCha20 schnell (etwa Gigabit-Rate), hat keinen Verhandlungszustand und bringt Roaming und NAT-Tauglichkeit mit. IPsec ist ein mögliches späteres Profil, eigenes TLS/QUIC-Tunneling im Userspace wurde verworfen. Die fehlende Algorithmen-Agilität wird architektonisch aufgefangen: Das Underlay ist hinter einer Schnittstelle gekapselt, sodass ein IPsec-Profil ohne Änderungen an Overlay und Steuerung einsetzbar bleibt. Die kryptografische Bewertung steht unter [Kryptografie](kryptografie.html).

### Schnittstellen und Adressierung

- **Ein WireGuard-Interface je Knoten** (`cp-ul0`) mit einem UDP-Port. Ein zweites Interface gibt es nur, wenn eine getrennte physische Storage-Fabric existiert.
- **Innenadressen nur IPv6 (ULA nach RFC 4193):** je Plattform ein /48, je Zelle ein /64, je Knoten eine /128. Die Adressen werden deterministisch aus Vertrauensdomäne, Region, Zelle und Knotenkennung **abgeleitet** – ein Adressregister ist nicht nötig, Konflikte erkennt die Planung. Vorteil: keine Kollision mit IPv4-Heimnetzen, und das physische Netz braucht kein IPv6.
- **Erlaubte Adressen je Peer** sind genau dessen /128. WireGuard authentisiert damit die Absenderadresse – die Grundlage dafür, dass Gossip und VXLAN dem Absender trauen dürfen.
- **Verkehrsklassen** werden über Ports und DSCP unterschieden (Steuerung vor Gossip vor Overlay vor Storage vor Migration), nicht über getrennte Tunnel. Im MVP wird mindestens Steuerungs- und Gossipverkehr priorisiert, damit Storage-Rebalancing auf kleinen Knoten keine Raft-Neuwahlen auslöst.

### Topologie in der Zelle: „Intent-Mesh“

Kernel-WireGuard kennt keinen „Peer auf Zuruf“. Das ist auch nicht nötig, weil der Agent aus dem **Sollzustand** weiß, mit wem er sprechen muss: Steuerungsgruppe und Seeds, Gossip-Partner, Hosts mit Workloads derselben VPCs, Storage-Partner, Gateways und Migrationsziele. Weil das Gossip-Protokoll (SWIM) zufällige Mitglieder prüft, ist das Underlay innerhalb einer Zelle faktisch ein **Vollmesh** (bis knapp 1.000 Peers je Knoten). Peers sind aber erst bei Verkehr aktiv; Konfigurationsänderungen erfolgen per Netlink **inkrementell**, nie als Vollersatz.

### Zwischen Zellen, Standorten und Regionen

| Beziehung | Topologie |
|---|---|
| Zellen derselben Region am selben Standort | direkte Peers bei Bedarf |
| Standorte einer Region | **Relay-Knoten** je Standort (mindestens zwei), Direktverbindungen, wo beide Seiten erreichbar sind |
| Regionen | nur Relay zu Relay, kein regionsübergreifendes Vollmesh |
| Externer Zeuge | Peer der Steuerungsgruppe bzw. eines Relays |

Relays routen im Kernel: Sie entschlüsseln, leiten weiter und verschlüsseln neu. Sie sehen den Underlay-Inhalt also im Klartext. Deshalb ist die Relay-Funktion an eine **hohe Mindest-Vertrauensstufe** des Knotens gebunden (siehe [Sicherheitsmodell](sicherheitsmodell.html)); eine Herabstufung entzieht sie automatisch. Relays, die nur verschlüsselte Pakete durchreichen, sind für eine spätere Phase vorgesehen.

Knoten hinter NAT bauen ausgehende Verbindungen zu den Relays auf (Keepalive nur auf diesen Peers). **Endpunkte** stammen aus einer signierten Selbstauskunft, Gossip liefert Lebendigkeit – aber **nie die Identität**: Der Schlüssel kommt immer aus dem Raft-Zustand.

### Schlüsselverteilung und Rotation

| Schritt | Mechanismus |
|---|---|
| Erzeugung | Der Knoten erzeugt sein Schlüsselpaar lokal bei der Adoption; der private Schlüssel verlässt den Knoten nie und liegt auf der verschlüsselten Datenpartition |
| Veröffentlichung | Der Knoten signiert seine Ankündigung (öffentlicher Schlüssel, nächster Schlüssel, Endpunkte, Innenadresse) mit seinem Knotenschlüssel; jeder Agent prüft sie gegen das Zellregister |
| Verteilung | Jeder Agent beobachtet die Schlüssel seiner Zelle und pflegt sein Interface inkrementell |
| Widerruf | Stilllegung oder Quarantäne entfernt den Eintrag; alle Peers löschen ihn in wenigen Sekunden (Ziel unter 5 s) |
| Rotation | alle 30 Tage, gestaffelt – nie mehrere Knoten einer Zelle gleichzeitig |

Im MVP wird **koordiniert umgeschaltet**: Der Knoten kündigt den nächsten Schlüssel samt Umschaltzeitpunkt an; alle Peers legen vorab einen Eintrag für den neuen Schlüssel an und verschieben zum Zeitpunkt die Adresszuordnung in einem Schritt. Die Unterbrechung schrumpft damit auf die Uhrabweichung. Ein vollständiges „make before break“ mit zweitem Interface folgt in Phase 2. Betreiber können eine Rotation über die API-Aktion `node:rotateUnderlayKey` anstoßen.

### Post-Quanten-Zusatzschlüssel

WireGuard erlaubt einen optionalen Pre-Shared Key, der die Sitzungsschlüssel gegen künftige Quantenangriffe absichert. Die Plattform leitet diese PSKs aus **einer** langlebigen, zeitlich begrenzten **hybriden TLS-1.3-Sitzung** (klassisch + ML-KEM) je Peer-Paar ab – je Zwei-Minuten-Epoche passend zum WireGuard-Rekey, sodass laufende Sitzungen nie unterbrochen werden. Der Kanal läuft außerhalb des Tunnels, ist nur für bekannte Peers geöffnet und hängt nicht von der Steuerungsebene ab. Damit ein längerer Steuerungsausfall das Underlay nicht mitreißt, werden **abgelaufene** Knotenzertifikate in einer Gnadenfrist von 72 Stunden mit Alarm akzeptiert – **widerrufene** oder in Quarantäne genommene Knoten nie. Schlüssel und Netlink-Zugriff liegen in einem privilegierten Hilfsprozess; der Agent selbst kennt nur die öffentliche Sicht.

### Leistung und MTU

**Zielwerte** (VM zu VM über zwei Hosts): Pi 4 mindestens 600 Mbit/s, Pi 5 mindestens 900 Mbit/s, amd64-Server mindestens 5 Gbit/s je Peer-Paar.

| Schicht | Overhead | bei physisch 1.500 | bei Jumbo 9.000 |
|---|---|---|---|
| WireGuard (Worst Case IPv6 außen) | 80 Byte | **1.420** | 8.920 |
| VXLAN über innen IPv6 | 70 Byte | **1.350** | 8.850 |
| Kubernetes mit flannel-VXLAN im VPC | 50 Byte | 1.300 | 8.800 |

Die Underlay-MTU ist unabhängig von der Außen-Adressfamilie fest, damit ein Wechsel zwischen IPv4- und IPv6-Endpunkt nichts ändert. Die VPC-MTU `auto` ist das Minimum über alle beteiligten Standorte, mit Untergrenze 1.280; sie wird per DHCP bzw. Router Advertisement verteilt. Am NAT-Gateway gibt es MSS-Clamping, und ICMP-Meldungen für die Path-MTU-Erkennung werden nie gefiltert.

## Mandanten-Overlay: Technikwahl

Gefordert sind VPCs mit **überlappungsfähigen** Adressräumen, Security Groups, Peering, NAT, Floating IPs, Load-Balancer und DHCP/DNS/Metadaten – bei geringem Speicherbedarf auf Raspberry Pi, **einer einzigen Wahrheit** im eigenen Raft und statischer Stabilität bei Steuerungsausfall.

### Optionen

| Kriterium | OVN/OVS | Cilium (eBPF) | **Eigene Lösung `cp-vnet`** |
|---|---|---|---|
| VPC-Funktionsumfang | sehr vollständig | Pod-Netz eines Kubernetes-Clusters; keine überlappenden Mandanten-Adressräume | muss gebaut werden, der Kernel liefert alle Bausteine |
| VMs erstklassig | ja | nur über Kubernetes | ja (TAP direkt) |
| Zweite Konsens-Datenbank | **ja** (eigene Nord-/Süd-Datenbanken) | ohne Kubernetes: etcd | **nein** |
| Speicher je Host | mehrere Dienste, auf Pi nicht planbar | Agent typischerweise 100–300 MB | nur Modul im vorhandenen Agenten, Datenpfad im Kernel |
| Fehlersuche | OpenFlow-Tabellen, drei Datenbanken | Kubernetes-Wissen nötig | Standard-Linux-Werkzeuge (`ip`, `nft`, `bridge`, `conntrack`) |
| Anschluss EVPN im RZ | möglich | möglich | naheliegend: das Modell entspricht dem Linux-EVPN-Modell |
| Reife | sehr hoch | sehr hoch | neu (eigenes Risiko) |

### Entscheidung für `cp-vnet`

1. **Eine Wahrheit:** OVN bringt eine eigene Raft-geclusterte Datenbank mit; der Sollzustand müsste gespiegelt werden – zwei Konsenssysteme mit unabhängigen Ausfallmodi und doppelter Sicherungsfrage.
2. **Ressourcenbudget:** Ein Pi-Arbeitsknoten soll VMs tragen; ein zusätzlicher Netz-Stack mit eigener Datenbank ist dort nicht planbar.
3. **Cilium passt nicht zur VPC-Semantik** – es bleibt eine Option *innerhalb* von Mandanten-Kubernetes-Clustern.
4. **Linux bringt die Bausteine:** VRF, VXLAN mit statischen Tabellen, nftables mit Sets, conntrack-Zonen, NAT, Flowtables, tc.
5. **Testbarkeit:** Der Controller ist reine Logik (Sollzustand → Netlink-/nftables-Operationen) und lässt sich in Simulation und Netz-Namespaces prüfen.

Risiken werden begrenzt durch einen hart begrenzten MVP-Umfang, **strukturelle** Isolation (VRF + conntrack-Zone + Anti-Spoofing) statt reiner Regeln, Eigenschaftstests „kein Paket zwischen VPCs ohne Peering“ und eine Backend-Schnittstelle, die OVN als spätere Option offenhält – dann als Cache, nicht als Wahrheit. Siehe auch [Rust-Stack](rust-stack.html).

## `cp-vnet` im Überblick

### Datenpfad je Host

| Baustein | Festlegung |
|---|---|
| VPC-Instanz | nur auf Hosts mit Workloads oder Gateway-Funktion des VPC: eine VRF und ein VXLAN-Gerät je VPC |
| Geroutetes Modell | jede VM-Schnittstelle ist ein eigener L3-Link; der Host beantwortet ARP/NDP; Host-Routen je Workload. **Keine L2-Nachbarschaft** zwischen Workloads, kein Broadcast über das Overlay |
| Entfernte Ziele | Route, Neighbor- und FDB-Eintrag werden **statisch** gesetzt – kein Lernen, kein Flooding |
| Kapselung | VXLAN, nur auf dem WireGuard-Interface; Geneve bleibt Option für einen späteren eBPF-Datenpfad |
| Überlappende Adressen | VRF trennt Routing, conntrack-Zone je VPC trennt Verbindungszustand |
| VNI-Vergabe | 24 Bit, je Region; nicht wiederverwendet, solange Logs darauf verweisen |
| Anti-Spoofing | je Schnittstelle nur zugewiesene MAC/IP-Adressen; DHCP- und RA-Antworten aus der VM werden verworfen |
| Verteiltes Routing | Routing zwischen Subnetzen eines VPC auf dem Quell-Host, ohne Umweg über Gateways |

### Steuerungsfluss

1. Ein Nutzer legt über API, Portal oder MCP ein Subnetz oder eine VM an (siehe [API-first](api-first.html)).
2. Der Netz-Controller der Zelle vergibt IP und MAC und bindet die Schnittstelle an einen Host.
3. Der Agent dieses Hosts legt VRF, VXLAN, TAP und Regeln an und meldet „bereit“.
4. Die Agenten aller anderen Hosts im VPC erhalten per gefiltertem Watch den neuen Endpunkt und setzen Route, Neighbor, FDB und Security-Group-Sets.

Die **Wahrheit** (Sollzustand und Bindungen) liegt im Raft der Heimatzelle des Projekts; Gossip wird für das Overlay bewusst nicht genutzt. Ein Host sieht nur die VPCs, an denen er beteiligt ist. Fallen Agent oder Raft aus, bleiben Routen und Regeln im Kernel wirksam; nach einem Neustart gleicht der Agent Ist und Soll ab und schreibt nur Differenzen. Ziel: neue VM innerhalb der Zelle in unter 2 s erreichbar. Details zur Steuerungsebene unter [Steuerungsebene](steuerungsebene.html).

### Security Groups

Security Groups sind zustandsbehaftet und **eingehend default-deny**. Ausgehend erlaubt die Standardgruppe alles; ab dem Betriebsprofil „Standard/C5“ kann der Betreiber ausgehend „deny“ als Leitplanke erzwingen. Regeln referenzieren CIDRs, andere Security Groups oder Präfixlisten; Mitgliedschaften werden als nftables-Sets gepflegt, sodass Änderungen nur Set-Updates sind. Durchgesetzt wird **doppelt** – am Ziel-Host eingehend und am Quell-Host ausgehend –, damit ein kompromittierter Host nur seine eigenen Regeln umgehen kann. Verworfene Pakete fließen ratenbegrenzt in die Flow-Logs. Zustandslose Netz-ACLs auf Subnetzebene folgen in Phase 2.

### DHCP, DNS, Metadaten

| Dienst | Umsetzung |
|---|---|
| DHCPv4/v6, Router Advertisement | lokal je Schnittstelle beantwortet, statische Zuordnung aus dem Sollzustand; kein DHCP-Verkehr im Overlay |
| DNS | je VPC eine Resolver-Adresse, vom lokalen Host beantwortet: interne Zone plus Weiterleitung nach außen mit DNSSEC-Validierung |
| Metadaten / Workload-Identität | bevorzugt über virtio-vsock; die link-lokale Adresse nur mit Pflicht-Token; Antwort nur für die anfragende Schnittstelle |

Weil diese Parser Daten von der Workload-Grenze verarbeiten, laufen sie **nicht** im Hauptprozess des Agenten, sondern in einem Sandbox-Hilfsprozess ohne Zugriff auf den Knotenschlüssel, mit minimalen Rechten, Größenlimits und je eigenem Fuzzing-Ziel. Workload-Identitäten stellt weiterhin der Agent aus (siehe [Identität und Rechte](identitaet.html)).

## Anbindung der Workloads

- **VMs (Cloud Hypervisor):** Der Agent legt die TAP-Schnittstelle an, hängt sie in die VRF und übergibt sie per File-Descriptor an den unprivilegierten Hypervisor-Prozess. Mehrere Schnittstellen je VM sind erlaubt. Bei **Livemigration** baut der Ziel-Host VRF und TAP vorab auf; die Umschaltung ist ein Bindungswechsel plus Gratuitous ARP, Ziel unter 1 s Unterbrechung.
- **Container Instances (Kata):** Ein CNI-Plugin der Plattform (`cp-cni`) legt Namespace und veth-Paar an und hängt die Host-Seite wie eine TAP in die VRF. Die Container Instance ist damit eine normale Schnittstelle im VPC.
- **Managed Kubernetes (k3s):** Mandanten-Cluster laufen auf VMs im Mandanten-VPC. Im MVP nutzt der Cluster flannel (VXLAN im VXLAN, Pod-MTU 1.300); ab Phase 2 folgt ein VPC-natives CNI mit Alias-IP-Bereichen ohne Doppelkapselung. Kubernetes-Services vom Typ `LoadBalancer` werden auf Load-Balancer der Plattform abgebildet.

## Nord-Süd-Verkehr

### Rolle `network-gateway`

| Funktion | Umsetzung | Phase |
|---|---|---|
| NAT-Gateway | SNAT auf Gateway-Knoten, die am VPC teilnehmen | MVP |
| Floating IP | 1:1-NAT auf dem besitzenden Gateway | MVP |
| L4-Load-Balancer | nftables-DNAT mit Hash-Verteilung, Health-Checks durch den Agenten | MVP (extern), Phase 2 (intern verteilt) |
| L7-Load-Balancer, TLS-Terminierung | als eigener Dienst hinter Prozessgrenze | Phase 3 |
| Underlay-Relay | optional auf Gateways (dann gilt die höhere Vertrauensstufe) | MVP für mehrere Standorte |

Je Region gibt es mindestens zwei Gateway-Knoten in verschiedenen Ausfallzonen; Ein-Knoten-Installationen übernehmen die Rolle ohne Redundanz und mit Warnung. Weil Gateways Nord-Süd-Verkehr der Mandanten im Klartext sehen, gilt auch für sie eine Mindest-Vertrauensstufe.

### Floating IPs und Besitz

Floating IPs existieren nur explizit und stammen aus regionalen Pools, die Projekten per Kontingent zugeteilt werden. Jede Floating IP gehört genau einem Gateway; der Besitz ist eine **Raft-Lease mit Fencing-Epoche**. Fällt ein Gateway bestätigt aus, übernimmt ein anderes nach Lease-Ablauf und kündigt die Adresse an. **Ohne Raft-Quorum gibt es keine Umverteilung** – so ist eine Doppelbelegung derselben Adresse ausgeschlossen. Eine VRRP-artige lokale Wahl zwischen Gateways wurde bewusst verworfen.

### Homelab und Rechenzentrum

- **Homelab (`l2announce`):** Floating IPs kommen aus einem LAN-Bereich, den der Betreiber im Heimrouter vom DHCP ausnimmt; der Einrichtungsassistent prüft per ARP auf Belegung. Das besitzende Gateway beantwortet ARP/NDP und sendet bei Übernahme Gratuitous ARP bzw. Unsolicited Neighbor Advertisement. Portweiterleitungen am Heimrouter bleiben Betreiberaufgabe; das Portal zeigt sie an. VPCs nutzen im MVP nur IPv6-ULA, öffentliches IPv6 folgt in Phase 2.
- **Rechenzentrum (BGP/EVPN):** Gateways kündigen Host-Routen per BGP an den Top-of-Rack-Switch an, mit ECMP für Load-Balancer-VIPs. Später kann EVPN die VPC-VXLANs in die Fabric verlängern, weil `cp-vnet` genau das Linux-EVPN-Modell nutzt. Routing-Daemons laufen nur hinter einer Prozessgrenze.

### Plattform-DNS

Die Plattform verwaltet ihre eigenen DNS-Einträge selbst; der zentrale DNS des Betreibers zeigt nur auf den Cluster.

Plattform-Einträge (Portal/API, Knoten, Boot-Dienst, SOA/NS) entstehen automatisch aus dem Cluster-Zustand, eigene Einträge kommen über API, CLI, MCP und Portal hinzu. Angebunden wird per NS-Delegation **und** bedingter Weiterleitung an **zwei feste VIPs je Region**, die automatisch auf gesunde Knoten der Rolle `dns` wandern – mit demselben Lease-und-Fencing-Muster wie Floating IPs. Der autoritative Server `cp-dnsd` ist eine Eigenentwicklung, läuft als eigener Dienst ohne Knotenschlüssel mit Ratenlimits und Fuzzing; DNSSEC ist je Zone einstellbar (standardmäßig an, im Homelab-Profil aus). Mehr dazu unter [Plattform-DNS](dns.html).

**DDoS-Schutz:** Im MVP gibt es Grundwerte im Gateway-Kernel (SYN-Cookies, Verbindungslimits je Floating IP und Quelle); später folgen Bandbreitenlimits je Mandant, Black-Holing per BGP, die Erkennung **ausgehender** Angriffe über Flow-Logs und ein XDP-Frühverwerfer.

## Ausfall und Beobachtbarkeit

| Szenario | Verhalten |
|---|---|
| Agent stürzt ab | WireGuard-Konfiguration und Datenpfad bleiben im Kernel; DHCP/DNS lokal bis zum Neustart (Sekunden) ausgefallen – daher DHCP-Leasezeit mindestens 1 h |
| Raft-Quorum der Zelle fehlt | bestehende VPCs, Security Groups und Floating IPs laufen weiter; Änderungen werden abgelehnt |
| Netzpartition | Minderheitsseite: lokaler Verkehr läuft, keine Floating-IP-Übernahme ohne Quorum |
| Gateway fällt aus | Floating IPs und NAT nach Lease-Ablauf auf anderem Gateway; bestehende NAT-Verbindungen brechen im MVP ab |
| Kompromittierter Host | Widerruf entfernt ihn binnen Sekunden aus allen Peers; er sieht nur den Verkehr der Workloads, die auf ihm liefen |

**Beobachtbarkeit:** Flow-Logs gehören dem **Mandanten**; der Betreiber sieht nur aggregierte, pseudonymisierte Statistik und Mandantendetails nur über einen protokollierten Zugriffsantrag. Hinzu kommen Underlay-Metriken, ein Drift-Zähler (Ist gegen Soll) und ein Topologie-Export für Prüfer.

**API-Ressourcen:** Mandanten arbeiten mit `Vpc`, `Subnet`, `SecurityGroup`, `NetworkInterface`, `NatGateway`, `FloatingIp` und `LoadBalancer`, später mit Peering, Routentabellen und Flow-Log-Konfiguration. Peering zwischen Mandanten verlangt **beidseitige Annahme**; das Anlegen von Floating IPs ist ein eigenes Recht, weil es öffentliche Erreichbarkeit schafft.

## Phasen

| Phase | Inhalt |
|---|---|
| **MVP** | Underlay mit Intent-Mesh und Relays, koordinierte Schlüsselrotation, PQ-PSK; `cp-vnet` mit VPC, Subnetz (IPv4, optional IPv6-ULA), Security Group, Schnittstelle, NAT-Gateway, Floating IP im L2-Modus, externer L4-Load-Balancer; DHCP/DNS/Metadaten lokal; Container Instances; k3s mit flannel; Zonen logisch |
| **Phase 2** | VLAN-Zonen physisch, öffentliches IPv6, Peering, Routentabellen, Netz-ACLs, Flow-Logs, interner verteilter Load-Balancer, VPC-natives CNI, Bandbreitenlimits, BGP, DNSSEC/DoT für Resolver, Topologie-Export, unterbrechungsfreie Schlüsselrotation |
| **Phase 3** | EVPN, zellübergreifende VPCs, direktes NAT-Traversal, Nur-Chiffrat-Relays, eBPF/XDP-Beschleunigung, conntrack-Synchronisation, optionales OVN-Backend, IPsec-Underlay-Profil |

Geprüft wird in Netz-Namespaces in der CI, in virtuellen Umgebungen mit über 100 Knoten, auf echter Pi-Hardware und durch einen externen Penetrationstest der Mandantentrennung. Weitere Hintergründe: [Sicherheitsmodell](sicherheitsmodell.html), [Bedrohungsmodell](bedrohungsmodell.html), [Speicher](speicher.html).
