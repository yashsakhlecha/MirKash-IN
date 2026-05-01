from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

client = GoogleAdsClient.load_from_storage("google-ads.yaml")
customer_id = "6186258758"
kp_idea_service = client.get_service("KeywordPlanIdeaService")
geo_service = client.get_service("GeoTargetConstantService")

INDIA = "2356"
USA   = "2840"
UK    = "2826"
CANADA = "2124"
AUSTRALIA = "2036"

def fetch_ideas(seed_keywords, geo_id, language_id="1000"):
    request = client.get_type("GenerateKeywordIdeasRequest")
    request.customer_id = customer_id
    request.language = client.get_service("GoogleAdsService").language_constant_path(language_id)
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
            low  = m.low_top_of_page_bid_micros  / 1_000_000 if m.low_top_of_page_bid_micros  else 0
            high = m.high_top_of_page_bid_micros / 1_000_000 if m.high_top_of_page_bid_micros else 0
            results.append((kw, vol, comp, low, high))
    except GoogleAdsException as ex:
        print(f"  ERROR: {ex.error.code().name} — {ex.failure.errors[0].message}")
        return []

    results.sort(key=lambda x: x[1], reverse=True)
    return results


def print_table(results, label, sym="₹", min_vol=10, top=50):
    filtered = [r for r in results if r[1] >= min_vol]
    print(f"\n{'='*120}")
    print(f"  {label}  ({len(filtered)} keywords with vol ≥ {min_vol})")
    print(f"{'='*120}")
    print(f"  {'Keyword':<60} {'Vol/mo':>8} {'Competition':>14} {'Low CPC':>10} {'High CPC':>10}")
    print(f"  {'-'*108}")
    for kw, vol, comp, low, high in filtered[:top]:
        print(f"  {kw:<60} {vol:>8,} {comp:>14} {sym}{low:>8.2f} {sym}{high:>8.2f}")
    if len(filtered) > top:
        print(f"  ... and {len(filtered) - top} more keywords")
    top_vol = sum(r[1] for r in filtered[:top])
    print(f"\n  Top-{min(top, len(filtered))} combined monthly search volume: {top_vol:,}")
    return filtered


# ─────────────────────────────────────────────────────────────────────────────
# CLUSTER 1: Core Booking Intent — INDIA
# ─────────────────────────────────────────────────────────────────────────────
core_booking_india = [
    "book kirtan artist",
    "hire kirtan singer",
    "kirtan booking",
    "kirtan for events",
    "kirtan artist booking",
    "kirtan performer booking",
    "kirtan group booking",
    "book kirtan online",
    "kirtan artists near me",
    "book kirtan singers",
]
r1 = fetch_ideas(core_booking_india, INDIA)
a1 = print_table(r1, "CLUSTER 1 — Core Booking Intent (India)", sym="₹")

# ─────────────────────────────────────────────────────────────────────────────
# CLUSTER 2: Wedding & Ceremony Kirtan — INDIA
# ─────────────────────────────────────────────────────────────────────────────
wedding_kirtan_india = [
    "kirtan for wedding",
    "kirtan for shaadi",
    "wedding kirtan group",
    "kirtan at wedding ceremony",
    "kirtan singers for wedding",
    "shabad kirtan for wedding",
    "kirtan for anand karaj",
    "kirtan for griha pravesh",
    "kirtan for engagement",
    "kirtan for reception",
    "kirtan for vivah",
]
r2 = fetch_ideas(wedding_kirtan_india, INDIA)
a2 = print_table(r2, "CLUSTER 2 — Wedding & Ceremony Kirtan (India)", sym="₹")

# ─────────────────────────────────────────────────────────────────────────────
# CLUSTER 3: Religious Event Kirtan — INDIA
# ─────────────────────────────────────────────────────────────────────────────
religious_event_india = [
    "kirtan for puja",
    "kirtan for jagran",
    "kirtan for satyanarayan puja",
    "kirtan for satsang",
    "kirtan for bhagwat",
    "kirtan for havan",
    "kirtan for navratri",
    "kirtan for diwali puja",
    "kirtan for bhumi pujan",
    "kirtan for akhand path",
    "kirtan for ramayan path",
    "kirtan for shrimad bhagwat katha",
    "bhajan kirtan group for events",
    "kirtan for temple events",
    "kirtan for spiritual events",
]
r3 = fetch_ideas(religious_event_india, INDIA)
a3 = print_table(r3, "CLUSTER 3 — Religious Events & Puja Kirtan (India)", sym="₹")

