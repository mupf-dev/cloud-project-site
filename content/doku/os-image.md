title: OS-Image (cpOS)
summary: Das unveränderliche Knoten-Betriebssystem – Debian-Basis mit mkosi, erofs und dm-verity, Unified Kernel Images, Secure und Measured Boot je Plattform, TPM-gebundene Verschlüsselung, A/B-Updates mit Health-Gate sowie Härtung und SBOM.
group: konzept
order: 80
quelle: Konzept 09 (OS-Konzept) und Beschreibung der OS-Image-Pipeline
---

## Überblick

Jeder Knoten der Plattform ist ein **Gerät mit einer Aufgabe**: Er führt den Agenten und die von ihm gesteuerten Rollenkomponenten sicher, aktualisierbar und ohne Handarbeit aus. Dafür bringt die Plattform ein eigenes, image-basiertes Betriebssystem mit – Arbeitsname **cpOS**. Daraus folgen fünf Leitlinien:

1. **Unveränderlich und überprüfbar:** Alles Ausführbare stammt aus einem signierten, integritätsgeschützten Image.
2. **Atomar aktualisierbar mit Rückfall:** Ein Update ist ein Slot-Wechsel, nie ein Paket-für-Paket-Umbau.
3. **Zustand klar getrennt:** Es gibt genau eine verschlüsselte Zustandspartition; alles andere ist reproduzierbar.
4. **API statt Shell:** Konfiguration, Diagnose und Wartung laufen über die Plattform-API, nicht per SSH.
5. **Passende Größe:** klein genug für einen Raspberry Pi 4 mit 2 GB (und Zeugen-Knoten auf noch kleineren Geräten), groß genug für Rechenzentrums-Server.

### Kernentscheidungen

| Thema | Entscheidung |
|---|---|
| Basis | eigenes Image, gebaut mit **mkosi aus Debian-13-Paketen**; Bausteine aus systemd (UKI, systemd-boot, repart, dm-verity, sysupdate, sysext, cryptenroll) |
| Raspberry Pi | **nativer Pi-Bootloader ohne UEFI**, A/B über den eingebauten „tryboot“-Mechanismus; Kernel und Firmware aus dem Raspberry-Pi-Archiv |
| Dateisysteme | nur `/usr` im Image (erofs mit dm-verity, A/B-Slots); `/` flüchtig, `/etc` bei jedem Start neu erzeugt; Persistenz nur in einer verschlüsselten Zustandspartition; **kein Paketmanager** |
| Inhalte | ein Basis-Image je Architektur (amd64, arm64-UEFI, arm64-Pi); rollenspezifische Laufzeiten als **signierte System-Erweiterungen**, im Gleichschritt versioniert |
| Betriebsarten | Discovery, Installer, Ersteinrichtung, Betrieb (lokal oder diskless) und Rettung entstehen aus denselben Bauquellen |
| Updates | inaktiven Slot schreiben, neu starten, **Health-Gate**; bei Fehlschlag automatischer Rückfall (Bootzähler bzw. „tryboot“ plus Watchdog) |
| Rollout | rollend über die Steuerungsebene; höchstens ein Steuerungsmitglied je Zelle gleichzeitig, Leader zuletzt; automatische Updates ab Werk an |
| Härtung | kein Login, keine Passwörter, kein SSH ab Werk; Kernel-Lockdown, Modulsignatur-Pflicht, Firewall default-deny, Sandboxing je Dienst |
| Secure / Measured Boot | eigene Schlüssel je Installation, TPM-2.0-gebundene Plattenverschlüsselung über **signierte PCR-Richtlinien** |
| Lieferkette | je Artefakt SBOM, Quellcode-Bündel und Provenienz; reproduzierbarer Bau |

## Basis-Auswahl

Bewertet wurden native Pi-Unterstützung, image-basierte Mechanik, ein etabliertes Sicherheitsteam mit langem Unterstützungszeitraum, Reproduzierbarkeit, Pflegeaufwand, Größe und Lizenzen. Verworfen wurden Fedora/CentOS Stream (kurzer Zyklus, Pi 5 nicht offiziell), Buildroot (kein Sicherheitsteam), ein Talos-artiges Eigen-OS (systemd-Funktionen nachbauen), Flatcar und Fedora CoreOS (Pi nur über UEFI), NixOS (Lernkurve, Größe) und Ubuntu Core (Bindung an einen Hersteller-Store). Yocto bleibt **Rückfalloption** für sehr kleine Profile. Ein UEFI-Pfad für den Pi wurde verworfen, weil die Community-Firmware kaum noch gepflegt wird.

