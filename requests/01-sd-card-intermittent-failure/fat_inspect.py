#!/usr/bin/env python3
"""fat_inspect.py -- inspect the p3a SD card's FAT32 volume through the
read-only raw-sector debug endpoints (CONFIG_P3A_SD_RAW_DEBUG build).

    python fat_inspect.py [--host p3a-fab.local] info
    python fat_inspect.py [--host ...] boot                  # MBR + BPB summary
    python fat_inspect.py [--host ...] dir p3a2/channel [--save NAME]
    python fat_inspect.py [--host ...] fatmirror             # FAT1 vs FAT2 diff
    python fat_inspect.py [--host ...] scan p3a2             # every dir under a path

`dir` walks the path from the root directory, dumps the directory's cluster
chain raw, parses every 32-byte entry (free, deleted, LFN, SFN) and reports
the anomalies that make FatFS lose files it just created:
  * a 0x00 ("end of directory") entry that is followed by live entries --
    FatFS's dir_find() stops at the first 0x00 while dir_alloc() skips past
    it, so anything allocated behind it is a phantom (create OK, open/rename
    ENOENT);
  * LFN sequences whose checksum does not match their SFN entry;
  * file entries whose cluster chain in the FAT is inconsistent with the
    recorded size (free/bad cluster inside the chain, chain too short/long).
It also fetches what FatFS enumerates (/api/debug/sd/ls) and lists the raw
entries FatFS cannot see.
"""
import argparse
import json
import struct
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent


