from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from collections import defaultdict
import time

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
    time.sleep(6)  # stay within API quota
    return results

def print_table(results, label, sym="₹", min_vol=10, top=40):
    filtered = [r for r in results if r[1] >= min_vol]
    print(f"\n{'='*130}")
    print(f"  {label}  ({len(filtered)} keywords vol ≥ {min_vol})")
    print(f"{'='*130}")
    print(f"  {'Keyword':<65} {'Vol/mo':>8} {'Comp':>10} {'Low CPC':>12} {'High CPC':>12}")
    print(f"  {'-'*113}")
    for kw, vol, comp, low, high in filtered[:top]:
        cpc = f"{sym}{low:.2f}–{sym}{high:.2f}" if high else "—"
        print(f"  {kw:<65} {vol:>8,} {comp:>10}   {cpc}")
    if len(filtered) > top:
        print(f"  ... and {len(filtered)-top} more")
    print(f"\n  Total vol shown: {sum(r[1] for r in filtered[:top]):,}/mo | Keywords: {len(filtered)}")
    return filtered

# ── Master collector ──────────────────────────────────────────────────────────
all_india   = []
all_global  = []   # USA + UK combined

# ═════════════════════════════════════════════════════════════════════════════
# SECTION A: KIRTAN STYLES
# ═════════════════════════════════════════════════════════════════════════════

# ── A1. Shabad Kirtan (Sikh) ──────────────────────────────────────────────────
shabad_seeds = [
    "shabad kirtan", "shabad keertan", "gurbani kirtan", "gurbani shabad",
    "sikh kirtan", "shabad kirtan for wedding", "anand karaj kirtan",
    "shabad kirtan jatha", "kirtan jatha", "ragis for wedding",
    "shabad kirtan at home", "gurbani kirtan booking", "sikh kirtan group",
    "shabad kirtan for antim ardas", "gurmat sangeet", "shabad gurbani",
]
r = fetch_ideas(shabad_seeds, INDIA)
a = print_table(r, "A1 — SHABAD KIRTAN / GURBANI (India)", sym="₹")
all_india.extend([(kw, vol, comp, low, high, "Shabad Kirtan") for kw,vol,comp,low,high in a])

r_us = fetch_ideas(shabad_seeds, USA)
a_us = print_table(r_us, "A1 — SHABAD KIRTAN / GURBANI (USA)", sym="$")
all_global.extend([(kw, vol, comp, low, high, "Shabad Kirtan") for kw,vol,comp,low,high in a_us])

# ── A2. ISKCON / Hare Krishna Kirtan ─────────────────────────────────────────
iskcon_seeds = [
    "hare krishna kirtan", "iskcon kirtan", "harinam sankirtan",
    "maha mantra kirtan", "hare krishna chanting", "hare ram hare krishna kirtan",
    "hare krishna kirtan at home", "iskcon kirtan group booking",
    "harinam kirtan booking", "kirtan for janmashtami", "hare krishna bhajan",
    "iskcon bhajan", "vaishnav kirtan", "kirtan for ekadashi",
    "hare krishna mantra chanting", "sankirtan booking",
]
r = fetch_ideas(iskcon_seeds, INDIA)
a = print_table(r, "A2 — ISKCON / HARE KRISHNA KIRTAN (India)", sym="₹")
all_india.extend([(kw, vol, comp, low, high, "ISKCON Kirtan") for kw,vol,comp,low,high in a])

r_us = fetch_ideas(iskcon_seeds, USA)
a_us = print_table(r_us, "A2 — ISKCON / HARE KRISHNA KIRTAN (USA)", sym="$")
all_global.extend([(kw, vol, comp, low, high, "ISKCON Kirtan") for kw,vol,comp,low,high in a_us])

