"""
Stage 1: Artist Discovery

Two-phase approach — collect first, extract later:

  python discover_artists.py --collect              # fetch web + YouTube results → serper_cache/
  python discover_artists.py --collect hare-krishna # fetch only one tradition
  python discover_artists.py --extract              # regex-extract names from cache → queue in DB
  python discover_artists.py --extract hare-krishna # extract only one tradition

Each query saves two files:
  serper_cache/<tradition>/NNN_<query>_web.json     ← Google web results
  serper_cache/<tradition>/NNN_<query>_yt.json      ← YouTube video results

YouTube channel names are extracted as high-confidence artist names.
Every pipeline entry records its source (tradition + query + type).
"""

import json
import sys
import os
import re
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SERPER_API_KEY = os.environ["SERPER_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

CACHE_DIR = Path(__file__).parent / "serper_cache"

# ── Search queries grouped by tradition ──────────────────────────────────────

QUERIES = {
    "hare-krishna": [
        "kirtaniya ISKCON kirtan artist",
        "Hare Krishna kirtan singer India booking",
        "ISKCON devotee kirtan performer",
        "Mayapur kirtan mela artists performers",
        "Bhakti Sangama kirtan artists",
        "kirtaniya site:youtube.com",
        "ISKCON kirtan artist wedding satsang India",
        "Vrindavan kirtan singer famous",
        "ISKCON Chowpatty kirtan lead singer",
        "BB Govinda Madhava Das Gauravani kirtaniya similar artists",
        "Mayapur TV kirtan artists featured",
        "ISKCON Bangalore kirtan devotee singers",
        "Hare Krishna kirtan live concert artists India",
        "Goloka kirtan band members India",
        "Prema Kirtan artists ISKCON",
        "kirtan mela Vrindavan featured artists",
        "ISKCON Juhu Mumbai kirtan singers",
        "Bhaktivedanta Manor kirtan artists UK",
        "ISKCON Pune kirtan devotees singers",
        "Hare Krishna mantra singer YouTube channel India",
        "Govinda Prabhu kirtan ISKCON artists similar",
        "Aindra Das kirtan prabhu artists similar",
        "24 hour kirtan ISKCON Vrindavan artists",
        "Gaura Vani kirtan artists similar",
        "Devaki Devi Dasi kirtan artists similar",
        "Janananda Goswami kirtan artists similar",
        "ISKCON kirtan artists performing at Rathayatra festival",
        "Bhaktivinoda Institute kirtan artists",
        "kirtan wallah ISKCON artists",
        "Harinam Sankirtan kirtan singers India",
        "ISKCON kirtan Das Prabhu singer devotee",
        "Gauranga Das kirtan singer ISKCON",
        "Bhakti Marga kirtan artists walking tour",
        "Vaishnava kirtan singer Radha Govinda Das",
        "Lokanath Swami kirtan similar artists",
        "Indradyumna Swami kirtan similar artists",
        "Radhanath Swami kirtan devotee singers",
        "Niranjana Swami kirtan similar artists",
        "Bhaktivedanta Swami kirtan artists disciples",
        "Kadamba Kanana Swami kirtan similar artists",
    ],
    "gurbani": [
        "Gurbani kirtan artist India booking",
        "Sikh kirtan singer wedding India",
        "ragi kirtan performers India famous",
        "Bhai Sarabjit Singh kirtan artists similar",
        "Gurbani kirtan singer YouTube channel",
        "Bhai Harjinder Singh Srinagar Wale artists similar",
        "Bhai Nirmal Singh Khalsa artists similar",
        "Amritsar Gurbani kirtan famous ragis",
        "Sikh devotional singer wedding Delhi Punjab",
        "Gurbani kirtan jatha Punjab artists",
        "Hazoori Ragi Sri Darbar Sahib artists",
        "Bhai Lakhwinder Singh kirtan artists similar",
        "Bhai Gurpreet Singh Shimla Wale artists similar",
        "Sikh kirtan artists performing Akhand Path",
        "famous Sikh kirtan singers India 2024",
    ],
    "bhajan": [
        "famous bhajan singer India booking events",
        "devotional bhajan artist Hindi singer India",
        "top bhajan singers India concerts 2024",
        "Anup Jalota bhajan artists similar India",
        "Anuradha Paudwal bhajan singers similar",
        "Jagjit Singh bhajans devotional artists similar",
        "bhajan singer for wedding pooja India",
        "Lata Mangeshkar bhajan devotional artists similar",
        "Suresh Wadkar bhajan artists similar India",
        "devotional singer India concerts satsang bhajan",
        "Vinod Agarwal bhajan singer artists similar",
        "Gulshan Kumar bhajan artists similar",
        "bhajan singer for Ram navami jagran event India",
        "famous bhajan singer Maharashtra Gujarat India",
        "bhajan singer for Navratri event India",
    ],
    "mantra-music": [
        "mantra music artist India kirtan yoga",
        "Sanskrit mantra chanting artist booking India",
        "devotional mantra singer India like Deva Premal",
        "Sanskrit chanting artist India meditation music",
        "yoga music kirtan artist India tour",
        "mantra chanting singer India international",
        "Deva Premal Miten artists similar India",
        "Snatam Kaur kirtan artists similar India",
        "Wah mantra music artists similar India",
        "New age Indian devotional mantra singer",
    ],
    "ram-naam": [
        "Ram naam kirtan artist India satsang",
        "Ram bhajan singer for satsang booking India",
        "Hanuman chalisa kirtan performer India",
        "Ram Naam sankirtan artists India",
        "Shri Ram bhajan singer India famous",
        "Ram katha singer India booking events",
        "Morari Bapu Ram katha kirtan artists similar",
        "Ramayan kirtan singer India satsang",
        "Ram dhun kirtan artist India",
        "Shiv bhajan kirtan singer India famous events",
    ],
    "haveli-sangeet": [
        "Haveli sangeet artist Pushtimarg Gujarat",
        "Pushtimarg kirtan singer booking",
        "Vallabhacharya sampradaya kirtan artist",
        "Haveli sangeet performer Nathdwara",
        "Vaishnav kirtan Pushtimarg artist India",
        "Haveli music Gujarat devotional singer",
        "Pushti Marg Vaishnav kirtan Vadodara Surat",
    ],
    "nirguni": [
        "Kabir doha kirtan artist India",
        "Nirguni bhajan singer India",
        "Kabir singer folk devotional India",
        "Kumar Gandharva Kabir artists similar India",
        "Nirguni sant sangeet singer India",
        "Kabir bhajan folk singer Rajasthan India",
        "Prahlad Singh Tipanya artists similar India",
        "Malini Awasthi folk devotional singers similar",
    ],
    "classical-devotional": [
        "Carnatic devotional singer India booking",
        "Hindustani classical devotional singer India",
        "MS Subbulakshmi devotional artists similar India",
        "Pandit Jasraj devotional artists similar",
        "classical Indian devotional singer weddings events",
        "Bombay Jayashri artists similar India",
        "Sudha Raghunathan devotional artists similar",
        "Carnatic vocalist performing Tiruppavai kirtan India",
        "Hindustani classical vocalist bhajan India famous",
        "Rashid Khan devotional artists similar India",
    ],
    "sufi": [
        "Sufi kirtan qawwali singer India booking",
        "Sufi singer India events wedding satsang",
        "Nusrat Fateh Ali Khan artists similar India",
        "Indian sufi devotional singer contemporary",
        "Kailash Kher Sufi artists similar India",
        "Abida Parveen sufi artists similar India",
        "Sufi qawwali singer India concerts booking",
        "Wadali Brothers artists similar India",
        "Indian sufi singer performing live events",
    ],
}


# ── Serper ────────────────────────────────────────────────────────────────────

def serper_web(query: str, num: int = 10) -> list[dict]:
    resp = requests.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
        json={"q": query, "num": num},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    results = []
    for r in data.get("organic", []):
        results.append({
            "title": r.get("title", ""),
            "snippet": r.get("snippet", ""),
            "link": r.get("link", ""),
            "channel": "",
        })
    for r in data.get("peopleAlsoAsk", []):
        results.append({
            "title": r.get("question", ""),
            "snippet": r.get("snippet", ""),
            "link": r.get("link", ""),
            "channel": "",
        })
    if data.get("knowledgeGraph"):
        kg = data["knowledgeGraph"]
        results.append({
            "title": kg.get("title", ""),
            "snippet": kg.get("description", ""),
            "link": kg.get("website", ""),
            "channel": "",
        })
    return results


def serper_youtube(query: str, num: int = 10) -> list[dict]:
    """Search YouTube via Serper's video endpoint. Returns channel names alongside results."""
    resp = requests.post(
        "https://google.serper.dev/videos",
        headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
        json={"q": query, "num": num},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    results = []
    for r in data.get("videos", []):
        results.append({
            "title": r.get("title", ""),
            "snippet": r.get("snippet", ""),
            "link": r.get("link", ""),
            "channel": r.get("channel", ""),      # artist's channel name — high confidence
            "channel_link": r.get("channelLink", ""),
        })
    return results


# ── Collect phase ─────────────────────────────────────────────────────────────

def collect(filter_tradition: str | None = None):
    CACHE_DIR.mkdir(exist_ok=True)

    traditions_to_run = (
        {filter_tradition: QUERIES[filter_tradition]}
        if filter_tradition and filter_tradition in QUERIES
        else QUERIES
    )
    total = sum(len(q) for q in traditions_to_run.values())
    # Each query = 1 web fetch + 1 YouTube fetch
    print(f"Collecting {total} queries (web + YouTube each) across {len(traditions_to_run)} tradition(s)\n")

    count = 0
    for tradition, queries in traditions_to_run.items():
        trad_dir = CACHE_DIR / tradition
        trad_dir.mkdir(exist_ok=True)
        print(f"── {tradition} ({len(queries)} queries) ──")
        for i, query in enumerate(queries):
            safe_name = re.sub(r"[^\w]+", "_", query)[:80]
            web_file = trad_dir / f"{i:03d}_{safe_name}_web.json"
            yt_file  = trad_dir / f"{i:03d}_{safe_name}_yt.json"

            web_cached = web_file.exists()
            yt_cached  = yt_file.exists()

            if web_cached and yt_cached:
                print(f"  [{count+1}/{total}] CACHED  {query}")
                count += 1
                continue

            print(f"  [{count+1}/{total}] Fetching {query}")

            if not web_cached:
                try:
                    time.sleep(0.3)
                    results = serper_web(query)
                    web_file.write_text(json.dumps({
                        "query": query, "tradition": tradition,
                        "source_type": "web", "results": results,
                    }, indent=2, ensure_ascii=False))
                    print(f"    web: {len(results)} results")
                except Exception as e:
                    print(f"    web error: {e}")
            else:
                print(f"    web: cached")

            if not yt_cached:
                try:
                    time.sleep(0.3)
                    results = serper_youtube(query)
                    yt_file.write_text(json.dumps({
                        "query": query, "tradition": tradition,
                        "source_type": "youtube", "results": results,
                    }, indent=2, ensure_ascii=False))
                    print(f"    youtube: {len(results)} results")
                except Exception as e:
                    print(f"    youtube error: {e}")
            else:
                print(f"    youtube: cached")

            count += 1

    print(f"\nDone. Cache saved to {CACHE_DIR}")


# ── Regex name extractor ──────────────────────────────────────────────────────

# Honorific suffixes/prefixes that reliably indicate a person's name
VAISHNAVA_SUFFIXES = r"(?:Das|Dasa|Dasi|Swami|Maharaj|Maharaja|Prabhu|Goswami|Giri|Tirtha|Puri|Bharati|Muni|Yogi|Acharya)"

# Pattern: "Firstname [Middlename] Das/Swami/etc"
RE_VAISHNAVA = re.compile(
    rf"\b([A-Z][a-z]{{2,}}(?:\s[A-Z][a-z]{{2,}})?(?:\s[A-Z][a-z]{{2,}})?)\s{VAISHNAVA_SUFFIXES}\b"
)
# Pattern: "Swami/Goswami Firstname" (reversed order, e.g. "Swami Prabhupada")
RE_VAISHNAVA_REV = re.compile(
    r"\b(?:Swami|Goswami)\s([A-Z][a-z]{2,}(?:\s[A-Z][a-z]{2,})?)\b"
)
# Bhai + 1-3 capitalised words (Sikh ragis)
RE_BHAI = re.compile(r"\bBhai\s([A-Z][a-z]{2,}(?:\s[A-Z][a-z]{2,}){0,2})\b")
# Pandit / Ustad / Vidushi / Ragi
RE_CLASSICAL = re.compile(
    r"\b(?:Pandit|Pt\.|Ustad|Vidushi|Ragi)\s([A-Z][a-z]{2,}(?:\s[A-Z][a-z]{2,}){0,2})\b"
)
# "Singh Wale" / "Singh Khalsa" suffix — Sikh ragis often named "Bhai X Singh Y Wale"
# already caught by RE_BHAI above; this catches standalone "X Singh" patterns
RE_SINGH = re.compile(r"\b([A-Z][a-z]{2,}(?:\s[A-Z][a-z]{2,})?)\sSingh\b")

# Common English / non-name words that appear title-cased in search snippets
_NOISE_WORDS = {
    "youtube", "instagram", "facebook", "twitter", "wikipedia", "google",
    "india", "indian", "kirtan", "bhajan", "mantra", "satsang", "temple",
    "iskcon", "hare", "krishna", "vrindavan", "mayapur", "mathura",
    "bangalore", "mumbai", "delhi", "punjab", "gujarat", "rajasthan",
    "festival", "event", "booking", "concert", "show", "tour", "live",
    "singer", "artist", "performer", "musician", "devotee", "disciple",
    "music", "song", "album", "video", "channel", "playlist",
    "more", "info", "read", "watch", "buy", "book", "view", "click",
    "new", "age", "south", "north", "east", "west", "central",
    "ratha", "yatra", "navratri", "diwali", "janmashtami", "holi",
    "akhand", "path", "golden", "darbar", "sahib", "gurudwara",
    "spiritual", "devotional", "sacred", "divine", "holy", "bhakti",
    "sufi", "qawwali", "mehfil", "night", "raat", "programme",
    "band", "group", "ensemble", "jatha", "orchestra",
    "open", "now", "traditional", "fusion", "experience", "soulful",
    "packed", "bollywood", "folk", "classical", "contemporary",
    "best", "top", "famous", "popular", "known", "well",
}


def looks_like_noise(name: str) -> bool:
    words = name.lower().split()
    # Any word in the name is a known noise word → discard
    if any(w in _NOISE_WORDS for w in words):
        return True
    if name.isupper():
        return True
    if len(name) < 5:
        return True
    return False


def extract_names_from_text(text: str) -> list[str]:
    found = []

    for m in RE_VAISHNAVA.finditer(text):
        found.append(m.group(0).strip())
    for m in RE_VAISHNAVA_REV.finditer(text):
        found.append(("Swami " + m.group(1)).strip())
    for m in RE_BHAI.finditer(text):
        found.append(("Bhai " + m.group(1)).strip())
    for m in RE_CLASSICAL.finditer(text):
        found.append(m.group(0).strip())
    for m in RE_SINGH.finditer(text):
        candidate = m.group(0).strip()
        if not looks_like_noise(candidate):
            found.append(candidate)

    return [n for n in found if not looks_like_noise(n)]


# For each result, find names AND the snippet + source they came from
def extract_names_from_results(results: list[dict], source_type: str = "web") -> list[tuple[str, str, str, str]]:
    """Returns list of (name, snippet, source_url, confidence).
    confidence: 'high' for YouTube channel names, 'normal' for regex matches.
    """
    found = []
    for r in results:
        url = r.get("link", "")
        snippet = r.get("snippet", r.get("title", ""))

        # YouTube channel name → high confidence, treat as a name directly
        channel = r.get("channel", "").strip()
        if source_type == "youtube" and channel and not looks_like_noise(channel):
            found.append((channel, snippet, r.get("channel_link", url), "high"))

        # Regex over title + snippet
        text = f"{r.get('title', '')} {r.get('snippet', '')}"
        names = extract_names_from_text(text)
        for name in names:
            found.append((name, snippet, url, "normal"))

    return found


# ── Kirtaniya scorer ─────────────────────────────────────────────────────────

# Strong positive: person is described doing kirtan/music
_KIRTAN_SIGNALS = {
    "kirtan", "kirtaniya", "kirtani", "bhajan", "singer", "vocalist",
    "performs", "performing", "chanting", "musician", "music", "sings",
    "satsang", "concert", "album", "recording", "youtube", "ragi",
    "harmonium", "mridanga", "tabla", "mantra", "devotional music",
}
# Strong negative: person is primarily something else
_NON_KIRTAN_SIGNALS = {
    "author", "book", "wrote", "writing", "speaker", "lecture", "preacher",
    "gbc", "guru", "sannyasi", "minister", "philosopher", "theologian",
    "politician", "president", "secretary", "founder", "founder-acharya",
    "temple president", "hospital", "charity", "institution",
}


def score_kirtaniya(name: str, snippets: list[str]) -> tuple[str, str]:
    """
    Returns (status, reason):
      status = 'pending'  → likely a performing kirtaniya, queue for Stage 2
      status = 'review'   → ambiguous, needs human check before Stage 2
    """
    combined = " ".join(snippets).lower()
    pos = sum(1 for s in _KIRTAN_SIGNALS if s in combined)
    neg = sum(1 for s in _NON_KIRTAN_SIGNALS if s in combined)

    if pos >= 2 and neg == 0:
        return "pending", f"kirtan signals: {pos}"
    if neg >= 2 and pos == 0:
        return "review", f"non-kirtan signals: {neg} (speaker/author/admin?)"
    if pos > neg:
        return "pending", f"kirtan: {pos}, non-kirtan: {neg}"
    return "review", f"kirtan: {pos}, non-kirtan: {neg} — ambiguous"


# ── DB helpers ────────────────────────────────────────────────────────────────

def get_existing_names() -> set[str]:
    pipeline = supabase.from_("artist_pipeline").select("name").execute()
    artists = supabase.from_("artists").select("name").execute()
    names = set()
    for row in (pipeline.data or []):
        names.add(row["name"].lower().strip())
    for row in (artists.data or []):
        names.add(row["name"].lower().strip())
    return names


def queue_artist(name: str, source_url: str, status: str, notes: str) -> None:
    supabase.from_("artist_pipeline").insert({
        "name": name,
        "source_url": source_url,
        "status": status,
        "notes": notes,
    }).execute()


# ── Extract phase ─────────────────────────────────────────────────────────────

def extract(filter_tradition: str | None = None):
    if not CACHE_DIR.exists():
        print("No cache found. Run --collect first.")
        return

    traditions_to_run = (
        [filter_tradition] if filter_tradition else list(QUERIES.keys())
    )

    print("Loading existing artists from DB...")
    existing = get_existing_names()
    print(f"  {len(existing)} names already known\n")

    # key → {name, snippets, source_url, sources[], high_confidence}
    candidates: dict[str, dict] = {}

    for tradition in traditions_to_run:
        trad_dir = CACHE_DIR / tradition
        if not trad_dir.exists():
            print(f"── {tradition}: no cache, skipping ──")
            continue

        # Process web and youtube files together, grouped by query index
        all_files = sorted(trad_dir.glob("*.json"))
        print(f"── {tradition} ({len(all_files)} cache files) ──")

        for cf in all_files:
            data = json.loads(cf.read_text())
            query = data.get("query", cf.stem)
            source_type = data.get("source_type", "web")
            results = data.get("results", [])

            hits = extract_names_from_results(results, source_type)
            new_here = 0
            for name, snippet, url, confidence in hits:
                key = name.lower().strip()
                if key in existing:
                    continue
                source_label = f"{tradition}/{source_type}: {query[:60]}"
                if key not in candidates:
                    candidates[key] = {
                        "name": name,
                        "snippets": [],
                        "sources": [],
                        "source_url": url,
                        "high_confidence": False,
                    }
                    new_here += 1
                candidates[key]["snippets"].append(snippet)
                candidates[key]["sources"].append(source_label)
                if confidence == "high":
                    candidates[key]["high_confidence"] = True

            label = f"[{source_type}] {query[:60]}"
            print(f"  {label}")
            print(f"    +{new_here} new  ({len(candidates)} running total)")

    print(f"\n── Scoring {len(candidates)} candidates ──")
    pending_count = review_count = 0
    for key, info in candidates.items():
        # YouTube channel names bypass scoring — they're self-declared artists
        if info["high_confidence"]:
            status, reason = "pending", "YouTube channel (high confidence)"
        else:
            status, reason = score_kirtaniya(info["name"], info["snippets"])

        sources_str = " | ".join(dict.fromkeys(info["sources"]))   # deduplicated
        context = info["snippets"][0][:150] if info["snippets"] else ""
        notes = f"[{status}] {reason} | src: {sources_str[:200]} | {context}"

        queue_artist(info["name"], info["source_url"], status, notes)
        if status == "pending":
            pending_count += 1
        else:
            review_count += 1

    print(f"  {pending_count} queued as 'pending' (ready for Stage 2)")
    print(f"  {review_count} queued as 'review' (needs human check)")
    print(f"\nDone. Run `python research_artist.py` for Stage 2 on pending artists.")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    if not args or args[0] not in ("--collect", "--extract"):
        print(__doc__)
        sys.exit(1)

    mode = args[0]
    filter_tradition = args[1] if len(args) > 1 else None

    if filter_tradition and filter_tradition not in QUERIES:
        print(f"Unknown tradition '{filter_tradition}'. Options: {', '.join(QUERIES)}")
        sys.exit(1)

    if mode == "--collect":
        collect(filter_tradition)
    else:
        extract(filter_tradition)


if __name__ == "__main__":
    main()