class Card:
    def __init__(self, host):
        self.base = f"http://{host}"
        self.sector = 512
        self.fat_cache = {}
        info = self.get_json("/api/debug/sd/info")["data"]
        self.info = info
        if info.get("csd"):
            self.sector = int(info["csd"]["sector_size"])
            self.capacity = int(info["csd"]["capacity_sectors"])
        self.parse_volume()

    def get_json(self, path):
        with urllib.request.urlopen(self.base + path, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))

    def read(self, lba, count):
        """Raw sector read. Retries a short response: the debug endpoint's
        reads bypass FatFS's lock, so one can land while the card is still
        programming a FatFS write and time out (seen as a 0x107 with card
        state 'prg')."""
        out = bytearray()
        while count > 0:
            n = min(count, 512)
            url = f"{self.base}/api/debug/sd/read?lba={lba}&count={n}"
            data = b""
            for attempt in range(4):
                with urllib.request.urlopen(url, timeout=60) as r:
                    data = r.read()
                if len(data) == n * self.sector:
                    break
                print(f"  (short raw read at lba={lba} n={n}: {len(data)} bytes, retry {attempt + 1})", file=sys.stderr)
            if len(data) != n * self.sector:
                raise IOError(f"short raw read at lba={lba} n={n}: got {len(data)} bytes")
            out += data
            lba += n
            count -= n
        return bytes(out)

    def read_dir_chain(self, first, quick=True):
        """Directory read. With quick=True, read each cluster in 16-sector
        pieces and stop at the first all-zero 8 KB piece (dir_alloc fills the
        first free run, so nothing FatFS wrote can sit beyond such a gap)."""
        clusters, status = self.chain(first)
        data = bytearray()
        for c in clusters:
            lba = self.cluster_lba(c)
            done = 0
            while done < self.spc:
                n = min(16, self.spc - done)
                piece = self.read(lba + done, n)
                data += piece
                done += n
                if quick and not any(piece):
                    break
            if quick and len(data) % (self.spc * self.bps) != 0:
                break  # stopped early inside this cluster; later clusters are not needed
        return bytes(data), clusters, status

    # --- volume geometry ---------------------------------------------------
    def parse_volume(self):
        s0 = self.read(0, 1)
        self.part_start = 0
        self.mbr = None
        if s0[510:512] == b"\x55\xaa" and s0[0] not in (0xEB, 0xE9):
            parts = []
            for i in range(4):
                e = s0[0x1BE + 16 * i: 0x1BE + 16 * (i + 1)]
                ptype = e[4]
                start, size = struct.unpack("<II", e[8:16])
                if ptype:
                    parts.append((i, ptype, start, size))
            self.mbr = parts
            if parts:
                self.part_start = parts[0][2]
        b = self.read(self.part_start, 1)
        self.bpb_raw = b
        (bps, spc, rsvd, nfats, root_ent, tot16, media, fatsz16) = struct.unpack("<HBHBHHBH", b[11:24])
        tot32, = struct.unpack("<I", b[32:36])
        fatsz32, ext_flags, fs_ver, root_clus, fsinfo = struct.unpack("<IHHIH", b[36:50])
        self.bps = bps
        self.spc = spc
        self.rsvd = rsvd
        self.nfats = nfats
        self.fatsz = fatsz32 if fatsz16 == 0 else fatsz16
        self.total = tot32 if tot16 == 0 else tot16
        self.root_cluster = root_clus
        self.fsinfo_sector = fsinfo
        self.fs_type = b[82:90].decode("ascii", "replace").strip()
        self.label = b[71:82].decode("ascii", "replace").strip()
        self.fat_start = self.part_start + rsvd
        self.data_start = self.fat_start + nfats * self.fatsz
        self.cluster_bytes = bps * spc
        self.n_clusters = (self.total - rsvd - nfats * self.fatsz) // spc
        if bps != self.sector:
            print(f"NOTE: BPB bytes/sector {bps} != card sector {self.sector}", file=sys.stderr)

    def cluster_lba(self, c):
        return self.data_start + (c - 2) * self.spc

    def fat_entry(self, c, fat_index=0):
        off = c * 4
        sec = off // self.bps
        key = (fat_index, sec)
        if key not in self.fat_cache:
            self.fat_cache[key] = self.read(self.fat_start + fat_index * self.fatsz + sec, 1)
        v, = struct.unpack_from("<I", self.fat_cache[key], off % self.bps)
        return v & 0x0FFFFFFF

    def chain(self, first, limit=1_000_000):
        out = []
        c = first
        seen = set()
        status = "eoc"
        while True:
            if c < 2 or c >= self.n_clusters + 2:
                status = f"bad-cluster-{c:#x}"
                break
            if c in seen:
                status = "loop"
                break
            seen.add(c)
            out.append(c)
            nxt = self.fat_entry(c)
            if nxt >= 0x0FFFFFF8:
                break
            if nxt == 0:
                status = "free-in-chain"
                break
            if nxt == 0x0FFFFFF7:
                status = "bad-in-chain"
                break
            c = nxt
            if len(out) >= limit:
                status = "limit"
                break
        return out, status

    def read_chain(self, first):
        clusters, status = self.chain(first)
        data = bytearray()
        for c in clusters:
            data += self.read(self.cluster_lba(c), self.spc)
        return bytes(data), clusters, status


# --- directory parsing -------------------------------------------------------

def lfn_checksum(sfn11):
    s = 0
    for ch in sfn11:
        s = ((s & 1) << 7) + (s >> 1) + ch
        s &= 0xFF
    return s


