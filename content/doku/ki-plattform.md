title: KI-native Plattform
summary: Wie cloud-project Modelle verwaltet, Inferenz-Endpunkte betreibt, Beschleuniger einplant und KI-Dienste über ein eigenes AI-Gateway mandantensicher und regelkonform bereitstellt.
group: konzept
order: 130
quelle: Konzept 113 (KI-native Plattform)
---

## Was „KI-nativ“ bedeutet

Für cloud-project heißt „KI-nativ“ dreierlei:

1. **KI-Dienste für Mandanten** – Modelle registrieren, als OpenAI-kompatible Endpunkte betreiben, über ein Gateway mit
   Schlüsseln, Budgets und Guardrails nutzen und Wissensbasen (RAG) aufbauen. Das reicht vom Homelab (CPU, Raspberry Pi,
   integrierte GPU, kleine NPUs) bis zum Rechenzentrum mit GPU-Servern.
2. **Die Plattform als Werkzeug für Agenten** – jede Funktion ist über MCP steuerbar (siehe [API-first](api-first.html)).
   Agenten sind eigene Akteure mit Schnittmengen-Rechten (siehe [Identität und Rechte](identitaet.html)).
3. **Compliance by Design für KI** – EU AI Act, DSGVO, BSI AIC4 und C5: Nachweise entstehen aus dem laufenden Betrieb
   (siehe [Compliance by Design](compliance-by-design.html)).

Nicht Gegenstand dieses Konzepts sind KI-gestützter Plattformbetrieb, das Training großer Modelle, Endnutzerprodukte wie
Copiloten, Gesichtserkennung und eigene GPU-Kernel.

Das Vorbild sind die KI-Angebote der Hyperscaler (Katalog, serverlose und dedizierte Endpunkte, Gateway, Guardrails,
Wissensbasen, Agenten-Laufzeit). Ihr gemeinsames Muster übernimmt cloud-project: **Steuerung, Abrechnung und Policy liegen bei
der Plattform, die Inferenz-Engines sind austauschbar.**

## Kernentscheidungen im Überblick

| Thema | Festlegung |
|---|---|
| Ressourcenmodell | eine API-Gruppe `ai.cloud-project.io/v1alpha1`, vollständig API-first (API, Portal, MCP, CLI) |
| Engines | Steuerung eigen, Engines extern hinter einer Prozessgrenze; zuerst llama.cpp, für GPU-Server vLLM |
| Isolation | Mandanten-dedizierte Endpunkte in MicroVMs mit durchgereichtem Beschleuniger; geteilte Modelle als Plattformdienst ohne Mandantencode |
| Treiber | Standard-Image nur mit offenen Stacks; proprietäre Laufzeiten nur als signierte, ausdrücklich freigeschaltete Betreiber-Erweiterung |
| Modelle | OCI-Artefakte in der Plattform-Registry, signiert, mit Cache je Zelle; nur sichere Formate |
| Skalierung | Scale-to-zero nur mit lokalem Modell-Cache; Gateway puffert während der Aktivierung |
| Verteilte Inferenz | zweistufig: zuerst engine-nativ, eigenes Protokoll nur nach Messung |
| AI-Gateway | eigenes, in Rust entwickeltes AI-Gateway – zunächst als eigener Prozess, später als Bibliothek |
| Agenten | Plattform selbst per MCP steuerbar, mit Token-Exchange und Schnittmengen-Rechten |
| Compliance | KI-Compliance als Querschnitt: Modellkarte, Lizenz, Herkunft, Risikoklasse, Kennzeichnung, Nachweise |

Die Entscheidungen wurden am 2026-11-14 festgelegt.

## Ressourcenmodell

Alle KI-Ressourcen folgen dem einheitlichen Ressourcenschema der Plattform (metadata/spec/status, URN, Conditions,
lang laufende Operationen, siehe [Steuerungsebene](steuerungsebene.html)). Projektressourcen sind regional; Katalogobjekte des
Betreibers liegen im globalen Plattformbereich.

