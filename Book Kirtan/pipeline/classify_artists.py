"""
Stage 2.5: Classify artist dumps as primary kirtan artists or not.

Fetches all artist_research_dump entries, sends condensed profiles to Claude
in a single batch call, then updates artist_pipeline:
  - Confirmed kirtan artists → status stays 'done'
  - Not primarily kirtan artists → status → 'skipped'

Usage:
  python classify_artists.py           # classify all unclassified dumps
  python classify_artists.py --dry-run # print decisions without updating DB
"""

import json
import os
import sys
import argparse
from dotenv import load_dotenv
from supabase import create_client, Client
import anthropic

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def condense(extracted: dict) -> str:
    """Return a short summary of an artist for classification."""
    parts = []
    if extracted.get("bio"):
        parts.append(f"Bio: {extracted['bio'][:400]}")
    if extracted.get("performs_in"):
        parts.append(f"Performs in: {', '.join(extracted['performs_in'])}")
    if extracted.get("achievements"):
        parts.append(f"Achievements: {'; '.join(extracted['achievements'][:4])}")
    if extracted.get("what_makes_special"):
        parts.append(f"What makes special: {extracted['what_makes_special'][:200]}")
    if extracted.get("occasions"):
        parts.append(f"Occasions: {', '.join(extracted['occasions'])}")
    return "\n".join(parts)


def classify_batch(artists: list[dict]) -> list[dict]:
    """
    Send all artists to Claude in one call.
    Returns list of {name, verdict, reason} dicts.
    verdict is either 'kirtan_artist' or 'not_kirtan_artist'.
    """
    profiles = ""
    for i, a in enumerate(artists, 1):
        profiles += f"\n--- ARTIST {i}: {a['artist_name']} ---\n"
        profiles += condense(a["extracted"]) + "\n"

    prompt = f"""You are classifying artists for a kirtan booking platform called BookMyKirtan.

We ONLY want artists whose PRIMARY career is performing kirtan or bhajan — singers, musicians, and kirtaniyas who are known and booked for kirtan performances.

We do NOT want:
- ISKCON swamis, sannyasis, or GBC members whose primary role is preaching, teaching, or organizational leadership (even if they occasionally lead kirtan)
- Spiritual speakers, life coaches, or motivational gurus who do kirtan as a side activity
- Mridanga/instrument teachers (not performers)
- People with no real public profile or verifiable kirtan career

For each artist below, respond with EXACTLY this format (one per line, no extra text):
ARTIST <number>: <kirtan_artist|not_kirtan_artist> | <one sentence reason>

{profiles}"""

    response = claude.messages.create(
        model="claude-opus-4-7",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    results = []

    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("ARTIST"):
            continue
        try:
            # "ARTIST 3: kirtan_artist | reason here"
            after_colon = line.split(":", 1)[1].strip()
            verdict_part, reason = after_colon.split("|", 1)
            verdict = verdict_part.strip()
            reason = reason.strip()
            idx = int(line.split()[1].rstrip(":")) - 1
            results.append({
                "name": artists[idx]["artist_name"],
                "verdict": verdict,
                "reason": reason,
            })
        except Exception as e:
            print(f"  Warning: could not parse line: {line!r} ({e})")

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print decisions without updating DB")
    args = parser.parse_args()

    rows = supabase.table("artist_research_dump").select("artist_name, extracted, pipeline_id").execute()
    if not rows.data:
        print("No research dumps found.")
        return

    # Deduplicate by artist_name (take first dump per artist)
    seen = {}
    for row in rows.data:
        name = row["artist_name"]
        if name not in seen:
            seen[name] = row
    artists = list(seen.values())

    print(f"Classifying {len(artists)} artists in one Claude call...")
    verdicts = classify_batch(artists)

    kirtan = [v for v in verdicts if v["verdict"] == "kirtan_artist"]
    not_kirtan = [v for v in verdicts if v["verdict"] == "not_kirtan_artist"]

    print(f"\n✓ Kirtan artists ({len(kirtan)}):")
    for v in kirtan:
        print(f"  {v['name']}: {v['reason']}")

    print(f"\n✗ Not primarily kirtan artists ({len(not_kirtan)}):")
    for v in not_kirtan:
        print(f"  {v['name']}: {v['reason']}")

    if args.dry_run:
        print("\n(dry-run — no DB changes)")
        return

    # Update pipeline: skip non-kirtan artists
    skipped = 0
    for v in not_kirtan:
        supabase.table("artist_pipeline").update({
            "status": "skipped",
            "notes": f"Not primarily a kirtan artist: {v['reason']}",
        }).eq("name", v["name"]).execute()
        skipped += 1

    print(f"\nUpdated {skipped} artists → skipped in pipeline.")
    print(f"{len(kirtan)} confirmed kirtan artists remain as 'done'.")


if __name__ == "__main__":
    main()