Nur Debian mit mkosi verbindet native Pi-Unterstützung, die systemd-Image-Bausteine und ein etabliertes Sicherheitsteam, **ohne dass das Projekt eine Distribution pflegen muss** – gepflegt wird ein *Rezept*, keine Pakete. Paketstände werden über Zeitstempel-Snapshots festgenagelt, die Lizenzlage ist klar (Debian `main` plus Firmware mit Weitergabelizenz). Der Wechsel auf die nächste Debian-Version ist als regulärer Minor-Release der Plattform geplant.

Für amd64 und arm64-UEFI wird der Debian-Kernel verwendet (signierte Module, Lockdown, Sicherheitsupdates durch das Kernel-Team), für den Pi der Raspberry-Pi-Kernel in einer LTS-Linie. Als C-Bibliothek dient glibc, gegen die die Rust-Komponenten gebaut werden.

## Aufbau des Images

### Schichten

| Schicht | Inhalt | Eigenschaft |
|---|---|---|
| Boot | UEFI: systemd-boot und Unified Kernel Images (UKI) für Slot A und B; Pi: Boot-Slots A/B mit Kernel, Device Trees und Initramfs | signiert |
| `/usr` | Basis (systemd, Agent, privilegierter Hilfsdienst, Kernel-Module, Netz- und Kryptowerkzeuge) plus Erweiterungen je Rolle | unveränderlich, erofs + dm-verity, Slot A/B |
| flüchtig | `/`, `/etc`, `/run` | tmpfs, bei jedem Start neu erzeugt |
| Zustand | Raft-Daten, Knotenidentität, Audit-Puffer, Journal, Erweiterungs-Cache, Container-Daten | dauerhaft, LUKS2-verschlüsselt |
| Daten | Datenträger der Speicherrollen | eigene Verschlüsselung je Volume (siehe [Speicher](speicher.html)) |

### Unveränderliches `/usr` mit dm-verity

`/usr` ist ein komprimiertes, reproduzierbar gebautes **erofs**-Dateisystem, gefolgt von einer Verity-Partition (Hash-Baum) und einer Signatur-Partition über den Root-Hash, angelegt nach der *Discoverable Partitions Specification*. Der **Root-Hash** steht in der Kernel-Befehlszeile der signierten UKI bzw. des Pi-Boot-Images. Im erhöhten Schutzprofil prüft der Kernel zusätzlich die Verity-Signatur gegen die Schlüssel der Installation, sodass selbst ein manipulierter Bootpfad kein fremdes `/usr` einhängen kann. Jeder Hash-Fehler führt zum Neustart; ein korrupter Slot wird so vom Bootzähler erkannt und verworfen.

Weil `/` ein tmpfs ist und `/etc` bei jedem Start aus signierten Vorgaben entsteht, gibt es **keinen Ort, an dem sich unbemerkt Konfiguration ansammeln kann** – das OS ist driftfrei.

### Partitionslayout

**UEFI (amd64, arm64) – GPT, beim Installieren erzeugt:**

| Partition | Größe (Richtwert) | Inhalt |
|---|---|---|
| EFI-Systempartition | 1 GiB | systemd-boot, UKIs für Slot A und B, Rettungs-UKI |
| `usr` A + Verity + Signatur | 2,5 GiB + Hash-Baum | Basis-`/usr` Version N |
| `usr` B + Verity + Signatur | wie A | Version N+1 bzw. N−1, anfangs leer |
| Zustand (LUKS2 → ext4) | 16–64 GiB | dauerhafter Knotenzustand |
| Daten (optional) | Rest | Reserve für Speicherrollen auf Ein-Platten-Knoten |

**Raspberry Pi 4/5:** zusätzlich eine kleine Steuerpartition mit der A/B-Auswahl und einer Rettungskonfiguration sowie zwei Boot-Slots mit je einem signierbaren Boot-Image (auf 180 MB begrenzt, Ziel ≤ 120 MB), danach dieselben `usr`-Slots, Zustands- und Datenpartition wie bei UEFI. Kleinstgeräte für Zeugen-Knoten nutzen dasselbe Layout ohne Datenpartition.

### Persistenz und Konfiguration

