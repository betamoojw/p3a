# Klipy API notes

**Status:** shipped. The integration lives in `components/klipy/` (trending,
search, and category channels for GIFs and stickers; BYOK key from
partner.klipy.com). This page is the API reference the component was built
against, plus the quirks the code depends on. API behavior was verified live on
2026-07-01 with a test key, and the resolve route was updated 2026-08-14.

## 1. The Klipy API

### 1.1 Access model

- **Base URL:** `https://api.klipy.com/api/v1/{API_KEY}/…`. The API key is a
  **path segment** (contrast Giphy's `?api_key=`).
- **Keys:** issued at `partner.klipy.com`. Test key = 100 req/hr (confirmed via
  `x-ratelimit-limit: 100`); production key = unlimited per Klipy's docs.
- **Rate-limit headers:** `x-ratelimit-limit` and `x-ratelimit-remaining` on
  success; no `-reset` header was observed.
- **ToS:** Klipy's Tenor-migration guide asks for visible "KLIPY"
  branding/attribution.
- **CDN:** media is served from `static.klipy.com`, path shape
  `…/ii/{32-hex}/{xx}/{yy}/{8-char-token}.{ext}`. The token is **random per
  format** and cannot be derived from the item id or slug (see section 2).

### 1.2 Endpoints

GIF product shown; `stickers`, `clips`, and `memes` share the shape with a
different prefix. p3a uses `gifs` and `stickers`.

| Method | Path | Purpose |
|---|---|---|
| GET | `gifs/trending?page=&per_page=` | Trending feed |
| GET | `gifs/search?q=&page=&per_page=` | Search |
| GET | `gifs/items?ids={id}[,{id}…]` | Resolve items by numeric id (used by p3a, see section 2) |
| GET | `gifs/{id-or-slug}` | Resolve a single item. **Returns HTTP 403 for our key tier since about 2026-08**; do not use |
| GET | `gifs/categories` | Curated category list, about 35 `{category, query, preview_url}` entries |
| GET | `gifs/recent/{customer_id}` | Per-user recents (personalization/ads) |
| POST | `gifs/view/{slug}` body `{customer_id}` | View tracking |
| POST | `gifs/share/{slug}` body `{customer_id}` | Share tracking |
| POST | `gifs/report/{slug}` | Content report |
| DELETE | `gifs/recent/{customer_id}?slug=` | Remove from recents |

**Params:** `q`, `page`, `per_page` (default 24, **min 8, max 50**), `locale`,
and `rating` (`g`/`pg`/`pg-13`/`r`). Pagination is page number plus
`has_next` (no cursor). Pages 1 to 50 at `per_page=50` were full, so at least
2,500 items are reachable per feed. Ads are opt-in: no `type:"ad"` items come
back without ad parameters.

### 1.3 Response envelope

```json
{ "result": true,
  "data": {
    "data": [ /* items */ ],
    "current_page": 1,
    "per_page": 24,
    "has_next": true,
    "meta": { "item_min_width": 80, "ad_max_resize_percent": 10 } } }
```

`items?ids=` returns the same envelope, with the requested items in `data.data`.

### 1.4 Item and media schema (GIF and sticker)

```json
{ "id": 6587795917955715,          // compact numeric (uint64)
  "slug": "hello-july-july-1",
  "title": "…",
  "type": "gif",                    // "gif" | "sticker" | "clip" | "ad"
  "tags": [],                       // present but often empty
  "blur_preview": "data:image/jpeg;base64,…",   // tiny JPEG placeholder
  "file": {
    "hd": { "webp": {"url","width","height","size"},
            "gif":  {"url","width","height","size"},
            "mp4":  {"url","width","height","size"} },   // stickers: no mp4
    "md": { … }, "sm": { … }, "xs": { … } } }
```

- WebP renditions are **animated with alpha** (VP8X), for GIFs and stickers
  alike. GIF renditions are GIF89a.
- The four tiers are **not** a strict resolution ladder: for
  `hello-july-july-1`, `md.webp` (640²) is larger than `hd.webp` (498²).
  **Select renditions by the explicit `width`/`height` fields, never by tier
  name.** `klipy_pick_rendition()` in `klipy_api.c` does this.
- GIF payloads run up to about 10x the WebP for the same frame, so WebP is the
  default format.

Observed sizes for `hello-july-july-1`:

| tier | webp | gif | mp4 |
|---|---|---|---|
| hd | 498² / 144 KB | 498² / 1.3 MB | 640² / 436 KB |
| md | 640² / 413 KB | 640² / 716 KB | 640² / 436 KB |
| sm | 220² / 79 KB | 220² / 100 KB | 320² / 108 KB |
| xs | 90² / 20 KB | 90² / 17 KB | 150² / 34 KB |

Content tops out around 480 to 640 px.

### 1.5 Clip schema (flat, not used by p3a)

```json
{ "type": "clip", "slug": "good-morning-57", "url": "https://klipy.com/…",
  "file": { "mp4":"…","gif":"…","webp":"…" },
  "file_meta": { "mp4": {"width":854,"height":480,"size":…},
                 "gif": {"width":320,"height":180,"size":…},
                 "webp":{"width":320,"height":180,"size":…} } }
```

### 1.6 Error envelope

```json
{ "result": false, "errors": { "message": ["…"] } }
```

- **Invalid API key → HTTP 404** (not 401/403), message
  `"The provided API key is invalid: […]"`. The auth latch in `klipy_api.c`
  therefore keys off a 404 on an otherwise-valid route, not off 401/403.
- Bad slug → HTTP 404, message `"404 Not Found"`.
- The invalid-key error body **echoes the API key**. Never log full error
  bodies.

## 2. Opaque CDN URLs: resolve by id at download time

Giphy entries store a short id and rebuild the CDN URL at play time. Klipy CDN
URLs are random per-format tokens (section 1.1) about 80 characters long, so
they can neither be rebuilt nor stored in the 64-byte channel entry.

The shipped solution: the channel entry stores the 8-byte numeric `id`. At
first download, `klipy_download.c` calls `GET {product}/items?ids={id}`, takes
the first item in `data.data`, picks the rendition by dimensions, and streams
the file to the sharded vault under `/sdcard/p3a/klipy/{gif|sticker}/`. That is
one small request per artwork's first download; after that the file plays from
the SD card.

The resolve originally used `GET {product}/{id}`. Klipy revoked that route for
our key tier around 2026-08 (HTTP 403 "You do not have permission to perform
this action"); `items?ids=` returns the same item schema and still works.