# ── A3. Bhajan Sandhya (Generic Hindu) ───────────────────────────────────────
bhajan_seeds = [
    "bhajan sandhya", "bhajan program", "bhajan singer for event",
    "bhajan group for home", "bhajan mandali booking", "bhajan party booking",
    "devotional music booking", "bhajan singer near me", "hire bhajan singer",
    "book bhajan singer", "bhajan for griha pravesh", "bhajan for wedding",
    "bhajan sandhya booking", "spiritual music event", "bhajan keertan",
    "religious singer for event", "bhajan for birthday party",
]
r = fetch_ideas(bhajan_seeds, INDIA)
a = print_table(r, "A3 — BHAJAN SANDHYA / GENERIC BHAJAN (India)", sym="₹")
all_india.extend([(kw, vol, comp, low, high, "Bhajan Sandhya") for kw,vol,comp,low,high in a])

# ── A4. Mata Ki Bhente / Devi Kirtan ─────────────────────────────────────────
mata_bhente_seeds = [
    "mata ki bhente", "mata ke bhajan", "devi bhajan", "durga bhajan",
    "mata rani ke bhajan", "sherawali mata bhajan", "vaishno devi bhajan",
    "mata bhajan singer", "mata bhajan sandhya", "jagran bhajan",
    "mata ki chowki singer", "jagran party booking", "devi kirtan",
    "navratri bhajan", "mata ki aarti", "jai mata di bhajan",
]
r = fetch_ideas(mata_bhente_seeds, INDIA)
a = print_table(r, "A4 — MATA KI BHENTE / DEVI KIRTAN (India)", sym="₹")
all_india.extend([(kw, vol, comp, low, high, "Mata Ki Bhente") for kw,vol,comp,low,high in a])

# ── A5. Ram Dhun & Ram Bhajans ────────────────────────────────────────────────
ram_seeds = [
    "ram bhajan", "ram dhun", "shri ram bhajan", "ram naam sankirtan",
    "ramayan bhajan", "jai shri ram bhajan", "ram katha bhajan",
    "ram bhajan sandhya", "ram bhajan singer", "ram bhajan for event",
    "ram bhajan group", "hanuman bhajan", "bajrangbali bhajan",
    "ram dhun for satsang", "ram naam kirtan", "sita ram bhajan",
]
r = fetch_ideas(ram_seeds, INDIA)
a = print_table(r, "A5 — RAM DHUN & RAM BHAJANS (India)", sym="₹")
all_india.extend([(kw, vol, comp, low, high, "Ram Bhajan") for kw,vol,comp,low,high in a])

# ── A6. Krishna Bhajan / Krishna Kirtan ──────────────────────────────────────
krishna_seeds = [
    "krishna bhajan", "krishna kirtan", "radha krishna bhajan",
    "govinda bhajan", "gopal bhajan", "radhe shyam bhajan",
    "krishna bhajan sandhya", "janmashtami bhajan", "krishna bhajan singer",
    "krishna bhajan for wedding", "nandlal bhajan", "radhe govinda bhajan",
    "vrindavan bhajan", "krishna katha bhajan", "gopala bhajan",
]
r = fetch_ideas(krishna_seeds, INDIA)
a = print_table(r, "A6 — KRISHNA BHAJAN / KRISHNA KIRTAN (India)", sym="₹")
all_india.extend([(kw, vol, comp, low, high, "Krishna Bhajan") for kw,vol,comp,low,high in a])

# ── A7. Balaji / Hanuman Kirtan ───────────────────────────────────────────────
balaji_seeds = [
    "balaji kirtan", "balaji bhajan", "hanuman kirtan", "hanuman bhajan sandhya",
    "bajrangbali bhajan", "hanuman chalisa kirtan", "mehandipur balaji bhajan",
    "salasar balaji bhajan", "balaji jagran", "hanuman bhajan mandali",
    "bajrang dal bhajan", "hanuman aarti", "hanuman bhajan singer",
    "balaji bhajan party", "sankat mochan bhajan",
]
r = fetch_ideas(balaji_seeds, INDIA)
a = print_table(r, "A7 — BALAJI / HANUMAN KIRTAN (India)", sym="₹")
all_india.extend([(kw, vol, comp, low, high, "Balaji Kirtan") for kw,vol,comp,low,high in a])