def parse_dir(raw):
    """Return (entries, anomalies). entries: list of dicts with index, kind, name..."""
    entries = []
    anomalies = []
    lfn_parts = {}
    lfn_sum = None
    lfn_start = None
    n = len(raw) // 32
    first_zero = None
    live_after_zero = 0
    for i in range(n):
        e = raw[i * 32:(i + 1) * 32]
        c0 = e[0]
        attr = e[11]
        if c0 == 0x00:
            if all(b == 0 for b in e):
                kind = "zero"
            else:
                kind = "zero-first-byte-nonzero-tail"
                anomalies.append(f"entry {i}: first byte 0x00 but tail not zero")
            if first_zero is None:
                first_zero = i
            entries.append({"i": i, "kind": kind})
            if lfn_parts:
                anomalies.append(f"entry {i}: LFN chain started at {lfn_start} ends in a zero entry")
                lfn_parts, lfn_sum, lfn_start = {}, None, None
            continue
        if first_zero is not None:
            live_after_zero += 1
        if c0 == 0xE5:
            entries.append({"i": i, "kind": "deleted", "attr": attr,
                            "sfn": e[0:11].hex()})
            if lfn_parts:
                anomalies.append(f"entry {i}: LFN chain started at {lfn_start} ends in a deleted entry")
                lfn_parts, lfn_sum, lfn_start = {}, None, None
            continue
        if attr & 0x3F == 0x0F:
            seq = c0 & 0x1F
            last = bool(c0 & 0x40)
            chk = e[13]
            name = e[1:11] + e[14:26] + e[28:32]
            if last or not lfn_parts:
                lfn_parts, lfn_sum, lfn_start = {}, chk, i
            elif chk != lfn_sum:
                anomalies.append(f"entry {i}: LFN checksum {chk:#04x} != chain {lfn_sum:#04x}")
            lfn_parts[seq] = name
            entries.append({"i": i, "kind": "lfn", "seq": seq, "last": last, "chk": chk})
            continue
        # SFN entry
        sfn = e[0:11]
        name8 = sfn[0:8].decode("ascii", "replace").rstrip()
        ext = sfn[8:11].decode("ascii", "replace").rstrip()
        short = name8 + ("." + ext if ext else "")
        hi, = struct.unpack_from("<H", e, 20)
        lo, = struct.unpack_from("<H", e, 26)
        size, = struct.unpack_from("<I", e, 28)
        first = (hi << 16) | lo
        long_name = None
        if lfn_parts:
            calc = lfn_checksum(sfn)
            if calc != lfn_sum:
                anomalies.append(f"entry {i}: SFN '{short}' checksum {calc:#04x} != LFN chain {lfn_sum:#04x} (chain at {lfn_start})")
            else:
                seqs = sorted(lfn_parts)
                if seqs != list(range(1, len(seqs) + 1)):
                    anomalies.append(f"entry {i}: LFN sequence for '{short}' is {seqs}")
                buf = b"".join(lfn_parts[s] for s in seqs)
                try:
                    u = buf.decode("utf-16-le", "replace")
                except Exception:
                    u = "?"
                long_name = u.split("\x00")[0].rstrip("￿")
            lfn_parts, lfn_sum, lfn_start = {}, None, None
        entries.append({"i": i, "kind": "dir" if attr & 0x10 else ("vol" if attr & 0x08 else "file"),
                        "attr": attr, "short": short, "name": long_name or short,
                        "first": first, "size": size})
    if first_zero is not None and live_after_zero:
        anomalies.append(
            f"PHANTOM ZONE: first 0x00 entry at index {first_zero} but {live_after_zero} non-zero "
            f"entries follow it (FatFS lookup stops at {first_zero}, allocation continues past it)")
    return entries, anomalies


def walk(card, path):
    """Follow a slash path from the root directory; return (dir_raw, clusters, status, breadcrumbs)."""
    parts = [p for p in path.strip("/").split("/") if p]
    cluster = card.root_cluster
    crumbs = []
    for p in parts:
        raw, clusters, status = card.read_dir_chain(cluster, quick=True)
        entries, _ = parse_dir(raw)
        match = None
        for e in entries:
            if e["kind"] == "dir" and (e["name"].lower() == p.lower() or e["short"].lower() == p.lower()):
                match = e
                break
        if not match:
            raise SystemExit(f"path component '{p}' not found (as a directory) in cluster {cluster}")
        crumbs.append((p, match["first"]))
        cluster = match["first"]
    raw, clusters, status = card.read_chain(cluster)
    return raw, clusters, status, crumbs, cluster


def cmd_info(card, a):
    print(json.dumps(card.info, indent=1))


def cmd_boot(card, a):
    print(f"MBR partitions: {card.mbr}")
    print(f"partition start LBA: {card.part_start}")
    print(f"fs_type='{card.fs_type}' label='{card.label}'")
    print(f"bytes/sector={card.bps} sectors/cluster={card.spc} cluster={card.cluster_bytes} B")
    print(f"reserved={card.rsvd} fats={card.nfats} fat_size={card.fatsz} sectors ({card.fatsz * card.bps / 1e6:.1f} MB each)")
    print(f"total sectors={card.total} clusters={card.n_clusters} root_cluster={card.root_cluster} fsinfo_sector={card.fsinfo_sector}")
    print(f"fat_start={card.fat_start} data_start={card.data_start}")
    fsi = card.read(card.part_start + card.fsinfo_sector, 1)
    lead, = struct.unpack_from("<I", fsi, 0)
    sig, free, nxt = struct.unpack_from("<III", fsi, 484)
    print(f"FSInfo: lead={lead:#x} sig={sig:#x} free_count={free} next_free={nxt}")


