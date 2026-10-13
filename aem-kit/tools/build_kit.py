#!/usr/bin/env python3
"""Build the AEM handoff kit for The List from the single-file landing page.

Output: the-list-aem-kit/
  dist/the-list.css         every rule scoped under .the-list
  dist/the-list.js          one classic script (no modules, no import map)
  dist/the-list.html        HTML fragment to place inside an AEM page
  content/the-list.json     books, places, credits, fun facts
  assets/                   media, covers and stills for the DAM
"""
import base64, json, os, re, shutil, subprocess, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/landing/index.html"
MEDIA = os.path.join(os.path.dirname(SRC), "media")
# Compact build: re-encoded MP4s from SMALL_MEDIA and no WebM copies.
SMALL_MEDIA = os.environ.get("SMALL_MEDIA")
DROP_WEBM = os.environ.get("DROP_WEBM") == "1"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/home/claude/aem-kit/the-list-aem-kit"

src = open(SRC, encoding="utf-8").read()


def must_replace(text, old, new, count=1, label=""):
    found = text.count(old)
    if found != count:
        raise SystemExit(f"[{label}] expected {count} match(es), found {found}: {old[:80]!r}")
    return text.replace(old, new)


# ------------------------------------------------------------------ pieces
blocks = {m.start(): (m.group(1), m.group(2), m.group(3))
          for m in re.finditer(r"<(script|style)([^>]*)>(.*?)</\1>", src, re.S)}
style = next(b for _, (t, a, b) in sorted(blocks.items()) if t == "style")
scripts = [(a.strip(), b) for _, (t, a, b) in sorted(blocks.items()) if t == "script"]


def script_starting(prefix):
    for attrs, body in scripts:
        if body.strip().startswith(prefix):
            return body
    raise SystemExit(f"script not found: {prefix}")


cover_js = script_starting("window.COVER_DATA")
module_js = next(b for a, b in scripts if 'type="module"' in a)
mylist_js = script_starting("// My List")
xp_js = next(b for a, b in scripts if "const GROUPS" in b)
smooth_js = script_starting("// Smoothed scrolling")

# ------------------------------------------------------------------ content
books_literal = module_js.split("const BOOKS = ", 1)[1].split(";\n", 1)[0]
books = json.loads(books_literal)
cover_ids = json.loads(re.search(r"const UPLOADED_COVER_DATA_IDS = (\[[^\]]*\]);", module_js).group(1))
cover_data = json.loads(cover_js.strip()[len("window.COVER_DATA = "):].rstrip().rstrip(";"))

groups_src = xp_js[xp_js.index("const GROUPS = "):xp_js.index("window.__THE_LIST = Object.assign(window.__THE_LIST || {}, { groups: GROUPS });")]
node = subprocess.run(["node", "-e", groups_src + "\nprocess.stdout.write(JSON.stringify(GROUPS));"],
                      capture_output=True, text=True, check=True)
groups = json.loads(node.stdout)

if os.path.exists(OUT):
    shutil.rmtree(OUT)
for sub in ["dist", "content", "assets/media", "assets/covers", "assets/stills"]:
    os.makedirs(os.path.join(OUT, sub), exist_ok=True)


def write_data_uri(uri, path_no_ext):
    head, data = uri.split(",", 1)
    ext = "png" if "image/png" in head else "jpg"
    path = f"{path_no_ext}.{ext}"
    with open(os.path.join(OUT, "assets", path), "wb") as fh:
        fh.write(base64.b64decode(data))
    return path


covers = {}
for key in cover_ids:
    covers[key] = write_data_uri(cover_data[key], f"covers/{key}")
for book, key in zip(books, cover_ids):
    book["coverKey"] = key
    book["cover"] = covers[key]


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


for group in groups:
    for item in group["items"]:
        for kind in ("film", "image"):
            media = item.get(kind)
            if media and isinstance(media.get("thumb"), str) and media["thumb"].startswith("data:"):
                media["thumb"] = write_data_uri(media["thumb"], f"stills/{slug(item['title'])}")

