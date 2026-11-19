title: Home
summary: Das Cloud Projekt (DCP) – an open-source, decentralized, multi-tenant cloud platform written in Rust. From a two-node homelab to a data center with thousands of nodes.
hero: ja
de: index
---
::: html
<section class="hero" aria-labelledby="hero-title">
  <div class="wrap hero-grid">
    <div>
      <p class="eyebrow">Open Source · Rust · AGPL-3.0 · Alpha</p>
      <h1 id="hero-title">Your cloud.<br><span class="hl">On your hardware.</span></h1>
      <p class="lead"><strong>Das Cloud Projekt (DCP)</strong> turns Raspberry Pis, laptops, mini PCs and rack servers into a cloud with the core services of a hyperscaler – VMs, containers, Kubernetes, storage, networks, identity and AI. From a two-node homelab to a data center with thousands of nodes, with no central controller.</p>
      <div class="buttons">
        <a class="btn primary" href="features.html">See what DCP does</a>
        <a class="btn" href="docs/index.html">Read the docs</a>
      </div>
      <ol class="flow" aria-label="The flow in short">
        <li><b>Plug in</b></li><li>node appears</li><li>approve</li><li>assign a role</li><li><b>done</b></li>
      </ol>
    </div>
    <div class="hero-art">
      <svg class="art" viewBox="0 0 520 400" role="img" aria-labelledby="art-t art-d">
        <title id="art-t">Devices joining into one cloud</title>
        <desc id="art-d">A Raspberry Pi, a laptop, a mini PC and a rack server are cabled into one shared cloud that provides virtual machines, Kubernetes, object storage, DNS and AI. Another, newly discovered node waits for approval with a confirmation code.</desc>
        <circle class="ring" cx="266" cy="108" r="120"/>
        <g class="float">
          <path class="cloud" d="M170 160 C138 160 130 118 162 108 C160 74 202 62 224 80 C238 44 302 44 314 82 C342 70 378 92 366 120 C394 126 390 160 360 160 Z"/>
          <text class="t-strong" x="266" y="112" text-anchor="middle">Das Cloud Projekt</text>
          <text x="266" y="132" text-anchor="middle">VM · K8s · S3 · DNS · AI</text>
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
        <text x="190" y="378" text-anchor="middle">Laptop</text>
        <!-- Mini-PC -->
        <rect class="dev" x="272" y="305" width="76" height="46" rx="8"/>
        <rect class="dev-2" x="282" y="318" width="40" height="4" rx="2"/>
        <rect class="dev-2" x="282" y="328" width="28" height="4" rx="2"/>
        <circle class="led l3" cx="336" cy="320" r="3"/>
        <text x="310" y="378" text-anchor="middle">Mini PC</text>
        <!-- Server -->
        <rect class="dev" x="380" y="280" width="110" height="22" rx="3"/>
        <rect class="dev" x="380" y="306" width="110" height="22" rx="3"/>
        <rect class="dev" x="380" y="332" width="110" height="22" rx="3"/>
        <g class="dev-2"><rect x="390" y="288" width="54" height="6" rx="1"/><rect x="390" y="314" width="54" height="6" rx="1"/><rect x="390" y="340" width="54" height="6" rx="1"/></g>
        <circle class="led" cx="476" cy="291" r="2.6"/><circle class="led l2" cx="476" cy="317" r="2.6"/><circle class="led l4" cx="476" cy="343" r="2.6"/>
        <text x="435" y="378" text-anchor="middle">Rack server</text>
        <!-- new node -->
        <rect class="dev" x="420" y="176" width="88" height="42" rx="5" stroke-dasharray="4 3"/>
        <circle class="led-warn" cx="432" cy="188" r="3"/>
        <text x="440" y="192">new</text>
        <text x="430" y="208" class="t-strong" style="font-family: var(--mono); font-size: 12px">482-913</text>
      </svg>
    </div>
  </div>
</section>

<div class="wrap stats-band">
  <ul class="stats" aria-label="Key facts">
    <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="6" rx="1"/><rect x="3" y="14" width="18" height="6" rx="1"/><path d="M7 7h.01M7 17h.01"/></svg></span><div><b>2 – 10,000+</b><span>nodes per installation, in cells and regions</span></div></li>
    <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M8 8l-4 4 4 4M16 8l4 4-4 4M14 5l-4 14"/></svg></span><div><b>3 interfaces</b><span>API, web portal and MCP – same feature set</span></div></li>
    <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="1"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/></svg></span><div><b>ARM64 + x86_64</b><span>mixed from day one</span></div></li>
    <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="12" cy="5" r="2"/><circle cx="5" cy="18" r="2"/><circle cx="19" cy="18" r="2"/><path d="M11 7l-5 9M13 7l5 9M7 18h10"/></svg></span><div><b>0 controllers</b><span>no central control node – Raft per cell, gossip</span></div></li>
  </ul>
