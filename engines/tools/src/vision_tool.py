"""
NEXUS Vision Tool v0.3 (Powered by Groq Llama 3.2 Vision)
Uses Groq's stable, ultra-fast vision API to bypass OpenRouter model rotation.
"""
import os
import json
import urllib.request
import urllib.error

class VisionTool:
    def __init__(self):
        self.api_key = os.environ.get("GROQ_API_KEY", "")
        self.url = "https://api.groq.com/openai/v1/chat/completions"
        # Groq's stable, high-performance vision model
        self.model = "llama-3.2-90b-vision-preview" 

    def see(self, image_url: str, question: str):
        if not self.api_key:
            return {"error": "No GROQ_API_KEY found for vision.", "method": "vision"}
            
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
            ],
            "temperature": 0.2
        }
        
        req = urllib.request.Request(
            self.url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "NEXUS-Vision/1.0"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return {"analysis": data["choices"][0]["message"]["content"], "method": "groq_vision"}
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            return {"error": f"Groq Vision Error {e.code}: {error_body}", "method": "vision"}
        except Exception as e:
            return {"error": str(e), "method": "vision"}
