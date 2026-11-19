title: Status und Roadmap
summary: Was BYOC heute kann, wie es nachgewiesen ist, was selbst entwickelt und was eingebunden ist – und was bis MVP und Release 1.0 noch folgt.
toc: ja
---
## Auf einen Blick {#ueberblick}

> **Alpha, vor dem ersten Release.** Version 0.x, alle API-Gruppen in `v1alpha1`. BYOC ist
> **nicht für den Produktiveinsatz geeignet**; Schnittstellen und Formate können sich noch ändern.
> BYOC (Build Your Own Cloud) ist ein Alpha-Name. Zeitangaben auf dieser Seite sind Planwerte,
> keine Zusagen.

::: html
<ol class="rm-phases" aria-label="Phasen von BYOC">
<li class="done"><span class="n">Phase</span><strong>Konzept und Architektur</strong><span class="status-ok">Abgeschlossen</span><p>Meilenstein „Architektur steht“ am 2026-11-12.</p></li>
<li class="run"><span class="n">Phase</span><strong>Fundament</strong><span class="status-run">Weitgehend umgesetzt</span><p>OS-Image, Cluster-Kern, Zugänge, Identität, Underlay; Updates und DNS in Abnahme.</p></li>
<li class="next"><span class="n">Meilenstein</span><strong>Kabel rein → Knoten im Cluster</strong><span class="status-run">In Arbeit</span><p>Zweiter Knoten per Netzboot auf echter Hardware. Geplant: Q1 2027.</p></li>
<li><span class="n">Meilenstein</span><strong>MVP Homelab</strong><span class="status-plan">Geplant</span><p>Mandanten, VMs, Container, Kubernetes, Speicher, Netz-Dienste. Zielplanung: Q2 2027.</p></li>
<li><span class="n">Meilenstein</span><strong>Release 1.0</strong><span class="status-plan">Geplant</span><p>Erweiterte Dienste, KI-Inferenz, mehrere Regionen. Zielplanung: Mitte 2027.</p></li>
</ol>
:::

Die Übersicht zeigt je Bereich den Stand und die Art der Umsetzung. Ein Klick führt zur Beschreibung.

::: html
<ul class="rm-legend" aria-label="Legende">
<li><span class="status-ok">Erreicht</span><span>umgesetzt und im Lab nachgewiesen</span></li>
<li><span class="status-review">In Abnahme</span><span>umgesetzt, Abnahme steht aus</span></li>
<li><span class="status-run">Teilweise</span><span>Grundlage steht, Teile folgen</span></li>
<li><span class="status-plan">Geplant</span><span>Konzept entschieden, Umsetzung folgt</span></li>
<li><span class="kind own">Eigen</span><span>vollständig selbst entwickelt</span></li>
<li><span class="kind lib">Eigen + Bibliothek</span><span>eigene Implementierung auf bewährten Bibliotheken</span></li>
<li><span class="kind mix">Eigen + Eingebunden</span><span>eigene Steuerung, bestehende Lösung als eigenständige Komponente</span></li>
<li><span class="kind ext">Eingebunden</span><span>bestehende Lösung, unverändert eingesetzt</span></li>
</ul>
<ul class="rm-matrix" aria-label="Stand je Bereich">
<li><a href="#os-image">OS-Image und Boot (cpOS)</a><span class="status-ok">Erreicht</span><span class="kind mix">Eigen + Eingebunden</span></li>
<li><a href="#netzboot">Netzboot-Dienst</a><span class="status-ok">Erreicht (Lab)</span><span class="kind mix">Eigen + Eingebunden</span></li>
<li><a href="#adoption">Erstknoten, Adoption und Installer</a><span class="status-ok">Erreicht</span><span class="kind mix">Eigen + Eingebunden</span></li>
<li><a href="#steuerungsebene">Steuerungsebene: Raft, Gossip, Zellen</a><span class="status-ok">Erreicht</span><span class="kind lib">Eigen + Bibliothek</span></li>
<li><a href="#knotensicherheit">Knoten-Identität und Kryptografie</a><span class="status-ok">Erreicht</span><span class="kind lib">Eigen + Bibliothek</span></li>
<li><a href="#identitaet">Identität und Mandanten</a><span class="status-run">Teilweise</span><span class="kind lib">Eigen + Bibliothek</span></li>
<li><a href="#zugaenge">API, Portal, MCP und CLI mit Parität</a><span class="status-ok">Erreicht</span><span class="kind lib">Eigen + Bibliothek</span></li>
<li><a href="#updates">Updates und Releases</a><span class="status-review">In Abnahme</span><span class="kind mix">Eigen + Eingebunden</span></li>
<li><a href="#plattform-dns">Plattform-DNS</a><span class="status-review">In Abnahme</span><span class="kind lib">Eigen + Bibliothek</span></li>
<li><a href="#netzwerk">Netzwerk: WireGuard-Underlay</a><span class="status-ok">Erreicht</span><span class="kind mix">Eigen + Eingebunden</span></li>
<li><a href="#speicher">Speicher</a><span class="status-plan">Geplant</span><span class="kind mix">Eigen + Eingebunden</span></li>
<li><a href="#lieferkette">Lieferkette und Compliance</a><span class="status-ok">Erreicht</span><span class="kind ext">Eingebunden</span></li>
<li><a href="#testlabs">Test- und Lab-Infrastruktur</a><span class="status-ok">Erreicht</span><span class="kind mix">Eigen + Eingebunden</span></li>
</ul>
:::

