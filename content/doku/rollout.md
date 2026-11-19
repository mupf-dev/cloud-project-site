title: Rollout-Controller
summary: Wie Plattform-Updates rollend und quorumsicher auf die Knoten kommen – Release-Pläne, Reihenfolge und Gates, Health-Gate am Knoten, Pause und Rückfall.
group: konzept
order: 82
quelle: Rollout-Controller
---

## Überblick

Ein Plattform-Update ersetzt auf jedem Knoten das **ganze Plattform-Release** – Agent, OS-Basis, Erweiterungen –
per **A/B-Slotwechsel** (siehe [OS-Image](os-image.html)). Der Weg dorthin hat drei Teile:

1. **Import:** Das signierte Release gelangt per Import in die Region und wird auf mindestens zwei Halter
   verteilt (siehe [Release-Bündel](release-buendel.html)).
2. **Rollout-Controller:** Er entscheidet, **welcher Knoten wann** aktualisiert wird – rollend, quorumsicher, mit
   Pause bei Fehlern.
3. **Knoten-Seite:** Agent und privilegierter Hilfsdienst laden, prüfen und schreiben den inaktiven Slot, starten neu
   und bestätigen den neuen Stand erst nach einem grünen Health-Gate.

Die Aufgaben sind klar getrennt: Das OS liefert die knotenlokale Mechanik, der Controller die Steuerung. Der
Controller schreibt nur die Zielversion, den Wartungszustand und eine Rollout-Markierung am Knotenobjekt; der Agent
schreibt nur den OS-Status seines eigenen Knotens.

## Der Controller

Der Rollout-Controller läuft im Agenten auf dem aktuellen **Raft-Leader** der Steuerungsebene (siehe
[Steuerungsebene](steuerungsebene.html)). Er ist **pegelgesteuert**: Jeder Durchlauf leitet alles aus dem
beobachteten Zustand ab; im Status stehen nur Beginn und Zeitlimit des aktuellen Schritts. Ein Wechsel des Leaders
unterbricht den Rollout deshalb nicht – der neue Leader setzt ihn aus demselben Zustand fort.

Die Entscheidungslogik ist eine reine, deterministische Funktion ohne Uhr, Netz oder Speicher. Dadurch lässt sie sich
in einer Simulation vollständig prüfen: Modellknoten mit Neustarts, Ausfallzeiten und Leader-Wechseln; gemessen
werden Schreibverfügbarkeit, gleichzeitig ausgefallene Voter und die Neustart-Reihenfolge.

**Gesundheit misst der Leader selbst** – anhand der Antworten auf die Replikation und des Abstands im Replikationslog,
nie anhand einer Selbstauskunft des Knotens.

## Release-Plan

Bevor eine Zielversion gesetzt wird, lässt sich ein **Plan** abrufen (Probelauf über die API-Aktion
`region:planUpdate`). Derselbe Plan wird beim tatsächlichen Setzen der Zielversion erneut geprüft. Er enthält:

- die **Reihenfolge** der Knoten,
- ob eine **Schreibpause** nötig ist (kleiner Cluster) und wie lange sie voraussichtlich dauert – geschätzt aus der
  gemessenen Neustartdauer,
- die **Hindernisse**, die einen Rollout verhindern.

| Hindernis | Bedeutung |
|---|---|
| Release nicht verfügbar | noch im Import, fehlgeschlagen oder zu wenige Halter |
| Versionsabstand | in einer Zelle wären mehr als zwei Versionen gleichzeitig im Einsatz |
| Mindestversion | die niedrigste laufende Version liegt unter der `minVersion` des Release – kein direkter Update-Pfad |

Eine **niedrigere Sicherheitsepoche** ist kein Hindernis im Plan, verlangt aber eine privilegierte Freigabe. Wie
jede Plattformfunktion steht die Steuerung über API, Kommandozeile, MCP und Portal zur Verfügung (siehe
[API-first](api-first.html)).

## Reihenfolge und Gates

### Ein Knoten nach dem anderen

Es ist immer **genau ein Knoten in Arbeit**. Ein Knoten gilt als in Arbeit, solange seine Zielversion von der
laufenden abweicht oder die Rollout-Markierung gesetzt ist. Erst danach wird der nächste freigegeben. Höchstens ein
Knoten ist gleichzeitig im Wartungszustand.

### Reihenfolge innerhalb der Region

Der Rollout geht **Zelle für Zelle** vor, Regionen nacheinander. Innerhalb einer Zelle gilt:

