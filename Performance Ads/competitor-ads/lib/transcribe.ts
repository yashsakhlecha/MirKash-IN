import { GoogleGenAI } from "@google/genai"

export interface VideoAnalysis {
  transcript: string | null
  sceneDescription: string | null
}

export async function analyseVideoUrl(videoUrl: string): Promise<VideoAnalysis> {
  const apiKey = process.env.GEMINI_API_KEY
  if (!apiKey) throw new Error("GEMINI_API_KEY not set")

  const ai = new GoogleGenAI({ apiKey })

  const response = await fetch(videoUrl, {
    headers: { "User-Agent": "Mozilla/5.0" },
  })
  if (!response.ok) return { transcript: null, sceneDescription: null }

  const blob = new Blob([await response.arrayBuffer()], { type: "video/mp4" })

  const uploaded = await ai.files.upload({
    file: blob,
    config: { mimeType: "video/mp4", displayName: "ad.mp4" },
  })

  let fileInfo = await ai.files.get({ name: uploaded.name! })
  let attempts = 0
  while (fileInfo.state === "PROCESSING" && attempts < 30) {
    await new Promise((r) => setTimeout(r, 2000))
    fileInfo = await ai.files.get({ name: uploaded.name! })
    attempts++
  }

  if (fileInfo.state !== "ACTIVE") return { transcript: null, sceneDescription: null }

  const result = await ai.models.generateContent({
    model: "gemini-3-flash-preview",
    contents: [
      {
        role: "user",
        parts: [
          { fileData: { mimeType: "video/mp4", fileUri: fileInfo.uri! } },
          {
            text: `Analyse this video ad and return a JSON object with exactly two keys:
{
  "transcript": <verbatim spoken words from the audio, or null if no speech>,
  "sceneDescription": <2-3 sentence description of what is shown visually: setting, people, products, actions, mood>
}
Return only valid JSON, no markdown.`,
          },
        ],
      },
    ],
    config: { responseMimeType: "application/json" },
  })

  await ai.files.delete({ name: uploaded.name! }).catch(() => {})

  try {
    const parsed = JSON.parse(result.text ?? "{}")
    return {
      transcript: parsed.transcript || null,
      sceneDescription: parsed.sceneDescription || null,
    }
  } catch {
    return { transcript: null, sceneDescription: null }
  }
}
