title: Das Portal
summary: Echte Aufnahmen des Web-Portals von BYOC mit fiktiven Demodaten – Übersicht, Knoten, wartende Hardware, Zellen, DNS, Releases, Operationen und Einrichtungsassistent.
wide: ja
---
::: html
<p class="shot-intro">Das Web-Portal ist einer von drei gleichwertigen Zugängen zur Plattform – neben REST-API (mit <code>cpctl</code>) und MCP. Es wird von jedem Knoten selbst ausgeliefert, braucht keinen separaten Server und folgt hell/dunkel der Systemeinstellung, genau wie diese Seite. Die Aufnahmen stammen aus einem echten Mehrknoten-Lab: vier Knoten in Containern, Region <code>eu-demo-1</code>, Portal-Adresse <code>portal.byoc.example</code>. Alle Namen, Adressen und Geräte sind fiktiv.</p>
:::

> **Alpha – die Oberfläche kann sich ändern.** Die Aufnahmen zeigen den Entwicklungsstand vom November 2026. Bereiche mit dem Hinweis „bald“ (Mandanten, Projekte, VMs, Volumes, Netze) folgen in späteren Phasen.

## Übersicht {#uebersicht}

Der Zustand einer Region auf einen Blick: aktive Knoten, wartende Hardware, laufende Operationen und die Gesundheit der Zellen. Werte aktualisieren sich live über Watch-Ströme der API.

::: html
<figure class="shot">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/img/portal/overview-de-dark.webp" width="1600" height="1000">
    <img src="assets/img/portal/overview-de-light.webp" width="1600" height="1000" loading="lazy" decoding="async" alt="Portal-Übersicht der Region eu-demo-1: 4 von 4 Knoten aktiv, 2 Geräte warten auf Adoption, Zelle c1 gesund, Zelle c2 im Aufbau, Liste der letzten Operationen.">
  </picture>
  <figcaption>Übersicht der Region – echtes Portal, fiktive Demodaten.</figcaption>
</figure>
:::

## Wartende Hardware {#wartende-hardware}

Neu entdeckte Geräte warten in Quarantäne. Ihre Angaben sind Fremdinhalt („ext“) und werden nur als Text angezeigt; adoptiert wird erst nach Bestätigung der Geräteidentität per Code oder automatisch über eine Adoptionsregel.

::: html
<figure class="shot">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/img/portal/discoveries-de-dark.webp" width="1600" height="1000">
    <img src="assets/img/portal/discoveries-de-light.webp" width="1600" height="1000" loading="lazy" decoding="async" alt="Liste wartender Hardware mit zwei Geräten vom Modell EdgeBox E2, Architektur x86_64, Vertrauensstufe T1, Phase Wartend, mit Schaltflächen Prüfen und adoptieren sowie Ablehnen.">
  </picture>
  <figcaption>Wartende Hardware in Quarantäne, Herstellerangaben als „ext“ markiert.</figcaption>
</figure>
:::

## Knoten {#knoten}

Alle adoptierten Knoten der Region mit Modell, Zelle, Standort, Rollen, Vertrauensstufe und Phase – filter- und sortierbar.

::: html
<figure class="shot">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/img/portal/nodes-de-dark.webp" width="1600" height="1000">
    <img src="assets/img/portal/nodes-de-light.webp" width="1600" height="1000" loading="lazy" decoding="async" alt="Knotenliste mit n1 und node-01 bis node-03, alle in Zelle c1, Rolle dns, Vertrauensstufe T1 und Phase Aktiv.">
  </picture>
  <figcaption>Knotenliste – drei Knoten wurden per Adoptionsregel automatisch aufgenommen.</figcaption>
</figure>
:::

## Knotendetail {#knotendetail}

Identität, Betriebssystem-Stand (A/B-Updates), Standort im Rechenzentrum sowie Rollen und Mitgliedschaft in der Steuerungsgruppe. Neu installieren, Ersetzen und Stilllegen sind privilegierte Aktionen mit Bestätigung.

::: html
<figure class="shot">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/img/portal/node-de-dark.webp" width="1600" height="1000">
    <img src="assets/img/portal/node-de-light.webp" width="1600" height="1000" loading="lazy" decoding="async" alt="Detailansicht von node-01: Identität mit URN, Zelle c1, Rolle dns, OS-Version 0.9.0, Betriebssystem läuft, Standort nicht angegeben, Rollen control, identity und dns, Voter der Steuerungsgruppe.">
  </picture>
  <figcaption>Knotendetail mit Betriebssystem-Stand und Steuerungsgruppe.</figcaption>
</figure>
:::

