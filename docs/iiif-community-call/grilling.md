# Grilling notes

Mock Q&A for the 2026-10-14 call, run as a class: each question an IIIF
audience member could ask, a spoken answer of about a minute, and the
facts behind it. Hats worn: Presentation and Discovery spec editors, and
image-server implementers. Facts were checked against the live specs and
endpoints on the date of each round.

## Round 1 (2026-09-11)

### Corrections found while preparing the round

Three facts surfaced during checking. Each changes an answer below, and
two change the deck.

1. **The "59 lines of shared C" claim is wrong.** `museums/common.c` is
   59 lines, but it holds the User-Agent builder and a percent-encoder,
   nothing IIIF. The URL template `{base}/{id}/full/!720,720/0/default.jpg`
   is one `snprintf` inside each of the seven IIIF adapters, in a
   `build_iiif_url()` of 13 to 25 lines; Cleveland and Minneapolis fill
   the same dispatch slot with their CDN URL. The honest number is "one
   line per museum", about 100 lines in total across seven. The claim
   appears in `v2/slides.md` (slide 5 bullet, slide 12 big number, the
   notes of both), `v1/slides.md`, `material.md` (three places), and
   `docs/outreach/code4lib-journal/article.md` line 190, which is the
   submitted article.
2. **The device reuses no connections.** `http_fetch.c` calls
   `esp_http_client_init` and `esp_http_client_cleanup` for every
   request; no `keep_alive`, no `esp_http_client_set_url`, anywhere in
   `components/` or `main/`. ESP-IDF's client keeps the connection open
   across requests on the same handle unless the server sends
   `Connection: close`. So "pays a TLS round trip per request" is true of
   the client, not of the protocol. Q6 exploits this.
3. **Re-probe of 2026-09-11.** Harvard `collections/top` is a valid P2
   Collection with one child; `collections/object` still returns HTTP
   500. Wellcome `presentation/collections` is a valid P3 Collection
   with five children; `collections/genres` and
   `collections/digitalcollections` still return 503. Neither root's
   items carry a `thumbnail`. Five weeks after the August probes.

### Q1. The finding, from a Presentation editor

**The question.** Presentation 3.0 says in its own scope statement that
discovery and harvesting are not what it provides. You spent two slides
and two days of probes establishing that a specification does not do
what it says it does not do. What is the actual finding, and why is it
not "p3a probed the wrong spec"?

**Say this.** You are right that the spec says so, and that is the
finding. I came in as a newcomer, and the newcomer's assumption, written
into my own design charter in May, was that Presentation Collections are
the natural carrier for browsing. The probes are the record of that
assumption failing, in the text and in the field. Two things for
editors. First, your own change log says paging was removed from 3.0
because it was never implemented, and that Collections became navigation
rather than discovery. My table is the outside view of the same fact: of
seven museums, two publish a Collection tree, and both have been broken
at enumeration depth since at least August, which tells me nothing in
production depends on them. Second, the family has a feed for harvesters
and a search for text inside one object, but no query surface for
"artworks in collection X, how many, give me 400 to 499". Every museum
already runs that index; its bespoke search API is that index. My
question is whether that boundary is deliberate.

**Class.**

- Presentation 3.0, Objectives and Scope: "Provision of metadata for
  harvesting and discovery is not directly supported." Search within the
  object is delegated to Content Search.
- Presentation 3.0 change log, entry 1.4.4: "As the Web Annotation Data
  Model defines the paging model, and Collection paging was neither
  implemented nor especially different from simply having a hierarchy of
  Collections, paging functionality was removed from the API." Issue
  #1343 called the removal a simplification "at no cost", and the log
  notes that Collections became "exclusively for navigation and not
  discovery". This is your strongest card. The editors said it first;
  quoting it turns "you probed the wrong spec" into agreement, and it
  belongs on the specification slide.
- "Discovery" means three things in this community. Change Discovery
  (the harvest feed), discovery for humans (how a person finds a IIIF
  resource from a web page), and what you mean: query in place. Name
  your sense in the first sentence so nobody talks past you.
