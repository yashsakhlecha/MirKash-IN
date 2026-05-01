"use client"

import { useState, useEffect } from "react"
import { CompetitorPanel } from "@/components/competitor-panel"
import { AdsTable } from "@/components/ads-table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Globe, TrendingUp, ChevronLeft } from "lucide-react"

interface Competitor {
  id: string
  name: string
  metaPageId: string
  libraryUrl: string
  totalAds: number
  lastSyncedAt: string | null
}

export default function Home() {
  const [competitors, setCompetitors] = useState<Competitor[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)

  useEffect(() => {
    fetch("/api/competitors")
      .then((r) => r.json())
      .then((data) => {
        setCompetitors(Array.isArray(data) ? data : [])
      })
  }, [])

  const selectedCompetitor = competitors.find((c) => c.id === selectedId) ?? null

  function handleAdd(competitor: Competitor) {
    setCompetitors((prev) => [competitor, ...prev])
    setSelectedId(competitor.id)
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button className="text-muted-foreground hover:text-foreground">
            <ChevronLeft className="h-5 w-5" />
          </button>
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-full bg-purple-100 dark:bg-purple-900/40 flex items-center justify-center">
              <Globe className="h-4 w-4 text-purple-600" />
            </div>
            <span className="font-semibold text-sm">Competitor Ads</span>
          </div>
        </div>
        <span className="text-xs text-muted-foreground bg-muted px-2.5 py-1 rounded-full">
          Powered by Tamasha
        </span>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6 space-y-6">
        {/* Title */}
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Track &amp; Analyse Competitors</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Search for competitor pages, sync their latest ads, and use AI to analyze their hooks and scripts.
          </p>
        </div>

        <Tabs defaultValue="explorer">
          <TabsList className="mb-4">
            <TabsTrigger value="explorer" className="gap-1.5">
              <Globe className="h-3.5 w-3.5" /> Explorer
            </TabsTrigger>
            <TabsTrigger value="global" className="gap-1.5" disabled>
              <TrendingUp className="h-3.5 w-3.5" /> Global Feed
            </TabsTrigger>
          </TabsList>

          <TabsContent value="explorer" className="space-y-6">
            <CompetitorPanel
              competitors={competitors}
              selectedId={selectedId}
              onSelect={setSelectedId}
              onAdd={handleAdd}
            />

            {selectedCompetitor && (
              <div className="border rounded-xl p-4">
                <AdsTable competitor={selectedCompetitor} />
              </div>
            )}
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
