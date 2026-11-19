title: Changing the portal hostname
summary: Runbook for changing the portal address – what happens to the OIDC issuer, the WebAuthn RP ID and registered passkeys, and how access is preserved.
group: prozess
order: 240
quelle: Runbook portal hostname
de: portal-hostname
---

## Background

A region's **portal address** is more than just a URL. It is at the same time:

- the **OIDC issuer** (`iss`) of all tokens the platform issues, and
- the basis of the **WebAuthn RP ID** – which is the hostname of the address.

Under the WebAuthn standard, passkeys are bound firmly to the RP ID. Changing the hostname therefore has
consequences for everyone who signs in with a passkey. This runbook describes how to carry out such a change in a
planned way and what to do after an unplanned change. Background on identities, passkeys and emergency access can be
found in [Identity](identity.html).

## What happens

| Change | Effect |
|---|---|
| only the **port** (`https://cloud.example.org:8443` → `https://cloud.example.org`) | The RP ID stays the same; passkeys remain valid. The issuer changes: access tokens from the previous issuer remain valid until they expire (10 minutes), and a refresh yields tokens with the new issuer. Command-line and MCP clients must enter the new endpoint. |
| the **hostname** (`cloud.example.org` → `portal.example.org`) | **New RP ID – all registered passkeys become unusable.** The browser does not offer them for the new domain, and the server rejects assertions with a foreign RP ID hash. Without countermeasures, nobody can sign in with a passkey anymore. |

Losing the passkeys is unavoidable by design – it is precisely the phishing protection that WebAuthn provides. The
runbook ensures that the change nevertheless succeeds in a controlled way and without locking anyone out.

## Planned hostname change

1. **Prepare (still under the old address):** prepare an admin invitation for every person with a passkey – **do not
   create** them yet, just record the list of affected people. Existing invitations and sessions can be listed via
   the command line or the portal.
2. **Ensure emergency access:** on a control node, locally and as administrator, enable the time-limited emergency
   access, for example for one hour. It can only be activated locally and is fully audited. This keeps the command
   line operational with an emergency token in case the switchover runs into problems.
3. **Switch DNS and address:** create the DNS record for the new name (when using the platform DNS role, via a
   dedicated zone, see [DNS](dns.html)) and then set the portal address to `https://portal.example.org`. The portal
   certificate is reissued; the shared issuer is picked up on all identity nodes within a few seconds via the
   replicated control plane (see [Control plane](control-plane.html)).
4. **Create new invitations:** use the emergency access to create new admin invitations. The invitation links
   already contain the new address. The recipients redeem them in the browser on the new domain and register a new
   passkey in the process.
5. **End emergency access:** after the first successful passkey sign-in, the emergency token is deactivated
   automatically; in addition, explicitly switch off the emergency access.
6. **Clean up:** revoke old sessions (command line or portal, "Sessions" section). Old passkey entries remain in
   place without effect until they are cleaned up.
7. **Update clients:** command-line users enter the new endpoint in their configuration and sign in again; the same
   applies to MCP clients.

## Unplanned change

If the hostname has already been changed and the passkeys are therefore invalid, the preparation step is dropped.
Step 2 (emergency access locally on the node) followed by steps 4 to 7 is sufficient.

Without administrative access to a control node, the only remaining option is the break-glass procedure from the
identity concept (see [Identity](identity.html)).

## Checks after the change

- The OIDC discovery under the new address
  (`https://portal.example.org/.well-known/openid-configuration`) lists the new address as `issuer`.
- For each node, the agent log shows an event about the changed issuer and the newly loaded portal certificate.
- The audit log contains the reactivation of emergency access, the invitations created and the first sign-in under
  the new address.

## Notes

- A **port-only change** is uncritical and only requires updating the clients.
- Choose the hostname deliberately during setup: the portal address is mandatory when initializing a region and must
  be a DNS name (see [OS image](os-image.html)).
- Emergency access is a deliberately narrow tool: local, time-limited, audited and switched off automatically after
  the first regular sign-in (see [Security model](security-model.html)).
