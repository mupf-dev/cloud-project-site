title: Start
summary: BYOC (Build Your Own Cloud) – quelloffene, dezentrale und mandantenfähige Cloud-Plattform in Rust. Vom 2-Knoten-Homelab bis zum Rechenzentrum mit tausenden Knoten.
hero: ja
---
::: html
<section class="hero" aria-labelledby="hero-titel">
  <div class="wrap hero-grid">
    <div>
      <p class="eyebrow">Open Source · Rust · AGPL-3.0 · Alpha</p>
      <h1 id="hero-titel">Deine Cloud.<br><span class="hl">Auf deiner Hardware.</span></h1>
      <p class="lead"><strong>BYOC (Build Your Own Cloud)</strong> macht aus Raspberry Pi, Notebook, Mini-PC oder Rack-Server eine Cloud mit den Grunddiensten eines Hyperscalers – VMs, Container, Kubernetes, Speicher, Netze, Identitäten und KI. Vom Homelab mit zwei Knoten bis zum Rechenzentrum mit tausenden, ohne zentralen Controller.</p>
      <div class="buttons">
        <a class="btn primary" href="funktionen.html">Was BYOC kann</a>
        <a class="btn" href="doku/index.html">Dokumentation lesen</a>
      </div>
      <ol class="flow" aria-label="Ablauf in Kurzform">
        <li><b>Kabel rein</b></li><li>Knoten erscheint</li><li>freigeben</li><li>Rolle zuweisen</li><li><b>fertig</b></li>
      </ol>
    </div>
    <div class="hero-art">
      <svg class="art" viewBox="0 0 520 400" role="img" aria-labelledby="art-t art-d">
        <title id="art-t">Geräte verbinden sich zu einer Cloud</title>
        <desc id="art-d">Ein Raspberry Pi, ein Notebook, ein Mini-PC und ein Rack-Server sind per Kabel mit einer gemeinsamen Cloud verbunden, die virtuelle Maschinen, Kubernetes, Objektspeicher, DNS und KI bereitstellt. Ein weiterer, neu entdeckter Knoten wartet mit Bestätigungscode auf seine Freigabe.</desc>
        <circle class="ring" cx="266" cy="108" r="120"/>
        <g class="float">
          <path class="cloud" d="M170 160 C138 160 130 118 162 108 C160 74 202 62 224 80 C238 44 302 44 314 82 C342 70 378 92 366 120 C394 126 390 160 360 160 Z"/>
          <text class="t-strong" x="266" y="112" text-anchor="middle">BYOC</text>
          <text x="266" y="132" text-anchor="middle">VM · K8s · S3 · DNS · KI</text>
        </g>
        <path class="wire" d="M75 300 C75 235 205 222 222 160"/>
        <path class="wire" d="M190 290 C190 232 238 212 246 160"/>
        <path class="wire" d="M310 305 C310 240 288 212 284 160"/>
        <path class="wire" d="M435 280 C435 222 334 212 322 160"/>
        <path class="wire" stroke-dasharray="4 5" d="M420 196 C398 190 378 176 362 152"/>
        <path class="pulse" d="M75 300 C75 235 205 222 222 160"/>
        <path class="pulse p2" d="M190 290 C190 232 238 212 246 160"/>
        <path class="pulse p3" d="M310 305 C310 240 288 212 284 160"/>
        <path class="pulse p4" d="M435 280 C435 222 334 212 322 160"/>
        <!-- Raspberry Pi -->
        <rect class="dev-2" x="30" y="300" width="92" height="58" rx="5"/>
        <rect class="dev" x="44" y="316" width="26" height="26" rx="2"/>
        <g class="acc"><circle cx="82" cy="308" r="1.6"/><circle cx="88" cy="308" r="1.6"/><circle cx="94" cy="308" r="1.6"/><circle cx="100" cy="308" r="1.6"/><circle cx="106" cy="308" r="1.6"/><circle cx="112" cy="308" r="1.6"/></g>
        <rect class="dev" x="84" y="324" width="28" height="20" rx="2"/>
        <circle class="led" cx="38" cy="350" r="2.6"/>
        <text x="76" y="378" text-anchor="middle">Raspberry Pi</text>
        <!-- Notebook -->
        <rect class="dev" x="150" y="290" width="80" height="54" rx="4"/>
        <rect class="dev-2" x="157" y="297" width="66" height="40" rx="2"/>
        <path class="acc-s" d="M164 324 l8-8 8 6 10-12 12 8"/>
        <path class="dev" d="M140 346 H240 L234 356 H146 Z"/>
        <circle class="led l2" cx="222" cy="351" r="2"/>
        <text x="190" y="378" text-anchor="middle">Notebook</text>
        <!-- Mini-PC -->
        <rect class="dev" x="272" y="305" width="76" height="46" rx="8"/>
        <rect class="dev-2" x="282" y="318" width="40" height="4" rx="2"/>
        <rect class="dev-2" x="282" y="328" width="28" height="4" rx="2"/>
        <circle class="led l3" cx="336" cy="320" r="3"/>
        <text x="310" y="378" text-anchor="middle">Mini-PC</text>
        <!-- Server -->
        <rect class="dev" x="380" y="280" width="110" height="22" rx="3"/>
        <rect class="dev" x="380" y="306" width="110" height="22" rx="3"/>
        <rect class="dev" x="380" y="332" width="110" height="22" rx="3"/>
        <g class="dev-2"><rect x="390" y="288" width="54" height="6" rx="1"/><rect x="390" y="314" width="54" height="6" rx="1"/><rect x="390" y="340" width="54" height="6" rx="1"/></g>
        <circle class="led" cx="476" cy="291" r="2.6"/><circle class="led l2" cx="476" cy="317" r="2.6"/><circle class="led l4" cx="476" cy="343" r="2.6"/>
        <text x="435" y="378" text-anchor="middle">Rack-Server</text>
        <!-- neuer Knoten -->
        <rect class="dev" x="420" y="176" width="88" height="42" rx="5" stroke-dasharray="4 3"/>
        <circle class="led-warn" cx="432" cy="188" r="3"/>
        <text x="440" y="192">neu</text>
        <text x="430" y="208" class="t-strong" style="font-family: var(--mono); font-size: 12px">482-913</text>
      </svg>
    </div>
  </div>
