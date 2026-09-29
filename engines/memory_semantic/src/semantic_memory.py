"""
NEXUS Semantic Memory Engine v0.5 (OpenRouter Embeddings + Qdrant REST)
"""
import os
import json
import urllib.request
import urllib.error
from datetime import datetime

class SemanticMemory:
    def __init__(self):
        self.url = os.environ.get("QDRANT_URL", "").rstrip('/')
        self.api_key = os.environ.get("QDRANT_API_KEY", "")
        self.collection_name = "nexus_discoveries"
        self._initialized = False
        
        if not self.url or not self.api_key:
            print("⚠️ SemanticMemory disabled: Missing QDRANT_URL or QDRANT_API_KEY")

    def _ensure_collection(self):
        if self._initialized or not self.url:
            return
            
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            req = urllib.request.Request(f"{self.url}/collections/{self.collection_name}", headers=headers)
            urllib.request.urlopen(req, timeout=5)
            self._initialized = True
            return
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise e
                
        body = json.dumps({
            "vectors": {"size": 768, "distance": "Cosine"},
            "on_disk_payload": True
        }).encode('utf-8')
        
        req = urllib.request.Request(
            f"{self.url}/collections/{self.collection_name}",
            data=body,
            headers=headers,
            method="PUT"
        )
        urllib.request.urlopen(req, timeout=10)
        self._initialized = True
        print(f"✅ Created Qdrant collection: {self.collection_name}")

    def _embed_text(self, text: str) -> list[float]:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("No OPENROUTER_API_KEY for embeddings")
            
        body = json.dumps({
            "model": "openai/text-embedding-3-small",
            "input": text[:2000],
            "dimensions": 768
        }).encode("utf-8")
        
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/embeddings",
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://nexus-core.onrender.com",
                "User-Agent": "NEXUS-Client/1.0"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["data"][0]["embedding"]
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"OPENROUTER EMBEDDING ERROR {e.code}: {e.read().decode()}") from e
    
    def store_discovery(self, title: str, content: str, metadata: dict = None):
        if not self.url:
            return {"stored": False, "error": "Qdrant not configured"}
            
        try:
            self._ensure_collection()
            vector = self._embed_text(f"{title}\n\n{content}")
            point_id = abs(hash(title + content)) % (10**18)
            
            payload = {
                "title": title,
                "content": content[:500],
                "full_content": content,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            body = json.dumps({
                "points": [{
                    "id": point_id,
                    "vector": vector,
                    "payload": payload
                }]
            }).encode('utf-8')
            
            req = urllib.request.Request(
                f"{self.url}/collections/{self.collection_name}/points",
                data=body,
                headers={"api-key": self.api_key, "Content-Type": "application/json"},
                method="PUT"
            )
            urllib.request.urlopen(req, timeout=10)
            return {"stored": True, "point_id": point_id}
        except Exception as e:
            return {"stored": False, "error": str(e)}
    
    def search_similar(self, query: str, limit: int = 3):
        if not self.url:
            return {"results": [], "error": "Qdrant not configured"}
            
        try:
            self._ensure_collection()
            vector = self._embed_text(query)
            body = json.dumps({
                "vector": vector,
                "limit": limit,
                "with_payload": True
            }).encode('utf-8')
            
            req = urllib.request.Request(
                f"{self.url}/collections/{self.collection_name}/points/search",
                data=body,
                headers={"api-key": self.api_key, "Content-Type": "application/json"},
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                
            results = []
            for hit in data.get("result", []):
                p = hit.get("payload", {})
                results.append({
                    "score": round(hit.get("score", 0), 4),
                    "title": p.get("title", ""),
                    "preview": p.get("content", "")[:200],
                    "metadata": p.get("metadata", {})
                })
            return {"results": results, "method": "semantic_search"}
        except Exception as e:
            return {"results": [], "error": str(e)}
