import { NextRequest, NextResponse } from "next/server"
import { prisma } from "@/lib/db"

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const ads = await prisma.ad.findMany({
    where: { competitorId: id },
    orderBy: [{ startDate: "asc" }, { createdAt: "desc" }],
  })
  return NextResponse.json(ads)
}
