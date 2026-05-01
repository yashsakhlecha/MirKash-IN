#!/usr/bin/env python3
"""
Mir Kash — Google Ads Campaign Setup
Creates all 5 campaigns in PAUSED state for review before enabling.

Budget summary (monthly → daily):
  1. Vegan Believers    Search  IN       ₹30,000 → ₹985/day
  2. Work / Weaver Tote Search  IN       ₹22,500 → ₹740/day
  3. Gifting            Search  IN       ₹ 7,500 → ₹246/day
  4. Category Discovery Shopping IN     ₹12,500 → ₹411/day
  5. International      Shopping US+UK  ₹27,500 → ₹904/day (~$11)
"""

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

client = GoogleAdsClient.load_from_storage("google-ads.yaml")
customer_id = "6186258758"

# ── Services ──────────────────────────────────────────────────────────────────
budget_svc   = client.get_service("CampaignBudgetService")
campaign_svc = client.get_service("CampaignService")
criterion_svc = client.get_service("CampaignCriterionService")
ag_svc       = client.get_service("AdGroupService")
ad_svc       = client.get_service("AdGroupAdService")
kw_svc       = client.get_service("AdGroupCriterionService")

GEO_IN  = "geoTargetConstants/2356"
GEO_US  = "geoTargetConstants/2840"
GEO_UK  = "geoTargetConstants/2826"
LANG_EN = "languageConstants/1000"

def to_micros(inr):
    return int(inr * 1_000_000)

# ── Merchant Center IDs (fill in from merchants.google.com → Settings → Account info)
# Leave as None to skip Shopping campaigns.
MC_IN  = 5768082829  # Merchant Center for mirkash.in  (INR feed)
MC_COM = None        # Merchant Center for mirkash.com (USD feed) — pending .com store connection

# ── Helper: budget ────────────────────────────────────────────────────────────
def make_budget(name, daily_inr):
    op = client.get_type("CampaignBudgetOperation")
    b = op.create
    b.name = name
    b.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
    b.amount_micros = to_micros(daily_inr)
    b.explicitly_shared = False
    r = budget_svc.mutate_campaign_budgets(customer_id=customer_id, operations=[op])
    return r.results[0].resource_name

# ── Helper: Search campaign ───────────────────────────────────────────────────
def make_search_campaign(name, budget_rn, geos):
    op = client.get_type("CampaignOperation")
    c = op.create
    c.name = name
    c.status = client.enums.CampaignStatusEnum.PAUSED
    c.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.SEARCH
    c.campaign_budget = budget_rn
    c.network_settings.target_google_search = True
    c.network_settings.target_search_network = False
    c.network_settings.target_content_network = False
    c.target_spend.target_spend_micros = 0  # Maximize Clicks, uncapped
    c.contains_eu_political_advertising = client.enums.EuPoliticalAdvertisingStatusEnum.DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING
    r = campaign_svc.mutate_campaigns(customer_id=customer_id, operations=[op])
    rn = r.results[0].resource_name
    _add_geo_lang(rn, geos)
    print(f"  ✓ {name}")
    return rn

# ── Helper: Shopping campaign ─────────────────────────────────────────────────
def make_shopping_campaign(name, budget_rn, geos, merchant_id):
    op = client.get_type("CampaignOperation")
    c = op.create
    c.name = name
    c.status = client.enums.CampaignStatusEnum.PAUSED
    c.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.SHOPPING
    c.campaign_budget = budget_rn
    c.shopping_setting.merchant_id = merchant_id
    c.shopping_setting.campaign_priority = 1  # MEDIUM; 0=LOW is proto3 default and gets dropped
    c.shopping_setting.enable_local = False
    c.target_spend.target_spend_micros = 0
    c.contains_eu_political_advertising = client.enums.EuPoliticalAdvertisingStatusEnum.DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING
    r = campaign_svc.mutate_campaigns(customer_id=customer_id, operations=[op])
    rn = r.results[0].resource_name
    _add_geo_lang(rn, geos, campaign_type="SHOPPING")
    print(f"  ✓ {name}")
    return rn

