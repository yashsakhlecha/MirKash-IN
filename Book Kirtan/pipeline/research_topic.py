"""
Topic research using Exa deep search.
Searches multiple angles on a kirtan tradition and prints consolidated findings.

Usage:
  python research_topic.py "Hare Krishna Kirtan"
"""

import json
import sys
import os
from dotenv import load_dotenv
from exa_py import Exa

load_dotenv()

EXA_API_KEY = os.environ["EXA_API_KEY"]
exa = Exa(api_key=EXA_API_KEY)


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


QUERIES = [
    {
        "angle": "Philosophy & Meaning",
        "query": "Hare Krishna kirtan Maha Mantra meaning philosophy Gaudiya Vaishnavism bhakti yoga",
    },
    {
        "angle": "Experience & How It Feels",
        "query": "what does Hare Krishna kirtan feel like personal experience first time chanting",
    },
    {
        "angle": "Occasions & Booking India",
        "query": "Hare Krishna kirtan occasions India wedding Janmashtami home puja event booking ISKCON",
    },
    {
        "angle": "Instruments & Practice",
        "query": "Hare Krishna kirtan instruments mridanga kartal harmonium call response practice guide",
    },
    {
        "angle": "Benefits & Transformation",
        "query": "Hare Krishna kirtan benefits mental peace transformation chanting Maha Mantra spiritual effects",
    },
    {
        "angle": "Artist Perspectives",
        "query": "Hare Krishna kirtan artist singer ISKCON kirtan leader performer India",
    },
]


def search_angle(angle: str, query: str) -> dict:
    print(f"  Searching: {angle}...")
    response = exa.search(
        query,
        type="neural",
        num_results=5,
        contents={"text": {"max_characters": 2000}, "highlights": True},
    )
    results = []
    for r in response.results:
        results.append({
            "title": r.title,
            "url": r.url,
            "text": getattr(r, "text", None),
            "highlights": to_jsonable(r.highlights) if r.highlights else [],
        })
    return {"angle": angle, "query": query, "results": results}


def main():
    topic = sys.argv[1] if len(sys.argv) > 1 else "Hare Krishna Kirtan"
    print(f"\n=== Deep Research: {topic} ===\n")

    all_findings = []
    for q in QUERIES:
        data = search_angle(q["angle"], q["query"])
        all_findings.append(data)

    # Print consolidated output
    for finding in all_findings:
        print(f"\n{'='*60}")
        print(f"ANGLE: {finding['angle']}")
        print(f"{'='*60}")
        for r in finding["results"]:
            print(f"\n--- {r['title']} ---")
            print(f"URL: {r['url']}")
            if r.get("highlights"):
                for h in r["highlights"][:3]:
                    print(f"  • {h}")
            elif r.get("text"):
                print(r["text"][:800])

    # Save to JSON
    out_file = f"research_{topic.lower().replace(' ', '_')}.json"
    with open(out_file, "w") as f:
        json.dump(all_findings, f, indent=2)
    print(f"\n\nFull results saved to: {out_file}")


if __name__ == "__main__":
    main()
