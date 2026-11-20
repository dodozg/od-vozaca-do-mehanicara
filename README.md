# Od vozača do mehaničara

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24407276.svg)](https://doi.org/10.5281/zenodo.24407276)

Praktični priručnik na hrvatskom za rad s jezičnim modelima: pokretanje, kvantizacija, fino podešavanje i dijagnostika. Namijenjen je iskusnim korisnicima AI alata koji nikad nisu sami pokrenuli model.

**Autori:** Domagoj Zoričić i Claude (Anthropic)

**Knjiga:** [Od-vozaca-do-mehanicara.pdf](Od-vozaca-do-mehanicara.pdf) (A4). Trenutačno izdanje, datum stanja alata i promjene su u [IZMJENE.md](IZMJENE.md), a PDF svakog izdanja među [Releases](https://github.com/dodozg/od-vozaca-do-mehanicara/releases).

## Sadržaj repozitorija

| Mapa ili datoteka | Što je u njoj |
|---|---|
| `poglavlja/` | Tekst knjige u Pandoc Markdownu: uvod, 19 poglavlja i dodaci A–C |
| `slike/` | Dijagrami i grafovi (SVG) |
| `prilozi/` | Podaci i skripte za vježbe, točne inačice alata i zapis mjerenja; ide uz knjigu |
| `tools/` | Gradnja knjige, stilovi, skripte za grafove i izvorni zapisi mjerenja |
| `.github/workflows/` | Mjesečna provjera poveznica, modela, licenci i inačica |
| `CINJENICE.md` | Provjerene činjenice i izvori brojki |
| `IZMJENE.md` | Popis izdanja i promjena |

## Gradnja

Potrebni su Pandoc, Google Chrome i Python s paketima iz `tools/requirements.txt`.

```bash
python tools/gradi.py --samo-html
python tools/ispisi_pdf.py Od-vozaca-do-mehanicara.pdf
```

Prva naredba stvara `build/knjiga-ispis.html` i `build/knjiga-web.html`, a druga ispisuje PDF.

## Održavanje

Nova izdanja izlaze otprilike dvaput godišnje, a između njih samo ispravci. Prije izdanja:

1. Pokreni `python tools/provjeri_aktualnost.py`, koju jednom mjesečno pokreće i GitHub Actions. Stavke koje traže reakciju otvaraju Issue s oznakom `provjera-aktualnosti`.
2. Podigni inačice u `prilozi/okruzenje/`, pa pokreni vježbe i usporedbu, kako piše u `prilozi/README.md`.
3. Promijeni tekst samo gdje se rezultati stvarno razlikuju, ručno pregledaj cijene i pravila.
4. Dodaj novi zapis na vrh `IZMJENE.md`, jer se broj izdanja upisuje samo tamo. Izgradi PDF, pa potvrdi promjene i pošalji ih na GitHub.
5. Pokreni `python tools/izdaj.py`. Kad provjere prođu, `python tools/izdaj.py --objavi` stvara oznaku `vGGGG.MM` i Release s PDF-om.
6. Objavi novu web verziju iz `build/knjiga-web.html`.

## Ograničenja

Vježbe su pokrenute na laptopu bez GPU-a (i5-10210U, 16 GB). Zato QLoRA, Unsloth, Axolotl i vLLM nisu pokrenuti, a njihovi primjeri u knjizi nose oznaku "Nije pokrenuto". Uredba (EU) 2026/1744 i računalni prag iz AI Acta oslanjaju se na sekundarne izvore.

## Licenca

Knjiga (tekst u `poglavlja/`, slike u `slike/` i PDF) objavljena je pod licencom [CC BY 4.0](LICENSE): slobodno je dijeli, tiskaj i prilagođavaj uz navođenje autora. Skripte u `tools/` i `prilozi/` su pod licencom [MIT](LICENSE-KOD).

Iznimke: izvadci iz Wikipedije u `prilozi/podaci/tekst/` su pod licencom CC BY-SA 4.0 (vidi [ATRIBUCIJA.md](prilozi/podaci/tekst/ATRIBUCIJA.md)), a `tools/paged.polyfill.min.js` je Paged.js pod licencom MIT.

## Citiranje

Podaci za citiranje su u [CITATION.cff](CITATION.cff), a GitHub ih nudi preko gumba „Cite this repository”.

Knjiga je arhivirana na Zenodu: [doi.org/10.5281/zenodo.24407276](https://doi.org/10.5281/zenodo.24407276). Taj DOI uvijek vodi na najnovije izdanje, a svako izdanje ima i vlastiti DOI.