- Change Discovery 1.0 lists as out of scope "the recommendation or
  creation of metadata search APIs or protocols". The one spec that
  could hold your gap declares it out of scope in writing.
- The Discovery group's published outputs are Change Discovery 1.0
  (2021) and Content State 1.0 (2022). Neither is a query surface. Ask
  whether anything since has been chartered.
- Who may be listening: Presentation 3.0's editors include Tom Crane,
  who built Wellcome's IIIF stack, and Robert Sanderson, whose Linked
  Art model is what the Rijksmuseum serves. If Crane is on the call the
  Wellcome 503 lands on him, and he is also the person most likely to
  say that Wellcome's catalogue API is the discovery layer by design.
  That is your conclusion stated as their architecture. Welcome it.
- Never say "Presentation failed". Say "Presentation kept its scope; the
  gap is above it."

**Deck changes.** Add the change-log sentence to the specification
slide. On the adoption slide, replace "7 and 9 August" with "August and
September" once you re-probe the week before.

### Q2. Thumbnails in Collections

**The question.** Your economics assume one manifest fetch per artwork
to reach an image identifier. But a Collection's items may carry a
`thumbnail` with an Image service, in 2.1 and 3.0. That gives you your
third primitive inline, with no manifest fetches. Did your probes check
whether Wellcome's or Harvard's Collection items carry thumbnails with
services? And if a museum published Collections that way, does "50 to
100 times" survive?

**Say this.** Fair, and the slide should say it. Presentation 3 says
items in a Collection should have a thumbnail, and recommends an Image
service on it, so a well-built Collection hands me the image id inline.
Two things keep the conclusion. In the field it did not happen: neither
Wellcome's nor Harvard's root carries thumbnails on its items, and the
children that would list artworks are down, so there was nothing to
measure. And thumbnails answer my third primitive only. They give no
totals and no offsets, and 3.0 has no paging, so a facet of 735,001
works is one document or a tree I walk end to end. With thumbnails the
multiplier drops from "a thousand manifests" to "walk the tree", roughly
ten fetches per thousand artworks, byte-competitive with the V&A's or
Wellcome's own search pages. So a museum that publishes hierarchy-paged
Collections with thumbnails and image services on every item satisfies
two of my three primitives, and I would write that adapter tomorrow.
Counts and offsets would still be missing.

**Class.**

- Presentation 3.0: "Collections or Manifests referenced in the items
  property must have the id, type and label properties. They should have
  the thumbnail property." On thumbnails: "It is recommended that a IIIF
  Image API service be available for images to enable manipulations such
  as resizing." The cookbook's Simple Collection recipe says items
  "should contain only necessary properties for presentation of the
  collection such as thumbnail". So the standard already prescribes the
  thing you ask for in checklist item 1, for this one document type.
- The service id in a thumbnail is your image identifier. Your template
  on it is legal on any Level 2 server.
- Estimate, labeled as such: an item with a thumbnail and service is
  about 500 bytes, so a 100-item sub-Collection is about 50 KB, and a
  1,024-artwork channel costs about 11 fetches and half a megabyte. That
  is inside the range of your bespoke pages (14 KB to 185 KB per 50 to
  100 records).
- Why museums do not do it: Collections are hand-curated navigation.
  The change log's "hierarchy instead of paging" assumes small sets. A
  735,001-item facet as a tree is not what anyone built.
- Your economics table should carry the qualifier "Collection items
  without thumbnails, as observed at both museums that publish
  Collections".

**Deck changes.** On the specification and economics slide, change
"about 1,000 manifest fetches" to "about 1,000 manifest fetches, since
no observed Collection carried thumbnails". Ask-back for the room: does
anyone publish a facet-sized Collection with thumbnails and image
services on every item?

### Q3. The client that never reads the menu

**The question.** You skip `info.json` and ask every server for
`!720,720`. A Level 0 static server, the cheapest way to publish IIIF,
serves only `max` and the sizes it lists, so your template 404s against
the servers a small institution can afford. And checklist item 6 asks
servers to "advertise only what is served", yet your client never reads
the advertisement. Why should a server keep `info.json` honest for a
client that does not negotiate, and how is "smallest patron" compatible
with ignoring the smallest servers?