Auf der Zustandspartition liegen Knotenidentität und Zertifikat (wo kein TPM vorhanden ist), die Raft-Datenbank (nur auf fsync-fähigem Speicher für Steuerungsknoten), lokaler Knotenzustand und Audit-Puffer, ein inhaltsadressierter Artefakt-Cache, aktive Erweiterungen, Container-Daten, das persistente Journal und die zuletzt bekannte gültige Uhrzeit.

Konfiguration entsteht in vier Ebenen, **ohne Paketmanager**:

| Ebene | Quelle |
|---|---|
| Image-Vorgaben | signiertes `/usr`: Units, Sysctl-Profil, Firewall-Grundregeln, AppArmor-Profile, Standard-Netz |
| Boot-Hinweise | Kernel-Befehlszeile – nur Hinweise, keine Vertrauensgrundlage |
| Knoten-Sollzustand | Steuerungsebene: Rollen, Netz, Betriebsart, Update-Kanal – der Agent rendert daraus Laufzeitkonfiguration |
| Geheimnisse | Adoptionspaket und KMS; TPM-versiegelt bzw. verschlüsselt auf der Zustandspartition, **nie im Image** |

Menschen ändern `/etc` nicht dauerhaft; jede Abweichung vom Sollzustand erkennt der Agent beim periodischen Abgleich und heilt sie. Software kommt ausschließlich über Image-Updates oder signierte Erweiterungen.

### Dienste

Der Agent (`cp-agent`) läuft als eigener Nutzer mit minimalen Rechten und strengem Sandboxing. Privilegierte Operationen (Netzkonfiguration, Partitionen, Erweiterungen, Updates, Löschen) erledigt ein getrennter Hilfsdienst (`cp-privd`) mit **festem, auditiertem Befehlsset**, der nur für den Agenten erreichbar ist. Der Boot-Dienst (`cp-bootd`) läuft nur auf Boot-Knoten als eigener Sandbox-Prozess ohne Zugriff auf Knotenschlüssel oder KMS. Eine Konsolenanzeige zeigt Setup-Token, Bestätigungscode und Zustand – ohne Login. Rollendienste laufen mit eigenen Nutzern, cgroup-Limits und Sandboxing.

### Basis-Image und Erweiterungen

Das Basis-Image enthält Kernel und signierte Module, nur benötigte Firmware, systemd, die Plattformdienste, nftables und WireGuard, Krypto- und Speicherwerkzeuge (cryptsetup, TPM-Unterstützung, Löschwerkzeuge), chrony mit NTS und auf dem Pi die EEPROM-Werkzeuge. Größenziel: `/usr` unkomprimiert höchstens etwa 600 MB.

Rollenspezifische Laufzeiten kommen als **System-Erweiterungen (sysext)**:

| Erweiterung | Inhalt | Rollen |
|---|---|---|
| compute | Cloud Hypervisor, virtiofsd, containerd, eine Rust-OCI-Laufzeit, Kata Containers | VM- und Container-Knoten |
| k8s | k3s | Kubernetes |
| garage | Garage-Objektspeicher (separater Prozess) | Objektspeicher |
| sdn | Netzkomponenten | Overlay, Gateways |
| observability | Metrik- und Log-Speicher | Beobachtbarkeit |
| debug | Diagnosewerkzeuge, SSH-Server für Tier-0-Zugang | nur in Diagnosesitzungen |

Warum Erweiterungen statt Monolith: Kleine Knoten tragen keine Hunderte Megabyte an Laufzeiten, die sie nie nutzen – weniger Code bedeutet weniger Angriffsfläche. Rollenwechsel gelingen ohne Neuinstallation. Erweiterungen sind selbst Disk-Images mit dm-verity und Signatur und fest an die Version der Basis gebunden. Regeln: Ein Plattform-Release besteht aus Basis, allen Erweiterungen und den Discovery-Artefakten mit **einer** Versionsnummer und einem Manifest; Erweiterungen werden beim Start aktiviert, zur Laufzeit nur beim Hinzufügen einer Rolle und entfernt erst nach dem Leerräumen des Knotens. Fremdkomponenten bleiben eigene Prozesse (siehe [Rust-Stack](rust-stack.html), [Lizenz-Governance](lizenz-governance.html)).

## Betriebsarten

