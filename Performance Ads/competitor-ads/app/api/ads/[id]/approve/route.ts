import { NextRequest, NextResponse } from "next/server"
import { prisma } from "@/lib/db"

export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const { status } = await req.json()

  if (!["approved", "rejected", "pending"].includes(status)) {
    return NextResponse.json({ error: "Invalid status" }, { status: 400 })
  }

  const ad = await prisma.ad.update({
    where: { id },
    data: { status },
  })

  return NextResponse.json(ad)
}