## Eigenentwicklung – und wann nicht {#eigenentwicklung}

Grundsatz des Projekts: **Was die Plattform steuert, entwickelt BYOC selbst** – in Rust, passend
zum gemeinsamen Raft-Zustand, zum Rechtemodell und zur Parität von API, Portal und MCP. Bestehende
Lösungen werden nur **begründet** eingebunden, und zwar dort, wo Reife, Sicherheit oder Pflegeaufwand
den Eigenbau nicht rechtfertigen: Linux-Kernel-Funktionen, der Hypervisor, Container-Laufzeiten,
Datenbank- und Speicher-Engines mit großem Pflegeaufwand sowie Prüfwerkzeuge der Lieferkette.
Eingebundene Komponenten laufen hinter klaren Prozessgrenzen. Rust-Bibliotheken nennt diese Seite nur,
wenn sie tragend sind. Die vollständige Abwägung je Funktion steht in der
[Hyperscaler-Funktionsanalyse](doku/funktionsanalyse.html).

## Was erreicht ist {#erreicht}

Alles in diesem Abschnitt ist umgesetzt und mindestens in einem automatisierten Lab nachgewiesen. Wo
der Nachweis auf echter Hardware noch aussteht, steht das dabei.

### OS-Image und Boot (cpOS) {#os-image}

::: html
<p class="rm-tags"><span class="status-ok">Erreicht</span><span class="kind mix">Eigen + Eingebunden</span></p>
:::

Unveränderliches Knoten-Betriebssystem für amd64 und arm64 (UEFI). `/usr` ist schreibgeschützt und
per dm-verity gegen Veränderung gesichert, es gibt zwei Slots (A/B) für Updates. Kernel, Initrd und
Kommandozeile stecken in einem signierten Unified Kernel Image; signiert wird mit eigenen
Secure-Boot-Schlüsseln. Die Zustandspartition ist mit LUKS2 verschlüsselt und an TPM 2.0 gebunden;
ohne TPM ist nur das Profil „homelab“ mit Passphrase erlaubt. Ein Health-Gate prüft nach jedem Start,
ob der Knoten gesund ist – sonst fällt der Bootloader nach drei Versuchen auf den alten Slot zurück.
Ab Werk gibt es kein Login, kein SSH und keinen Paketmanager; eingehend gilt „alles verboten“.

- **Eigen:** Image-Definition, Partitionslayout, Härtungsprofil, Betriebsarten, Health-Gate.
- **Eingebunden:** Debian-Pakete, Linux-Kernel (dm-verity, dm-crypt/LUKS2, TPM 2.0), systemd
  (systemd-boot, systemd-repart, systemd-sysupdate), mkosi als Bauwerkzeug, AppArmor, nftables.
- **Nachweis:** Ende-zu-Ende-Boot-Tests in QEMU für beide Architekturen mit emuliertem TPM;
  automatische Härtungsprüfung im gestarteten Image. Ein Erstknoten läuft auf einem gebrauchten
  Business-Notebook. Raspberry Pi ist vorbereitet,
  aber noch nicht auf echter Hardware getestet.

Mehr: [OS-Image](doku/os-image.html).

### Netzboot-Dienst {#netzboot}

::: html
<p class="rm-tags"><span class="status-ok">Erreicht (Lab)</span><span class="kind mix">Eigen + Eingebunden</span></p>
:::

