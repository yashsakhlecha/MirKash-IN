import { NextRequest, NextResponse } from "next/server"
import { prisma } from "@/lib/db"
import { scrapeCompetitorAds } from "@/lib/scraper"
import { analyseVideoUrl } from "@/lib/transcribe"
import { classifyAd } from "@/lib/classify"

export async function POST(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params

  const competitor = await prisma.competitor.findUnique({ where: { id } })
  if (!competitor) {
    return NextResponse.json({ error: "Competitor not found" }, { status: 404 })
  }

  let rawAds
  try {
    rawAds = await scrapeCompetitorAds(competitor.libraryUrl)
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Scrape failed"
    return NextResponse.json({ error: msg }, { status: 502 })
  }

  // Save all new ads to DB first
  const newAdIds: { adId: string; videoUrl: string | null; adCopyText: string | null }[] = []

  for (const raw of rawAds) {
    const exists = await prisma.ad.findUnique({ where: { metaAdId: raw.metaAdId } })
    if (exists) continue

    const ad = await prisma.ad.create({
      data: {
        competitorId: id,
        metaAdId: raw.metaAdId,
        videoUrl: raw.videoUrl,
        thumbnailUrl: raw.thumbnailUrl,
        adCopyText: raw.adCopyText,
        startDate: raw.startDate,
      },
    })

    newAdIds.push({ adId: ad.id, videoUrl: raw.videoUrl, adCopyText: raw.adCopyText })
  }

  await prisma.competitor.update({
    where: { id },
    data: { totalAds: rawAds.length, lastSyncedAt: new Date() },
  })

  // Pick top 10 oldest ads (longest-running = most battle-tested) for analysis
  const adsToAnalyse = await prisma.ad.findMany({
    where: { competitorId: id, language: null },
    orderBy: { startDate: "asc" },
    take: 10,
  })

  // Process all ads in parallel (fire-and-forget)
  processAdsInParallel(adsToAnalyse.map((a) => ({ adId: a.id, videoUrl: a.videoUrl, adCopyText: a.adCopyText })))

  return NextResponse.json({ newAds: newAdIds.length, totalAds: rawAds.length, analysing: adsToAnalyse.length })
}

async function processAdsInParallel(
  ads: { adId: string; videoUrl: string | null; adCopyText: string | null }[]
) {
  await Promise.all(ads.map((ad) => processAd(ad.adId, ad.videoUrl, ad.adCopyText)))
}

async function processAd(
  adId: string,
  videoUrl: string | null,
  adCopyText: string | null
) {
  try {
    let script: string | null = null
    let sceneDescription: string | null = null

    if (videoUrl) {
      const analysis = await analyseVideoUrl(videoUrl)
      script = analysis.transcript
      sceneDescription = analysis.sceneDescription
    }

    const classification = await classifyAd(script, adCopyText)

    await prisma.ad.update({
      where: { id: adId },
      data: {
        script,
        sceneDescription,
        language: classification.language,
        archetype: classification.archetype,
        hookType: classification.hookType,
      },
    })
  } catch {
    // best-effort
  }
}
