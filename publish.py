import os, sys, json, re, subprocess, urllib.request, datetime

NEXUS_URL = "https://nexus-core-1qk0.onrender.com"
API_KEY = os.environ.get("NEXUS_API_KEY", "")
REPO = os.path.expanduser("~/ai-business")
OUT = os.path.join(REPO, "public", "resources")

def slugify(t): return re.sub(r'[^a-z0-9]+','-',t.lower()).strip('-')[:60]
def inline(s):
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    return re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', s)

def md_to_html(md):
    out, in_ul = [], False
    for line in md.split('\n'):
        s = line.strip()
        if s.startswith(('- ','* ')):
            if not in_ul: out.append('<ul>'); in_ul=True
            out.append('<li>'+inline(s[2:])+'</li>'); continue
        if in_ul: out.append('</ul>'); in_ul=False
        if s.startswith('### '): out.append('<h3>'+inline(s[4:])+'</h3>')
        elif s.startswith('## '): out.append('<h2>'+inline(s[3:])+'</h2>')
        elif s.startswith('# '): out.append('<h2>'+inline(s[2:])+'</h2>')
        elif s: out.append('<p>'+inline(s)+'</p>')
    if in_ul: out.append('</ul>')
    return '\n'.join(out)

TPL = '''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} | AI Business</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="https://www.ai-business.com.ng/resources/{slug}.html">
<style>body{{background:#0b1220;color:#e2e8f0;font-family:system-ui,sans-serif;line-height:1.7;margin:0;padding:24px 16px;max-width:720px;margin:auto}}h1{{font-size:26px}}h2,h3{{color:#f8fafc}}a{{color:#3b82f6}}.cta{{margin:32px 0;padding:16px;border:1px solid #1e293b;border-radius:12px;background:#0f172a;font-size:14px}}table{{border-collapse:collapse;width:100%;margin:16px 0}}th,td{{border:1px solid #334155;padding:8px;text-align:left}}th{{background:#0f172a}}</style>
</head><body>
<p style="font-size:12px;color:#64748b"><a href="/">AI Business</a> &rsaquo; <a href="/resources">Resources</a> &rsaquo; {date}</p>
<h1>{title}</h1>
{body}
<div class="cta"><strong>Want this handled for you?</strong> AI Business finds your leads, drafts the WhatsApp follow-ups, and remembers every enquiry so nothing falls through. <a href="/auth?signup=true">Start free</a> or <a href="/demo">try the demo</a> - no card.</div>
</body></html>'''

def fetch_nexus(topic):
    req = urllib.request.Request(NEXUS_URL + "/growth/seo",
        data=json.dumps({"topic": topic, "target_keyword": topic}).encode(),
        headers={"Content-Type":"application/json","X-NEXUS-Key":API_KEY}, method="POST")
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())

def main():
    topic = " ".join(sys.argv[1:]) or input("Topic: ")
    if not topic: return
    
    print(f"🧠 Asking NEXUS to write about: {topic}")
    try:
        res = fetch_nexus(topic)
        d = res.get("data", {})
        md = d.get("body_markdown","")
        title = d.get("title", topic)
        print(f"✅ NEXUS wrote: {title}")
        print(f"   Length: {len(md)} characters")
    except Exception as e:
        print(f"❌ NEXUS unreachable: {e}")
        return
    
    if not md or not md.strip():
        print("❌ Empty article received, aborting.")
        return
    
    print("-"*40)
    print(md[:500])
    print("-"*40)
    
    if input("Save into public/resources and stage for git? (y/n): ").strip().lower() != "y":
        print("Discarded."); return
    
    slug = slugify(title)
    path = os.path.join(OUT, slug + ".html")
    
    if os.path.exists(path):
        print(f"❌ Slug exists: {path}")
        print("   Try a different title or delete the existing file.")
        return
    
    os.makedirs(OUT, exist_ok=True)
    desc = re.sub(r'<[^>]+>','', md_to_html(md))[:150]
    
    html = TPL.format(
        title=title, 
        desc=desc, 
        slug=slug,
        date=datetime.date.today().isoformat(), 
        body=md_to_html(md)
    )
    
    html = html.replace("?ref=nexus_user","").replace("?aff=nexus_user","")
    with open(path,"w",encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ Saved: {path}")
    
    try:
        subprocess.run(["git","-C",REPO,"add",path], check=True)
        print(f'🚀 Staged for git!')
        print(f'\nNext steps:')
        print(f'  cd ~/ai-business')
        print(f'  git commit -m "Add guide: {title}"')
        print(f'  git push')
    except Exception as e:
        print(f"⚠️  Git error: {e}")
        print("   Make sure ~/ai-business is a git repo")

if __name__ == "__main__": main()
