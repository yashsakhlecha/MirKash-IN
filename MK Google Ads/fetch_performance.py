#!/usr/bin/env python3
"""Fetch campaign + ad group performance from Google Ads."""

from google.ads.googleads.client import GoogleAdsClient
from datetime import date, timedelta

client = GoogleAdsClient.load_from_storage("google-ads.yaml")
customer_id = "6186258758"
ga_svc = client.get_service("GoogleAdsService")

# Date range: last 30 days
today = date.today()
start = (today - timedelta(days=30)).strftime("%Y-%m-%d")
end = today.strftime("%Y-%m-%d")

print(f"\n{'='*70}")
print(f"  MIR KASH — Google Ads Performance  ({start} → {end})")
print(f"{'='*70}")

# ── 1. Campaign-level summary ─────────────────────────────────────────────────
campaign_query = f"""
    SELECT
        campaign.name,
        campaign.status,
        campaign.advertising_channel_type,
        metrics.impressions,
        metrics.clicks,
        metrics.cost_micros,
        metrics.ctr,
        metrics.average_cpc,
        metrics.conversions,
        metrics.conversions_value,
        metrics.all_conversions
    FROM campaign
    WHERE segments.date BETWEEN '{start}' AND '{end}'
      AND campaign.name LIKE 'MK |%'
    ORDER BY metrics.cost_micros DESC
"""

rows = list(ga_svc.search(customer_id=customer_id, query=campaign_query))

print(f"\n{'CAMPAIGN PERFORMANCE':^70}")
print(f"{'─'*70}")
if not rows:
    print("  No data yet (campaigns may be paused or too new).")
else:
    fmt = "{:<42} {:<8} {:>6} {:>6} {:>8} {:>6} {:>6}"
    print(fmt.format("Campaign", "Status", "Impr", "Clicks", "Spend(₹)", "CTR%", "Conv"))
    print("─" * 70)
    total_cost = total_clicks = total_impr = total_conv = 0
    for row in rows:
        c = row.campaign
        m = row.metrics
        cost_inr = m.cost_micros / 1_000_000
        ctr_pct = m.ctr * 100
        name = c.name[:41]
        status = c.status.name[:7]
        print(fmt.format(
            name, status,
            f"{m.impressions:,}", f"{m.clicks:,}",
            f"₹{cost_inr:,.0f}", f"{ctr_pct:.2f}", f"{m.conversions:.1f}"
        ))
        total_cost += cost_inr
        total_clicks += m.clicks
        total_impr += m.impressions
        total_conv += m.conversions
    print("─" * 70)
    overall_ctr = (total_clicks / total_impr * 100) if total_impr else 0
    print(fmt.format("TOTAL", "", f"{total_impr:,}", f"{total_clicks:,}",
                     f"₹{total_cost:,.0f}", f"{overall_ctr:.2f}", f"{total_conv:.1f}"))

# ── 2. Ad group breakdown ──────────────────────────────────────────────────────
ag_query = f"""
    SELECT
        campaign.name,
        ad_group.name,
        ad_group.status,
        metrics.impressions,
        metrics.clicks,
        metrics.cost_micros,
        metrics.ctr,
        metrics.average_cpc,
        metrics.conversions
    FROM ad_group
    WHERE segments.date BETWEEN '{start}' AND '{end}'
      AND campaign.name LIKE 'MK |%'
      AND metrics.impressions > 0
    ORDER BY campaign.name, metrics.clicks DESC
"""

ag_rows = list(ga_svc.search(customer_id=customer_id, query=ag_query))

print(f"\n\n{'AD GROUP BREAKDOWN (impressions > 0 only)':^70}")
print(f"{'─'*70}")
if not ag_rows:
    print("  No ad group data yet.")