# ── A8. Khatu Shyam Baba Kirtan ───────────────────────────────────────────────
shyam_seeds = [
    "khatu shyam bhajan", "shyam baba kirtan", "khatu shyam kirtan",
    "shyam sandhya", "shyam bhajan sandhya", "khatu shyam jagran",
    "shyam chalisa", "om shri shyam devay namah", "shyam baba bhajan party",
    "khatu shyamji bhajan", "shyam baba aarti", "khatu shyam baba bhajan",
    "shyam bhajan singer", "barbarika kirtan",
]
r = fetch_ideas(shyam_seeds, INDIA)
a = print_table(r, "A8 — KHATU SHYAM BABA KIRTAN (India)", sym="₹")
all_india.extend([(kw, vol, comp, low, high, "Khatu Shyam") for kw,vol,comp,low,high in a])

# ── A9. Sai Sandhya ───────────────────────────────────────────────────────────
sai_seeds = [
    "sai sandhya", "sai bhajan sandhya", "sai baba bhajan",
    "sai bhajan singer", "shirdi sai bhajan", "sai baba sandhya",
    "sai bhakti sandhya", "sai bhajan mandali", "sai baba kirtan",
    "sai sandhya booking", "sai aarti", "sai baba bhajan party",
    "sai bhajan for home", "thursday sai bhajan",
]
r = fetch_ideas(sai_seeds, INDIA)
a = print_table(r, "A9 — SAI SANDHYA (India)", sym="₹")
all_india.extend([(kw, vol, comp, low, high, "Sai Sandhya") for kw,vol,comp,low,high in a])

# ── A10. Shiv Sandhya ─────────────────────────────────────────────────────────
shiv_seeds = [
    "shiv sandhya", "shiv bhajan sandhya", "shiv bhajan",
    "shiva bhajan", "om namah shivaya bhajan", "shiv amritwani",
    "somvar bhajan", "mahashivratri bhajan", "shiv chalisa kirtan",
    "shiv bhajan singer", "shiv bhajan mandali", "bhole baba bhajan",
    "shiv shankar bhajan", "shravan bhajan",
]
r = fetch_ideas(shiv_seeds, INDIA)
a = print_table(r, "A10 — SHIV SANDHYA (India)", sym="₹")
all_india.extend([(kw, vol, comp, low, high, "Shiv Sandhya") for kw,vol,comp,low,high in a])

# ─────────────────────────────────────────────────────────────────────────────
# SECTION B: CEREMONY / RITUAL TYPES
# ─────────────────────────────────────────────────────────────────────────────

# ── B1. Mata Ka Jagran ────────────────────────────────────────────────────────
jagran_seeds = [
    "mata ka jagran", "jagran booking", "jagran party near me",
    "jagran mandali booking", "mata jagran price", "jagran party booking delhi",
    "jagran party booking", "mata ka jagrata", "devi jagran booking",
    "mata rani jagran", "navratri jagran", "jagran organiser",
    "allnight jagran booking", "jagran singer near me", "jagran for home",
]
r = fetch_ideas(jagran_seeds, INDIA)
a = print_table(r, "B1 — MATA KA JAGRAN (India)", sym="₹")
all_india.extend([(kw, vol, comp, low, high, "Mata Ka Jagran") for kw,vol,comp,low,high in a])

# ── B2. Mata Ki Chowki ────────────────────────────────────────────────────────
chowki_seeds = [
    "mata ki chowki", "mata ki chowki booking", "mata chowki singer",
    "chowki singer near me", "mata ki chowki price", "chowki party booking",
    "mata chowki for home", "mata chowki for birthday", "devi chowki booking",
    "mata ki choki", "navratri chowki booking", "mata ki chowki mandali",
]
r = fetch_ideas(chowki_seeds, INDIA)
a = print_table(r, "B2 — MATA KI CHOWKI (India)", sym="₹")
all_india.extend([(kw, vol, comp, low, high, "Mata Ki Chowki") for kw,vol,comp,low,high in a])