</section>

<div class="wrap stats-band">
  <ul class="stats" aria-label="Eckdaten">
    <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="6" rx="1"/><rect x="3" y="14" width="18" height="6" rx="1"/><path d="M7 7h.01M7 17h.01"/></svg></span><div><b>2 – 10.000+</b><span>Knoten je Installation, in Zellen und Regionen</span></div></li>
    <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M8 8l-4 4 4 4M16 8l4 4-4 4M14 5l-4 14"/></svg></span><div><b>3 Zugänge</b><span>API, Web-Portal und MCP – gleicher Funktionsumfang</span></div></li>
    <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="1"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/></svg></span><div><b>ARM64 + x86_64</b><span>gemischt ab dem ersten Tag</span></div></li>
    <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="12" cy="5" r="2"/><circle cx="5" cy="18" r="2"/><circle cx="19" cy="18" r="2"/><path d="M11 7l-5 9M13 7l5 9M7 18h10"/></svg></span><div><b>0 Controller</b><span>kein zentraler Steuerknoten – Raft je Zelle, Gossip</span></div></li>
  </ul>
</div>

<section class="section" aria-labelledby="prinzipien">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">Leitprinzipien</p>
      <h2 id="prinzipien">Hyperscaler-Komfort, ohne Hyperscaler.</h2>
      <p>Öffentliche Clouds liefern Maschinen, Speicher und Netze per Klick. Wer Daten, Kosten und Abhängigkeiten selbst in der Hand behalten will, baut sich diesen Komfort heute aus vielen Einzelprodukten zusammen. BYOC bündelt ihn in einer Plattform, die auf genau der Hardware läuft, die sie steuert.</p>
    </div>
    <ul class="features">
      <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="12" cy="5" r="2"/><circle cx="5" cy="18" r="2"/><circle cx="19" cy="18" r="2"/><path d="M11 7l-5 9M13 7l5 9M7 18h10"/></svg></span><h3>Dezentral</h3><p>Kein zentraler Controller. Zustand über Raft je Zelle, Mitgliedschaft über Gossip. Fällt die Steuerung aus, laufen Workloads weiter.</p></li>
      <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M8 8l-4 4 4 4M16 8l4 4-4 4M14 5l-4 14"/></svg></span><h3>API-first, drei Zugänge</h3><p>Jede Funktion auf jeder Ebene über API, Portal und MCP – auch Ersteinrichtung und Adoption. Die Gleichwertigkeit prüft die CI.</p></li>
      <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M9 2v5M15 2v5M6 7h12v4a6 6 0 0 1-12 0zM12 17v5"/></svg></span><h3>Zero-Touch nach dem Kabel</h3><p>Kein Bildschirm, keine Tastatur, kein SSH. Einzige bewusste Handlung ist die Freigabe (Adoption) eines neuen Knotens.</p></li>
      <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M4 20V14M9.3 20V10M14.6 20V7M20 20V3"/></svg></span><h3>Skaliert in beide Richtungen</h3><p>Zwei Knoten sind ein vollwertiger Betriebsmodus. Wachstum auf tausende Knoten über Zellen und Regionen – ohne Neuinstallation.</p></li>
      <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><rect x="5" y="11" width="14" height="10" rx="1"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg></span><h3>Unveränderliche Knoten</h3><p>Eigenes Image-OS cpOS mit dm-verity, A/B-Updates, Secure Boot und TPM-gebundener Verschlüsselung.</p></li>
      <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/></svg></span><h3>Secure &amp; Compliant by Design</h3><p>mTLS überall, Mandantentrennung auf allen Schichten, lückenloses Audit, Nachweise für ISO 27001 und BSI IT-Grundschutz.</p></li>
      <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="6" cy="6" r="2"/><circle cx="6" cy="18" r="2"/><circle cx="18" cy="8" r="2"/><path d="M6 8v8M18 10c0 4-6 3-10 6"/></svg></span><h3>Open Source durchgehend</h3><p>Nur quelloffene Abhängigkeiten, eigene Komponenten in Rust, signierte Releases mit SBOM.</p></li>
      <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><rect x="3" y="3" width="8" height="8" rx="1"/><rect x="13" y="13" width="8" height="8" rx="1"/><path d="M11 7h4a2 2 0 0 1 2 2v4M13 17H9a2 2 0 0 1-2-2v-4"/></svg></span><h3>Bewährtes integrieren</h3><p>Kein eigener Hypervisor, kein Dateisystem von Null: BYOC baut Steuerung, Automatisierung und die einheitliche Oberfläche.</p></li>
    </ul>
  </div>
