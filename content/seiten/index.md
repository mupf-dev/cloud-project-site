title: Start
summary: Quelloffene, dezentrale und mandantenfähige Cloud-Plattform in Rust – vom 2-Knoten-Homelab bis zum Rechenzentrum mit tausenden Knoten.
hero: ja
---
::: html
<section class="hero" aria-labelledby="hero-titel">
  <h1 id="hero-titel">Die eigene Cloud – dezentral, quelloffen, mandantenfähig.</h1>
  <p class="lead">cloud-project macht aus beliebiger Hardware – Raspberry Pi, Notebook, Mini-PC oder Rack-Server – eine Cloud mit den Grunddiensten eines Hyperscalers. Vom Homelab mit zwei Knoten bis zum Rechenzentrum mit tausenden Knoten, ohne zentralen Controller.</p>
  <p class="tagline">Kabel rein → Knoten erscheint → freigeben → Rolle zuweisen → fertig.</p>
  <div class="buttons">
    <a class="btn primary" href="funktionen.html">Funktionsumfang</a>
    <a class="btn" href="architektur.html">Architektur</a>
    <a class="btn" href="doku/index.html">Dokumentation</a>
  </div>
</section>
<ul class="stats" aria-label="Eckdaten">
  <li><b>2 – 10.000+</b><span>Knoten je Installation, in Zellen und Regionen</span></li>
  <li><b>3 Zugänge</b><span>API, Web-Portal und MCP mit gleichem Funktionsumfang</span></li>
  <li><b>ARM64 + x86_64</b><span>gemischt ab dem ersten Tag</span></li>
  <li><b>Rust</b><span>Kern, Agent und Dienste; AGPL-3.0-or-later</span></li>
</ul>
:::

## Worum es geht

Öffentliche Clouds bieten Komfort: Maschinen, Speicher und Netze per Klick oder API. Wer Daten,
Kosten und Abhängigkeiten selbst in der Hand behalten will, muss diesen Komfort heute aus vielen
Einzelprodukten zusammenbauen und pflegen. **cloud-project** verfolgt einen anderen Weg: Eine
einheitliche Plattform übernimmt Hardware per Netzwerk- oder USB-Boot, verwaltet sie als Pool und
stellt darauf Dienste bereit, die sich wie die eines Hyperscalers anfühlen – virtuelle Maschinen,
Container, Managed Kubernetes, Block- und Objektspeicher, virtuelle Netze, Identitäten, DNS und
KI-Inferenz.

Die Plattform läuft **auf der Hardware, die sie steuert**. Jeder Knoten trägt denselben Agenten;
Portal, API und MCP-Server sind auf jedem Knoten erreichbar. Fällt ein Knoten aus, übernimmt ein
anderer.

## Leitprinzipien

::: html
<ul class="cards">
  <li><div class="card"><strong>Dezentral</strong><span>Kein zentraler Controller. Zustand über Raft je Zelle, Mitgliedschaft über Gossip. Ausfall der Steuerung stoppt keine laufenden Workloads.</span></div></li>
  <li><div class="card"><strong>API-first, drei gleichwertige Zugänge</strong><span>Jede Funktion auf jeder Ebene über API, Portal und MCP – auch Ersteinrichtung und Adoption. Die Gleichwertigkeit wird in der CI geprüft.</span></div></li>
  <li><div class="card"><strong>Zero-Touch nach dem Kabel</strong><span>Kein Bildschirm, keine Tastatur, kein SSH. Einzige bewusste Handlung ist die Freigabe (Adoption) eines neuen Knotens.</span></div></li>
  <li><div class="card"><strong>Skaliert in beide Richtungen</strong><span>Zwei Knoten sind ein vollwertiger Betriebsmodus. Wachstum auf tausende Knoten über Zellen und Regionen ohne Neuinstallation.</span></div></li>
  <li><div class="card"><strong>Unveränderliche Knoten</strong><span>Eigenes Image-OS cpOS mit dm-verity, A/B-Updates, Secure Boot und TPM-gebundener Verschlüsselung.</span></div></li>
  <li><div class="card"><strong>Secure &amp; Compliant by Design</strong><span>mTLS überall, Mandantentrennung auf allen Schichten, lückenloses Audit, Nachweise für ISO 27001 und BSI IT-Grundschutz.</span></div></li>
  <li><div class="card"><strong>Open Source durchgehend</strong><span>Nur quelloffene Abhängigkeiten, eigene Komponenten in Rust, signierte Releases mit SBOM.</span></div></li>
  <li><div class="card"><strong>Bewährtes integrieren</strong><span>Kein eigener Hypervisor, kein Dateisystem von Null: Die Plattform baut Steuerung, Automatisierung und die einheitliche Oberfläche.</span></div></li>
</ul>
:::

## Für wen?

| Stufe | Knoten | Typische Hardware | Besonderheit |
|---|---|---|---|
| **Homelab** | 2–10 | Raspberry Pi, alte Notebooks, Mini-PCs | 2-Knoten-Betrieb mit Zeuge, koexistiert mit dem DHCP des Routers |
| **Edge / KMU** | 10–100 | Mini-PCs, Server | mehrere Mandanten, erste Compliance-Anforderungen |
| **Rechenzentrum** | 100–10.000+ | Rack-Server mit BMC | Zellen und Regionen, mehrere Standorte, Zertifizierung des Betreibers |

Der erste Schwerpunkt ist das Homelab – die Architektur enthält aber keine Entscheidung, die das
Rechenzentrum verbaut.

## So sieht das aus

Ein neuer Knoten bootet per Netzwerk, meldet seine Hardware und wartet in der Quarantäne auf
Freigabe. Das geht im Portal, per API oder über einen KI-Assistenten via MCP – mit identischem
Ergebnis:

```sh
$ cpctl list discoveries
NAME        ARCH     CPU  RAM    DISKS        TRUST  CODE
d-7f3a91    arm64    4    8 GiB  1× 256 GB    T1     482-913
$ cpctl discovery adopt d-7f3a91 --node-name node-03 --dry-run
$ cpctl discovery adopt d-7f3a91 --node-name node-03 --confirmation-token <token> --wait
$ cpctl list nodes
NAME     ROLES                    STATE           VERSION
node-01  control,boot             Aktiv           0.4.0
node-02  control,compute-vm       Aktiv           0.4.0
node-03  -                        Bereitgestellt  0.4.0
```

*(Ausgabe beispielhaft; Befehle und Felder können sich bis zum ersten Release ändern.)*

## Projektstand

Die Architektur ist abgenommen (Meilenstein „Architektur steht“, November 2026). Die Phase
„Fundament“ läuft: Agent, Steuerungsebene, OS-Image, Boot und Adoption, Release- und
Update-Kette sowie Plattform-DNS entstehen. Mehr unter [Status & Roadmap](roadmap.html).

> Das Projekt ist noch nicht für den Produktiveinsatz bereit. Der Quellcode wird veröffentlicht,
> sobald Lizenzdateien, Sicherheitsrichtlinie und REUSE-Konformität vollständig stehen.
