title: Bedrohungsmodell
summary: Methode und Prinzipien der Produkt-Risikoanalyse – STRIDE je Vertrauensgrenze, Bewertung und Behandlung nach BSI-Standard 200-3, abstrakte Angreifermodelle, Sicherheitsannahmen und Pflege des Modells.
group: konzept
order: 110
quelle: Konzept 67 (Bedrohungsmodell)
---

Das Bedrohungsmodell ist die **Produkt-Risikoanalyse des Projekts**. Es bewertet die Software und ihre vorgesehene Architektur, nicht einen konkreten Betrieb. Betreiber führen für ihren Informationsverbund eine eigene Risikoanalyse durch; das Modell ist so aufgebaut, dass Bedrohungen, Maßnahmen und Restrisiken als **Vorlage** in ein Betreiber-ISMS übernommen werden können. Diese Seite fasst Methode und Prinzipien zusammen; die Maßnahmen selbst finden sich in den Fachkonzepten, insbesondere im [Sicherheitsmodell](sicherheitsmodell.html) und in der [Kryptografie](kryptografie.html).

## Methode

Bedrohungen werden mit **STRIDE je Vertrauensgrenze** ermittelt und nach **BSI-Standard 200-3** bewertet und behandelt. Das Vorgehen:

1. **Systemmodell:** Schutzobjekte, Datenflüsse und Vertrauensgrenzen.
2. **Angreifermodelle und Annahmen.**
3. **Gefährdungsübersicht:** STRIDE je Grenze; jede Bedrohung wird mindestens einer **elementaren Gefährdung** des IT-Grundschutzes zugeordnet, damit Betreiber sie in ihre 200-3- bzw. Grundschutz++-Werkzeuge übernehmen können.
4. **Risikoeinstufung:** Eintrittshäufigkeit × Schadenshöhe, jeweils brutto (ohne) und netto (mit Maßnahmen).
5. **Risikobehandlung:** Vermeiden, Reduzieren, Übertragen, Akzeptieren.
6. **Konsolidierung** neuer Maßnahmen und verbleibender Risiken.
7. **Rückführung** in die Fachkonzepte und den Entwicklungsprozess.

STRIDE bildet die Schutzziele ab: *Spoofing* verletzt die Authentizität, *Tampering* die Integrität, *Repudiation* die Nichtabstreitbarkeit, *Information Disclosure* die Vertraulichkeit, *Denial of Service* die Verfügbarkeit und *Elevation of Privilege* die Autorisierung. Querschnittlich betrachtet werden Softwareschwachstellen, Produkte aus unzuverlässiger Quelle, Fehlbedienung, Diebstahl und Schadprogramme.

### Bewertungsskalen

Bewertet wird für ein **Referenzprofil „Mehrmandanten-Betrieb“** über ein typisches Betriebsjahr. Die Eintrittshäufigkeit reicht in vier Stufen von *selten* (setzt seltene Fähigkeiten oder eine Fehlerkette voraus) bis *sehr häufig* (der Normalbetrieb erzeugt die Bedingung). Die Schadenshöhe reicht von *vernachlässigbar* bis *existenzbedrohend* – letzteres bedeutet mandantenübergreifenden Vertraulichkeits- oder Integritätsverlust oder die Übernahme einer Zelle, Region oder PKI. Aus beiden ergibt sich eine von vier Risikokategorien: gering, mittel, hoch, sehr hoch.

### Akzeptanzkriterien

| Kategorie | Umgang |
|---|---|
| gering | akzeptiert |
| mittel | akzeptiert unter der Bedingung, dass die Wirksamkeit der Maßnahme nachgewiesen ist (Test, Pentest) |
| hoch | Release-Blocker, sofern nicht ausdrücklich als Restrisiko akzeptiert |
| sehr hoch | nie akzeptiert – die Architektur wird geändert |

Ein Netto-Risiko gilt erst dann als gesenkt, wenn die Maßnahme **umgesetzt und getestet** ist; bis dahin zählt das Brutto-Risiko.

## Vertrauensgrenzen

Das Systemmodell unterscheidet dreizehn Vertrauensgrenzen, darunter: Internet und Nutzer gegenüber Portal und API, KI-Clients gegenüber der MCP-Schnittstelle, Mandant gegenüber Mandant, Mandanten-Workload gegenüber Host, Knoten untereinander, Steuerungsgruppe gegenüber übrigen Knoten, Zeugen, Discovery- und Boot-Netz, Out-of-Band-Management, Lieferkette gegenüber Installation, Betreiber gegenüber Mandanteninhalten, physischer Standort sowie fremde Identitätsanbieter. Für jede Grenze ist festgelegt, was sie überquert und wodurch sie durchgesetzt wird.

