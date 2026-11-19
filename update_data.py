"""Refresh videos.json from the lab's YouTube channel and (best effort) data/metrics.json
from Google Scholar. Run daily by .github/workflows/update-data.yml. Standard library only."""
import json, re, sys, datetime, pathlib, urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent
CHANNEL_ID = "UCRGRrIHFWcaugICQ1GbqotQ"          # youtube.com/@TufanKumbasar
SCHOLAR_ID = "i2hguUsAAAAJ"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9"}

CATEGORY_RULES = [  # first match wins; edit freely
    ("Aerial robotics", r"drone|quadcopter|quadrotor|uav|crazyflie|aerial|flight"),
    ("Autonomous driving", r"driving|vehicle|car[- ]following|racing|lane|traffic"),
    ("Medical robotics", r"endoscop|medical|surgical|capsule"),
    ("Multi-agent & vision", r"multi-agent|formation|swarm|homograph|vision|camera"),
    ("Learning & UQ", r"uncertainty|conformal|learning|neural|explainab|identification|prediction"),
    ("Fuzzy control", r"fuzzy|pid|control"),
]

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

def guess_category(title):
    for cat, rx in CATEGORY_RULES:
        if re.search(rx, title, re.I):
            return cat
    return "Latest"

def update_videos():
    path = ROOT / "videos.json"
    videos = json.loads(path.read_text(encoding="utf-8"))
    known = {v["id"] for v in videos}
    ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
    feed = ET.fromstring(get(f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"))
    new = []
    for e in feed.findall("a:entry", ns):  # newest first
        vid = e.findtext("yt:videoId", namespaces=ns)
        if not vid or vid in known:
            continue
        title = (e.findtext("a:title", namespaces=ns) or "").strip()
        if "#shorts" in title.lower():
            continue
        published = e.findtext("a:published", namespaces=ns) or ""
        new.append({"id": vid, "t": title, "cat": guess_category(title), "y": int(published[:4]) if published[:4].isdigit() else None,
                    "v": "", "d": "", "paper": ""})
    if new:
        path.write_text(json.dumps(new + videos, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"videos: {len(new)} new")

def update_metrics():
    path = ROOT / "metrics.json"
    m = json.loads(path.read_text(encoding="utf-8"))
    try:
        html = get(f"https://scholar.google.com/citations?user={SCHOLAR_ID}&hl=en")
        vals = re.findall(r'<td class="gsc_rsb_std">(\d+)</td>', html)
        if len(vals) < 6:
            raise ValueError("metrics table not found (Scholar may have served a CAPTCHA)")
        count, start = 0, 0
        while True:
            page = get(f"https://scholar.google.com/citations?user={SCHOLAR_ID}&hl=en&cstart={start}&pagesize=100")
            n = page.count('class="gsc_a_tr"')
            count += n
            if n < 100:
                break
            start += 100
        new = {"citations": int(vals[0]), "h_index": int(vals[2]), "i10_index": int(vals[4])}
        if count:
            new["publications"] = count
        if any(m.get(k) != v for k, v in new.items()):
            m.update(new)
            m["updated"] = datetime.date.today().isoformat()
            path.write_text(json.dumps(m, indent=1), encoding="utf-8")
        print("metrics:", new)
    except Exception as ex:  # Scholar often blocks automated requests; keep the last good values
        print("metrics: skipped -", ex, file=sys.stderr)

if __name__ == "__main__":
    update_videos()
    update_metrics()