Der Boot-Dienst `cp-bootd` läuft als Rolle auf Cluster-Knoten und ergänzt den vorhandenen
DHCP-Server, statt ihn zu ersetzen (proxyDHCP). Er beherrscht PXE für BIOS und UEFI, UEFI HTTP Boot,
iPXE und – vorbereitet – den Netzboot des Raspberry Pi. Alle Artefakte werden über ein signiertes
Boot-Manifest geprüft. Mehrere Boot-Dienste können parallel laufen.

- **Eigen:** DHCP- und TFTP-Verarbeitung (eigene, schlanke Parser), Boot-Entscheidungen, Manifest.
- **Eingebunden:** iPXE als Netzwerk-Bootloader (signiert gebaut).
- **Nachweis:** Boot-Labor in QEMU mit zwei Boot-Diensten in einem nachgebildeten Heimnetz;
  Fuzz- und Eigenschaftstests der Parser. Der Netzboot auf echter Hardware ist der nächste Schritt.

Mehr: [Boot und Adoption](doku/boot-adoption.html).

### Erstknoten, Adoption und Installer {#adoption}

::: html
<p class="rm-tags"><span class="status-ok">Erreicht</span><span class="status-review">Feinschliff in Abnahme</span><span class="kind mix">Eigen + Eingebunden</span></p>
:::

Der erste Knoten startet vom USB-Stick; ein Einrichtungsassistent führt über Portal, API oder MCP
durch Region, Portal-Adresse und den ersten Administrator (Einladung plus Passkey). Neue Knoten
melden sich als „wartend“ und werden freigegeben – von Hand oder per Auto-Adopt-Regel. Rollen werden
deklarativ zugewiesen, ein Reconciler setzt sie um. Der Installer schreibt cpOS nach festen Regeln auf
die interne Platte: nie auf das Startmedium, fremde Daten nur nach ausdrücklicher Bestätigung,
TPM-Bindung und Neusignierung mit dem Schlüssel der eigenen Installation. Knoten lassen sich außer
Betrieb nehmen und ersetzen, auch über Zellgrenzen.

- **Eigen:** Assistent, Adoptionsablauf, Rollenmodell, Installer einschließlich UEFI-Booteinträgen.
- **Eingebunden:** systemd-repart (Partitionierung), LUKS2 (Verschlüsselung).
- **Nachweis:** QEMU-Installation vom Stick mit und ohne TPM; Container-Labs für Adoption und
  Rollen; auf echter Notebook-Hardware als Erstknoten in Betrieb. Nachbesserungen am Assistenten
  sind umgesetzt und in Abnahme.

### Steuerungsebene: Raft, Gossip, Zellen {#steuerungsebene}

::: html
<p class="rm-tags"><span class="status-ok">Erreicht</span><span class="kind lib">Eigen + Bibliothek</span></p>
:::

Auf jedem Knoten läuft `cp-agent`. Die Mitgliedschaft verbreitet sich per Gossip, der verbindliche
Zustand liegt in einer Raft-Gruppe je Zelle. Schon zwei Knoten plus ein **Zeuge** ohne Nutzdaten sind
ausfallfest; die Steuerungsgruppe wird automatisch gewählt. Zeugen schreiben signierte Prüfpunkte,
damit ein zurückgesetzter Knoten erkannt wird. Der Scheduler platziert nach Architektur (ARM/x86),
Ressourcen und Knotenpools.

- **Eigen:** Zellen- und Zeugenmodell, Wahl der Steuerungsgruppe, Zustandsmaschine, Scheduler,
  Knoten-Lebenszyklus.
- **Bibliotheken (tragend):** openraft (Raft-Konsens), foca (SWIM-Gossip), redb (lokaler Speicher).
- **Nachweis:** deterministische Simulation mit festen Zufallssaaten (je Szenario bis zu 1.000
  Saaten ohne Invariantenverletzung) und Container-Labs mit Mehrknoten-Clustern.

Mehr: [Steuerungsebene](doku/steuerungsebene.html).

### Knoten-Identität und Kryptografie {#knotensicherheit}

::: html
<p class="rm-tags"><span class="status-ok">Erreicht</span><span class="kind lib">Eigen + Bibliothek</span></p>
:::

Eine interne Zertifizierungsstelle stellt jedem Knoten eine Identität aus; Knoten sprechen nur per
gegenseitig authentisiertem TLS miteinander. Die Algorithmen folgen wählbaren Kryptoprofilen, die sich
an BSI TR-02102 orientieren. Privilegierte Aufgaben erledigt ein enger Root-Helfer `cp-privd` mit fest
definierten Befehlen; der Agent selbst läuft ohne Root-Rechte.

