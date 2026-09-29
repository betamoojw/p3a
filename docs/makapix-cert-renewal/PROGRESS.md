# Makapix mTLS Client-Certificate Renewal — Progress

## 2026-07-08 — Implementation (branch `feature/makapix-cert-renewal`)

Implemented per PLAN.md. Firmware version unchanged at `1.1.0` (Fab's call;
release versioning decided at release time), webui `2.15`.

### What was built

- **`components/makapix/makapix_renewal.c/.h` (new)** — renewal engine:
  - Periodic task (`cert_renew`, PSRAM stack): every check waits until
    Wi-Fi holds an IP **and** the clock is SNTP-synchronized (10 s poll; no
    arbitrary boot delay), then runs; repeats every
    `CONFIG_MAKAPIX_CERT_RENEW_CHECK_HOURS` (default 24), plus an early kick
    on every MQTT connect.
  - Local expiry read: `mbedtls_x509_crt_parse` on the stored client cert,
    `notAfter` → epoch via a UTC days-from-civil helper (no mktime/timezone
    traps).
  - Clock gate: no decision (and no API traffic) unless
    `time(NULL) >= 2026-01-01` — an unsynced 1970 clock cannot trigger a
    fleet renewal storm.
  - Window: `CONFIG_MAKAPIX_CERT_RENEW_WINDOW_DAYS` (default 45, inside the
    server's 90) with a fresh 0–7-day jitter draw per check; jitter is
    bypassed within 14 days of expiry and after expiry.
  - Token bootstrap: stored token, else `POST /player/{key}/token/rotate`
    (persist-before-rely; NVS write failure retries the write, never the
    rotate). Renewal: `POST /player/renew-cert` with `Authorization: Bearer`;
    one rotate-and-retry on 401; 400 = not-due; 404 = player gone; 429/5xx =
    wait for next check.
  - Persist: `makapix_store_save_renewed_certs()` — cert+key+CA in a single
    NVS commit (make-before-break; power loss leaves the old working set).
  - Adoption: disconnected devices pick the new PEMs up on the next reconnect
    cycle (which reads NVS); connected devices are left alone; a latched
    `REGISTRATION_INVALID` state is cleared and reconnection restarted when a
    forced renewal succeeds.
- **Self-heal** (`makapix_connection.c`): at the `MAX_AUTH_FAILURES`
  threshold, one forced renewal attempt per outage (flag re-armed on every
  successful connect) before latching `REGISTRATION_INVALID`. Expiry state
  per the local clock is logged with the attempt.
- **Token capture at registration** (`makapix_provision.c/.h`,
  `makapix_provision_flow.c`): the credentials response's one-time
  `api_token` is now parsed and persisted in the same NVS transaction as the
  registration (previously discarded — the reason the whole existing fleet
  needs the token/rotate bootstrap).
- **Store** (`makapix_store.c/.h`): `api_token` NVS key (get/set, cleared on
  unregister), `makapix_store_save_renewed_certs()`,
  `makapix_store_save_registration()` gained an optional `api_token` arg.
- **Status surfacing**: `/api/status` `makapix` object gains
  `cert_expires_at` (ISO 8601) + `cert_renewal` (last result); settings webui
  Makapix tab shows "Certificate valid until … (N days)" / "expired — renews
  automatically" under the health badge. No manual renew button (decision:
  Fab, 2026-07-08).
- **Config**: `MAKAPIX_CERT_RENEW_WINDOW_DAYS`, `MAKAPIX_CERT_RENEW_CHECK_HOURS`
  in `components/makapix/Kconfig`.

### Decisions recorded

- No webui "Renew now" button (owner-gated endpoint stays server-side only).
- Self-heal trigger: expiry-first logging, one unconditional attempt before
  latching — confirmed by Fab.
- Renewal never bounces a live MQTT connection; new certs apply on the next
  natural reconnect (make-before-break both ends).

### Pending

