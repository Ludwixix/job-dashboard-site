// netlify/functions/generate.mjs
// Serverless handler powering the "✨ Generate" button on each dashboard card.
//
// Contract (see index.html -> window.generateJob):
//   POST /.netlify/functions/generate
//   body:  { title, company, description, why, location }
//   resp:  { resume: "<markdown>", cover_letter: "<markdown>" }
//
// The client renders the returned markdown to styled HTML and invokes the
// browser print dialog to produce the PDF. No server-side PDF needed.
//
// Secrets are read from Netlify env vars (set via `netlify env:set`), NOT from
// committed source. Reads: OPENROUTER_API_KEY (or OPENAI_API_KEY) and LLM_MODEL.

import { readFileSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

// --- LLM call via raw fetch (no SDK dependency) --------------------------
async function callLLM(messages) {
  const key = process.env.OPENROUTER_API_KEY || process.env.OPENAI_API_KEY;
  if (!key) {
    return { error: "OPENROUTER_API_KEY not configured on this function" };
  }

  const url = "https://openrouter.ai/api/v1/chat/completions";
  const model = process.env.LLM_MODEL || "openrouter/google/gemini-2.5-flash-lite";

  try {
    const resp = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${key}`,
      },
      body: JSON.stringify({
        model,
        messages,
        temperature: 0.4,
        max_tokens: 4000,
      }),
    });

    if (!resp.ok) {
      const body = await resp.text();
      return { error: `LLM upstream ${resp.status}: ${body.slice(0, 300)}` };
    }
    const data = await resp.json();
    const content = data?.choices?.[0]?.message?.content;
    if (!content) return { error: "LLM returned empty content" };
    return { content };
  } catch (e) {
    return { error: `fetch failed: ${e.message}` };
  }
}

// --- Read a committed repo-root file from the deployed function ----------
function readRepoFile(rel) {
  const here = dirname(fileURLToPath(import.meta.url));
  // <site>/netlify/functions/generate.mjs -> <site>/<rel>
  const p = join(here, "..", "..", rel);
  return readFileSync(p, "utf-8");
}

export const handler = async (event) => {
  let job;
  try {
    job = JSON.parse(event.body || "{}");
  } catch {
    return { statusCode: 400, body: JSON.stringify({ error: "invalid JSON" }) };
  }

  const title = job.title || "";
  const company = job.company || "";
  const description = (job.description || "").slice(0, 1200);
  const why = job.why || "";
  const location = job.location || "";

  // Candidate source-of-truth (committed files).
  let resume = "";
  let profile = "";
  try {
    resume = readRepoFile("resume.md");
  } catch {}
  try {
    profile = readRepoFile("job_profile.json");
  } catch {}

  const systemPrompt = `You are a senior Australian recruitment specialist producing a
tailored résumé and cover letter, in Markdown, from the candidate's REAL, VERIFIED
work history ONLY.

RULES — ABSOLUTE:
- NEVER fabricate employers, job titles, dates, qualifications, licences, security
  clearances, vehicle access, RSA, or any skill not present in the candidate profile.
- The role-specific résumé should re-order and tailor REAL experience and skills to
  match the job posting.
- Cover letter: 3-4 short paragraphs, professional but human, referencing the company,
  role title, location, and 2-3 genuinely matched wins. No fabrications.
- Australian spelling (organise, licence). Clean Markdown.
- Do NOT include an email/phone identity block at the top of the résumé body; the
  on-screen header already carries the identity.`;

  const userPrompt = `Candidate master résumé (VERIFIED FACT ONLY):
${resume}

Candidate profile JSON:
${profile}

=== TARGET ROLE ===
Title: ${title}
Company: ${company}
Location: ${location}
Why we flagged it: ${why}

Role description:
${description}

Produce TWO Markdown documents, separated exactly by the single line:
===COVER_LETTER===

Résumé section first (## Résumé headings, - bullets, no identity/contact block),
then the separator line, then the cover letter (## Cover Letter, 3-4 paragraphs,
company-aware).`;

  const result = await callLLM([
    { role: "system", content: systemPrompt },
    { role: "user", content: userPrompt },
  ]);

  if (result.error) {
    return {
      statusCode: 502,
      body: JSON.stringify({
        error: result.error,
        hint: "Ensure OPENROUTER_API_KEY env is set on this Netlify function.",
      }),
    };
  }

  // Split on the separator (fall back to a blank line or treat all as resume).
  const SEP = "===COVER_LETTER===";
  const idx = result.content.indexOf(SEP);
  let resumeMd = result.content;
  let coverMd = "";
  if (idx >= 0) {
    resumeMd = result.content.slice(0, idx).trim();
    coverMd = result.content.slice(idx + SEP.length).trim();
  }

  return {
    statusCode: 200,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resume: resumeMd, cover_letter: coverMd }),
  };
};