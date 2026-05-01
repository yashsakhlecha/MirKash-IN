"use client"

import { useState, useEffect, useRef } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Loader2, RefreshCw, CheckCircle, Info } from "lucide-react"

interface Ad {
  id: string
  metaAdId: string
  videoUrl: string | null
  thumbnailUrl: string | null
  adCopyText: string | null
  script: string | null
  sceneDescription: string | null
  language: string | null
  archetype: string | null
  hookType: string | null
  status: string
  startDate: string | null
  createdAt: string
}

interface Competitor {
  id: string
  name: string
  totalAds: number
  lastSyncedAt: string | null
}

interface Props {
  competitor: Competitor
}

const ARCHETYPE_COLORS: Record<string, string> = {
  ROMANTIC_SEEKER: "bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-300",
  VENTING_OUT: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300",
  ASPIRATIONAL: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300",
  PROBLEM_SOLVER: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300",
  SOCIAL_PROOF: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300",
  FEAR_BASED: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300",
  CURIOSITY: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300",
  HUMOR: "bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-300",
  EDUCATIONAL: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300",
}

export function AdsTable({ competitor }: Props) {
  const [ads, setAds] = useState<Ad[]>([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [search, setSearch] = useState("")
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    fetchAds()
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [competitor.id])

  async function fetchAds() {
    setLoading(true)
    try {
      const res = await fetch(`/api/competitors/${competitor.id}/ads`)
      const data = await res.json()
      setAds(Array.isArray(data) ? data : [])
    } finally {
      setLoading(false)
    }
  }

  async function handleSync() {
    setSyncing(true)
    try {
      await fetch(`/api/competitors/${competitor.id}/sync`, { method: "POST" })
      await fetchAds()
      // poll every 5s for up to 3 minutes to catch transcription completions
      let ticks = 0
      pollRef.current = setInterval(async () => {
        ticks++
        await fetchAds()
        if (ticks >= 36 && pollRef.current) clearInterval(pollRef.current)
      }, 5000)
    } finally {
      setSyncing(false)
    }
  }

  async function handleApprove(adId: string) {
    await fetch(`/api/ads/${adId}/approve`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "approved" }),
    })
    setAds((prev) => prev.map((a) => (a.id === adId ? { ...a, status: "approved" } : a)))
  }

  const filtered = ads.filter((ad) => {
    if (!search) return true
    const q = search.toLowerCase()
    return (
      ad.script?.toLowerCase().includes(q) ||
      ad.adCopyText?.toLowerCase().includes(q) ||
      ad.language?.toLowerCase().includes(q) ||
      ad.archetype?.toLowerCase().includes(q)
    )
  })

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center gap-3 flex-wrap">
        <h2 className="font-semibold text-lg">{competitor.name} Ads</h2>
        <Badge variant="outline" className="text-purple-600 border-purple-300 gap-1">
          <span className="text-xs">⚡</span> {competitor.totalAds} Ads
        </Badge>
        <div className="flex-1" />
        <Input
          placeholder="Search ads..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-48 h-8 text-sm"
        />
        <Button
          size="sm"
          variant="outline"
          onClick={handleSync}
          disabled={syncing}
          className="gap-1.5"
        >
          {syncing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
          Sync Ads
        </Button>
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex items-center justify-center h-40 text-muted-foreground gap-2">
          <Loader2 className="animate-spin h-4 w-4" /> Loading ads...
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex items-center justify-center h-40 text-muted-foreground text-sm">
          {ads.length === 0 ? "No ads synced yet. Click Sync Ads to start." : "No ads match your search."}
        </div>
      ) : (
        <div className="border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-muted/50 border-b">
                <th className="text-left p-3 font-medium text-muted-foreground w-48">Ad Video</th>
                <th className="text-left p-3 font-medium text-muted-foreground w-44">Language & Archetype</th>
                <th className="text-left p-3 font-medium text-muted-foreground">Ad Script</th>
                <th className="text-left p-3 font-medium text-muted-foreground w-48">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((ad, i) => (
                <tr key={ad.id} className={`border-b last:border-0 ${i % 2 === 0 ? "" : "bg-muted/20"}`}>
                  {/* Video */}
                  <td className="p-3 align-top">
                    <div className="w-40 space-y-1">
                      {ad.videoUrl ? (
                        <video
                          src={ad.videoUrl}
                          poster={ad.thumbnailUrl ?? undefined}
                          controls
                          className="w-full rounded aspect-[9/16] object-cover bg-black"
                        />
                      ) : ad.thumbnailUrl ? (
                        <img
                          src={ad.thumbnailUrl}
                          alt="ad thumbnail"
                          className="w-full rounded aspect-[9/16] object-cover bg-muted"
                        />
                      ) : (
                        <div className="w-full rounded aspect-[9/16] bg-muted flex items-center justify-center text-xs text-muted-foreground">
                          No media
                        </div>
                      )}
                      <p className="text-xs text-muted-foreground truncate">ID: {ad.metaAdId}</p>
                    </div>
                  </td>

                  {/* Language & Archetype */}
                  <td className="p-3 align-top">
                    <div className="flex flex-col gap-1.5">
                      {ad.language && (
                        <Badge variant="outline" className="text-xs w-fit">
                          🌐 {ad.language}
                        </Badge>
                      )}
                      {ad.archetype && (
                        <span
                          className={`text-xs px-2 py-0.5 rounded-full font-medium w-fit ${
                            ARCHETYPE_COLORS[ad.archetype] ?? "bg-gray-100 text-gray-700"
                          }`}
                        >
                          {ad.archetype.replace(/_/g, " ")}
                        </span>
                      )}
                      {ad.hookType && (
                        <span className="text-xs px-2 py-0.5 rounded-full font-medium w-fit bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300">
                          ⚡ {ad.hookType.replace(/_/g, " ")}
                        </span>
                      )}
                      {!ad.language && !ad.archetype && (
                        <span className="text-xs text-muted-foreground flex items-center gap-1">
                          <Loader2 className="h-3 w-3 animate-spin" /> Processing...
                        </span>
                      )}
                    </div>
                  </td>

                  {/* Script & Scene */}
                  <td className="p-3 align-top max-w-xs">
                    <div className="space-y-2">
                      {ad.script ? (
                        <div>
                          <p className="text-xs font-medium text-muted-foreground mb-0.5">Script</p>
                          <p className={`text-sm leading-relaxed ${expandedId === ad.id ? "" : "line-clamp-4"}`}>
                            {ad.script}
                          </p>
                          {ad.script.length > 200 && (
                            <button
                              className="text-xs text-purple-600 mt-1 hover:underline"
                              onClick={() => setExpandedId(expandedId === ad.id ? null : ad.id)}
                            >
                              {expandedId === ad.id ? "Show less" : "Show more"}
                            </button>
                          )}
                        </div>
                      ) : ad.adCopyText ? (
                        <div>
                          <p className="text-xs font-medium text-muted-foreground mb-0.5">Ad Copy</p>
                          <p className="text-sm text-muted-foreground italic line-clamp-4">{ad.adCopyText}</p>
                        </div>
                      ) : (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                      {ad.sceneDescription && (
                        <div>
                          <p className="text-xs font-medium text-muted-foreground mb-0.5">Scene</p>
                          <p className="text-xs text-muted-foreground leading-relaxed line-clamp-3">{ad.sceneDescription}</p>
                        </div>
                      )}
                    </div>
                  </td>

                  {/* Actions */}
                  <td className="p-3 align-top">
                    <div className="flex flex-col gap-2">
                      <a
                        href={`https://www.facebook.com/ads/library/?id=${ad.metaAdId}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center justify-center gap-1.5 text-xs h-8 w-full rounded-md border border-input bg-background px-3 hover:bg-accent hover:text-accent-foreground transition-colors"
                      >
                        <Info className="h-3.5 w-3.5" /> View Ad Details
                      </a>
                      {ad.status === "approved" ? (
                        <div className="flex items-center gap-1.5 text-xs text-green-600 font-medium">
                          <CheckCircle className="h-3.5 w-3.5" /> Approved
                        </div>
                      ) : (
                        <Button
                          size="sm"
                          className="gap-1.5 text-xs h-8 w-full bg-purple-600 hover:bg-purple-700"
                          onClick={() => handleApprove(ad.id)}
                        >
                          <CheckCircle className="h-3.5 w-3.5" /> Approve for Auto Gen
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
