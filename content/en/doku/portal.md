title: Portal technology
summary: Architecture decision for the web portal – why a Svelte 5 SPA embedded in the agent won out over Rust/WASM, React and server-side rendering.
group: konzept
order: 120
quelle: Concept 11 (ADR Portal Technology)
de: portal
---

> Status: **accepted** on 2026-11-12 after an open-ended comparative prototype. Decision: **Svelte 5 + Vite as a pure single-page app** (without SvelteKit), **Bits UI** for complex accessible building blocks, all other components built in-house following the WAI-ARIA Authoring Practices.

## Context

- On **every node**, the Rust agent serves the API, web portal and MCP itself. There is no central web server; the portal is **embedded as static assets in the agent binary** and must be servable even from a Raspberry Pi with a small memory budget.
- **Parity principle:** every API operation is also available in the portal and via MCP. Forms should be derived **from the API schema** (OpenAPI 3.1 / JSON Schema) wherever possible, so that new API features appear without manual work (see [API-first](api-first.html)).
- **Feature scope:** initial setup wizard, node and hardware overview with adoption, live updates, tenant self-service (VMs, containers, Kubernetes, volumes, buckets, networks), serial console and VNC, charts, German/English, light and dark themes, and **accessibility according to BITV 2.0 / WCAG 2.1 AA** for public-sector use.
- **Security:** a strict Content Security Policy without inline scripts and without `eval`, a traceable supply chain (SBOM). Text supplied by tenants or devices is **never rendered as HTML** and is visibly marked as third-party content.
- **Confirmation page:** for out-of-band confirmation of destructive actions and of adoption, the platform renders a dedicated page with an impact report and passkey confirmation. It is part of the portal but is populated exclusively by the platform – never by an AI client.
- The guiding principle "own components in Rust" applies to the **control plane**. The portal is a client of the API, not a control component – so the choice of language was open.

## Decision drivers

| Criterion | Weight | Why |
|---|---|---|
| Accessibility (WCAG 2.1 AA / BITV 2.0) | high | Mandatory for public authorities; expensive to retrofit |
| Schema-driven forms / parity | high | Otherwise the portal backlog grows with every API version |
| Component ecosystem (tables, charts, terminal, VNC, dialogs) | high | A large share of the work |
| Security and supply chain (CSP, SBOM) | high | Compliance by design, browser attack surface |
| Maturity and longevity | high | The platform is to be maintained for at least ten years |
| Contributor pool, development speed | medium-high | An open source project lives on contributions |
| Type safety against the API | medium | "Client/server drift" class of bugs |
| Bundle size, embedding in the binary | medium | Binary size, load time over slow links |
| Load on Pi nodes | medium | Serving only, rendering happens in the browser |
| Internationalization, theming | medium | Standard requirement |
| Testability incl. automated accessibility checks | medium | Regression tests in CI |

## Options considered

| Family | Options |
|---|---|
| **A – Rust/WASM** | Leptos (client-side, optionally with server-side rendering), Dioxus, Yew |
| **B – TypeScript SPA** (statically built, served by the agent) | React, Svelte 5 (with or without SvelteKit), SolidJS, Vue 3 |
| **C – Server-side rendering in Rust** | HTMX with server-side HTML templates |

### Maturity of Rust frontends (as of November 2026)

- **Leptos:** stable 0.8 line, version 0.9 in beta with further breaking changes; a very small circle of core developers, no 1.0 in sight. Component libraries exist, but without demonstrated WCAG conformance.
- **Dioxus:** company-backed, with accessible base components ("primitives"), but likewise pre-1.0, with the next major version bringing breaking changes; increasingly focused on desktop and mobile.
- **Yew:** in maintenance mode; no longer advisable for a new project.

**Conclusion:** all Rust frontends are pre-1.0 and break their APIs roughly once a year. For a platform aimed at the public sector with a ten-year horizon, that is a significant risk that does not arise in the same way with the major versions of the TypeScript frameworks, which have been stable for years.

## Assessment

Scale: ++ very good · + good · o neutral · − weak · −− critical