</div>

<section class="section" aria-labelledby="principles">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">Principles</p>
      <h2 id="principles">Hyperscaler comfort, without the hyperscaler.</h2>
      <p>Public clouds hand out machines, storage and networks at the click of a button. If you want to keep control of your data, costs and dependencies, today you have to assemble that comfort from many separate products. DCP bundles it into one platform that runs on the very hardware it manages.</p>
    </div>
    <ul class="features">
      <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="12" cy="5" r="2"/><circle cx="5" cy="18" r="2"/><circle cx="19" cy="18" r="2"/><path d="M11 7l-5 9M13 7l5 9M7 18h10"/></svg></span><h3>Decentralized</h3><p>No central controller. State via Raft per cell, membership via gossip. If the control plane fails, workloads keep running.</p></li>
      <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M8 8l-4 4 4 4M16 8l4 4-4 4M14 5l-4 14"/></svg></span><h3>API-first, three interfaces</h3><p>Every function at every level via API, portal and MCP – including initial setup and adoption. CI checks that they stay equivalent.</p></li>
      <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M9 2v5M15 2v5M6 7h12v4a6 6 0 0 1-12 0zM12 17v5"/></svg></span><h3>Zero-touch after the cable</h3><p>No screen, no keyboard, no SSH. The only deliberate step is approving (adopting) a new node.</p></li>
      <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M4 20V14M9.3 20V10M14.6 20V7M20 20V3"/></svg></span><h3>Scales both ways</h3><p>Two nodes are a fully supported mode of operation. Grow to thousands of nodes through cells and regions – without reinstalling.</p></li>
      <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><rect x="5" y="11" width="14" height="10" rx="1"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg></span><h3>Immutable nodes</h3><p>Purpose-built image OS cpOS with dm-verity, A/B updates, Secure Boot and TPM-bound encryption.</p></li>
      <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/></svg></span><h3>Secure &amp; Compliant by Design</h3><p>mTLS everywhere, tenant isolation at every layer, a complete audit trail, evidence for ISO 27001 and BSI IT-Grundschutz.</p></li>
      <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="6" cy="6" r="2"/><circle cx="6" cy="18" r="2"/><circle cx="18" cy="8" r="2"/><path d="M6 8v8M18 10c0 4-6 3-10 6"/></svg></span><h3>Open source throughout</h3><p>Open-source dependencies only, own components in Rust, signed releases with an SBOM.</p></li>
      <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><rect x="3" y="3" width="8" height="8" rx="1"/><rect x="13" y="13" width="8" height="8" rx="1"/><path d="M11 7h4a2 2 0 0 1 2 2v4M13 17H9a2 2 0 0 1-2-2v-4"/></svg></span><h3>Integrate what works</h3><p>No homegrown hypervisor, no file system from scratch: DCP builds the control, the automation and the unified interface.</p></li>
    </ul>
  </div>
</section>

