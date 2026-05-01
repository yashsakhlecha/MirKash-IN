"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Globe, Plus, Loader2 } from "lucide-react"

interface Competitor {
  id: string
  name: string
  metaPageId: string
  libraryUrl: string
  totalAds: number
  lastSyncedAt: string | null
}

interface Props {
  competitors: Competitor[]
  selectedId: string | null
  onSelect: (id: string) => void
  onAdd: (competitor: Competitor) => void
}

export function CompetitorPanel({ competitors, selectedId, onSelect, onAdd }: Props) {
  const [url, setUrl] = useState("")
  const [name, setName] = useState("")
  const [adding, setAdding] = useState(false)
  const [error, setError] = useState("")

  async function handleAdd() {
    if (!url.trim() || !name.trim()) {
      setError("Both name and URL are required")
      return
    }
    setAdding(true)
    setError("")
    try {
      const res = await fetch("/api/competitors", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name.trim(), libraryUrl: url.trim() }),
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.error ?? "Failed to add competitor")
        return
      }
      onAdd(data)
      setUrl("")
      setName("")
    } finally {
      setAdding(false)
    }
  }

  return (
    <div className="grid grid-cols-2 gap-4">
      {/* Add Competitor */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <span className="text-purple-500">✦</span> Add Competitor
          </CardTitle>
          <p className="text-xs text-muted-foreground">Search by name or paste a Meta Ad Library URL</p>
        </CardHeader>
        <CardContent className="space-y-3">
          <Input
            placeholder="Paste Ad Library URL..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
          <p className="text-xs text-muted-foreground">
            Tip: Provide the full URL containing &apos;view_all_page_id&apos;
          </p>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <div className="flex-1 h-px bg-border" />
            OR SEARCH BY NAME
            <div className="flex-1 h-px bg-border" />
          </div>
          <Input
            placeholder="Competitor name..."
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          {error && <p className="text-xs text-red-500">{error}</p>}
          <Button onClick={handleAdd} disabled={adding} className="w-full gap-1.5" size="sm">
            {adding ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Plus className="h-3.5 w-3.5" />}
            Add Competitor
          </Button>
        </CardContent>
      </Card>

      {/* Tracked Competitors */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <span className="text-green-500">●</span> Tracked Competitors ({competitors.length})
          </CardTitle>
          <p className="text-xs text-muted-foreground">Select a competitor to view and analyze their ads</p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-2">
            {competitors.map((c) => (
              <button
                key={c.id}
                onClick={() => onSelect(c.id)}
                className={`flex flex-col items-center gap-1.5 p-3 rounded-lg border text-xs transition-colors hover:bg-accent ${
                  selectedId === c.id ? "border-purple-400 bg-purple-50 dark:bg-purple-950/20" : "border-border"
                }`}
              >
                <Globe className="h-6 w-6 text-purple-400" />
                <span className="text-center leading-tight font-medium">{c.name}</span>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