1. Arbeitsknoten und Learner,
2. der Zeuge,
3. Follower-Voter einzeln,
4. **der Leader zuletzt** – vorher übergibt er die Führung an einen gesunden, aufgeholten Voter.

### Quorumschutz

Ein Voter (und der Zeuge) wird nur aktualisiert, wenn **alle übrigen Daten-Voter gesund und aufgeholt** sind – das
Quorum ist also auch ohne ihn stabil. Für kleine Cluster gilt:

- **ein einziger Voter:** Das Update bedeutet eine kurze Schreibsperre; es ist nur mit Warnung und ausdrücklicher
  Bestätigung erlaubt.
- **zwei Daten-Voter mit Zeuge:** ein Daten-Voter nach dem anderen, nur wenn der Zeuge erreichbar ist.

### Geplanter Neustart ist kein Ausfall

Vor dem Neustart setzt der Controller den Knoten in den **Wartungszustand** (Drain): Workloads werden migriert, wo
möglich live, sonst gemäß Mandanten-Richtlinie neu gestartet; Speicherrollen warten auf einen gesunden
Replikationszustand (siehe [Speicher](speicher.html)). Knoten in Wartung zählen nicht in die
**Massenausfall-Bremse** der Steuerungsebene – ein geplanter Neustart soll keine Notfallreaktion auslösen. Leases und
Fencing bleiben unverändert wirksam.

### Versionsabstand und Feature-Gates

In einer Zelle laufen höchstens zwei Versionen gleichzeitig (N und N−1). Neue Formate für die replizierte Datenbank
oder den Speicher dürfen erst geschrieben werden, wenn **alle** Knoten sie lesen können – sonst könnte ein Knoten mit
Vorgängerversion das Log nicht mehr anwenden. Dafür gibt es **Feature-Gates**:

- Jedes Gate nennt die Mindestversion, ab der das Format gelesen werden kann.
- Eingeschaltet wird es erst, wenn der Rollout **vollständig** ist und die niedrigste laufende Version diese
  Mindestversion erreicht.
- Ein eingeschaltetes Gate bleibt eingeschaltet. Danach ist ein Zurück auf die Vorgängerversion nicht mehr möglich;
  ein Rückfall ist nur noch innerhalb der Version möglich.

## Ablauf am Knoten

Der Knoten folgt einem festen Vertrag, den er aus seiner Zielversion und seinem Zustand ableitet:

| Knoten sieht | Knoten tut | meldet |
|---|---|---|
| Zielversion = laufende Version | nichts, offene Phase beenden | `Running` |
| neue Zielversion W | Release von den Haltern laden, prüfen, inaktiven Slot schreiben – im laufenden Betrieb, gedrosselt | `Staging` → `Staged` bzw. `Failed` mit Grund |
| `Staged`, Wartung und Rollout-Freigabe für W | Neustart in den neuen Slot | vorher `Rebooting` |
| nach dem Start läuft W, Health-Gate grün | neuen Slot bestätigen (*bless*) | `Running` (W), vorherige Version vermerkt |
| nach dem Start läuft die alte Version | – | `RolledBack` mit Grund aus dem Journal |
| `RolledBack` oder `Failed` für W | **kein** neuer Versuch | unverändert |

Download, Prüfung und Slot-Schreiben laufen ohne Unterbrechung im Betrieb; beeinträchtigt ist der Knoten erst ab dem
Drain.

### Prüfung und Schreiben

Der Agent legt das Release in einem Staging-Bereich ab und beauftragt den privilegierten Hilfsdienst über ein
festes, kleines Nachrichtenformat. Der Agent nennt dabei nur **Version** und **Prüfzeitpunkt**; Pfade, Dateinamen,
Partitionen und Befehle legt der Hilfsdienst selbst fest.

Der Hilfsdienst **vertraut dem Agenten nicht**: Er prüft die Signaturkette erneut gegen den Root im Image, prüft das
Manifest mit den Release-Regeln (siehe [Release-Signatur](release-signatur.html)) und kopiert nur die Artefakte
seiner Architektur in eine eigene Quelle – mit Prüfung von Länge, SHA-256 und SHA-512 beim Kopieren. Spätere
Änderungen im Staging wirken danach nicht mehr. Das eigentliche Schreiben übernimmt `systemd-sysupdate` mit dieser
lokalen Quelle in einer eigenen, abgeschotteten Unit; es schützt die laufende Version und versieht das neue
Boot-Image mit einem **Bootzähler**.

