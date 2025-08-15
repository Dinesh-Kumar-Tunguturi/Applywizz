# prune_packages.py
"""
Shrink the Vercel Serverless Function bundle by removing bulky, non-runtime
files from site-packages after pip install.

Safe for: matplotlib, numpy, lxml, Pillow, PyPDF2, Twilio, (partial) PyMuPDF.

Run this in the Build Command *after* pip install.
"""

import site, os, shutil
from pathlib import Path

def rm(p: Path):
    if not p.exists():
        return
    try:
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
            print("removed dir:", p)
        else:
            p.unlink(missing_ok=True)
            print("removed file:", p)
    except Exception as e:
        print("skip (in use?):", p, "->", e)

def keep_only(dirpath: Path, keep_names: set[str]):
    if not dirpath.exists():
        return
    for child in dirpath.iterdir():
        if child.name not in keep_names:
            rm(child)

sp = Path(site.getsitepackages()[0])
print("site-packages:", sp)

# ------- matplotlib --------
mpl = sp / "matplotlib"
if mpl.exists():
    # tests & samples
    rm(mpl / "tests")
    rm(mpl / "mpl-data" / "sample_data")
    rm(mpl / "mpl-data" / "images")

    # prune fonts: keep one core TTF
    ttf = mpl / "mpl-data" / "fonts" / "ttf"
    keep_only(ttf, {"DejaVuSans.ttf"})
    # drop other font families
    rm(mpl / "mpl-data" / "fonts" / "afm")
    rm(mpl / "mpl-data" / "fonts" / "pdfcorefonts")
    rm(mpl / "mpl-data" / "fonts" / "dejavu")  # sometimes present

# ------- numpy --------
np = sp / "numpy"
if np.exists():
    rm(np / "tests")
    rm(np / "doc")
    rm(np / "f2py" / "docs")

# ------- lxml --------
lxml = sp / "lxml"
if lxml.exists():
    rm(lxml / "tests")

# ------- Pillow (if present) --------
pil = sp / "PIL"
if pil.exists():
    rm(pil / "tests")
    rm(pil / "docs")

# ------- PyPDF2 (light already) -----
pypdf2 = sp / "PyPDF2"
if pypdf2.exists():
    rm(pypdf2 / "tests")

# ------- BeautifulSoup4 (tiny) ------
bs4 = sp / "bs4"
if bs4.exists():
    rm(bs4 / "tests")

# ------- Twilio (tiny) --------------
twilio = sp / "twilio"
if twilio.exists():
    rm(twilio / "tests")

# ------- PyMuPDF (HEAVY) ------------
# NOTE: The core binary (.so) & .libs must remain or PyMuPDF will break.
pymupdf = sp / "fitz"          # PyMuPDF exposes as 'fitz' + 'PyMuPDF' pkg meta
pymupdf_pkg = sp / "PyMuPDF"
if pymupdf_pkg.exists():
    rm(pymupdf_pkg / "tests")
    rm(pymupdf_pkg / "docs")
# Some wheels ship extra samples under 'PyMuPDF-*/examples' – best-effort:
for d in sp.glob("PyMuPDF*"):
    if d.is_dir():
        rm(d / "tests")
        rm(d / "docs")
        rm(d / "examples")

# ------- generic caches -------------
rm(sp / "__pycache__")

print("Prune step done.")
