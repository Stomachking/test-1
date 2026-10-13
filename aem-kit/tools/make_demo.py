import os, sys
OUT = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/aem-kit/the-list-aem-kit"
frag = open(os.path.join(OUT, "dist/the-list.html"), encoding="utf-8").read()
frag = frag.replace('data-asset-base="/content/dam/the-list/"', 'data-asset-base="../assets/"', 1)
page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>The List - embedded demo</title>
  <!-- Fonts used by The List (add to the AEM page head or a clientlib) -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../dist/the-list.css">
  <style>
    /* Stand-in for the host AEM page's own styles */
    body {{ margin: 0; font: 16px/1.6 Georgia, serif; color: #222; background: #fafaf7; }}
    .site-header {{ display: flex; justify-content: space-between; align-items: center; padding: 18px 32px; background: #fff; border-bottom: 1px solid #e3e1da; }}
    .site-header strong {{ font: 600 15px/1 Arial, sans-serif; letter-spacing: .08em; text-transform: uppercase; }}
    .site-header nav a {{ margin-left: 22px; color: #222; font: 14px Arial, sans-serif; text-decoration: none; }}
    .host-copy {{ max-width: 760px; margin: 0 auto; padding: 64px 24px; }}
    .host-copy h1 {{ font-size: 40px; line-height: 1.1; margin: 0 0 16px; }}
    .site-footer {{ padding: 48px 32px; background: #222; color: #ddd; font: 14px Arial, sans-serif; }}
  </style>
</head>
<body>
  <header class="site-header"><strong>Host site</strong><nav><a href="#">Home</a><a href="#">About</a><a href="#">Contact</a></nav></header>
  <section class="host-copy" id="host-intro">
    <h1>An AEM page with The List embedded</h1>
    <p>This copy stands in for the content an AEM page has above the component. Scroll down to reach The List, then keep going to see the page continue below it.</p>
  </section>

{frag}
  <section class="host-copy" id="host-after">
    <h2>Content after the component</h2>
    <p>The host page carries on normally after The List.</p>
  </section>
  <footer class="site-footer">Host site footer</footer>
  <script src="../dist/the-list.js"></script>
</body>
</html>
"""
os.makedirs(os.path.join(OUT, "demo"), exist_ok=True)
open(os.path.join(OUT, "demo/index.html"), "w", encoding="utf-8").write(page)
import re
fetch_frag = re.sub(r'\n  <script type="application/json" class="the-list-content">.*?</script>', '', frag, count=1, flags=re.S)
fetch_frag = fetch_frag.replace('data-asset-base="../assets/"', 'data-asset-base="../assets/" data-content-url="../content/the-list.json"', 1)
fetch_page = page.replace(frag, fetch_frag).replace("<title>The List - embedded demo</title>", "<title>The List - demo (content from JSON file)</title>")
assert fetch_page != page
open(os.path.join(OUT, "demo/content-from-json.html"), "w", encoding="utf-8").write(fetch_page)
self_page = page.replace("<title>The List - embedded demo</title>", """<title>The List - demo (self-hosted three.js)</title>
  <script type="importmap">
  {
    "imports": {
      "three": "../vendor/three@0.165.0/build/three.module.js",
      "three/addons/": "../vendor/three@0.165.0/examples/jsm/"
    }
  }
  </script>""").replace('data-asset-base="../assets/"', 'data-asset-base="../assets/" data-three-module="three" data-three-addons="three/addons"', 1)
assert self_page.count('data-three-module') == 1
open(os.path.join(OUT, "demo/self-hosted-three.html"), "w", encoding="utf-8").write(self_page)
print("demo written")