<section class="section alt" aria-labelledby="how-it-works">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">How it works</p>
      <h2 id="how-it-works">From cable to cloud service in four steps.</h2>
      <p>New hardware never gets access to data automatically. Only approval grants it an identity – after that, everything runs on its own.</p>
    </div>
    <ol class="steps">
      <li>
        <svg class="step-art sa" viewBox="0 0 200 110" aria-hidden="true" focusable="false"><rect class="bg" width="200" height="110"/><rect class="dev" x="22" y="34" width="70" height="44" rx="5"/><rect class="soft" x="78" y="50" width="10" height="12" rx="1"/><path class="acc-s" d="M88 56 H120 C140 56 140 40 160 40 H178"/><rect class="dev" x="116" y="49" width="16" height="14" rx="2"/><circle class="acc" cx="34" cy="68" r="3"/><text x="57" y="98" text-anchor="middle">network boot</text><text x="150" y="98" text-anchor="middle">or USB</text><path class="ln" d="M150 66 v14"/><rect class="soft" x="140" y="58" width="20" height="9" rx="2"/></svg>
        <h3>Plug it in</h3>
        <p>The node boots over the network (PXE/HTTP, Raspberry Pi network boot) or from a USB stick into an in-memory discovery system.</p>
      </li>
      <li>
        <svg class="step-art sa" viewBox="0 0 200 110" aria-hidden="true" focusable="false"><rect class="bg" width="200" height="110"/><rect class="dev" x="18" y="16" width="164" height="78" rx="5"/><text class="tx" x="30" y="36">d-7f3a91</text><text x="30" y="52">arm64 · 4 CPU · 8 GiB</text><text x="30" y="66">1× 256 GB · T1</text><rect class="warn" x="30" y="74" width="58" height="14" rx="2"/><text x="59" y="84" text-anchor="middle" style="fill: var(--warn-fg); font-weight: 600">pending</text><text class="tx" x="170" y="36" text-anchor="end">482-913</text></svg>
        <h3>The node is discovered</h3>
        <p>It reports its hardware profile, writes nothing to disk and waits in quarantine – with a confirmation code.</p>
      </li>
      <li>
        <svg class="step-art sa" viewBox="0 0 200 110" aria-hidden="true" focusable="false"><rect class="bg" width="200" height="110"/><rect class="dev" x="18" y="22" width="80" height="66" rx="5"/><text class="tx" x="30" y="42">node-03</text><circle class="ok" cx="84" cy="38" r="8" style="fill: var(--ok-bg); stroke: var(--ok-fg)"/><path d="M80 38l3 3 5-6" fill="none" style="stroke: var(--ok-fg)" stroke-width="1.8"/><rect class="soft" x="112" y="22" width="72" height="18" rx="2"/><text class="tx" x="148" y="35" text-anchor="middle">control</text><rect class="soft" x="112" y="46" width="72" height="18" rx="2"/><text class="tx" x="148" y="59" text-anchor="middle">compute-vm</text><rect class="soft" x="112" y="70" width="72" height="18" rx="2"/><text class="tx" x="148" y="83" text-anchor="middle">storage</text><path class="ln" d="M98 55 H110"/><text x="30" y="60">adopted</text><text x="30" y="74">mTLS ✓</text></svg>
        <h3>Approve &amp; assign roles</h3>
        <p>Approve via portal, API or MCP. Then assign roles manually, by rule or as suggested by the scheduler – control plane, VMs or storage, for example.</p>
      </li>
      <li>
        <svg class="step-art sa" viewBox="0 0 200 110" aria-hidden="true" focusable="false"><rect class="bg" width="200" height="110"/><path class="soft" d="M54 92 C30 92 26 64 48 58 C46 34 76 26 90 40 C100 16 146 16 152 44 C176 40 186 66 170 76 C186 82 180 92 160 92 Z"/><rect class="dev" x="62" y="56" width="26" height="20" rx="2"/><text class="tx" x="75" y="70" text-anchor="middle">VM</text><rect class="dev" x="92" y="56" width="30" height="20" rx="2"/><text class="tx" x="107" y="70" text-anchor="middle">K8s</text><rect class="dev" x="126" y="56" width="24" height="20" rx="2"/><text class="tx" x="138" y="70" text-anchor="middle">S3</text><rect class="dev" x="88" y="36" width="34" height="16" rx="2"/><text class="tx" x="105" y="48" text-anchor="middle">AI</text></svg>
        <h3>Use the services</h3>
        <p>VMs, containers, managed Kubernetes, block and object storage, virtual networks, DNS and AI inference – for multiple tenants.</p>
      </li>
    </ol>
  </div>
</section>

