#!/usr/bin/env python3
"""Crta mjerene grafove iz tools/grafovi/*.csv u slike/. Samo standardna biblioteka.
Boje su CSS tokeni jer se SVG ugraduje u HTML (svijetli ispis i tamni web)."""
import csv
from pathlib import Path

K = Path(__file__).resolve().parent.parent
G = K / "tools" / "grafovi"
S = K / "slike"
LAB = 'font-family="Barlow, Arial, sans-serif"'
NASL = 'font-family="Barlow Condensed, Arial, sans-serif" font-weight="600"'


def br(x, d):
    return f"{x:.{d}f}".replace(".", ",")


def stupci(tip, vr, x0, sir, y0, oznaka, d, jed):
    """Vodoravni stupci, zajednicka os od nule, vrijednost uz kraj stupca."""
    mx = max(vr)
    v = 25
    o = [f'<text x="{x0}" y="{y0 - 14}" {NASL} font-size="16" fill="var(--fig-ink)">{oznaka}</text>']
    o.append(f'<line x1="{x0}" y1="{y0 - 4}" x2="{x0}" y2="{y0 + v * len(vr) - 3}" stroke="var(--fig-line)" stroke-width="1"/>')
    for i, (t, x) in enumerate(zip(tip, vr)):
        y = y0 + i * v
        w = x / mx * sir
        o.append(f'<path d="M{x0} {y}h{w - 4:.1f}a4 4 0 0 1 4 4v10a4 4 0 0 1 -4 4h-{w - 4:.1f}z" fill="var(--graf-a)"/>')
        o.append(f'<text x="{x0 + w + 6:.1f}" y="{y + 13}" {LAB} font-size="13" fill="var(--fig-ink)">{br(x, d)} {jed}</text>')
    return o


def kvant():
    vel = [r for r in csv.DictReader(open(G / "kvantizacija_velicina.csv")) if r["imatrix"] == "False"]
    brz = {r["tip"]: r for r in csv.DictReader(open(G / "kvantizacija_brzina.csv"))}
    tip = [r["tip"] for r in vel]
    gb = [int(r["bajtova"]) / 1e9 for r in vel]
    tok = [float(brz[t]["gen_tok_s"]) for t in tip]
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 212" role="img" '
         'aria-label="SmolLM3 po razini kvantizacije: veličina datoteke pada od 3,28 GB za Q8_0 do 1,25 GB za Q2_K, a brzina generiranja raste od 4,38 do 9,57 tokena u sekundi.">']
    for i, t in enumerate(tip):
        o.append(f'<text x="58" y="{46 + i * 25 + 13}" text-anchor="end" {LAB} font-size="13" fill="var(--fig-ink)">{t}</text>')
    o += stupci(tip, gb, 66, 200, 46, "Veličina datoteke", 2, "GB")
    o += stupci(tip, tok, 392, 200, 46, "Brzina generiranja", 2, "tok/s")
    o.append(f'<text x="0" y="206" {LAB} font-size="12" fill="var(--fig-muted)">Laptop i5-10210U, samo CPU. Razlike u brzini između susjednih razina mogu biti i šum mjerenja.</text>')
    o.append("</svg>")
    (S / "kvant-velicina.svg").write_text("\n".join(o), encoding="utf-8")


def linije(rows, x0, sir, y0, vis, naslov, ymax, oznaci):
    xs = [float(r["epoha"]) for r in rows]
    xm = max(xs)
    X = lambda e: x0 + e / xm * sir
    Y = lambda v: y0 + vis - v / ymax * vis
    o = [f'<text x="{x0}" y="{y0 - 12}" {NASL} font-size="16" fill="var(--fig-ink)">{naslov}</text>']
    for t in range(0, int(ymax) + 1):
        o.append(f'<line x1="{x0}" y1="{Y(t):.1f}" x2="{x0 + sir}" y2="{Y(t):.1f}" stroke="var(--fig-line)" stroke-width="{1 if t == 0 else 0.5}"/>')
        o.append(f'<text x="{x0 - 6}" y="{Y(t) + 4:.1f}" text-anchor="end" {LAB} font-size="12" fill="var(--fig-muted)">{t}</text>')
    kor = max(1, round(xm / 4))
    e = 0
    while e <= xm:
        o.append(f'<text x="{X(e):.1f}" y="{y0 + vis + 16}" text-anchor="middle" {LAB} font-size="12" fill="var(--fig-muted)">{e}</text>')
        e += kor
    o.append(f'<text x="{x0 + sir / 2}" y="{y0 + vis + 32}" text-anchor="middle" {LAB} font-size="12" fill="var(--fig-muted)">epoha</text>')
    for kljuc, boja in (("val_loss", "var(--graf-b)"), ("train_loss", "var(--graf-a)")):
        t = [(float(r["epoha"]), float(r[kljuc])) for r in rows if r[kljuc]]
        d = " ".join(f"{X(a):.1f},{Y(b):.1f}" for a, b in t)
        o.append(f'<polyline points="{d}" fill="none" stroke="{boja}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')
        a, b = t[-1]
        o.append(f'<circle cx="{X(a):.1f}" cy="{Y(b):.1f}" r="4" fill="{boja}" stroke="var(--fig-bg)" stroke-width="2"/>')
    for tekst, x, y, anchor in oznaci:
        o.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" {LAB} font-size="13" fill="var(--fig-ink)">{tekst}</text>')
    return o


def gubitak():
    gl = list(csv.DictReader(open(G / "gubitak_glavni.csv")))
    pr = list(csv.DictReader(open(G / "gubitak_prenaucen.csv")))
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 290" role="img" '
         'aria-label="Krivulje gubitka LoRA treninga. S 240 primjera nakon 5 epoha trening je 0,0374, a validacija 0,0628. S 20 primjera nakon 20 epoha trening je 0,0011, a validacija 0,5914: veliki jaz, a validacija ostaje ravna.">']
    # legenda
    o.append('<line x1="30" y1="12" x2="54" y2="12" stroke="var(--graf-a)" stroke-width="2"/>')
    o.append(f'<text x="60" y="16" {LAB} font-size="13" fill="var(--fig-ink)">trening</text>')
    o.append('<line x1="120" y1="12" x2="144" y2="12" stroke="var(--graf-b)" stroke-width="2"/>')
    o.append(f'<text x="150" y="16" {LAB} font-size="13" fill="var(--fig-ink)">validacija</text>')
    o += linije(gl, 30, 270, 62, 170, "240 primjera, 5 epoha", 3,
                [("val 0,0628", 300, 205, "end"), ("trening 0,0374", 300, 225, "end")])
    o += linije(pr, 380, 270, 62, 170, "Namjerno: 20 primjera, 20 epoha", 3,
                [("val 0,5914", 650, 185, "end"), ("trening 0,0011", 650, 225, "end")])
    o.append("</svg>")
    (S / "gubitak-krivulje.svg").write_text("\n".join(o), encoding="utf-8")


kvant()
gubitak()
print("gotovo")