| Art | Zweck |
|---|---|
| `Model` | logisches Modell: Familie, Aufgaben (Chat, Embedding, Rerank, Sprache, OCR, Vision), Lizenz, Herkunft, Modellkarte, AI-Act-Metadaten |
| `ModelVersion` | unveränderliches Artefakt: OCI-Referenz mit Digest, Format, Quantisierung, Kontextlänge, Speicherbedarf, Engine-Kompatibilität, Signaturstatus, Stufe (`draft` bis `deprecated`), Herkunftskette, Evaluationsergebnisse |
| `InferenceEndpoint` | gewünschter Dienst: API-Arten, Traffic-Aufteilung auf Revisionen, Skalierung, Platzierung, Netz |
| `InferenceDeployment` | unveränderliche **Revision** eines Endpunkts (Modellversion, Engine, Ressourcen, Parallelität); Canary und Rollback über Gewichte |
| `AiGateway` | Instanz bzw. Mandantenbereich des AI-Gateways mit Eingängen, Standard-Policies und Log-Politik |
| `GatewayRoute` | öffentlicher Modellname → Ziele (interne Endpunkte, externe Anbieter), Gewichte, Fallbacks, Limits, Guardrails, Cache |
| `AiBudget` | Betrag, Zeitraum, Warnschwellen, Token-Limits – an Projekt, Dienstkonto, Schlüssel oder Route |
| `GuardrailPolicy` | geordnete Filterkette (PII, Prompt-Filter, Prüfmodell, Themensperren, KI-Kennzeichnung) mit Fehlerverhalten |
| `VectorIndex`, `KnowledgeBase` | Vektorindex und Wissensbasis für RAG |
| `BatchInferenceJob` | Stapelverarbeitung aus dem Objektspeicher, nutzt Restkapazität |
| `AcceleratorClass` | Betreiberdefinierte Beschleunigerklasse: Selektor über das Inventar, Teilbarkeit, Preis, Mindest-Vertrauensstufe |

Ein vereinfachtes Beispiel für einen Endpunkt:

```yaml
apiVersion: ai.cloud-project.io/v1alpha1
kind: InferenceEndpoint
metadata:
  name: chat
spec:
  apis: [openai.chat, openai.completions]
  traffic:
    - { deployment: r7, percent: 90 }
    - { deployment: r8, percent: 10 }   # Canary
  scaling: { minReplicas: 0, maxReplicas: 4, scaleToZeroAfter: 15m, coldStartTimeout: 120s }
  placement: { arch: any, minTrustLevel: basic, dataClass: standard, spreadBy: zone }
  network: { exposure: private, gateway: default }
  deploymentTemplate:
    engine: { kind: llama-cpp, version: auto }
    resources: { accelerator: { class: igpu-vulkan, count: 1 }, memoryGiB: 12, cpu: 4 }
```

**Keine eigene KI-Schlüsselart.** Aufrufer authentisieren sich mit Plattform-Identitäten: Workload-Token, API-Schlüssel von
Dienstkonten oder Nutzer-Token. Als Komfortfunktion legt die Portal-Abkürzung „KI-Schlüssel erstellen“ in einem Schritt ein
Dienstkonto mit Aufrufrecht auf die gewählten Routen und ein Budget an. Plattform-Workloads nutzen ihre Workload-Identität ganz
ohne gespeicherten Schlüssel.

**Rechte und Audit.** Das Aufrufen eines Endpunkts (`invoke`) ist ein eigenes Recht der Datenebene, getrennt von der
Verwaltung. Das Löschen produktiver Modellversionen oder befüllter Wissensbasen gilt als destruktiv und braucht eine Bestätigung
außerhalb des aufrufenden Clients. Modellausgaben und Dokumentinhalte sind als nicht vertrauenswürdig markiert: Agenten erhalten
sie als Daten, nie als Anweisungen, und das Portal rendert sie nie als HTML. Prompts und Antworten sind Mandanteninhalt und
gehören nicht ins Plattform-Audit; nur Nutzungsmetadaten (Token, Modell, Route, Kosten, Guardrail-Treffer) gehen ans Metering.

## Inferenz-Engines

Die Leistung von Inferenz entsteht in handoptimierten Kerneln für CUDA, ROCm, Vulkan, AVX oder NEON, die große Communities
pflegen. Eine Eigenentwicklung wäre hier nicht sinnvoll. **Eigen ist alles drumherum:** Adapter, Endpunkt-Proxy,
Scheduler-Anbindung, Cache und Verteilung, Gateway, Metering und Compliance.

