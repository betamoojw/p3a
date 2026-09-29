#!/usr/bin/env python3
"""soak_monitor.py -- overnight monitor for the SD self-repair build.

    python soak_monitor.py [--host p3a-fab.local] [--interval-min 30] [--hours 10]

Every interval it records to logs/soak/<start>.jsonl:
  * /status: uptime (reboot detection), heap, sd_card_failed, sd_repair counters
  * FAT drift: per-512-sector-chunk SHA-256 of FAT1 and FAT2 versus the first
    snapshot, so a new misplaced 16 KB block landing on the FAT while the device
    is powered shows up as a changed chunk that FatFS did not write (FatFS
    writes change FAT1 and FAT2 together; a block that changes one copy only,
    or turns a plausible chunk into junk, is card-inflicted)
  * root directory drift: raw hash of the /p3a2 and /p3a2/channel directory
    clusters (should only change when files come and go)
Needs the CONFIG_P3A_SD_RAW_DEBUG build. Reads are retried; an unreachable
device is logged and skipped, never fatal.
"""
import argparse
import datetime as dt
import hashlib
import json
import struct
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from fat_inspect import Card, parse_dir  # noqa: E402


def now():
    return dt.datetime.now().isoformat(timespec="seconds")


def plausible_chunk(data, n_clusters):
    vals = struct.unpack(f"<{len(data) // 4}I", data)
    bad = 0
    for v in vals:
        v &= 0x0FFFFFFF
        if v == 0 or v >= 0x0FFFFFF7 or 2 <= v < n_clusters + 2:
            continue
        bad += 1
    return bad


def fat_hashes(card, copy):
    out = []
    base = card.fat_start + copy * card.fatsz
    for sec in range(0, card.fatsz, 512):
        n = min(512, card.fatsz - sec)
        d = card.read(base + sec, n)
        out.append((hashlib.sha256(d).hexdigest()[:16], plausible_chunk(d, card.n_clusters)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="p3a-fab.local")
    ap.add_argument("--interval-min", type=float, default=30)
    ap.add_argument("--hours", type=float, default=10)
    a = ap.parse_args()

    out_dir = HERE / "logs" / "soak"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / (dt.datetime.now().strftime("%Y%m%d-%H%M%S") + ".jsonl")
    print(f"writing {out}")

    baseline = None
    last_uptime = None
    deadline = time.time() + a.hours * 3600
    while True:
        rec = {"ts": now()}
        try:
            card = Card(a.host)
            st = card.get_json("/status")["data"]
            rec["uptime_ms"] = st.get("uptime_ms")
            rec["heap_free"] = st.get("heap_free")
            rec["sd_card_failed"] = st.get("sd_card_failed")
            rec["sd_repair"] = st.get("sd_repair")
            rec["fw"] = st.get("fw", {}).get("version")
            if last_uptime is not None and rec["uptime_ms"] is not None and rec["uptime_ms"] < last_uptime:
                rec["REBOOT_DETECTED"] = True
            last_uptime = rec["uptime_ms"]

            f1 = fat_hashes(card, 0)
            f2 = fat_hashes(card, 1)
            rec["fat_chunks"] = len(f1)
            rec["fat_mirror_diff_chunks"] = [i for i in range(len(f1)) if f1[i][0] != f2[i][0]]
            rec["fat1_junk_chunks"] = [i for i in range(len(f1)) if f1[i][1] > 0]
            rec["fat2_junk_chunks"] = [i for i in range(len(f2)) if f2[i][1] > 0]
            if baseline is None:
                baseline = (f1, f2)
                rec["baseline"] = True
            else:
                rec["fat1_changed_vs_baseline"] = [i for i in range(len(f1)) if f1[i][0] != baseline[0][i][0]]
                rec["fat2_changed_vs_baseline"] = [i for i in range(len(f2)) if f2[i][0] != baseline[1][i][0]]
                # A chunk that changed in exactly one copy is not a FatFS write.
                one_sided = sorted(set(rec["fat1_changed_vs_baseline"]) ^ set(rec["fat2_changed_vs_baseline"]))
                rec["fat_one_sided_changes"] = one_sided
                new_junk1 = [i for i in rec["fat1_junk_chunks"] if baseline[0][i][1] == 0]
                new_junk2 = [i for i in rec["fat2_junk_chunks"] if baseline[1][i][1] == 0]
                rec["NEW_FAT_JUNK"] = {"fat1": new_junk1, "fat2": new_junk2} if (new_junk1 or new_junk2) else None

            # directory sanity: root and channel parse clean?
            from fat_inspect import walk
            for name in ("p3a2", "p3a2/channel"):
                raw, clusters, status, _, _ = walk(card, name)
                entries, anomalies = parse_dir(raw)
                rec[f"dir_{name.replace('/', '_')}"] = {
                    "live": sum(1 for e in entries if e["kind"] in ("file", "dir")),
                    "anomalies": anomalies,
                    "hash": hashlib.sha256(raw).hexdigest()[:16],
                }
        except Exception as ex:
            rec["error"] = f"{type(ex).__name__}: {ex}"
        with out.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        flag = ""
        if rec.get("REBOOT_DETECTED"):
            flag += " REBOOT"
        if rec.get("NEW_FAT_JUNK"):
            flag += " NEW_FAT_JUNK"
        if rec.get("fat_one_sided_changes"):
            flag += f" one_sided={len(rec['fat_one_sided_changes'])}"
        sr = rec.get("sd_repair") or {}
        print(f"{rec['ts']} uptime={rec.get('uptime_ms')} repairs_boot={sr.get('dir_repairs_boot')} total={sr.get('dir_repairs_total')} "
              f"failed={rec.get('sd_card_failed')} mirror_diff_chunks={len(rec.get('fat_mirror_diff_chunks', []))} "
              f"err={rec.get('error')}{flag}", flush=True)
        if time.time() > deadline:
            break
        time.sleep(a.interval_min * 60)


if __name__ == "__main__":
    main()
