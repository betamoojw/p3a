# Outreach execution ledger

What has actually been sent, where, with what result, and what is still
parked. This is the record behind the plans in `outreach-plan.md` (maker
track) and `museum-outreach-plan.md` (museum track). Check it before
proposing any outreach action so nothing gets double-sent or a venue burned.
Update it whenever something is actually sent.

Last updated: 2026-08-25.

## Status at a glance

Public actions fired so far:

| Date | Venue | Result |
|------|-------|--------|
| (before 2026-06) | r/esp32, more than once | 100+ upvotes, tens of shares each; on cooldown |
| (before 2026-06) | Show HN / HN, once | About zero engagement; framing and title problem, not the project. A retry needs a sharper title, a first comment, and a better landing asset |
| (before 2026-06) | CNX-Software contact form | No response after months; cold |
| (before 2026-06) | r/embedded | Posted long ago; spent |
| (before 2026-06) | r/diyelectronics | Posted, weak reception (device is not "DIY enough", it ships ready out of the box) |
| 2026-06-07 | r/MuseumPros | 200+ upvotes, about 100 shares in four days. The big win. Validates the open-access-payoff framing and the photo plus discussion-question format |
| 2026-06-15 | r/DigitalHumanities (survey-led) | 10 upvotes, 1 comment |
| 2026-08-10 | Code4Lib Journal article submitted | Receipt confirmed 2026-08-24; the Journal is on hold for new issues, no timeline |
| 2026-08-16 | r/DigitalHumanities (device announcement, 5 fresh photos) | 351 views, 16 upvotes, 3 shares at T+3h; venue now fully spent (two posts) |
| 2026-08-25 | IIIF-Discuss mailing list | Submitted; held in Google Groups first-post moderation (see below) |

Everything else (museum digital-team emails, the four editorial tips,
Hackaday tip, Adafruit Show & Tell, YouTuber units, awesome-esp PR,
Bluesky/Mastodon, Lospec Discord, r/ArtHistory, r/Libraries, r/Archivists)
remains unsent.

Venues closed to us: r/pixelart (mods require every post to be pixel art),
r/museums (dead: 5,041 subs, hot median 4, ~25-day-stale front page),
r/raspberry_pi and r/arduino (Pi identity / not Arduino, overlaps r/esp32),
r/somethingimade (bans all self-promo links including comments; optional at
best), code4lib-l listserv (parked, see 2026-06-23).

## Blockers and gates

- **Critical path: the 30-second demo video.** Every editorial, museum, and
  social draft carries an unfilled `{{video_url}}` placeholder. A brief is
  ready at `museum-mode-video-brief.md`. With the cheap broadcast maker
  channels spent, the video gates essentially all remaining high-ROI moves
  (HN redo, Hackaday feature, editorial tips, museum emails). No usable demo
  video exists; the campaign is running video-less because of asset absence,
  not preference (decision 2026-06-23).
- Ready to send with no video: Hackaday tip (`hackaday-tip-email.md`, drafted
  2026-06-23), Adafruit Show & Tell (live demo), YouTuber review units (the
  unit is the demo; highest remaining ROI), awesome-esp PR, Bluesky/Mastodon
  wave (photos now exist), r/ArtHistory mod-DM.
- README gaps cleared: README2 was merged as README.md (37245caa).

## Policies

**Social-proof citation policy (confirmed 2026-06-11, tiered by register):**
explicit numbers plus the `{{museumpros_thread_url}}` link in the four
editorial tips (Hyperallergic, Open Culture, WMMNA, and the MCN cover email
only, not the drop-in blurb); one soft no-numbers sentence in all seven
museum digital-team email variants; nothing in code4lib, IIIF-Discuss, or
IIIF news (Reddit karma on professional listservs reads as marketing). Refresh
the numbers on each send day.

**Register (2026-08-25):** no em dashes in any outreach text (an AI-text
tell), a confident non-apologetic voice, shorter and less dense.

