"""
NEXUS Vision Tool v0.2
Allows NEXUS to analyze images using OpenRouter's vision models.
"""
import os
import json
import urllib.request

class VisionTool:
    def __init__(self):
        self.api_key = os.environ.get("OPENROUTER_API_KEY", "")
        self.url = "https://openrouter.ai/api/v1/chat/completions"
        # Using a reliable, free vision model on OpenRouter
        self.model = "google/gemini-flash-1.5" 

    def see(self, image_url: str, question: str):
        if not self.api_key:
            return {"error": "No OpenRouter key for vision.", "method": "vision"}
            
        body = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ]
        }
        
        req = urllib.request.Request(
            self.url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://nexus-core.onrender.com",
                "X-Title": "NEXUS Vision"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return {"analysis": data["choices"][0]["message"]["content"], "method": "vision"}
        except urllib.error.HTTPError as e:
            # Capture the actual API error from OpenRouter
            error_body = e.read().decode("utf-8")
            return {"error": f"Vision API Error {e.code}: {error_body}", "method": "vision"}
        except Exception as e:
            return {"error": str(e), "method": "vision"}