| Engine | Lizenz | Rolle |
|---|---|---|
| llama.cpp | MIT | **erste Engine**: breiteste Hardware (CPU, Vulkan, CUDA, ROCm), arm64 und amd64, GGUF, auch für Embeddings und Reranker |
| vLLM | Apache-2.0 | **zweite Engine** für GPU-Server: Tensor-, Pipeline-, Expert- und Datenparallelität |
| ONNX Runtime, whisper.cpp | MIT | für OCR/Vision bzw. Spracherkennung, jeweils als eigener Engine-Prozess |
| Hailo-Laufzeit | teilweise proprietär | nur als Betreiber-Erweiterung für Randdienste (Vision, Sprache, kleine LLMs) |
| candle und andere Rust-Engines | permissiv | derzeit nicht eingesetzt; Kandidaten für spätere Neubewertung |
| Ollama, TGI | – | nicht eingesetzt (doppelte Modellverwaltung bzw. Wartungsmodus) |

Eine CPU-Vergleichsmessung zeigte eine Rust-Engine auf candle-Basis bei 44–65 % der Decode- und 25–47 % der
Prefill-Leistung von llama.cpp. Deshalb laufen **alle** Modellarten – auch Embeddings und Reranker – über externe Engines.

### Engine-Adapter-Vertrag

Engines laufen als signierte OCI-Images im Container-Dienst der Plattform, nie direkt mit Mandantenrechten:

- **Image** aus dem Engine-Katalog des Betreibers, Freigabe pro Version, mit SBOM und Provenienz.
- **Modell** als schreibgeschützte Einbindung aus dem lokalen Zell-Cache – kein Download im Engine-Prozess, kein Egress.
- **Schnittstelle:** OpenAI-kompatibles HTTP auf einem Unix-Socket. Ein eigener Endpunkt-Proxy terminiert mTLS bzw.
  Workload-Token, setzt Nebenläufigkeitslimits, zählt Token und liefert Skalierungssignale. Engines sprechen nie direkt mit
  Mandanten oder Gateway.
- **Pflichtfunktionen** je Adapter: Startbeschreibung, Bereitschaft, Metriken (Warteschlange, laufende Sequenzen, Token,
  KV-Cache-Auslastung), Fähigkeiten und geordnetes Herunterfahren. Eine neue Engine braucht nur Adapter und Image.
- **Sandbox:** eigener Benutzer, seccomp/Landlock, nur die benötigten Gerätedateien, kein Netz außer dem Socket.

Weil Engines als Prozess betrieben und nicht gelinkt werden, sind auch Copyleft-Lizenzen unkritisch. Modellgewichte haben
**eigene** Lizenzen, teils mit Nutzungsbeschränkungen; der Katalog führt sie als Pflichtfeld, kennzeichnet nicht-OSI-Lizenzen und
kann sie per Richtlinie sperren.

## Beschleuniger und Platzierung

Das Knoteninventar erkennt Beschleuniger (Hersteller, Modell, Speicher, Treiber- und Firmwarestand, IOMMU-Gruppe, NUMA-Knoten,
PCIe-Link, Teilbarkeit). Geräteauskünfte gelten als nicht vertrauenswürdig; über die Eignung entscheiden eine
Smoke-Inferenz bei der Aufnahme und Betreiber-Labels.

| Gerät | Stack | Einordnung |
|---|---|---|
| CPU (AVX2/AVX-512/NEON) | offen | Basis, immer verfügbar; kleine Modelle, Embeddings, Batch |
| integrierte GPU (Vulkan) | offen | gut fürs Homelab |
| AMD-GPU (ROCm) | offen | empfohlen für einen durchgehend offenen Stack |
| NVIDIA-GPU (CUDA) | Userspace proprietär | Marktstandard, nur als signierte Betreiber-Erweiterung |
| NPUs (AMD XDNA, Intel) | teils offen | beobachten, später |
| Hailo-Module | Compiler proprietär | Betreiber-Erweiterung für Randdienste |

