title: Kryptografie
summary: Grundsätze des Kryptokonzepts – Ausrichtung an BSI TR-02102, zwei Krypto-Profile, PKI mit kurzen Laufzeiten, zweistufige Verschlüsselung ruhender Daten und ein Fahrplan zur Post-Quanten-Kryptografie.
group: konzept
order: 100
quelle: Konzept 102 (Kryptokonzept)
---

Das Kryptokonzept beschreibt den **produktseitigen Teil** eines Kryptokonzepts nach BSI IT-Grundschutz (Baustein CON.1): Verfahren, Voreinstellungen, Schlüssellebenszyklus und Nachweisfunktionen für alle Komponenten der Plattform. Organisatorische Teile – Profilwahl, Schlüsselzeremonie, Verwahrung von Wiederherstellungsanteilen – ergänzt der Betreiber. Kryptografie *innerhalb* von Mandanten-Workloads liegt in Mandantenverantwortung; die Plattform stellt dafür Schlüssel, Zertifikate und Zufall bereit. Wem welcher Schlüssel anvertraut wird, regelt das [Sicherheitsmodell](sicherheitsmodell.html).

## Grundsätze

1. **Keine eigenen Krypto-Primitive** – nur geprüfte Bibliotheken (rustls mit aws-lc-rs im Userland, Kernel-Kryptografie, TPM).
2. **BSI TR-02102 ist maßgeblich.** Abweichungen werden je Fundstelle begründet, dokumentiert und vom Betreiber bewertet.
3. **Sicherheitsniveau von mindestens 120 Bit**; für langlebige Vertraulichkeit AES-256.
4. **Quantensicherheit zuerst für Vertraulichkeit** (Schutz gegen „jetzt mitschneiden, später entschlüsseln“), danach für Signaturen.
5. **Kurze Lebensdauern statt Widerrufsinfrastruktur**, wo möglich.
6. **Zweckbindung:** ein Schlüssel, ein Zweck – durchgesetzt über Kontext-Labels bei Ableitung und Wrapping.
7. **Krypto-Agilität:** Algorithmen sind nie im Datenformat hart verdrahtet; jedes Chiffrat trägt Algorithmus, Schlüsselkennung und Version.
8. **Fail closed:** Ein Agent verweigert Verbindungen, wenn sein Krypto-Profil nicht erfüllbar ist – außer bei ausdrücklich freigegebenen Ausnahmen.
9. **Symmetrisch, wo immer möglich:** Schlüsselhierarchie, Backups und Archive nutzen ausschließlich AES-256 und SHA-2-basierte Verfahren und sind damit bereits heute quantenresistent.

## Normgrundlage

Grundlage ist die Technische Richtlinie **BSI TR-02102** in ihrer aktuellen Fassung. Für das Konzept besonders relevant:

- **TLS 1.3** ist das Zielprotokoll; TLS 1.2 ist nur noch übergangsweise zulässig.
- Rein klassische Schlüsseleinigung wird nur noch bis Ende 2031 empfohlen; danach nur **hybrid mit Post-Quanten-Verfahren** (ML-KEM).
- Rein klassische Signaturen sind bis Ende 2035 vorgesehen; als Post-Quanten-Signaturen kommen ML-DSA, SLH-DSA und hashbasierte Verfahren in Betracht.
- Für IPsec deckt die Richtlinie nur IKEv2 ab. Das als Underlay eingesetzte WireGuard ist dort nicht erfasst; die Plattform ergänzt es um eine Post-Quanten-Schicht. Abweichungen werden dokumentiert und vom Betreiber bewertet.

## Krypto-Profile

Die Plattform kennt zwei zentral konfigurierbare Profile. Das aktive Profil ist eine Plattform-Ressource, gilt auf allen Ebenen und wird von jedem Agenten durchgesetzt und als Ist-Zustand gemeldet. Regionen dürfen verschärfen, nie lockern.

| | `bsi-strict` (Standard) | `compatible` (z. B. Homelab) |
|---|---|---|
| Transport | TLS 1.3 ohne 0-RTT | zusätzlich TLS 1.2 am öffentlichen Eingang für Alt-Clients |
| Schlüsseleinigung | hybrid, bevorzugt `SecP256r1MLKEM768` | hybrid, bevorzugt `X25519MLKEM768` |
| Signaturen | ECDSA P-384 (CA) und P-256 (Endzertifikate) | zusätzlich Ed25519 |
| Symmetrisch | AES-256-GCM, AES-256-XTS | zusätzlich ChaCha20-Poly1305 für Geräte ohne AES-Beschleunigung |
| Underlay | WireGuard mit Pflicht-PQ-Schicht | PQ-Schicht standardmäßig an, abschaltbar mit Warnung |

**Hybride Post-Quanten-Schlüsseleinigung ist in beiden Profilen ab dem ersten Release Standard.** Beide Profile verbieten veraltete Verfahren wie TLS bis 1.1, kurze RSA-Schlüssel, SHA-1/MD5 für Sicherheitszwecke, CBC-Modi in TLS und 0-RTT. Das Profil `compatible` ist eine bewusste, im Compliance-Bericht sichtbare Entscheidung. Profilwechsel laufen als gestaffelter Rollout: zuerst neue Verfahren annehmen, dann alte abschalten.