def check_file_chain(card, e):
    if e["first"] == 0:
        return "no-cluster" if e["size"] else "empty-ok"
    clusters, status = card.chain(e["first"], limit=200000)
    need = (e["size"] + card.cluster_bytes - 1) // card.cluster_bytes if e["kind"] == "file" else None
    if status != "eoc":
        return f"chain {status} after {len(clusters)} clusters"
    if need is not None and len(clusters) != max(need, 1):
        return f"chain {len(clusters)} clusters but size needs {need}"
    return "ok"


def cmd_dir(card, a):
    raw, clusters, status, crumbs, cluster = walk(card, a.path)
    print(f"path /{a.path.strip('/')} -> cluster {cluster}; crumbs={crumbs}")
    print(f"directory chain: {len(clusters)} clusters {clusters[:16]}{'...' if len(clusters) > 16 else ''} status={status}")
    print(f"directory bytes: {len(raw)} = {len(raw) // 32} entries")
    if a.save:
        out = HERE / "logs" / a.save
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(raw)
        print(f"raw directory saved to {out}")
    entries, anomalies = parse_dir(raw)
    kinds = {}
    for e in entries:
        kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
    print(f"entry kinds: {kinds}")
    live = [e for e in entries if e["kind"] in ("file", "dir", "vol")]
    print(f"live entries: {len(live)}")
    last_nonzero = max((e["i"] for e in entries if e["kind"] != "zero"), default=-1)
    print(f"last non-zero entry index: {last_nonzero}")
    if a.verbose:
        for e in entries:
            if e["kind"] == "zero":
                continue
            print("  ", e)
    print("--- live entries ---")
    for e in live:
        chk = check_file_chain(card, e) if a.chains else ""
        print(f"  [{e['i']:5d}] {e['kind']:4s} {e['name']:40s} short={e['short']:13s} first={e['first']:<8d} size={e['size']:<10d} {chk}")
    print("--- anomalies ---")
    if not anomalies:
        print("  none")
    for x in anomalies:
        print("  " + x)
    # Compare with what FatFS sees
    vfs_path = "/sdcard/" + a.path.strip("/")
    try:
        ls = card.get_json(f"/api/debug/sd/ls?path={urllib.request.quote(vfs_path)}")["data"]
        seen = {e["name"].lower() for e in ls.get("entries", [])}
        print(f"--- FatFS enumerates {ls.get('count')} entries (readdir_end_errno={ls.get('readdir_end_errno')}, opendir_errno={ls.get('opendir_errno')}) ---")
        hidden = [e for e in live if e["name"].lower() not in seen and e["kind"] != "vol"]
        if hidden:
            print(f"  {len(hidden)} raw live entries NOT visible to FatFS:")
            for e in hidden:
                print(f"    [{e['i']:5d}] {e['name']} size={e['size']} first={e['first']}")
        else:
            print("  every raw live entry is visible to FatFS")
        extra = seen - {e["name"].lower() for e in live}
        if extra:
            print(f"  FatFS lists names not found raw: {sorted(extra)[:20]}")
    except Exception as ex:
        print(f"  (ls comparison failed: {ex})")