</section>

<section class="section alt" aria-labelledby="ablauf">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">So funktioniert's</p>
      <h2 id="ablauf">Vom Kabel zum Dienst in vier Schritten.</h2>
      <p>Neue Hardware bekommt nie automatisch Zugriff auf Daten. Erst die Freigabe vergibt eine Identität – danach läuft alles von selbst.</p>
    </div>
    <ol class="steps">
      <li>
        <svg class="step-art sa" viewBox="0 0 200 110" aria-hidden="true" focusable="false"><rect class="bg" width="200" height="110"/><rect class="dev" x="22" y="34" width="70" height="44" rx="5"/><rect class="soft" x="78" y="50" width="10" height="12" rx="1"/><path class="acc-s" d="M88 56 H120 C140 56 140 40 160 40 H178"/><rect class="dev" x="116" y="49" width="16" height="14" rx="2"/><circle class="acc" cx="34" cy="68" r="3"/><text x="57" y="98" text-anchor="middle">Netzboot</text><text x="150" y="98" text-anchor="middle">oder USB</text><path class="ln" d="M150 66 v14"/><rect class="soft" x="140" y="58" width="20" height="9" rx="2"/></svg>
        <h3>Kabel rein</h3>
        <p>Der Knoten startet per Netzwerk (PXE/HTTP, Raspberry-Pi-Netzboot) oder vom USB-Stick in ein Discovery-System im Arbeitsspeicher.</p>
      </li>
      <li>
        <svg class="step-art sa" viewBox="0 0 200 110" aria-hidden="true" focusable="false"><rect class="bg" width="200" height="110"/><rect class="dev" x="18" y="16" width="164" height="78" rx="5"/><text class="tx" x="30" y="36">d-7f3a91</text><text x="30" y="52">arm64 · 4 CPU · 8 GiB</text><text x="30" y="66">1× 256 GB · T1</text><rect class="warn" x="30" y="74" width="58" height="14" rx="2"/><text x="59" y="84" text-anchor="middle" style="fill: var(--warn-fg); font-weight: 600">wartet</text><text class="tx" x="170" y="36" text-anchor="end">482-913</text></svg>
        <h3>Knoten wird erkannt</h3>
        <p>Er meldet seinen Hardware-Steckbrief, schreibt nichts auf Platten und wartet in der Quarantäne – mit Bestätigungscode.</p>
      </li>
      <li>
        <svg class="step-art sa" viewBox="0 0 200 110" aria-hidden="true" focusable="false"><rect class="bg" width="200" height="110"/><rect class="dev" x="18" y="22" width="80" height="66" rx="5"/><text class="tx" x="30" y="42">node-03</text><circle class="ok" cx="84" cy="38" r="8" style="fill: var(--ok-bg); stroke: var(--ok-fg)"/><path d="M80 38l3 3 5-6" fill="none" style="stroke: var(--ok-fg)" stroke-width="1.8"/><rect class="soft" x="112" y="22" width="72" height="18" rx="2"/><text class="tx" x="148" y="35" text-anchor="middle">control</text><rect class="soft" x="112" y="46" width="72" height="18" rx="2"/><text class="tx" x="148" y="59" text-anchor="middle">compute-vm</text><rect class="soft" x="112" y="70" width="72" height="18" rx="2"/><text class="tx" x="148" y="83" text-anchor="middle">storage</text><path class="ln" d="M98 55 H110"/><text x="30" y="60">freigegeben</text><text x="30" y="74">mTLS ✓</text></svg>
        <h3>Freigeben &amp; Rolle zuweisen</h3>
        <p>Freigabe per Portal, API oder MCP. Danach Rollen manuell, per Regel oder auf Vorschlag des Planers – etwa Steuerung, VMs oder Speicher.</p>
      </li>
      <li>
        <svg class="step-art sa" viewBox="0 0 200 110" aria-hidden="true" focusable="false"><rect class="bg" width="200" height="110"/><path class="soft" d="M54 92 C30 92 26 64 48 58 C46 34 76 26 90 40 C100 16 146 16 152 44 C176 40 186 66 170 76 C186 82 180 92 160 92 Z"/><rect class="dev" x="62" y="56" width="26" height="20" rx="2"/><text class="tx" x="75" y="70" text-anchor="middle">VM</text><rect class="dev" x="92" y="56" width="30" height="20" rx="2"/><text class="tx" x="107" y="70" text-anchor="middle">K8s</text><rect class="dev" x="126" y="56" width="24" height="20" rx="2"/><text class="tx" x="138" y="70" text-anchor="middle">S3</text><rect class="dev" x="88" y="36" width="34" height="16" rx="2"/><text class="tx" x="105" y="48" text-anchor="middle">KI</text></svg>
        <h3>Dienste nutzen</h3>
        <p>VMs, Container, Managed Kubernetes, Block- und Objektspeicher, virtuelle Netze, DNS und KI-Inferenz – für mehrere Mandanten.</p>
      </li>
    </ol>
  </div>