THREE_SRC = os.environ.get("THREE_SRC")
if THREE_SRC:
    vendor = os.path.join(OUT, "vendor/three@0.165.0")
    for rel in ["LICENSE", "build/three.module.js", "examples/jsm/controls/OrbitControls.js",
                "examples/jsm/environments/RoomEnvironment.js", "examples/jsm/geometries/RoundedBoxGeometry.js",
                "examples/jsm/lights/RectAreaLightUniformsLib.js"]:
        os.makedirs(os.path.dirname(os.path.join(vendor, rel)), exist_ok=True)
        shutil.copy2(os.path.join(THREE_SRC, rel), os.path.join(vendor, rel))

for name in sorted(os.listdir(MEDIA)):
    if DROP_WEBM and name.endswith(".webm"):
        continue
    source = os.path.join(SMALL_MEDIA, name) if SMALL_MEDIA and os.path.exists(os.path.join(SMALL_MEDIA, name)) else os.path.join(MEDIA, name)
    shutil.copy2(source, os.path.join(OUT, "assets/media", name))
if DROP_WEBM:
    for group in groups:
        for item in group["items"]:
            if item.get("film"):
                item["film"].pop("webm", None)

content = {
    "_comment": "Content for The List. Paths are relative to the asset base set on the .the-list element (data-asset-base).",
    "books": books,
    "groups": groups,
    "covers": covers,
}
with open(os.path.join(OUT, "content/the-list.json"), "w", encoding="utf-8") as fh:
    json.dump(content, fh, ensure_ascii=False, indent=2)

# ------------------------------------------------------------------ CSS
ROOT = ".the-list"
css = re.sub(r"/\*.*?\*/", "", style, flags=re.S)
for page_rule in [
    r"html\.is-reading,\s*html\.is-reading body\s*\{[^}]*\}",
    r"html\s*\{\s*scroll-snap-type:\s*y mandatory;\s*\}",
    r"html\.is-free-scroll,\s*html\.is-reading\s*\{[^}]*\}",
    r"@media \(hover: hover\) and \(pointer: fine\)\s*\{\s*html\s*\{\s*scroll-snap-type:\s*none;\s*\}\s*\}",
    r"html\.is-mylist,\s*html\.is-mylist body\s*\{[^}]*\}",
]:
    css, n = re.subn(page_rule, "", css)
    if n != 1:
        raise SystemExit(f"page-level rule not found once: {page_rule} ({n})")


def split_top(text, sep=","):
    parts, depth, cur = [], 0, ""
    for ch in text:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == sep and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return parts


def scope_selector(sel):
    sel = sel.strip()
    if not sel:
        return sel
    if sel.startswith(":root"):
        return ROOT + sel[len(":root"):]
    if re.match(r"html\b", sel):
        out = ROOT + sel[4:]
        return re.sub(r"^(\.the-list\S*)\s+body\b", r"\1", out)
    if re.match(r"body\b", sel):
        return ROOT + sel[4:]
    return f"{ROOT} {sel}"


def scope_block(text):
    out, i, n = [], 0, len(text)
    while i < n:
        j = text.find("{", i)
        semi = text.find(";", i)
        if j == -1:
            out.append(text[i:])
            break
        if semi != -1 and semi < j and text[i:semi].strip().startswith("@"):
            out.append(text[i:semi + 1])          # @import / @charset
            i = semi + 1
            continue
        prelude = text[i:j]
        depth, k = 1, j + 1
        while depth and k < n:
            if text[k] == "{":
                depth += 1
            elif text[k] == "}":
                depth -= 1
            k += 1
        inner = text[j + 1:k - 1]
        head = prelude.strip()
        if head.startswith("@media") or head.startswith("@supports") or head.startswith("@container"):
            out.append(f"\n{head} {{{scope_block(inner)}\n}}\n")
        elif head.startswith("@"):
            out.append(f"\n{head} {{{inner}}}\n")    # @keyframes, @font-face: unchanged
        elif head:
            selectors = ",\n".join(scope_selector(s) for s in split_top(head))
            out.append(f"\n{selectors} {{{inner}}}\n")
        i = k
    return "".join(out)