<section class="section" aria-labelledby="comparison">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">Comparison</p>
      <h2 id="comparison">Like AWS, Azure or Google Cloud – but yours.</h2>
      <p>The services are modeled on the well-known public clouds. The difference is where they run and who owns them.</p>
    </div>
    <div class="compare">
      <div class="col">
        <h3>Public cloud <span class="tag">hyperscaler</span></h3>
        <ul>
          <li><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14"/></svg><span>runs in the provider's data center, under the provider's jurisdiction</span></li>
          <li><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14"/></svg><span>the provider sets prices and the billing model</span></li>
          <li><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14"/></svg><span>proprietary interfaces make switching costly</span></li>
          <li><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12l5 5 9-10"/></svg><span>a large service catalog via click and API</span></li>
        </ul>
      </div>
      <div class="col us">
        <h3>DCP <span class="tag acc">yours</span></h3>
        <ul>
          <li><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12l5 5 9-10"/></svg><span>runs on your own hardware – from Raspberry Pi to rack, ARM and x86 mixed</span></li>
          <li><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12l5 5 9-10"/></svg><span>data, keys and audit log stay with the operator</span></li>
          <li><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12l5 5 9-10"/></svg><span>open source (AGPL), open interfaces: OpenAPI, MCP, S3-compatible</span></li>
          <li><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12l5 5 9-10"/></svg><span>core services via portal, API and MCP – more follow phase by phase</span></li>
        </ul>
      </div>
    </div>
    <div class="svc">
      <div class="table-wrap"><table>
        <caption class="sr-only">DCP services and their hyperscaler counterparts</caption>
        <thead><tr><th scope="col">DCP service</th><th scope="col">Roughly equivalent to</th></tr></thead>
        <tbody>
          <tr><td>Virtual machines</td><td>AWS EC2 · Azure VMs · Compute Engine</td></tr>
          <tr><td>Container Instances</td><td>Fargate · Azure Container Instances · Cloud Run</td></tr>
          <tr><td>Managed Kubernetes</td><td>EKS · AKS · GKE</td></tr>
          <tr><td>Block and object storage</td><td>EBS · S3 / Managed Disks · Blob Storage / Persistent Disk · Cloud Storage</td></tr>
          <tr><td>VPCs, Load Balancer, DNS</td><td>VPC · Route 53 / VNet · Azure DNS / VPC · Cloud DNS</td></tr>
          <tr><td>Tenants, roles, keys</td><td>IAM · KMS / Entra ID · Key Vault / Cloud IAM</td></tr>
          <tr><td>AI inference, AI gateway</td><td>Bedrock · Azure AI Foundry · Vertex AI</td></tr>
        </tbody>
      </table></div>
      <p class="note">Details and phases: <a href="features.html">Features</a> · <a href="docs/hyperscaler-analysis.html">Hyperscaler feature analysis</a>.</p>
    </div>
  </div>
</section>

<section class="section alt" aria-labelledby="security">
  <div class="wrap split">
    <div>
      <p class="eyebrow">Security &amp; sovereignty</p>
      <h2 id="security" class="h2-plain">Trust that starts in the hardware.</h2>
      <p class="muted-lead">Every node boots only signed software, binds its keys to the TPM and talks to other nodes exclusively over mutually authenticated TLS. Every change lands in the audit log.</p>
      <ul class="checks">
        <li><strong>Secure Boot</strong> with the installation's own keys, measured boot</li>
        <li><strong>TPM 2.0</strong>-bound disk encryption, remote attestation</li>
        <li><strong>Signed updates</strong>: release bundles with an SBOM, A/B updates with automatic fallback</li>
        <li><strong>mTLS everywhere</strong>, short-lived certificates, cryptography per BSI TR-02102</li>
        <li><strong>Compliance by design</strong>: requirements from ISO/IEC 27001 and BSI IT-Grundschutz, exportable evidence</li>
      </ul>
      <div class="badges" aria-label="Frameworks covered">
        <span class="tag acc">ISO/IEC 27001</span><span class="tag acc">BSI IT-Grundschutz</span><span class="tag">BSI C5</span><span class="tag">NIS2</span><span class="tag">CRA</span><span class="tag">GDPR</span>
      </div>
      <p class="note">DCP provides building blocks and evidence for the operator's certification – the platform itself is not certified. More: <a href="docs/security-model.html">Security model</a>.</p>
    </div>
    <figure class="art-card">
      <svg class="g" viewBox="0 0 440 360" role="img" aria-labelledby="vk-t vk-d">
        <title id="vk-t">Chain of trust of a node</title>
        <desc id="vk-d">From bottom to top: hardware with TPM 2.0, secure and measured boot, immutable cpOS with dm-verity and A/B partitions, node identity with a short-lived certificate and mTLS, and on top services and tenants with a complete audit trail.</desc>
        <defs><marker id="vk-ah" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path class="ah-acc" d="M0,0 L10,5 L0,10 z"/></marker></defs>
        <rect class="soft" x="40" y="16" width="360" height="50" rx="5"/><text class="b" x="60" y="38">Services &amp; tenants</text><text class="s" x="60" y="55">audit signed and hash-chained</text>
        <rect class="box" x="40" y="86" width="360" height="50" rx="5"/><text class="b" x="60" y="108">Node identity</text><text class="s" x="60" y="125">short-lived certificate · mTLS · T0–T4</text>
        <rect class="box" x="40" y="156" width="360" height="50" rx="5"/><text class="b" x="60" y="178">cpOS – immutable</text><text class="s" x="60" y="195">dm-verity · A/B · signed updates</text>
        <rect class="box" x="40" y="226" width="360" height="50" rx="5"/><text class="b" x="60" y="248">Secure Boot · Measured Boot</text><text class="s" x="60" y="265">the installation's own keys</text>
        <rect class="solid" x="40" y="296" width="360" height="48" rx="5"/><text class="on" x="60" y="325">Hardware + TPM 2.0</text>
        <g><circle class="t4" cx="372" cy="41" r="7"/><circle class="t3" cx="372" cy="111" r="7"/><circle class="t2" cx="372" cy="181" r="7"/><circle class="t1" cx="372" cy="251" r="7"/></g>
        <path class="acc-ln" d="M20 330 V30" marker-end="url(#vk-ah)"/>
        <text class="s" x="14" y="190" transform="rotate(-90 14 190)" text-anchor="middle">chain of trust</text>
      </svg>
      <figcaption>Each layer verifies the next – from hardware to service.</figcaption>
    </figure>
  </div>
