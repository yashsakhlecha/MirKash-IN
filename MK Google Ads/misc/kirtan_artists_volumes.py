from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

client = GoogleAdsClient.load_from_storage("google-ads.yaml")
customer_id = "6186258758"
kp_idea_service = client.get_service("KeywordPlanIdeaService")
geo_service = client.get_service("GeoTargetConstantService")

INDIA = "2356"
USA   = "2840"
UK    = "2826"

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

def print_table(results, label, sym="₹", min_vol=10, top=40):
    filtered = [r for r in results if r[1] >= min_vol]
    print(f"\n{'='*120}")
    print(f"  {label}  ({len(filtered)} keywords vol ≥ {min_vol})")
    print(f"{'='*120}")
    print(f"  {'Keyword':<60} {'Vol/mo':>8} {'Comp':>10} {'Low CPC':>10} {'High CPC':>10}")
    print(f"  {'-'*104}")
    for kw, vol, comp, low, high in filtered[:top]:
        cpc_str = f"{sym}{low:.2f}–{sym}{high:.2f}" if high else "—"
        print(f"  {kw:<60} {vol:>8,} {comp:>10}   {cpc_str}")
    if len(filtered) > top:
        print(f"  ... and {len(filtered)-top} more")
    print(f"\n  Total vol (shown): {sum(r[1] for r in filtered[:top]):,}/mo  |  Keywords found: {len(filtered)}")
    return filtered

# ─────────────────────────────────────────────────────────────────────────────
# ISKCON / WESTERN KIRTAN ARTISTS
# ─────────────────────────────────────────────────────────────────────────────
iskcon_western_seeds = [
    "radhika das",
    "krishna das kirtan",
    "jai uttal kirtan",
    "deva premal kirtan",
    "gaura vani kirtan",
    "dave stringer kirtan",
    "bada haridas kirtan",
    "mahadeva das kirtan",
    "aindra das kirtan",
    "lokanath swami kirtan",
    "indradyumna swami kirtan",
    "sivarama swami kirtan",
    "sacinandana swami kirtan",
    "niranjana swami kirtan",
    "bhakti charu swami kirtan",
]

print("\n" + "█"*120)
print("  ISKCON & WESTERN KIRTAN ARTISTS — INDIA")
print("█"*120)
r_iskcon_india = fetch_ideas(iskcon_western_seeds, INDIA)
a_iskcon_india = print_table(r_iskcon_india, "ISKCON / Western Kirtan Artists (India)", sym="₹")

print("\n" + "█"*120)
print("  ISKCON & WESTERN KIRTAN ARTISTS — USA")
print("█"*120)
r_iskcon_usa = fetch_ideas(iskcon_western_seeds, USA)
a_iskcon_usa = print_table(r_iskcon_usa, "ISKCON / Western Kirtan Artists (USA)", sym="$")

print("\n" + "█"*120)
print("  ISKCON & WESTERN KIRTAN ARTISTS — UK")
print("█"*120)
r_iskcon_uk = fetch_ideas(iskcon_western_seeds, UK)
a_iskcon_uk = print_table(r_iskcon_uk, "ISKCON / Western Kirtan Artists (UK)", sym="£")

# ─────────────────────────────────────────────────────────────────────────────
# SIKH / GURBANI KIRTAN ARTISTS
# ─────────────────────────────────────────────────────────────────────────────
sikh_artists_seeds = [
    "bhai harjinder singh srinagar wale",
    "bhai gurpreet singh shimla wale",
    "bhai nirmal singh khalsa",
    "bhai maninder singh srinagar wale",
    "bhai davinder singh sodhi",
    "bhai jaswant singh",
    "bhai satnam singh sethi",
    "bhai lakhwinder singh",
    "bhai sarabjit singh",
    "prof surinder singh ji",
    "bhai ravinder singh ji",
    "bhai paramjeet singh ji",
]

print("\n" + "█"*120)
print("  SIKH / GURBANI KIRTAN ARTISTS — INDIA")
print("█"*120)
r_sikh_india = fetch_ideas(sikh_artists_seeds, INDIA)
a_sikh_india = print_table(r_sikh_india, "Sikh / Gurbani Kirtan Artists (India)", sym="₹")

print("\n" + "█"*120)
print("  SIKH / GURBANI KIRTAN ARTISTS — USA")
print("█"*120)
r_sikh_usa = fetch_ideas(sikh_artists_seeds, USA)
a_sikh_usa = print_table(r_sikh_usa, "Sikh / Gurbani Kirtan Artists (USA)", sym="$")

# ─────────────────────────────────────────────────────────────────────────────
# HINDU BHAJAN / KIRTAN ARTISTS
# ─────────────────────────────────────────────────────────────────────────────
hindu_bhajan_seeds = [
    "lakhbir singh lakha",
    "narendra chanchal bhajan",
    "vinod agarwal mathura",
    "anup jalota bhajan",
    "anuradha paudwal bhajan",
    "suresh wadkar bhajan",
    "hariharan bhajan",
    "shankar mahadevan bhajan",
    "kumar vishwas",
    "morari bapu",
    "ramesh bhai ojha",
    "devki nandan thakur",
    "bageshwar dham sarkar",
    "devi chitralekha",
    "jaya kishori",
]