</section>

<section class="section" aria-labelledby="vergleich">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">Vergleich</p>
      <h2 id="vergleich">Wie AWS, Azure oder Google Cloud – nur bei dir.</h2>
      <p>Die Dienste orientieren sich an den bekannten öffentlichen Clouds. Der Unterschied liegt darin, wo sie laufen und wem sie gehören.</p>
    </div>
    <div class="compare">
      <div class="col">
        <h3>Öffentliche Cloud <span class="tag">Hyperscaler</span></h3>
        <ul>
          <li><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14"/></svg><span>läuft im Rechenzentrum und unter der Rechtsordnung des Anbieters</span></li>
          <li><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14"/></svg><span>Preise und Abrechnungsmodell bestimmt der Anbieter</span></li>
          <li><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14"/></svg><span>proprietäre Schnittstellen, Wechsel ist aufwendig</span></li>
          <li><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12l5 5 9-10"/></svg><span>großer Dienstkatalog per Klick und API</span></li>
        </ul>
      </div>
      <div class="col us">
        <h3>BYOC <span class="tag acc">bei dir</span></h3>
        <ul>
          <li><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12l5 5 9-10"/></svg><span>läuft auf eigener Hardware – vom Raspberry Pi bis zum Rack, gemischt ARM und x86</span></li>
          <li><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12l5 5 9-10"/></svg><span>Daten, Schlüssel und Audit-Log bleiben beim Betreiber</span></li>
          <li><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12l5 5 9-10"/></svg><span>Open Source (AGPL), offene Schnittstellen: OpenAPI, MCP, S3-kompatibel</span></li>
          <li><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12l5 5 9-10"/></svg><span>die Grunddienste per Portal, API und MCP – weitere folgen phasenweise</span></li>
        </ul>
      </div>
    </div>
    <div class="svc">
      <div class="table-wrap"><table>
        <caption class="sr-only">Dienste von BYOC und ihre Entsprechungen bei Hyperscalern</caption>
        <thead><tr><th scope="col">Dienst in BYOC</th><th scope="col">Entspricht etwa</th></tr></thead>
        <tbody>
          <tr><td>Virtuelle Maschinen</td><td>AWS EC2 · Azure VMs · Compute Engine</td></tr>
          <tr><td>Container Instances</td><td>Fargate · Azure Container Instances · Cloud Run</td></tr>
          <tr><td>Managed Kubernetes</td><td>EKS · AKS · GKE</td></tr>
          <tr><td>Block- und Objektspeicher</td><td>EBS · S3 / Managed Disks · Blob Storage / Persistent Disk · Cloud Storage</td></tr>
          <tr><td>VPCs, Load Balancer, DNS</td><td>VPC · Route 53 / VNet · Azure DNS / VPC · Cloud DNS</td></tr>
          <tr><td>Mandanten, Rollen, Schlüssel</td><td>IAM · KMS / Entra ID · Key Vault / Cloud IAM</td></tr>
          <tr><td>KI-Inferenz, AI-Gateway</td><td>Bedrock · Azure AI Foundry · Vertex AI</td></tr>
        </tbody>
      </table></div>
      <p class="note">Details und Phasen: <a href="funktionen.html">Funktionsumfang</a> · <a href="doku/funktionsanalyse.html">Hyperscaler-Funktionsanalyse</a>.</p>
    </div>
  </div>
