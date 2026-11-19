title: Architektur
summary: Wie BYOC aufgebaut ist – Agent auf jedem Knoten, Steuerungsebene mit Raft und Gossip, Zellen und Regionen, Netz, OS-Image und Update-Kette.
toc: ja
---
## Überblick in Schichten

BYOC hat keinen zentralen Controller. Auf **jedem Knoten** läuft derselbe Agent
`cp-agent`, der API, Portal und MCP ausliefert, Anfragen an die zuständige Stelle weiterleitet und
den Sollzustand seines Knotens umsetzt. Der gewünschte Zustand liegt in einer **Raft-Gruppe je
Zelle**; Mitgliedschaft und Erreichbarkeit verbreiten sich per **Gossip**. Darunter liegt das
unveränderliche Betriebssystem **cpOS**.

::: html
<figure class="diagram" role="group" aria-labelledby="sch-cap">
<svg viewBox="0 0 860 420" role="img" aria-labelledby="sch-t sch-d">
<title id="sch-t">Schichtenmodell von BYOC</title>
<desc id="sch-d">Oben die Zugänge Portal, REST-API und cpctl, MCP. Darunter der cp-agent auf jedem Knoten mit API-Eingang, Router, Reconcilern, Rollen und Audit. Darunter Steuerungskern mit Raft je Zelle und Gossip. Externe Komponenten wie Hypervisor und Speicher als eigene systemd-Units. Ganz unten cpOS und Hardware.</desc>
<rect class="box2" x="20" y="15" width="820" height="60" rx="10"/>
<text x="40" y="38" class="b">Zugänge – gleichwertig</text>
<rect class="box" x="230" y="27" width="140" height="38" rx="6"/><text x="300" y="51" text-anchor="middle">Web-Portal</text>
<rect class="box" x="390" y="27" width="180" height="38" rx="6"/><text x="480" y="51" text-anchor="middle">REST-API · cpctl · IaC</text>
<rect class="box" x="590" y="27" width="230" height="38" rx="6"/><text x="705" y="51" text-anchor="middle">MCP (KI-Assistenten, Agenten)</text>
<rect class="box3" x="20" y="95" width="820" height="150" rx="10"/>
<text x="40" y="118" class="b">cp-agent – ein Prozess je Knoten</text>
<rect class="box" x="40" y="130" width="180" height="46" rx="6"/><text x="130" y="150" text-anchor="middle">API-Eingang</text><text x="130" y="166" text-anchor="middle" class="s">AuthN/AuthZ, Kontingente</text>
<rect class="box" x="235" y="130" width="180" height="46" rx="6"/><text x="325" y="150" text-anchor="middle">Router</text><text x="325" y="166" text-anchor="middle" class="s">URN → Region/Zelle → Leader</text>
<rect class="box" x="430" y="130" width="190" height="46" rx="6"/><text x="525" y="150" text-anchor="middle">Reconciler</text><text x="525" y="166" text-anchor="middle" class="s">Zellen-Controller, Knoten</text>
<rect class="box" x="635" y="130" width="185" height="46" rx="6"/><text x="727" y="150" text-anchor="middle">Audit · Telemetrie</text><text x="727" y="166" text-anchor="middle" class="s">signiert, hash-verkettet</text>
<rect class="box" x="40" y="188" width="380" height="44" rx="6"/><text x="230" y="208" text-anchor="middle">Steuerungskern: Raft (Zustand) · Gossip (Mitgliedschaft)</text><text x="230" y="224" text-anchor="middle" class="s">eigene Laufzeit, priorisiert</text>
<rect class="box" x="430" y="188" width="390" height="44" rx="6"/><text x="625" y="208" text-anchor="middle">Rollen als Module</text><text x="625" y="224" text-anchor="middle" class="s">control · boot · dns · identity · compute · storage · gateway …</text>
<rect class="box4" x="20" y="265" width="820" height="56" rx="10"/>
<text x="40" y="288" class="b">Getrennte Prozesse</text>
<text x="40" y="308" class="s">Sandbox-Dienste ohne Knotenschlüssel (Netzboot, DNS) · privilegierter Hilfsdienst mit festem Befehlssatz · Hypervisor, Speicher- und Netzdienste als systemd-Units</text>
<rect class="box" x="20" y="340" width="820" height="60" rx="10"/>
<text x="40" y="364" class="b">cpOS + Hardware</text>
<text x="40" y="385" class="s">unveränderliches /usr (dm-verity, A/B) · Secure/Measured Boot · TPM2 + LUKS2 · amd64, arm64, Raspberry Pi</text>
<path class="ln" d="M430 75 V93"/><path class="ln" d="M430 245 V263"/><path class="ln" d="M430 321 V338"/>
</svg>
<figcaption id="sch-cap">Schichtenmodell. Ein Neustart des Agenten beendet keine Workloads, weil externe Komponenten als eigene systemd-Units laufen.</figcaption>
</figure>
:::

