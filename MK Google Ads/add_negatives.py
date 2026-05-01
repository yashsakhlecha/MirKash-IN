#!/usr/bin/env python3
"""Add negative keywords from search term report findings."""

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

client = GoogleAdsClient.load_from_storage("google-ads.yaml")
customer_id = "6186258758"
ga_svc = client.get_service("GoogleAdsService")
criterion_svc = client.get_service("CampaignCriterionService")

# Competitor brands + irrelevant terms to block across all Search campaigns
NEW_NEGATIVES = [
    "charles and keith",
    "miraggio",
    "zouk",
    "myntra",
    "rijac",
    "amazon",
    "flipkart",
    "nykaa",
    "meesho",
    "ajio",
    "zara",
    "h&m",
    "forever 21",
    "lavie",
    "caprese",
    "baggit",
    "aldo",
    "hidesign",
    "fastrack",
]

# Fetch all MK Search campaign resource names
query = """
    SELECT campaign.name, campaign.resource_name, campaign.advertising_channel_type
    FROM campaign
    WHERE campaign.name LIKE 'MK |%'
      AND campaign.advertising_channel_type = 'SEARCH'
      AND campaign.status != 'REMOVED'
"""
rows = list(ga_svc.search(customer_id=customer_id, query=query))

print(f"\nAdding {len(NEW_NEGATIVES)} negative keywords to {len(rows)} Search campaigns...\n")

for row in rows:
    camp_name = row.campaign.name
    camp_rn = row.campaign.resource_name

    # Check which negatives already exist to avoid duplicates
    existing_query = f"""
        SELECT campaign_criterion.keyword.text
        FROM campaign_criterion
        WHERE campaign_criterion.campaign = '{camp_rn}'
          AND campaign_criterion.negative = TRUE
          AND campaign_criterion.type = 'KEYWORD'
    """
    existing = {r.campaign_criterion.keyword.text.lower()
                for r in ga_svc.search(customer_id=customer_id, query=existing_query)}

    ops = []
    skipped = []
    for word in NEW_NEGATIVES:
        if word.lower() in existing:
            skipped.append(word)
            continue
        op = client.get_type("CampaignCriterionOperation")
        c = op.create
        c.campaign = camp_rn
        c.negative = True
        c.keyword.text = word
        c.keyword.match_type = client.enums.KeywordMatchTypeEnum.BROAD
        ops.append(op)

    if ops:
        added_words = [op.create.keyword.text for op in ops]
        try:
            criterion_svc.mutate_campaign_criteria(customer_id=customer_id, operations=ops)
            print(f"  ✓ {camp_name}")
            print(f"    Added: {', '.join(added_words)}")
        except GoogleAdsException as ex:
            for error in ex.failure.errors:
                print(f"  ERROR on {camp_name}: {error.message}")
    else:
        print(f"  ✓ {camp_name} — all already present, nothing to add")

    if skipped:
        print(f"    Already existed: {', '.join(skipped)}")

print("\nDone.\n")