</section>

<section class="section alt" aria-labelledby="sicherheit">
  <div class="wrap split">
    <div>
      <p class="eyebrow">Sicherheit &amp; Souveränität</p>
      <h2 id="sicherheit" class="h2-plain">Vertrauen, das in der Hardware beginnt.</h2>
      <p class="muted-lead">Jeder Knoten startet nur signierte Software, bindet seine Schlüssel an das TPM und spricht mit anderen ausschließlich über gegenseitig authentisiertes TLS. Jede Änderung landet im Audit-Log.</p>
      <ul class="checks">
        <li><strong>Secure Boot</strong> mit eigenen Schlüsseln der Installation, Measured Boot</li>
        <li><strong>TPM 2.0</strong>-gebundene Plattenverschlüsselung, Remote Attestation</li>
        <li><strong>Signierte Updates</strong>: Release-Bündel mit SBOM, A/B-Updates mit Rückfall</li>
        <li><strong>mTLS überall</strong>, kurzlebige Zertifikate, Kryptografie nach BSI TR-02102</li>
        <li><strong>Compliance by Design</strong>: Anforderungen aus ISO/IEC 27001 und BSI IT-Grundschutz, exportierbare Nachweise</li>
      </ul>
      <div class="badges" aria-label="Berücksichtigte Regelwerke">
        <span class="tag acc">ISO/IEC 27001</span><span class="tag acc">BSI IT-Grundschutz</span><span class="tag">BSI C5</span><span class="tag">NIS2</span><span class="tag">CRA</span><span class="tag">DSGVO</span>
      </div>
      <p class="note">BYOC liefert Bausteine und Nachweise für die Zertifizierung des Betreibers – die Plattform selbst ist nicht zertifiziert. Mehr: <a href="doku/sicherheitsmodell.html">Sicherheitsmodell</a>.</p>
    </div>
    <figure class="art-card">
      <svg class="g" viewBox="0 0 440 360" role="img" aria-labelledby="vk-t vk-d">
        <title id="vk-t">Vertrauenskette eines Knotens</title>
        <desc id="vk-d">Von unten nach oben: Hardware mit TPM 2.0, Secure und Measured Boot, unveränderliches cpOS mit dm-verity und A/B-Partitionen, Knotenidentität mit kurzlebigem Zertifikat und mTLS, darüber Dienste und Mandanten mit lückenlosem Audit.</desc>
        <defs><marker id="vk-ah" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path class="ah-acc" d="M0,0 L10,5 L0,10 z"/></marker></defs>
        <rect class="soft" x="40" y="16" width="360" height="50" rx="5"/><text class="b" x="60" y="38">Dienste &amp; Mandanten</text><text class="s" x="60" y="55">Audit signiert und hash-verkettet</text>
        <rect class="box" x="40" y="86" width="360" height="50" rx="5"/><text class="b" x="60" y="108">Knotenidentität</text><text class="s" x="60" y="125">kurzlebiges Zertifikat · mTLS · T0–T4</text>
        <rect class="box" x="40" y="156" width="360" height="50" rx="5"/><text class="b" x="60" y="178">cpOS – unveränderlich</text><text class="s" x="60" y="195">dm-verity · A/B · signierte Updates</text>
        <rect class="box" x="40" y="226" width="360" height="50" rx="5"/><text class="b" x="60" y="248">Secure Boot · Measured Boot</text><text class="s" x="60" y="265">eigene Schlüssel der Installation</text>
        <rect class="solid" x="40" y="296" width="360" height="48" rx="5"/><text class="on" x="60" y="325">Hardware + TPM 2.0</text>
        <g><circle class="t4" cx="372" cy="41" r="7"/><circle class="t3" cx="372" cy="111" r="7"/><circle class="t2" cx="372" cy="181" r="7"/><circle class="t1" cx="372" cy="251" r="7"/></g>
        <path class="acc-ln" d="M20 330 V30" marker-end="url(#vk-ah)"/>
        <text class="s" x="14" y="190" transform="rotate(-90 14 190)" text-anchor="middle">Vertrauenskette</text>
      </svg>
      <figcaption>Jede Schicht prüft die nächste – von der Hardware bis zum Dienst.</figcaption>
    </figure>
  </div>
