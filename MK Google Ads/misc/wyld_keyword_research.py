from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

client = GoogleAdsClient.load_from_storage("google-ads.yaml")
customer_id = "6186258758"
kp_idea_service = client.get_service("KeywordPlanIdeaService")
geo_service = client.get_service("GeoTargetConstantService")

INDIA = "2356"
USA = "2840"

def fetch_ideas(seed_keywords, geo_id):
    request = client.get_type("GenerateKeywordIdeasRequest")
    request.customer_id = customer_id
    request.language = client.get_service("GoogleAdsService").language_constant_path("1000")
    request.geo_target_constants.append(geo_service.geo_target_constant_path(geo_id))
    request.include_adult_keywords = False
    request.keyword_plan_network = client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
    request.keyword_seed.keywords.extend(seed_keywords)

    results = []
    try:
        response = kp_idea_service.generate_keyword_ideas(request=request)
        for idea in response:
            kw = idea.text
            m = idea.keyword_idea_metrics
            vol = m.avg_monthly_searches
            comp = m.competition.name
            low = m.low_top_of_page_bid_micros / 1_000_000 if m.low_top_of_page_bid_micros else 0
            high = m.high_top_of_page_bid_micros / 1_000_000 if m.high_top_of_page_bid_micros else 0
            results.append((kw, vol, comp, low, high))
    except GoogleAdsException as ex:
        print(f"  ERROR: {ex.error.code().name} — {ex.failure.errors[0].message}")
        return []

    results.sort(key=lambda x: x[1], reverse=True)
    return results

def print_table(results, label, sym="₹", min_vol=10, top=40):
    filtered = [r for r in results if r[1] >= min_vol]
    print(f"\n{'='*110}")
    print(f"  {label}  ({len(filtered)} keywords with vol ≥ {min_vol})")
    print(f"{'='*110}")
    print(f"  {'Keyword':<55} {'Vol/mo':>8} {'Competition':>12} {'Low CPC':>10} {'High CPC':>10}")
    print(f"  {'-'*103}")
    for kw, vol, comp, low, high in filtered[:top]:
        print(f"  {kw:<55} {vol:>8,} {comp:>12} {sym}{low:>8.2f} {sym}{high:>8.2f}")
    if len(filtered) > top:
        print(f"  ... and {len(filtered) - top} more")
    top_vol = sum(r[1] for r in filtered[:top])
    print(f"\n  Top-{top} combined monthly search volume: {top_vol:,}")
    return filtered


# ─────────────────────────────────────────────────────────────────
# CLUSTER 1: Influencer Marketing Platform — INDIA
# ─────────────────────────────────────────────────────────────────
influencer_platform_india_seeds = [
    "influencer marketing platform india",
    "micro influencer marketing india",
    "nano influencer marketing india",
    "influencer marketing agency india",
    "instagram influencer marketing india",
    "influencer marketing for brands india",
    "influencer marketing company india",
    "best influencer marketing platform india",
]
r1 = fetch_ideas(influencer_platform_india_seeds, INDIA)
all_india_influencer = print_table(r1, "CLUSTER 1 — Influencer Marketing Platform (India)", sym="₹")


# ─────────────────────────────────────────────────────────────────
# CLUSTER 2: UGC Content & Creator Economy — INDIA
# ─────────────────────────────────────────────────────────────────
ugc_india_seeds = [
    "ugc content india",
    "user generated content marketing india",
    "ugc creator india",
    "ugc marketing platform india",
    "ugc agency india",
    "ugc content for brands india",
    "creator economy india",
    "content creator marketing india",
]
r2 = fetch_ideas(ugc_india_seeds, INDIA)
all_india_ugc = print_table(r2, "CLUSTER 2 — UGC Content & Creator Economy (India)", sym="₹")


# ─────────────────────────────────────────────────────────────────
# CLUSTER 3: Affordable / Performance Marketing — INDIA
# ─────────────────────────────────────────────────────────────────
affordable_india_seeds = [
    "affordable influencer marketing india",
    "cheap influencer marketing india",
    "performance based influencer marketing india",
    "pay per post influencer marketing india",
    "influencer marketing cost india",
    "influencer marketing roi india",
    "influencer marketing for small business india",
    "influencer marketing for startups india",
    "d2c influencer marketing india",
]
r3 = fetch_ideas(affordable_india_seeds, INDIA)
all_india_affordable = print_table(r3, "CLUSTER 3 — Affordable / Performance Marketing (India)", sym="₹")