else:
    fmt2 = "{:<25} {:<22} {:>6} {:>6} {:>8} {:>5}"
    print(fmt2.format("Campaign (short)", "Ad Group", "Impr", "Clicks", "Spend(₹)", "CTR%"))
    print("─" * 70)
    for row in ag_rows:
        camp_short = row.campaign.name.replace("MK | ", "").replace(" | Search | IN", "").replace(" | Shopping | IN", " Shop").replace(" | Shopping | US-UK", " Intl")[:24]
        ag_name = row.ad_group.name[:21]
        m = row.metrics
        cost_inr = m.cost_micros / 1_000_000
        ctr_pct = m.ctr * 100
        print(fmt2.format(camp_short, ag_name, f"{m.impressions:,}", f"{m.clicks:,}",
                          f"₹{cost_inr:,.0f}", f"{ctr_pct:.2f}"))

# ── 3. Top keywords by clicks ──────────────────────────────────────────────────
kw_query = f"""
    SELECT
        campaign.name,
        ad_group_criterion.keyword.text,
        ad_group_criterion.keyword.match_type,
        metrics.impressions,
        metrics.clicks,
        metrics.cost_micros,
        metrics.ctr,
        metrics.average_cpc,
        metrics.conversions
    FROM keyword_view
    WHERE segments.date BETWEEN '{start}' AND '{end}'
      AND campaign.name LIKE 'MK |%'
      AND metrics.impressions > 0
    ORDER BY metrics.clicks DESC
    LIMIT 20
"""

kw_rows = list(ga_svc.search(customer_id=customer_id, query=kw_query))

print(f"\n\n{'TOP KEYWORDS (by clicks)':^70}")
print(f"{'─'*70}")
if not kw_rows:
    print("  No keyword data yet.")
else:
    fmt3 = "{:<32} {:<8} {:>6} {:>6} {:>8} {:>6}"
    print(fmt3.format("Keyword", "Match", "Impr", "Clicks", "Spend(₹)", "CTR%"))
    print("─" * 70)
    for row in kw_rows:
        kw = row.ad_group_criterion.keyword
        m = row.metrics
        cost_inr = m.cost_micros / 1_000_000
        ctr_pct = m.ctr * 100
        match = kw.match_type.name[:6]
        print(fmt3.format(kw.text[:31], match, f"{m.impressions:,}", f"{m.clicks:,}",
                          f"₹{cost_inr:,.0f}", f"{ctr_pct:.2f}"))

# ── 4. Search terms report (what people actually searched) ────────────────────
st_query = f"""
    SELECT
        search_term_view.search_term,
        search_term_view.status,
        metrics.impressions,
        metrics.clicks,
        metrics.cost_micros,
        metrics.conversions
    FROM search_term_view
    WHERE segments.date BETWEEN '{start}' AND '{end}'
      AND campaign.name LIKE 'MK |%'
      AND metrics.impressions > 0
    ORDER BY metrics.clicks DESC
    LIMIT 25
"""

st_rows = list(ga_svc.search(customer_id=customer_id, query=st_query))

print(f"\n\n{'ACTUAL SEARCH TERMS (what people typed)':^70}")
print(f"{'─'*70}")
if not st_rows:
    print("  No search term data yet.")
else:
    fmt4 = "{:<42} {:>6} {:>6} {:>8}"
    print(fmt4.format("Search Term", "Impr", "Clicks", "Spend(₹)"))
    print("─" * 70)
    for row in st_rows:
        m = row.metrics
        cost_inr = m.cost_micros / 1_000_000
        status = "✓" if row.search_term_view.status.name == "ADDED" else " "
        print(fmt4.format(f"{status} {row.search_term_view.search_term[:40]}",
                          f"{m.impressions:,}", f"{m.clicks:,}", f"₹{cost_inr:,.0f}"))

# ── 5. Account-level conversion actions ───────────────────────────────────────
conv_query = """
    SELECT
        conversion_action.name,
        conversion_action.status,
        conversion_action.type,
        conversion_action.category
    FROM conversion_action
    WHERE conversion_action.status = 'ENABLED'
"""
conv_rows = list(ga_svc.search(customer_id=customer_id, query=conv_query))

print(f"\n\n{'CONVERSION ACTIONS (enabled)':^70}")
print(f"{'─'*70}")
if not conv_rows:
    print("  No conversion actions configured.")
else:
    for row in conv_rows:
        ca = row.conversion_action
        print(f"  • {ca.name}  [{ca.category.name}]")

print(f"\n{'='*70}\n")