# ── B3. Bhagwat Katha ─────────────────────────────────────────────────────────
bhagwat_seeds = [
    "bhagwat katha booking", "shrimad bhagwat katha", "bhagwat saptah booking",
    "bhagwat kathavachak", "bhagwat katha for home", "bhagwat katha price",
    "bhagavatam katha booking", "bhagwat katha organiser",
    "krishna katha booking", "bhagwat katha singer", "bhagwat katha 7 days",
    "bhagwat katha programme", "bhagwat katha pravachan",
]
r = fetch_ideas(bhagwat_seeds, INDIA)
a = print_table(r, "B3 — BHAGWAT KATHA (India)", sym="₹")
all_india.extend([(kw, vol, comp, low, high, "Bhagwat Katha") for kw,vol,comp,low,high in a])

# ── B4. Shri Ram Katha ────────────────────────────────────────────────────────
ramkatha_seeds = [
    "ram katha booking", "shri ram katha", "ramayan katha booking",
    "ramcharitmanas katha", "ram kathavachak", "ram katha for home",
    "ramayan pravachan", "ram katha programme", "ram navami katha",
    "ram katha 7 days", "ramkatha organiser", "ramayana katha booking",
]
r = fetch_ideas(ramkatha_seeds, INDIA)
a = print_table(r, "B4 — SHRI RAM KATHA (India)", sym="₹")
all_india.extend([(kw, vol, comp, low, high, "Shri Ram Katha") for kw,vol,comp,low,high in a])

# ── B5. Sunderkand Path ───────────────────────────────────────────────────────
sunderkand_seeds = [
    "sunderkand path", "sundarkand path booking", "sunderkand path at home",
    "sunderkand paath", "sundarkand paath booking", "sunderkand path price",
    "sunderkand for griha pravesh", "sunderkand path singer",
    "sundar kand path", "sunderkand path on tuesday", "sunderkand path mandali",
    "sunderkand path benefits", "hanuman path booking",
]
r = fetch_ideas(sunderkand_seeds, INDIA)
a = print_table(r, "B5 — SUNDERKAND PATH (India)", sym="₹")
all_india.extend([(kw, vol, comp, low, high, "Sunderkand Path") for kw,vol,comp,low,high in a])

# ── B6. Navratri / Garba Night ────────────────────────────────────────────────
navratri_seeds = [
    "navratri garba night", "garba singer booking", "navratri kirtan booking",
    "garba event organiser", "dandiya night booking", "navratri bhajan singer",
    "garba dandiya singer", "navratri programme booking",
    "navratri garba for society", "garba night for housing society",
    "navratri cultural programme", "navaratri bhajan booking",
    "navratri DJ garba booking", "live garba singer",
]
r = fetch_ideas(navratri_seeds, INDIA)
a = print_table(r, "B6 — NAVRATRI / GARBA NIGHT (India)", sym="₹")
all_india.extend([(kw, vol, comp, low, high, "Navratri Garba") for kw,vol,comp,low,high in a])

# ── B7. Bhaktmal Katha ────────────────────────────────────────────────────────
bhaktmal_seeds = [
    "bhaktmal katha", "bhaktamal katha booking", "bhakta charitra katha",
    "bhaktmal pravachan", "sant charitra katha", "bhaktamal path",
    "ramanandi katha", "bhakti katha booking", "sant katha booking",
]
r = fetch_ideas(bhaktmal_seeds, INDIA)
a = print_table(r, "B7 — BHAKTMAL KATHA (India)", sym="₹")
all_india.extend([(kw, vol, comp, low, high, "Bhaktmal Katha") for kw,vol,comp,low,high in a])

# ── B8. Antim Ardas / Antam Sanskar (Sikh last rites) ────────────────────────
antim_seeds = [
    "antim ardas", "antam sanskar", "antim sanskar", "sikh funeral kirtan",
    "sikh last rites kirtan", "sikh funeral prayers", "antim ardaas",
    "sikh funeral path", "akhand path for death", "sikh bereavement kirtan",
    "13 day path sikh", "death anniversary kirtan sikh",
]
r = fetch_ideas(antim_seeds, INDIA)
a = print_table(r, "B8 — ANTIM ARDAS / ANTAM SANSKAR (India)", sym="₹")
all_india.extend([(kw, vol, comp, low, high, "Antim Ardas") for kw,vol,comp,low,high in a])