# ─────────────────────────────────────────────────────────────────────────────
# CLUSTER 4: Bhajan & Devotional Music Booking — INDIA
# ─────────────────────────────────────────────────────────────────────────────
bhajan_india = [
    "book bhajan singer",
    "hire bhajan singer",
    "bhajan singer for events",
    "bhajan group for events",
    "devotional music for events",
    "bhajan mandali booking",
    "bhajan singer near me",
    "bhajan artist booking",
    "bhajan performers for hire",
    "book devotional singer",
    "spiritual music for events",
    "religious singer for events",
]
r4 = fetch_ideas(bhajan_india, INDIA)
a4 = print_table(r4, "CLUSTER 4 — Bhajan & Devotional Music Booking (India)", sym="₹")

# ─────────────────────────────────────────────────────────────────────────────
# CLUSTER 5: Specific Kirtan Genres & Styles — INDIA
# ─────────────────────────────────────────────────────────────────────────────
kirtan_styles_india = [
    "shabad kirtan",
    "gurbani kirtan artist",
    "gurbani kirtan booking",
    "hare krishna kirtan",
    "iskcon kirtan",
    "vaishnav kirtan",
    "sufi kirtan",
    "kirtan wallah",
    "kirtan band",
    "kirtan mandali",
    "kirtan party booking",
    "kirtan jatha booking",
    "kirtan singers india",
]
r5 = fetch_ideas(kirtan_styles_india, INDIA)
a5 = print_table(r5, "CLUSTER 5 — Kirtan Genres & Styles (India)", sym="₹")

# ─────────────────────────────────────────────────────────────────────────────
# CLUSTER 6: Broad Religious Event Services — INDIA (TAM sizing)
# ─────────────────────────────────────────────────────────────────────────────
religious_services_india = [
    "book pandit for puja",
    "book priest for wedding",
    "book pundit online",
    "online pandit booking",
    "puja booking platform",
    "book astrologer online",
    "spiritual services booking",
    "book musician for events",
    "event performer booking india",
    "hire artist for event india",
    "book entertainer india",
    "cultural event performers india",
    "religious event planning india",
    "puja samagri online",
    "book kathak dancer",
    "book classical musician",
]
r6 = fetch_ideas(religious_services_india, INDIA)
a6 = print_table(r6, "CLUSTER 6 — Broader Religious/Spiritual Services (India) — TAM Sizing", sym="₹")

# ─────────────────────────────────────────────────────────────────────────────
# CLUSTER 7: Diaspora Market — USA (Indian community abroad)
# ─────────────────────────────────────────────────────────────────────────────
diaspora_usa = [
    "kirtan artists usa",
    "book kirtan usa",
    "hire kirtan singer usa",
    "kirtan for events usa",
    "kirtan group near me",
    "indian devotional music booking",
    "book bhajan singer usa",
    "kirtan near me",
    "hire kirtan group",
    "gurbani kirtan usa",
    "shabad kirtan usa",
    "hindu religious music usa",
    "kirtan musicians for hire",
    "book indian spiritual singer",
    "sikh kirtan usa",
]
r7 = fetch_ideas(diaspora_usa, USA)
a7 = print_table(r7, "CLUSTER 7 — Diaspora Market (USA)", sym="$")

# ─────────────────────────────────────────────────────────────────────────────
# CLUSTER 8: Diaspora Market — UK
# ─────────────────────────────────────────────────────────────────────────────
diaspora_uk = [
    "kirtan artists uk",
    "book kirtan uk",
    "hire kirtan singer uk",
    "kirtan for events uk",
    "book bhajan singer uk",
    "gurbani kirtan uk",
    "hindu religious event uk",
    "kirtan group uk",
    "spiritual music uk",
    "sikh kirtan uk",
]
r8 = fetch_ideas(diaspora_uk, UK)
a8 = print_table(r8, "CLUSTER 8 — Diaspora Market (UK)", sym="£")