## Angreifermodelle

Die Angreifer sind abstrakt nach Ausgangslage und Fähigkeiten modelliert:

- **Externer Angreifer** mit Zugang zu öffentlichen Endpunkten, von automatisierten Scans bis zum gezielten Angriff.
- **Böswilliger Mandant** mit gültigem Konto und beliebigem Code in eigenen Workloads.
- **Kompromittierter Knoten** mit Root-Rechten und dem Schlüsselmaterial dieses Knotens.
- **Fremdes Gerät im Discovery- oder Heimnetz** im selben Netzsegment.
- **Physischer Angreifer** mit kurzzeitigem oder dauerhaftem Zugriff auf Geräte und Datenträger.
- **Böswilliger Betreiber oder Insider** – bewusst stark modelliert.
- **Kompromittierte Abhängigkeit oder Lieferkette.**
- **Kompromittierter oder manipulierter KI-Agent**, etwa über Prompt-Injection gesteuert.
- **Fremdbetreiber eines externen Zeugen.**

Zusätzlich gelten Fehlbedienung, Hardware- und Stromausfälle sowie Softwarefehler als Gefährdungsquellen im Sinne von 200-3.

## Sicherheitsannahmen und Nicht-Ziele

Das Modell beruht auf ausdrücklich benannten Annahmen, darunter: Die eingesetzten kryptografischen Primitive und der Zufallsgenerator sind sicher; CPU, Virtualisierungshardware und IOMMU funktionieren wie spezifiziert; Steuerungsknoten sind physisch geschützt oder verfügen über TPM, Measured Boot und Datenträgerverschlüsselung; höchstens ein Voter einer Zelle ist gleichzeitig kompromittiert (der Konsens ist nicht byzantinisch fehlertolerant); Menschen kontrollieren ihre Authenticatoren; Betreiber erfüllen ihre Pflichten aus der Verantwortungsteilung; die Uhrzeit ist nach dem Start authentisiert.

**Nicht-Ziele** sind der Schutz gegen staatliche Angreifer mit Hardware-Implantaten in Neugeräten, der Schutz von Mandanteninhalten gegen Betreiber mit physischem Zugriff ohne Confidential Computing sowie die Abwehr volumetrischer DDoS-Angriffe auf die Internetanbindung.

## Grundsätze der Risikobehandlung

- **Vermeiden** durch Architekturentscheidungen, die eine Bedrohung entfallen lassen – etwa kein geteilter Kernel zwischen Mandanten, kein interaktiver Login ab Werk, kein automatischer Break-Glass, keine destruktiven Aktionen aus Gossip-Meldungen, keine sicherheitskritischen Rollen bei der Adoption, keine automatische Aufnahme fremder Geräte.
- **Reduzieren** durch technische Maßnahmen in den Fachkonzepten.
- **Übertragen** auf Betreiber (Netztrennung, physischer Schutz, Firmware-Auswahl) oder Mandanten (Gast-Betriebssysteme, eigene Anwendungen) gemäß Verantwortungsteilung, dokumentiert in Betreiber- und Mandantenhandbüchern.
- **Akzeptieren** nur, was nach Reduktion höchstens *mittel* ist oder ausdrücklich vom Risikoeigentümer übernommen wurde.

Leitprinzipien aus der Analyse: Vertrauen darf **nie aus dem Netzboot** entstehen, sondern nur aus einem an einen Geräteschlüssel gebundenen Adoptionsvorgang mit menschlicher Bestätigung oder Allowlist; neue Knoten starten in einer niedrigeren Vertrauensstufe. Destruktive Aktionen von KI-Agenten werden **außerhalb des Clients** bestätigt, weil Prompt-Injection nicht vollständig vermeidbar ist.

## Pflege des Modells

Das Modell wird aktualisiert bei neuen Rollen, Komponenten oder Vertrauensgrenzen, beim Wechsel einer Fremdkomponente, nach Pentest-Befunden und sicherheitsrelevanten Schwachstellen, bei neuen Versionen der MCP-Spezifikation und mindestens vor jedem Minor-Release. Es wird maschinenlesbar gepflegt, sodass die CI prüfen kann, dass jede Bedrohung eine Maßnahme mit Test oder eine dokumentierte Akzeptanz hat. Jede Maßnahme mit Netto-Risiko *mittel* erhält mindestens einen automatisierten Test oder einen Pentest-Prüfpunkt.

Verwandte Seiten: [Grundschutz](grundschutz.html) · [Compliance by Design](compliance-by-design.html) · [Schwachstellenmanagement](schwachstellenmanagement.html)
