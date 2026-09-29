#!/usr/bin/env python3
"""clean_false_404.py -- remove the false .404 markers left by the first
overnight build of the self-repair (request 01).

That build returned ESP_ERR_NOT_FOUND from fs_atomic after a directory repair;
the download manager treats that code as HTTP 404 and writes
"<artwork>.404" next to the artwork, so the one download that triggered each
repair got tombstoned inside the freshly recreated directory. Markers only
disappear through age-based eviction, so this removes them explicitly.

Scope: every recreated directory (mapped back from lost/<path_with_underscores>-<n>),
markers with mtime on or after --since (default 2026-09-28T19:00). Needs the
CONFIG_P3A_SD_RAW_DEBUG build (GET /api/debug/sd/{ls,unlink}).

    python clean_false_404.py [--host p3a-fab.local] [--since 2026-09-28T19:00] [--dry-run]
"""
import argparse
import datetime as dt
import json
import urllib.request


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="p3a-fab.local")
    ap.add_argument("--since", default="2026-09-28T19:00")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    base = f"http://{a.host}"
    since = dt.datetime.fromisoformat(a.since).timestamp()

    def get(path):
        with urllib.request.urlopen(base + path, timeout=30) as r:
            return json.load(r)["data"]

    def ls(p):
        return get(f"/api/debug/sd/ls?path={urllib.request.quote(p)}")

    lost = ls("/sdcard/p3a2/lost")["entries"]
    removed = kept = 0
    for e in lost:
        stem = e["name"].rsplit("-", 1)[0]
        if "_" not in stem:
            continue  # first-night naming (basename only) cannot be mapped back
        orig = "/sdcard/p3a2/" + stem.replace("_", "/")
        try:
            d = ls(orig)
        except Exception as ex:
            print(f"  skip {orig}: {ex}")
            continue
        for x in d.get("entries", []):
            if not x["name"].endswith(".404"):
                continue
            if x.get("mtime", 0) < since:
                kept += 1
                continue
            full = f"{orig}/{x['name']}"
            if a.dry_run:
                print(f"  would unlink {full}")
                removed += 1
                continue
            r = get(f"/api/debug/sd/unlink?path={urllib.request.quote(full)}")
            if r.get("unlinked"):
                removed += 1
            else:
                print(f"  unlink failed {full}: errno={r.get('errno')}")
    print(f"{'would remove' if a.dry_run else 'removed'} {removed} false markers, kept {kept} older ones")


if __name__ == "__main__":
    main()
