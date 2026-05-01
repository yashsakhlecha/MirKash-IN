from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

client = GoogleAdsClient.load_from_storage("google-ads.yaml")
customer_id = "6186258758"
kp_idea_service = client.get_service("KeywordPlanIdeaService")
geo_service = client.get_service("GeoTargetConstantService")
INDIA = "2356"

def fetch_ideas(seed_keywords, label):
    request = client.get_type("GenerateKeywordIdeasRequest")
    request.customer_id = customer_id
    request.language = client.get_service("GoogleAdsService").language_constant_path("1000")
    request.geo_target_constants.append(geo_service.geo_target_constant_path(INDIA))
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
        print(f"Error: {ex}")
        return []

    results.sort(key=lambda x: x[1], reverse=True)
    return results

def print_table(results, label, sym="₹", min_vol=10, exclude_words=None):
    if exclude_words is None:
        exclude_words = []
    filtered = [r for r in results if r[1] >= min_vol and not any(e in r[0].lower() for e in exclude_words)]
    print(f"\n{'='*105}")
    print(f"  {label}  ({len(filtered)} keywords)")
    print(f"{'='*105}")
    print(f"  {'Keyword':<52} {'Vol/mo':>8} {'Competition':>12} {'Low CPC':>10} {'High CPC':>10}")
    print(f"  {'-'*98}")
    for kw, vol, comp, low, high in filtered[:35]:
        print(f"  {kw:<52} {vol:>8,} {comp:>12} {sym}{low:>8.2f} {sym}{high:>8.2f}")
    total_vol = sum(r[1] for r in filtered[:35])
    print(f"\n  Top-35 total monthly search volume: {total_vol:,}")

# --- GROUP 1: Work / Functional (Weaver Tote) ---
work_seeds = [
    "laptop bag for women india",
    "office bag for women india",
    "work bag women india",
    "macbook bag women",
    "13 inch laptop bag women",
    "laptop tote bag women",
    "work tote bag women",
    "professional bag women india",
    "laptop handbag women",
    "office handbag india",
]
work_results = fetch_ideas(work_seeds, "WORK / FUNCTIONAL — India")
print_table(work_results, "WORK / FUNCTIONAL — India (Weaver Tote)",
            exclude_words=["men", "boys", "school", "backpack", "trolley", "wheeled", "rolling"])

# --- GROUP 2: Gifting ---
gift_seeds = [
    "gift for wife india",
    "birthday gift for girlfriend india",
    "diwali gift for her",
    "anniversary gift for wife india",
    "luxury gift for women india",
    "gift for women india",
    "gift for her india",
    "valentines gift for girlfriend india",
    "raksha bandhan gift for sister india",
    "womens day gift india",
]
gift_results = fetch_ideas(gift_seeds, "GIFTING — India")
print_table(gift_results, "GIFTING — India",
            exclude_words=["men", "boys", "him", "husband", "brother", "boyfriend", "gadget", "phone", "watch", "earphone"])

# --- GROUP 3: Category / Shopping keywords ---
category_seeds = [
    "crossbody bag women india",
    "sling bag for women india",
    "shoulder bag for women india",
    "clutch for women india",
    "tote bag women india",
    "handbag for women india",
    "mini bag women india",
    "structured handbag india",
    "premium handbag india",
    "designer bag india women",
]
cat_results = fetch_ideas(category_seeds, "CATEGORY / SHOPPING — India")
print_table(cat_results, "CATEGORY / SHOPPING — India (for Shopping campaigns only)",
            exclude_words=["men", "boys", "school", "backpack", "trolley", "cheap", "under 500", "under 1000",
                           "wholesale", "manufacturer", "supplier", "wallets", "wallet"])