</section>

<section class="section" aria-labelledby="parity">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">One API, three interfaces</p>
      <h2 id="parity">Click it, script it or ask for it – same result.</h2>
      <p>The portal and the MCP tools are derived from the same API schema. A CI check prevents any interface from gaining a capability the others lack – at every level, from the platform down to a single resource.</p>
    </div>
    <div class="split rev">
      <figure class="art-card">
        <svg class="mock" viewBox="0 0 560 350" role="img" aria-labelledby="pm-t pm-d">
          <title id="pm-t">Stylized view of the web portal</title>
          <desc id="pm-d">Sketch of the portal with a dark sidebar and the node overview: three key figures, a notice about a new node with its confirmation code and a table of three nodes. All data is fictional.</desc>
          <rect class="frame" x="0.5" y="0.5" width="559" height="349" rx="6"/>
          <path class="chrome" d="M1 7 a6 6 0 0 1 6-6 H553 a6 6 0 0 1 6 6 V26 H1 Z"/>
          <circle class="dot-r" cx="14" cy="13.5" r="4"/><circle class="dot-y" cx="27" cy="13.5" r="4"/><circle class="dot-g" cx="40" cy="13.5" r="4"/>
          <text class="m mu" x="280" y="17" text-anchor="middle">portal.example.org</text>
          <rect class="side" x="1" y="26" width="120" height="323"/>
          <rect class="acc" x="12" y="38" width="18" height="18" rx="3"/><text class="side-t" x="38" y="51" style="font-weight: 650">DCP</text>
          <text class="side-mu m" x="14" y="80" style="font-size: 9px">PLATFORM</text>
          <text class="side-t" x="14" y="100">Overview</text>
          <rect class="side-act" x="8" y="108" width="106" height="20" rx="3"/><text class="side-act-t" x="14" y="122">Nodes</text>
          <text class="side-t" x="14" y="144">Discoveries</text><rect class="warn-bg" x="94" y="134" width="16" height="13" rx="6"/><text class="warn-t" x="102" y="144" text-anchor="middle" style="font-size: 9px">1</text>
          <text class="side-t" x="14" y="166">Cells</text>
          <text class="side-mu m" x="14" y="194" style="font-size: 9px">SERVICES</text>
          <text class="side-t" x="14" y="214">VMs</text><text class="side-t" x="14" y="236">Kubernetes</text><text class="side-t" x="14" y="258">Storage</text><text class="side-t" x="14" y="280">Networks</text>
          <text x="138" y="54" style="font-size: 15px; font-weight: 650">Nodes</text>
          <rect class="acc" x="470" y="40" width="74" height="22" rx="4"/><text class="on-acc" x="507" y="55" text-anchor="middle">+ Node</text>
          <rect class="card" x="138" y="72" width="128" height="50" rx="5"/><text class="mu" x="148" y="90">Nodes active</text><text class="m" x="148" y="112" style="font-size: 16px; font-weight: 650">2 / 3</text>
          <rect class="card" x="276" y="72" width="128" height="50" rx="5"/><text class="mu" x="286" y="90">Cells</text><text class="m" x="286" y="112" style="font-size: 16px; font-weight: 650">1</text>
          <rect class="card" x="414" y="72" width="130" height="50" rx="5"/><text class="mu" x="424" y="90">CPU usage</text><rect class="bar-track" x="424" y="104" width="106" height="7" rx="3"/><rect class="bar-fill" x="424" y="104" width="40" height="7" rx="3"/>
          <rect class="warn-bg" x="138" y="134" width="406" height="28" rx="4"/><text class="warn-t" x="150" y="152">1 new node awaiting approval · code 482-913</text><text class="warn-t" x="532" y="152" text-anchor="end">Review →</text>
          <rect class="card" x="138" y="174" width="406" height="160" rx="5"/>
          <rect class="row" x="139" y="175" width="404" height="24"/>
          <text class="mu m" x="150" y="191" style="font-size: 9.5px">NAME</text><text class="mu m" x="250" y="191" style="font-size: 9.5px">ROLES</text><text class="mu m" x="420" y="191" style="font-size: 9.5px">STATE</text>
          <text class="m" x="150" y="222">node-01</text><text x="250" y="222">control, boot</text><rect class="ok-bg" x="420" y="210" width="50" height="17" rx="3"/><text class="ok-t m" x="445" y="222" text-anchor="middle" style="font-size: 9.5px">ACTIVE</text>
          <line class="line" x1="139" y1="236" x2="543" y2="236"/>
          <text class="m" x="150" y="258">node-02</text><text x="250" y="258">control, compute-vm</text><rect class="ok-bg" x="420" y="246" width="50" height="17" rx="3"/><text class="ok-t m" x="445" y="258" text-anchor="middle" style="font-size: 9.5px">ACTIVE</text>
          <line class="line" x1="139" y1="272" x2="543" y2="272"/>
          <text class="m" x="150" y="294">node-03</text><text class="mu" x="250" y="294">–</text><rect class="warn-bg" x="420" y="282" width="104" height="17" rx="3"/><text class="warn-t m" x="472" y="294" text-anchor="middle" style="font-size: 9.5px">PROVISIONED</text>
        </svg>
        <figcaption>Stylized portal view with fictional data.</figcaption>
      </figure>
      <div>
        <svg class="g" viewBox="0 0 420 200" role="img" aria-labelledby="pa-t pa-d">
          <title id="pa-t">Three interfaces, one API</title>
          <desc id="pa-d">The web portal, the REST API with cpctl and MCP for AI assistants all lead into the same resource API with one OpenAPI schema, which talks to the control plane.</desc>
          <defs><marker id="pa-ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path class="ah-acc" d="M0,0 L10,5 L0,10 z"/></marker></defs>
          <rect class="box" x="4" y="10" width="124" height="40" rx="5"/><text class="b" x="66" y="35" text-anchor="middle">Web portal</text>
          <rect class="box" x="148" y="10" width="124" height="40" rx="5"/><text class="b" x="210" y="35" text-anchor="middle">REST · cpctl</text>
          <rect class="box" x="292" y="10" width="124" height="40" rx="5"/><text class="b" x="354" y="35" text-anchor="middle">MCP · AI</text>
          <path class="flow-ln" d="M66 50 V72 H210 V96" marker-end="url(#pa-ah)"/><path class="flow-ln" d="M210 50 V96"/><path class="flow-ln" d="M354 50 V72 H210"/>
          <rect class="soft" x="64" y="100" width="292" height="40" rx="5"/><text class="b" x="210" y="119" text-anchor="middle">Resource API</text><text class="s" x="210" y="133" text-anchor="middle">one OpenAPI schema · AuthZ · audit</text>
          <path class="acc-ln" d="M210 140 V158" marker-end="url(#pa-ah)"/>
          <rect class="solid" x="64" y="160" width="292" height="34" rx="5"/><text class="on" x="210" y="182" text-anchor="middle">Control plane (Raft per cell)</text>
        </svg>
        <div class="console" role="group" aria-label="Command-line example">
          <div class="console-bar"><i></i><i></i><i></i><span>cpctl</span></div>