r_us = fetch_ideas(antim_seeds, USA)
a_us = print_table(r_us, "B8 — ANTIM ARDAS / ANTAM SANSKAR (USA)", sym="$")
all_global.extend([(kw, vol, comp, low, high, "Antim Ardas") for kw,vol,comp,low,high in a_us])

# ─────────────────────────────────────────────────────────────────────────────
# SECTION C: BOOKING OCCASIONS / SETTINGS
# ─────────────────────────────────────────────────────────────────────────────

# ── C1. Wedding & Shaadi ──────────────────────────────────────────────────────
wedding_seeds = [
    "kirtan for wedding", "bhajan for wedding", "wedding kirtan group",
    "shaadi kirtan", "vivah kirtan", "wedding bhajan singer",
    "kirtan singer for shaadi", "anand karaj kirtan singer",
    "pre wedding kirtan", "vidai bhajan", "wedding satsang",
    "bhajan party for wedding", "kirtan for marriage ceremony",
    "wedding devotional music", "shadi ke bhajan",
]
r = fetch_ideas(wedding_seeds, INDIA)
a = print_table(r, "C1 — WEDDING & SHAADI KIRTAN (India)", sym="₹")
all_india.extend([(kw, vol, comp, low, high, "Wedding") for kw,vol,comp,low,high in a])

# ── C2. Musical Pheras ────────────────────────────────────────────────────────
pheras_seeds = [
    "musical pheras", "musical phere", "sangeetmay pheras",
    "saat phere bhajan", "vedic wedding music", "live music for pheras",
    "kirtan during pheras", "bhajan during wedding ceremony",
    "live bhajan for saat phere", "musical wedding ceremony",
    "wedding ceremony singer", "pheras with live singing",
    "sangeet pheras booking", "sacred music for wedding",
]
r = fetch_ideas(pheras_seeds, INDIA)
a = print_table(r, "C2 — MUSICAL PHERAS (India)", sym="₹")
all_india.extend([(kw, vol, comp, low, high, "Musical Pheras") for kw,vol,comp,low,high in a])

# ── C3. Ghar Ka Satsang / Home Session ───────────────────────────────────────
home_seeds = [
    "ghar ka satsang", "home satsang booking", "home bhajan singer",
    "home kirtan booking", "bhajan for home", "house satsang",
    "kirtan at home", "weekly home satsang", "ghar mein bhajan",
    "home bhajan party", "satsang singer for home", "private kirtan booking",
    "bhajan singer for home event", "home puja singer",
]
r = fetch_ideas(home_seeds, INDIA)
a = print_table(r, "C3 — GHAR KA SATSANG / HOME SESSION (India)", sym="₹")
all_india.extend([(kw, vol, comp, low, high, "Ghar Ka Satsang") for kw,vol,comp,low,high in a])

# ── C4. Griha Pravesh ─────────────────────────────────────────────────────────
griha_seeds = [
    "griha pravesh kirtan", "griha pravesh bhajan", "grih pravesh kirtan",
    "housewarming kirtan", "housewarming bhajan", "griha pravesh puja singer",
    "sunderkand for griha pravesh", "kirtan for new home",
    "bhajan for housewarming", "grihapravesh kirtan booking",
    "grah pravesh bhajan singer", "gruha pravesh kirtan",
]
r = fetch_ideas(griha_seeds, INDIA)
a = print_table(r, "C4 — GRIHA PRAVESH KIRTAN (India)", sym="₹")
all_india.extend([(kw, vol, comp, low, high, "Griha Pravesh") for kw,vol,comp,low,high in a])