# ─────────────────────────────────────────────────────────────────────────────
# CLUSTER 9: Competitor & Platform Discovery — INDIA
# ─────────────────────────────────────────────────────────────────────────────
competitors_india = [
    "book my kirtan",
    "kirtan booking platform india",
    "kirtan artist marketplace india",
    "bookmyshow religious events",
    "sulekha kirtan",
    "urban company puja",
    "puja app india",
    "spiritual platform india",
    "devotional artist platform india",
    "online kirtan artist",
    "best kirtan artist india",
    "famous kirtan singers india",
    "top bhajan singers india",
    "religious artist management india",
]
r9 = fetch_ideas(competitors_india, INDIA)
a9 = print_table(r9, "CLUSTER 9 — Competitor & Platform Discovery (India)", sym="₹")

# ─────────────────────────────────────────────────────────────────────────────
# CLUSTER 10: Corporate & Social Events — INDIA
# ─────────────────────────────────────────────────────────────────────────────
corporate_india = [
    "kirtan for corporate event",
    "kirtan for office event",
    "kirtan for community event",
    "kirtan for birthday party",
    "kirtan for anniversary",
    "kirtan for house warming",
    "kirtan for mundan ceremony",
    "kirtan for name ceremony",
    "kirtan for namkaran",
    "kirtan for shraadh",
    "kirtan for death anniversary",
    "kirtan for prayer meeting",
    "kirtan for memorial service",
]
r10 = fetch_ideas(corporate_india, INDIA)
a10 = print_table(r10, "CLUSTER 10 — Life Events & Social Occasions (India)", sym="₹")


# ─────────────────────────────────────────────────────────────────────────────
# MASTER INDIA SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n\n{'#'*120}")
print("  MASTER INDIA LIST — All Unique Keywords (vol ≥ 10), sorted by volume")
print(f"{'#'*120}")

all_india_raw = a1 + a2 + a3 + a4 + a5 + a6 + a9 + a10
seen = set()
deduped_india = []
for row in sorted(all_india_raw, key=lambda x: x[1], reverse=True):
    if row[0] not in seen and row[1] >= 10:
        seen.add(row[0])
        deduped_india.append(row)

print(f"\n  {'Keyword':<60} {'Vol/mo':>8} {'Competition':>14} {'Low CPC':>10} {'High CPC':>10}")
print(f"  {'-'*108}")
for kw, vol, comp, low, high in deduped_india[:80]:
    print(f"  {kw:<60} {vol:>8,} {comp:>14} ₹{low:>8.2f} ₹{high:>8.2f}")
print(f"\n  Total unique India keywords (vol ≥ 10): {len(deduped_india)}")
print(f"  Total addressable search volume (top 80): {sum(r[1] for r in deduped_india[:80]):,}/mo")

# ─────────────────────────────────────────────────────────────────────────────
# SEO OPPORTUNITY SCORING: Low competition + decent volume
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n\n{'#'*120}")
print("  SEO SWEET SPOTS — Low/Medium Competition, Vol ≥ 10 (India)")
print(f"{'#'*120}")
print(f"\n  {'Keyword':<60} {'Vol/mo':>8} {'Competition':>14} {'Low CPC':>10} {'High CPC':>10}")
print(f"  {'-'*108}")
seo_opps = [r for r in deduped_india if r[2] in ("LOW", "MEDIUM") and r[1] >= 10]
seo_opps.sort(key=lambda x: x[1], reverse=True)
for kw, vol, comp, low, high in seo_opps[:50]:
    print(f"  {kw:<60} {vol:>8,} {comp:>14} ₹{low:>8.2f} ₹{high:>8.2f}")
print(f"\n  Total SEO opportunities: {len(seo_opps)}")

# ─────────────────────────────────────────────────────────────────────────────
# MASTER GLOBAL DIASPORA SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n\n{'#'*120}")
print("  DIASPORA MARKETS — All Unique Keywords (vol ≥ 10), sorted by volume")
print(f"{'#'*120}")

all_global_raw = a7 + a8
seen_g = set()
deduped_global = []
for row in sorted(all_global_raw, key=lambda x: x[1], reverse=True):
    if row[0] not in seen_g and row[1] >= 10:
        seen_g.add(row[0])
        deduped_global.append(row)

print(f"\n  {'Keyword':<60} {'Vol/mo':>8} {'Competition':>14} {'Low CPC':>10} {'High CPC':>10}")
print(f"  {'-'*108}")
for kw, vol, comp, low, high in deduped_global[:40]:
    print(f"  {kw:<60} {vol:>8,} {comp:>14} ${low:>8.2f} ${high:>8.2f}")
print(f"\n  Total unique Diaspora keywords (vol ≥ 10): {len(deduped_global)}")