# ── Helper: geo + language criteria ──────────────────────────────────────────
def _add_geo_lang(campaign_rn, geos, campaign_type="SEARCH"):
    ops = []
    for geo in geos:
        op = client.get_type("CampaignCriterionOperation")
        c = op.create
        c.campaign = campaign_rn
        c.location.geo_target_constant = geo
        ops.append(op)
    # Language targeting only for Search — Shopping uses feed language automatically
    if campaign_type == "SEARCH":
        op = client.get_type("CampaignCriterionOperation")
        c = op.create
        c.campaign = campaign_rn
        c.language.language_constant = LANG_EN
        ops.append(op)
    criterion_svc.mutate_campaign_criteria(customer_id=customer_id, operations=ops)

# ── Helper: campaign-level negative keywords ──────────────────────────────────
def add_negatives(campaign_rn, words):
    ops = []
    for w in words:
        op = client.get_type("CampaignCriterionOperation")
        c = op.create
        c.campaign = campaign_rn
        c.negative = True
        c.keyword.text = w
        c.keyword.match_type = client.enums.KeywordMatchTypeEnum.BROAD
        ops.append(op)
    criterion_svc.mutate_campaign_criteria(customer_id=customer_id, operations=ops)

# ── Helper: ad group ──────────────────────────────────────────────────────────
def make_ad_group(name, campaign_rn, ag_type="SEARCH_STANDARD"):
    op = client.get_type("AdGroupOperation")
    ag = op.create
    ag.name = name
    ag.campaign = campaign_rn
    ag.status = client.enums.AdGroupStatusEnum.ENABLED
    ag.type_ = getattr(client.enums.AdGroupTypeEnum, ag_type)
    r = ag_svc.mutate_ad_groups(customer_id=customer_id, operations=[op])
    return r.results[0].resource_name

# ── Helper: keywords ──────────────────────────────────────────────────────────
def add_keywords(ag_rn, kws):
    ops = []
    for text, match in kws:
        op = client.get_type("AdGroupCriterionOperation")
        c = op.create
        c.ad_group = ag_rn
        c.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
        c.keyword.text = text
        c.keyword.match_type = getattr(client.enums.KeywordMatchTypeEnum, match)
        ops.append(op)
    kw_svc.mutate_ad_group_criteria(customer_id=customer_id, operations=ops)

# ── Helper: all-products listing group (Shopping) ────────────────────────────
def add_all_products_listing_group(ag_rn):
    op = client.get_type("AdGroupCriterionOperation")
    c = op.create
    c.ad_group = ag_rn
    c.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
    c.listing_group.type_ = client.enums.ListingGroupTypeEnum.UNIT
    c.cpc_bid_micros = 30_000_000  # ₹30 nominal; Maximize Clicks overrides at campaign level
    kw_svc.mutate_ad_group_criteria(customer_id=customer_id, operations=[op])

# ── Helper: RSA ───────────────────────────────────────────────────────────────
def make_rsa(ag_rn, url, headlines, descs):
    op = client.get_type("AdGroupAdOperation")
    aga = op.create
    aga.status = client.enums.AdGroupAdStatusEnum.ENABLED
    aga.ad_group = ag_rn
    ad = aga.ad
    ad.final_urls.append(url)
    rsa = ad.responsive_search_ad
    for h in headlines:
        a = client.get_type("AdTextAsset")
        a.text = h
        rsa.headlines.append(a)
    for d in descs:
        a = client.get_type("AdTextAsset")
        a.text = d
        rsa.descriptions.append(a)
    ad_svc.mutate_ad_group_ads(customer_id=customer_id, operations=[op])


# ══════════════════════════════════════════════════════════════════════════════
# 1. VEGAN BELIEVERS — Search, India, ₹30K/mo
# ══════════════════════════════════════════════════════════════════════════════
print("\n[1/5] Vegan Believers...")
b1 = make_budget("MK Vegan Believers Budget", 985)
c1 = make_search_campaign("MK | Vegan Believers | Search | IN", b1, [GEO_IN])
add_negatives(c1, [
    "men", "man", "boys", "male", "backpack", "wallet", "wallets",
    "luggage", "wholesale", "manufacturer", "cheap", "free",
])