| Betriebsart | Artefakt | Schreibt auf Platte? |
|---|---|---|
| Discovery | kleines, signiertes Discovery-UKI bzw. Pi-Boot-Image mit Agent im eingeschränkten Modus | nein |
| Installer | wie Discovery, zusätzlich Partitionierung und Löschwerkzeuge | ja, nach Adoption |
| Ersteinrichtung | Universal-Stick-Image mit Discovery-UKI und vollständigem `/usr`-Slot | erst nach der Initialisierung |
| Betrieb lokal | UKI bzw. Boot-Slot A/B | ja (Zustandspartition) |
| Betrieb diskless | UKI und `/usr`-Image über HTTP | nein (optional Scratch-Platte) |
| Rettung | Rettungs-UKI bzw. Rettungseintrag | nein |

Alle Artefakte entstehen aus **denselben Paketständen**. Wie die Betriebsarten im Boot-Ablauf eingesetzt werden, beschreibt [Boot und Adoption](boot-adoption.html).

**Lokale Installation:** Nach der Adoption prüft der Installer Manifest-Signatur und Mindestversion, legt das GPT-Layout an, richtet die verschlüsselte Zustandspartition mit TPM-, netzgebundener oder Pi-Geräteschlüssel-Bindung ein, schreibt Slot A, markiert Slot B als leer und startet in den Betrieb. Dort erzeugt der Knoten seinen Langzeitschlüssel, erhält sein Zertifikat und bestätigt den Boot erst nach dem Health-Gate. Der Ersteinrichtungs-Knoten kopiert seinen laufenden Slot blockweise auf die Zielplatte – ganz ohne Download. Vorhandene Daten sind geschützt: Ohne weitere Angabe wird nur eine **leere** Platte beschrieben; eine vorhandene cpOS-Installation nur nach Bestätigung, fremde Daten nur bei ausdrücklich gewählter Platte mit eigener Bestätigung und Warnung im Dry-Run.

**Diskless:** Das Initramfs lädt das `/usr`-Image über HTTP in den RAM, prüft es per dm-verity gegen den Root-Hash aus der signierten Befehlszeile und hängt es ein. Ein Update ist schlicht der nächste Netzboot, ein Rückfall die Auslieferung der vorigen Version. Diskless setzt ausreichend RAM voraus; dauerhafte Identität gibt es nur mit TPM bzw. Pi-Geräteschlüssel.

## Updates

### Versionen, Kanäle, Manifest

Versioniert wird das **gesamte Plattform-Release** (Agent, Basis, Erweiterungen, Discovery) als `MAJOR.MINOR.PATCH`. PATCH enthält **nur Sicherheits- und Fehlerbehebungen**, MINOR Funktionen und Basiswechsel, MAJOR bewusst inkompatible Änderungen mit Migrationspfad. Es gibt die Kanäle `stable` (Standard), `candidate` (Vorabtest) und `edge` (nur Entwicklung) sowie Release-Linien mit Patch-Pflege.

Ein **signiertes Release-Manifest** beschreibt Version, Kanal, eine Sicherheitsepoche (Downgrade unter die Epoche ist verboten), die Mindestversion für einen direkten Update-Pfad, alle Artefakte mit Hash und Verity-Root-Hash, Verweise auf SBOM, Quellbündel und Provenienz sowie ein Ablaufdatum gegen das Einfrieren auf einem alten Manifest. Details unter [Release-Bündel](release-buendel.html) und [Release-Signatur](release-signatur.html).

### Ablauf auf dem Knoten

1. Die Steuerungsebene gibt eine Zielversion für den Knoten frei.
2. Der Agent holt Manifest und Artefakte (inhaltsadressiert, auch von anderen Knoten) und prüft Signatur, Kanal, Sicherheitsepoche, Mindestversion und Ablauf.
3. Der privilegierte Hilfsdienst schreibt über systemd-sysupdate den **inaktiven Slot**, die neue UKI mit Bootzähler bzw. den Pi-Slot B und die benötigten Erweiterungen – im laufenden Betrieb und I/O-gedrosselt.
4. Erst jetzt wird der Knoten leergeräumt (Workloads migrieren, bei Bedarf Leader-Wechsel) und neu gestartet.
5. Der neue Slot startet; das **Health-Gate** entscheidet.
6. Grün: Der Boot wird bestätigt („bless“). Rot oder Hänger: Watchdog bzw. Bootzähler führen zum Neustart in den **alten Slot**, der Knoten meldet „zurückgerollt“ samt Grund.