- **Eigen:** PKI-Abläufe, Kryptoprofile, Root-Helfer, zentrale Krypto-Schnittstelle.
- **Bibliotheken (tragend):** rustls (TLS), aws-lc-rs (Kryptografie), rcgen (Zertifikate).
- **Nachweis:** Unit- und Fuzz-Tests, Container-Labs mit mTLS zwischen allen Knoten.

Mehr: [Sicherheitsmodell](doku/sicherheitsmodell.html), [Kryptografie](doku/kryptografie.html).

### Identität und Mandanten {#identitaet}

::: html
<p class="rm-tags"><span class="status-ok">Identitätsdienst erreicht</span><span class="status-plan">Mandanten geplant</span><span class="kind lib">Eigen + Bibliothek</span></p>
:::

Ein **eigener OIDC-/OAuth-2.1-Autorisierungsserver** läuft als Rolle `identity`. Anmeldung
ausschließlich per Passkey (WebAuthn); dazu Authorization Code mit PKCE, Device Flow für die
Kommandozeile, Token-Widerruf, DPoP und Rate-Limits. Die Signaturschlüssel liegen nur im separaten
Prozess `cp-identityd`. API, Portal, `cpctl` und MCP nutzen dieselben Tokens.

- **Eigen:** Autorisierungsserver, Passkey-Prüfung, Token- und Sitzungsverwaltung.
- **Bibliotheken:** aws-lc-rs (Signaturen) über die zentrale Krypto-Schnittstelle.
- **Nachweis:** Container-Labs mit Ende-zu-Ende-Anmeldeflüssen; Browser-Tests mit virtuellem
  Passkey gegen einen echten Agenten.
