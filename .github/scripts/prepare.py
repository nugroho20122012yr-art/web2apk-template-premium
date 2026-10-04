"""Menyiapkan project Android dari config yang di-commit oleh website."""
import json, os, re, shutil, subprocess, sys
from xml.sax.saxutils import escape

JAVA_KW = {"abstract","assert","boolean","break","byte","case","catch","char","class","const",
    "continue","default","do","double","else","enum","extends","final","finally","float","for",
    "goto","if","implements","import","instanceof","int","interface","long","native","new",
    "package","private","protected","public","return","short","static","strictfp","super",
    "switch","synchronized","this","throw","throws","transient","try","void","volatile","while"}

with open("config/app.json", encoding="utf-8") as f:
    cfg = json.load(f)

name = str(cfg.get("appName", "Web App")).strip()[:50] or "Web App"
pkg = str(cfg.get("packageName", "")).strip()

if not re.fullmatch(r"[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+", pkg) or any(p in JAVA_KW for p in pkg.split(".")):
    sys.exit("Package name tidak valid: %r (contoh benar: com.nama.app)" % pkg)

# 1) Nama app -> strings.xml (di-escape)
safe = escape(name).replace("'", "\\'").replace('"', '\\"')
if safe.startswith("@") or safe.startswith("?"):
    safe = "\\" + safe
with open("app/src/main/res/values/strings.xml", "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
            '    <string name="app_name">%s</string>\n</resources>\n' % safe)

# 2) Package name -> applicationId
path = "app/build.gradle"
text = open(path, encoding="utf-8").read()
text = re.sub(r'applicationId\s+".*?"', 'applicationId "%s"' % pkg, text, count=1)
open(path, "w", encoding="utf-8").write(text)

# 3) Salin www/ ke assets
for need in ("www/index.html", "www/url.txt"):
    if not os.path.exists(need):
        sys.exit("File wajib tidak ada: " + need)
shutil.copytree("www", "app/src/main/assets/www", dirs_exist_ok=True)

# 4) Icon -> semua ukuran mipmap
icon = "config/icon.png"
if not os.path.exists(icon):
    sys.exit("config/icon.png tidak ada")
im = shutil.which("magick") or shutil.which("convert")
if not im:
    sys.exit("ImageMagick tidak ditemukan")
sizes = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
for dpi, px in sizes.items():
    d = "app/src/main/res/mipmap-%s" % dpi
    os.makedirs(d, exist_ok=True)
    subprocess.check_call([im, icon, "-resize", "%dx%d^" % (px, px), "-gravity", "center",
                           "-extent", "%dx%d" % (px, px), "PNG32:%s/ic_launcher.png" % d])

print("OK -> app: %s | package: %s" % (name, pkg))
