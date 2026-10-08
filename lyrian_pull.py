#!/usr/bin/env python3
"""
lyrian_pull.py - download Lyrian Chronicles rules data from the official
site's public data feed (the same feed rpg.angelssword.com / Clio load from).

    python lyrian_pull.py --check              # just print the latest rules version
    python lyrian_pull.py                      # pull the latest version into ./lyrian-data/<version>/
    python lyrian_pull.py --version 0.13.2     # pull a specific version
    python lyrian_pull.py --extras             # also grab Clio's structured weapon-mod files
    python lyrian_pull.py --force              # re-pull a version you already have

Needs Python 3.8+ and nothing else (standard library only).

Be gentle with their server. The script already:
  - skips the pull if you already have that version (use --force to redo it),
  - makes 4 requests at a time (max 6), 30 s timeout, 3 retries with back-off,
  - honours Retry-After and stops on its own after 10 failures in a row.
A full pull is ~545 requests; on 2026-10-08 it finished with zero failures.

Output (one folder per rules version):
    raw/      the feed's responses; list files are byte-for-byte, the five
              *_details.json files join the individual detail responses
    clean/    same records + plain-text copies of HTML fields + trimmed names
    derived/  class_progression.json (what each class grants, in level order)
              ability_sources.json   (every place an ability comes from)
    extras/   (with --extras) Clio's items-mods.json + mod-descriptions.json
    manifest.json  version, time, record counts, SHA-256 of every file

Shared by VerboseBard (Angel Sword: Lyrian Chronicles Character Builder).
Unofficial fan tool. Game content (c) Angel's Sword Studios.
This script only reads public data.
"""
import argparse
import concurrent.futures as cf
import hashlib
import html
import http.client
import json
import os
import re
import shutil
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser

API = "https://clio-proxy.angelssword.com/api/ttrpg"
CLIO_DATA = "https://clio.angelssword.com/characterbuilder/data"
USER_AGENT = "lyrian-community-data-pack/1.1 (fan tool; read-only)"
MAX_CONSECUTIVE_FAILURES = 10
VERSION_RE = re.compile(r"^[0-9A-Za-z][0-9A-Za-z._-]*$")

# list endpoint -> output file name
LISTS = {
    "classes": "classes",
    "key-abilities": "key_abilities",
    "true-abilities": "true_abilities",
    "items": "items",
    "monsters": "monsters",
    "monsters-abilities": "monster_abilities",
    "monsters-abilities-lists": "monster_ability_lists",
    "monsters-active-actions": "monster_active_actions",
    "monsters-active-actions-lists": "monster_active_action_lists",
    "primary-races": "primary_races",
    "ancestries": "ancestries",
    "breakthroughs": "breakthroughs",
    "keywords": "keywords",
    "rulebook": "rulebook",
    "settings-guide": "settings_guide",
    "patch-notes": "patch_notes",
}
# detail endpoint, the list it comes from, the id field to use, output file
DETAILS = [
    ("class", "classes", "classId", "class_details"),
    ("item", "items", "itemId", "item_details"),
    ("monster", "monsters", "monsterId", "monster_details"),
    ("primary-race", "primary_races", "primaryRaceId", "primary_race_details"),
    ("ancestry", "ancestries", "ancestryId", "ancestry_details"),
]
EXTRAS = ["items-mods.json", "mod-descriptions.json"]

# Class detail slots in purchase order. The fields carry no numbers; levels
# 1-8 are the order the official builder sells them in (Key / Ability /
# Skills / Ability / Heart / Ability / Soul / Ultimate).
LEVEL_SLOTS = [
    (1, "keyAbility", "key ability"),
    (2, "ability1", "ability"),
    (3, "skills", "skills"),
    (4, "ability2", "ability"),
    (5, "heart", "heart"),
    (6, "ability3", "ability"),
    (7, "soul", "soul"),
    (8, "ultimateAbility", "ultimate"),
]

