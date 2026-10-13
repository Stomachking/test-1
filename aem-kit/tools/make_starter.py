#!/usr/bin/env python3
"""Generate the AEM component starter (ui.apps) from the built dist files."""
import os, re, shutil, sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/aem-kit/the-list-aem-kit"
APP = "myproject"   # rename to the project's app folder
BASE = os.path.join(OUT, "aem-starter/ui.apps/src/main/content/jcr_root/apps", APP)
COMP = os.path.join(BASE, "components/the-list")
CLIB = os.path.join(BASE, "clientlibs/clientlib-the-list")
for path in [COMP, os.path.join(COMP, "_cq_dialog"), os.path.join(CLIB, "css"), os.path.join(CLIB, "js")]:
    os.makedirs(path, exist_ok=True)


def write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


# ---------------------------------------------------------------- component
write(os.path.join(COMP, ".content.xml"), """<?xml version="1.0" encoding="UTF-8"?>
<jcr:root xmlns:sling="http://sling.apache.org/jcr/sling/1.0" xmlns:cq="http://www.day.com/jcr/cq/1.0" xmlns:jcr="http://www.jcp.org/jcr/1.0"
    jcr:primaryType="cq:Component"
    jcr:title="The List"
    jcr:description="Immersive books and experiences: 3D shelf, scroll-driven films, My List."
    componentGroup="MyProject - Content"/>
""")

fragment = open(os.path.join(OUT, "dist/the-list.html"), encoding="utf-8").read()
markup = fragment[fragment.index('<div class="the-list"'):]
markup = re.sub(r'\n  <script type="application/json" class="the-list-content">.*?</script>', "", markup, count=1, flags=re.S)
inner = markup[markup.index(">") + 1:markup.rindex("</div>")]
# HTL treats ${...} as expressions; the static markup has none, but guard anyway.
if "${" in inner:
    raise SystemExit("markup contains ${ which HTL would evaluate")

htl = f"""<!--/*
  The List - HTL for the component.
  Dialog properties: assetBase, contentUrl, crossOrigin, threeModule, threeAddons.
  In the page editor a simple placeholder is shown instead of the full experience.
*/-->
<sly data-sly-use.clientlib="/libs/granite/sightly/templates/clientlib.html"></sly>
<div data-sly-test="${{wcmmode.edit}}" class="cq-placeholder" style="padding:24px;border:1px dashed #999;font:14px sans-serif">
  The List - immersive books and experiences. Preview the page to see it.
  Content: ${{properties.contentUrl || '/content/dam/the-list/the-list.json'}}
</div>
<sly data-sly-test="${{!wcmmode.edit}}">
<sly data-sly-call="${{clientlib.css @ categories='{APP}.the-list'}}"></sly>
<div class="the-list"
     data-asset-base="${{properties.assetBase || '/content/dam/the-list/' @ context='uri'}}"
     data-content-url="${{properties.contentUrl || '/content/dam/the-list/the-list.json' @ context='uri'}}"
     data-cross-origin="${{properties.crossOrigin @ context='attribute'}}"
     data-three-module="${{properties.threeModule @ context='attribute'}}"
     data-three-addons="${{properties.threeAddons @ context='attribute'}}">{inner}</div>
<sly data-sly-call="${{clientlib.js @ categories='{APP}.the-list'}}"></sly>
</sly>
"""
write(os.path.join(COMP, "the-list.html"), htl)

write(os.path.join(COMP, "_cq_dialog/.content.xml"), """<?xml version="1.0" encoding="UTF-8"?>
<jcr:root xmlns:sling="http://sling.apache.org/jcr/sling/1.0" xmlns:granite="http://www.adobe.com/jcr/granite/1.0" xmlns:cq="http://www.day.com/jcr/cq/1.0" xmlns:jcr="http://www.jcp.org/jcr/1.0" xmlns:nt="http://www.jcp.org/jcr/nt/1.0"
    jcr:primaryType="nt:unstructured"
    jcr:title="The List"
    sling:resourceType="cq/gui/components/authoring/dialog">
    <content jcr:primaryType="nt:unstructured" sling:resourceType="granite/ui/components/coral/foundation/container">
        <items jcr:primaryType="nt:unstructured">
            <contentUrl jcr:primaryType="nt:unstructured"
                sling:resourceType="granite/ui/components/coral/foundation/form/pathfield"
                fieldLabel="Content JSON"
                fieldDescription="The the-list.json file in the DAM (books, places, Picked by credits)."
                rootPath="/content/dam"
                name="./contentUrl"/>
            <assetBase jcr:primaryType="nt:unstructured"
                sling:resourceType="granite/ui/components/coral/foundation/form/pathfield"
                fieldLabel="Asset folder"
                fieldDescription="DAM folder holding covers/, media/ and stills/. Paths in the JSON are relative to it."
                rootPath="/content/dam"
                name="./assetBase"/>
            <crossOrigin jcr:primaryType="nt:unstructured"
                sling:resourceType="granite/ui/components/coral/foundation/form/select"
                fieldLabel="Assets on another domain"
                fieldDescription="Choose 'anonymous' only if DAM files are served from a different domain that sends CORS headers."
                name="./crossOrigin">
                <items jcr:primaryType="nt:unstructured">
                    <same jcr:primaryType="nt:unstructured" text="No (same domain)" value=""/>
                    <anon jcr:primaryType="nt:unstructured" text="anonymous" value="anonymous"/>
                </items>
            </crossOrigin>
            <threeModule jcr:primaryType="nt:unstructured"
                sling:resourceType="granite/ui/components/coral/foundation/form/textfield"
                fieldLabel="three.js module (advanced)"
                fieldDescription="Leave empty to load three.js 0.165 from jsDelivr. Set to 'three' when the page has an import map (see README)."
                name="./threeModule"/>
            <threeAddons jcr:primaryType="nt:unstructured"
                sling:resourceType="granite/ui/components/coral/foundation/form/textfield"
                fieldLabel="three.js add-ons (advanced)"
                fieldDescription="Leave empty for jsDelivr. Set to 'three/addons' with the import map."
                name="./threeAddons"/>
        </items>
    </content>
</jcr:root>
""")

# ---------------------------------------------------------------- clientlib
write(os.path.join(CLIB, ".content.xml"), f"""<?xml version="1.0" encoding="UTF-8"?>
<jcr:root xmlns:cq="http://www.day.com/jcr/cq/1.0" xmlns:jcr="http://www.jcp.org/jcr/1.0"
    jcr:primaryType="cq:ClientLibraryFolder"
    allowProxy="{{Boolean}}true"
    categories="[{APP}.the-list]"/>
""")
write(os.path.join(CLIB, "css.txt"), "#base=css\nthe-list.css\n")
write(os.path.join(CLIB, "js.txt"), "#base=js\nthe-list.js\n")
shutil.copy2(os.path.join(OUT, "dist/the-list.css"), os.path.join(CLIB, "css/the-list.css"))
shutil.copy2(os.path.join(OUT, "dist/the-list.js"), os.path.join(CLIB, "js/the-list.js"))
vendor = os.path.join(OUT, "vendor/three@0.165.0")
if os.path.isdir(vendor):
    dest = os.path.join(CLIB, "resources/three@0.165.0")
    shutil.copytree(vendor, dest, dirs_exist_ok=True)
print("starter written:", os.path.relpath(BASE, OUT))
