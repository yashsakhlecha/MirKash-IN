import { ApifyClient } from "apify-client"

export interface RawAd {
  metaAdId: string
  videoUrl: string | null
  thumbnailUrl: string | null
  adCopyText: string | null
  startDate: Date | null
}

function extractBody(body: unknown): string | null {
  if (typeof body === "string" && body.trim()) return body.trim()
  if (body && typeof body === "object" && "text" in body && typeof (body as Record<string, unknown>).text === "string") {
    return ((body as Record<string, unknown>).text as string).trim() || null
  }
  return null
}

export async function scrapeCompetitorAds(
  libraryUrl: string,
  maxResults = 50
): Promise<RawAd[]> {
  const apiToken = process.env.APIFY_API_TOKEN
  if (!apiToken) throw new Error("APIFY_API_TOKEN not set")

  const client = new ApifyClient({ token: apiToken })

  const run = await client.actor("curious_coder/facebook-ads-library-scraper").call({
    urls: [{ url: libraryUrl }],
    maxResults,
  })

  const { items } = await client.dataset(run.defaultDatasetId).listItems()

  return items.map((item: Record<string, unknown>) => {
    const snapshot = item.snapshot as Record<string, unknown> | undefined
    const cards = snapshot?.cards as Array<Record<string, unknown>> | undefined

    // Find the first card with a video, else fall back to first card
    const videoCard = cards?.find((c) => c.video_hd_url) ?? cards?.[0]

    const videoUrl =
      (videoCard?.video_hd_url as string | undefined) ??
      (videoCard?.video_sd_url as string | undefined) ??
      null

    const thumbnailUrl =
      (videoCard?.video_preview_image_url as string | undefined) ??
      (videoCard?.original_image_url as string | undefined) ??
      null

    // Body text: prefer snapshot-level, fall back to first card body
    // snapshot.body can be a string or { text: "..." }
    const adCopyText = extractBody(snapshot?.body) ?? extractBody(videoCard?.body) ?? null

    const startDateRaw = item.start_date as number | string | undefined
    const startDate = startDateRaw
      ? new Date(typeof startDateRaw === "number" ? startDateRaw * 1000 : startDateRaw)
      : null

    return {
      metaAdId: String(item.ad_archive_id ?? item.adId ?? Math.random()),
      videoUrl,
      thumbnailUrl,
      adCopyText,
      startDate,
    }
  })
}