# Ad Group A: Core vegan leather terms
ag1a = make_ad_group("Vegan Leather Bags", c1)
add_keywords(ag1a, [
    ("vegan leather bag", "EXACT"),
    ("vegan leather handbag", "EXACT"),
    ("vegan leather bags india", "EXACT"),
    ("vegan leather crossbody bag", "EXACT"),
    ("vegan leather tote bag", "EXACT"),
    ("vegan leather shoulder bag", "PHRASE"),
    ("vegan leather purse", "PHRASE"),
    ("vegan handbag india", "PHRASE"),
    ("luxury vegan handbag", "PHRASE"),
    ("vegan leather bag women", "PHRASE"),
])
make_rsa(ag1a, "https://mirkash.in/collections/all", headlines=[
    "Luxury Vegan Leather Bags",
    "Cruelty-Free Luxury Bags",
    "Plant-Based Premium Bags",
    "Mir Kash Vegan Luxury",
    "Shop Vegan Leather Bags",
    "Free Shipping Across India",
    "No Animal. All Luxury.",
    "Vegan Leather Handbags",
    "Braidey and Weaver Tote",
    "India's Vegan Luxury Brand",
    "Structured Vegan Bags",
    "From ₹8,000. Ships Free.",
    "Explore Our Collection",
    "Designed to Last a Lifetime",
    "The Bag Worth Believing In",
], descs=[
    "Handcrafted vegan leather bags made to last. Free shipping across India.",
    "Premium bags from apple leather & plant-based materials. Shop now.",
    "Luxury without compromise. Mir Kash vegan bags for women who know better.",
    "Structured, carry-all vegan leather bags. From boardrooms to brunches.",
])

# Ad Group B: Alternative material terms (apple/cactus leather)
ag1b = make_ad_group("Alternative Materials", c1)
add_keywords(ag1b, [
    ("apple leather bag", "EXACT"),
    ("cactus leather bag", "EXACT"),
    ("plant based leather bag", "PHRASE"),
    ("cruelty free handbag", "PHRASE"),
    ("cruelty free bag india", "PHRASE"),
    ("vegan leather mini bag", "PHRASE"),
])
make_rsa(ag1b, "https://mirkash.in/collections/all", headlines=[
    "Apple Leather Bags India",
    "Cactus Leather Luxury Bags",
    "Cruelty-Free Luxury Bags",
    "Plant-Based Premium Bags",
    "Mir Kash Vegan Luxury",
    "Shop Cruelty-Free Handbags",
    "Free Shipping Across India",
    "No Animal. All Luxury.",
    "India's Vegan Luxury Brand",
    "From ₹8,000. Ships Free.",
    "Explore Our Collection",
    "Designed to Last a Lifetime",
    "Zero Compromise. Full Luxury.",
    "The Bag Worth Believing In",
    "Braidey and Weaver Tote",
], descs=[
    "Bags crafted from apple leather, cactus leather & plant-based materials. Ships free.",
    "Premium cruelty-free handbags for the conscious luxury buyer. Free shipping India.",
    "Luxury without compromise. Mir Kash — for women who know the difference.",
    "Structured, carry-all vegan leather bags. From boardrooms to brunches.",
])
print("  ✓ Ad groups, keywords & RSAs added")


# ══════════════════════════════════════════════════════════════════════════════
# 2. WORK / WEAVER TOTE — Search, India, ₹22.5K/mo
# ══════════════════════════════════════════════════════════════════════════════
print("\n[2/5] Work / Weaver Tote...")
b2 = make_budget("MK Work Weaver Tote Budget", 740)
c2 = make_search_campaign("MK | Work Weaver Tote | Search | IN", b2, [GEO_IN])
add_negatives(c2, [
    "men", "man", "boys", "male", "school", "college", "kids",
    "backpack", "trolley", "wheeled", "rolling", "wholesale",
    "cheap", "under 500", "under 1000",
])