Wichtige Grundsätze:

- **Zwei Ebenen der Wahrheit.** Raft hält den gewünschten Zustand, Zuweisungen und Leases. Gossip
  transportiert Mitgliedschaft, Erreichbarkeit und kurzlebige Metadaten – und löst **nie allein**
  eine destruktive Aktion aus.
- **Statische Stabilität.** Fällt die Steuerungsebene aus, laufen alle Workloads weiter; Knoten
  arbeiten mit dem zuletzt bekannten Sollzustand.
- **Reconciler sind level-getrieben, idempotent und abgesichert.** Zellen-Controller laufen als
  Shards mit Leases; jeder Schreibzugriff trägt ein Epochen-Token, veraltete Schreiber werden
  abgewiesen.
- **Parser an Vertrauensgrenzen** (Netzboot, DNS, Eingaben von Geräten) laufen in eigenen
  Sandbox-Prozessen ohne Zugriff auf den Knotenschlüssel.

Details: [Architektur der Steuerungsebene](doku/steuerungsebene.html) ·
[Rust-Stack](doku/rust-stack.html).

## Zellen und Regionen

Eine **Zelle** ist die Einheit für Konsens und Fehlerisolation (Richtwert bis etwa 1.000 Knoten).
Mehrere Zellen bilden eine **Region**; eine kleine Regions-Raft-Gruppe hält regionsweite Daten.
Bei nur einer Zelle fallen beide Gruppen zusammen. Anfragen werden über die **URN** der Ressource
und eine versionierte Shard-Karte zur richtigen Zelle geleitet.

