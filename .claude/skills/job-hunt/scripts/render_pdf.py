"""Render a resume HTML file to an A4, one-page PDF with headless Edge/Chrome/Chromium.

Usage: python run.py render_pdf.py <input.html> <output.pdf> [--max-pages N]   (default 1)
Exits non-zero if the result is not A4 or runs past the page limit.
"""
import shutil
import subprocess
import sys
from pathlib import Path

from pypdf import PdfReader

CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]
ON_PATH = ["google-chrome", "chromium", "chromium-browser", "microsoft-edge", "msedge", "chrome"]


def find_browser():
    for b in CANDIDATES:
        if Path(b).exists():
            return b
    return next((shutil.which(n) for n in ON_PATH if shutil.which(n)), None)


def main():
    src, dst = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    max_pages = int(sys.argv[sys.argv.index("--max-pages") + 1]) if "--max-pages" in sys.argv else 1
    dst.parent.mkdir(parents=True, exist_ok=True)
    browser = find_browser()
    if not browser:
        sys.exit("ERROR: no Edge/Chrome/Chromium found; install one to render PDFs.")
    subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={dst}", src.as_uri()], check=True, capture_output=True, timeout=120)
    reader = PdfReader(str(dst))
    pages = len(reader.pages)
    box = reader.pages[0].mediabox
    w_mm, h_mm = float(box.width) / 72 * 25.4, float(box.height) / 72 * 25.4
    is_a4 = abs(w_mm - 210) < 2 and abs(h_mm - 297) < 2
    print(f"{dst}  pages={pages}  size={w_mm:.0f}x{h_mm:.0f}mm")
    if not is_a4:
        sys.exit("ERROR: not A4. The HTML must keep `@page { size: A4; ... }`; fix it and re-render.")
    if pages > max_pages:
        sys.exit(f"ERROR: {pages} pages, limit is {max_pages}. Trim content and re-render.")


if __name__ == "__main__":
    main()