**Isolation.** Mandanten-dedizierte Endpunkte erhalten ein ganzes Gerät, das per VFIO an genau eine MicroVM durchgereicht wird –
es gibt keinen geteilten Kernel zwischen Mandanten (siehe [Sicherheitsmodell](sicherheitsmodell.html)). Geräte ohne saubere
IOMMU-Trennung dienen nur geteilten Plattformdiensten. GPU-Teilung zwischen Mandanten per Container ist erst in einer späteren
Phase und nur mit Hardware-Partitionierung (MIG) vorgesehen; Zeitscheibenverfahren ohne Hardware-Isolation bleiben
ausgeschlossen.

**Anforderungen an den Scheduler:**

1. Beschleuniger als harte Ressource (Klasse, Anzahl, Mindestspeicher), Bin-Packing nach Beschleunigerspeicher.
2. **Gang-Scheduling:** ein Mehrknoten-Deployment wird ganz oder gar nicht platziert.
3. **Topologie:** Mindestbandbreite, gleiche Zone, maximale Netzsprünge.
4. **Cache-Affinität:** Knoten mit dem Modell im lokalen Cache werden bevorzugt.
5. **Prioritäten:** Produktion vor interaktiv vor Batch; Batch-Jobs sind verdrängbar.
6. **Kontingente** für Beschleuniger und Beschleunigerspeicher; geteilte Modelle über Token-Budgets.
7. **Vertrauensstufe** und Datenklasse wie bei virtuellen Maschinen.

## Betriebsmodelle

| | Dediziert | Geteilt (serverless) | Extern |
|---|---|---|---|
| Betreibt die Engine | Mandant (Plattform-Steuerung) | Betreiber | Drittanbieter |
| Isolation | MicroVM mit durchgereichtem Gerät | Prozess des Betreibers mit Zusatzregeln | Vertrag/AVV |
| Abrechnung | Gerätestunden | Token | Token, Weiterberechnung |
| Modelle | beliebig, auch eigene Fine-Tunes | Katalog des Betreibers | Anbieterkatalog |
| Typisch | Datenschutz, eigene Modelle | kleine Teams, Embeddings | Spitzenmodelle |

Für geteilte Modelle gelten feste Regeln: **kein mandantenübergreifender Prefix- oder KV-Cache**, Quoten je Mandant, keine
Speicherung von Prompts ohne Zustimmung, Speicher nach der Anfrage verworfen, Engine-Prozess ohne Netz, sensible Daten nur auf
Knoten hoher Vertrauensstufe. Alle drei Modelle laufen über dasselbe Gateway: ein Schlüssel, ein Budget, eine Policy.

## Skalierung und Scale-to-zero

Ein Kaltstart besteht aus Platzierung, Container-Start, Modell-Laden und Warmup – das Laden dominiert. Ein 8B-Modell (Q4, rund
5 GB) lädt von lokaler NVMe in wenigen Sekunden, über 1-GbE aus dem Zell-Cache aber in rund 45 Sekunden; ein 70B-Modell braucht
über 1 GbE mehrere Minuten. Daraus folgt:

- Scale-to-zero nur, wenn das Modell **lokal** liegt (Cache-Affinität, Vorwärmen bei Anlage).
- Das Gateway puffert Anfragen während der Aktivierung und antwortet nach Ablauf mit `503` und `Retry-After`.
- Skalierungssignal sind Warteschlangenlänge und laufende Sequenzen je Replik, nicht die CPU-Last.
- Vorlage: im Homelab nach 15 Minuten Leerlauf schlafen legen, in Produktion mindestens eine Replik.

## Modellverteilung: OCI und Signatur

- **Format:** Ein Modell ist ein OCI-Artefakt mit eigenem Medientyp; die Schichten sind Gewichte, Tokenizer, Modellkarte und
  Lizenztext. Große Dateien werden in Chunks zerlegt – für parallele Übertragung und Deduplizierung.
- **Import:** Ein Import-Job lädt aus einer explizit freigegebenen Quelle, prüft Hashes, erzeugt eine **Modell-Stückliste**
  (Dateien, Hashes, Lizenz, Quelle, Revision) und signiert sie mit dem Plattform-Codesigning (siehe
  [Kryptografie](kryptografie.html)). Herstellersignaturen werden zusätzlich geprüft, wenn vorhanden. Ohne gültige Signatur
  keine Platzierung in regulierten Profilen; im Homelab gibt es eine Warnung.