</section>

<section class="section" aria-labelledby="paritaet">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">Ein API, drei Zugänge</p>
      <h2 id="paritaet">Klicken, skripten oder fragen – mit identischem Ergebnis.</h2>
      <p>Portal und MCP-Werkzeuge werden aus demselben API-Schema abgeleitet. Eine CI-Prüfung verhindert, dass ein Zugang etwas kann, das den anderen fehlt – auf jeder Ebene, von der Plattform bis zur einzelnen Ressource.</p>
    </div>
    <div class="split rev">
      <figure class="art-card real">
        <picture>
          <source media="(prefers-color-scheme: dark)" srcset="assets/img/portal/overview-de-dark.webp" width="1600" height="1000">
          <img src="assets/img/portal/overview-de-light.webp" width="1600" height="1000" loading="lazy" decoding="async" alt="Übersicht des Web-Portals für die Region eu-demo-1: 4 von 4 Knoten aktiv, 2 Geräte warten auf Adoption, Zellen c1 und c2, Liste der Operationen.">
        </picture>
        <figcaption>Echtes Portal, fiktive Demodaten · Alpha – Oberfläche kann sich ändern. <a href="portal.html">Weitere Ansichten</a></figcaption>
      </figure>
      <div>
        <svg class="g" viewBox="0 0 420 200" role="img" aria-labelledby="pa-t pa-d">
          <title id="pa-t">Drei Zugänge, ein API</title>
          <desc id="pa-d">Web-Portal, REST-API mit cpctl und MCP für KI-Assistenten führen alle in dieselbe Ressourcen-API mit OpenAPI-Schema, die die Steuerungsebene anspricht.</desc>
          <defs><marker id="pa-ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path class="ah-acc" d="M0,0 L10,5 L0,10 z"/></marker></defs>
          <rect class="box" x="4" y="10" width="124" height="40" rx="5"/><text class="b" x="66" y="35" text-anchor="middle">Web-Portal</text>
          <rect class="box" x="148" y="10" width="124" height="40" rx="5"/><text class="b" x="210" y="35" text-anchor="middle">REST · cpctl</text>
          <rect class="box" x="292" y="10" width="124" height="40" rx="5"/><text class="b" x="354" y="35" text-anchor="middle">MCP · KI</text>
          <path class="flow-ln" d="M66 50 V72 H210 V96" marker-end="url(#pa-ah)"/><path class="flow-ln" d="M210 50 V96"/><path class="flow-ln" d="M354 50 V72 H210"/>
          <rect class="soft" x="64" y="100" width="292" height="40" rx="5"/><text class="b" x="210" y="119" text-anchor="middle">Ressourcen-API</text><text class="s" x="210" y="133" text-anchor="middle">ein OpenAPI-Schema · AuthZ · Audit</text>
          <path class="acc-ln" d="M210 140 V158" marker-end="url(#pa-ah)"/>
          <rect class="solid" x="64" y="160" width="292" height="34" rx="5"/><text class="on" x="210" y="182" text-anchor="middle">Steuerungsebene (Raft je Zelle)</text>
        </svg>
        <div class="console" role="group" aria-label="Beispiel auf der Kommandozeile">
          <div class="console-bar"><i></i><i></i><i></i><span>cpctl</span></div>
