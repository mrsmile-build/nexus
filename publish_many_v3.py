import os, sys, re, subprocess, datetime, time
sys.path.insert(0, os.path.expanduser("~/nexus"))
import publish as P

topics = []
for tf in ("topics.txt", "topics2.txt"):
    fp = os.path.expanduser("~/nexus/" + tf)
    if os.path.exists(fp):
        topics += [l.strip() for l in open(fp) if l.strip()]

saved, failed = [], []
for t in topics:
    if os.path.exists(os.path.join(P.OUT, P.slugify(t) + ".html")):
        continue
    md, title = None, t
    for attempt in range(2):
        try:
            d = P.fetch_nexus(t).get("data", {})
            md, title = d.get("body_markdown",""), d.get("title", t)
            if not md.strip():
                print("EMPTY:", t); md = None
            break
        except Exception as e:
            print("FAIL attempt %d:" % (attempt+1), t, "-", str(e)[:60])
            md = None
            if attempt == 0: time.sleep(15)
    if not md:
        failed.append(t); continue
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
    time.sleep(10)

if saved:
    sm = os.path.join(P.REPO, "public", "sitemap.xml")
    s = open(sm).read()
    add = "".join('  <url><loc>https://www.ai-business.com.ng/resources/%s.html</loc><changefreq>monthly</changefreq></url>\n' % x for x in saved if (x + ".html") not in s)
    if add:
        s = s.replace("</urlset>", add + "</urlset>")
        open(sm,"w").write(s)
        subprocess.run(["git","-C",P.REPO,"add",sm])
        print("sitemap +", len(saved), "urls")
print("\nDONE: %d saved, %d failed" % (len(saved), len(failed)))
for f in failed: print("  retry later:", f)
