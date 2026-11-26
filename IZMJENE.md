# Izmjene

Broj izdanja upisuje se samo ovdje: naslovnica i objava uzimaju najgornji zapis. Svako izdanje ima git oznaku (`v2026.11`) i Release s PDF-om na GitHubu, pa su stare inačice uvijek dostupne.

- **Novo izdanje** (`2026.11`, godina i mjesec): podignute inačice alata, nova mjerenja ili novi sadržaj. Zapis mora sadržavati redak `Stanje alata i mjerenja: D. M. GGGG.`
- **Ispravak** (`2026.11.1`, treći broj): ispravljene greške, a inačice i mjerenja ostaju isti. Datum stanja nasljeđuje se od prethodnog zapisa.

## 2026.12

Novo mjerenje: SmolLM3-3B na zlatnom skupu. Stanje alata i mjerenja: 26. 11. 2026. Alati su isti (llama.cpp b12110), a ostala mjerenja su od 4. 11. 2026.

- Poglavlje 12, vježba, korak 4: umjesto okvira „Nije pokrenuto” izmjereni rezultat za SmolLM3 Q8_0, Q4_K_M i Q2_K (točnost po polju 31,9 %, 33,1 % i 21,2 %, trajanje 712 s, 350 s i 324 s) i usporedba s PPL-om i KLD-om istih datoteka. Petlja u koraku 4 sad prolazi Q2_K umjesto Q3_K_M, kao u mjerenju.
- Poglavlje 12: tekst o rezultatima više ne kaže da SmolLM3 na zlatnom skupu nije mjeren; okvir „Simptom → uzrok” opisuje zauzet port 8091.
- `mjerenja.md`: novi odjeljak za SmolLM3 u L8, s ponovljenim prolazom Q2_K i opisom neuspjelog prvog pokušaja.
- Sirovi logovi `l8_smol3_*` i CSV `tocnost_zlatni_smol3.csv` dodani u `tools/sirovo` i `prilozi/grafovi`.

## 2026.11.2

Ispravak bez promjene mjerenja, prema recenziji.

- Naslovnica: DOI (Zenodo), a uvod navodi adresu repozitorija s prilozima.
- Hrvatski navodnici „…” u cijeloj knjizi.
- Okvir „Pokrenuto u drugom obliku” za osam naredbi koje jesu izvedene, ali iz druge ljuske, kroz skriptu ili lanac skripti; „Nije pokrenuto” ostaje samo za neizvedeno.
- Popravljeni prikazi: `_0` u poglavlju 11, ispis iz poglavlja 17, upit s „pumpa” u poglavlju 13, eksponenti u poglavljima 7, 16 i 19.
- Decimalni zarezi u vježbi poglavlja 7, `×` u računima poglavlja 1 i 3, „macOS-u”, „izračunat”.
- Okviri „Nakon ovog poglavlja znaš” svi su liste; potpisi slika bez završne točke, potpis slike u poglavlju 11 navodi i brzinu.
- Naslov vježbe više ne ostaje sam na dnu stranice; sažetak poglavlja 13 kraći.

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
