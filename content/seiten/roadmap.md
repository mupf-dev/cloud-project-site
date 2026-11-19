title: Status und Roadmap
summary: Wo BYOC steht, in welcher Reihenfolge die Funktionen entstehen und woran der MVP gemessen wird.
toc: ja
---
## Aktueller Stand

> **Vor dem ersten Release.** Version 0.x, alle API-Gruppen in `v1alpha1`. Noch nicht für den
> Produktiveinsatz geeignet. BYOC (Build Your Own Cloud) ist ein Alpha-Name.

- <span class="status-ok">Abgeschlossen:</span> Architektur und Konzepte – Meilenstein
  „Architektur steht“ am 2026-11-12. Lizenzentscheidung (AGPL-3.0-or-later für den Kern) am
  2026-11-12, Entscheidungen zum Speicherkonzept am 2026-11-14.
- <span class="status-run">In Arbeit – Phase 1 „Fundament“:</span> Agent und Steuerungsebene
  (Raft je Zelle, Gossip, Zeuge), Ressourcen-API mit REST, MCP und Kommandozeile, Portal,
  interne PKI, Identitätsdienst, Netzboot und Adoption, Installer, OS-Image cpOS für amd64 und
  arm64 mit A/B-Updates, signierte Release-Bündel, Rollout-Controller und Plattform-DNS.
- <span class="status-plan">Geplant:</span> die weiteren Phasen unten – in dieser Reihenfolge, ohne
  feste Termine.

## Phasen

Die Nummerierung folgt dem Rollenkatalog des Vision-Konzepts; aufgeführt sind die Phasen, denen dort Rollen und Dienste zugeordnet sind.

| Phase | Schwerpunkt | Rollen und Dienste |
|---|---|---|
| 1 | Fundament | Agent, Steuerungsgruppe (`control`), Zeuge (`witness`), API/Portal/MCP, Sicherheitsgrundlagen |
| 3 | Boot und Adoption | Netzboot-Dienst (`boot`), Discovery-Quarantäne, Installation, Updates |
| 4 | Identität und Mandanten | Rolle `identity`, Passkeys, Föderation, Rechtemodell, Kontingente |
| 5 | Netzwerk | Mandanten-Overlay, Sicherheitsgruppen, `network-gateway` mit NAT, Floating IPs, Load Balancer |
| 6 | Compute | virtuelle Maschinen, Container Instances, Managed Kubernetes |
| 7 | Speicher | Block-Volumes, S3-kompatibler Objektspeicher |
| 8 | Beobachtbarkeit | Metriken, Logs, Traces, Rolle `observability` |
| 9 | Erweiterte Dienste | Datenbanken, Secrets, DNS-Dienst für Mandanten, Warteschlangen, Serverless, Dateispeicher, GPU/NPU, OpenTofu-Provider, KI-Inferenz |
| 10 | Verbund | mehrere Regionen und Standorte, globale Identität und API |

Nach dem MVP folgen Ausbaustufen wie Hardware-Attestierung als Voraussetzung für dauerhafte
Auto-Adopt-Regeln, replizierte Block-Volumes nach bestandenem Reife-Gate, ein Topologie-Modell für
Racks sowie Erasure Coding für Objekt- und Archivklassen. Die API-Gruppen gehen nach dem MVP von
`v1alpha1` über `v1beta1` zu `v1`.

## Qualitätstore

- **Phase-1-Gate:** Ausfallfestigkeit (zwei Knoten plus Zeuge, kein Single Point of Failure ab drei
  Knoten) wird sowohl in einer **deterministischen Simulation** mit 10.000 Zufallssaaten ohne
  Invariantenverletzung als auch auf **echter Hardware** nachgewiesen.
- **Vor jedem Phasen-Gate:** Tests auf realer Hardware (Raspberry Pi, Notebooks, Server).
- **Vor jedem Minor-Release:** Jepsen-artige Konsistenzprüfungen.
- **Vor Mandantendaten auf replizierten Volumes:** Reife-Gate mit Simulation, Fehlerinjektion,
  Langlauf, Wiederherstellungstest und externem Review.

## Erfolgskriterien für den MVP

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

## Nicht-Ziele

BYOC baut **keinen eigenen Hypervisor**, **kein verteiltes Dateisystem von Null** und
setzt **nicht auf Kubernetes als Fundament** der Plattform. Bewährte, quelloffene Komponenten
werden hinter klaren Prozessgrenzen integriert. Mehr dazu in
[Vision, Begriffe und Abgrenzung](doku/vision.html).
