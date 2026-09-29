"""Set each v3 slide's [~m:ss] mark from its spoken word count (140 wpm) and refresh the word/minute totals in README.md. Run from anywhere: python set_durations.py"""
import io, os, re, sys

BASE = os.path.dirname(os.path.abspath(__file__)) + "/"
SLIDES = BASE + "v3/slides.md"
WPM = 140.0

s = io.open(SLIDES, encoding="utf-8").read()

# split on slide separators (a line that is exactly ---), skipping the front matter
parts = re.split(r"^---\s*$", s, flags=re.M)
# parts[0] is empty, parts[1] is front matter, slides start at parts[2]
slides = parts[2:]

def spoken_words(note):
    body = note
    # drop everything from "If asked:" to the end
    i = body.find("If asked:")
    if i >= 0:
        body = body[:i]
    # drop the "[if silence...]" question list on the last slide
    j = body.find("[if silence")
    if j >= 0:
        body = body[:j]
    # drop the duration mark
    body = re.sub(r"^\[~[^\]]*\]\s*", "", body.strip())
    # drop bracketed stage cues
    body = re.sub(r"\[[^\]]*\]", " ", body)
    return len(re.findall(r"[A-Za-z0-9'’]+(?:[-.,][A-Za-z0-9'’]+)*", body))

def fmt(seconds):
    q = int(round(seconds / 15.0)) * 15
    q = max(q, 30)
    return f"{q // 60}:{q % 60:02d}"

rows = []
total_s = 0
new_parts = parts[:2]
for k, sl in enumerate(slides, start=1):
    m = re.search(r"<!--\s*\n(.*?)-->", sl, flags=re.S)
    if not m:
        print("no notes on slide", k); sys.exit(1)
    note = m.group(1)
    w = spoken_words(note)
    sec = w / WPM * 60
    total_s += sec
    title = re.search(r"^# (.+)$", sl, flags=re.M)
    title = title.group(1) if title else "?"
    rows.append((k, w, fmt(sec), title))
    new_note = re.sub(r"^(\s*)\[~[^\]]*\]", lambda mm: f"{mm.group(1)}[~{fmt(sec)}]", note, count=1)
    sl = sl.replace(note, new_note, 1)
    new_parts.append(sl)

# re.split removed the separator text; rebuild with blank lines around each separator
body = "\n\n---\n\n".join(p.strip("\n") for p in new_parts[2:])
out = "---\n" + new_parts[1].strip("\n") + "\n---\n\n" + body + "\n"
io.open(SLIDES, "w", encoding="utf-8", newline="\n").write(out)

print(f"{'#':>2}  {'words':>5}  {'time':>5}  title")
for k, w, t, title in rows:
    print(f"{k:>2}  {w:>5}  {t:>5}  {title}")
tot_words = sum(r[1] for r in rows)
print(f"total words {tot_words}, about {total_s/60:.1f} minutes at {WPM:.0f} wpm")

# ---------------------------------------------------------------- README
# One-time section additions were applied on the first run; now only refresh the numbers.
p = BASE + "README.md"
r = io.open(p, encoding="utf-8").read()
minutes = int(round(total_s / 60))
pat = re.compile(r"about [\d,]+ words, about \d+ minutes")
n = len(pat.findall(r))
r = pat.sub(f"about {tot_words:,} words, about {minutes} minutes", r)
io.open(p, "w", encoding="utf-8", newline="\n").write(r)
print(f"README numbers refreshed in {n} places")
