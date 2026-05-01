from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

client = GoogleAdsClient.load_from_storage("google-ads.yaml")
customer_id = "6186258758"

kp_idea_service = client.get_service("KeywordPlanIdeaService")
geo_service = client.get_service("GeoTargetConstantService")

seed_keywords = [
    "vegan leather bag",
    "vegan leather handbag",
    "vegan leather bags india",
    "vegan handbag india",
    "apple leather bag",
    "cactus leather bag",
    "cruelty free handbag",
    "vegan leather crossbody bag",
    "vegan leather tote bag",
    "vegan leather shoulder bag",
    "vegan clutch bag",
    "vegan leather purse",
    "vegan leather mini bag",
    "plant based leather bag",
    "vegan leather bag women",
    "luxury vegan handbag",
]

def fetch_ideas(geo_id, geo_name, currency_symbol):
    request = client.get_type("GenerateKeywordIdeasRequest")
    request.customer_id = customer_id
    request.language = client.get_service("GoogleAdsService").language_constant_path("1000")
    request.geo_target_constants.append(geo_service.geo_target_constant_path(str(geo_id)))
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
        print(f"Error for {geo_name}: {ex}")

    results.sort(key=lambda x: x[1], reverse=True)
    return results

for geo_id, geo_name, sym in [(2356, "INDIA", "₹"), (2840, "UNITED STATES", "$"), (2826, "UNITED KINGDOM", "£")]:
    results = fetch_ideas(geo_id, geo_name, sym)
    # Filter: vol >= 10, exclude mens/backpack/wallet/luggage
    exclude = {"mens", "men's", "men", "backpack", "wallet", "luggage", "suitcase", "diaper", "briefcase", "rucksack"}
    filtered = [(kw, vol, comp, low, high) for kw, vol, comp, low, high in results
                if vol >= 10 and not any(e in kw.lower() for e in exclude)]

    print(f"\n{'='*100}")
    print(f"  {geo_name} — Top Keywords")
    print(f"{'='*100}")
    print(f"{'Keyword':<52} {'Vol/mo':>8} {'Competition':>12} {'Low CPC':>12} {'High CPC':>12}")
    print("-"*100)
    for kw, vol, comp, low, high in filtered[:40]:
        print(f"{kw:<52} {vol:>8,} {comp:>12} {sym}{low:>10.2f} {sym}{high:>10.2f}")
    print(f"\n  Total relevant keywords: {len(filtered)}")
