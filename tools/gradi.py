#!/usr/bin/env python3
"""Gradi knjigu iz poglavlja/*.md: build/knjiga-ispis.html -> PDF (Chrome + Paged.js) i build/knjiga-web.html.

Pokretanje:  python tools/gradi.py [--samo-html]
"""
import html
import re
import subprocess
import sys
from pathlib import Path

KORIJEN = Path(__file__).resolve().parent.parent
POGL = KORIJEN / "poglavlja"
SLIKE = KORIJEN / "slike"
BUILD = KORIJEN / "build"
ALATI = KORIJEN / "tools"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PDF = KORIJEN / "Od-vozaca-do-mehanicara.pdf"
NASLOV = "Od vozača do mehaničara"
AUTORI = "Domagoj Zoričić i Claude (Anthropic)"
PODNASLOV = "Praktični priručnik za rad s jezičnim modelima: pokretanje, kvantizacija, fino podešavanje i dijagnostika"
FONTOVI = ("https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;600;700"
           "&family=Barlow:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600"
           "&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,650;1,8..60,400&display=swap")

DIJELOVI = {
    1: ("Dio I", "Prva vožnja i pogled pod haubu", "Pokrećeš model na svom računalu, a zatim otvaraš što se krije iza njega: datoteke, tokene, predloške i motor."),
    7: ("Dio II", "Motor, gorivo, mjere", "Brojevi, memorija i brzina. Ovdje učiš izračunati što ti treba, izabrati model i ne skinuti nešto opasno."),
    11: ("Dio III", "Štednja goriva", "Kvantizacijom model staje u manje memorije. Zatim mjeriš koliko je to koštalo."),
    13: ("Dio IV", "Preinake", "Kada se isplati mijenjati model, kako pripremiti podatke i kako izgleda trening."),
    17: ("Dio V", "Radionica i pogon", "Dva izborna poglavlja za one koji žele dalje, a zatim cijeli put od početka do kraja."),
    20: ("Dodaci", "Pri ruci", "Rječnik, šalabahter i izvori."),
}


def pandoc(md_tekst: str) -> str:
    p = subprocess.run(
        ["pandoc", "-f", "markdown+fenced_divs+pipe_tables+smart-implicit_figures+implicit_figures",
         "-t", "html5", "--wrap=none", "--mathjax"],
        input=md_tekst.encode("utf-8"), capture_output=True, check=True)
    h = p.stdout.decode("utf-8").replace("\r\n", "\n")  # pandoc na Windowsu daje CRLF
    # Redovi koda kao blokovi, bez znaka novog reda izmedu njih (inace ih Paged.js udvostruci).
    h = re.sub(r'</span>\n<span id="cb', '</span><span id="cb', h)
    # Duge tablice smiju preko stranice, kratke ostaju cijele.
    def oznaci(m):
        t = m.group(0)
        return t.replace("<table", '<table data-duga="da"', 1) if t.count("<tr") > 14 else t
    return re.sub(r"<table.*?</table>", oznaci, h, flags=re.S)


def ugradi_slike(h: str) -> str:
    """Ubacuje SVG izravno u HTML da mogu koristiti tokene boja."""
    def zamijeni(m):
        src = m.group(1)
        put = KORIJEN / src
        if src.endswith(".svg") and put.exists():
            svg = put.read_text(encoding="utf-8")
            svg = re.sub(r"<\?xml.*?\?>", "", svg).strip()
            return svg
        if not put.exists():
            print(f"  NEDOSTAJE SLIKA: {src}", file=sys.stderr)
            return f'<p class="neprovjereno">Nedostaje slika {html.escape(src)}</p>'
        return m.group(0)
    return re.sub(r'<img src="([^"]+)"[^>]*/?>', zamijeni, h)


def poglavlja():
    izlaz, stavke = [], []
    datoteke = sorted(POGL.glob("*.md"))
    uvod = [d for d in datoteke if d.name.startswith("00")]
    glavna = [d for d in datoteke if re.match(r"(0[1-9]|1\d)-", d.name)]
    dodaci = [d for d in datoteke if re.match(r"[A-C]-", d.name)]

    for d in uvod:
        h = ugradi_slike(pandoc(d.read_text(encoding="utf-8")))
        izlaz.append(f'<section class="poglavlje uvod" id="uvod">{h}</section>')
        naslov = re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S).group(1)
        stavke.append(f'<li><a href="#uvod"><span class="t-br"></span><span>{naslov}</span></a></li>')

    for d in glavna:
        br = int(d.name[:2])
        if br in DIJELOVI:
            izlaz.append(dio_html(br, stavke))
        h = ugradi_slike(pandoc(d.read_text(encoding="utf-8")))
        izlaz.append(oblikuj(h, f"p{br}", str(br), stavke))
    if dodaci:
        izlaz.append(dio_html(20, stavke))
    for d in dodaci:
        slovo = d.name[0]
        h = ugradi_slike(pandoc(d.read_text(encoding="utf-8")))
        izlaz.append(oblikuj(h, f"d{slovo}", slovo, stavke))
    return "\n".join(izlaz), "\n".join(stavke)


