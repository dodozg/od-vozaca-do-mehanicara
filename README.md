# Od vozača do mehaničara

Praktični priručnik na hrvatskom za rad s jezičnim modelima: pokretanje, kvantizacija, fino podešavanje i dijagnostika. Namijenjen je iskusnim korisnicima AI alata koji nikad nisu sami pokrenuli model.

**Autori:** Domagoj Zoričić i Claude (Anthropic). Stanje alata i mjerenja: 4. 11. 2026.

**Knjiga:** [Od-vozaca-do-mehanicara.pdf](Od-vozaca-do-mehanicara.pdf) (193 stranice, A4)

## Sadržaj repozitorija

| Mapa ili datoteka | Što je u njoj |
|---|---|
| `poglavlja/` | Tekst knjige u Pandoc Markdownu: uvod, 19 poglavlja i dodaci A–C |
| `slike/` | Dijagrami i grafovi (SVG) |
| `prilozi/` | Podaci i skripte za vježbe te zapis mjerenja; ide uz knjigu |
| `tools/` | Gradnja knjige, stilovi, skripte za grafove i izvorni zapisi mjerenja |
| `ISPRAVCI.md` | Greške izvornog priručnika koje su u knjizi ispravljene |
| `PLAN.md`, `STIL.md`, `CINJENICE.md`, `STANJE.md` | Plan, upute za pisanje, provjerene činjenice i stanje posla |

## Gradnja

Potrebni su Pandoc, Google Chrome i Python s paketom `websocket-client`.

```bash
python tools/gradi.py --samo-html
python tools/ispisi_pdf.py Od-vozaca-do-mehanicara.pdf
```

Prva naredba stvara `build/knjiga-ispis.html` i `build/knjiga-web.html`, a druga ispisuje PDF.

## Ograničenja

Vježbe su pokrenute na laptopu bez GPU-a (i5-10210U, 16 GB). Zato QLoRA, Unsloth, Axolotl i vLLM nisu pokrenuti, a njihovi primjeri u knjizi nose oznaku "Nije pokrenuto". Uredba (EU) 2026/1744 i računalni prag iz AI Acta oslanjaju se na sekundarne izvore.