scoped = scope_block(css)
scoped = re.sub(r"\n\s*\n+", "\n", scoped)
css_out = f"""/*!
 * The List - scoped styles for embedding in AEM.
 * Every rule applies only inside .the-list, so the host page is untouched.
 * Fonts: Inter from Google Fonts (see README); the serif is a system font stack.
 */
{scoped}
/* Embedding: contain the experience's layers and keep its width in its box. */
.the-list {{
  position: relative;
  isolation: isolate;
  overflow-x: clip;
}}

/* The My List panel lives in a small wrapper at the end of <body> so it can
   cover the whole screen; that wrapper must not pick up the section's box styles. */
.the-list.the-list--portal {{
  position: static;
  width: 0;
  height: 0;
  min-height: 0;
  overflow: visible;
  background: none;
}}
"""
open(os.path.join(OUT, "dist/the-list.css"), "w", encoding="utf-8").write(css_out)

# ------------------------------------------------------------------ JS
SNAP_LINE = re.compile(r"^[ \t]*(?:if \([^\n]*?\) )?[\w.]+\.style\.scrollSnapType = [^;\n]*;[ \t]*\n", re.M)

# 3D shelf: a classic async function with on-demand imports instead of a module.
shelf = module_js
shelf = must_replace(shelf, 'import * as THREE from "three";\n', "", label="shelf")
for addon in ["controls/OrbitControls.js", "environments/RoomEnvironment.js",
              "geometries/RoundedBoxGeometry.js", "lights/RectAreaLightUniformsLib.js"]:
    name = re.search(rf'import \{{ (\w+) \}} from "three/addons/{re.escape(addon)}";', shelf).group(1)
    shelf = must_replace(shelf, f'import {{ {name} }} from "three/addons/{addon}";\n',
                         f'const {{ {name} }} = await TL_addon("{addon}");\n', label="shelf")
if re.search(r'^\s*import ', shelf, re.M):
    raise SystemExit("unhandled import left in shelf script")
shelf = must_replace(shelf, "const BOOKS = " + books_literal + ";",
                     "const BOOKS = window.THE_LIST_CONTENT.books;", label="shelf")
shelf = must_replace(shelf, "const rootStyle = document.documentElement.style;",
                     "const rootStyle = TL_ROOT.style;", label="shelf")
shelf = must_replace(shelf, 'document.documentElement.classList.add("is-reading");',
                     'TL_ROOT.classList.add("is-reading");\n      window.TL_lockPage("reading", true);', label="shelf")
shelf = must_replace(shelf, 'document.documentElement.classList.remove("is-reading");',
                     'TL_ROOT.classList.remove("is-reading");\n      window.TL_lockPage("reading", false);', label="shelf")
shelf = must_replace(shelf, '      if (mode !== "hero" || event.metaKey || event.ctrlKey || event.altKey) return;',
                     '      if (mode !== "hero" || event.metaKey || event.ctrlKey || event.altKey) return;\n'
                     '      if (event.target instanceof HTMLElement && event.target.closest("input, textarea, select, [contenteditable]")) return;',
                     label="shelf")
shelf = must_replace(shelf, 'const image = new Image();\n      image.decoding = "async";\n      image.src = src;',
                     'const image = new Image();\n      image.decoding = "async";\n'
                     '      if (TL_ROOT.dataset.crossOrigin) image.crossOrigin = TL_ROOT.dataset.crossOrigin;\n'
                     '      image.src = src;', label="shelf")
shelf = SNAP_LINE.sub("", shelf)
if "document.documentElement" in shelf:
    raise SystemExit("shelf still touches document.documentElement")

# My List
mylist = mylist_js
mylist = must_replace(mylist, 'document.documentElement.classList.add("is-mylist");',
                      'TL_ROOT.classList.add("is-mylist");\n        window.TL_lockPage("mylist", true);', label="mylist")
mylist = must_replace(mylist, 'document.documentElement.classList.remove("is-mylist");',
                      'TL_ROOT.classList.remove("is-mylist");\n        window.TL_lockPage("mylist", false);', label="mylist")
mylist = must_replace(mylist, "        document.body.append(panel);",
                      '        const portal = document.createElement("div");\n'
                      '        portal.className = "the-list the-list--portal";\n'
                      '        portal.append(panel);\n'
                      '        document.body.append(portal);', label="mylist")
mylist = must_replace(mylist, "          const img = new Image();\n",
                      "          const img = new Image();\n"
                      "          if (TL_ROOT.dataset.crossOrigin) img.crossOrigin = TL_ROOT.dataset.crossOrigin;\n", label="mylist")
mylist = must_replace(mylist, '      document.addEventListener("DOMContentLoaded", syncAll);',
                      '      setTimeout(syncAll, 0);', label="mylist")

