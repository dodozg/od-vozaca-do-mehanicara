# Crta slike/naslovnica.svg: presjek motora koji se udesno raspada u mrezu brojeva.
# Samo standardna biblioteka. Pokretanje: python tools/crtaj_naslovnicu.py
# Sve boje su tokeni iz knjiga.css; nasumicnost ima stalan seed, pa je izlaz uvijek isti.
import math
import pathlib
import random

W, H = 595, 330
CELIJA_W, CELIJA_H = 33, 15          # mreza brojeva
POCETAK, PUNO = 235, 440             # x gdje raspad pocinje i gdje je potpun
DNO_LIJEVO = 278                     # ispod ovoga lijevo ide impresum, pa nema crteza
rnd = random.Random(1907)


def udio(x):
    """Koliko je celija na polozaju x vec postala broj (0 do 1)."""
    t = max(0.0, min(1.0, (x - POCETAK) / (PUNO - POCETAK)))
    return t * t * (3 - 2 * t)


stupaca = W // CELIJA_W + 1
redaka = H // CELIJA_H + 1
digit = {}
for s in range(stupaca):
    for r in range(redaka):
        digit[(s, r)] = rnd.random() < udio((s + 0.5) * CELIJA_W)


def celija(x, y):
    return int(x // CELIJA_W), int(y // CELIJA_H)


# Geometrija: svaka crta je popis tocaka, razvrstana po debljini.
crte = {"debela": [], "srednja": [], "tanka": []}


def crta(vrsta, *tocke):
    crte[vrsta].append(list(tocke))


def luk(vrsta, cx, cy, r, a0=0, a1=360, korak=8):
    n = max(3, int(abs(a1 - a0) / korak))
    crta(vrsta, *[(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                   cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)])


def pravokutnik(vrsta, x0, y0, x1, y1):
    crta(vrsta, (x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0))


PROVRT = 43     # polovica provrta
RAZMAK = 118    # razmak cilindara
CENTRI = [62 + RAZMAK * i for i in range(5)]
VRH_POKLOPCA, VRH_GLAVE, DNO_GLAVE = 6, 42, 84
KOLJENO_Y, HOD, KLIP_V, OJNICA = 216, 25, 36, 66
KUTOVI = [20, 200, 110, 290, 20]
L0, L1 = 12, CENTRI[-1] + 60

# Kuciste: glava, blok, korito
crta("debela", (L0 + 8, VRH_GLAVE), (L0 + 8, VRH_POKLOPCA), (L1, VRH_POKLOPCA))
crta("debela", (L0, VRH_GLAVE), (L1, VRH_GLAVE))
crta("debela", (L0, DNO_GLAVE), (L1, DNO_GLAVE))
crta("debela", (L0, VRH_GLAVE), (L0, 196), (L0 - 6, 202), (L0 - 6, 262), (L0 + 10, 272), (L1, 272))
crta("debela", (L0 - 6, 202), (L1, 202))

for i, cx in enumerate(CENTRI):
    k = KUTOVI[i]
    # Stijenke cilindra i rashladni kanal
    crta("debela", (cx - PROVRT, DNO_GLAVE), (cx - PROVRT, 196))
    crta("debela", (cx + PROVRT, DNO_GLAVE), (cx + PROVRT, 196))
    crta("tanka", (cx - PROVRT - 6, DNO_GLAVE + 6), (cx - PROVRT - 6, 180))
    crta("tanka", (cx + PROVRT + 6, DNO_GLAVE + 6), (cx + PROVRT + 6, 180))
    crta("tanka", (cx - PROVRT - 12, DNO_GLAVE + 6), (cx - PROVRT - 12, 180))
    crta("tanka", (cx + PROVRT + 12, DNO_GLAVE + 6), (cx + PROVRT + 12, 180))

    # Komora izgaranja
    crta("srednja", (cx - PROVRT, DNO_GLAVE), (cx - 26, 72), (cx + 26, 72), (cx + PROVRT, DNO_GLAVE))

    # Ventili s oprugama i bregasto vratilo
    for znak in (-1, 1):
        vx = cx + znak * 19
        crta("srednja", (vx, 40), (vx, 73))
        crta("srednja", (vx - 13, 76), (vx + 13, 76), (vx + 3, 72), (vx - 3, 72), (vx - 13, 76))
        crta("tanka", *[(vx + (5 if j % 2 else -5), 49 + j * 3.2) for j in range(7)])
        luk("srednja", vx, 24, 8.5)
        kut = k + znak * 40
        crta("srednja", (vx - 7, 39), (vx + 7, 39), (vx + 7, 43), (vx - 7, 43), (vx - 7, 39))
        crta("srednja", (vx - 8.5 * math.sin(math.radians(kut)), 24 + 8.5 * math.cos(math.radians(kut))),
             (vx + 13 * math.cos(math.radians(kut)), 24 + 13 * math.sin(math.radians(kut))),
             (vx + 8.5 * math.sin(math.radians(kut)), 24 - 8.5 * math.cos(math.radians(kut))))
    # Svjecica
    crta("srednja", (cx, 44), (cx, 70))
    crta("tanka", (cx - 3, 46), (cx + 3, 46), (cx + 3, 60), (cx - 3, 60), (cx - 3, 46))

    # Koljenasto vratilo, ojnica i klip: polozaji iz stvarne geometrije
    a = math.radians(k)
    kx = cx + HOD * math.sin(a)
    ky = KOLJENO_Y - HOD * math.cos(a)
    py = ky - math.sqrt(OJNICA ** 2 - (kx - cx) ** 2)
    pravokutnik("debela", cx - PROVRT + 1.5, py - 24, cx + PROVRT - 1.5, py + KLIP_V - 24)
    for d in (5, 10, 15):
        crta("tanka", (cx - PROVRT + 1.5, py - 24 + d), (cx + PROVRT - 1.5, py - 24 + d))
    luk("srednja", cx, py, 5.5)

    dx, dy = kx - cx, ky - py
    d = math.hypot(dx, dy)
    nx, ny = -dy / d, dx / d
    crta("srednja", (cx + nx * 6, py + ny * 6), (kx + nx * 11, ky + ny * 11))
    crta("srednja", (cx - nx * 6, py - ny * 6), (kx - nx * 11, ky - ny * 11))
    luk("srednja", kx, ky, 12)
    luk("tanka", kx, ky, 7)

    # Ramena koljena i protuuteg, nasuprot rukavcu
    rx, ry = (kx - cx) / HOD, (ky - KOLJENO_Y) / HOD
    for z in (-1, 1):
        crta("tanka", (cx - ry * 8 * z, KOLJENO_Y + rx * 8 * z), (kx - ry * 8 * z, ky + rx * 8 * z))
    a0, a1 = k + 30, k + 150
    luk("srednja", cx, KOLJENO_Y, 31, a0, a1)
    crta("srednja", (cx + 31 * math.cos(math.radians(a0)), KOLJENO_Y + 31 * math.sin(math.radians(a0))),
         (cx + 8 * math.cos(math.radians(a0)), KOLJENO_Y + 8 * math.sin(math.radians(a0))))
    crta("srednja", (cx + 31 * math.cos(math.radians(a1)), KOLJENO_Y + 31 * math.sin(math.radians(a1))),
         (cx + 8 * math.cos(math.radians(a1)), KOLJENO_Y + 8 * math.sin(math.radians(a1))))
    luk("tanka", cx, KOLJENO_Y, 8)

# Os vratila i brojevi: rezanje crta po celijama
crta("tanka", (L0, KOLJENO_Y), (L1, KOLJENO_Y))


def izrezi(tocke, korak=2.5):
    """Rastavlja crtu na dijelove koji ne prolaze kroz celije pretvorene u broj."""
    komadi, tek = [], []
    for (x0, y0), (x1, y1) in zip(tocke, tocke[1:]):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / korak))
        for i in range(n):
            ax = x0 + (x1 - x0) * i / n
            ay = y0 + (y1 - y0) * i / n
            bx = x0 + (x1 - x0) * (i + 1) / n
            by = y0 + (y1 - y0) * (i + 1) / n
            izvan = bx >= W or digit.get(celija((ax + bx) / 2, (ay + by) / 2), True)
            if izvan:
                if len(tek) > 1:
                    komadi.append(tek)
                tek = []
            else:
                if not tek:
                    tek = [(ax, ay)]
                tek.append((bx, by))
    if len(tek) > 1:
        komadi.append(tek)
    return komadi


