#!/usr/bin/env python3
"""
DataForSEO v2 — additional organic research + keyword research for mirkash.com
"""

import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

AUTH    = "Basic eWFzaEBnZXR3eWxkLmluOjgyNWEwNTI2M2UwNmRjNTY="
HEADERS = {"Authorization": AUTH, "Content-Type": "application/json"}
BASE    = "https://api.dataforseo.com/v3"
IN      = 2356
LANG    = "en"

def post(endpoint, payload):
    url  = f"{BASE}/{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(url, data=data, headers=HEADERS, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "detail": e.read().decode("utf-8")}
    except Exception as ex:
        return {"error": str(ex)}

def task_result(resp):
    try:
        t = resp.get("tasks", [{}])[0]
        if t.get("status_code") != 20000:
            return None, t.get("status_message", "task error")
        results = t.get("result") or []
        return (results[0] if results else {}), None
    except Exception as ex:
        return None, str(ex)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


# ── Organic Research ──────────────────────────────────────────────────────────
DOMAINS = ["rijac.com", "nappadori.com", "nooe.co"]

def organic_research():
    log("=== Organic Research ===")
    results = {}

    for domain in DOMAINS:
        log(f"  ranked_keywords: {domain}")
        rk_resp = post("dataforseo_labs/google/ranked_keywords/live", [
            {
                "target":        domain,
                "location_code": IN,
                "language_code": LANG,
                "limit":         20,
                "order_by":      ["keyword_data.keyword_info.search_volume,desc"],
            }
        ])
        rk_result, rk_err = task_result(rk_resp)

        top_keywords = []
        overview = {}
        if rk_result:
            m = (rk_result.get("metrics") or {}).get("organic", {})
            overview = {
                "estimated_monthly_traffic": m.get("etv"),
                "total_keywords":            m.get("count"),
                "pos_1":                     m.get("pos_1"),
            }
            for item in (rk_result.get("items") or []):
                kd   = item.get("keyword_data", {})
                ki   = kd.get("keyword_info", {})
                serp = item.get("ranked_serp_element", {}).get("serp_item", {})
                top_keywords.append({
                    "keyword":       kd.get("keyword"),
                    "search_volume": ki.get("search_volume"),
                    "position":      serp.get("rank_absolute"),
                    "ranking_url":   serp.get("url"),
                })

        results[domain] = {
            "location":        "IN",
            "overview":        overview,
            "top_20_keywords": top_keywords,
            "error":           rk_err,
        }
        log(f"    traffic={overview.get('estimated_monthly_traffic')}  keywords={overview.get('total_keywords')}  top_kw={len(top_keywords)}")
        time.sleep(1)

    return results


# ── Keyword Research ──────────────────────────────────────────────────────────
KEYWORDS = [
    "vegan leather bags india",
    "vegan handbags india",
    "apple leather handbag",
    "apple leather bag india",
    "bags under 10000 india",
    "bags under 15000 india",
    "premium bags women",
    "branded bags women india",
    "gift for women india handbag",
    "women's bags india",
    "luxury bags india",
    "best bags women india",
]

def keyword_research():
    log("=== Keyword Research ===")
    log(f"  keyword_overview: {len(KEYWORDS)} keywords (India)...")

    resp = post("dataforseo_labs/google/keyword_overview/live", [
        {"keywords": KEYWORDS, "location_code": IN, "language_code": LANG}
    ])
    result, err = task_result(resp)

    kw_data = {}
    errors  = []

    if err:
        errors.append({"step": "keyword_overview", "error": err})
        log(f"  ERROR: {err}")
    elif result:
        for item in (result.get("items") or []):
            kw = item.get("keyword")
            if not kw:
                continue
            ki = item.get("keyword_info", {}) or {}
            kp = item.get("keyword_properties", {}) or {}
            si = item.get("search_intent_info", {}) or {}
            kw_data[kw] = {
                "search_volume":      ki.get("search_volume"),
                "cpc":                ki.get("cpc"),
                "competition":        ki.get("competition"),
                "competition_level":  ki.get("competition_level"),
                "keyword_difficulty": kp.get("keyword_difficulty"),
                "search_intent":      si.get("main_intent"),
                "secondary_intents":  si.get("foreign_intent"),
                "search_volume_trend": ki.get("search_volume_trend"),
                "monthly_searches":   ki.get("monthly_searches"),
            }

        log(f"  Got data for {len(kw_data)}/{len(KEYWORDS)} keywords")
        missing = [k for k in KEYWORDS if k not in kw_data]
        if missing:
            log(f"  No data for: {missing}")
            for k in missing:
                kw_data[k] = {"search_volume": None, "note": "no data from API"}

    return {"data": kw_data, "errors": errors}


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    log("Starting DataForSEO v2 research...")
    output = {
        "generated_at":     datetime.now(timezone.utc).isoformat(),
        "organic_research": {},
        "keyword_research": {},
    }

    try:
        output["organic_research"] = organic_research()
    except Exception as e:
        output["organic_research"] = {"fatal_error": str(e)}
        log(f"FATAL organic: {e}")

    try:
        output["keyword_research"] = keyword_research()
    except Exception as e:
        output["keyword_research"] = {"fatal_error": str(e)}
        log(f"FATAL keywords: {e}")

    out_path = "/Users/rohan/Coding/competitor_seo_research_v2.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    log(f"Saved → {out_path}")

    print(f"\n{'='*50}")
    print(f"  Organic domains : {len(output['organic_research'])}")
    print(f"  Keywords        : {len(output['keyword_research'].get('data', {}))}")

if __name__ == "__main__":
    main()
