# Library of Congress integration

**Status:** Deferred. Scaffolded 2026-05-13 (adapter, browse module,
dispatch entry), removed 2026-05-15 before any release shipped it
(commit `ebe793bc`).
**Scope:** Adding the Library of Congress (loc.gov) as a museum channel.

## What was deferred

A `loc` museum adapter alongside the nine shipped museums: device-side
refresh against the loc.gov JSON API, IIIF download from `tile.loc.gov`,
and a browser-side browse module.

## Why

The binding constraint is the 48-byte `iiif_key` slot in
`institution_channel_entry_t` (see
[`finalized-design.md` §4.2](../art-institutions/finalized-design.md)).
LoC IIIF identifiers are bimodal: 27 to 47 chars for the image-rich
subtrees (`service:pnp:`, `service:gmd:`, `service:mss:`,
`public:gdc:`), and 60 to 123 chars for newspapers, music, and
multi-segment archives. No facet separates the two shapes, so a format
filter mixes both, and only a prefix filter on the id itself keeps the
entries that fit.

The second problem is IIIF coverage. Many listing results carry only a
`_150px.jpg` storage thumbnail and no IIIF URL (8% of the photo format
surfaced IIIF in a 100-result sample; the Prints and Photographs
division surfaced none). Deriving an IIIF id from the thumbnail path
does not work in general. A refresh that pages until the cache is full
would issue roughly ten times AIC's request count for the same yield.

Together, coverage and metadata quality did not meet the bar for p3a.

## Key API facts

- Anonymous access with a polite `User-Agent`. No API key.
- Search: `GET https://www.loc.gov/search/?fo=json`, page size
  `c` in {25, 50, 100, 150}, 1-based page `sp`, `pagination.total` for
  the count. Path shortcuts (`/photos/`, `/maps/`, `/collections/{slug}/`)
  are equivalent to the `fa=` filters.
- Facet syntax is brittle and fails silently: the field name uses dashes
  (`original-format`, `online-format`, `partof`) and the value is the
  lowercase display title with spaces, verbatim
  (`fa=original-format:photo, print, drawing`). Check `facet_trail` in
  the response to confirm a filter applied.
- "Has IIIF" is detectable only by finding a URL starting with
  `https://tile.loc.gov/image-services/iiif/` in `image_url[]` or
  `resources[].image`.
- IIIF Image API v2 level 2 on `tile.loc.gov`;
  `/full/!720,720/0/default.jpg` returns a valid JPEG. Masters are large
  (5,000 to 8,500 px).
- About 640 collections, listed at `/collections/?fo=json&c=160`.
- Rate limit: none documented at investigation time; the 2026-09
  content-sources survey later measured a 20 req/min limit on the JSON
  API, with a one-hour block when exceeded.

## Revisit when

- The `iiif_key` slot grows (a cache-entry format change), or the
  adapter stores a short derived key and rebuilds the full id at
  download time, or
- A non-IIIF route proves viable: the 2026-09 survey found a ~1024 px
  `v.jpg` derivative inline in the search JSON, which would be a
  zero-hop, Cleveland-style fixed-rendition source that sidesteps both
  the id length and the IIIF coverage problems. The survey
  (`docs/content-sources-survey.md`) was retired in the 2026-10 docs
  cleanup and is in git history.

Any revival must respect the 20 req/min limit in both the browser
(term counts) and the device (refresh pages).

## Reference materials

The investigation (`REPORT.md`, probe scripts, parsed outputs) and the
removed adapter, design, and plan live in git history:
`docs/art-institutions/loc-investigation/` before the commit that
added this page, and `components/art_institution/museums/loc.c`,
`webui/museum/loc.js`, `docs/art-institutions/loc-channel-design.md`
at `ebe793bc^`.
