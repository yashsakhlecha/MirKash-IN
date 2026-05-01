import { NextRequest, NextResponse } from "next/server"
import { prisma } from "@/lib/db"

export async function GET() {
  const competitors = await prisma.competitor.findMany({
    orderBy: { createdAt: "desc" },
    include: { _count: { select: { ads: true } } },
  })
  return NextResponse.json(competitors)
}

export async function POST(req: NextRequest) {
  const { name, libraryUrl } = await req.json()

  if (!name || !libraryUrl) {
    return NextResponse.json({ error: "name and libraryUrl are required" }, { status: 400 })
  }

  const pageIdMatch = libraryUrl.match(/view_all_page_id=(\d+)/)
  if (!pageIdMatch) {
    return NextResponse.json(
      { error: "URL must contain view_all_page_id=XXX" },
      { status: 400 }
    )
  }
  const metaPageId = pageIdMatch[1]

  const existing = await prisma.competitor.findUnique({ where: { metaPageId } })
  if (existing) {
    return NextResponse.json({ error: "Competitor already tracked" }, { status: 409 })
  }

  const competitor = await prisma.competitor.create({
    data: { name, metaPageId, libraryUrl },
  })

  return NextResponse.json(competitor, { status: 201 })
}
