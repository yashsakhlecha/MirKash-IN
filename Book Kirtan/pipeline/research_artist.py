"""
Stage 2: Research Agent
Picks pending artists from artist_pipeline, runs two Exa deep searches
(biography + social/performances), saves structured dump to artist_research_dump.

No Claude in this stage — Exa's outputSchema does the extraction directly.
Claude runs in Stage 3 to write publication-ready prose.

Usage:
  python research_artist.py                  # process all pending
  python research_artist.py "Radhika Das"    # process one specific artist
"""

import json
import sys
import os
from dotenv import load_dotenv
from exa_py import Exa
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
EXA_API_KEY = os.environ["EXA_API_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
exa = Exa(api_key=EXA_API_KEY)

# Exa returns some rich objects (e.g. grounding) that aren't JSON-serializable.
# Supabase insert/update payloads must be JSON-safe.
def to_jsonable(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {k: to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(v) for v in value]
    if hasattr(value, "model_dump"):
        return to_jsonable(value.model_dump())
    if hasattr(value, "dict"):
        return to_jsonable(value.dict())
    if hasattr(value, "__dict__"):
        return to_jsonable(vars(value))
    return str(value)

# Exa outputSchema for biographical data
BIO_SCHEMA = {
    "type": "object",
    "description": "Biographical information about a kirtan or Indian devotional music artist",
    "required": ["name", "tradition", "location", "bio", "achievements"],
    "properties": {
        "name": {
            "type": "string",
            "description": "Full name as commonly known"
        },
        "tradition": {
            "type": "string",
            "description": "Musical or spiritual tradition, e.g. ISKCON, Gaudiya Vaishnava, Hindustani Classical, Haveli Sangeet, Sikh Kirtan"
        },
        "location": {
            "type": "string",
            "description": "City, State or Country the artist is based in"
        },
        "bio": {
            "type": "string",
            "description": "Full biographical information about the artist — background, training, lineage, career"
        },
        "what_makes_special": {
            "type": "string",
            "description": "What makes this artist unique — their style, spiritual lineage, or distinctive approach to kirtan"
        },
        "achievements": {
            "type": "array",
            "description": "Notable awards, recognitions, and career milestones",
            "items": {"type": "string"}
        },
        "performs_in": {
            "type": "array",
            "description": "Musical styles and genres they perform e.g. Bhajan, Kirtan, Dhrupad, Thumri",
            "items": {"type": "string"}
        }
    }
}

# Exa outputSchema for social media and performance data
SOCIAL_SCHEMA = {
    "type": "object",
    "description": "Social media presence and performance history of a kirtan artist",
    "required": ["video_links", "occasions"],
    "properties": {
        "instagram_url": {
            "type": "string",
            "description": "Full Instagram profile URL e.g. https://www.instagram.com/username"
        },
        "youtube_channel_url": {
            "type": "string",
            "description": "Full YouTube channel URL"
        },
        "instagram_followers": {
            "type": "string",
            "description": "Instagram followers count as a plain number e.g. 45000"
        },
        "youtube_subscribers": {
            "type": "string",
            "description": "YouTube subscribers count as a plain number e.g. 120000"
        },
        "video_links": {
            "type": "array",
            "description": "Full YouTube video URLs of notable performances",
            "items": {"type": "string"}
        },
        "occasions": {
            "type": "array",
            "description": "Types of occasions they perform at e.g. wedding, festival, temple, corporate event, satsang",
            "items": {"type": "string"}
        },
        "past_big_events": {
            "type": "array",
            "description": "Notable past performances — event name and year if known",
            "items": {"type": "string"}
        }
    }
}


def search_biography(name: str) -> dict:
    """Deep search for biographical and musical background."""
    response = exa.search(
        f"{name} kirtan singer biography musical background tradition",
        type="deep",
        num_results=5,
        output_schema=BIO_SCHEMA,
        contents={"highlights": True},
    )
    return {
        "output": to_jsonable(response.output.content) if response.output else None,
        "grounding": to_jsonable(response.output.grounding) if response.output else None,
        "results": [
            {"title": r.title, "url": r.url, "highlights": to_jsonable(r.highlights)}
            for r in response.results
        ],
    }


def search_social(name: str) -> dict:
    """Deep search for social media, videos, and performance history."""
    response = exa.search(
        f"{name} kirtan YouTube Instagram performances events",
        type="deep",
        num_results=5,
        output_schema=SOCIAL_SCHEMA,
        contents={"highlights": True},
    )
    return {
        "output": to_jsonable(response.output.content) if response.output else None,
        "grounding": to_jsonable(response.output.grounding) if response.output else None,
        "results": [
            {"title": r.title, "url": r.url, "highlights": to_jsonable(r.highlights)}
            for r in response.results
        ],
    }


def merge_extracted(bio_output: dict | None, social_output: dict | None) -> dict:
    """Merge the two outputSchema results into one flat dict."""
    merged = {}
    if bio_output:
        merged.update(bio_output)
    if social_output:
        # Don't overwrite name/tradition/location if already found
        for k, v in social_output.items():
            if k not in merged or not merged[k]:
                merged[k] = v
    return merged


def research_artist(pipeline_id: str, name: str) -> None:
    print(f"\n→ Researching: {name}")

    supabase.table("artist_pipeline").update({"status": "researching"}).eq("id", pipeline_id).execute()

    try:
        print("  Running biography search (Exa deep)...")
        bio_data = search_biography(name)

        print("  Running social + performances search (Exa deep)...")
        social_data = search_social(name)

        # Merge structured outputs
        extracted = merge_extracted(
            bio_data.get("output"),
            social_data.get("output"),
        )

        # Combine all highlight text for Stage 3 to use
        all_highlights = []
        for result in bio_data.get("results", []) + social_data.get("results", []):
            if result.get("highlights"):
                all_highlights.append(
                    f"SOURCE: {result['title']}\nURL: {result['url']}\n"
                    + "\n".join(result["highlights"])
                )
        raw_text = "\n\n" + ("=" * 60) + "\n\n".join(all_highlights)

        exa_results = {"bio": bio_data, "social": social_data}

        if not extracted:
            print("  Exa returned no structured output — marking as skipped")
            supabase.table("artist_pipeline").update({
                "status": "skipped",
                "notes": "Exa returned no structured output"
            }).eq("id", pipeline_id).execute()
            return

        supabase.table("artist_research_dump").insert(to_jsonable({
            "pipeline_id": pipeline_id,
            "artist_name": name,
            "exa_results": exa_results,
            "raw_text": raw_text,
            "extracted": extracted,
            "model_used": "exa-deep",
        })).execute()

        supabase.table("artist_pipeline").update({"status": "done"}).eq("id", pipeline_id).execute()

        filled = [k for k, v in extracted.items() if v]
        print(f"  Done. Extracted: {', '.join(filled)}")

    except Exception as e:
        supabase.table("artist_pipeline").update({
            "status": "pending",
            "notes": f"Error: {str(e)}"
        }).eq("id", pipeline_id).execute()
        print(f"  Failed: {e}")
        raise


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("name", nargs="?", help="Research a specific artist by name")
    parser.add_argument("--limit", type=int, default=None, help="Max number of pending artists to process")
    parser.add_argument("--tradition", type=str, default=None, help="Filter by tradition slug (matches notes field)")
    args = parser.parse_args()

    if args.name:
        existing = supabase.table("artist_pipeline").select("id, status").eq("name", args.name).execute()
        if existing.data:
            row = existing.data[0]
            if row["status"] == "done":
                print(f"'{args.name}' already researched. Re-running.")
                supabase.table("artist_pipeline").update({"status": "pending"}).eq("id", row["id"]).execute()
            pipeline_id = row["id"]
        else:
            result = supabase.table("artist_pipeline").insert({
                "name": args.name,
                "status": "pending"
            }).execute()
            pipeline_id = result.data[0]["id"]

        research_artist(pipeline_id, args.name)

    else:
        query = supabase.table("artist_pipeline").select("id, name, notes").eq("status", "pending")
        if args.tradition:
            query = query.ilike("notes", f"%{args.tradition}%")
        if args.limit:
            query = query.limit(args.limit)
        rows = query.execute()

        if not rows.data:
            print("No pending artists found.")
            return

        print(f"Processing {len(rows.data)} artist(s)" + (f" [{args.tradition}]" if args.tradition else ""))
        for row in rows.data:
            research_artist(row["id"], row["name"])

    print("\nAll done.")


if __name__ == "__main__":
    main()