print("\n" + "█"*120)
print("  HINDU BHAJAN / KIRTAN ARTISTS — INDIA")
print("█"*120)
r_hindu_india = fetch_ideas(hindu_bhajan_seeds, INDIA)
a_hindu_india = print_table(r_hindu_india, "Hindu Bhajan / Kirtan Artists (India)", sym="₹")

# ─────────────────────────────────────────────────────────────────────────────
# HARE KRISHNA / VAISHNAV ARTISTS — INDIA SPECIFIC
# ─────────────────────────────────────────────────────────────────────────────
vaishnav_seeds = [
    "radhika das kirtan",
    "aindra das",
    "gour govinda swami kirtan",
    "bhaktivinoda thakur kirtan",
    "narottama das thakur kirtan",
    "mukunda goswami kirtan",
    "vrindavan das kirtan",
    "madhava das kirtan",
    "acyuta priya das kirtan",
    "prahlad nrsimha das",
    "vishoka das kirtan",
    "bhurijana das kirtan",
    "bhurijan das kirtan",
    "sri prahlad das kirtan",
    "gaura nitai das kirtan",
]

print("\n" + "█"*120)
print("  VAISHNAV / HARE KRISHNA ARTISTS — INDIA")
print("█"*120)
r_vaishnav_india = fetch_ideas(vaishnav_seeds, INDIA)
a_vaishnav_india = print_table(r_vaishnav_india, "Vaishnav / Hare Krishna Artists (India)", sym="₹")

print("\n" + "█"*120)
print("  VAISHNAV / HARE KRISHNA ARTISTS — USA")
print("█"*120)
r_vaishnav_usa = fetch_ideas(vaishnav_seeds, USA)
a_vaishnav_usa = print_table(r_vaishnav_usa, "Vaishnav / Hare Krishna Artists (USA)", sym="$")

# ─────────────────────────────────────────────────────────────────────────────
# YOGA / WELLNESS KIRTAN ARTISTS (Western market)
# ─────────────────────────────────────────────────────────────────────────────
yoga_kirtan_seeds = [
    "krishna das",
    "jai uttal",
    "deva premal",
    "miten kirtan",
    "wah kirtan",
    "ragani kirtan",
    "shyamdas kirtan",
    "bhagavan das kirtan",
    "giriraja swami kirtan",
    "ananda monet kirtan",
    "donna de lory kirtan",
    "stevan devouks kirtan",
    "c c white kirtan",
    "kirtan wallah",
]

print("\n" + "█"*120)
print("  YOGA / WELLNESS KIRTAN ARTISTS — USA")
print("█"*120)
r_yoga_usa = fetch_ideas(yoga_kirtan_seeds, USA)
a_yoga_usa = print_table(r_yoga_usa, "Yoga / Wellness Kirtan Artists (USA)", sym="$")

print("\n" + "█"*120)
print("  YOGA / WELLNESS KIRTAN ARTISTS — UK")
print("█"*120)
r_yoga_uk = fetch_ideas(yoga_kirtan_seeds, UK)
a_yoga_uk = print_table(r_yoga_uk, "Yoga / Wellness Kirtan Artists (UK)", sym="£")

# ─────────────────────────────────────────────────────────────────────────────
# MASTER CROSS-MARKET ARTIST VOLUME TABLE
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n\n{'#'*120}")
print("  MASTER ARTIST VOLUME TABLE — Top Artists by Total Search Volume")
print(f"{'#'*120}")

all_results = (
    a_iskcon_india + a_iskcon_usa + a_iskcon_uk +
    a_sikh_india + a_sikh_usa +
    a_hindu_india +
    a_vaishnav_india + a_vaishnav_usa +
    a_yoga_usa + a_yoga_uk
)

# Aggregate by keyword
from collections import defaultdict
kw_totals = defaultdict(int)
kw_data = {}
for kw, vol, comp, low, high in all_results:
    kw_totals[kw] += vol
    if kw not in kw_data or vol > kw_data[kw][0]:
        kw_data[kw] = (vol, comp, low, high)

sorted_totals = sorted(kw_totals.items(), key=lambda x: x[1], reverse=True)

print(f"\n  {'Keyword':<60} {'Total Vol':>10} {'Best Single Mkt Vol':>20}")
print(f"  {'-'*96}")
for kw, total_vol in sorted_totals[:60]:
    best_vol = kw_data[kw][0]
    print(f"  {kw:<60} {total_vol:>10,} {best_vol:>20,}")

print(f"\n  Total unique keywords found: {len(kw_totals)}")
print(f"  Combined cross-market volume (top 60): {sum(v for _,v in sorted_totals[:60]):,}/mo")
