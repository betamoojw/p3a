# IIIF Community Call, 2026-10-14: working folder

Start here for anything about the talk. Status, decisions, and the file
map live in this file; the content lives in the files it points to.

## Event facts

- **What:** a 30-minute presentation plus 15 minutes of questions on one
  of the IIIF community's monthly community calls. The calendar entry
  reads: "IIIF community calls provide a regular forum for new and
  existing participants to share their work, learn about activities
  across the community, and discuss IIIF technology and future
  directions."
- **When:** 2026-10-14. Time and Zoom link come from the organizers.
- **How it came about:** Fab joined the IIIF-Discuss list (2026-08-24)
  and posted the p3a announcement (2026-08-25; it appeared in the
  archive, no replies on the list). He then joined the IIIF Slack, where
  a member said he had seen the email and invited him to present.
  The iiif.io/news cover email to Glen Robson was never sent; it remains
  an option to raise on the call.
- **Recording:** IIIF monthly community calls are normally recorded and
  posted to the IIIF YouTube channel
  (https://www.youtube.com/channel/UClcQIkLdYra7ZnOmMJnC5OA; the July
  2026 call is at https://www.youtube.com/live/eaf6zekj7IA). Assume the
  talk is public and permanent.
- **Audience:** IIIF implementers and institution staff. Assume they know
  IIIF thoroughly and have never seen p3a. Staff from the Rijksmuseum,
  Wellcome, Harvard, the V&A, and SMK may be on the call.

## Status

- 2026-09-08: folder created; Fab interviewed (28 questions, 8 rounds);
  `material.md`, `qa-prep.md`, `video-shot-list.md`, and the first deck
  (`v1/`) drafted. Nothing rehearsed yet.
- 2026-09-08, later: decks organized into version folders. `v2/` drafted
  as a sparse, bullet-driven deck (21 slides) with everything that left
  the slides moved into expanded speaker notes.
- 2026-09-11: grilling round 1 (`grilling.md`). Found that the "59 lines
  of shared C" figure is wrong (that file is a User-Agent and a URL
  encoder; the IIIF template is one line per adapter), that the firmware
  reuses no HTTP connections, and that Harvard `collections/object`
  still 500s and Wellcome facet children still 503.