TAG_RE = re.compile(r"<[a-zA-Z/][^>]*>")


class _Text(HTMLParser):
    BLOCK = {"p", "li", "br", "div", "h1", "h2", "h3", "h4", "h5", "h6", "tr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "li":
            self.parts.append("\n- ")
        elif tag == "br":
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        self.parts.append(data)


def html_to_text(value):
    p = _Text()
    p.feed(value)
    text = html.unescape("".join(p.parts)).replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


class Fetcher:
    """GET with timeout, retries, Retry-After, and a stop switch."""

    def __init__(self, timeout, retries):
        self.timeout = timeout
        self.retries = retries
        self.requests = 0
        self.failures = []
        self.consecutive = 0
        self.stopped = False
        self.lock = threading.Lock()

    def _fail(self, url, error):
        with self.lock:
            self.failures.append({"url": url, "error": error})
            self.consecutive += 1
            if self.consecutive >= MAX_CONSECUTIVE_FAILURES and not self.stopped:
                self.stopped = True
                print(f"  Stopping: {MAX_CONSECUTIVE_FAILURES} failures in a row (the server may be refusing us).")

    def get(self, url):
        """Return the response body (bytes) or None."""
        if self.stopped:
            self._fail(url, "skipped after repeated failures")
            return None
        last = "unknown error"
        for attempt in range(self.retries + 1):
            with self.lock:
                self.requests += 1
            wait = 2 ** (attempt + 1)
            try:
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    body = resp.read()
                with self.lock:
                    self.consecutive = 0
                return body
            except urllib.error.HTTPError as exc:
                last = f"HTTP {exc.code}"
                if exc.code in (400, 401, 403, 404):
                    break  # not something a retry will fix
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                if retry_after and retry_after.isdigit():
                    wait = min(int(retry_after), 120)
            except (urllib.error.URLError, http.client.HTTPException, TimeoutError, ConnectionError, OSError, ValueError) as exc:
                last = str(exc)
            if attempt < self.retries and not self.stopped:
                time.sleep(wait)
        self._fail(url, last)
        return None


def parse_json(fetcher, url, blob):
    if blob is None:
        return None
    try:
        return json.loads(blob)
    except ValueError:
        fetcher._fail(url, "response was not JSON (maintenance or block page?)")
        return None


def write_bytes(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)


def write_json(path, obj):
    write_bytes(path, json.dumps(obj, ensure_ascii=False, indent=1).encode("utf-8"))


def clean_value(value):
    if isinstance(value, dict):
        return clean_record(value)
    if isinstance(value, list):
        return [clean_value(v) for v in value]
    return value


def clean_record(rec):
    if not isinstance(rec, dict):
        return rec
    out = {}
    for key, value in rec.items():
        if isinstance(value, (dict, list)):
            out[key] = clean_value(value)
            continue
        if key == "name" and isinstance(value, str) and value != value.strip():
            out["nameOriginal"] = value
            value = value.strip()
        out[key] = value
        if isinstance(value, str) and TAG_RE.search(value):
            out[key + "Text"] = html_to_text(value)
    return out


def build_derived(data):
    by_index = {}
    for fam in ("true_abilities", "key_abilities"):
        for rec in data.get(fam) or []:
            by_index[rec["indexId"]] = (fam, rec)

    def ref(index_id):
        fam, rec = by_index.get(index_id, (None, None))
        if not rec:
            return {"indexId": index_id, "unresolved": True}
        slug = rec.get("trueAbilityId") or rec.get("abilityId")
        return {"indexId": index_id, "id": slug, "name": rec["name"].strip(), "family": fam}

    progression = []
    sources = {}

    def add_source(index_id, entry):
        if index_id:
            sources.setdefault(index_id, []).append(entry)

    for c in data.get("class_details") or []:
        levels = []
        for level, slot, kind in LEVEL_SLOTS:
            value = c.get(slot) or ""
            if kind in ("skills", "heart", "soul"):
                levels.append({"level": level, "kind": kind, "text": value})
            else:
                levels.append(dict({"level": level, "kind": kind}, **ref(value)) if value else {"level": level, "kind": kind})
                add_source(value, {"type": "class", "class": c["name"].strip(), "classId": c["classId"], "level": level, "slot": slot})
        progression.append({
            "class": c["name"].strip(), "classId": c["classId"], "indexId": c["indexId"],
            "tier": c.get("tier"), "roles": [r for r in (c.get("role1"), c.get("role2")) if r],
            "requirements": c.get("requirements", ""), "levels": levels,
        })

    for a in data.get("ancestry_details") or []:
        for slot in ("trait1", "trait2", "trait3"):
            add_source(a.get(slot), {"type": "ancestry", "ancestry": a["name"].strip(), "primaryRace": a.get("primaryRace"), "slot": slot})
    for r in data.get("primary_race_details") or []:
        for slot in ("ability1", "ability2"):
            add_source(r.get(slot), {"type": "primaryRace", "race": r["name"].strip(), "slot": slot})
        for key, value in r.items():
            if isinstance(value, dict) and value.get("ability"):
                add_source(value["ability"], {"type": "primaryRaceOption", "race": r["name"].strip(), "option": key})
    for b in data.get("breakthroughs") or []:
        add_source(b.get("ability"), {"type": "breakthrough", "breakthrough": b["name"].strip()})
    for k in data.get("key_abilities") or []:
        assoc = k.get("associatedAbility")
        if assoc and assoc != "None":
            add_source(assoc, {"type": "keyAbilityGrant", "keyAbility": k["name"].strip()})

    ability_sources = []
    for t in data.get("true_abilities") or []:
        entries = sources.get(t["indexId"], [])
        levels = sorted({e["level"] for e in entries if e["type"] == "class"})
        ability_sources.append({
            "name": t["name"].strip(), "id": t["trueAbilityId"], "indexId": t["indexId"],
            "sources": entries, "differentLevelsByClass": len(levels) > 1,
        })
    return progression, ability_sources


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_version(value):
    value = str(value or "").strip()
    if not VERSION_RE.match(value) or value in (".", ".."):
        sys.exit(f"Refusing odd version string: {value!r}")
    return value


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="print the latest rules version and exit")
    ap.add_argument("--version", help="rules version to pull (default: latest)")
    ap.add_argument("--out", default="lyrian-data", help="output folder (default: ./lyrian-data)")
    ap.add_argument("--parallel", type=int, default=4, help="requests at a time, 1-6 (default 4)")
    ap.add_argument("--timeout", type=int, default=30, help="seconds per request (default 30)")
    ap.add_argument("--retries", type=int, default=3, help="retries per request (default 3)")
    ap.add_argument("--extras", action="store_true", help="also download Clio's weapon-mod files")
    ap.add_argument("--force", action="store_true", help="re-pull even if this version is already on disk")
    args = ap.parse_args()
    parallel = max(1, min(6, args.parallel))
    f = Fetcher(args.timeout, args.retries)

    latest_url = f"{API}/version/latest"
    latest_raw = f.get(latest_url)
    latest = parse_json(f, latest_url, latest_raw)
    if not isinstance(latest, dict) or not latest.get("versionNumber"):
        detail = f.failures[-1]["error"] if f.failures else "unexpected response"
        sys.exit(f"Could not read {latest_url}: {detail}")
    if args.check:
        print(f"Latest rules version: {latest.get('versionNumber')} (id {latest.get('versionId')})")
        return
    version = safe_version(args.version or latest["versionNumber"])
    final_dir = os.path.join(args.out, version)
    if os.path.exists(os.path.join(final_dir, "manifest.json")) and not args.force:
        print(f"Already have {version} in {final_dir} - nothing to do (use --force to pull it again).")
        return
    work_dir = final_dir + ".partial"
    shutil.rmtree(work_dir, ignore_errors=True)
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(f"Pulling rules {version} -> {final_dir} ({parallel} at a time)")

    data = {}

    def fetch_json(url):
        return url, f.get(url)

    def save_raw(name, url, blob):
        obj = parse_json(f, url, blob)
        if obj is not None:
            write_bytes(os.path.join(work_dir, "raw", name + ".json"), blob)
            data[name] = obj

    versions_url = f"{API}/version/list"
    save_raw("versions", versions_url, f.get(versions_url))
    write_bytes(os.path.join(work_dir, "raw", "version_latest.json"), latest_raw)

    with cf.ThreadPoolExecutor(max_workers=parallel) as pool:
        futures = {pool.submit(fetch_json, f"{API}/{version}/{ep}"): name for ep, name in LISTS.items()}
        for fut in cf.as_completed(futures):
            url, blob = fut.result()
            save_raw(futures[fut], url, blob)
        print(f"  lists done ({len(data)} files, {f.requests} requests)")

        for ep, list_name, id_field, out_name in DETAILS:
            ids = [rec[id_field] for rec in data.get(list_name) or [] if rec.get(id_field)]
            urls = [f"{API}/{version}/{ep}/{urllib.parse.quote(str(i), safe='')}" for i in ids]
            records = []
            for url, blob in pool.map(fetch_json, urls):
                obj = parse_json(f, url, blob)
                if obj is not None:
                    records.append(obj)
            write_json_compact = json.dumps(records, ensure_ascii=False).encode("utf-8")
            write_bytes(os.path.join(work_dir, "raw", out_name + ".json"), write_json_compact)
            data[out_name] = records
            print(f"  {out_name}: {len(records)}/{len(ids)}")

    if args.extras:
        for fn in EXTRAS:
            url = f"{CLIO_DATA}/{fn}"
            blob = f.get(url)
            if parse_json(f, url, blob) is not None:
                write_bytes(os.path.join(work_dir, "extras", fn), blob)

    for name, obj in data.items():
        write_json(os.path.join(work_dir, "clean", name + ".json"), clean_value(obj))
    progression, ability_sources = build_derived(data)
    write_json(os.path.join(work_dir, "derived", "class_progression.json"), progression)
    write_json(os.path.join(work_dir, "derived", "ability_sources.json"), ability_sources)

    files = {}
    for dirpath, _, names in os.walk(work_dir):
        for n in sorted(names):
            p = os.path.join(dirpath, n)
            files[os.path.relpath(p, work_dir).replace(os.sep, "/")] = {"bytes": os.path.getsize(p), "sha256": sha256(p)}
    manifest = {
        "source": API, "rulesVersion": version, "latest": latest,
        "pulledAtUtc": started, "finishedAtUtc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "requests": f.requests, "failures": f.failures,
        "recordCounts": {k: (len(v) if isinstance(v, list) else 1) for k, v in sorted(data.items())},
        "files": files,
    }
    write_json(os.path.join(work_dir, "manifest.json"), manifest)

    if f.failures:
        print(f"{len(f.failures)} request(s) failed. First ones:")
        for item in f.failures[:5]:
            print(f"  {item['url']}  ->  {item['error']}")
        print(f"Full list: {os.path.join(work_dir, 'manifest.json')} (\"failures\"). Your previous copy was not touched.")
        sys.exit(1)

    # Swap in the new copy without ever leaving you with no copy.
    old_dir = final_dir + ".old"
    shutil.rmtree(old_dir, ignore_errors=True)
    if os.path.exists(final_dir):
        os.replace(final_dir, old_dir)
    os.replace(work_dir, final_dir)
    shutil.rmtree(old_dir, ignore_errors=True)
    print(f"Done: {f.requests} requests, 0 failures -> {final_dir}")


if __name__ == "__main__":
    main()