# Ad Group A: Laptop bag terms
ag2a = make_ad_group("Laptop Bags Women", c2)
add_keywords(ag2a, [
    ("laptop bag for women", "PHRASE"),
    ("laptop bag for women india", "EXACT"),
    ("ladies laptop bag", "PHRASE"),
    ("13 inch laptop bag women", "PHRASE"),
    ("macbook bag women", "PHRASE"),
    ("laptop tote bag women", "EXACT"),
    ("laptop handbag women", "PHRASE"),
    ("laptop bags for ladies", "PHRASE"),
    ("women laptop bag india", "PHRASE"),
])
make_rsa(ag2a, "https://mirkash.in/products/weaver-tote", headlines=[
    "Laptop Bags for Women India",
    "The Perfect Work Bag",
    "Carry Your Laptop in Style",
    "Laptop Tote for Women",
    "Premium Work Bags From ₹8,000",
    "Free Shipping. Easy Returns.",
    "Vegan Leather Work Bags",
    "Professional Bags for Women",
    "The Weaver Tote. Work Ready.",
    "Bags That Mean Business",
    "Shop Laptop Totes Women",
    "Spacious. Structured. Stylish.",
    "Mir Kash Work-Ready Luxury",
    "Fits 13in Laptop. Ships Free.",
    "From Desk to Dinner. One Bag.",
], descs=[
    "The Weaver Tote fits a 13in laptop and everything else. Vegan leather. Ships free.",
    "Structured work bags for women who mean business. Crafted from luxury vegan leather.",
    "Office bags that go from desk to dinner. Vegan leather. Free shipping across India.",
    "Premium laptop totes for women. Ships in 2 days, free shipping across India.",
])

# Ad Group B: Office bag terms
ag2b = make_ad_group("Office Bags Women", c2)
add_keywords(ag2b, [
    ("office bag for women", "PHRASE"),
    ("office bag for women india", "EXACT"),
    ("work bag women india", "EXACT"),
    ("professional bag women india", "EXACT"),
    ("work tote bag women", "EXACT"),
    ("office handbag india", "PHRASE"),
    ("office tote bag women", "PHRASE"),
    ("office bags for ladies", "PHRASE"),
])
make_rsa(ag2b, "https://mirkash.in/products/weaver-tote", headlines=[
    "Office Bags for Women India",
    "The Perfect Work Bag",
    "Work Bags That Mean Business",
    "Premium Office Bags ₹8,000+",
    "Free Shipping. Easy Returns.",
    "Vegan Leather Office Bags",
    "Professional Bags for Women",
    "The Weaver Tote. Work Ready.",
    "Bags That Mean Business",
    "Shop Work Totes for Women",
    "Spacious. Structured. Stylish.",
    "Mir Kash Work-Ready Luxury",
    "Carry Your Laptop in Style",
    "Office to Dinner. One Bag.",
    "Best Office Bag for Her India",
], descs=[
    "Structured office bags for women who mean business. Crafted from luxury vegan leather.",
    "The Weaver Tote fits a 13in laptop and everything you need. Ships free across India.",
    "Office bags that go from desk to dinner. Vegan leather. Free shipping across India.",
    "Premium work totes for women. Ships in 2 days, free shipping across India.",
])
print("  ✓ Ad groups, keywords & RSAs added")


# ══════════════════════════════════════════════════════════════════════════════
# 3. GIFTING — Search, India, ₹7.5K/mo
# ══════════════════════════════════════════════════════════════════════════════
print("\n[3/5] Gifting...")
b3 = make_budget("MK Gifting Budget", 246)
c3 = make_search_campaign("MK | Gifting | Search | IN", b3, [GEO_IN])
add_negatives(c3, [
    "men", "man", "boys", "male", "him", "husband", "brother",
    "boyfriend", "gadget", "phone", "watch", "earphone", "earbuds",
    "perfume", "chocolate", "jewelry", "jewellery", "cheap",
])

# Ad Group A: Year-round gifting
ag3a = make_ad_group("Gifting Occasions", c3)
add_keywords(ag3a, [
    ("gift for wife india", "PHRASE"),
    ("birthday gift for girlfriend india", "PHRASE"),
    ("anniversary gift for wife india", "PHRASE"),
    ("gift for girlfriend india", "PHRASE"),
    ("gift for women india", "PHRASE"),
    ("gift for her india", "PHRASE"),
    ("luxury gift for women india", "PHRASE"),
    ("valentines gift for girlfriend india", "PHRASE"),
    ("womens day gift india", "PHRASE"),
    ("handbag gift for her", "PHRASE"),
])
make_rsa(ag3a, "https://mirkash.in/collections/all", headlines=[
    "The Perfect Gift for Her",
    "Luxury Bag. Unforgettable Gift.",
    "Gift a Mir Kash Handbag",
    "Birthday Gift for Girlfriend",
    "Anniversary Gift for Wife",
    "Luxury Gifts for Women India",
    "Free Gift Wrapping Available",
    "Ships 2 Days. Gift Ready.",
    "The Gift She Will Love",
    "Vegan Leather Gift Bags",
    "From ₹8,000. Free Shipping.",
    "Gift Her Luxury. Mir Kash.",
    "Gift-Ready. Ships in 2 Days.",
    "Beautifully Packaged. Luxe.",
    "Premium Handbags. Gift-Worthy.",
], descs=[
    "Give luxury she'll love. Mir Kash bags arrive gift-ready. Free shipping across India.",
    "Premium handbags for birthdays & anniversaries. Ships in 2 days, beautifully packaged.",
    "Surprise her with a Mir Kash. The luxury vegan leather bag she's been wanting.",
    "Beautifully packaged, ships fast. The gift for the woman who has everything.",
])