- [ ] Build + flash by Fab (per repo policy, Claude does not build).
- [x] End-to-end test against development.makapix.club — run 2026-07-08 with
  dev build (host=development, window 3650 d, check 1 h), test player_key
  79c3a2f0-89ea-43c7-8a41-5d117a753cf8. Results (messages 0003–0008 in the
  MPX repo's docs/cert-renewal/messages/):
  - T1 registration + api_token capture: PASS.
  - T2 renewal under live MQTT connection: PASS (zero disconnects, ~3 s).
  - Self-heal at auth-failure threshold: PASS (fired live during the dev
    broker SAN incident; renewed under fire, exactly one attempt).
  - Un-latch self-recovery from REGISTRATION_INVALID: PASS (hourly renewal
    cleared the latch with no human touch; first successful dev connect).
  - T3 token loss (server deleted player_tokens row): PASS — 401 → exactly
    one rotate (persist-before-rely) → renewed.
  - T4 cert revocation (server CRL'd current serial): PASS — reject →
    proactive renewal → reconnect with fresh PEMs → online in ~11 s;
    REGISTRATION_INVALID never appeared.
  - Bonus finds: dev broker cert lacked development.makapix.club SAN (first
    hostname-verifying client ever on dev:8884; server fixed with env-aware
    SANs + re-mint); server's CRL inotify watcher missed its first
    cross-container event (server hardened with 60 s content-hash poll —
    matters for prod's 2026-07-25 CRL deadline).
- [x] T5 rate-limit (429): PASS 2026-07-09 ~15:01 UTC — after burning the
  10/day/player budget via repeated boot renewals, the 11th attempt returned
  HTTP 429; device classified it `rate_limited`, no retry loop, MQTT session
  unaffected, waits for the next hourly check. (Observed window semantics:
  fixed 24 h window from first renewal of the period, not sliding.)
  T6 clock gate: declared covered — the network+SNTP prerequisite gate was
  observed holding the check at every boot.
- [x] Final results message 0009 sent 2026-07-09 (MPX repo, develop) —
  full matrix reported; release committed for END OF JULY 2026; server
  housekeeping green-lit; prod CRL-watcher-before-2026-07-25 reminder given.
- [x] Teardown done 2026-07-09: prod sdkconfig restored (renewal defaults
  45 d / 24 h committed), rebuilt, reflashed, device re-registered on prod
  (new player_key cd5ef4ac-…, api_token captured at registration, connected
  to makapix.club:8883, renewal task correctly silent — fresh cert not in
  window). Note: the pre-test prod player record (5cf229f7-…) is now an
  orphan in Fab's account and can be deleted from the makapix.club web UI.
- [x] Merge feature/makapix-cert-renewal → main — DONE 2026-07-09
  (fast-forward, main @ 8389ee7c); released as v1.1.0 on 2026-07-17 (tag on
  a3f65c61), ahead of the end-of-July commitment.
- [x] External watch item: MPX team deploys hardened CRL watcher to prod
  BEFORE 2026-07-25 — CONFIRMED by the MPX team (recorded 2026-08-10):
  deployed before the deadline; no at-risk window occurred.
- [x] Prod `min(cert_expires_at)` — CONFIRMED 2026-12-12 09:12 UTC (4 certs
  Dec 2026; 15/24 before Jun 2027; 9 already 3-year). Renewal window opens
  2026-09-13 = firmware release deadline. MPX plan doc updated by server team.
- [x] Prod stale-CRL check — no active outage (broker restarted 2026-07-07,
  loaded CRL valid to 2026-07-25); server team commits to deploying the CRL
  watcher to prod BEFORE 2026-07-25 (else manual broker restart Jul 18-25).
- [x] Release + OTA rollout before 2026-09-13 (window-open) and hard-before
  2026-12-12 (first expiry) — v1.1.0 published to GitHub Releases 2026-07-17
  with ~2 months of runway; fleet adopts via OTA.

## 2026-08-10 — Project CLOSED

The MPX team confirmed the hardened prod CRL watcher was deployed before
the 2026-07-25 CRL-expiry deadline — the last external dependency on this
project. With firmware renewal released in v1.1.0 (2026-07-17), the renewal
window opening 2026-09-13, and the earliest fleet cert expiry 2026-12-12,
the cliff is fully de-risked: renewal is automatic, self-healing was e2e
tested (T1–T6), and no further tracking is needed.

## 2026-09-29 — Reopened: MQTT CA rotation (old trust anchor expires 2026-10-25)

Trigger: MPX message 0010 (MPX repo, `docs/cert-renewal/messages/`). The
server re-issued the MQTT CA on 2026-05-27 (same key, 10-year cert). The
previous CA certificate expires 2026-10-25 02:08 UTC. Devices only receive
`ca_pem` at provisioning and through the renew-cert response, so 15 of 29
production players (provisioned before the re-issue, client certs expiring
2026-12-12 to 2027-04-16) still trust only the old CA. The server raised
`CERT_RENEWAL_THRESHOLD_DAYS` 90 -> 200 on 2026-09-29 so every such cert is
inside the server window, and asked whether our check uses a local constant.

Findings against the shipped firmware (1.1.0 through 1.2.3):

- The window IS a local constant: 45 days, checked every 24 h (the "hourly"
  the MPX team remembered was the July dev config). Earliest fleet cert
  2026-12-12 puts the first local window at 2026-10-28, after the CA expiry,
  so no pre-re-issue device renews proactively. All 15 take the three-failure
  self-heal path: an expired trusted root gives mbedTLS `BADCERT_EXPIRED`,
  esp-tls reports 0x801a (the code the auth-failure counter keys on) with
  non-zero verify flags, the reconnect task force-renews after failure #3,
  renew-cert runs over HTTPS with the public bundle (independent of the MQTT
  CA), and the response's `ca_pem` is persisted. About 2 minutes of backoff
  per device, then online. Not lab-tested against an expired root.
- Gap: the self-heal is one-shot per outage. A transient failure of that one
  renew-cert call latches `REGISTRATION_INVALID`, and the daily check honours
  the 45-day window ("not_due"), so such a device stays dark until a
  power-cycle.

Firmware changes on main for 1.2.4 (release committed to MPX for 2026-10-10;
unverified on hardware until Fab tests):

1. `MAKAPIX_CERT_RENEW_WINDOW_DAYS` default 45 -> 190 (inside the server's
   200), in Kconfig and the tracked `sdkconfig`. Updated devices renew every
   pre-re-issue cert within the 0-7 day jitter of taking the OTA.
2. Broker-certificate verify failure forces an immediate renewal: the MQTT
   error handler records non-zero `esp_tls_cert_verify_flags`
   (`makapix_mqtt_server_cert_verify_failed()`), and the reconnect task
   calls the shared `try_cert_selfheal()` on the first such failure instead
   of waiting for the threshold. Future CA rotations no longer depend on the
   renewal window. A "no_clock" outcome does not consume the one-shot.
3. The periodic check forces the attempt while the state is
   `REGISTRATION_INVALID`, so a latched device retries once per check
   interval and the server (400/404) decides whether the latch is genuine.

Reply sent as MPX message 0011 (answers (a), (b), (c); asks them to keep 200
permanent and to report reconnect counts after 2026-10-25).
