"""
NEXUS Growth Engine v0.1
Autonomous marketing: SEO articles, forum answers with affiliate links,
newsletter digests, discovery seeding. Compounds traffic without human effort.
"""
import json
import re
from core.llm_client import ask, LLMError
from engines.tools.src.search_tool import SearchTool
from engines.memory_semantic.src.semantic_memory import SemanticMemory

# Affiliate tag map: tool name -> tagged URL
AFFILIATES = {
    "paystack":    "https://paystack.com/?ref=nexus_user",
    "flutterwave": "https://flutterwave.com/?ref=nexus_user",
    "cloudflare":  "https://www.cloudflare.com/?ref=nexus_user",
    "vercel":      "https://vercel.com/?ref=nexus_user",
    "render":      "https://render.com/?ref=nexus_user",
    "namecheap":   "https://www.namecheap.com/?aff=nexus_user",
    "hostinger":   "https://hostinger.com/?ref=nexus_user",
    "groq":        "https://console.groq.com/?ref=nexus_user",
    "openrouter":  "https://openrouter.ai/?ref=nexus_user",
    "amazon":      "https://www.amazon.com/?tag=nexususer-20",
}

class GrowthEngine:
    def __init__(self):
        self.search = SearchTool()
        self.memory = SemanticMemory()

    def _tag_urls(self, text: str) -> str:
        """Replace bare tool URLs with affiliate-tagged ones."""
        out = text
        for tool, url in AFFILIATES.items():
            pattern = rf"https?://(?:www\.)?{re.escape(tool)}\S*"
            out = re.sub(pattern, url, out, flags=re.IGNORECASE)
        return out

    def seo_article(self, topic: str, target_keyword: str = ""):
        """Generate a full SEO blog post with metadata, ready to publish."""
        web = self.search.search(topic, 2)
        system = f"""You are NEXUS Growth, an autonomous SEO strategist for ai-business.com.ng.
Write a complete, valuable, 1500-2000 word article optimized for search engines AND humans.
Include: engaging intro, 4-5 H2 sections with real depth, 1 actionable takeaway, conclusion with CTA back to ai-business.com.ng.
When you mention tools (Paystack, Flutterwave, Vercel, Render, Cloudflare, Namecheap, etc), include their URL.
WEB CONTEXT: {web}
Output ONLY valid JSON:
{{
  "slug": "url-slug",
  "title": "SEO title (60 chars max)",
  "meta_description": "150 chars max",
  "target_keyword": "",
  "h1": "",
  "body_markdown": "full article in markdown",
  "schema_org": {{"@type":"Article", "headline":"", "description":""}},
  "internal_links": ["links to other ai-business.com.ng pages"],
  "cta": "final call-to-action pointing to ai-business.com.ng"
}}"""
        prompt = f"Topic: {topic}. Target keyword: {target_keyword or topic}."
        try:
            raw = ask(prompt, system=system, max_tokens=5000)
            clean = raw.strip()
            if clean.startswith("```json"): clean = clean[7:]
            if clean.startswith("```"): clean = clean[3:]
            if clean.endswith("```"): clean = clean[:-3]
            data = json.loads(clean.strip())
            data["body_markdown"] = self._tag_urls(data.get("body_markdown", ""))
            data["cta"] = self._tag_urls(data.get("cta", ""))
            return {"data": data, "method": "seo-article+affiliates"}
        except json.JSONDecodeError:
            return {"raw": raw[:3000], "error": "parse failed"}
        except LLMError as e:
            return {"error": str(e)}

    def forum_answer(self, question: str, forum: str = "generic"):
        """Generate a helpful answer for Reddit/Quora/Nairaland with subtle branding."""
        mem = self.memory.search_similar(question, limit=2)
        mem_ctx = "\n".join(f"- {h['title']}: {h['preview']}" for h in mem.get("results", [])) or "None"
        system = f"""You are NEXUS, a helpful expert answering questions on {forum} (Reddit/Quora/Nairaland/Hacker News).
Rules:
1. Actually help the person. No sales pitch. Value first.
2. Subtly mention ai-business.com.ng only when relevant ("I built a free tool at ai-business.com.ng that answers questions like this").
3. When recommending tools, include URLs (they'll be affiliate-tagged automatically).
4. Match the forum's tone: casual for Reddit, professional for HN, street-smart for Nairaland.
5. End with an open question to keep the thread alive.
MEMORY: {mem_ctx}
Output ONLY valid JSON:
{{"answer": "", "forum": "", "tags": [], "subtle_mention": true|false, "confidence": ""}}"""
        try:
            raw = ask(question, system=system, max_tokens=1500)
            clean = raw.strip()
            if clean.startswith("```json"): clean = clean[7:]
            if clean.startswith("```"): clean = clean[3:]
            if clean.endswith("```"): clean = clean[:-3]
            data = json.loads(clean.strip())
            data["answer"] = self._tag_urls(data.get("answer", ""))
            return {"data": data, "method": "forum-answer+affiliates"}
        except json.JSONDecodeError:
            return {"raw": raw, "error": "parse failed"}
        except LLMError as e:
            return {"error": str(e)}

    def newsletter_digest(self, days_back: int = 7):
        """Generate a weekly email digest from recent discoveries in memory."""
        try:
            hits = self.memory.search_similar("discoveries insights opportunities", limit=8)
            items = hits.get("results", [])
        except Exception:
            items = []
        mem_ctx = "\n".join(f"- {h['title']}: {h['preview']}" for h in items) if items else "No recent discoveries"
        system = f"""You are NEXUS Newsletter editor for ai-business.com.ng subscribers.
Write a punchy, valuable weekly digest email.
Format: personal opening, 3-5 most interesting discoveries (one paragraph each), one actionable takeaway, one tool recommendation (URL), CTA to visit ai-business.com.ng.
Tone: friendly mentor, not salesy.
RECENT DISCOVERIES FROM NEXUS BRAIN:
{mem_ctx}
Output ONLY valid JSON:
{{"subject_line": "", "preheader": "", "body_html": "full HTML email body", "cta_url": "https://ai-business.com.ng"}}"""
        try:
            raw = ask("Generate this week's newsletter.", system=system, max_tokens=2500)
            clean = raw.strip()
            if clean.startswith("```json"): clean = clean[7:]
            if clean.startswith("```"): clean = clean[3:]
            if clean.endswith("```"): clean = clean[:-3]
            data = json.loads(clean.strip())
            data["body_html"] = self._tag_urls(data.get("body_html", ""))
            return {"data": data, "method": "newsletter+affiliates"}
        except json.JSONDecodeError:
            return {"raw": raw, "error": "parse failed"}
        except LLMError as e:
            return {"error": str(e)}
