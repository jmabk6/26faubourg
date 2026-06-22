#!/usr/bin/env python3
"""
Build du site Hôtel 26 Faubourg.

Usage :
    python build.py

À partir de site.html (que tu édites — voir le bloc CONFIG tout en haut du
<script>), ce script régénère :
  - index.html ............ copie déployable (références images/ relatives)
  - 26faubourg-apercu.html  version autonome (photos en base64) à ouvrir en
                            local pour vérifier le rendu
  - 26faubourg-site.zip ... archive prête pour Cloudflare Pages / GitHub Pages
                            (index.html + dossier images/)

Workflow : tu modifies une valeur dans CONFIG (prix, promo, offre, avis...) ou
tu remplaces une photo dans images/, tu enregistres, tu lances `python build.py`,
puis tu déploies le zip (ou tu pousses index.html + images/ sur ton repo).

Aucune dépendance externe : Python 3 standard suffit.
"""

import base64
import os
import re
import shutil
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "site.html")
IMG = os.path.join(ROOT, "images")
EXTS = (".jpg", ".jpeg", ".png")


def images():
    if not os.path.isdir(IMG):
        return []
    return [f for f in sorted(os.listdir(IMG)) if f.lower().endswith(EXTS)]


def main():
    if not os.path.exists(SRC):
        sys.exit("ERREUR : site.html introuvable dans " + ROOT)

    html = open(SRC, encoding="utf-8").read()

    # 1) index.html : copie déployable telle quelle (chemins images/ relatifs)
    shutil.copyfile(SRC, os.path.join(ROOT, "index.html"))

    # 2) aperçu autonome : on remplace les références locales par du base64.
    #    On ne remplace QUE les formes "images/x" et 'images/x' (avec guillemets)
    #    afin de NE PAS toucher aux URL absolues des balises Open Graph / schema.
    preview = html
    for fn in images():
        mime = "image/png" if fn.lower().endswith(".png") else "image/jpeg"
        with open(os.path.join(IMG, fn), "rb") as fh:
            data = "data:%s;base64,%s" % (mime, base64.b64encode(fh.read()).decode())
        preview = preview.replace('"images/%s"' % fn, '"%s"' % data)
        preview = preview.replace("'images/%s'" % fn, "'%s'" % data)
    with open(os.path.join(ROOT, "26faubourg-apercu.html"), "w", encoding="utf-8") as fh:
        fh.write(preview)

    # 3) zip déployable
    zpath = os.path.join(ROOT, "26faubourg-site.zip")
    if os.path.exists(zpath):
        os.remove(zpath)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(os.path.join(ROOT, "index.html"), "index.html")
        for fn in images():
            z.write(os.path.join(IMG, fn), "images/" + fn)

    # 4) contrôles rapides
    so, sc = len(re.findall(r"<section[\s>]", html)), html.count("</section>")
    leftover = re.findall(r"['\"(]images/[A-Za-z0-9_-]+\.(?:jpg|jpeg|png)", preview)
    nb_img = len(images())

    print("Build OK")
    print("  - index.html")
    print("  - 26faubourg-apercu.html  (%d photos intégrées)" % nb_img)
    print("  - 26faubourg-site.zip")
    print("  sections : %d/%d%s" % (so, sc, " OK" if so == sc else "  /!\\ DESEQUILIBRE"))
    if leftover:
        print("  /!\\ refs images non integrees dans l'apercu :", sorted(set(leftover)))


if __name__ == "__main__":
    main()
