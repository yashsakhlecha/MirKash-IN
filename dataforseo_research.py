#!/usr/bin/env python3
"""
DataForSEO Competitive Research for mirkash.com
Pulls organic research, keyword data, and SERP analysis → saves to competitor_seo_research.json
"""

import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

# ── Credentials ───────────────────────────────────────────────────────────────
AUTH    = "Basic eWFzaEBnZXR3eWxkLmluOjgyNWEwNTI2M2UwNmRjNTY="
HEADERS = {"Authorization": AUTH, "Content-Type": "application/json"}
BASE    = "https://api.dataforseo.com/v3"

IN   = 2356   # India
US   = 2840   # United States
LANG = "en"

# ── HTTP helpers ──────────────────────────────────────────────────────────────
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
    """Return the first result block from a DataForSEO response, or {}."""
    try:
        r = resp.get("tasks", [{}])[0]
        if r.get("status_code") != 20000:
            return None, r.get("status_message", "task error")
        results = r.get("result") or []
        return (results[0] if results else {}), None
    except Exception as ex:
        return None, str(ex)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


# ── Step 1 — Competitor Organic Research ──────────────────────────────────────
COMPETITORS = [
    {"domain": "mirkash.com",            "location_code": IN},
    {"domain": "mirkash.in",             "location_code": IN},
    {"domain": "charleskeith.in",        "location_code": IN},
    {"domain": "miraggiolife.com",       "location_code": IN},
    {"domain": "da-milano.in",           "location_code": IN},
    {"domain": "outhouse-jewellery.com", "location_code": IN},
    {"domain": "hidesign.com",           "location_code": IN},
    {"domain": "greenhermitage.com",     "location_code": IN},
    {"domain": "sarjaa.in",              "location_code": IN},
    {"domain": "mattandnat.com",         "location_code": US},
]

