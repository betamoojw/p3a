# Questions and answers

Asked 2026-09-28 before starting the work.

## Round 1

**Which on-device messages have you actually seen?**
Runtime: "SD card error" overlay (plus the web UI "SD Card Failure" banner).
The boot-time "No Usable SD Card / Format card for p3a" screen was not seen.

**What is the history of this card and when did the trouble start?**
Same card used all along (the dev unit's long-standing card). The card was
formatted by p3a on-device at least once.

**Which hardware is available for A/B tests?**
Only what is connected now: UART bridge on COM5 and the LAN. Later, when Fab
is back home, a known-good spare microSD may be swapped in, and a PC card
reader (with a microSD-to-SD adapter) may be available.

**What am I allowed to do to the device during diagnosis?**
Full ownership of the device and its microSD card: reboot freely, flash
diagnostic builds, leave it running for hours, change settings, reset or
format the card.

## Round 2

**How often does the runtime latch trip, and since when?**
Constant since today (Monday 2026-09-28). Last Friday (2026-09-25) it was
working normally.

**Desired outcome if the cause is sporadic bus errors from the card?**
Diagnosis plus shippable mitigation: implement resilience fit for `main`
(for example retries on transient SD errors, 40 MHz to 20 MHz fallback,
smarter latch), device-verified here before merge.

**Where should firmware changes land while in progress?**
Feature branch (`fix/sd-resilience`); the `requests/` folder commits ride on
it too. Fab merges when satisfied.

**Does the trouble coincide with anything specific?**
No pattern noticed. The device was working normally, was unplugged, sat
unplugged for three days, and was having issues when replugged today.

## Round 3 (evening of 2026-09-28, before the overnight soak)

**Format the card overnight to test the format path and a clean filesystem?**
No, keep the card as-is: preserve the evidence for the later A/B and PC
inspection; only archive dumps and observe.

**Boot FAT mirror check costs about one second per boot on 64 GB. Acceptable?**
One second is fine; keep the full compare.

**Branch handover?** Push `fix/sd-resilience` to origin, no pull request.

**Anything else overnight?** Overnight soak with a morning report; a
release-configuration build of the branch (no debug overlay) flashed in the
morning for a final check; a simplify/review pass on the new code with no
behavior change without device re-test.