def stisni(tek):
    """Izbacuje tocke koje leze na istom pravcu, da datoteka ostane mala."""
    izlaz = [tek[0]]
    for i in range(1, len(tek) - 1):
        (x0, y0), (x1, y1), (x2, y2) = izlaz[-1], tek[i], tek[i + 1]
        if abs((x1 - x0) * (y2 - y0) - (y1 - y0) * (x2 - x0)) > 0.4:
            izlaz.append(tek[i])
    izlaz.append(tek[-1])
    return izlaz


def putanja(vrsta):
    d = []
    for t in crte[vrsta]:
        for komad in izrezi(t):
            k = stisni(komad)
            d.append("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in k))
    return "".join(d)


# Brojevi: tezine u hrvatskom zapisu, nasumicne ali stalne
obicni, naglaseni, blijedi = [], [], []
for (s, r), je in sorted(digit.items()):
    if not je:
        continue
    x, y = s * CELIJA_W + 3, r * CELIJA_H + 11
    if y > H - 3 or x > W - 4:
        continue
    if x < 300 and y > DNO_LIJEVO:
        continue
    v = rnd.gauss(0, 0.55)
    t = f"{'−' if v < 0 else ' '}{abs(v):.2f}".replace(".", ",").replace(" ", " ")
    z = rnd.random()
    zapis = f'<text x="{x}" y="{y}">{t}</text>'
    if z < 0.07:
        naglaseni.append(zapis)
    elif z < 0.42:
        blijedi.append(zapis)
    else:
        obicni.append(zapis)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="Tehnički crtež presjeka motora: klipovi, ojnice i koljenasto vratilo. Prema desnoj strani crtež se raspada u mrežu brojeva.">
  <g fill="none" stroke="var(--fig-a)" stroke-linecap="round" stroke-linejoin="round">
    <path stroke-width=".55" stroke="var(--fig-line)" d="{putanja('tanka')}"/>
    <path stroke-width=".8" d="{putanja('srednja')}"/>
    <path stroke-width="1.2" d="{putanja('debela')}"/>
  </g>
  <g font-family="JetBrains Mono, Consolas, monospace" font-size="8">
    <g fill="var(--fig-a)">{''.join(obicni)}</g>
    <g fill="var(--fig-line)">{''.join(blijedi)}</g>
    <g fill="var(--fig-b)" font-weight="600">{''.join(naglaseni)}</g>
  </g>
</svg>
'''
pathlib.Path(__file__).resolve().parent.parent.joinpath("slike", "naslovnica.svg").write_text(svg, encoding="utf-8")
print(f"naslovnica.svg: {len(svg)} znakova")
