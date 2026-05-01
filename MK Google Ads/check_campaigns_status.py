#!/usr/bin/env python3
"""Check all campaigns: status, final_url_suffix, and sample ad final URLs."""

from google.ads.googleads.client import GoogleAdsClient

client = GoogleAdsClient.load_from_storage("google-ads.yaml")
ga_service = client.get_service("GoogleAdsService")
CUSTOMER_ID = "6186258758"

# ── 1. Campaigns ──────────────────────────────────────────────────────────────
query = """
SELECT
  campaign.id,
  campaign.name,
  campaign.status,
  campaign.final_url_suffix,
  campaign.advertising_channel_type
FROM campaign
ORDER BY campaign.id
"""
print("=" * 70)
print("CAMPAIGNS")
print("=" * 70)
response = ga_service.search(customer_id=CUSTOMER_ID, query=query)
campaigns = []
for row in response:
    c = row.campaign
    status = c.status.name
    suffix = c.final_url_suffix or "(none)"
    ch = c.advertising_channel_type.name
    print(f"  [{c.id}] {c.name}")
    print(f"    Status: {status}  |  Type: {ch}")
    print(f"    UTM suffix: {suffix}")
    print()
    campaigns.append(c.id)

# ── 2. Sample ad final URLs ───────────────────────────────────────────────────
query2 = """
SELECT
  campaign.id,
  campaign.name,
  ad_group_ad.ad.id,
  ad_group_ad.ad.final_urls,
  ad_group_ad.status
FROM ad_group_ad
WHERE ad_group_ad.status != 'REMOVED'
LIMIT 30
"""
print("=" * 70)
print("AD FINAL URLs (sample)")
print("=" * 70)
response2 = ga_service.search(customer_id=CUSTOMER_ID, query=query2)
seen = set()
for row in response2:
    ad = row.ad_group_ad.ad
    cid = row.campaign.id
    if cid in seen:
        continue
    seen.add(cid)
    urls = list(ad.final_urls)
    print(f"  Campaign [{cid}]: {row.campaign.name}")
    print(f"    Ad status: {row.ad_group_ad.status.name}")
    for u in urls:
        print(f"    URL: {u}")
    print()
