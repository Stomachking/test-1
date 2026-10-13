# The List: AEM handoff kit

**Download the whole kit:** [the-list-aem-kit.zip](https://github.com/Stomachking/test-1/raw/main/aem-kit/the-list-aem-kit.zip) (11 MB)

**See it running inside a mock host page:**
- [Content inline, three.js from jsDelivr](https://stomachking.github.io/test-1/aem-kit/demo/index.html)
- [Content loaded from the JSON file](https://stomachking.github.io/test-1/aem-kit/demo/content-from-json.html)
- [three.js self-hosted, no CDN](https://stomachking.github.io/test-1/aem-kit/demo/self-hosted-three.html)

The List is an immersive section with three parts:

- a 3D shelf of 11 books
- a scroll-driven fly-through of 7 experiences and 3 wineries, with films that change scene as you scroll
- a My List checklist that visitors can share as an image

This kit packages it to sit **inside an AEM page, among other content**.

- Live reference: https://stomachking.github.io/test-1/
- Built from that page on 13 October 2026. Rebuild with `build_kit.py` if the page changes.

## What's in the kit

| Path | What it is |
| --- | --- |
| `dist/the-list.css` | All styles, every rule scoped under `.the-list`. Nothing applies to the host page. |
| `dist/the-list.js` | One classic script: no modules, no build step, no import map needed. |
| `dist/the-list.html` | The HTML fragment (markup plus inline content JSON), for reference or a static embed. |
| `content/the-list.json` | All content: books, places, "Picked by" credits, winery facts, film scene timings, colours. |
| `assets/covers/` | 11 book covers (used by the 3D shelf, the static catalogue and the share card). |
| `assets/media/` | Films (`.mp4`, H.264 720p, compressed for sharing) and poster stills for teamLab, National Geographic and Burgess. |
| `assets/stills/` | Small stills shown on the place cards and while films load. |
| `vendor/three@0.165.0/` | three.js r165 (MIT licence), for self-hosting instead of the public CDN. |
| `aem-starter/` | A starting point for `ui.apps`: component, author dialog, HTL and clientlib. |
| `demo/` | Three test pages that embed the kit inside a mock host page (see "Try it locally"). |

## Quick start in AEM

1. **Upload to the DAM.** Create `/content/dam/the-list/`. Upload `content/the-list.json` there, then the `covers/`, `media/` and `stills/` folders from `assets/`, keeping the folder names.
2. **Add the component.** Copy `aem-starter/ui.apps/...` into your `ui.apps` module and rename `myproject` to your app folder: in the paths, the clientlib category `myproject.the-list` and `componentGroup`. Deploy.
3. **Allow the component** in the template policy for the container where it should go.
4. **Place it on a page.** Use the dialog to set:
   - **Content JSON**: `/content/dam/the-list/the-list.json`
   - **Asset folder**: `/content/dam/the-list/`
5. **Preview** (not Edit mode). In the editor the component shows a placeholder, because the full-screen 3D and scroll effects get in the way of authoring.

The HTL in `aem-starter` outputs the markup with these attributes. If you embed it another way, this is the contract:

```html
<link rel="stylesheet" href="/etc.clientlibs/myproject/clientlibs/clientlib-the-list.css">
<div class="the-list"
     data-asset-base="/content/dam/the-list/"
     data-content-url="/content/dam/the-list/the-list.json">
  ...markup from dist/the-list.html (without the JSON <script> if you use data-content-url)...
</div>
<script src="/etc.clientlibs/myproject/clientlibs/clientlib-the-list.js"></script>
```

### Options on `.the-list`

| Attribute | Default | Use |
| --- | --- | --- |
| `data-content-url` | none | URL of the content JSON. Alternative: put the JSON inline in `<script type="application/json" class="the-list-content">` inside `.the-list`; inline wins if both exist. |
| `data-asset-base` | none | Folder the relative paths in the JSON resolve against, with a trailing slash. Absolute URLs in the JSON are left alone. |
| `data-cross-origin` | none | Set to `anonymous` only if DAM files come from a different domain (for example a CDN). That domain must send CORS headers, or WebGL and the share card can't use the covers. |
| `data-three-module` | jsDelivr | Where to load three.js from. Leave it empty to use `https://cdn.jsdelivr.net/npm/three@0.165.0/+esm`. |
| `data-three-addons` | jsDelivr | Where to load the three.js add-ons from (see self-hosting below). |

## Things to check on your AEM site

- **Dispatcher and the JSON file.** Many dispatcher configs block `.json` under `/content`. Allow just this file, for example:

  ```
  /0901 { /type "allow" /method "GET" /path "/content/dam/the-list/*" /extension "json" }
  ```

  If you'd rather not open that, render the JSON inline from a Sling Model. Read the asset's original rendition and output it inside `<script type="application/json" class="the-list-content">` with `@ context='unsafe'`. Then remove `data-content-url`.
- **Content Security Policy.** By default the kit loads:
  - three.js from `cdn.jsdelivr.net` (`script-src`)
  - the Inter font from Google Fonts (`style-src fonts.googleapis.com`, `font-src fonts.gstatic.com`)

  It also needs `img-src data: blob:` and `media-src` for the DAM. To avoid any third-party CDN, self-host three.js (next section) and the font.
- **Sticky positioning.** The shelf and the film stage use `position: sticky`. If any ancestor container has `overflow: hidden`, `overflow: auto` or a `transform`, they stop sticking. Check the layout container and column wrappers around the component.
- **Sticky site header.** The experience uses the full viewport height. A sticky or fixed site header will cover its top edge while scrolling through it. Hide or shrink the header over this section, or accept the overlap.
- **Once per page.** Element IDs (`#books`, `#experiences`, `#scene`…) are global. Put one instance of the component on a page.
- **Fonts.** Add Inter (400, 500, 600) to the page, for example in the site's head clientlib:

  ```html
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
  ```

  The serif is a system font stack, so nothing to load.

## Self-hosting three.js (no public CDN)

1. The files are in `vendor/three@0.165.0/`, and copied into the starter clientlib under `resources/three@0.165.0/`, so they're served from `/etc.clientlibs/myproject/clientlibs/clientlib-the-list/resources/three@0.165.0/`.
2. Add an import map to the page **head** (once, before any module script runs):

   ```html
   <script type="importmap">
   {
     "imports": {
       "three": "/etc.clientlibs/myproject/clientlibs/clientlib-the-list/resources/three@0.165.0/build/three.module.js",
       "three/addons/": "/etc.clientlibs/myproject/clientlibs/clientlib-the-list/resources/three@0.165.0/examples/jsm/"
     }
   }
   </script>
   ```

3. In the component dialog, set **three.js module** to `three` and **three.js add-ons** to `three/addons`. With bare attributes, that's `data-three-module="three" data-three-addons="three/addons"`.

Alternatively, if your `ui.frontend` uses webpack or Vite, install `three@0.165.0`. Then replace the two `import(...)` calls near the end of `the-list.js` with static imports.

If three.js can't load at all, for example because the CSP blocks it, the book section shows a static catalogue of all 11 books instead of the 3D shelf. The experiences and My List don't depend on three.js.

## Editing content

All content lives in `the-list.json`. Edit it and re-upload; no code release is needed.

- **Books** (`books[]`):
  - `title`, `author`, `blurb` (the one-liner) and `description`. Put `*asterisks*` around a title to set it in italics.
  - `cover`: a path under the asset folder.
  - `pickedBy`: `{ name, role, note }`. The initials badge is made from the name.
  - `palette`: the colours the page takes on for that book.
  - The 3D fields (`width`, `height`, `depth`, `seed`, `coverAspect`…) shape the rendered book. Leave them as they are.
- **Places** (`groups[]`, one per tab: Experiences, Wineries):
  - `items[]` with `title`, `kind`, `place`, `description`, `details` (label and value pairs), `pickedBy`, optional `funFact` (shown as "Did you know?") and optional `credit`.
  - Media is either:
    - `film`: `{ mp4, webm, poster, thumb, label, scenes }`. `scenes` is a list of `[from, to]` seconds, one per scroll stop. The first is the floating card; each later one zooms in and plays that window.
    - `image`: `{ src, alt }`.
    - Leave both out and the place shows a "Film to come" placeholder.

The "Picked by" names are placeholders ("Senior Leader 1" to "Senior Leader 21", "Title to come") until the real names, titles and quotes are in.

## Behaviour inside a page

- **Host page untouched.** Every style is scoped under `.the-list`. The script doesn't add page-wide classes, scroll snapping or scroll restoration.
- **Wheel smoothing.** Mouse and trackpad scrolling is smoothed only while the pointer is over The List. Scrolling over the rest of the page is native. Touch scrolling is always native.
- **Page lock.** While a book is open, or the My List panel is open, page scrolling is paused, by setting `overflow: hidden` on `<html>`. It's restored on close.
- **My List storage.** Visitors' ticks are saved in their own browser (`localStorage`, key `the-list:v1`). Nothing is sent to a server. On phones, "Share my list" opens the native share sheet with a 1080×1350 PNG; elsewhere it downloads the image.
- **Browser support.** Current Chrome, Edge, Firefox and Safari 16.2 or later. The 3D shelf needs WebGL.

## Try it locally

From the kit folder, run any static server that supports range requests, so films can seek. Then open the demo pages:

```
npx http-server -p 8080 .
# or: python3 -m http.server 8080   (films won't seek to their scenes with this one)
```

- `demo/index.html`: content inline, three.js from jsDelivr.
- `demo/content-from-json.html`: content loaded from `content/the-list.json` via `data-content-url`.
- `demo/self-hosted-three.html`: three.js from `vendor/` via an import map, so no CDN requests.

Each demo wraps The List in a mock host page (a header, intro copy, content after it and a footer), to show it doesn't affect the page around it.

## What was tested

These were tested in Chromium at desktop (1440×900) and phone (390×844) sizes, inside the mock host page:

- The host page's fonts, background and scrolling were unchanged.
- The wheel over host content wasn't intercepted.
- Media resolved from the asset folder, with no missing files.
- The 3D shelf loaded both from jsDelivr and self-hosted. A book opened with its "Picked by" credit.
- Cards jumped to the right place.
- My List opened, locked and released the page, and saved its ticks.
- The static catalogue appeared when three.js was blocked.

Not tested here: Safari, Firefox, a real AEM instance, the dispatcher and the CSP. Please check those in your environment.