# ─────────────────────────────────────────────────────────────────
# CLUSTER 4: Social Commerce / Cashback / Creator Cards — INDIA
# ─────────────────────────────────────────────────────────────────
social_commerce_india_seeds = [
    "social commerce india",
    "earn money instagram india",
    "earn cashback instagram india",
    "monetize instagram india",
    "instagram cashback india",
    "influencer cashback india",
    "social currency india",
    "brand ambassador program india",
    "influencer rewards program india",
    "get paid to post on instagram india",
]
r4 = fetch_ideas(social_commerce_india_seeds, INDIA)
all_india_social = print_table(r4, "CLUSTER 4 — Social Commerce & Creator Monetization (India)", sym="₹")


# ─────────────────────────────────────────────────────────────────
# CLUSTER 5: UGC Platform — GLOBAL (USA)
# ─────────────────────────────────────────────────────────────────
ugc_global_seeds = [
    "ugc content platform",
    "ugc creator platform",
    "ugc marketing platform",
    "ugc agency",
    "user generated content platform",
    "buy ugc content",
    "ugc content for ads",
    "ugc video platform",
    "ugc content creator marketplace",
]
r5 = fetch_ideas(ugc_global_seeds, USA)
all_usa_ugc = print_table(r5, "CLUSTER 5 — UGC Platform (Global / USA)", sym="$")


# ─────────────────────────────────────────────────────────────────
# CLUSTER 6: Micro / Nano Influencer Marketing — GLOBAL (USA)
# ─────────────────────────────────────────────────────────────────
micro_global_seeds = [
    "micro influencer marketing platform",
    "nano influencer marketing",
    "micro influencer agency",
    "micro influencer platform",
    "nano influencer platform",
    "influencer marketing for small brands",
    "affordable influencer marketing platform",
    "performance influencer marketing platform",
    "influencer seeding platform",
]
r6 = fetch_ideas(micro_global_seeds, USA)
all_usa_micro = print_table(r6, "CLUSTER 6 — Micro/Nano Influencer Marketing (Global / USA)", sym="$")


# ─────────────────────────────────────────────────────────────────
# CLUSTER 7: Competitor + Category keywords — INDIA
# ─────────────────────────────────────────────────────────────────
competitor_india_seeds = [
    "one impression influencer platform",
    "grynow influencer marketing",
    "chtrbox influencer platform",
    "qoruz influencer platform",
    "cherry app india creators",
    "influencer marketing platform india free",
    "instagram influencer platform india",
    "influencer discovery platform india",
    "influencer marketplace india",
]
r7 = fetch_ideas(competitor_india_seeds, INDIA)
all_india_comp = print_table(r7, "CLUSTER 7 — Competitor & Category Keywords (India)", sym="₹")


# ─────────────────────────────────────────────────────────────────
# SUMMARY: All India keywords sorted by volume
# ─────────────────────────────────────────────────────────────────
print(f"\n\n{'#'*110}")
print("  MASTER INDIA LIST — All Unique Keywords (vol ≥ 50), sorted by volume")
print(f"{'#'*110}")

all_india = all_india_influencer + all_india_ugc + all_india_affordable + all_india_social + all_india_comp
seen = set()
deduped = []
for row in sorted(all_india, key=lambda x: x[1], reverse=True):
    if row[0] not in seen and row[1] >= 50:
        seen.add(row[0])
        deduped.append(row)

print(f"\n  {'Keyword':<55} {'Vol/mo':>8} {'Competition':>12} {'Low CPC':>10} {'High CPC':>10}")
print(f"  {'-'*103}")
for kw, vol, comp, low, high in deduped[:60]:
    print(f"  {kw:<55} {vol:>8,} {comp:>12} ₹{low:>8.2f} ₹{high:>8.2f}")
print(f"\n  Total unique India keywords (vol ≥ 50): {len(deduped)}")


# ─────────────────────────────────────────────────────────────────
# SUMMARY: All Global keywords sorted by volume
# ─────────────────────────────────────────────────────────────────
print(f"\n\n{'#'*110}")
print("  MASTER GLOBAL LIST — All Unique Keywords (vol ≥ 100), sorted by volume")
print(f"{'#'*110}")

all_global = all_usa_ugc + all_usa_micro
seen_g = set()
deduped_g = []
for row in sorted(all_global, key=lambda x: x[1], reverse=True):
    if row[0] not in seen_g and row[1] >= 100:
        seen_g.add(row[0])
        deduped_g.append(row)

print(f"\n  {'Keyword':<55} {'Vol/mo':>8} {'Competition':>12} {'Low CPC':>10} {'High CPC':>10}")
print(f"  {'-'*103}")
for kw, vol, comp, low, high in deduped_g[:60]:
    print(f"  {kw:<55} {vol:>8,} {comp:>12} ${low:>8.2f} ${high:>8.2f}")
print(f"\n  Total unique Global keywords (vol ≥ 100): {len(deduped_g)}")