<pre><code><span class="p">$</span> cpctl list discoveries
NAME      ARCH   CPU  RAM    TRUST  CODE
d-7f3a91  arm64  4    8 GiB  T1     482-913
<span class="p">$</span> cpctl discovery adopt d-7f3a91 --node-name node-03 --wait
<span class="p">$</span> cpctl list nodes
NAME     ROLES               STATE
node-01  control,boot        Aktiv
node-02  control,compute-vm  Aktiv
node-03  -                   Bereitgestellt</code></pre>
        </div>
        <p class="note">Ausgabe beispielhaft, vereinfacht; Befehle und Felder können sich bis zum ersten Release ändern. Mehr: <a href="doku/api-first.html">API-first-Prinzip</a>.</p>
      </div>
    </div>
  </div>
</section>

<section class="section alt" aria-labelledby="zielgruppen">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">Für wen?</p>
      <h2 id="zielgruppen">Klein anfangen. Groß werden. Ohne Neuinstallation.</h2>
      <p>Der erste Schwerpunkt ist das Homelab – die Architektur enthält aber keine Entscheidung, die das Rechenzentrum verbaut.</p>
    </div>
    <ul class="tiers">
      <li>
        <svg class="tier-art sa" viewBox="0 0 200 80" aria-hidden="true" focusable="false"><rect class="bg" width="200" height="80" rx="4"/><rect class="dev" x="44" y="28" width="46" height="30" rx="3"/><rect class="dev" x="110" y="28" width="46" height="30" rx="3"/><rect class="soft" x="90" y="52" width="20" height="14" rx="2"/><circle class="acc" cx="52" cy="50" r="2.5"/><circle class="acc" cx="118" cy="50" r="2.5"/><text x="100" y="20" text-anchor="middle">2 Knoten + Zeuge</text></svg>
        <p class="n">2–10 Knoten</p><h3>Homelab</h3>
        <p>Raspberry Pi, alte Notebooks, Mini-PCs. Zwei-Knoten-Betrieb mit Zeuge; koexistiert mit dem DHCP des Routers.</p>
      </li>
      <li>
        <svg class="tier-art sa" viewBox="0 0 200 80" aria-hidden="true" focusable="false"><rect class="bg" width="200" height="80" rx="4"/><g><rect class="dev" x="22" y="22" width="34" height="22" rx="3"/><rect class="dev" x="62" y="22" width="34" height="22" rx="3"/><rect class="dev" x="102" y="22" width="34" height="22" rx="3"/><rect class="dev" x="142" y="22" width="34" height="22" rx="3"/><rect class="dev" x="42" y="50" width="34" height="22" rx="3"/><rect class="dev" x="82" y="50" width="34" height="22" rx="3"/><rect class="soft" x="122" y="50" width="34" height="22" rx="3"/></g></svg>
        <p class="n">10–100 Knoten</p><h3>Edge &amp; KMU</h3>
        <p>Mini-PCs und Server, mehrere Mandanten, erste Compliance-Anforderungen.</p>
      </li>
      <li>
        <svg class="tier-art sa" viewBox="0 0 200 80" aria-hidden="true" focusable="false"><rect class="bg" width="200" height="80" rx="4"/><g><rect class="dev" x="18" y="12" width="30" height="58" rx="2"/><rect class="dev" x="54" y="12" width="30" height="58" rx="2"/><rect class="soft" x="90" y="12" width="30" height="58" rx="2"/><rect class="dev" x="126" y="12" width="30" height="58" rx="2"/><rect class="dev" x="162" y="12" width="22" height="58" rx="2"/></g><path class="ln" d="M22 24h22M22 34h22M22 44h22M58 24h22M58 34h22M58 44h22M94 24h22M94 34h22M94 44h22M130 24h22M130 34h22M130 44h22"/></svg>
        <p class="n">100–10.000+ Knoten</p><h3>Rechenzentrum</h3>
        <p>Rack-Server mit BMC, Zellen und Regionen, mehrere Standorte, Zertifizierung des Betreibers.</p>
      </li>
    </ul>
  </div>