Ein Betreiber-Rollback auf eine Version derselben Sicherheitsepoche ist erlaubt, sonst nur mit privilegierter Freigabe. Ein hardwaregestützter Rollback-Schutz über TPM-Zähler ist für eine spätere Phase vorgesehen; Pis ohne TPM haben diesen Schutz nicht – eine dokumentierte Grenze.

### Health-Gate

Vor dem Abschluss des Bootvorgangs prüft das Health-Gate innerhalb eines Zeitlimits (Standard 10 Minuten):

1. `/usr` per dm-verity eingehängt, alle Erweiterungen aktiv, Zustandspartition entsperrt.
2. Agent läuft, Watchdog wird bedient, Zertifikat gültig.
3. Underlay-Verbindung zu mindestens einem Seed, Gossip-Beitritt erfolgt.
4. Alle Rollendienste aktiv.
5. Für Steuerungsknoten: Raft-Log zum Leader aufgeholt, Mitgliedschaft wie vorher.
6. Für Boot-Knoten: Boot-Projektion geladen, Ports gebunden.

**UEFI** nutzt die Bootzähler von systemd-boot (drei Versuche). Der **Pi** startet den neuen Slot einmalig per „tryboot“; schlägt das Gate fehl oder hängt der Knoten, löst der Hardware-Watchdog einen Neustart aus, und die Firmware startet automatisch den alten Slot. Erst bei grünem Gate wird die Slot-Auswahl dauerhaft umgeschrieben. Ist selbst der Standard-Slot unbrauchbar, fällt der Pi auf eine Rettungskonfiguration bzw. den Netzboot zurück.

### Rollende Updates

Den Rollout steuert ein Update-Controller in der [Steuerungsebene](steuerungsebene.html); das OS liefert nur die knotenlokale Mechanik. Eine Update-Richtlinie legt Kanal, Zielversion, Wartungsfenster und Stufen fest (Kanarienvogel mit Beobachtungszeit, Arbeitsknoten mit begrenzter gleichzeitiger Nichtverfügbarkeit, Boot-Knoten einzeln, Steuerungsknoten einzeln mit Leader zuletzt). Sicherheitspatches mit hohem Schweregrad dürfen außerhalb des Wartungsfensters eingespielt werden.

Regeln: Das **Quorum wird nie gefährdet** – ein Steuerungsmitglied wird nur aktualisiert, wenn alle übrigen gesund und aufgeholt sind. Bei nur einem Steuerungsmitglied ist ein Update mit kurzer, angekündigter Schreibpause erlaubt (mit Warnung und Bestätigung). In einer Zelle laufen höchstens zwei benachbarte Versionen; neue Datenformate folgen erst nach vollständigem Rollout. Es wird **Zelle für Zelle** aktualisiert, ein Fehlschlag pausiert den Rollout automatisch. Vor dem Neustart werden VMs live migriert, Speicherrollen warten auf gesunde Replikation. Offline-Umgebungen importieren Releases mit gleicher Prüfung. Details unter [Rollout](rollout.html).

Firmware (Pi-EEPROM, UEFI) ist nicht Teil der A/B-Slots; Pi-EEPROM-Updates kommen als eigenes signiertes Artefakt und werden einzeln per Richtlinie angewendet.

## Secure Boot und Measured Boot

| Plattform | Verifizierte Kette | Plattenschlüssel | Vertrauensstufe |
|---|---|---|---|
| UEFI mit **eigenen Schlüsseln der Installation** | Firmware → systemd-boot → signierte UKI → dm-verity-`/usr` → signierte Erweiterungen; Messung in TPM-PCRs | TPM 2.0 mit signierter PCR-Richtlinie | mit TPM hoch (attestiert erst ab späterer Phase), ohne TPM mittel |
| UEFI nur mit Herstellerschlüsseln | über einen signierten Shim – nur Rückfall, im erhöhten Profil unzulässig | wie oben | mit TPM hoch, ohne TPM niedrig |
| UEFI ohne Secure Boot | keine Prüfung durch die Firmware; dm-verity schützt `/usr` zur Laufzeit | TPM oder netzgebundene Entsperrung | mit TPM hoch, ohne niedrig |
| Pi mit Pi-Secure-Boot (irreversibel) | Boot-ROM → signiertes Boot-Image → dm-verity; keine TPM-Messung | Geräteschlüssel im OTP, optional netzgebunden | mittel, nie attestiert |
| Pi ohne Pi-Secure-Boot | lokal keine Prüfung; signiertes HTTP-Netzboot möglich | netzgebundene Entsperrung | niedrig |