::: html
<figure class="diagram" role="group" aria-labelledby="zel-cap">
<svg viewBox="0 0 860 300" role="img" aria-labelledby="zel-t zel-d">
<title id="zel-t">Region mit mehreren Zellen</title>
<desc id="zel-d">Eine Region enthält eine kleine Regions-Raft-Gruppe und mehrere Zellen. Jede Zelle hat eine Steuerungsgruppe mit drei oder fünf Votern und viele Arbeitsknoten, verbunden per Gossip.</desc>
<rect class="box2" x="10" y="10" width="840" height="280" rx="12"/>
<text x="30" y="34" class="b">Region</text>
<rect class="box4" x="300" y="22" width="260" height="40" rx="8"/><text x="430" y="47" text-anchor="middle">Regions-Raft (Mandanten, Identität, Karte)</text>
<g>
<rect class="box3" x="30" y="80" width="390" height="190" rx="10"/><text x="50" y="102" class="b">Zelle A</text>
<text x="50" y="124" class="s">Steuerungsgruppe (Raft, 3 oder 5 Voter)</text>
<circle class="box2" cx="80" cy="152" r="18"/><text x="80" y="157" text-anchor="middle" class="s">L</text>
<circle class="box2" cx="130" cy="152" r="18"/><circle class="box2" cx="180" cy="152" r="18"/>
<text x="50" y="200" class="s">Arbeitsknoten (Gossip/SWIM)</text>
<g class="nodes"><rect class="box" x="50" y="210" width="34" height="26" rx="4"/><rect class="box" x="92" y="210" width="34" height="26" rx="4"/><rect class="box" x="134" y="210" width="34" height="26" rx="4"/><rect class="box" x="176" y="210" width="34" height="26" rx="4"/><rect class="box" x="218" y="210" width="34" height="26" rx="4"/><rect class="box" x="260" y="210" width="34" height="26" rx="4"/><rect class="box" x="302" y="210" width="34" height="26" rx="4"/><rect class="box" x="344" y="210" width="34" height="26" rx="4"/></g>
<path class="ln dash" d="M130 170 V208"/>
</g>
<g>
<rect class="box3" x="440" y="80" width="390" height="190" rx="10"/><text x="460" y="102" class="b">Zelle B</text>
<text x="460" y="124" class="s">Steuerungsgruppe (Raft, 3 oder 5 Voter)</text>
<circle class="box2" cx="490" cy="152" r="18"/><text x="490" y="157" text-anchor="middle" class="s">L</text>
<circle class="box2" cx="540" cy="152" r="18"/><circle class="box2" cx="590" cy="152" r="18"/><circle class="box2" cx="640" cy="152" r="18"/><circle class="box2" cx="690" cy="152" r="18"/>
<text x="460" y="200" class="s">Arbeitsknoten (Gossip/SWIM)</text>
<rect class="box" x="460" y="210" width="34" height="26" rx="4"/><rect class="box" x="502" y="210" width="34" height="26" rx="4"/><rect class="box" x="544" y="210" width="34" height="26" rx="4"/><rect class="box" x="586" y="210" width="34" height="26" rx="4"/><rect class="box" x="628" y="210" width="34" height="26" rx="4"/><rect class="box" x="670" y="210" width="34" height="26" rx="4"/><rect class="box" x="712" y="210" width="34" height="26" rx="4"/><rect class="box" x="754" y="210" width="34" height="26" rx="4"/>
<path class="ln dash" d="M540 170 V208"/>
</g>
<path class="ln" d="M380 62 L230 80"/><path class="ln" d="M480 62 L630 80"/>
</svg>
<figcaption id="zel-cap">Region mit zwei Zellen. „L“ markiert den Raft-Leader. Der Ausfall einer Zelle betrifft nur diese Zelle.</figcaption>
</figure>
:::

| Knoten | Steuerungsgruppe | Zellen | Bemerkung |
|---|---|---|---|
| 2 | 2 + Zeuge | 1 | Zeuge (z. B. kleiner Raspberry Pi) zwingend für das Quorum |
| 3–20 | 3 | 1 | Standard-Homelab |
| 20 – ca. 1.000 | 5 | 1 | Gossip für Mitgliedschaft, Raft nur für Zustand |
| > ca. 1.000 | 5 je Zelle | n | Regions-Ebene koordiniert Zellen |
| mehrere Standorte | je Region | n | Verbund mit globaler Identität (spätere Phase) |

Die Steuerungsgruppe wird **automatisch** gebildet und wächst mit: ein Knoten → zwei Datenknoten
plus Zeuge → drei → fünf Voter. Neue Mitglieder starten als Learner und werden erst nach dem
Aufholen befördert; es gibt immer nur eine Mitgliedschaftsänderung gleichzeitig.

## Zwei Knoten mit Zeuge

Zwei Knoten allein können bei einer Netztrennung nicht entscheiden, wer weiterarbeiten darf. Ein
**Zeuge** – ein leichter Voter ohne Nutzdaten, der selbst nie Leader wird – liefert die dritte
Stimme. Fällt ein Datenknoten aus, arbeitet der andere mit dem Zeugen weiter. Ist nur noch ein
Knoten übrig, ist der Restbetrieb **nur lesend**; Schreiben ohne Quorum gibt es nur über ein
protokolliertes Break-Glass-Verfahren, nie automatisch.