- **Noch offen:** Mandanten, Projekte, Gruppen, Rechtemodell und Kontingente – siehe
  [Bis zum MVP](#mvp).

Mehr: [Identität und Rechte](doku/identitaet.html).

### API, Portal, MCP und CLI mit Parität {#zugaenge}

::: html
<p class="rm-tags"><span class="status-ok">Erreicht</span><span class="kind lib">Eigen + Bibliothek</span></p>
:::

Jeder Agent bedient die Ressourcen-API (REST, OpenAPI) und leitet Anfragen an den zuständigen Knoten
weiter. Aus demselben Schema entstehen die Kommandozeile `cpctl` und der MCP-Server für KI-Agenten.
Das Web-Portal wird vom Knoten selbst ausgeliefert, zeigt Änderungen live und ist über mehrere Knoten
erreichbar. Eine Paritätsprüfung in der CI stellt sicher, dass jede ändernde Operation in allen Zugängen
verfügbar ist.

- **Eigen:** Ressourcenmodell, API, Weiterleitung, `cpctl`, MCP-Werkzeuge, Portal, Paritätsprüfung.
- **Bibliotheken (tragend):** axum/hyper (HTTP), rmcp (MCP-Protokoll), Svelte und Vite (Portal).
- **Nachweis:** Container-Labs, Browser-Tests des Portals, Paritätsprüfung in jedem CI-Lauf.

Mehr: [API-first](doku/api-first.html), [Portal](doku/portal.html).

### Updates und Releases {#updates}

::: html
<p class="rm-tags"><span class="status-review">In Abnahme</span><span class="kind mix">Eigen + Eingebunden</span></p>
:::

Ein Release ist ein signiertes Bündel aus OS-Image, Diensten und SBOM. Die Signaturkette folgt dem
TUF-Muster (mehrere Rollen, Root-Rotation, Schutz vor Rollback). Releases werden **importiert**,
nicht online abgerufen, und von mindestens zwei Knoten zur Verteilung gehalten. Knoten schreiben das
neue Release in den freien A/B-Slot und starten neu; das Health-Gate bestätigt oder es folgt der
automatische Rückfall. Ein Update-Controller rollt Knoten für Knoten aus, schützt das Raft-Quorum,
aktualisiert den Leader zuletzt und pausiert bei Fehlern. Vorab zeigt eine Planvorschau Reihenfolge und
Auswirkungen.

- **Eigen:** Release-Format, Prüfung der Signaturkette nach TUF-Spezifikation, Import und Verteilung,
  Update-Controller.
- **Eingebunden:** systemd-sysupdate (Schreiben in den A/B-Slot), systemd-boot (Bootzähler, Rückfall).
- **Nachweis:** QEMU-Labs für Import, Knoten-Update und Ausrollen. Die Ende-zu-Ende-Abnahme mit
  Rollout und Rollback sowie ein echtes Update auf Hardware stehen als Nächstes an.

Mehr: [Release-Bündel](doku/release-buendel.html), [Rollout](doku/rollout.html).

### Plattform-DNS {#plattform-dns}

::: html
<p class="rm-tags"><span class="status-review">In Abnahme</span><span class="kind lib">Eigen + Bibliothek</span></p>
:::

Der Cluster verwaltet seine eigene DNS-Zone: `cp-dnsd` beantwortet sie autoritativ aus dem
Raft-Zustand, auf Wunsch mit DNSSEC. Zwei feste virtuelle IP-Adressen werden per Raft-Lease vergeben
(VRRP-artig, Eigenentwicklung). Der vorhandene DNS-Server im Netz braucht nur eine Weiterleitung oder
Delegation auf diese Adressen.

- **Eigen:** DNS-Server-Logik, Zonenaufbau, DNSSEC-Signatur, Vergabe der virtuellen Adressen.
- **Bibliothek:** hickory-proto – nur für das DNS-Wire-Format.
- **Nachweis:** Container-Lab mit Mehrknoten-Cluster. Der Wechsel der virtuellen Adressen wird beim
  Hardwaretest mit zwei Knoten gemessen.

Mehr: [Plattform-DNS](doku/dns.html).

### Netzwerk: WireGuard-Underlay {#netzwerk}

::: html
<p class="rm-tags"><span class="status-ok">Underlay erreicht</span><span class="status-plan">Mandanten-Overlay geplant</span><span class="kind mix">Eigen + Eingebunden</span></p>
:::

Jeder Knoten baut sein verschlüsseltes Underlay selbst auf, ohne Konfiguration durch den Betreiber:
Schlüssel je Knoten, signierte Ankündigungen über den Cluster-Zustand, Vollmesh je Standort, Relays
zwischen Standorten und für Knoten hinter NAT, Schlüsselrotation ohne Verbindungsabbruch. Zusätzlich
schützt ein Pre-Shared-Key aus einem hybriden Schlüsselaustausch (klassisch plus ML-KEM) gegen
spätere Entschlüsselung durch Quantenrechner.

- **Eigen:** Topologieplanung, Schlüsselverteilung und Rotation, Netlink-Ansteuerung über den Root-Helfer.
- **Eingebunden:** WireGuard im Linux-Kernel.
- **Nachweis:** Container-Labs mit Mehrknoten-Clustern und Simulation der Topologie.

Mehr: [Netzwerk](doku/netzwerk.html).

### Speicher {#speicher}

::: html
<p class="rm-tags"><span class="status-plan">Konzept entschieden, Umsetzung geplant</span><span class="kind mix">Eigen + Eingebunden</span></p>
:::

Das Speicherkonzept ist entschieden: ein **eigener Blockspeicher** `cp-blk` für 2 bis über 1.000
Knoten (zuerst lokal, repliziert erst nach einem Reife-Gate) und S3-kompatibler Objektspeicher mit
Garage hinter einem eigenen S3-Frontend. Umgesetzt ist bisher nur die verschlüsselte Zustandspartition
der Knoten.

Mehr: [Speicher](doku/speicher.html).

### Lieferkette und Compliance {#lieferkette}

::: html
<p class="rm-tags"><span class="status-ok">Erreicht</span><span class="kind ext">Eingebunden</span><span class="kind own">Eigene Regeln</span></p>
:::

Jeder CI-Lauf prüft Formatierung, Lints, Tests, Lizenzen und Quellen der Abhängigkeiten,
Sicherheitshinweise, REUSE-Konformität und die Paritäts- und Compliance-Regeln. Für Binärdateien und
OS-Image entstehen SBOMs (CycloneDX und SPDX) sowie VEX-Dokumente; Releases tragen Signaturen und
Herkunftsnachweise. Reproduzierbare Builds sind für x86_64 und aarch64 nachgewiesen. Ein
Schwachstellenprozess mit koordinierter Offenlegung ist eingerichtet. Die Anforderungen aus
BSI IT-Grundschutz und ISO-Normen sind auf Komponenten abgebildet – das ist Vorbereitung, keine
Zertifizierung.

- **Eingebunden:** cargo-deny, cargo-audit, REUSE-Werkzeug, cargo-cyclonedx, cosign, OpenSCAP.
- **Eigen:** Policy-as-Code-Regeln, Paritäts- und Compliance-Prüfung, SBOM-Erzeugung für das OS-Image.

Mehr: [Compliance by Design](doku/compliance-by-design.html),
[Schwachstellenmanagement](doku/schwachstellenmanagement.html).

### Test- und Lab-Infrastruktur {#testlabs}

::: html
<p class="rm-tags"><span class="status-ok">Erreicht</span><span class="kind mix">Eigen + Eingebunden</span></p>
:::

- **Deterministische Simulation** des Clusters mit festen Saaten; ein Lauf lässt sich exakt
  wiederholen und nennt den ersten abweichenden Schritt (eigen, auf der Bibliothek turmoil).
- **Container-Labs** mit Mehrknoten-Clustern; jedes Lab wird gegen eine Soll-Tabelle geprüft und
  ist Teil der Abnahme (eigen).
- **Ende-zu-Ende-Labs in QEMU** mit UEFI-Firmware und emuliertem TPM für Boot, Installation,
  Netzboot und Updates (eingebunden: QEMU, OVMF, swtpm).
- **Browser-Tests** des Portals mit virtuellem Passkey (eingebunden: Playwright).
- **Echte Hardware:** ein gebrauchtes Business-Notebook als Erstknoten. Weitere Notebooks und
  Raspberry Pi folgen.

## Nächste Schritte {#naechste-schritte}

Kurzfristig, bis zum Meilenstein **„Kabel rein → Knoten im Cluster“** (geplant: Q1 2027):

::: html
<ul class="rm-plan">
<li><strong>Update-Abnahme</strong><span class="status-plan">Als Nächstes</span><p>Rollout und Rollback in QEMU-Labs, danach ein echtes Update auf dem Notebook-Erstknoten.</p></li>
<li><strong>Installer über Netzboot</strong><span class="status-plan">Geplant</span><p>Der PXE-Pfad: Netzboot, Erkennung, Freigabe und Installation ohne USB-Stick.</p></li>
<li><strong>Zweiter Knoten per Netzboot</strong><span class="status-plan">Geplant</span><p>Ein zweites Notebook bootet per Kabel, wird adoptiert und installiert; dabei Messung des Wechsels der DNS-Adressen.</p></li>
<li><strong>Meilenstein „Kabel rein → Knoten im Cluster“</strong><span class="status-plan">Geplant · Q1 2027</span><p>Ein neuer Knoten wird allein per Netzwerkkabel aufgenommen und installiert – auf echter Hardware nachgewiesen.</p></li>
<li><strong>Entsperrung ohne TPM</strong><span class="status-plan">Geplant</span><p>Knoten ohne TPM entsperren ihre Zustandspartition über vertraute Cluster-Knoten im Netz statt per Passphrase.</p></li>
<li><strong>Restpunkte Fundament</strong><span class="status-plan">Geplant</span><p>Zertifikatssperrung im Handshake, vom Agenten erzeugte Firewall-Regeln, Messung der Root-Helfer im Image.</p></li>
</ul>
:::

## Bis zum MVP {#mvp}

Zielplanung: Q2 2027. Der MVP ist eine vollständige, kleine Cloud für das Homelab: Mandanten legen
Ressourcen selbst an – über Portal, API und MCP.

::: html
<ul class="rm-plan">
<li><strong>Mandanten und Rechte</strong><span class="kind lib">Eigen + Bibliothek</span><p>Mandanten, Projekte, Nutzer, Gruppen, API-Schlüssel, Kontingente, Audit-Log. Rechte als eigener Beziehungsspeicher plus Richtliniensprache.</p><p class="with"><b>Eingebunden:</b> Cedar (Richtlinien)</p></li>
<li><strong>Anmeldung in VMs und Containern</strong><span class="kind own">Eigen</span><p>Login mit der Plattform-Identität bis ins Gast-Betriebssystem, Rollen werden zu Rechten im Gast.</p></li>
<li><strong>Mandanten-Netze</strong><span class="kind mix">Eigen + Eingebunden</span><p>VPCs und Subnetze als Overlay im verschlüsselten Underlay, IPAM, DHCP, internes DNS, Security Groups, NAT, Floating IPs, Load Balancer.</p><p class="with"><b>Eingebunden:</b> Linux-Kernel (VRF, VXLAN, nftables)</p></li>
<li><strong>Virtuelle Maschinen</strong><span class="kind mix">Eigen + Eingebunden</span><p>Lebenszyklus, Images, cloud-init, Konsole im Portal – eigene Steuerung über einem bewährten Hypervisor.</p><p class="with"><b>Eingebunden:</b> Cloud Hypervisor</p></li>
<li><strong>Container Instances und Registry</strong><span class="kind mix">Eigen + Eingebunden</span><p>Einzelne Container mit MicroVM-Isolation, eine Registry je Mandant.</p><p class="with"><b>Eingebunden:</b> Container-Laufzeit und MicroVM (Kandidaten: containerd, youki, Kata Containers), zot</p></li>
<li><strong>Managed Kubernetes</strong><span class="kind mix">Eigen + Eingebunden</span><p>Kubernetes-Cluster je Mandant; Erzeugen, Upgraden und Knotenpools steuert BYOC selbst.</p><p class="with"><b>Eingebunden:</b> k3s</p></li>
<li><strong>Block-Volumes (lokal)</strong><span class="kind mix">Eigen + Eingebunden</span><p>Eigener Blockspeicher <code>cp-blk</code> mit Snapshots und Verschlüsselung je Mandant.</p><p class="with"><b>Eingebunden:</b> Linux-Kernel (dm-thin, dm-crypt)</p></li>
<li><strong>Objektspeicher (S3)</strong><span class="kind mix">Eigen + Eingebunden</span><p>Buckets je Mandant hinter einem eigenen S3-Frontend mit Rechteprüfung.</p><p class="with"><b>Eingebunden:</b> Garage</p></li>
<li><strong>Schlüsselverwaltung</strong><span class="kind own">Eigen</span><p>Schlüsselhierarchie je Mandant und Verschlüsselung ruhender Daten.</p></li>
<li><strong>Beobachtbarkeit</strong><span class="kind mix">Eigen + Eingebunden</span><p>Erfassung, Alarme und Dashboards im Portal sind eigen; gespeichert wird in bewährten Zeitreihen- und Log-Speichern.</p><p class="with"><b>Eingebunden:</b> VictoriaMetrics, Log-Speicher (in Prüfung)</p></li>
<li><strong>Betrieb</strong><span class="kind own">Eigen</span><p>Backup und Wiederherstellung der Steuerungsebene, Notfall- und Wiederanlaufkonzept, Nutzungserfassung, Update-Richtlinien und Wartungsfenster.</p></li>
<li><strong>Sicherheitsnachweise</strong><span class="kind mix">Eigen + Eingebunden</span><p>Kontrollmatrix und Nachweis-Export für Betreiber, externer Penetrationstest vor dem MVP.</p></li>
</ul>
:::

## Bis Release 1.0 {#release-1}

Zielplanung: Mitte 2027. Nach dem MVP folgen die erweiterten Dienste, KI-Inferenz und der Betrieb
über mehrere Standorte.

::: html
<ul class="rm-plan">
<li><strong>Replizierter Blockspeicher</strong><span class="kind own">Eigen</span><p><code>cp-blk</code> repliziert über Knoten – erst nach einem Reife-Gate mit Simulation, Fehlerinjektion, Langlauf und externem Review.</p></li>
<li><strong>Dateispeicher (NFS)</strong><span class="kind mix">Eigen + Eingebunden</span><p>Freigaben je Mandant auf replizierten Volumes; Verwaltung und Mandantentrennung eigen.</p><p class="with"><b>Eingebunden:</b> NFS-Ganesha</p></li>
<li><strong>KI-Inferenz</strong><span class="kind mix">Eigen + Eingebunden</span><p>Beschleuniger erkennen und zuteilen, Modell-Registry, OpenAI-kompatible Inference-Endpunkte, verteilte Inferenz, eigenes AI-Gateway.</p><p class="with"><b>Eingebunden:</b> llama.cpp, vLLM (Inferenz-Engines)</p></li>
<li><strong>Datenbanken und Messaging</strong><span class="kind mix">Eigen + Eingebunden</span><p>Verwaltete Datenbanken und Warteschlangen; Lebenszyklus, Backup und Rechte eigen.</p><p class="with"><b>Eingebunden:</b> PostgreSQL, MariaDB, Valkey, NATS</p></li>
<li><strong>Secrets und Zertifikate</strong><span class="kind own">Eigen</span><p>Secrets-Dienst, private CA und Zertifikatsdienst für Mandanten – auf dem vorhandenen Raft-Zustand statt eines zweiten Konsenssystems.</p></li>
<li><strong>DNS als Dienst</strong><span class="kind lib">Eigen + Bibliothek</span><p>Öffentliche und private Zonen für Mandanten, aufbauend auf dem Plattform-DNS.</p><p class="with"><b>Bibliothek:</b> hickory-proto</p></li>
<li><strong>Serverless Functions</strong><span class="kind lib">Eigen + Bibliothek</span><p>Funktionen als WebAssembly mit Ereignis-Triggern und Scale-to-zero.</p><p class="with"><b>Bibliothek:</b> wasmtime</p></li>
<li><strong>L7-Load-Balancer</strong><span class="kind lib">Eigen + Bibliothek</span><p>HTTP-Routing mit TLS-Terminierung und automatischen ACME-Zertifikaten.</p><p class="with"><b>Bibliothek:</b> Pingora</p></li>
<li><strong>Infrastructure as Code und SDKs</strong><span class="kind own">Eigen</span><p>OpenTofu-Provider und generierte SDKs aus dem API-Schema.</p></li>
<li><strong>Mehrere Regionen und Rechenzentrum</strong><span class="kind mix">Eigen + Eingebunden</span><p>Föderation, globale API, Skalierungstests mit über 1.000 Knoten, Hardwareverwaltung per Redfish/IPMI, BGP-Anbindung, Disaster Recovery.</p><p class="with"><b>Eingebunden:</b> Routing-Daemon für BGP (Auswahl offen)</p></li>
<li><strong>Mandanten-Dienste für Betrieb und Sicherheit</strong><span class="kind own">Eigen</span><p>Backup-Dienst, Observability für Mandanten, Richtlinien-Compliance, Zero-Trust-Zugang, Plattformstatus.</p></li>
<li><strong>Abrechnung und Ökosystem</strong><span class="kind own">Eigen</span><p>Abrechnung auf Basis der Nutzungserfassung, Self-Service-Registrierung, Vorlagen-Marketplace, Upgrade- und Support-Politik.</p></li>
</ul>
:::

**Danach (Release 1.x):** Autoscaling-Gruppen, Container-Serverless, VPN und Private Endpoints,
ein eigener Objektspeicher mit Versionierung und Object Lock, Erasure Coding und Archivklassen,
Hardware-Attestierung als Voraussetzung für dauerhafte Auto-Adopt-Regeln sowie ein Topologie-Modell
für Racks. Die API-Gruppen gehen nach dem MVP von `v1alpha1` über `v1beta1` zu `v1`.

## Qualitätstore {#qualitaetstore}

- **Phase-1-Gate:** Ausfallfestigkeit (zwei Knoten plus Zeuge, kein Single Point of Failure ab drei
  Knoten) wird in der **deterministischen Simulation** mit 10.000 Zufallssaaten ohne
  Invariantenverletzung und auf **echter Hardware** nachgewiesen. Die Simulation läuft bereits mit bis
  zu 1.000 Saaten je Szenario; der volle Lauf und der Hardwarenachweis stehen noch aus.
- **Vor jedem Phasen-Gate:** Tests auf realer Hardware (Raspberry Pi, Notebooks, Server).
- **Vor jedem Minor-Release:** Jepsen-artige Konsistenzprüfungen.
- **Vor Mandantendaten auf replizierten Volumes:** Reife-Gate mit Simulation, Fehlerinjektion,
  Langlauf, Wiederherstellungstest und externem Review.

## Erfolgskriterien für den MVP {#mvp-kriterien}

| # | Kriterium |
|---|---|
| E1 | Erster Knoten per USB-Stick; Einrichtung über Portal, API oder MCP – höchstens 15 Minuten bis zum Portal |
| E2 | Neuer Knoten per Kabel bis zum Zustand „wartend“ in höchstens 5 Minuten (Raspberry Pi 4/5, x86-Notebook, Server) |
| E3 | Zwei Knoten plus Zeuge überstehen den Ausfall eines Knotens |
| E4 | Gemischter Cluster aus ARM64 und x86_64 mit passender Platzierung |
| E5 | Zwei Mandanten vollständig getrennt (Netz, Compute, Speicher, Schlüssel); Penetrationstest ohne kritische Befunde |
| E6 | Ein Mandant legt VM, Container Instance, Kubernetes-Cluster, Volume und Bucket selbst an – über alle drei Zugänge |
| E7 | Paritätsprüfung zu 100 % erfüllt – Ziel: keine Ausnahmen bei ändernden Operationen |
| E8 | Kein Single Point of Failure ab drei Knoten: Boot, API, Portal und MCP überleben einen Knotenausfall |
| E9 | Nachweise exportierbar (Kontrollmatrix für BSI C5, ISO 27001, IT-Grundschutz) |

## Nicht-Ziele {#nicht-ziele}

BYOC baut **keinen eigenen Hypervisor**, **kein verteiltes Dateisystem von Null** und
setzt **nicht auf Kubernetes als Fundament** der Plattform. Bewährte, quelloffene Komponenten
werden hinter klaren Prozessgrenzen integriert. Mehr dazu in
[Vision, Begriffe und Abgrenzung](doku/vision.html).