**Eigene Schlüssel je Installation:** Bei der Ersteinrichtung erzeugt jede Installation ihre eigenen Secure-Boot-Schlüssel (Platform Key, KEK, db) und eine Boot-CA. Sie prüft die Signatur des Projekt-Releases und **signiert die Boot-Komponenten neu** – UKI, Bootloader, iPXE und die Verity-Signaturen. Kein fremder Shim, keine MOK-Verwaltung.

**Signierte PCR-Richtlinie:** Die Zustandspartition ist nicht an feste Messwerte gebunden, sondern an einen **Schlüssel**: Jede vom Projekt signierte UKI entsperrt die Platte in genau der vorgesehenen Bootphase – auch nach einem Update, ohne Neuversiegelung –, eine fremde oder unsignierte nicht. Nach dieser Phase gibt das TPM den Schlüssel nicht mehr heraus. Ohne TPM wird die Platte netzgebunden über die Zelle entsperrt. Referenz-PCR-Werte werden je Release im Manifest mitgeliefert und dienen der Attestierung beim Beitritt. Schlüsselverwaltung und Vertrauensstufen beschreiben [Kryptografie](kryptografie.html) und [Sicherheitsmodell](sicherheitsmodell.html).

## Härtung

### Orientierung

Das Härtungsprofil ist auf den BSI-Grundschutz (Server unter Linux bzw. die entsprechenden Grundschutz++-Anforderungen) und den CIS-Benchmark für Debian gemappt (siehe [Grundschutz](grundschutz.html)). Viele Kontrollen entfallen strukturell – es gibt keinen Paketmanager, keine Logins, kein SSH und keinen cron. Die Einhaltung wird je Release automatisiert geprüft und ist je Knoten abfragbar.

### Kernel

| Bereich | Maßnahmen |
|---|---|
| Integrität | Lockdown, Pflicht zur Modulsignatur, signierte Verity-Root-Hashes, keine Module aus beschreibbaren Pfaden |
| Speicher | Initialisierung bei Allokation, keine Slab-Zusammenlegung, zufällige Seitenreihenfolge, zufälliger Kernel-Stack-Offset |
| Angriffsfläche | debugfs aus, striktes IOMMU, kein vsyscall und keine 32-Bit-Emulation auf amd64, CPU-Mitigations nie abgeschaltet |
| LSM | Landlock, Lockdown, Yama, AppArmor, BPF; Integrity Policy Enforcement als Kandidat |
| Erhöhtes Profil | eigene UKI mit Lockdown „confidentiality“, Speicherlöschen bei Freigabe, Panik bei Oops |

Ein **Sysctl-Profil** beschränkt unter anderem unprivilegiertes eBPF, kexec, ptrace, SysRq und io_uring, deaktiviert Core-Dumps und härtet den Netzstack; Abweichungen, die Overlay und WireGuard erfordern, sind begründet. Ein zur Laufzeit unveränderlicher **Audit-Regelsatz** nach CIS- und ANSSI-Empfehlungen erfasst sicherheitsrelevante Systemereignisse.

### Nutzerraum

- **Keine Logins, root gesperrt, keine Passwörter, kein SSH-Zugang ab Werk.** SUID/SGID-Bits sind entfernt.
- Firewall **default-deny** eingehend: nur Boot-Dienste (nur auf Boot-Knoten), API/Portal/MCP und WireGuard; Steuerung und Gossip ausschließlich über das Underlay (siehe [Netzwerk](netzwerk.html)).
- Jeder Dienst mit eigenem Nutzer, schreibgeschütztem System, minimalen Capabilities, Systemaufruf- und Adressfamilien-Filtern und einem AppArmor-Profil im Modus „enforce“; das Härtungsniveau je Dienst wird in der CI gemessen.
- Beschreibbare Bereiche sind `nosuid`, `nodev` und weitgehend `noexec`; der Host führt im Regelfall nur Code aus signiertem `/usr` und signierten Erweiterungen aus.
- USB-Massenspeicher ist im Betrieb gesperrt.
- Kein Echtzeit-Virenscanner auf dem Host (begründet durch dm-verity und fehlende Schreibpfade für Binärdateien) und **keine Telemetrie** an das Projekt.

### Diagnosezugriff und Rettung