<pre><code><span class="p">$</span> cpctl list discoveries
NAME      ARCH   CPU  RAM    TRUST  CODE
d-7f3a91  arm64  4    8 GiB  T1     482-913
<span class="p">$</span> cpctl discovery adopt d-7f3a91 --node-name node-03 --wait
<span class="p">$</span> cpctl list nodes
NAME     ROLES               STATE
node-01  control,boot        Active
node-02  control,compute-vm  Active
node-03  -                   Provisioned</code></pre>
        </div>
        <p class="note">Example output, simplified; commands and fields may change before the first release. More: <a href="docs/api-first.html">API-first principle</a>.</p>
      </div>
    </div>
  </div>
</section>

<section class="section alt" aria-labelledby="audiences">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">Who is it for?</p>
      <h2 id="audiences">Start small. Grow big. Never reinstall.</h2>
      <p>The first focus is the homelab – but the architecture contains no decision that rules out the data center.</p>
    </div>
    <ul class="tiers">
      <li>
        <svg class="tier-art sa" viewBox="0 0 200 80" aria-hidden="true" focusable="false"><rect class="bg" width="200" height="80" rx="4"/><rect class="dev" x="44" y="28" width="46" height="30" rx="3"/><rect class="dev" x="110" y="28" width="46" height="30" rx="3"/><rect class="soft" x="90" y="52" width="20" height="14" rx="2"/><circle class="acc" cx="52" cy="50" r="2.5"/><circle class="acc" cx="118" cy="50" r="2.5"/><text x="100" y="20" text-anchor="middle">2 nodes + witness</text></svg>
        <p class="n">2–10 nodes</p><h3>Homelab</h3>
        <p>Raspberry Pis, old laptops, mini PCs. Two-node operation with a witness; coexists with your router's DHCP.</p>
      </li>
      <li>
        <svg class="tier-art sa" viewBox="0 0 200 80" aria-hidden="true" focusable="false"><rect class="bg" width="200" height="80" rx="4"/><g><rect class="dev" x="22" y="22" width="34" height="22" rx="3"/><rect class="dev" x="62" y="22" width="34" height="22" rx="3"/><rect class="dev" x="102" y="22" width="34" height="22" rx="3"/><rect class="dev" x="142" y="22" width="34" height="22" rx="3"/><rect class="dev" x="42" y="50" width="34" height="22" rx="3"/><rect class="dev" x="82" y="50" width="34" height="22" rx="3"/><rect class="soft" x="122" y="50" width="34" height="22" rx="3"/></g></svg>
        <p class="n">10–100 nodes</p><h3>Edge &amp; SMB</h3>
        <p>Mini PCs and servers, multiple tenants, first compliance requirements.</p>
      </li>
      <li>
        <svg class="tier-art sa" viewBox="0 0 200 80" aria-hidden="true" focusable="false"><rect class="bg" width="200" height="80" rx="4"/><g><rect class="dev" x="18" y="12" width="30" height="58" rx="2"/><rect class="dev" x="54" y="12" width="30" height="58" rx="2"/><rect class="soft" x="90" y="12" width="30" height="58" rx="2"/><rect class="dev" x="126" y="12" width="30" height="58" rx="2"/><rect class="dev" x="162" y="12" width="22" height="58" rx="2"/></g><path class="ln" d="M22 24h22M22 34h22M22 44h22M58 24h22M58 34h22M58 44h22M94 24h22M94 34h22M94 44h22M130 24h22M130 34h22M130 44h22"/></svg>
        <p class="n">100–10,000+ nodes</p><h3>Data center</h3>
        <p>Rack servers with BMC, cells and regions, multiple sites, operator certification.</p>
      </li>
    </ul>
  </div>
</section>

<section class="section cta" aria-labelledby="contribute-cta">
  <div class="wrap">
    <div>
      <p class="eyebrow">Get involved</p>
      <h2 id="contribute-cta">Built in the open. Build with us.</h2>
      <p>The concepts and architecture decisions are public. Feedback on architecture, security and usability is very welcome – the source code follows as soon as license files, security policy and REUSE compliance are complete.</p>
      <div class="buttons">
        <a class="btn primary" href="docs/index.html">Read the docs</a>
        <a class="btn" href="contribute.html">Contribute</a>
        <a class="btn" href="architecture.html">Architecture</a>
      </div>
    </div>
    <div class="status">
      <p><span class="tag">Project status · November 2026</span></p>
      <p>The architecture has been signed off (milestone "Architecture in place"). Phase 1 "Foundation" is under way: agent, control plane, OS image, boot and adoption, release and update chain, and platform DNS.</p>
      <p>Not ready for production use yet. <a href="roadmap.html">Status &amp; roadmap</a></p>
    </div>
  </div>
</section>
:::
