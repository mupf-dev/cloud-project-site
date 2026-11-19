title: Portal-Hostname ändern
summary: Runbook für den Wechsel der Portal-Adresse – was mit OIDC-Aussteller, WebAuthn-RP-ID und registrierten Passkeys passiert und wie der Zugang erhalten bleibt.
group: prozess
order: 240
quelle: Runbook Portal-Hostname
---

## Hintergrund

Die **Portal-Adresse** einer Region ist mehr als nur eine URL. Sie ist zugleich:

- der **OIDC-Aussteller** (`iss`) aller Tokens, die die Plattform ausstellt, und
- die Grundlage der **WebAuthn-RP-ID** – das ist der Hostname der Adresse.

Passkeys sind nach dem WebAuthn-Standard fest an die RP-ID gebunden. Ein Wechsel des Hostnamens hat deshalb
Folgen für jede Person, die sich per Passkey anmeldet. Dieses Runbook beschreibt, wie ein solcher Wechsel geplant
durchgeführt wird und was bei einem ungeplanten Wechsel zu tun ist. Hintergründe zu Identitäten, Passkeys und
Notfallzugang stehen in [Identität](identitaet.html).

## Was passiert

| Änderung | Wirkung |
|---|---|
| nur der **Port** (`https://cloud.example.org:8443` → `https://cloud.example.org`) | Die RP-ID bleibt gleich, Passkeys gelten weiter. Der Aussteller ändert sich: Access-Tokens des bisherigen Ausstellers bleiben bis zu ihrem Ablauf (10 Minuten) gültig, ein Refresh liefert Tokens mit dem neuen Aussteller. Kommandozeilen- und MCP-Clients müssen den Endpunkt neu eintragen. |
| der **Hostname** (`cloud.example.org` → `portal.example.org`) | **Neue RP-ID – alle registrierten Passkeys werden unbrauchbar.** Der Browser bietet sie für die neue Domain nicht an, und der Server lehnt Assertions mit fremdem RP-ID-Hash ab. Ohne Gegenmaßnahme kann sich niemand mehr per Passkey anmelden. |

Der Verlust der Passkeys ist fachlich unvermeidbar – er ist gerade die Schutzwirkung von WebAuthn gegen Phishing.
Das Runbook sorgt dafür, dass der Wechsel trotzdem kontrolliert und ohne Aussperren gelingt.

## Geplanter Hostname-Wechsel

1. **Vorbereiten (noch unter der alten Adresse):** Für jede Person mit Passkey eine Admin-Einladung vorbereiten –
   noch **nicht anlegen**, nur die Liste der betroffenen Personen festhalten. Bestehende Einladungen und Sitzungen
   lassen sich über die Kommandozeile oder das Portal auflisten.
2. **Notfallzugang sicherstellen:** Auf einem Steuerungsknoten lokal und als Administrator den zeitlich begrenzten
   Notfallzugang einschalten, etwa für eine Stunde. Er ist nur lokal aktivierbar und wird vollständig auditiert.
   Damit bleibt die Kommandozeile mit einem Notfall-Token handlungsfähig, falls die Umstellung hakt.
3. **DNS und Adresse umstellen:** Den DNS-Eintrag für den neuen Namen anlegen (bei Nutzung der Plattform-DNS-Rolle
   über eine eigene Zone, siehe [DNS](dns.html)) und anschließend die Portal-Adresse auf
   `https://portal.example.org` setzen. Das Portal-Zertifikat wird neu ausgestellt; der gemeinsame Aussteller wird
   über die replizierte Steuerungsebene innerhalb weniger Sekunden auf allen Identitätsknoten übernommen (siehe
   [Steuerungsebene](steuerungsebene.html)).
4. **Neue Einladungen anlegen:** Mit dem Notfallzugang neue Admin-Einladungen erstellen. Die Einladungslinks
   enthalten bereits die neue Adresse. Die Personen lösen sie im Browser auf der neuen Domain ein und registrieren
   dabei einen neuen Passkey.
5. **Notfallzugang beenden:** Nach der ersten erfolgreichen Passkey-Anmeldung wird der Notfall-Token automatisch
   wieder deaktiviert; zusätzlich den Notfallzugang ausdrücklich abschalten.
6. **Aufräumen:** Alte Sitzungen widerrufen (Kommandozeile oder Portal, Bereich „Sitzungen“). Alte Passkey-Einträge
   bleiben wirkungslos stehen, bis sie bereinigt werden.
7. **Clients anpassen:** Nutzer der Kommandozeile tragen den neuen Endpunkt in ihrer Konfiguration ein und melden
   sich neu an; MCP-Clients ebenso.

## Ungeplanter Wechsel

Ist der Hostname bereits geändert und sind die Passkeys damit ungültig, entfällt die Vorbereitung. Es genügen
Schritt 2 (Notfallzugang lokal am Knoten) und anschließend die Schritte 4 bis 7.

Ohne administrativen Zugang zu einem Steuerungsknoten bleibt nur der Break-Glass-Ablauf aus dem
Identitätskonzept (siehe [Identität](identitaet.html)).

## Prüfungen nach dem Wechsel

- Die OIDC-Discovery unter der neuen Adresse
  (`https://portal.example.org/.well-known/openid-configuration`) nennt als `issuer` die neue Adresse.
- Im Agenten-Log erscheint je Knoten ein Ereignis über den geänderten Aussteller und das neu geladene
  Portal-Zertifikat.
- Das Audit-Log enthält die Reaktivierung des Notfallzugangs, die angelegten Einladungen und die erste Anmeldung
  unter der neuen Adresse.

## Hinweise

- Ein **reiner Portwechsel** ist unkritisch und braucht nur die Anpassung der Clients.
- Den Hostnamen deshalb bei der Einrichtung bewusst wählen: Die Portal-Adresse ist bei der Initialisierung einer
  Region Pflicht und muss ein DNS-Name sein (siehe [OS-Image](os-image.html)).
- Der Notfallzugang ist ein bewusst eng begrenztes Werkzeug: lokal, befristet, auditiert und mit automatischer
  Abschaltung nach der ersten regulären Anmeldung (siehe [Sicherheitsmodell](sicherheitsmodell.html)).