def step1_organic_research():
    log("=== STEP 1: Organic Research ===")
    organic_research = {}

    for comp in COMPETITORS:
        domain = comp["domain"]
        loc    = comp["location_code"]

        # ── Domain Rank Overview ──────────────────────────────────
        log(f"  domain_rank_overview: {domain}")
        ov_resp = post("dataforseo_labs/google/domain_rank_overview/live", [
            {"target": domain, "location_code": loc, "language_code": LANG}
        ])
        ov_result, ov_err = task_result(ov_resp)
        overview = {}
        if ov_result:
            items = ov_result.get("items") or []
            if items:
                m = items[0].get("metrics", {}).get("organic", {})
            else:
                # Some plans return metrics directly on result
                m = ov_result.get("metrics", {})
                if isinstance(m, dict):
                    m = m.get("organic", {}) or m
            overview = {
                "estimated_monthly_traffic": m.get("etv"),
                "total_keywords":            m.get("count"),
                "pos_1":                     m.get("pos_1"),
            }
        time.sleep(0.6)

        # ── Ranked Keywords ───────────────────────────────────────
        log(f"  ranked_keywords:      {domain}")
        rk_resp = post("dataforseo_labs/google/ranked_keywords/live", [
            {
                "target":        domain,
                "location_code": loc,
                "language_code": LANG,
                "limit":         20,
                "order_by":      ["keyword_data.keyword_info.search_volume,desc"],
            }
        ])
        rk_result, rk_err = task_result(rk_resp)
        top_keywords = []
        metrics_overview = {}
        if rk_result:
            # Aggregate metrics (total traffic, keyword count) live here
            m = (rk_result.get("metrics") or {}).get("organic", {})
            metrics_overview = {
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

        # Use ranked_keywords metrics if overview came back empty
        if not overview.get("estimated_monthly_traffic") and metrics_overview.get("estimated_monthly_traffic"):
            overview = metrics_overview

        organic_research[domain] = {
            "location":        "IN" if loc == IN else "US",
            "overview":        overview,
            "overview_error":  ov_err,
            "top_20_keywords": top_keywords,
            "ranked_error":    rk_err,
        }
        log(f"    traffic={overview.get('estimated_monthly_traffic')}  keywords={overview.get('total_keywords')}  top_kw_found={len(top_keywords)}")
        time.sleep(1)

    return organic_research


# ── Step 2 — Keyword Research ──────────────────────────────────────────────────
KEYWORDS = [
    "handbags women india",
    "luxury handbags india",
    "best handbag brands india",
    "designer bags india",
    "women's bags under 10000",
    "women's bags under 15000",
    "charles and keith india",
    "vegan leather handbag india",
    "cruelty free bags india",
    "apple leather bag",
    "cactus leather bag",
    "plant based leather bag",
    "premium crossbody bag women india",
    "everyday luxury bag india",
    "sustainable handbags india",
    "best quality handbag women",
    "vegan handbag brand india",
    "handbag gift women india",
    "outhouse bags india",
    "miraggio bags",
    "hidesign bags",
    "what is vegan leather",
    "vegan leather vs real leather",
    "best women's bags 2025",
]

def step2_keyword_research():
    log("=== STEP 2: Keyword Research ===")
    keyword_results = {}
    errors = []

    log(f"  keyword_overview: {len(KEYWORDS)} keywords (India)...")
    resp = post("dataforseo_labs/google/keyword_overview/live", [
        {"keywords": KEYWORDS, "location_code": IN, "language_code": LANG}
    ])
    result, err = task_result(resp)
    if err:
        errors.append({"step": "keyword_overview", "error": err})
        log(f"  ERROR: {err}")
    elif result:
        for item in (result.get("items") or []):
            kw  = item.get("keyword")
            if not kw:
                continue
            ki  = item.get("keyword_info", {}) or {}
            kp  = item.get("keyword_properties", {}) or {}
            si  = item.get("search_intent_info", {}) or {}
            keyword_results[kw] = {
                "search_volume":      ki.get("search_volume"),
                "monthly_searches":   ki.get("monthly_searches"),
                "cpc":                ki.get("cpc"),
                "competition":        ki.get("competition"),
                "competition_level":  ki.get("competition_level"),
                "keyword_difficulty": kp.get("keyword_difficulty"),
                "search_intent":      si.get("main_intent"),
                "secondary_intents":  si.get("foreign_intent"),
                "search_volume_trend": ki.get("search_volume_trend"),
            }
        log(f"  Got data for {len(keyword_results)}/{len(KEYWORDS)} keywords")
        # Log any keywords that came back empty
        missing = [k for k in KEYWORDS if k not in keyword_results]
        if missing:
            log(f"  No data returned for: {missing}")
            for k in missing:
                keyword_results[k] = {"search_volume": None, "note": "no data from API"}

    return {"data": keyword_results, "errors": errors}


# ── Step 3 — SERP Analysis ────────────────────────────────────────────────────
SERP_KEYWORDS = [
    "best handbag brands india",
    "premium handbags women india",
    "vegan leather handbag india",
    "cruelty free bags india",
    "apple leather bag",
]

def step3_serp_analysis():
    log("=== STEP 3: SERP Analysis ===")
    serp_results = {}

    for kw in SERP_KEYWORDS:
        log(f"  SERP: {kw}")
        resp = post("serp/google/organic/live/advanced", [
            {
                "keyword":       kw,
                "location_code": IN,
                "language_code": LANG,
                "device":        "desktop",
                "os":            "windows",
                "depth":         10,
            }
        ])
        result, err = task_result(resp)
        top10 = []
        if result:
            for item in (result.get("items") or []):
                if item.get("type") == "organic":
                    top10.append({
                        "position":    item.get("rank_absolute"),
                        "title":       item.get("title"),
                        "url":         item.get("url"),
                        "domain":      item.get("domain"),
                        "description": item.get("description"),
                    })
        serp_results[kw] = {"top_10": top10, "error": err}
        log(f"    organic results: {len(top10)}")
        time.sleep(1)

    return serp_results


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    log("Starting DataForSEO research for mirkash.com...")
    output = {
        "generated_at":     datetime.now(timezone.utc).isoformat(),
        "organic_research": {},
        "keyword_research": {},
        "serp_analysis":    {},
    }

    try:
        output["organic_research"] = step1_organic_research()
    except Exception as e:
        output["organic_research"] = {"fatal_error": str(e)}
        log(f"FATAL Step 1: {e}")

    try:
        output["keyword_research"] = step2_keyword_research()
    except Exception as e:
        output["keyword_research"] = {"fatal_error": str(e)}
        log(f"FATAL Step 2: {e}")

    try:
        output["serp_analysis"] = step3_serp_analysis()
    except Exception as e:
        output["serp_analysis"] = {"fatal_error": str(e)}
        log(f"FATAL Step 3: {e}")

    out_path = "/Users/rohan/Coding/competitor_seo_research.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    log(f"Saved → {out_path}")

    or_data = output.get("organic_research", {})
    kw_data = output.get("keyword_research", {}).get("data", {})
    serp    = output.get("serp_analysis", {})
    print(f"\n{'='*50}")
    print(f"  Organic domains processed : {len(or_data)}")
    print(f"  Keywords researched       : {len(kw_data)}")
    print(f"  SERP keywords analysed    : {len(serp)}")

if __name__ == "__main__":
    main()