::: html
<figure class="diagram" role="group" aria-labelledby="zg-cap">
<svg viewBox="0 0 860 160" role="img" aria-labelledby="zg-t zg-d">
<title id="zg-t">Zwei-Knoten-Betrieb mit Zeuge</title>
<desc id="zg-d">Zwei Datenknoten replizieren den Raft-Zustand. Ein Zeuge stimmt mit ab, hält aber keine Nutzdaten.</desc>
<rect class="box3" x="60" y="40" width="220" height="80" rx="10"/><text x="170" y="74" text-anchor="middle" class="b">Knoten 1</text><text x="170" y="96" text-anchor="middle" class="s">control · Daten · Voter</text>
<rect class="box3" x="580" y="40" width="220" height="80" rx="10"/><text x="690" y="74" text-anchor="middle" class="b">Knoten 2</text><text x="690" y="96" text-anchor="middle" class="s">control · Daten · Voter</text>
<rect class="box4" x="355" y="50" width="150" height="60" rx="10"/><text x="430" y="76" text-anchor="middle" class="b">Zeuge</text><text x="430" y="96" text-anchor="middle" class="s">Stimme, keine Nutzdaten</text>
<path class="ln" d="M280 70 H353"/><path class="ln" d="M505 70 H578"/>
<path class="ln dash" d="M280 112 C 400 150, 460 150, 580 112"/><text x="430" y="150" text-anchor="middle" class="s">Raft-Replikation des Zustands</text>
</svg>
<figcaption id="zg-cap">Zwei Knoten plus Zeuge ergeben ein Quorum von drei Stimmen.</figcaption>
</figure>
:::

## Netzwerk

Die Plattform trennt Netze **immer kryptografisch** und, wo die Infrastruktur es erlaubt,
zusätzlich physisch über VLANs oder geroutete Segmente.

::: html
<figure class="diagram" role="group" aria-labelledby="net-cap">
<svg viewBox="0 0 860 250" role="img" aria-labelledby="net-t net-d">
<title id="net-t">Underlay und Mandanten-Overlay</title>
<desc id="net-d">Physisches Netz unten. Darüber das WireGuard-Underlay zwischen allen Knoten, IPv6 innen. Darüber Mandanten-VPCs als VRF mit VXLAN, ausschließlich im WireGuard-Tunnel transportiert. Nord-Süd-Verkehr über network-gateway-Knoten.</desc>
<rect class="box" x="20" y="190" width="820" height="44" rx="8"/><text x="430" y="217" text-anchor="middle">Physisches Netz: flat (ein LAN) · vlan · routed (L3 bis zum Host, BGP)</text>
<rect class="box2" x="20" y="125" width="820" height="50" rx="8"/><text x="430" y="148" text-anchor="middle" class="b">Underlay: WireGuard je Knoten, innen IPv6</text><text x="430" y="166" text-anchor="middle" class="s">Peers aus Raft (Schlüssel) und Gossip (Endpunkte) · zusätzlicher Post-Quanten-PSK · mTLS für Steuerung</text>
<rect class="box3" x="20" y="20" width="250" height="90" rx="8"/><text x="145" y="45" text-anchor="middle" class="b">VPC Mandant A</text><text x="145" y="66" text-anchor="middle" class="s">VRF · VXLAN im Tunnel</text><text x="145" y="84" text-anchor="middle" class="s">Sicherheitsgruppen (default-deny)</text>
<rect class="box3" x="290" y="20" width="250" height="90" rx="8"/><text x="415" y="45" text-anchor="middle" class="b">VPC Mandant B</text><text x="415" y="66" text-anchor="middle" class="s">VRF · VXLAN im Tunnel</text><text x="415" y="84" text-anchor="middle" class="s">lokales DHCP/DNS/Metadaten je Host</text>
<rect class="box4" x="560" y="20" width="280" height="90" rx="8"/><text x="700" y="45" text-anchor="middle" class="b">network-gateway</text><text x="700" y="66" text-anchor="middle" class="s">NAT · Floating IPs · L4-Load-Balancer</text><text x="700" y="84" text-anchor="middle" class="s">Bekanntgabe per L2 oder BGP</text>
<path class="ln" d="M145 110 V123"/><path class="ln" d="M415 110 V123"/><path class="ln" d="M700 110 V123"/>
</svg>
<figcaption id="net-cap">Overlay-Pakete verlassen einen Knoten nur verschlüsselt im WireGuard-Underlay.</figcaption>
</figure>
:::

Details: [Netzwerkarchitektur](doku/netzwerk.html) · [Plattform-DNS](doku/dns.html).

## Boot- und Vertrauenskette

Jeder Start beginnt bei signierten Vorgaben. Die Kette ist auf UEFI-Systemen und Raspberry Pi
unterschiedlich umgesetzt, folgt aber demselben Prinzip.