**KPI split:** the museum track converts to reputation (shares, thread
quality, downstream pickups), not builders. Adoption (stars, flashes) must
come from the maker track, measured by release-asset downloads. Baseline
captured 2026-06-11 after the MuseumPros post: about 8 uniques/day before,
then 27 / 58 / 18 / 9 on days 0 to 3 (about 80 incremental uniques), 1 star,
1 fork, no flash uptick (v0.10.1 cumulative since May 26: manifest.json 83,
mostly OTA version probes, vs p3a.bin 3 and p3a-flasher.exe 4).

## Timeline

- **2026-06-07** r/MuseumPros posted (Fab, directly). 200+ upvotes, about
  100 shares in four days.
- **2026-06-08** GitHub Topics added; subscribed to code4lib-l (2 to 3 week
  lurk before posting). Every outreach draft swept from five museums to seven
  (Harvard Art Museums and Smithsonian added) across about 11 files. Two real
  bugs fixed in the sweep: Smithsonian was listed as a future "roadmap"
  aggregator in `iiif-discuss-thread.md` and `code4lib-post.md` (it had
  shipped), and the "five museums, interchangeable endpoints" over-claim was
  reframed as sizing solved, discovery heterogeneous (Rijks Linked-Art walk,
  Harvard NRS to IDS redirect, Smithsonian WAF/User-Agent quirk). Harvard and
  Smithsonian email variants (#6, #7) and two social posts (6a, 6b) drafted.
  Confirmed both honor the `!720,720` confined-size request (HAM 8/8, SI
  17/17; some Smithsonian NMAI `ark:/65665` ids 404 on IDS, a per-unit
  coverage gap, not a size-param rejection).
- **2026-06-09** README2.md drafted (full marketing rewrite): comparison
  table (p3a is an IPS LCD, not an LED-matrix competitor; honest landscape vs
  Pixoo 64 and Tidbyt, the latter no longer sold after the 2024 Modal
  acquisition) plus a "Why I built this" section. CTA: DIY only plus Discord
  assist; nobody sells pre-flashed units.
- **2026-06-11** Drafts swept for the MuseumPros result; `!720,720` checklist
  item verified against firmware; tiered social-proof lines added;
  `{{museumpros_thread_url}}` placeholder added to the four editorial drafts;
  execution-status section added to `museum-outreach-plan.md`.
- **2026-06-15** r/DigitalHumanities posted, survey-led not device-led: the
  IIIF-API survey (`reference/museum-art/docs/museum-candidates.md`, about 18
  sources ranked, 9-source watch list, 60+ rejected) is the lede; "the Met and
  Cleveland have CC0 APIs but no IIIF" is the teaser; pagination
  offset-vs-cursor-vs-walk is the recurring-headache nugget. Body text-only,
  research-pure, ends on an engagement question; device link and photo in a
  self-reply comment. Constraint learned: r/DigitalHumanities forbids images
  in comments, so the photo went in as a hosted-image link. Considered and
  rejected deleting and reposting with a body photo (repost-spam filters, a
  body image tips the post toward product showcase).
- **2026-06-23** Decision: proceed video-less. code4lib-l post finalized, then
  **parked entirely** the same day after reading 30 days of the list: no
  IIIF, image-delivery, digitization, or museum traffic, mostly jobs, CFPs,
  events, and library-ops threads; project shares that land there solve a
  library's own problem, whereas p3a is creative reuse on a consumer gadget.
  The Code4Lib Journal remains the better-fit option, pitched directly.
  Hackaday tip drafted (`hackaday-tip-email.md`, tips@hackaday.com):
  hack-first framing (embedded IIIF client, dual-radio ESP32-C6, on-device
  hardware JPEG decode, web flasher and OTA), board second; cites the r/esp32
  and r/MuseumPros numbers per policy. The Makezine article is real and live
  (https://makezine.com/projects/desktop-pixel-art-player-p3a/, linked from
  the README) and is cited as credibility. Maker-track ledger confirmed with
  Fab (the table above). Lesson: cheap broadcast maker channels are spent;
  remaining gains need earned-media assets (Hackaday feature, YouTuber units)
  or the museum reputation engine, which raises the video's value.
- **2026-08-08** Code4Lib Journal article drafted in
  `docs/outreach/code4lib-journal/` (README is the decision sheet;
  `article.md` about 4,400 words, "Writing an IIIF Client on a $40
  Microcontroller"; `presentation-api-research.md` holds live 7-museum probes
  from 2026-08-07 showing IIIF Presentation could not have been the discovery
  layer: adoption broken on 5+ of 7, no counts, offset, or facets, 50 to 100
  times the request cost). The journal takes rolling submissions
  (c4ljournal@gmail.com); article first, then proposal; full AI disclosure in
  narrative and methods note; hero photo is AIC 45243 Degas *Two Dancers*
  (CC0).
- **2026-08-10** Article approved after Fab's full review (merged e8d3008c):
  JPEG section made evidence-based (AIC and HAM serve progressive JPEG,
  hence always-software decode; the other five baseline), build cost "$70
  all-in" on a $39.99 board, the candor paragraph and phone-on-shelf sentence
  dropped, priority claim kept with "I would welcome correction". **Submitted
  11:16 ET** (as-sent text in `code4lib-journal/submission-email.md`).
- **2026-08-16** r/DigitalHumanities device announcement posted with 5 fresh
  photos (first real photo set; press-kit seed; text archived in
  `reddit-digitalhumanities-post.md`). Same day, a live Reddit venue audit via
  in-browser about.json/rules.json/hot.json produced the closed-venue list
  above plus: **r/ArtHistory is the new lead Reddit venue** (359,657 subs,
  active) but has a strict art-history-not-art-appreciation rule, so mod-DM
  first with a Malraux musée-imaginaire / reproduction-history essay framing
  (key beats: scale abolished, sequence out of the viewer's hands, museums now
  run the presses; closing ask is reading recommendations on domestic display
  of reproductions); **r/Libraries (154,316) and r/Archivists (33,612)** are
  viable next stops from 2026-08-23 with a Wellcome/SI and
  IIIF-as-library-standard angle. Queued: seed comment on the DH post (IIIF
  sizing plus discovery-heterogeneity footnote), Bluesky/Mastodon wave,
  Hackaday tip send, r/ArtHistory mod-DM.
- **2026-08-24** Code4Lib Journal reply: submission received, but the Journal
  is on hold for new issues (only a special-topic issue in progress) for
  administrative and technical reasons, with no estimate for when regular
  evaluation resumes. The old "decision by about 09-10" clock is void. No
  action; a short status check is reasonable in late 2026. Withdrawing to
  place the article elsewhere is Fab's open option, not decided. Recorded in
  `code4lib-journal/README.md` and `museum-outreach-plan.md`.
- **2026-08-25** IIIF track re-armed as a mailing-list email. Fab joined
  IIIF-Discuss on 2026-08-24; the list email replaces the planned
  discuss.iiif.io forum post (send one, not both), goes video-less with 1 to 2
  photos from the 08-16 shoot, and gives the AIC Cloudflare block one factual
  sentence with no discussion question. `iiif-discuss-thread.md` reworked
  (subject line, plain-text body, 9 museums, CMA/Mia non-IIIF contrast
  bullet, a Europeana-400px / DPLA-thumbnail question replacing the stale
  "Europeana/DPLA on roadmap" claim); companion references updated in
  `museum-outreach-plan.md` and `iiif-news-submission.md`. Archive skim (30
  threads Mar to Aug, 4 full reads): announcements from individuals and
  vendors are a normal genre, no forum mirroring, no [ANN] prefixes, posts
  are link-only, expect a quiet reception (0 to 4 replies, 24 to 42 web
  views; the value is inbox reach and the archive). **Submitted, then held in
  Google Groups first-post moderation** (new-member posts are moderated; the
  author cannot see their own pending message). Not visible in the archive
  means not sent for sequencing purposes: the 2 to 3 day IIIF news-email
  clock starts when the post appears. If not visible in 5 to 7 days, contact
  iiif-discuss+owners@googlegroups.com or resend. The museum-track Tier 1
  cascade (museum-team emails citing IIIF pickup) starts once the post is
  live.

## Open decisions (not blockers)

- Cadence: do Harvard and Smithsonian get their own digital-team email weeks
  (6 and 7), or does the Smithsonian route through its Tier-2 Open Access
  showcase slot? Flagged in `museum-outreach-plan.md`; variants are drafted
  either way.
- Pending harvest: the r/MuseumPros comment thread for institution
  suggestions (roadmap) and recurring questions (prepped replies).
