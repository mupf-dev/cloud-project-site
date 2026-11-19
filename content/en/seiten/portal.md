title: The portal
summary: Real screenshots of the BYOC web portal with fictitious demo data – overview, nodes, waiting hardware, cells, DNS, releases, operations and the setup wizard.
wide: ja
de: portal
---
::: html
<p class="shot-intro">The web portal is one of three equivalent ways into the platform – alongside the REST API (with <code>cpctl</code>) and MCP. Every node serves it itself, no separate server is needed, and it follows the system's light/dark setting, just like this site. The screenshots come from a real multi-node lab: four nodes in containers, region <code>eu-demo-1</code>, portal address <code>portal.byoc.example</code>. All names, addresses and devices are fictitious.</p>
:::

> **Alpha – the interface may change.** The screenshots show the state of development as of November 2026. Areas marked “soon” (tenants, projects, VMs, volumes, networks) follow in later phases.

## Overview {#overview}

A region's state at a glance: active nodes, waiting hardware, running operations and the health of the cells. Values update live via the API's watch streams.

::: html
<figure class="shot">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../assets/img/portal/overview-en-dark.webp" width="1600" height="1000">
    <img src="../assets/img/portal/overview-en-light.webp" width="1600" height="1000" loading="lazy" decoding="async" alt="Portal overview of region eu-demo-1: 4 of 4 nodes active, 2 devices waiting for adoption, cell c1 healthy, cell c2 forming, list of recent operations.">
  </picture>
  <figcaption>Region overview – real portal, fictitious demo data.</figcaption>
</figure>
:::

## Waiting hardware {#waiting-hardware}

Newly discovered devices wait in quarantine. What they report is untrusted content (“ext”) and is shown as text only; adoption requires confirming the device identity with a code, or happens automatically via an adoption rule.

::: html
<figure class="shot">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../assets/img/portal/discoveries-en-dark.webp" width="1600" height="1000">
    <img src="../assets/img/portal/discoveries-en-light.webp" width="1600" height="1000" loading="lazy" decoding="async" alt="List of waiting hardware with two devices of model EdgeBox E2, architecture x86_64, trust level T1, phase waiting, with buttons to review and adopt or reject.">
  </picture>
  <figcaption>Waiting hardware in quarantine, vendor data marked as “ext”.</figcaption>
</figure>
:::

## Nodes {#nodes}

All adopted nodes of the region with model, cell, location, roles, trust level and phase – filterable and sortable.

::: html
<figure class="shot">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../assets/img/portal/nodes-en-dark.webp" width="1600" height="1000">
    <img src="../assets/img/portal/nodes-en-light.webp" width="1600" height="1000" loading="lazy" decoding="async" alt="Node list with n1 and node-01 to node-03, all in cell c1, role dns, trust level T1 and phase active.">
  </picture>
  <figcaption>Node list – three nodes were taken in automatically by an adoption rule.</figcaption>
</figure>
:::

## Node detail {#node-detail}

Identity, operating system state (A/B updates), location in the data center, roles and membership in the control group. Reinstall, replace and decommission are privileged actions that require confirmation.

::: html
<figure class="shot">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../assets/img/portal/node-en-dark.webp" width="1600" height="1000">
    <img src="../assets/img/portal/node-en-light.webp" width="1600" height="1000" loading="lazy" decoding="async" alt="Detail view of node-01: identity with URN, cell c1, role dns, OS version 0.9.0, operating system running, location not set, roles control, identity and dns, voter of the control group.">
  </picture>
  <figcaption>Node detail with operating system state and control group.</figcaption>
</figure>
:::

## Cells and control group {#cells}

A cell groups nodes with their own Raft control group. The view shows voters, leader and term and checks whether the voters are spread across failure zones so that losing one rack does not stop the control plane.

::: html
<figure class="shot">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../assets/img/portal/cell-en-dark.webp" width="1600" height="1000">
    <img src="../assets/img/portal/cell-en-light.webp" width="1600" height="1000" loading="lazy" decoding="async" alt="Detail view of cell c1 (Rack A): 4 nodes, 3 voters, leader n1, term 2, notice well distributed, list of the cell's nodes.">
  </picture>
  <figcaption>Cell c1 with control group and failure-zone check.</figcaption>
</figure>
:::

## Platform DNS {#dns}

Zones of the region, answered by <code>cp-dnsd</code> on the nodes with the dns role, with fixed VIPs, DNSSEC and automatically generated platform records for the portal and the nodes.

::: html
<figure class="shot">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../assets/img/portal/dns-en-dark.webp" width="1600" height="1000">
    <img src="../assets/img/portal/dns-en-light.webp" width="1600" height="1000" loading="lazy" decoding="async" alt="DNS view of the region: two fixed VIPs from the documentation range with the nodes currently holding them, below the zone byoc.example with 5 custom and 20 platform records, DNSSEC on, served by all four nodes.">
  </picture>
  <figcaption>Platform DNS: zone byoc.example with DNSSEC.</figcaption>
</figure>
:::

## Platform releases {#releases}

Signed release bundles are verified (signature chain, security epoch, minimum version) and stored content-addressed on several holders; nodes fetch their updates from there.

::: html
<figure class="shot">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../assets/img/portal/releases-en-dark.webp" width="1600" height="1000">
    <img src="../assets/img/portal/releases-en-light.webp" width="1600" height="1000" loading="lazy" decoding="async" alt="List of platform releases 1.0.0 and 0.9.0 in channel stable, phase available, with holders, above it the form for importing a release bundle.">
  </picture>
  <figcaption>Platform releases – simulated releases without artifacts in the lab (hence 0 B).</figcaption>
</figure>
:::

## Operations {#operations}

Every change is a traceable operation with channel (API, portal, MCP, system), initiator, progress and result.

::: html
<figure class="shot">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../assets/img/portal/operations-en-dark.webp" width="1600" height="1000">
    <img src="../assets/img/portal/operations-en-light.webp" width="1600" height="1000" loading="lazy" decoding="async" alt="List of the region's operations with action, target, channel, initiator, progress and status succeeded.">
  </picture>
  <figcaption>Operations with channel and initiator.</figcaption>
</figure>
:::

## Setup wizard {#setup}

Initial setup runs in the browser: setup token and confirmation code from the first node's console, hardware and network checks, then platform, region, portal address and DNS. Before anything is executed, the wizard shows the complete plan.

::: html
<figure class="shot">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../assets/img/portal/setup-de-dark.webp" width="1600" height="644">
    <img src="../assets/img/portal/setup-de-light.webp" width="1600" height="644" loading="lazy" decoding="async" alt="Excerpt from the setup wizard (German interface): list of the plan's effects – platform demo with trust domain byoc.example, region eu-demo-1 with cell c1, certificate authorities, recovery shares, first administrator, DNS zone byoc.example with two VIPs.">
  </picture>
  <figcaption>Setup wizard, excerpt: effects of the plan before execution (the wizard is currently German only).</figcaption>
</figure>
:::

More about the concepts behind these views: [portal concept](docs/portal.html), [features](features.html), [architecture](architecture.html) and the [documentation](docs/index.html).