| Criterion | Leptos | Dioxus | React | Svelte | Solid | Vue | HTMX |
|---|---|---|---|---|---|---|---|
| Accessibility | − | o | ++ | + | + | + | + / − for dynamic widgets |
| Schema forms | − | − | ++ | + | o | + | o |
| Components (charts, terminal, VNC) | − | − | ++ | + | o | + | − |
| CSP and supply chain | ++ | + | o | o | o | o | ++ |
| Maturity, longevity | − | − | ++ | + | o | + | + |
| Contributors, speed | − | o | ++ | + | o | + | o |
| API type safety | ++ | ++ | + | + | + | + | ++ |
| Bundle, embedding | o | o/− | + | ++ | ++ | + | ++ |
| Load on the Pi | + | + | + | + | + | + | − |
| i18n, theming | o | o | ++ | + | o | ++ | + |
| Testability | o | o | ++ | ++ | + | ++ | + |

### Key trade-offs

**1. Rust's type-safety advantage is smaller than it looks.** Shared Rust types are the strongest argument for Leptos or Dioxus. But since the portal works from the OpenAPI schema anyway, the schema is the actual source of the contract. A type-safe TypeScript client generated on every build, plus a CI check, catches drift just as reliably. Generic form rendering works with JSON Schema at runtime – compile-time type safety does not help there in any language.

**2. The hard widgets are JavaScript – whatever the framework.** Terminal emulation (serial console), VNC, time-series charts and mature accessible data tables exist only in the JS ecosystem. Rust/WASM would need bridges for each of them – and would still bring npm into the supply chain.

**3. Accessibility is the toughest criterion.** BITV requires accessible comboboxes, dialogs with focus traps, sortable tables, live regions for real-time updates and full keyboard operation. The JS ecosystem has proven headless libraries for this; the Rust ecosystem has only a young approach with no audit history. In our experience, building accessible widgets in-house is the most expensive and error-prone frontend work.

**4. Supply chain: npm vs. cargo.** npm suffered several large-scale compromises in 2025. cargo is not immune, but has a flatter dependency landscape. **The risk with TypeScript is real but manageable**, because npm packages run only at build time and only the reviewed, bundled output ends up in the binary.

**5. Load on the Pi argues against server-side rendering.** All SPA variants serve only precompressed static files – CPU load close to zero. HTMX, by contrast, renders every view in the agent and creates a **second presentation interface alongside the REST API**. The API would no longer be the single source of truth, which contradicts parity. Console, VNC and charts would still need JavaScript.

**6. Server-side rendering with hydration brings no benefit here.** SEO and fast first page load are irrelevant for an authenticated admin portal; it would only shift load onto Pi nodes.

## The comparative prototype

Instead of fixing the technology up front, an **open-ended comparison** was carried out: Svelte and Leptos were measured against the same views that are critical for accessibility; React remained the fallback option.

| View | Tests |
|---|---|
| Node overview with adoption | Table accessibility, live regions, dialog focus trap, live updates, theme |
| "Create VM" purely from OpenAPI | Schema renderer, drift check, i18n, form accessibility |
| VM detail with console, VNC and time series | Lazy loading, strict CSP, keyboard operability, bundle budgets |
| Confirmation page | Passkey integration, strict CSP, no rendering of third-party content as HTML |

Acceptance criteria included: meeting the performance budgets, a CSP without `unsafe-inline` and `unsafe-eval`, zero serious findings from automated accessibility checks plus manual testing with screen readers (NVDA, Orca) and keyboard only, schema changes appearing in the form without portal code changes, SBOM generation for the portal build, and measured serving from the Pi.

**Result:** the Svelte variant came in at around **28 KiB of initial JavaScript** (Brotli), ran with a **CSP without any exceptions** and had no findings from the automated accessibility checks. The Leptos variant was considerably larger at around 191 KiB, needed a CSP exception for WebAssembly and had a much longer build time. Because SvelteKit generates an inline bootstrap script, the choice fell on **plain Vite + Svelte** instead of SvelteKit.

## Decision

The portal is a **Svelte 5 single-page app built with Vite**, statically bundled, precompressed and embedded in the agent binary. Type safety against the API comes from code generation from OpenAPI; forms are rendered at runtime from JSON Schema with the project's own schema extensions.