**Say this.** Two concessions and one defense. First: `!w,h` is a Level
2 feature in both 2.1 and 3.0. A Level 0 static server serves `max` and
the sizes it lists, and my template fails there. All seven museums I
integrated run Level 1 or 2 dynamic servers, so I never hit it, but the
smallest patron should work with the smallest servers. The fix is cheap
and I intend to make it: try the template; on a 400 or 404, fetch
`info.json` once per host, pick the largest listed size that fits 720,
and remember it. One extra request per host, once, not one per image.
Second: a client that never reads the advertisement has no standing to
complain that it lies. My standing comes from the fallback: the moment I
read `info.json`, I am the client that believes it, and SMK's 400 shows
what happens then. The defense: at Level 2 the spec lets a client skip
negotiation, the request count matters at my scale, and in four months
of production the bet never lost. It is a bet. I will say so.

**Class.**

- Image API 2.1 compliance: Level 0 requires `full` size only. Level 1
  adds `w,`, `,h`, `pct:n`. Level 2 adds `w,h` and `!w,h`. `max` is
  optional at every level.
- Image API 3.0 compliance: Level 0 requires `max`. Level 1 adds `w,`,
  `,h`, `w,h`. Level 2 adds `pct:n` and `!w,h`. Upscaling with `^` is
  optional at every level.
- So `!720,720` is a Level 2 request under both versions. Your slide
  says "Image API 2, best fit"; say "Level 2" out loud once.
- Level 0 in practice: pre-generated tiles and sizes on a plain web
  server, S3, or GitHub Pages. `info.json` may list `sizes` with the
  available full-region dimensions. Reading it once per host and
  choosing the largest entry that fits 720 is the whole fallback. On a
  2.1 server without `sizes`, `full/full` returns the master; your
  16 MiB cap already guards that.
- The same read helps Level 2 servers: a deep-zoom stack such as Micrio
  may assemble an arbitrary size from tiles on the fly, while a listed
  size is a pre-rendered derivative. A client that asks for listed sizes
  is cheaper to serve. That is a politeness argument for the fallback,
  not only a compatibility one.
- Version note: the URL is identical in 2 and 3 for what you request.
  3.0's `^` prefix requests server-side upscaling; you never want it.
  Works smaller than 720 stay small and the device fits them to the
  panel without cropping; non-square works are letterboxed. You never
  use the `square` region because you do not crop art. Say that if
  anyone asks why not `square/720,720`.

**Deck changes.** Simplifications slide: "No `info.json`. `!720,720`
honored everywhere; zero misfires" becomes "No `info.json`. A Level 2
bet, won so far; fallback planned". Checklist item 6 stays; the fallback
is what gives you standing to keep it.

### Q4. 59 versus 4,700

**The question.** Cleveland and Minneapolis do no IIIF, so their 966
lines say nothing about IIIF. Chicago's 849 include a bisection built
around a search cap no discovery standard would have removed. And the
streaming download, the 16 MiB cap, and the rename-on-completion logic
that consume IIIF responses live in 994 core lines you did not count. Is
59 versus 4,700 honest, or a number chosen for the slide?

**Say this.** Mostly right, and the slide changes. The 59-line figure is
wrong: that file holds a User-Agent string and a URL encoder. The IIIF
part of each adapter is one line, a `snprintf` of the template, seven
times. The honest comparison is: seven IIIF museums, 3,740 lines to find
an artwork, one line each to fetch it. Cleveland and Minneapolis come out
of the numerator; they are evidence that without IIIF I also had to
write rendition logic, not evidence about IIIF. The core is not IIIF
either: the streaming, the cap and the rename live in a fetch helper
every source in the firmware uses, and the museum download loop is
scheduling. Chicago's bisection is my requirement, arbitrary offsets,
meeting their cap; a standard with cursors and totals would have
replaced it with a walk, which is the Rijksmuseum's cost, not zero. So
the shape holds: the standard made the pixel layer one line, and every
other line is discovery. The number on the slide was wrong and I fixed
it.