# Experiences
xp = xp_js
xp = must_replace(xp, groups_src, "const GROUPS = window.THE_LIST_CONTENT.groups;\n      ", label="xp")
xp = SNAP_LINE.sub("", xp)

# Smoothed scrolling: only for wheel input over the experience itself.
smooth = smooth_js
smooth = must_replace(smooth, "      const root = document.documentElement;",
                      "      const root = document.documentElement;\n      const TLR = window.TL_ROOT;", label="smooth")
smooth = smooth.replace('root.classList.contains("is-', 'TLR.classList.contains("is-')
smooth = must_replace(smooth, "        if (!finePointer.matches || reduced.matches) return;",
                      "        if (!finePointer.matches || reduced.matches) return;\n"
                      "        // Embedded: only smooth wheel input over The List, never the host page.\n"
                      "        if (!TLR || !TLR.contains(event.target)) return;", label="smooth")
smooth = SNAP_LINE.sub("", smooth)
smooth = smooth.replace('[...document.querySelectorAll(".xp .snap-stop")]', '[...TLR.querySelectorAll(".xp .snap-stop")]')

for name, code in [("mylist", mylist), ("xp", xp), ("smooth", smooth)]:
    if "scrollSnapType" in code:
        raise SystemExit(f"{name} still sets scrollSnapType")


def indent(code, pad="  "):
    return "\n".join((pad + line) if line.strip() else line for line in code.strip("\n").split("\n"))


js_out = f"""/*!
 * The List - books and experiences, for embedding in AEM.
 * One classic script: include it once, after (or before) the .the-list markup.
 * Content comes from data-content-url (a JSON file, e.g. in the DAM) or from a
 * <script type="application/json" class="the-list-content"> inside .the-list.
 * Media paths in that JSON are resolved against data-asset-base.
 */
(function () {{
  "use strict";

  function boot() {{
    var TL_ROOT = document.querySelector(".the-list:not(.the-list--portal)");
    if (!TL_ROOT || TL_ROOT.dataset.tlBooted) return;
    TL_ROOT.dataset.tlBooted = "1";
    window.TL_ROOT = TL_ROOT;

    /* ---------------------------- content + assets ---------------------------- */
    var dataNode = TL_ROOT.querySelector("script.the-list-content");
    if (dataNode) {{
      start(JSON.parse(dataNode.textContent));
    }} else if (TL_ROOT.dataset.contentUrl) {{
      fetch(TL_ROOT.dataset.contentUrl, {{ credentials: "same-origin" }})
        .then(function (response) {{ if (!response.ok) throw new Error("HTTP " + response.status); return response.json(); }})
        .then(start)
        .catch(function (error) {{ console.error("[The List] Could not load content from " + TL_ROOT.dataset.contentUrl, error); }});
    }} else {{
      console.error("[The List] No content: add data-content-url or a <script type=\\"application/json\\" class=\\"the-list-content\\">.");
    }}
  }}

  function start(content) {{
    var TL_ROOT = window.TL_ROOT;
    var base = TL_ROOT.dataset.assetBase || "";
    if (base && !/\\/$/.test(base)) base += "/";
    var resolve = function (value) {{
      return typeof value === "string"
        && !/^(?:[a-z]+:|\\/\\/|\\/|#)/i.test(value)
        && /\\.(?:jpe?g|png|webp|gif|svg|mp4|webm|mov)(?:[?#].*)?$/i.test(value)
        ? base + value
        : value;
    }};
    var walk = function (node) {{
      if (Array.isArray(node)) return node.map(walk);
      if (node && typeof node === "object") {{
        Object.keys(node).forEach(function (key) {{ node[key] = walk(node[key]); }});
        return node;
      }}
      return resolve(node);
    }};
    walk(content);
    window.THE_LIST_CONTENT = content;
    window.COVER_DATA = content.covers || {{}};
    window.__THE_LIST = Object.assign(window.__THE_LIST || {{}}, {{
      books: content.books,
      covers: content.books.map(function (book) {{ return book.cover; }}),
      groups: content.groups
    }});

    TL_ROOT.querySelectorAll("[data-tl-src]").forEach(function (el) {{ el.setAttribute("src", resolve(el.getAttribute("data-tl-src"))); }});
    TL_ROOT.querySelectorAll("[data-tl-poster]").forEach(function (el) {{ el.setAttribute("poster", resolve(el.getAttribute("data-tl-poster"))); }});
    TL_ROOT.querySelectorAll("video").forEach(function (video) {{ if (video.querySelector("source[src]")) video.load(); }});
    TL_ROOT.querySelectorAll("img[data-cover]").forEach(function (img) {{ img.src = window.COVER_DATA[img.dataset.cover]; }});

    /* Stop the host page scrolling behind an open book or the My List panel. */
    var locks = new Set();
    var savedOverflow = "";
    window.TL_lockPage = function (key, on) {{
      var had = locks.size > 0;
      if (on) locks.add(key); else locks.delete(key);
      if (!had && locks.size) {{
        savedOverflow = document.documentElement.style.overflow;
        document.documentElement.style.overflow = "hidden";
      }} else if (had && !locks.size) {{
        document.documentElement.style.overflow = savedOverflow;
      }}
    }};

    /* -------------------------------- My List -------------------------------- */
{indent(mylist, "    ")}

    /* ------------------------------ Experiences ------------------------------ */
{indent(xp, "    ")}

    /* ---------------------------- Smoothed scrolling ---------------------------- */
{indent(smooth, "    ")}

    /* ------------------------------ 3D book shelf ------------------------------ */
    var cfg = TL_ROOT.dataset;
    var CDN = "https://cdn.jsdelivr.net/npm/three@0.165.0";
    var threeUrl = cfg.threeModule || CDN + "/+esm";
    var addonsBase = (cfg.threeAddons || CDN + "/examples/jsm").replace(/\\/$/, "");
    var addonSuffix = cfg.threeAddons ? "" : "/+esm";
    var TL_addon = function (path) {{ return import(addonsBase + "/" + path + addonSuffix); }};

    (async function () {{
      const THREE = await import(threeUrl);
{indent(shelf, "      ")}
    }})().catch(function (error) {{
      console.error("[The List] The 3D shelf could not load; showing the static catalog.", error);
      var loading = TL_ROOT.querySelector("#loading");
      var fallback = TL_ROOT.querySelector("#static-fallback");
      var status = TL_ROOT.querySelector("#fallback-status");
      if (loading) loading.hidden = true;
      if (fallback) fallback.hidden = false;
      if (status) status.textContent = "The interactive shelf could not load here. The complete catalog remains available.";
    }});
  }}

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
}})();
"""
open(os.path.join(OUT, "dist/the-list.js"), "w", encoding="utf-8").write(js_out)