| Building block | Choice |
|---|---|
| Framework | Svelte 5 + Vite, pure SPA |
| API client | Types generated from OpenAPI + lean fetch client |
| Accessible base components | Bits UI (headless); in-house builds only following WAI-ARIA patterns |
| Styling, theme | CSS custom properties as design tokens; light, dark, high contrast |
| Schema forms | Own renderer for JSON Schema plus extensions for widget, order, translation keys |
| Tables | Headless table library |
| Charts | Small time-series library, complex charts loaded on demand |
| Serial console, VNC | Established JS libraries, loaded on demand |
| Live updates | Server-Sent Events with announcements via live regions; WebSocket only for console and VNC |
| i18n | Translation at build time; keys from the API reused |
| Tests | Unit and component tests, end-to-end tests with automated accessibility checks |

**Why Svelte rather than React?** React has the strongest ecosystem and remains the fallback option. Svelte wins on bundle size – important because every node carries the portal – has far fewer transitive npm dependencies, a low barrier to entry for Rust developers, and built-in accessibility warnings in the compiler.

**Why not Leptos?** Leptos is the most serious Rust candidate, and the advantage of shared types is real. Against it are its pre-1.0 status with a small maintainer circle, a lack of proven accessible components, JS bridges for all core widgets, larger bundles and a smaller contributor pool. The decision will be **reviewed at the end of 2027**. A switch remains possible because the portal talks exclusively through the public API.

### Rejected options

- **Yew:** maintenance mode, weakest ecosystem.
- **Dioxus:** pre-1.0, focus on multi-platform rather than a web admin interface, larger bundles.
- **Leptos with server-side rendering:** load on the Pi, no benefit for an authenticated portal.
- **SolidJS:** technically excellent, but a smaller pool and less mature form and accessibility libraries.
- **Vue 3:** solid, but larger bundles than Svelte and a smaller accessibility ecosystem than React.
- **HTMX with templates:** a second rendering path alongside the API, load on nodes; conceivable at most as an emergency page without JavaScript.

## Consequences

**Positive:**

- Access to mature, accessible components – BITV/WCAG evidence becomes realistic.
- Large contributor pool; frontend developers do not have to learn Rust.
- The portal is a **pure API client** and thus enforces parity technically: whatever the portal can do, the API can do too.
- Small bundles, no rendering load on nodes; the portal works identically from any node.

**Effort and mandatory measures:**

- **A second toolchain** in the build. The portal build runs as a separate CI step; its artifact is fed into the Rust build in versioned form. Rust contributors can build without Node using a prebuilt artifact or a placeholder portal.
- **Actively manage the npm supply chain:** locked dependencies, install scripts disabled by default, a minimum age for new package versions to guard against freshly compromised releases, a limited dependency budget with review of every new dependency, SBOMs for npm and cargo (the portal SBOM is part of the agent SBOM), vulnerability scans in CI and a reproducible portal build.
- **Content Security Policy as a must**, checked automatically: only own sources for scripts and connections, no objects, no embedding in third-party frames, no `unsafe-inline`, no `unsafe-eval`, no tenant HTML.
- Types are not shared but generated – OpenAPI is the source, code generation runs in CI.
- The binary grows by about 1–3 MB. The agent serves the precompressed files directly, without runtime compression, with long-term caching for files with a hash in their name.

### Performance budgets (binding from MVP)

| Metric | Budget |
|---|---|
| Initial JavaScript (Brotli) | ≤ 120 KB |
| Initial CSS (Brotli) | ≤ 30 KB |
| Lazy-loaded parts for console, VNC, charts | ≤ 250 KB each |
| Time to interactive over a 10 Mbit/s link | ≤ 2 s |
| Agent CPU load on a Pi 4 | negligible |
| Serious accessibility findings (automated, all views) | 0 |

## Sign-in and switching nodes

All nodes of a region sit behind a shared regional DNS name and therefore the same origin. The session runs via a cookie for this origin (HttpOnly, Secure, SameSite=Strict, short lifetime); at the ingress node it is exchanged for short-lived tokens bound to the target cell. Switching between regions without signing in again is still open (see [Identity](identity.html)).

## Open issues

- Vocabulary of the schema extensions and the boundary with hand-built views such as the dashboard and console.
- Behavior with mixed versions during a rolling update (feature detection, compatibility window).
- Formal BITV test before a first public-sector pilot, and an accessibility statement (see [Compliance requirements](compliance-requirements.html)).
- Possibly a minimal emergency page without JavaScript for status and initial setup – as a supplement, not a second portal.
- Further languages beyond German and English, and a translation workflow.