**Class.**

- Verified today: `artic.c` 849, `rijksmuseum.c` 645, `smithsonian.c`
  526, `mia.c` 491, `ham.c` 477, `cma.c` 475, `wellcome.c` 438, `smk.c`
  406, `vam.c` 399, `common.c` 59. Seven IIIF adapters: 3,740. Two CDN
  adapters: 966. Core: 994 (`art_institution.c` 302, refresh 269,
  resolve 198, download 138, rate limit 87).
- `build_iiif_url()` per adapter: 13 to 16 lines, Rijksmuseum 25 because
  it splits the `{micrio}|{hmo}` key. The template string is line 99 of
  `artic.c`, 83 of `ham.c`, 135 of `rijksmuseum.c`, 104 of
  `smithsonian.c`, 77 of `smk.c`, 89 of `vam.c`, 89 of `wellcome.c`.
- The better slide is two numbers: "1 line per museum turns an id into
  pixels" against "3,740 lines to find the id". It is punchier than 59
  and it is true.
- If pressed on fixed cost: some of each adapter is the cost of having
  any adapter (parse a page, walk a facet list, handle a key), and you
  have not measured that split. Concede it and say the variance is the
  rest.

**Deck changes.** Slide 5 bullet "Fifty-nine lines of shared C" becomes
"One line of C per museum". Slide 12 big numbers become "1" and "3,740"
with the seven-museum scope stated. Fix `material.md` and, when the
Code4Lib editors come back with revisions, the article's table row.

### Q5. Harvest at build time

**The question.** You say a microcontroller cannot be a harvester, so
Change Discovery is unusable. But you already harvest at build time: the
Rijksmuseum's 193 sets and Cleveland's vocabulary are baked into the
firmware from scans on your machine. Why not run the Change Discovery
harvest on your laptop, ship a compact per-museum index on the SD card,
and let the device query that? No cloud middleman. What breaks?

**Say this.** Nothing breaks technically, and the principle is not
absolute: the device already trusts GitHub Releases for firmware and
carries a copy of the Rijksmuseum's set list. A per-museum index on the
card is a legitimate design. Three things stopped me. Adoption: none of
the seven IIIF museums documents a Change Discovery feed for artworks.
The Rijksmuseum and Getty publish ActivityStreams over Linked Art
records, not IIIF manifests, so at six of seven there is nothing
standard to harvest. Size and freshness: the Rijksmuseum alone is
735,001 image-bearing objects, 35 MB of identifiers, and a snapshot goes
stale the day I ship it. The feed is built for incremental updates, but
applying them is harvesting again, so a harvester has to run somewhere
on a schedule, and that somewhere is the middleman, which would be me,
one person, and every device would depend on it. And it moves the truth:
today a channel is the museum's own facet, live; with a baked index it
is my snapshot of the museum. Where I did bake, it was 193 strings
blocked by CORS, not a discovery layer. If the community wanted a
harvested-index design, the right owner is an aggregator, and the thin
query surface I am asking for is exactly what an aggregator should
expose.

**Class.**

- Change Discovery 1.0: "The intended audience is other IIIF-aware
  systems that can leverage the content and APIs." Purpose: "enable the
  collaborative development of global or thematic search engines and
  portal applications." Out of scope: "the recommendation or creation of
  metadata search APIs or protocols." `totalItems` on the
  OrderedCollection is optional. Consumers "should start at the end and
  walk backwards". Every sentence assumes a crawler with storage.
- Your research notes say none of the seven advertises a feed, and mark
  it "UNVERIFIED beyond absence from their docs". Keep the hedge in your
  mouth: "none documents one". Do not say "none has one".
- Arithmetic: 735,001 records at 48 bytes is 35 MB, at 64 bytes 47 MB.
  Fits a card, not the 32 MB flash. The device's own hard ceiling, 64
  channels of 4,096 records, is 16 MB.
