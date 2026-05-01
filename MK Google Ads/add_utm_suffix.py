#!/usr/bin/env python3
"""Add final_url_suffix with UTM params to all MK campaigns."""

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

client = GoogleAdsClient.load_from_storage("google-ads.yaml")
customer_id = "6186258758"
ga_svc = client.get_service("GoogleAdsService")
campaign_svc = client.get_service("CampaignService")

# ValueTrack params — auto-filled by Google on each click
UTM_SUFFIX = (
    "utm_source=google"
    "&utm_medium={ifsearch:cpc}{ifcontent:display}{ifshopping:shopping}"
    "&utm_campaign={campaign}"
    "&utm_content={adgroupid}"
    "&utm_term={keyword}"
)

# Fetch all MK campaign resource names
query = """
    SELECT campaign.name, campaign.resource_name, campaign.status
    FROM campaign
    WHERE campaign.name LIKE 'MK |%'
      AND campaign.status != 'REMOVED'
"""
rows = list(ga_svc.search(customer_id=customer_id, query=query))
print(f"\nSetting final_url_suffix on {len(rows)} campaigns...\n")

ops = []
for row in rows:
    op = client.get_type("CampaignOperation")
    op.update.resource_name = row.campaign.resource_name
    op.update.final_url_suffix = UTM_SUFFIX
    op.update_mask.paths.append("final_url_suffix")
    ops.append((row.campaign.name, op))

for name, op in ops:
    try:
        campaign_svc.mutate_campaigns(customer_id=customer_id, operations=[op])
        print(f"  ✓ {name}")
    except GoogleAdsException as ex:
        for error in ex.failure.errors:
            print(f"  ✗ {name}: {error.message}")

print(f"\nSuffix applied:\n  {UTM_SUFFIX}\n")