# ------------------------------------------------------------------ HTML fragment
body = src[src.index("<body"):src.index("</body>")]
body = body[body.index(">") + 1:]
body = re.sub(r"\s*<script\b.*?</script>", "", body, flags=re.S)
body = must_replace(body, "<main>", "", label="html")
body = must_replace(body, "</main>", "", label="html")
if DROP_WEBM:
    body = re.sub(r'<source src="media/[^"]+\.webm" type="video/webm">', "", body)
body = re.sub(r'\b(src|poster)="(media/[^"]+)"', lambda m: f'data-tl-{m.group(1)}="{m.group(2)}"', body)
if re.search(r'(?<!data-tl-)(?:src|poster)="media/', body):
    raise SystemExit("unresolved media path in fragment")
body = "\n".join(line[2:] if line.startswith("  ") else line for line in body.strip("\n").split("\n"))

content_inline = json.dumps({"books": books, "groups": groups, "covers": covers}, ensure_ascii=False)
content_inline = content_inline.replace("</", "<\\/")
fragment = f"""<!--
  The List - HTML fragment for AEM.
  Place once on the page. Set data-asset-base to the DAM folder that holds the
  assets/ files (with a trailing slash), e.g. /content/dam/the-list/.
  The JSON block below is the content; in AEM it is usually rendered from
  content/the-list.json (see README).
-->
<div class="the-list" data-asset-base="/content/dam/the-list/">
  <script type="application/json" class="the-list-content">{content_inline}</script>
{indent(body, "  ")}
</div>
"""
open(os.path.join(OUT, "dist/the-list.html"), "w", encoding="utf-8").write(fragment)

print("books", len(books), "groups", [len(g["items"]) for g in groups], "covers", len(covers))
print("css", len(css_out), "js", len(js_out), "html", len(fragment))