- **Nur sichere Formate:** safetensors und GGUF. Pickle-basierte Formate werden in **allen** Profilen beim Import abgewiesen.
- **Cache je Zelle:** Jeder Inferenzknoten hält einen inhaltsadressierten, verschlüsselten Cache. Knoten übertragen Modelle
  untereinander per mTLS mit Bereichsanfragen – zuerst von Nachbarn, dann aus der Registry. Per Gossip wird nur verbreitet, wer
  welchen Digest hat.
- **Mandantenmodelle** (eigene Fine-Tunes) sind Mandanteninhalt, liegen mit Mandantenschlüssel verschlüsselt und lassen sich
  per Krypto-Löschung sicher entfernen.

## Verteilte Inferenz

Welche Aufteilung sinnvoll ist, hängt vom Netz ab:

| Verfahren | Netzbedarf | Eignung über 1 GbE |
|---|---|---|
| Datenparallel (Repliken) | keiner | **beste Wahl**, solange das Modell auf einen Knoten passt |
| Pipeline (Schichten auf Knoten) | Aktivierungen an Stufengrenzen, wenig latenzempfindlich | gut |
| Expert (MoE) | All-to-All je MoE-Schicht | mittel, abhängig vom Modell |
| Tensor | zwei Synchronisationen je Schicht, sehr latenzempfindlich | nur innerhalb eines Servers oder mit ≥ 25–100 GbE/RDMA |

**Raspberry-Pi-Cluster** sind realistisch für kleine Modelle, Embeddings und Spracherkennung nahe am Ort, für Batch- und
Hintergrundaufgaben, für MoE-Modelle mit kleinem aktiven Anteil sowie für Lehre und Forschung. Für interaktive Großmodelle
reichen sie nicht: Decode ist speicherbandbreitengebunden (ein 8B-Modell erreicht auf einem Pi 5 grob 2 Token/s), Prefill ist
rechengebunden (lange Prompts brauchen rund eine Minute).

Die Plattform geht deshalb zweistufig vor:

- **Stufe A:** Mehrknoten-Deployments ausschließlich engine-nativ (vLLM, llama.cpp-RPC). Die Plattform liefert
  Gang-Scheduling, Topologie-Bedingungen, ein abgeschottetes, verschlüsseltes **Engine-Mesh** je Deployment, Health und
  gemeinsame Abschaltung.
- **Stufe B:** ein eigenes Rust-Protokoll für Pipeline- und Expert-Parallelität nur dann, wenn Stufe A messbar nicht reicht.
  Kein eigenes Tensor-Parallel-Verfahren.

Verkehr im Engine-Mesh ist Mandanteninhalt, weil Aktivierungen Rückschlüsse auf Prompts erlauben, und wird daher verschlüsselt
(siehe [Netzwerk](netzwerk.html)).

## AI-Gateway

Das AI-Gateway ist der gemeinsame Eingang für alle KI-Aufrufe. Sein Funktionsumfang:

- OpenAI-kompatible Datenebene (Chat, Completions, Embeddings, Audio, Bilder) sowie das Anthropic-Messages-Format.
- Routing auf interne Endpunkte und externe Anbieter mit Gewichten, Prioritätsgruppen, Fallback, Retry und Circuit Breaker.
- Authentisierung ausschließlich mit Plattform-Identitäten (signierte Token mit Zielgruppenbindung, gebundene Schlüssel).
- Limits (Anfragen, Token, Nebenläufigkeit) und Budgets je Projekt, Dienstkonto, Schlüssel und Route; Token-Metering mit Preisen.
- Guardrails: PII-Erkennung, Prompt-Injection-Heuristik, Prüfmodelle, Themensperren.
- Exakter und semantischer Cache, **je Projekt getrennt**.
- Payload-Logging nur per Opt-in; MCP-Gateway; Beobachtbarkeit über OpenTelemetry; Audit der Konfiguration.

**Grundlage ist ein eigenes, in Rust entwickeltes AI-Gateway** unter derselben Lizenz (AGPL-3.0-or-later, siehe
[Lizenz und Governance](lizenz-governance.html)) und mit deckungsgleichem Technologie-Stack (siehe
[Rust-Stack](rust-stack.html)). Ein Neubau hätte Monate an Arbeit wiederholt. Das Gateway bietet bereits Mandantenstrukturen,
Routing, Limits, Guardrails, MCP-Gateway, deklarative Konfiguration und einen sehr geringen Latenzaufschlag im
Sub-Millisekunden-Bereich.