def cmd_fatmirror(card, a):
    if card.nfats < 2:
        print("single FAT, nothing to compare")
        return
    diffs = 0
    step = 512
    for sec in range(0, card.fatsz, step):
        n = min(step, card.fatsz - sec)
        f1 = card.read(card.fat_start + sec, n)
        f2 = card.read(card.fat_start + card.fatsz + sec, n)
        if f1 != f2:
            for k in range(n):
                a1 = f1[k * card.bps:(k + 1) * card.bps]
                a2 = f2[k * card.bps:(k + 1) * card.bps]
                if a1 != a2:
                    diffs += 1
                    if diffs <= 40:
                        first_cluster = (sec + k) * card.bps // 4
                        nd = sum(1 for j in range(0, card.bps, 4) if a1[j:j + 4] != a2[j:j + 4])
                        print(f"  FAT sector {sec + k} (clusters {first_cluster}..{first_cluster + card.bps // 4 - 1}): {nd} entries differ")
        print(f"\r  compared {sec + n}/{card.fatsz} FAT sectors, {diffs} differ", end="", file=sys.stderr)
    print(file=sys.stderr)
    print(f"FAT1 vs FAT2: {diffs} differing sectors out of {card.fatsz}")


def cmd_scan(card, a):
    """Recursively parse every directory under a path (quick reads), report
    anomalies, junk-looking entries, and per-tree totals."""
    todo = [(a.path.strip("/"), None)]
    seen = set()
    n_dirs = n_files = n_bytes = n_anom = 0
    junk_dirs = []
    # resolve the start directory's cluster by walking once
    _, _, _, _, start_cluster = walk(card, todo[0][0])
    todo[0] = (todo[0][0], start_cluster)
    while todo:
        p, cluster = todo.pop(0)
        if cluster in seen:
            continue
        seen.add(cluster)
        raw, clusters, status = card.read_dir_chain(cluster, quick=True)
        entries, anomalies = parse_dir(raw)
        live = [e for e in entries if e["kind"] in ("file", "dir")]
        # junk heuristic: live names with characters outside printable ASCII,
        # or 'vol'/'zero-first-byte-nonzero-tail' kinds, mean foreign data
        junk = sum(1 for e in entries if e["kind"] in ("vol", "zero-first-byte-nonzero-tail")
                   or (e["kind"] in ("file", "dir") and any(ord(ch) < 32 or ord(ch) > 126 for ch in e["name"])))
        n_dirs += 1
        files = [e for e in live if e["kind"] == "file"]
        n_files += len(files)
        n_bytes += sum(e["size"] for e in files)
        flag = ""
        if anomalies:
            flag += "ANOMALY "
            n_anom += 1
        if junk:
            flag += f"JUNK({junk}) "
            junk_dirs.append(p)
        if flag or a.verbose:
            print(f"{flag}/{p}: cluster={cluster} chain={len(clusters)}({status}) read={len(raw)}B entries={len(entries)} live={len(live)} files={len(files)}")
            for x in anomalies:
                print("    " + x)
        for e in live:
            if e["kind"] == "dir" and e["name"] not in (".", "..") and e["first"] >= 2:
                todo.append((p + "/" + e["name"], e["first"]))
        print(f"\r  dirs={n_dirs} files={n_files} bytes={n_bytes / 1e6:.1f}MB", end="", file=sys.stderr)
    print(file=sys.stderr)
    print(f"TOTAL under /{a.path.strip('/')}: dirs={n_dirs} files={n_files} bytes={n_bytes} ({n_bytes / 1e6:.1f} MB) anomaly_dirs={n_anom} junk_dirs={len(junk_dirs)}")
    for d in junk_dirs:
        print(f"  junk in: /{d}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="p3a-fab.local")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("info").set_defaults(fn=cmd_info)
    sub.add_parser("boot").set_defaults(fn=cmd_boot)
    d = sub.add_parser("dir")
    d.add_argument("path")
    d.add_argument("--save")
    d.add_argument("--verbose", action="store_true")
    d.add_argument("--chains", action="store_true", help="follow each file's FAT chain and check it against its size")
    d.set_defaults(fn=cmd_dir)
    sub.add_parser("fatmirror").set_defaults(fn=cmd_fatmirror)
    s = sub.add_parser("scan")
    s.add_argument("path")
    s.add_argument("--verbose", action="store_true")
    s.set_defaults(fn=cmd_scan)
    a = ap.parse_args()
    card = Card(a.host)
    a.fn(card, a)


if __name__ == "__main__":
    main()
