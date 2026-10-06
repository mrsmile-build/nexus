import os, sys, re, subprocess, datetime, time
sys.path.insert(0, os.path.expanduser("~/nexus"))
import publish as P

topics = [l.strip() for l in open(os.path.expanduser("~/nexus/topics.txt")) if l.strip()]
saved, failed = [], []
for t in topics:
    if os.path.exists(os.path.join(P.OUT, P.slugify(t) + ".html")):
        print("SKIP exists:", t); continue
    try:
        d = P.fetch_nexus(t).get("data", {})
        md, title = d.get("body_markdown",""), d.get("title", t)
    except Exception as e:
        print("FAIL:", t, "-", e); failed.append(t); continue
    if not md.strip():
        print("EMPTY:", t); failed.append(t); continue
    slug = P.slugify(title); path = os.path.join(P.OUT, slug + ".html")
    if os.path.exists(path):
        print("SKIP exists:", title); continue
    os.makedirs(P.OUT, exist_ok=True)
    desc = re.sub(r'<[^>]+>','', P.md_to_html(md))[:150]
    html = P.TPL.format(title=title, desc=desc, slug=slug,
        date=datetime.date.today().isoformat(), body=P.md_to_html(md))
    html = html.replace("?ref=nexus_user","").replace("?aff=nexus_user","")
    open(path,"w",encoding="utf-8").write(html)
    subprocess.run(["git","-C",P.REPO,"add",path])
    saved.append(slug); print("SAVED:", title)
    time.sleep(4)

if saved:
    sm = os.path.join(P.REPO, "public", "sitemap.xml")
    s = open(sm).read()
    add = "".join('  <url><loc>https://www.ai-business.com.ng/resources/%s</loc><changefreq>monthly</changefreq></url>\n' % x for x in saved if x not in s)
    if add:
        s = s.replace("</urlset>", add + "</urlset>")
        open(sm,"w").write(s)
        subprocess.run(["git","-C",P.REPO,"add",sm])
        print("sitemap updated with", len(saved), "urls")
print("\nDONE: %d saved, %d failed" % (len(saved), len(failed)))
for f in failed: print("  retry later:", f)