</section>

<section class="section cta" aria-labelledby="mitmachen-cta">
  <div class="wrap">
    <div>
      <p class="eyebrow">Mitmachen</p>
      <h2 id="mitmachen-cta">Gebaut wird offen. Bau mit.</h2>
      <p>Die Konzepte und Architekturentscheidungen sind öffentlich. Rückmeldungen zu Architektur, Sicherheit und Bedienbarkeit sind ausdrücklich willkommen – der Quellcode folgt, sobald Lizenzdateien, Sicherheitsrichtlinie und REUSE-Konformität vollständig sind.</p>
      <div class="buttons">
        <a class="btn primary" href="doku/index.html">Dokumentation lesen</a>
        <a class="btn" href="mitmachen.html">Mitmachen</a>
        <a class="btn" href="architektur.html">Architektur</a>
      </div>
    </div>
    <div class="status">
      <p><span class="tag">Projektstand · November 2026</span></p>
      <p>Die Architektur ist abgenommen (Meilenstein „Architektur steht“). Phase 1 „Fundament“ läuft: Agent, Steuerungsebene, OS-Image, Boot und Adoption, Release- und Update-Kette sowie Plattform-DNS.</p>
      <p>Noch nicht für den Produktiveinsatz bereit. <a href="roadmap.html">Status &amp; Roadmap</a></p>
    </div>
  </div>
</section>
:::