::: html
<figure class="diagram" role="group" aria-labelledby="boot-cap">
<svg viewBox="0 0 860 150" role="img" aria-labelledby="boot-t boot-d">
<title id="boot-t">Boot- und Vertrauenskette auf UEFI-Systemen</title>
<desc id="boot-d">Firmware mit Secure Boot, signierter Bootloader, signiertes Unified Kernel Image, schreibgeschütztes /usr per dm-verity, entsperrte Zustandspartition per TPM, cp-agent, Health-Gate.</desc>
<defs><marker id="ah2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path class="arrowhead" d="M0,0 L10,5 L0,10 z"/></marker></defs>
<rect class="box" x="10" y="40" width="110" height="60" rx="8"/><text x="65" y="66" text-anchor="middle">Firmware</text><text x="65" y="84" text-anchor="middle" class="s">Secure Boot</text>
<rect class="box" x="135" y="40" width="110" height="60" rx="8"/><text x="190" y="66" text-anchor="middle">Bootloader</text><text x="190" y="84" text-anchor="middle" class="s">signiert</text>
<rect class="box2" x="260" y="40" width="110" height="60" rx="8"/><text x="315" y="66" text-anchor="middle">UKI</text><text x="315" y="84" text-anchor="middle" class="s">Kernel+Initrd+Cmdline</text>
<rect class="box2" x="385" y="40" width="110" height="60" rx="8"/><text x="440" y="66" text-anchor="middle">/usr</text><text x="440" y="84" text-anchor="middle" class="s">dm-verity, A/B</text>
<rect class="box2" x="510" y="40" width="110" height="60" rx="8"/><text x="565" y="66" text-anchor="middle">Zustand</text><text x="565" y="84" text-anchor="middle" class="s">LUKS2 + TPM2</text>
<rect class="box3" x="635" y="40" width="100" height="60" rx="8"/><text x="685" y="66" text-anchor="middle">cp-agent</text><text x="685" y="84" text-anchor="middle" class="s">gehärtet</text>
<rect class="box3" x="750" y="40" width="100" height="60" rx="8"/><text x="800" y="66" text-anchor="middle">Health-Gate</text><text x="800" y="84" text-anchor="middle" class="s">Boot gültig</text>
<path class="ln" d="M120 70 H133" marker-end="url(#ah2)"/><path class="ln" d="M245 70 H258" marker-end="url(#ah2)"/><path class="ln" d="M370 70 H383" marker-end="url(#ah2)"/><path class="ln" d="M495 70 H508" marker-end="url(#ah2)"/><path class="ln" d="M620 70 H633" marker-end="url(#ah2)"/><path class="ln" d="M735 70 H748" marker-end="url(#ah2)"/>
<text x="430" y="130" text-anchor="middle" class="s">Messwerte (PCR) fließen in die TPM-Richtlinie; nur ein unverändertes, signiertes System entsperrt die Zustandspartition.</text>
</svg>
<figcaption id="boot-cap">Boot- und Vertrauenskette (UEFI). Raspberry Pi nutzt den nativen Bootloader mit eigenem A/B-Mechanismus.</figcaption>
</figure>
:::

`/` ist ein flüchtiges tmpfs, `/etc` wird bei jedem Start aus den signierten Vorgaben erzeugt.
Persistenz gibt es nur in der verschlüsselten Zustandspartition. Rollenspezifische Laufzeiten
(Hypervisor, Speicher, Kubernetes) kommen als signierte System-Erweiterungen hinzu.
Details: [OS-Image](doku/os-image.html) · [Boot und Adoption](doku/boot-adoption.html) ·
[Sicherheitsmodell](doku/sicherheitsmodell.html).

## Release- und Update-Kette

