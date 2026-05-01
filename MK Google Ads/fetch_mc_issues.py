#!/usr/bin/env python3
"""Fetch product issues from Merchant Center via Merchant API (v1)."""

import yaml, requests, collections
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

with open("google-ads.yaml") as f:
    cfg = yaml.safe_load(f)

creds = Credentials(
    token=None,
    refresh_token=cfg["refresh_token"],
    client_id=cfg["client_id"],
    client_secret=cfg["client_secret"],
    token_uri="https://oauth2.googleapis.com/token",
    scopes=["https://www.googleapis.com/auth/content"],
)
creds.refresh(Request())

merchant_id = 5772927765
BASE = "https://merchantapi.googleapis.com"
headers = {"Authorization": f"Bearer {creds.token}"}

# ── 1. List all products ──────────────────────────────────────────────────────
print(f"\nFetching products from MC {merchant_id}...\n")
products = []
url = f"{BASE}/products/v1/accounts/{merchant_id}/products?pageSize=250"
while url:
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    data = r.json()
    products.extend(data.get("products", []))
    token = data.get("nextPageToken")
    url = f"{BASE}/products/v1/accounts/{merchant_id}/products?pageSize=250&pageToken={token}" if token else None

print(f"Total products found: {len(products)}")

# ── 2. Fetch product statuses (issues) via Reports API ───────────────────────
print("Fetching product issues via Reports API...\n")

query = """
SELECT
  product_view.id,
  product_view.title,
  product_view.offer_id,
  product_view.item_issues
FROM ProductView
"""

issues_by_product = {}
page_token = None
while True:
    payload = {"query": query, "pageSize": 1000}
    if page_token:
        payload["pageToken"] = page_token
    r = requests.post(
        f"{BASE}/reports/v1/accounts/{merchant_id}:search",
        headers=headers,
        json=payload,
    )
    if not r.ok:
        print(f"Reports API error: {r.status_code} {r.text[:500]}")
        break
    data = r.json()
    for row in data.get("results", []):
        pv = row.get("productView", {})
        issues = pv.get("itemIssues", [])
        if issues:
            issues_by_product[pv.get("offerId", pv.get("id", "?"))] = {
                "title": pv.get("title", "?"),
                "issues": issues,
            }
    page_token = data.get("nextPageToken")
    if not page_token:
        break

# ── 3. Summarise ──────────────────────────────────────────────────────────────
issue_counter = collections.Counter()
for offer_id, info in issues_by_product.items():
    for issue in info["issues"]:
        resolution = issue.get("resolution", "?")
        desc = issue.get("issueMessage", issue.get("code", "unknown"))
        issue_counter[f"{resolution} | {desc}"] += 1

print(f"Products with issues: {len(issues_by_product)}/{len(products)}\n")
print("── Issue Summary ─────────────────────────────────────────────────────")
for issue, count in issue_counter.most_common():
    print(f"  {count:>3}x  {issue}")

print("\n── Sample products with issues ───────────────────────────────────────")
for offer_id, info in list(issues_by_product.items())[:10]:
    print(f"\n  [{offer_id}] {info['title'][:60]}")
    for issue in info["issues"]:
        resolution = issue.get("resolution", "?")
        desc = issue.get("issueMessage", "?")
        attrs = ", ".join(issue.get("applicableCountries", []))
        print(f"    [{resolution}] {desc}" + (f"  ({attrs})" if attrs else ""))