### Sicherheitsepoche am Knoten

Zusätzlich zur Manifest-Prüfung hält der Hilfsdienst je Version die geprüfte Sicherheitsepoche fest und als
Untergrenze die höchste Epoche eines **bestätigten** Starts. Schreiben unter diese Untergrenze und Starten eines
Slots darunter werden verweigert. Ein Rückfall auf den vorherigen Slot ist damit nur innerhalb derselben Epoche
möglich.

## Health-Gate

Nach dem Neustart entscheidet das **Health-Gate**, ob der neue Slot bestätigt wird. Es nutzt das *Automatic Boot
Assessment* von systemd: Erst wenn das Gate grün ist, wird der Bootzähler entfernt. Geprüft wird mit Zeitlimit
(Standard zehn Minuten, Überschreitung gilt als rot):

1. Das verity-geschützte `/usr` ist eingehängt, alle Systemerweiterungen sind aktiv, der Zustandsbereich ist
   entsperrt.
2. Der Agent läuft, bedient seinen Watchdog und hat ein gültiges Zertifikat.
3. Das Underlay zu mindestens einem Seed steht, der Gossip-Beitritt ist erfolgt (siehe [Netzwerk](netzwerk.html)).
4. Alle Rollen-Units sind aktiv, der Rollen-Reconcile läuft fehlerfrei.
5. Für Steuerungsknoten: Das Replikationslog ist zum Leader aufgeholt, der Knoten hat wieder seine vorherige Rolle.
6. Für Boot-Knoten: Boot-Daten geladen, Ports gebunden.

Der Agent schreibt dazu regelmäßig einen kleinen, atomar ersetzten Bericht mit Zeitstempel, laufender Version,
Gesamtergebnis und Einzelprüfungen. Das Gate selbst läuft ohne Netz, verlangt einen frischen Bericht und prüft die
Rollen-Units zusätzlich selbst.

## Abbruch und Rückfall

**Auf dem Knoten:** Ist das Gate rot oder hängt der Start, löst der Watchdog einen Neustart aus. Der Bootzähler des
neuen Slots ist dann verbraucht, und der Knoten startet automatisch den **alten** Slot. Auf Raspberry-Pi-Hardware
übernimmt der einmalige *tryboot*-Mechanismus der Firmware dieselbe Aufgabe. Der Knoten meldet `RolledBack` mit dem
Grund aus dem Journal des Fehlversuchs.

**Im Controller:** Meldet ein Knoten `RolledBack` oder `Failed`, oder läuft ein Schritt in eine Zeitüberschreitung,
**pausiert** der Controller den Rollout: Er setzt die Bedingung `RolloutPaused`, erzeugt Audit-Eintrag und Alarm und
gibt keine weiteren Knoten frei. Der betroffene Knoten versucht es nicht erneut. Ein Fehlschlag beim ersten Knoten
stoppt so den gesamten Rollout, bevor er sich ausbreitet.

**Durch den Betreiber:** Ein Rückfall per Aktion `node:rollback` ist möglich, solange die Zielversion dieselbe
Sicherheitsepoche hat und der vorherige Slot noch vorhanden ist; sonst nur mit privilegierter Freigabe. Weiter
zurück geht es nur durch eine Neuinstallation des Knotens. Ein Knoten kann außerdem auf seiner Version festgehalten
und wieder freigegeben werden.

## Ausbaustufen

Der aktuelle Kern umfasst Zielversion je Region und Knoten, rollend einen Knoten, Quorumschutz, Leader zuletzt,
Rückfall über das Health-Gate, Pause bei Fehlern und den Betreiber-Rollback. Vorgesehen sind außerdem
Update-Richtlinien mit **Stufen** – etwa ein einzelner Kanarienvogel-Knoten mit Beobachtungszeit, danach
Arbeitsknoten mit begrenztem Anteil, Boot-Knoten einzeln, Steuerungsknoten einzeln mit Leader zuletzt –,
**Wartungsfenster**, automatische Updates ab Werk mit der Möglichkeit, dringende Sicherheits-Patches auch außerhalb des
Fensters einzuspielen, sowie eine Verteilung der Releases zwischen beliebigen Knoten (Peer-to-Peer). Wie
Sicherheitsrelease und Rollout zusammenspielen, beschreibt [Schwachstellenmanagement](schwachstellenmanagement.html).