::: html
<figure class="diagram" role="group" aria-labelledby="upd-cap">
<svg viewBox="0 0 860 210" role="img" aria-labelledby="upd-t upd-d">
<title id="upd-t">Weg eines Updates</title>
<desc id="upd-d">Reproduzierbarer Bau, offline Signatur, Release-Bündel, Import und Prüfung in der Plattform, Rollout-Controller in Wellen, Knoten schreibt inaktiven Slot, Neustart, Health-Gate. Bei Fehler automatischer Rückfall auf den alten Slot und Anhalten des Rollouts.</desc>
<defs><marker id="ah3" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path class="arrowhead" d="M0,0 L10,5 L0,10 z"/></marker></defs>
<rect class="box" x="10" y="30" width="120" height="60" rx="8"/><text x="70" y="56" text-anchor="middle">Bau</text><text x="70" y="74" text-anchor="middle" class="s">reproduzierbar, SBOM</text>
<rect class="box" x="150" y="30" width="120" height="60" rx="8"/><text x="210" y="56" text-anchor="middle">Signatur</text><text x="210" y="74" text-anchor="middle" class="s">offline, TUF-Rollen</text>
<rect class="box2" x="290" y="30" width="120" height="60" rx="8"/><text x="350" y="56" text-anchor="middle">Release-Bündel</text><text x="350" y="74" text-anchor="middle" class="s">Manifest + Artefakte</text>
<rect class="box2" x="430" y="30" width="120" height="60" rx="8"/><text x="490" y="56" text-anchor="middle">Import</text><text x="490" y="74" text-anchor="middle" class="s">Prüfung, Dedup</text>
<rect class="box3" x="570" y="30" width="130" height="60" rx="8"/><text x="635" y="56" text-anchor="middle">Rollout</text><text x="635" y="74" text-anchor="middle" class="s">Wellen, Gates</text>
<rect class="box3" x="720" y="30" width="130" height="60" rx="8"/><text x="785" y="56" text-anchor="middle">Knoten</text><text x="785" y="74" text-anchor="middle" class="s">inaktiver Slot</text>
<path class="ln" d="M130 60 H148" marker-end="url(#ah3)"/><path class="ln" d="M270 60 H288" marker-end="url(#ah3)"/><path class="ln" d="M410 60 H428" marker-end="url(#ah3)"/><path class="ln" d="M550 60 H568" marker-end="url(#ah3)"/><path class="ln" d="M700 60 H718" marker-end="url(#ah3)"/>
<rect class="box3" x="720" y="130" width="130" height="50" rx="8"/><text x="785" y="152" text-anchor="middle">Health-Gate grün</text><text x="785" y="168" text-anchor="middle" class="s">neuer Stand gilt</text>
<rect class="box4" x="520" y="130" width="180" height="50" rx="8"/><text x="610" y="152" text-anchor="middle">Gate rot</text><text x="610" y="168" text-anchor="middle" class="s">Rückfall, Rollout hält an</text>
<path class="ln" d="M785 90 V128" marker-end="url(#ah3)"/><path class="ln dash" d="M760 90 L690 128" marker-end="url(#ah3)"/>
</svg>
<figcaption id="upd-cap">Release- und Update-Kette. Agent, Installer und Import prüfen ein Bündel nach denselben Regeln.</figcaption>
</figure>
:::

Details: [Rollout-Controller](doku/rollout.html) · [Release-Bündel](doku/release-buendel.html) ·
[Release-Signatur](doku/release-signatur.html).

## Technologieentscheidungen

| Bereich | Entscheidung |
|---|---|
| Sprache | Rust (Edition 2024), `unsafe` grundsätzlich verboten, Ausnahmen nur registriert |
| Laufzeit | tokio, axum (REST, SSE, MCP), tonic/gRPC intern mit mTLS |
| Konsens / Mitgliedschaft | openraft je Zelle, SWIM-Gossip (foca) |
| Lokaler Speicher | redb (eingebettet) |
| Autorisierung | eigener Beziehungsspeicher + Cedar-Richtlinien |
| Virtualisierung | Cloud Hypervisor/KVM, MicroVMs für Container |
| Objektspeicher | Garage hinter eigenem S3-Frontend |
| OS-Image | mkosi aus Debian-13-Paketen, systemd-Bausteine (UKI, repart, sysupdate, sysext) |
| Portal | Single-Page-App mit Svelte 5 und Vite, aus dem API-Schema generierte Typen und Formulare |
| Architekturen | amd64 und arm64 (inkl. Raspberry Pi 4/5), Cross-Compilation |

Begründungen: [ADR Rust-Stack](doku/rust-stack.html) · [ADR Portal-Technologie](doku/portal.html).
