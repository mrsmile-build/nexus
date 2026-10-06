import os, sys, json, urllib.request

NEXUS_URL = "https://nexus-core-1qk0.onrender.com"
API_KEY = os.environ.get("NEXUS_API_KEY", "")
topic = "How to invoice clients professionally in Nigeria"

req = urllib.request.Request(NEXUS_URL + "/growth/seo",
    data=json.dumps({"topic": topic, "target_keyword": topic}).encode(),
    headers={"Content-Type":"application/json","X-NEXUS-Key":API_KEY}, method="POST")
try:
    with urllib.request.urlopen(req, timeout=90) as r:
        res = json.loads(r.read().decode())
        print("FULL RESPONSE:")
        print(json.dumps(res, indent=2))
except Exception as e:
    print("ERROR:", e)