def dio_html(k, stavke):
    oz, nas, opis = DIJELOVI[k]
    i = f"dio{k}"
    stavke.append(f'<li class="t-dio"><a href="#{i}"><span>{oz}. {nas}</span></a></li>')
    return (f'<section class="dio" id="{i}"><p class="dio-oznaka">{oz}</p>'
            f'<h1>{nas}</h1><p class="dio-opis">{opis}</p></section>')


def oblikuj(h, ident, oznaka, stavke):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S)
    naslov = m.group(1)
    h = h.replace(m.group(0), f'<span class="broj-pogl">{oznaka}</span><h1>{naslov}</h1>', 1)
    stavke.append(f'<li><a href="#{ident}"><span class="t-br">{oznaka}</span><span>{naslov}</span></a></li>')
    return f'<section class="poglavlje" id="{ident}">{h}</section>'


def naslovnica():
    crtez = SLIKE / "naslovnica.svg"
    c = crtez.read_text(encoding="utf-8") if crtez.exists() else ""
    return (f'<section class="naslovnica"><p class="oznaka">Servisna knjižica za jezične modele</p>'
            f'<h1>Od vozača<br>do mehaničara</h1><p class="podnaslov">{PODNASLOV}</p>'
            f'<p class="autor">{AUTORI}</p>'
            f'<div class="crtez">{c}</div>'
            f'<p class="impresum">Studeni 2026. Stanje alata i mjerenja: 4. 11. 2026.</p></section>')


def sadrzaj(stavke):
    return f'<section class="sadrzaj" id="sadrzaj"><h1>Sadržaj</h1><ol>{stavke}</ol></section>'


def main():
    BUILD.mkdir(exist_ok=True)
    tijelo, stavke = poglavlja()
    css = (ALATI / "knjiga.css").read_text(encoding="utf-8")
    ispis = (ALATI / "ispis.css").read_text(encoding="utf-8")
    web = (ALATI / "web.css").read_text(encoding="utf-8")
    sredina = naslovnica() + sadrzaj(stavke) + tijelo

    (BUILD / "paged.polyfill.min.js").write_bytes((ALATI / "paged.polyfill.min.js").read_bytes())
    # Paged.js obraduje samo povezane stilove, pa ih dajemo kao datoteke.
    (BUILD / "knjiga.css").write_text(css, encoding="utf-8")
    (BUILD / "ispis.css").write_text(ispis, encoding="utf-8")
    (BUILD / "knjiga-ispis.html").write_text(
        f'<!doctype html><html lang="hr"><head><meta charset="utf-8"><title>{NASLOV}</title>'
        f'<link rel="stylesheet" href="{FONTOVI}"><link rel="stylesheet" href="knjiga.css">'
        f'<link rel="stylesheet" href="ispis.css">'
        f'<script src="paged.polyfill.min.js"></script></head><body>{sredina}</body></html>', encoding="utf-8")

    (BUILD / "knjiga-web.html").write_text(
        f'<title>{NASLOV}</title><meta name="claude:viewport-fit-sides" content="cover">'
        f'<link rel="stylesheet" href="{FONTOVI}"><style>{css}\n{web}</style>'
        f'<main class="knjiga" lang="hr">{sredina.replace(chr(0xFFFD), "&#xFFFD;")}</main>', encoding="utf-8")
    print("HTML gotov;", len(re.findall(r'class="poglavlje', tijelo)), "poglavlja")

    if "--samo-html" in sys.argv:
        return
    ulaz = (BUILD / "knjiga-ispis.html").as_uri()
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--allow-file-access-from-files",
                    "--virtual-time-budget=240000", "--run-all-compositor-stages-before-draw",
                    f"--print-to-pdf={PDF}", ulaz], check=True, timeout=600,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("PDF:", PDF, PDF.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