## Zellen und Steuerungsgruppe {#zellen}

Eine Zelle bündelt Knoten mit eigener Raft-Steuerungsgruppe. Die Ansicht zeigt Voter, Leader und Term und prüft, ob die Voter so über Ausfallzonen verteilt sind, dass der Ausfall eines Racks die Steuerung nicht lahmlegt.

::: html
<figure class="shot">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/img/portal/cell-de-dark.webp" width="1600" height="1000">
    <img src="assets/img/portal/cell-de-light.webp" width="1600" height="1000" loading="lazy" decoding="async" alt="Detailansicht der Zelle c1 (Rack A): 4 Knoten, 3 Voter, Leader n1, Term 2, Hinweis Gut verteilt, Liste der Knoten der Zelle.">
  </picture>
  <figcaption>Zelle c1 mit Steuerungsgruppe und Prüfung der Ausfallzonen.</figcaption>
</figure>
:::

## Plattform-DNS {#dns}

Zonen der Region, beantwortet von <code>cp-dnsd</code> auf den Knoten mit Rolle dns, mit festen VIPs, DNSSEC und automatisch erzeugten Plattform-Einträgen für Portal und Knoten.

::: html
<figure class="shot">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/img/portal/dns-de-dark.webp" width="1600" height="1000">
    <img src="assets/img/portal/dns-de-light.webp" width="1600" height="1000" loading="lazy" decoding="async" alt="DNS-Ansicht der Region: zwei feste VIPs aus dem Dokumentationsnetz mit ihren Trägerknoten, darunter die Zone byoc.example mit 5 eigenen und 20 Plattform-Einträgen, DNSSEC an, ausgeliefert von allen vier Knoten.">
  </picture>
  <figcaption>Plattform-DNS: Zone byoc.example mit DNSSEC.</figcaption>
</figure>
:::

## Plattform-Releases {#releases}

Signierte Release-Bündel werden geprüft (Signaturkette, Sicherheitsepoche, Mindestversion) und inhaltsadressiert auf mehreren Haltern abgelegt; von dort beziehen die Knoten ihre Updates.

::: html
<figure class="shot">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/img/portal/releases-de-dark.webp" width="1600" height="1000">
    <img src="assets/img/portal/releases-de-light.webp" width="1600" height="1000" loading="lazy" decoding="async" alt="Liste der Plattform-Releases 1.0.0 und 0.9.0 im Kanal stable, Phase Verfügbar, mit Haltern, darüber das Formular zum Import eines Release-Bündels.">
  </picture>
  <figcaption>Plattform-Releases – im Lab simulierte Releases ohne Artefakte (daher 0 B).</figcaption>
</figure>
:::

## Operationen {#operationen}

Jede Änderung ist eine nachvollziehbare Operation mit Kanal (API, Portal, MCP, System), Auslöser, Fortschritt und Ergebnis.

::: html
<figure class="shot">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/img/portal/operations-de-dark.webp" width="1600" height="1000">
    <img src="assets/img/portal/operations-de-light.webp" width="1600" height="1000" loading="lazy" decoding="async" alt="Liste der Operationen der Region mit Aktion, Ziel, Kanal, Auslöser, Fortschritt und Status Erfolgreich.">
  </picture>
  <figcaption>Operationen mit Kanal und Auslöser.</figcaption>
</figure>
:::

## Einrichtungsassistent {#einrichtung}

Die Ersteinrichtung läuft im Browser: Setup-Token und Bestätigungscode von der Konsole des ersten Knotens, Hardware- und Netzprüfung, dann Plattform, Region, Portal-Adresse und DNS festlegen. Vor der Ausführung zeigt der Assistent den vollständigen Plan.

::: html
<figure class="shot">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/img/portal/setup-de-dark.webp" width="1600" height="644">
    <img src="assets/img/portal/setup-de-light.webp" width="1600" height="644" loading="lazy" decoding="async" alt="Auszug aus dem Einrichtungsassistenten: Liste der Auswirkungen des Plans – Plattform demo mit Trust Domain byoc.example, Region eu-demo-1 mit Zelle c1, Zertifizierungsstellen, Wiederherstellungsanteile, erster Administrator, DNS-Zone byoc.example mit zwei VIPs.">
  </picture>
  <figcaption>Einrichtungsassistent, Auszug: Auswirkungen des Plans vor der Ausführung.</figcaption>
</figure>
:::

Mehr zu den Konzepten hinter den Ansichten: [Portal-Konzept](doku/portal.html), [Funktionsumfang](funktionen.html), [Architektur](architektur.html) und die [Dokumentation](doku/index.html).