### Integrationsvarianten

| Variante | Beschreibung | Status |
|---|---|---|
| **V1 Prozess** | Gateway als Plattformdienst-Image; ein Controller übersetzt Plattform-Ressourcen in die deklarative Gateway-Konfiguration | erster Schritt |
| **V2 Bibliothek** | Kernbausteine des Gateways als Bibliothek eines Plattformdienstes; Konfiguration direkt aus den Plattformressourcen, UI im Portal | Ziel für ein späteres 1.x-Release |
| V3 Neubau | eigener Gateway innerhalb von cloud-project | verworfen (Doppelarbeit) |

Im Plattformbetrieb ist die **Plattform die einzige Wahrheit**: Die eigene Verwaltungsoberfläche des Gateways ist abgeschaltet,
lokale Datenhaltung dient nur als Cache. Mandanten werden auf Organisationen, Projekte auf Teams, Routen auf Modellgruppen,
Budgets und Guardrail-Policies auf die entsprechenden Gateway-Objekte abgebildet.

Die Schnittstellen zwischen Plattform und Gateway sind klar definiert: externe Authentisierung der Datenebene gegen den
Plattform-Autorisierungsserver, Konfigurationsquelle, Anbieter für interne Endpunkte mit Dienst-Discovery und Kaltstartsignal,
plattformweite Zähler für Budgets, Nutzungsereignisse **ohne Payload** ans Metering, Audit, Geheimnisse aus dem Secrets
Manager (nie in Konfiguration oder Log), TLS-Profil nach Kryptokonzept, Token-Exchange zum Plattform-MCP-Server und
Payload-Logs nur per Opt-in im verschlüsselten Mandanten-Bucket.

**Platzierung:** regionaler Plattformdienst mit mindestens zwei Instanzen hinter dem L7-Load-Balancer. Jede Instanz hält einen
vollständigen Konfigurations-Snapshot und arbeitet bei Ausfall der Steuerung mit dem letzten Stand weiter. Optional gibt es ein
projekteigenes Gateway im Mandanten-VPC. Weil Prompts im Klartext durchlaufen, gelten dieselben Vertrauensstufen wie für
öffentliche Eingänge.

## RAG und Vektorsuche – Leitplanken

- Die Pipeline ist **eigen**: Quellen aus Buckets → Parser (extern als Prozess) → Chunking → Embedding über einen
  Inferenz-Endpunkt → Index → Abfrage-API und OpenAI-kompatible Einbindung über das Gateway.
- Index: eingebettet für kleine Installationen, Qdrant als eigener Prozess für große, pgvector über den Datenbankdienst;
  Hybridsuche mit BM25.
- **Berechtigungen auf Dokumentebene:** Jede Abfrage filtert nach den Rechten des aufrufenden Principals. Ohne diese
  Filterung würde RAG zum Kanal für Datenabfluss.
- Indizes und Embeddings sind Mandanteninhalt; das Löschen einer Quelle entfernt Chunks und Vektoren mit Nachweis.

## MCP und Agenten

- **Plattform per MCP:** Alle KI-Ressourcen erscheinen automatisch als MCP-Werkzeuge. Agenten können Modelle importieren,
  Endpunkte anlegen und Budgets setzen – mit Schnittmengen-Rechten und Bestätigung destruktiver Aktionen.
- **Agenten der Mandanten über das Gateway:** Das MCP-Gateway bündelt die MCP-Server der Mandanten und den Plattform-MCP-Server.
  Statt Token durchzureichen, wird per Token-Exchange (RFC 8693) ein neues Token mit Akteurskette und eingeschränkten Scopes
  ausgestellt. Jeder Werkzeugaufruf wird mit Principal und Akteur protokolliert und gegen Limits gezählt.
- **Agenten-Laufzeit** (spätere Phase) baut auf Gateway, Workload-Identität, Containern und Functions auf; ihr Gedächtnis sind
  Wissensbasen und Objektspeicher.