- The Europeana framing is worth saying: Europeana is the harvest-and-
  query aggregator the spec imagines, and it fails you at pixels, with
  thumbnails capped at 400 px. The museums kept the pixels and have no
  shared discovery. The two halves of your requirement live in different
  institutions.
- The precedents you can cite for "baking": the 193 Rijksmuseum sets
  (OAI-PMH without CORS) and Cleveland's vocabulary (no facet endpoint).
  Both are vocabularies, neither is an index.

**Deck changes.** None required. Add one line to the Rijksmuseum deep
dive notes: "not IIIF, but Linked Art, the standards path in the wider
sense". Someone will make the distinction if you do not.

### Q6. Whose multiplier is it?

**The question.** You say the device "pays a TLS round trip per
request" and that this makes the Presentation path 50 to 100 times more
expensive. Your fetch layer creates a new client and tears it down for
every request, so there is no connection reuse at all. Keep-alive alone
would turn a thousand manifest fetches into a handful of handshakes.
Isn't the multiplier a property of your client, and why should the spec
community fix a cost you chose?

**Say this.** Guilty on the client. p3a opens and closes a connection
per request, and ESP-IDF's HTTP client keeps a connection open if you
reuse the handle. I will fix that; it is cheap and it also speeds the
Rijksmuseum's three hops. Now what changes and what does not.
Handshakes: with reuse, a thousand manifests from one host cost a
handful, so the TLS cost mostly goes away. Round trips: still a thousand
sequential requests at a hundred to three hundred milliseconds each on
this radio, and still a thousand against the museum's quota. On
Harvard's 2,500-per-day key that is 40 percent of a day for one channel;
under Chicago's 60 per minute it is 17 minutes of wall clock. Bytes:
unchanged, 2.5 MB at Chicago's manifest size and over 100 MB at
Wellcome's, against 140 KB to 2 MB on the bespoke path. And the
specification ground is unchanged: at the end of the walk there are
still no counts and no offsets. So the slide should say "a round trip
per request", not "a TLS handshake per request". The 50 to 100 is a
request count, and request counts are what quotas meter.

**Class.**

- Verified: `http_fetch.c` calls `esp_http_client_init` and
  `esp_http_client_cleanup` around every request. No `keep_alive_*`
  config, no `esp_http_client_set_url`, nowhere in the firmware.
- ESP-IDF 5.5 docs: "If the server does not request to close the
  connection with the Connection: close header, the connection is not
  dropped but is instead kept open and used for further requests." And:
  "make as many requests as possible using the same handle instance."
  The `keep_alive_enable`, `keep_alive_idle`, `keep_alive_interval`,
  `keep_alive_count` fields are TCP keepalive probes, a different thing;
  HTTP persistence comes from handle reuse alone.
- The fix shape: one handle per host for the duration of a refresh or
  download pass, `esp_http_client_set_url` for each subsequent request,
  released when the pass ends or on any transport error. An idle TLS
  context holds tens of kilobytes, and you have a two-session budget, so
  reuse must be scoped to a pass, never left idle across museums.
- What reuse does not change: request count against per-IP and per-key
  quotas (Harvard 2,500 per day, Chicago 60 per minute, Smithsonian
  1,000 per hour), bytes over the radio and onto the card, and the
  absence of counts and offsets. Say those three every time.
- Not worth mentioning unless asked: HTTP/2 multiplexing is not in
  `esp_http_client`; TLS session resumption would shrink handshakes
  further but whether the HTTP client exposes it in 5.5 is unverified.

**Deck changes.** Simplifications slide notes and the economics notes:
replace "pays a TLS round trip per request" with "pays a round trip and
a quota unit per request". Decide before the call whether to implement
handle reuse; if you do, say "fixed since" instead of "will fix".

### Ask-backs collected from this round

- Is a query profile over Collections, or a small collection-search
  spec, anything the Discovery group has considered since Change
  Discovery 1.0?
- Does anyone publish a facet-sized Collection with thumbnails and image
  services on every item?
- Does anyone run a Level 0 IIIF service that a client like this should
  be tested against?