- 2026-09-17: `v3/` drafted (41 slides) from a third interview (8
  questions, 2 rounds). Product half expanded (channels, playsets,
  everyday use, owner's journey, context), the four-beat road to museums
  (pixel-art player, AI scouting, the UBI built separately, the UBI as
  reference), grilling round 1 corrections folded in, hardware limits
  separated from project choices, no conclusion slide. Ten screenshots
  captured from the dev unit and the UBI test app into `screenshots/`.
  Per-slide suggested durations replace cumulative time marks; Fab trims
  to 30 minutes. The stale "59 lines" and "TLS round trip per request"
  claims were also corrected in `material.md`. **`v3/` is current.**
  Not rehearsed, not yet trimmed.
- 2026-09-17, later: v3's notes rewritten from bullet prompts into the
  full spoken script (about 8,577 words, about 61 minutes at
  140 words a minute), one slide at a time, from a fourth interview (7
  questions, 2 rounds). Each slide's notes now hold a duration mark
  computed from its word count, the words to say, bracketed stage cues,
  and a short "If asked" block of reserve facts.

## Versions

One folder per deck version. Shared material (this README,
`material.md`, `qa-prep.md`, `video-shot-list.md`,
`figure-architecture.svg`, the demo clip) stays at the top level and
serves every version. Each version folder holds `slides.md` plus its
git-ignored exports.

| Version | Slides | Character | Status |
|---|---|---|---|
| `v1/` | 32 (5 section dividers) | Verbose: full sentences and paragraphs on slides, bullet-prompt notes. | Superseded, kept for reference. |
| `v2/` | 21 | Sparse: headline plus up to five short bullets, two tables (nine museums, adoption probe), two allowed exceptions (nine quirk one-liners, seven checklist items). Expanded bullet notes carry every fact and number that left the slides, with cumulative time marks. | Superseded by v3, kept for reference. |
| `v3/` | 41 | Sparse like v2, expanded to be trimmed: 18 product and journey slides, 23 IIIF-perspective slides, ten screenshots, `hardware` and `choice` tags. Notes are the spoken script: a `[~m:ss]` mark computed from the word count at 140 words a minute, the words to read, bracketed stage cues, and an "If asked" block. About 8,577 words, about 61 minutes untrimmed; a 30-minute cut keeps about 22 slides. | Current. Not rehearsed, not yet trimmed. |

To start a v3: copy the current version folder, edit `slides.md`, add a
row here.

## Decision sheet (interview of 2026-09-08)

1. **Title:** "IIIF from the smallest patron". Subtitle: "what nine
   museum APIs look like from a 32 MB art frame".
2. **One takeaway:** the IIIF Image API kept its promise (one URL
   template served pixels from seven image stacks); discovery above it
   is the gap (nine museums needed nine bespoke adapters).
3. **The ask:** feedback on the discovery-gap analysis. Is the
   "Presentation Collections cannot be the discovery layer" conclusion
   right, and is anything on IIIF's roadmap meant to close it?
4. **Time split (balanced):** what p3a is + video 6 min; how p3a uses
   IIIF 5; development process 5; discovery gap 7; idiosyncrasies 5;
   close and ask 2.
5. **Deck format:** Marp Markdown (`slides.md`), exported to PDF, PPTX,
   and HTML. Speaker notes are bullet prompts, not a script.
6. **Demo:** a pre-recorded clip, to be shot per `video-shot-list.md`.
   Fallback: `images/videos/art-institution-channels/p3a-museums-2026-05-19.mp4`
   (from the five-museum era). No live device on camera.
7. **Naming museums:** by name, affection first, quirks shown as observed
   behavior, never as complaints. Invite staff on the call to correct.
8. **AI assistance:** one explicit slide in the process section: the
   project is built with LLM assistance, and an agent scouting for
   content sources surfaced the IIIF Image API.
9. **Code on slides:** the IIIF URL template only. No pseudo-code, no C.
10. **Idiosyncrasies:** one table slide (one line per museum) plus three
    deep dives: Rijksmuseum's Linked Art walk on a microcontroller, the
    Smithsonian WAF that rejects with HTTP 200, SMK's `info.json` that
    advertises WebP and returns 400.
11. **Presentation API argument:** full, three grounds with numbers
    (adoption, specification, economics) across two slides.
12. **Constraints slide:** yes, in the IIIF-usage section (64-byte
    record, 48-byte id, 33-byte identifier, parse buffers, two TLS
    sessions, no `info.json`).
13. **Museums not shipped:** one slide (LoC, Gallica, Getty, Europeana,
    DPLA, plus Smithsonian NMAI/FSG).
14. **Checklist:** all seven "what would help small clients" items on one
    slide.
15. **AIC:** still blocked; one factual sentence framed as "bot defense is
    now a compatibility issue".
16. **Code4Lib article:** mentioned once, as under review, on the closing
    slide.
17. **p3a identity:** one slide on what p3a is (all sources, Makapix
    Club in one sentence), then museums.
18. **Try-it slide:** yes (board, price, web flasher, GitHub).
19. **Bio (title slide):** "Fabrício Kury is a biomedical informatician
    in New York City. He currently works with Medicare claims data
    analytics at Sparx, Inc."
20. **Sharing:** PDF shared with hosts and attendees, CC BY 4.0 on the
    closing slide.
21. **Q&A prep:** separate file, `qa-prep.md`.

Added for v2 (2026-09-08, second interview):

22. **Versioning:** one folder per deck version; shared material at the
    top level.
23. **Density:** headline plus at most five bullets of about eight
    words; no paragraphs; at most two small tables; the quirks list
    (nine one-liners, two columns) and the seven-item checklist are the
    two allowed exceptions.
24. **Slide count:** about 20, always fewer than the 30 minutes. No
    section dividers.
25. **Notes:** expanded bullet notes inside `slides.md` only, no
    separate script file. Everything removed from a slide lands in that
    slide's notes.
26. **Merges relative to v1:** hardware folded into "what p3a is";
    museum-ubi and the AI disclosure share a slide; specification and
    economics share a slide; Smithsonian and SMK share a two-column
    slide; "what is changing" folded into the checklist notes; "try it"
    folded into the closing slide.

Added for v3 (2026-09-17, third interview):

27. **Goal split:** 40% p3a as a product, 60% how IIIF looks from p3a's
    perspective. Generate more than fits; Fab trims. Every slide must
    still earn its place.
28. **The road to museums, four beats,** told before the museum
    channels: a pixel-art player; asking a model to scout the internet
    (this beat carries the AI disclosure); the UBI (unified browsing
    interface, repo name museum-ubi) built separately to prove the
    sources; the UBI as technical reference for the firmware. The May 5
    "Chicago plus NASA APOD" first plan is one line in the scouting
    notes; APOD is not named on a slide.
29. **Product slides beyond what/how/channels/playsets:** the owner's
    journey (fifteen minutes), everyday use, and context. Makapix Club
    gets no slide of its own.
30. **Ending:** no conclusion slide and no push-back ask. The seven-item
    checklist is the last content slide, then thanks. The ask-backs from
    the grilling live in the thank-you notes, for silence.
31. **Inherent versus chosen.** Hardware: 720 × 720, the RAM totals, the
    JPEG decoder's limits, the TLS fingerprint, no browser, and the
    RAM-derived budgets (two TLS sessions, parse buffers, streaming to
    the card). Project choices: the 64-byte record and 48-byte id (a
    16 MB budget so 64 channels × 4,096 records fit in RAM at once), the
    33-byte channel id, no `info.json`, JPEG-only for museums, no
    metadata on the device, no middleman or harvester, the three
    discovery primitives. One slide draws the split; `hardware` and
    `choice` tags mark it elsewhere. Never present a choice as a limit.
32. **Grilling round 1 folded in:** one line of C per museum (1 versus
    3,740 across the seven IIIF adapters); "a round trip and a quota
    unit per request"; `info.json` as "a Level 2 bet, won so far;
    fallback planned"; the Presentation 3.0 change-log sentence on the
    specification slide; the thumbnail qualifier on the economics slide;
    two new slides for the counter-cases (thumbnails in Collections,
    harvest elsewhere). HTTP handle reuse and the `info.json` fallback
    are still planned; the notes carry the "fixed since" wording to swap
    in if either ships before the call.
33. **Size and style:** about 40 slides in v2's sparse style, with a
    suggested duration per slide. Of the three "deliberate
    simplifications", only `info.json` stays on a slide; JPEG-only and
    stream-never-buffer are hardware-column facts in the notes.
34. **Maker-audience material** (progressive-JPEG fallback, chunked
    streaming, per-museum parse buffers, the one-byte state machine, the
    CORS-baked set list) lives in the notes of the slide it supports.
    Not on slides, not cut.
35. **Visuals:** screenshots captured 2026-09-17 from the dev unit
    (`p3a-fab.local`: playset editor, channel cards, the browse modal at
    three steps, home, info card, museum settings) and from the UBI test
    app served locally (`reference/museum-art/ubi-test`,
    `python -m http.server 8765`). Stored in `screenshots/` at the top
    level, shared by every version.

Added for the v3 script (2026-09-17, fourth interview):

36. **Notes are the talk, verbatim.** Each slide's notes are the words
    to read aloud, first person, written to that slide's duration at
    140 words a minute. The `[~m:ss]` mark is computed from the word
    count by `set_durations.py` in this folder, so it is honest after
    every edit; re-run it after trimming and it re-sums the README too.
37. **Voice:** conversational, contractions, dry humor allowed, never
    apologetic, American spelling, no em dashes.
38. **What else lives in the notes:** bracketed stage cues (`[pause]`,
    `[point at the figure]`, `[play the clip]`) and a short "If asked"
    block of reserve facts under each script. Nothing unspoken beyond
    that; the rest stays in material.md, qa-prep.md, grilling.md.
39. **AI tools are named** on the scouting slide: Cursor, Claude Code,
    Anthropic's models, followed by "no affiliation".
40. **Direct asides** to museum staff who may be on the call (Wellcome
    and Harvard on the probe slide, SMK on the two-museum slide, WAF
    operators on the bot-defense slide). The opening carries the
    placeholders `[host name]` and `[the Slack member who invited me]`.
41. **Video narration** is keyed to the seven shots of
    `video-shot-list.md`, with a line saying what to skip over the
    fallback clip.
42. **Transitions flow:** each script ends by setting up the next slide.
    After trimming, fix the seams (the last sentence of each surviving
    slide and the first of the next).

## Files

| File | What |
|---|---|
| `README.md` | This file: event facts, status, decisions, file map. |
| `material.md` | Everything that might go into the talk: facts, numbers, stories, timeline, quotes, asset inventory, with pointers to the sources in the repo. |
| `qa-prep.md` | Anticipated questions from an IIIF audience with drafted answers. |
| `grilling.md` | Mock Q&A run as a class: hard questions, spoken answers, the facts behind them, and the deck changes each one forces. Round 1 on 2026-09-11. |
| `video-shot-list.md` | Shot list for the 60-90 second demo clip. |
| `set_durations.py` | Recomputes each v3 slide's `[~m:ss]` mark from its spoken word count at 140 words a minute and refreshes the totals in this README. Run after any edit to `v3/slides.md`. |
| `figure-architecture.svg` | The article's architecture figure with its counts updated to nine museums. Shared by every version. |
| `screenshots/` | Ten JPEGs (862 × 1400) captured 2026-09-17: `playset-editor`, `playset-editor-channels`, `browse-modal-museums`, `browse-modal-rijks-sets`, `browse-modal-preview`, `home`, `home-info`, `settings-museum` from the dev unit; `ubi-test-home`, `ubi-test-collection` from the UBI test app. Shared by every version; recapture after a web UI change. |
| `v1/slides.md`, `v2/slides.md`, `v3/slides.md` | The Marp decks. Speaker notes are the HTML comments under each slide: bullet prompts with cumulative time marks in v1 and v2; in v3 the full spoken script per slide, with a computed duration mark, stage cues, and an "If asked" block. |
| `v*/slides.pdf`, `v*/slides.pptx`, `v*/slides.html` | Exports (git-ignored, regenerate with the commands below). The video slide is a placeholder in PDF and PPTX; the HTML export plays `demo.mp4` if it sits at the top level of this folder. |

## Exporting the deck

Marp CLI runs through `npx` and uses a local Chrome or Edge for PDF and
PPTX. Run from the repo root, substituting the version folder:

```powershell
Set-Location docs/iiif-community-call/v3
npx --yes @marp-team/marp-cli slides.md --allow-local-files --html --pdf -o slides.pdf
npx --yes @marp-team/marp-cli slides.md --allow-local-files --html --pptx -o slides.pptx
npx --yes @marp-team/marp-cli slides.md --allow-local-files --html -o slides.html
```

`--html` is required: the decks use `<div>` grids and a `<video>` tag.
To review every slide as an image: add `--images png -o out/s.png`
(`out/` is git-ignored).

The PPTX export is one image per slide (Marp's default), which presents
fine but is not editable in PowerPoint. Edit `slides.md` and re-export
instead. `--pptx-editable` exists but is experimental.

For live preview while editing: `npx --yes @marp-team/marp-cli -s .`
serves the folder at http://localhost:8080.

## Before the talk

- [ ] Trim v3 to about 22 slides; sum the `[~m:ss]` durations in the
      notes to 30:00. Cut the product half harder than the IIIF half
      (target 40/60). Then fix the transition sentences at the seams and
      fill in `[host name]` and `[the Slack member who invited me]` on
      the title slide.
- [ ] Decide whether to implement HTTP handle reuse and the `info.json`
      fallback before the call. If either ships, change "planned" to
      "fixed since <date>" on the `info.json` slide, the economics slide,
      and the polite-client notes.
- [ ] Shoot the demo clip (`video-shot-list.md`) and drop it in this
      folder as `demo.mp4`; the video slide links to that name.
- [ ] Re-test AIC on the device the week before; update the coverage
      slide if it unblocked.
- [ ] Re-run the Harvard and Wellcome Presentation probes the week
      before (commands in `material.md` §6.3), so the "broke one level
      down" claim is current on the day.
- [ ] Re-check the board price on waveshare.com and update the try-it
      slide.
- [ ] Rehearse at least three times against the time marks in the
      speaker notes; the deck is built for 30:00 with no slack.
- [ ] Export the final PDF and send it to the hosts after the call.