# ── C5. Memorial & Prayer Meeting ────────────────────────────────────────────
memorial_seeds = [
    "shradhanjali sabha", "shok sabha bhajan", "prayer meeting bhajan",
    "condolence meeting kirtan", "tehravin bhajan", "chautha bhajan",
    "barsi satsang", "death anniversary bhajan", "memorial kirtan",
    "shraddhanjali kirtan", "antim ardas bhajan", "13th day kirtan",
    "shraadh bhajan", "rasam pagri kirtan", "prayer meet singer",
    "death ceremony bhajan singer",
]
r = fetch_ideas(memorial_seeds, INDIA)
a = print_table(r, "C5 — MEMORIAL & PRAYER MEETING (India)", sym="₹")
all_india.extend([(kw, vol, comp, low, high, "Memorial") for kw,vol,comp,low,high in a])

# ── C6. Guru Ji Kirtan / Satsang ─────────────────────────────────────────────
guruji_seeds = [
    "guru ji kirtan", "guruji satsang", "guru ji bhajan sandhya",
    "guru satsang booking", "guru bhajan singer", "spiritual guru kirtan",
    "guruji mantra jaap", "shukrana satsang", "guru ji program booking",
    "guru ji ki sandhya", "guru purnima kirtan", "guru nanak jayanti kirtan",
]
r = fetch_ideas(guruji_seeds, INDIA)
a = print_table(r, "C6 — GURU JI KIRTAN / SATSANG (India)", sym="₹")
all_india.extend([(kw, vol, comp, low, high, "Guru Ji Kirtan") for kw,vol,comp,low,high in a])

# ─────────────────────────────────────────────────────────────────────────────
# SECTION D: DIASPORA — GLOBAL BOOKING INTENT
# ─────────────────────────────────────────────────────────────────────────────
diaspora_seeds = [
    "kirtan near me", "kirtan for events near me", "hire kirtan group",
    "book kirtan singer", "kirtan booking usa", "kirtan for home usa",
    "indian devotional music booking", "bhajan singer near me",
    "kirtan for navratri usa", "hindu religious music event",
    "kirtan for wedding usa", "sikh kirtan booking usa",
    "hare krishna kirtan near me", "kirtan meditation event",
    "book devotional singer", "live kirtan concert near me",
]
r_us = fetch_ideas(diaspora_seeds, USA)
a_us = print_table(r_us, "D1 — DIASPORA BOOKING INTENT (USA)", sym="$")
all_global.extend([(kw, vol, comp, low, high, "Diaspora USA") for kw,vol,comp,low,high in a_us])

r_uk = fetch_ideas(diaspora_seeds, UK)
a_uk = print_table(r_uk, "D2 — DIASPORA BOOKING INTENT (UK)", sym="£")
all_global.extend([(kw, vol, comp, low, high, "Diaspora UK") for kw,vol,comp,low,high in a_uk])

# ─────────────────────────────────────────────────────────────────────────────
# SECTION E: VARIANT SPELLINGS & SYNONYMS (catch alternate searches)
# ─────────────────────────────────────────────────────────────────────────────
variant_seeds = [
    "keertan booking", "keertana booking", "bhakti sangeet",
    "satsanga booking", "jagrata booking", "jagraan booking",
    "navaratri garba", "navrathri bhajan", "griha pravesha kirtan",
    "gruh pravesh kirtan", "shradhanjali sabha", "shraddhanjali",
    "tehravin", "chautha ceremony", "antam ardas", "antim ardaas",
    "sundarkand path", "ramcharitmanas path", "bhagavata katha",
    "krishna katha", "mataji bhajan", "sherawali mata bhajan",
    "vaishno devi kirtan", "hanuman chalisa path", "kirtan wala",
    "kirtanwala booking", "kirtan seva booking",
]
r = fetch_ideas(variant_seeds, INDIA)
a = print_table(r, "E1 — VARIANT SPELLINGS & SYNONYMS (India)", sym="₹")
all_india.extend([(kw, vol, comp, low, high, "Variants") for kw,vol,comp,low,high in a])

# ═════════════════════════════════════════════════════════════════════════════
# MASTER SUMMARY TABLES
# ═════════════════════════════════════════════════════════════════════════════

print(f"\n\n{'█'*130}")
print("  MASTER INDIA TABLE — All Unique Keywords (vol ≥ 10) sorted by volume")
print(f"{'█'*130}")

