import { GoogleGenAI } from "@google/genai"

export interface Classification {
  language: string
  archetype: string
  hookType: string
}

const PROMPT = `You are an expert ad analyst. Given an ad script and/or ad copy text, classify the ad.
Return ONLY valid JSON with these exact keys:
{
  "language": one of "HINDI" | "ENGLISH" | "TELUGU" | "KANNADA" | "TAMIL" | "BENGALI" | "MARATHI" | "PUNJABI" | "GUJARATI" | "MALAYALAM" | "OTHER",
  "archetype": one of "ROMANTIC_SEEKER" | "VENTING_OUT" | "ASPIRATIONAL" | "PROBLEM_SOLVER" | "SOCIAL_PROOF" | "FEAR_BASED" | "CURIOSITY" | "HUMOR" | "EDUCATIONAL",
  "hookType": one of "HUMAN_SHOT" | "ANIMATION" | "UGC" | "TALKING_HEAD" | "SLIDESHOW" | "SCREEN_RECORDING" | "TEXT_ONLY"
}
Base language on the script text language. Archetype on the emotional hook/narrative. HookType on video format cues.`

export async function classifyAd(
  script: string | null,
  adCopyText: string | null
): Promise<Classification> {
  const apiKey = process.env.GEMINI_API_KEY
  if (!apiKey) throw new Error("GEMINI_API_KEY not set")

  const content = [
    script ? `Script: ${script}` : "",
    adCopyText ? `Ad Copy: ${adCopyText}` : "",
  ]
    .filter(Boolean)
    .join("\n\n")

  if (!content.trim()) {
    return { language: "UNKNOWN", archetype: "UNKNOWN", hookType: "UNKNOWN" }
  }

  const ai = new GoogleGenAI({ apiKey })

  const result = await ai.models.generateContent({
    model: "gemini-3.1-flash-lite-preview",
    contents: [{ role: "user", parts: [{ text: `${PROMPT}\n\n${content}` }] }],
    config: {
      responseMimeType: "application/json",
      maxOutputTokens: 150,
    },
  })

  const raw = result.text ?? "{}"
  const parsed = JSON.parse(raw)

  return {
    language: parsed.language ?? "UNKNOWN",
    archetype: parsed.archetype ?? "UNKNOWN",
    hookType: parsed.hookType ?? "UNKNOWN",
  }
}
