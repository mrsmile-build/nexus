"""
NEXUS Web Search Tool v0.1
Retrieves real-world data to ground LLM reasoning in current facts.
"""
import urllib.request
import urllib.parse
import json
import os

class SearchTool:
    def __init__(self):
        # Reads the search API URL from environment (e.g., SEARCH_API_URL_1)
        self.url = os.environ.get("SEARCH_API_URL_1", "")
        
    def search(self, query, num_results=3):
        if not self.url:
            return "Search API not configured."
            
        # Construct the URL (assumes standard ?q= format or {query} placeholder)
        if "{query}" in self.url:
            req_url = self.url.replace("{query}", urllib.parse.quote(query))
        else:
            req_url = f"{self.url}?q={urllib.parse.quote(query)}"
            
        try:
            req = urllib.request.Request(req_url, headers={"User-Agent": "NEXUS-Search/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                
                # Best-effort extraction of text snippets from common API formats
                snippets = []
                results = []
                if isinstance(data, dict):
                    results = data.get("organic_results") or data.get("results") or data.get("data") or []
                elif isinstance(data, list):
                    results = data
                    
                for item in results[:num_results]:
                    if isinstance(item, dict):
                        text = item.get("snippet") or item.get("description") or item.get("title", "")
                        if text: snippets.append(text)
                        
                return "\n".join(snippets) if snippets else "No relevant search results found."
        except Exception as e:
            return f"Search failed: {str(e)}"