# Deduplicate
india_by_kw = {}
for kw, vol, comp, low, high, cat in sorted(all_india, key=lambda x: x[1], reverse=True):
    if kw not in india_by_kw:
        india_by_kw[kw] = (vol, comp, low, high, cat)

deduped_india = [(kw,) + v for kw, v in sorted(india_by_kw.items(), key=lambda x: x[1][0], reverse=True) if v[0] >= 10]

print(f"\n  {'Keyword':<65} {'Vol/mo':>8} {'Comp':>10} {'Category':<22} {'Low CPC':>10} {'High CPC':>10}")
print(f"  {'-'*131}")
for kw, vol, comp, low, high, cat in deduped_india[:100]:
    cpc = f"₹{low:.2f}–₹{high:.2f}" if high else "—"
    print(f"  {kw:<65} {vol:>8,} {comp:>10} {cat:<22} {cpc}")
print(f"\n  Total unique India keywords (vol ≥ 10): {len(deduped_india)}")
print(f"  Combined vol (top 100): {sum(r[1] for r in deduped_india[:100]):,}/mo")

# ── By Category summary ──────────────────────────────────────────────────────
print(f"\n\n{'█'*130}")
print("  INDIA — VOLUME BY CATEGORY")
print(f"{'█'*130}")
cat_vol = defaultdict(int)
cat_count = defaultdict(int)
for kw, vol, comp, low, high, cat in deduped_india:
    cat_vol[cat] += vol
    cat_count[cat] += 1

print(f"\n  {'Category':<28} {'Total Vol/mo':>14} {'Keywords':>10} {'Avg Vol':>10}")
print(f"  {'-'*68}")
for cat, vol in sorted(cat_vol.items(), key=lambda x: x[1], reverse=True):
    avg = vol // cat_count[cat]
    print(f"  {cat:<28} {vol:>14,} {cat_count[cat]:>10,} {avg:>10,}")

# ── SEO Sweet Spots ───────────────────────────────────────────────────────────
print(f"\n\n{'█'*130}")
print("  SEO SWEET SPOTS — Low Competition + Vol ≥ 10 (India) — BEST PAGES TO BUILD")
print(f"{'█'*130}")
sweet = [(kw, vol, comp, low, high, cat) for kw, vol, comp, low, high, cat in deduped_india if comp in ("LOW","MEDIUM")]
sweet.sort(key=lambda x: x[1], reverse=True)
print(f"\n  {'Keyword':<65} {'Vol/mo':>8} {'Comp':>10} {'Category':<22}")
print(f"  {'-'*111}")
for kw, vol, comp, low, high, cat in sweet[:80]:
    print(f"  {kw:<65} {vol:>8,} {comp:>10} {cat:<22}")
print(f"\n  Total SEO opportunities: {len(sweet)}")

# ── Global Diaspora Table ────────────────────────────────────────────────────
print(f"\n\n{'█'*130}")
print("  DIASPORA MASTER TABLE — All Unique Keywords (vol ≥ 10) sorted by volume")
print(f"{'█'*130}")
global_by_kw = {}
for kw, vol, comp, low, high, cat in sorted(all_global, key=lambda x: x[1], reverse=True):
    if kw not in global_by_kw:
        global_by_kw[kw] = (vol, comp, low, high, cat)
deduped_global = [(kw,)+v for kw,v in sorted(global_by_kw.items(), key=lambda x: x[1][0], reverse=True) if v[0] >= 10]
print(f"\n  {'Keyword':<65} {'Vol/mo':>8} {'Comp':>10} {'Category':<20}")
print(f"  {'-'*109}")
for kw, vol, comp, low, high, cat in deduped_global[:60]:
    print(f"  {kw:<65} {vol:>8,} {comp:>10} {cat:<20}")
print(f"\n  Total Diaspora keywords (vol ≥ 10): {len(deduped_global)}")
print(f"  Combined vol (top 60): {sum(r[1] for r in deduped_global[:60]):,}/mo")