Einzelne Knoten können eine **befristete, begründete und freigegebene Ausnahme** erhalten, etwa ein Gerät ohne AES-Beschleunigung. Solche Knoten werden automatisch von der Platzierung schutzbedürftiger Workloads ausgeschlossen und erscheinen im Compliance-Export.

## PKI

Die interne PKI ist hierarchisch: **Plattform-Root-CA → Regions-CA → Zellen-CA → Knoten- und Dienstzertifikate**. Daneben stehen eine eigene **Workload-CA** für Mandanten-Workloads und eine separate CA (öffentlich per ACME oder vom Betreiber) für öffentliche Endpunkte.

- **Getrennte Vertrauensdomänen:** Infrastruktur-mTLS vertraut nur Zellen- und Regions-CAs, nie der Workload-CA. Eine Mandanten-Workload kann sich so nie als Knoten ausweisen.
- **Kurze Laufzeiten:** Knotenzertifikate gelten Tage, Dienstzertifikate Stunden, Workload-Zertifikate Minuten. Erneuert wird ab der Hälfte der Laufzeit.
- **Widerruf:** Statt OCSP oder öffentlicher Sperrlisten genügen kurze Laufzeiten. Nur für Knoten gibt es zusätzlich eine replizierte, signierte und versionierte Sperrliste, die sofort wirkt und nicht zurückgespielt werden kann.
- **Root-Schlüssel:** Bei der Initialisierung wird der Root-Schlüssel in **k-aus-n-Wiederherstellungsanteile** (Shamir) zerlegt. Im Profil `bsi-strict` wird die Online-Kopie nach Ausstellung der Regions-CA gelöscht; der Root ist dann nur per Zeremonie im Vier-Augen-Prinzip rekonstruierbar.
- CA-Schlüssel liegen gewrappt in der Schlüsselverwaltung; signiert wird nur auf Steuerungsknoten.

Schlüssel werden bevorzugt im **TPM 2.0** gehalten. Geräte ohne TPM entsperren ihren Datenträger über eine **netzgebundene Schwellwert-Freigabe** durch die Zelle.

## Daten at rest und Schlüsselhierarchie

Ruhende Daten werden **zweistufig** verschlüsselt:

1. **Plattformschicht:** Jeder Knotendatenträger ist mit LUKS2 (AES-256-XTS) verschlüsselt – Schutz gegen Diebstahl und Geräterückgabe.
2. **Mandantenschicht:** Jedes Volume, jeder Bucket und jedes Backup hat einen eigenen Datenschlüssel (DEK). Blockspeicher wird auf dem Compute-Host verschlüsselt, sodass Speicherknoten nur Chiffrat sehen (siehe [Speicher](speicher.html)).

Die Schlüsselhierarchie lautet **Plattform-Root-Key → Regions-KEK → Mandanten-KEK → DEK**. Gewrappt wird mit AES-256-GCM; die zusätzlich authentisierten Daten binden jeden gewrappten Schlüssel an Objekt, Zweck, Mandant und KEK-Version, sodass er sich für nichts anderes entpacken lässt. Klartextschlüssel existieren nur im Arbeitsspeicher der Schlüsselverwaltung bzw. kurzzeitig beim berechtigten Host. Einen DEK erhält ein Host nur für Ressourcen, die nachweislich auf ihm platziert sind; Betreiberrollen erhalten nie Mandanten-DEKs. **Krypto-Löschung** durch Vernichten eines Schlüssels macht Daten einschließlich Backups unlesbar und wird mit einem signierten Löschnachweis belegt. Mandanteneigene Schlüssel aus externen KMS/HSM (BYOK/HYOK) folgen in einer späteren Phase.

## Krypto-Agilität und PQC-Fahrplan

Agilität ist eingebaut: Das Profil ist Konfiguration, alle eigenen Formate sind versioniert, Algorithmuswechsel laufen als Expand/Contract-Rollout, und Agenten melden die tatsächlich ausgehandelten Verfahren – abgeschaltet wird erst bei vollständiger Umstellung. Wo kein Standard für kombinierte Signaturen existiert, werden Doppelsignaturen eingesetzt, die beide gültig sein müssen. Jede Verwendung von Kryptografie ist in einem maschinenlesbaren **Krypto-Inventar (CycloneDX-CBOM)** erfasst und wird in der CI gegen das Profil geprüft.

| Zeitpunkt | Schritt |
|---|---|
| Erstes Release | Hybride Schlüsseleinigung an allen Endpunkten, PQ-Schicht im Underlay, Krypto-Inventar, Profile, AES-256 für ruhende Daten |
| Folgephase | ML-DSA-Doppelsignaturen für Updates, Audit und Löschnachweise; mandanteneigene Schlüssel |
| Nach Aufnahme in TR-02102 | ML-DSA in der internen PKI, zunächst parallel zur klassischen Kette |
| Bis Ende 2030 | Interne PKI vollständig post-quanten-fähig |
| Ende 2031 | Keine rein klassische Schlüsseleinigung mehr |
| Ende 2035 | Keine rein klassischen Signaturen mehr (soweit die Hardware-Boot-Ketten es zulassen) |

Inventar, Fahrplan, hybride Verfahren und jährliche Revision liefern zugleich die Grundlage für eine PQC-Strategie, wie sie aktuelle Cloud-Prüfkataloge erwarten (siehe [Compliance-Anforderungen](compliance-anforderungen.html)).