- **Prompt-Injection:** Modellausgaben und abgerufene Dokumente sind nicht vertrauenswürdig. Destruktive Plattformaktionen eines
  Agenten bleiben an eine Bestätigung außerhalb des Clients gebunden – die wirksamste Gegenmaßnahme gegen indirekte
  Prompt-Injection (siehe [Bedrohungsmodell](bedrohungsmodell.html)).

## Mandantentrennung und Datenschutz

| Thema | Festlegung |
|---|---|
| Prompts und Antworten | Mandanteninhalt; keine Speicherung ohne Opt-in; Einsicht durch den Betreiber nur über einen genehmigten Zugriffsantrag |
| Nutzungsmetadaten | Abrechnungs- und Metadaten; Principals in Betreibersichten pseudonymisiert |
| KV-/Prefix-Cache | nie mandantenübergreifend; Gateway-Cache je Projekt getrennt |
| Modelle der Mandanten | eigenes Repository, Mandantenschlüssel, Krypto-Löschung |
| Externe Anbieter | ausgehende Verbindung explizit freigegeben; Datenstandort je Route, Nicht-EU per Policy sperrbar |
| Training mit Mandantendaten | **nie** durch die Plattform; Fine-Tuning nur als Job des Mandanten |
| Löschung | Endpunkt- und Projektlöschung entfernt Cache, Logs und Indizes, mit Nachweis |
| DSGVO Art. 22/35 | Plattform liefert Bausteine; die Datenschutz-Folgenabschätzung bleibt beim Verantwortlichen |

## EU AI Act und BSI AIC4

**Rollen.** Wer cloud-project betreibt, stellt im Regelfall Infrastruktur bereit und ist weder Anbieter eines KI-Systems noch
eines KI-Modells mit allgemeinem Verwendungszweck (GPAI). Anbieter wird er erst, wenn er ein Modell oder System unter eigenem
Namen bereitstellt. Mandanten sind Betreiber oder Anbieter ihrer KI-Systeme; die Plattform muss ihnen die Pflichterfüllung
**ermöglichen**. Die juristische Einordnung ist im Einzelfall zu prüfen.

| Pflicht (AI Act) | Plattform-Baustein |
|---|---|
| Verbotene Praktiken, KI-Kompetenz | Katalog-Policy sperrt Vorlagen für verbotene Zwecke; vorgesehene und ausgeschlossene Verwendungen je Modell; Hinweise im Portal |
| GPAI-Pflichten | AI-Act-Status je Modell (GPAI, systemisches Risiko, Verweis auf Anbieterdokumentation); Herkunftskette von Fine-Tunes |
| Transparenz (Art. 50) | Guardrail-Baustein „KI-Hinweis“, maschinenlesbare Kennzeichnung synthetischer Inhalte |
| Hochrisiko | zunächst Einsatzzweck mit Risikoklasse je Endpunkt; volle Unterstützung (Pflicht-Logs, menschliche Aufsicht, Metriken, Dokumentationsexport) als eigenes Paket in einer späteren Phase |

**BSI AIC4** setzt C5 voraus. Die Plattform trägt bei mit Guardrails, Signatur und Herkunft der Modelle sowie Isolation
(Sicherheit & Robustheit), Evaluationsläufen je Modellversion (Performance), SLOs, Fallback und Canary (Zuverlässigkeit),
Modell-Stückliste und Herkunftskette (Datenqualität), Modellkarten und Quellenangaben bei RAG (Erklärbarkeit) sowie
Evaluations-Sets für Bias. Ergänzend dienen ISO/IEC 42001 und 23894 als Organisationsnormen beim Betreiber und die OWASP Top 10
für LLM-Anwendungen als Prüfkatalog.

**Nachweise** sind maschinenlesbar und signiert: Modell-Stückliste und Signatur je Modellversion, Katalog-Export (Lizenz,
Herkunft, GPAI-Status), Endpunkt-Register (Einsatzzweck, Risikoklasse, Guardrails, Datenstandort), Nutzungsberichte ohne
Inhalte, Löschnachweise und eine OSCAL-Komponentendefinition „AI Services“ mit AIC4- und AI-Act-Mapping (siehe
[Compliance-Anforderungen](compliance-anforderungen.html)).