| Weg | Wann | Absicherung |
|---|---|---|
| **Diagnosesitzung** | Normalfall der Fehlersuche: festes Befehlsset (Journal, Dienststatus, Netz- und Plattenzustand), optional eine Shell | befristet, begründet, privilegiert, optional Vier-Augen; aufgezeichnet, auditiert und am Knoten sichtbar markiert |
| **Tier-0-SSH** | Fehlersuche durch einen eng begrenzten Personenkreis | nur kurzlebige SSH-Zertifikate (höchstens 60 Minuten) nach Passkey-Anmeldung, nur über Underlay/Management; eigenes Recht, ab Werk niemandem zugewiesen |
| **Lokaler Rettungszugang** | Knoten bootet nicht oder Steuerungsebene unerreichbar | Rettungseintrag an der Konsole, freigeschaltet mit dem Wiederherstellungsschlüssel der Plattform; anschließend Re-Zertifizierung mit Freigabe |

Keiner dieser Wege gewährt Zugriff auf Mandanteninhalte über die API; dass eine Root-Shell technisch mehr kann, wird Mandanten transparent gemacht (siehe [Identität und Rechte](identitaet.html)).

**Weitere Basisdienste:** chrony mit NTS (Geräte ohne Echtzeituhr starten mit einer Zeit-Untergrenze), Hardware-Zufallsquellen als Zusatz zum Kernel-CSPRNG, ein persistentes Journal mit Weiterleitung über den Agenten und sichere Löschverfahren (NVMe Sanitize, Krypto-Löschung, ATA Secure Erase) mit signiertem Nachweis.

## SBOM, Quellcode, Lizenzen

Für das Basis-`/usr` jeder Architektur, jede Erweiterung, jedes Discovery- und Boot-Artefakt sowie iPXE entsteht eine **eigene SBOM** (CycloneDX) mit den Mindestfeldern nach BSI TR-03183-2, die in der CI geprüft werden. Die SBOM liegt im Image und im Release-Manifest; der Agent stellt sie je Knoten bereit und gleicht sie gegen Sicherheitsmeldungen ab.

GPL-Pflichten werden erfüllt, indem die **Quellen zusammen mit den Binärdateien** veröffentlicht und mindestens so lange aufbewahrt werden wie das Image. Proprietäre Firmware (Pi, Netzwerkkarten) wird mit ihrer Weitergabelizenz ausgeliefert und in SBOM und NOTICE aufgeführt. Jeder Bau durchläuft einen Lizenz-Scan.

## Bau-Pipeline (abstrakt)

1. **Fixierte Eingänge:** signierte Commits mit Rezept und Agent-Quellen, ein fester Debian-Snapshot-Zeitstempel, ein eigener Spiegel des Pi-Archivs und eine gepinnte mkosi-Version.
2. **Bau** in einer isolierten Umgebung: Rust-Komponenten werden für amd64 und arm64 cross-kompiliert, mkosi baut je Profil und Architektur `/usr`, Erweiterungen, Discovery-, Pi- und Stick-Images; dazu erofs und dm-verity.
3. **Signatur** in einem getrennten Signierdienst.
4. **Prüfung:** Zweitbau auf einer anderen Instanz mit Hash-Vergleich der unsignierten Artefakte, virtuelle Testmatrix mit Secure Boot und Software-TPM (Boot jeder Betriebsart, Update N→N+1, absichtlich rotes Health-Gate, korrupter Slot, TPM-Entsperrung nach Update, Rollout-Simulation ohne Quorumverlust), Tests auf echter Pi- und x86-Hardware sowie SBOM-, Schwachstellen-, Lizenz- und Härtungsprüfung.
5. **Veröffentlichung** von Manifest, Artefakten, SBOM, Quellbündel und Provenienz.

**Reproduzierbarkeit** entsteht durch feste Paketstände, feste Zeitstempel, Partitions-UUIDs und Verity-Salt, reproduzierbare Rust-Builds mit festgelegter Toolchain sowie SLSA-Provenienz je Artefakt (Ziel SLSA Level 3). Im Betrieb werden die SBOMs aller gepflegten Release-Linien täglich gegen Sicherheitsmeldungen abgeglichen; Treffer mit hohem Schweregrad führen automatisch zu einem PATCH-Bau, der über `candidate` nach `stable` wandert (siehe [Schwachstellenmanagement](schwachstellenmanagement.html)).
