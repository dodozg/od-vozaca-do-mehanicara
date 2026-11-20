# Izmjene

Broj izdanja upisuje se samo ovdje: naslovnica i objava uzimaju najgornji zapis. Svako izdanje ima git oznaku (`v2026.11`) i Release s PDF-om na GitHubu, pa su stare inačice uvijek dostupne.

- **Novo izdanje** (`2026.11`, godina i mjesec): podignute inačice alata, nova mjerenja ili novi sadržaj. Zapis mora sadržavati redak `Stanje alata i mjerenja: D. M. GGGG.`
- **Ispravak** (`2026.11.1`, treći broj): ispravljene greške, a inačice i mjerenja ostaju isti. Datum stanja nasljeđuje se od prethodnog zapisa.

## 2026.11.1

Ispravak bez promjene mjerenja; repozitorij postaje javan i arhivira se na Zenodu.

- Licence: knjiga pod CC BY 4.0 (navedeno i na naslovnici), skripte pod MIT.
- Podaci za citiranje (`CITATION.cff`) i za Zenodo (`.zenodo.json`).
- Radne bilješke (planovi, upute za pisanje, stanje posla) više nisu dio repozitorija.

## 2026.11

Prvo dovršeno izdanje. Stanje alata i mjerenja: 4. 11. 2026. (llama.cpp b12110).

- Oznaka izdanja na naslovnici.
- Poglavlja 11 i 12 navode da su izvadci teksta iz mjerenja priloženi u `prilozi/podaci/tekst`.
- Poglavlje 17: izlaz modela sa šumom mijenja se od pokretanja do pokretanja, a `dare_ties` pada uz `HF_HUB_OFFLINE=1`.
- `prilozi/`: točne inačice alata i modela, `pokreni_vjezbe.py` za pokretanje i usporedbu CPU vježbi te mjesečna automatska provjera aktualnosti.