# Ad Group B: Festive / seasonal gifting
ag3b = make_ad_group("Festive Gifting", c3)
add_keywords(ag3b, [
    ("diwali gift for her", "PHRASE"),
    ("diwali gift for wife", "PHRASE"),
    ("diwali gift for girlfriend", "PHRASE"),
    ("diwali gift for ladies", "PHRASE"),
    ("raksha bandhan gift for sister india", "PHRASE"),
    ("diwali gifts for women india", "PHRASE"),
    ("festive gift for her india", "PHRASE"),
])
make_rsa(ag3b, "https://mirkash.in/collections/all", headlines=[
    "Diwali Gifts for Her India",
    "The Perfect Diwali Gift",
    "Gift a Mir Kash This Diwali",
    "Luxury Bag. Unforgettable Gift.",
    "Raksha Bandhan Gift for Sister",
    "Luxury Gifts for Women India",
    "Free Gift Wrapping Available",
    "Ships 2 Days. Gift Ready.",
    "The Gift She Will Love",
    "From ₹8,000. Free Shipping.",
    "Gift Her Luxury This Diwali",
    "Gift-Ready. Ships in 2 Days.",
    "Festive Gifts for Her India",
    "Perfect Gift This Season",
    "Vegan Leather Gift Bags",
], descs=[
    "Give luxury she'll love this Diwali. Mir Kash bags arrive gift-ready. Free shipping.",
    "Premium vegan leather handbags. The perfect Diwali gift. Ships in 2 days, gift-ready.",
    "Surprise her this festive season with Mir Kash. The luxury bag she's been wanting.",
    "Gift-ready vegan leather handbags for Diwali & Raksha Bandhan. Free shipping India.",
])
print("  ✓ Ad groups, keywords & RSAs added")


# ══════════════════════════════════════════════════════════════════════════════
# 4. CATEGORY DISCOVERY — Standard Shopping, India, ₹12.5K/mo
# ══════════════════════════════════════════════════════════════════════════════
print("\n[4/5] Category Discovery Shopping (India)...")
if MC_IN:
    b4 = make_budget("MK Category Shopping IN Budget", 411)
    c4 = make_shopping_campaign(
        "MK | Category Discovery | Shopping | IN",
        b4, [GEO_IN], MC_IN,
    )
    ag4 = make_ad_group("All Products IN", c4, "SHOPPING_PRODUCT_ADS")
    add_all_products_listing_group(ag4)
    print("  ✓ Shopping campaign ready")
else:
    print("  ⚠️  Skipped — link Merchant Center first")


# ══════════════════════════════════════════════════════════════════════════════
# 5. INTERNATIONAL — Standard Shopping, US + UK, ₹27.5K/mo (~$11/day)
# ══════════════════════════════════════════════════════════════════════════════
print("\n[5/5] International Shopping (US + UK)...")
if MC_COM:
    b5 = make_budget("MK International Shopping Budget", 904)
    c5 = make_shopping_campaign(
        "MK | International | Shopping | US-UK",
        b5, [GEO_US, GEO_UK], MC_COM,
    )
    ag5 = make_ad_group("All Products International", c5, "SHOPPING_PRODUCT_ADS")
    add_all_products_listing_group(ag5)
    print("  ✓ Shopping campaign ready")
else:
    print("  ⚠️  Skipped — link Merchant Center first")


print("\n" + "=" * 60)
print("  All campaigns created in PAUSED state.")
print("  Review in Google Ads UI before enabling.")
print("=" * 60)
