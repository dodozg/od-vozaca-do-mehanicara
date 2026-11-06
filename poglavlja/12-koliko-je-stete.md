# Koliko je štete

::: {.cilj}
**Nakon ovog poglavlja znaš:** što perpleksnost mjeri, kako je pročitati i kada je smiješ uspoređivati; odvojiti stvarnu štetu od mjernog šuma; što KLD dodaje i što nijedna od tih mjera ne vidi; izabrati razinu kvantizacije po pravilu, uz pomoć zlatnog skupa.
:::

Iz poglavlja 11 imaš šest razina SmolLM3, a iz poglavlja 9 zlatni skup. Manjem modelu lako je postaviti nekoliko pitanja i zaključiti da radi dobro. Taj zaključak ne vrijedi, a ovdje vidiš čime ga zamijeniti.

## Zašto razgovor vara

Probni razgovor ima četiri slabosti:

- **Malo uzoraka.** Pet pitanja ne može pokazati pad točnosti od nekoliko postotaka.
- **Glatkoća izgleda kao znanje.** Tečna rečenica s pogrešnom činjenicom čita se jednako lako kao točna.
- **Slučaj.** Uzorkovanje (sampling) iz poglavlja 6 daje različite odgovore i bez kvantizacije, pa ne znaš što je uzrok promjene.
- **Pristranost pitanja.** Obično pitaš ono što očekuješ da model zna, često na engleskom.

Razgovor zato hvata samo katastrofu. Trebaju ti dva mjerna instrumenta: perpleksnost za štetu na jeziku općenito i zlatni skup za štetu na tvom poslu.

## Perpleksnost: koliko model iznenađuje stvarni tekst

Zamisli da čitaš rečenicu i prije svake riječi pogađaš sljedeću. Iza "Stavio je ključ u" očekuješ "bravu". Riječ "juhu" te iznenadi. Model radi isto: za svaki položaj u poznatom tekstu daje vjerojatnost svakom tokenu (poglavlje 6), a nas zanima koliku je dao tokenu koji stvarno slijedi.

Perpleksnost (perplexity, PPL) to sažima u jedan broj:

```text
PPL = exp( -(1/N) · Σ ln P(token i | tokeni prije njega) )
```

Pročitaj je iznutra prema van:

1. `P` je vjerojatnost koju je model dao pravom tokenu.
2. `-ln P` je iznenađenje. Za P = 1 iznosi 0, a što je P manji, to je veće.
3. `(1/N) · Σ` je prosjek iznenađenja preko N tokena teksta.
4. `exp` vraća taj prosjek iz logaritma u običan broj.

Primjer s tri tokena čije su vjerojatnosti 0,5, 0,25 i 0,125: iznenađenja su 0,693, 1,386 i 2,079, prosjek je 1,386, a exp(1,386) = 4.

Taj broj ima jednostavno značenje. Model koji bira ravnomjerno između N mogućnosti svakom tokenu daje P = 1/N, pa mu je PPL točno N. Zato PPL čitaš kao "broj mogućnosti":

- **PPL 1**: model je pri svakom tokenu potpuno siguran i u pravu. To je donja granica.
- **PPL 20**: model je u prosjeku nesiguran kao da bira između 20 jednako vjerojatnih tokena.
- **Manje je bolje.**

Pravilo koje se najčešće krši: **PPL uspoređuješ samo unutar istog modela i na istom tekstu**, uz isti `-c`. Drugi model ima drukčiji tokenizator, dakle drukčije tokene i drukčiji N. Drugi tekst može biti jednostavno teži.

## Mjerenje

```bash
./llama/llama-perplexity -m models/smol3/SmolLM3-Q4_K_M.gguf \
  -f models/tekst/ppl_hr_krat.txt -t 4 -c 512 -b 512
```

Tekst je iz vježbe u poglavlju 11, s Wikipedije. Prolaz za F16, skraćeno:

```text
perplexity: calculating perplexity over 3 chunks, n_ctx=512,
  batch_size=512, n_seq=1
[1]15.7569,[2]17.5513,[3]19.7689,
Final estimate: PPL = 19.7689 +/- 2.18144
```

Alat reže tekst na komade duljine `-c` i nakon svakog ispisuje dosadašnji rezultat. Prema izvornom kodu ocjenjuje samo drugu polovicu svakog komada, da model uvijek ima kontekst. Tri komada od 512 tokena znače 765 ocijenjenih tokena. Prolaz je trajao 43 do 93 s.

Rezultati s laptopa i5-10210U, 16 GB, bez GPU-a, llama.cpp b12110. Rast je računat prema F16:

| Razina | PPL HR | PPL EN | Rast HR | Rast EN |
|---|---:|---:|---:|---:|
| F16 | 19,77 ± 2,18 | 7,08 ± 0,62 | | |
| Q8_0 | 19,86 ± 2,19 | 7,13 ± 0,62 | 0,5 % | 0,7 % |
| Q6_K | 20,41 ± 2,26 | 7,19 ± 0,63 | 3,2 % | 1,6 % |
| Q5_K_M | 20,43 ± 2,27 | 7,14 ± 0,62 | 3,3 % | 0,8 % |
| Q4_K_M | 21,14 ± 2,35 | 7,51 ± 0,66 | 6,9 % | 6,1 % |
| Q4_K_M, imatrix | 20,97 ± 2,31 | 7,26 ± 0,63 | 6,1 % | 2,6 % |
| Q3_K_M | 25,17 ± 2,82 | 8,19 ± 0,73 | 27,3 % | 15,7 % |
| Q3_K_M, imatrix | 23,06 ± 2,58 | 7,92 ± 0,71 | 16,7 % | 11,9 % |
| Q2_K | 58,80 ± 6,97 | 12,88 ± 1,24 | 197,4 % | 81,9 % |

To su brojke jednog stroja i jednog teksta, a svoje izmjeriš u vježbi.

### Hrvatski

Poglavlje 4 pita predviđa li model hrvatski lošije od engleskog. Na ovim tekstovima predviđa: već u F16 PPL je 19,77 prema 7,08. Omjer od 2,8 puta ipak nije čista mjera jezika jer su to dva različita teksta i tokeni različite duljine. Za tri komada trebalo je oko 5600 znakova hrvatskog i 9700 engleskog.

Glavni nalaz je u zadnjem retku. Q2_K podiže hrvatski s 19,77 na 58,80, a engleski sa 7,08 na 12,88. To je 2,97 puta prema 1,82 puta. Pošteno je usporediti prosječno iznenađenje, dakle ln PPL, jer se upravo ono u formuli zbraja: hrvatski raste za 1,09, a engleski za 0,60. **Q2_K pogađa hrvatski otprilike dvostruko jače.** Apsolutna razlika (+39,03 prema +5,80) to preuveličava.

Uzrok ovo mjerenje ne pokazuje. Posljedica je ipak jasna: test na engleskom ne govori ti koliko je štete na hrvatskom.

### Što je šum

Broj iza ± alat računa iz raspršenosti iznenađenja po tokenima, a oko 2,2 na hrvatskom velik je u odnosu na većinu razlika u tablici. Koliko se rezultat miče s tekstom, vidiš već u gornjem ispisu: isti F16 nakon prvog komada ima 15,76, a nakon trećeg 19,77. To je pomak od 4,01, a cijeli skok od F16 do Q4_K_M iznosi 1,37.

Tablicu zato čitaj ovako:

- **F16, Q8_0, Q6_K, Q5_K_M i Q4_K_M ne možeš poredati.** Ne tvrdi da je Q6_K bolji od Q5_K_M ili obrnuto.
- **Q3_K_M na hrvatskom vjerojatno je stvaran rast.** Razlika od F16 je 5,40, malo iznad zbroja dviju nesigurnosti (5,00). Na engleskom je 1,11, unutar zbroja (1,35).
- **Q2_K je šteta bez dvojbe** na oba jezika.
- **"Dvostruko" je gruba brojka.** Mjerena je na jednom modelu, s dva teksta i ± 6,97 na hrvatskom. Smjer je jasan, faktor nije.
- **imatrix samo pokazuje smjer.** U sva četiri para smanjio je PPL, najviše na Q3_K_M na hrvatskom (25,17 na 23,06), ali s kalibracijom od samo 2048 tokena, gdje autor metode preporučuje oko 50 tisuća, i uz ± veći od svih tih razlika.

Sve razine čitaju iste tokene, pa su razlike možda pouzdanije nego što ± sugerira, ali nesigurnost same razlike alat ne ispisuje.

**Kako treba mjeriti.** Isti, znatno dulji tekst za sve razine, iz spremljene datoteke, jer se Wikipedija mijenja. Ista naredba s `-f models/tekst/ppl_hr.txt` dala bi oko 16 komada, na Q4_K_M oko 4 minute (procjena, autor to nije pokrenuo). Još bolje je izmjeriti dva ili tri nezavisna teksta i gledati ostaje li poredak isti. Za engleski je među razvijateljima llama.cpp uobičajen testni dio skupa Wikitext-2 (`scripts/get-wikitext-2.sh`), a za hrvatski trebaš vlastiti tekst.

### Zašto nema tablice "gubitak po razini"

Možeš naići na tablice u kojima svaka razina ima stalan postotak gubitka i na pragove poput "rast PPL-a veći od 0,5 znači ozbiljnu štetu". Ovdje ih nema jer takve brojke ovise o modelu i tekstu.

Dokaz je u gornjoj tablici. Na istom modelu Q3_K_M ima rast od 27 % ili 16 %, ovisno o tekstu, a Q2_K 197 % ili 82 %. Prag od 0,5 proglasio bi Q6_K oštećenim na hrvatskom (+0,64), iako je ta razlika nekoliko puta manja od ±, a ne bi na engleskom (+0,11). Univerzalnih pragova nema. Možeš samo usporediti razine istog modela na svom tekstu.

## KLD: usporedba s punim modelom

Perpleksnost uspoređuje model s tekstom. Kullback–Leiblerova divergencija (KLD) uspoređuje kvantizirani model s punim. Oba dobivaju isti tekst, a mjera za svaki položaj gleda koliko se raspodjele vjerojatnosti njihovih sljedećih tokena razlikuju. Prema README-u alata, vrijednost 0 znači da su raspodjele iste.

Time težina teksta prestaje smetati, pa je KLD prirodan kandidat za gornje razine, gdje razlike u PPL-u tonu u šum. Nizak KLD ipak znači samo da kvantizirani griješi jednako kao puni. Ako je puni model slab na hrvatskom, bit će slaba i kopija.

Postupak ima dva koraka. Puni model najprije zapisuje sve svoje izlaze u datoteku, a zatim se kvantizirani model mjeri prema njoj:

```bash
./llama/llama-perplexity -m models/smol3/SmolLM3-F16.gguf \
  -f models/tekst/ppl_hr_krat.txt -t 6 -c 512 -b 512 \
  --kl-divergence-base models/smol3/baza-hr.kld
./llama/llama-perplexity -m models/smol3/SmolLM3-Q4_K_M.gguf \
  -f models/tekst/ppl_hr_krat.txt -t 6 -c 512 -b 512 \
  --kl-divergence-base models/smol3/baza-hr.kld --kl-divergence
```

Obje naredbe pokrenute su kako piše, za oba kratka teksta (3 komada od 512 tokena) i tri razine. Izmjereno na SmolLM3-3B, llama.cpp b12110:

| Razina | KLD hr | isti top-1 hr | KLD en | isti top-1 en |
|---|---:|---:|---:|---:|
| Q8_0 | 0,0035 | 95,3 % | 0,0029 | 97,3 % |
| Q4_K_M | 0,084 | 83,9 % | 0,105 | 85,4 % |
| Q2_K | 1,26 | 43,5 % | 0,95 | 60,8 % |

"Isti top-1" je udio položaja na kojima kvantizirani model i F16 biraju isti najvjerojatniji token. Čak i Q8_0 u jednom od dvadesetak položaja bira drugi token, iako mu je perpleksnost praktički jednaka F16. Greške mjerenja su male prema razlikama među razinama: za hrvatski ±0,0002, ±0,004 i ±0,045. Poredak jezika nije isti kao kod PPL-a. Na Q4_K_M je KLD veći za engleski (0,105 prema 0,084), a na Q2_K veći za hrvatski, kao i kod PPL-a. Dvije mjere ne moraju govoriti isto, pa gledaj obje.

Pazi na disk. Datoteka `.kld` za naš kratki tekst imala je 196 243 964 B (oko 196 MB) za hrvatski i isto toliko za engleski. Prema README-u alata, ta datoteka za LLaMA 3 na testnom dijelu Wikitext-2 ima 37 GiB. Za vježbu zato uzmi kratak tekst, poput ovog. Datoteku ne spremaj na sinkronizirani disk (poglavlje 10).

## Što PPL ne mjeri

Perpleksnost mjeri štetu na statistici jezika: koliko dobro model predviđa sljedeći token u enciklopedijskom tekstu. Korisnost ne mjeri. Iz nje ne doznaješ izvlači li model točan dio iz zapisnika, slijedi li sistemsku poruku i zna li činjenice. Ni KLD to ne vidi, pa ti treba drugi instrument.

## Zlatni skup po razinama

Ista skripta i isti skup iz poglavlja 9 pokreću se za svaku razinu. Prvo o tome što je stvarno mjereno:

- Po razinama je mjeren samo mali podešeni model: SmolLM2-135M s LoRA adapterom, spojen pa kvantiziran (trening je u poglavlju 16).
- Gemma 4 E2B mjerena je samo na Q4_K_M, a SmolLM3 na zlatnom skupu nije mjeren.
- PPL je mjeren na SmolLM3, a zlatni skup na SmolLM2, pa te tablice ne možeš izravno povezati.
- LoRA model u F16 izmjeren je naknadno, istom naredbom (poglavlje 16). Nepodešena baza u F16 služi kao donja granica.
- Mali model dobio je skraćenu sistemsku poruku jer je tako treniran, pa njegove postotke ne uspoređuj s Gemminih 74,4 %.

Rezultati na istom laptopu, način `shema`:

| Model i razina | Polja od 160 | Točnost | Cijeli zapisnik | Datoteka |
|---|---:|---:|---:|---:|
| LoRA F16 | 77 | 48,1 % | 5/40 | 271 MB |
| LoRA Q8_0 | 73 | 45,6 % | 5/40 | 145 MB |
| LoRA Q4_K_M | 71 | 44,4 % | 5/40 | 105 MB |
| LoRA Q2_K | 41 | 25,6 % | 0/40 | 88 MB |
| baza F16, bez LoRA-e | 27 | 16,9 % | 0/40 | |

Po poljima, od 40:

| Model i razina | uređaj | kvar | dio | hitnost |
|---|---:|---:|---:|---:|
| LoRA F16 | 21 | 20 | 20 | 16 |
| LoRA Q8_0 | 20 | 19 | 19 | 15 |
| LoRA Q4_K_M | 17 | 22 | 20 | 12 |
| LoRA Q2_K | 15 | 3 | 6 | 17 |
| baza F16, bez LoRA-e | 8 | 5 | 3 | 11 |

**Q8_0 i Q4_K_M ne razlikuješ.** Jedno polje vrijedi 0,625 boda, a razlika je 2 polja. Pojedina polja pritom idu u oba smjera (kvar +3, uređaj −3), što izgleda kao šum. Ni F16 nije daleko: 4 polja više od Q8_0.

**Q2_K šteti neravnomjerno.** Ukupan pad je 32 polja, ali `kvar` pada s 19 na 3, ispod nepodešene baze, a `dio` s 19 na 6. Odgovori se skupljaju na omiljene vrijednosti: `zamrzivač` se pojavljuje 22 puta, a `ne hladi` 19 puta u 40 odgovora. Tako izgleda kad kvantizacija pojede dio ispravka iz poglavlja 15.

**Porast `hitnosti` na 17 nije otpornost.** To polje ima tri vrijednosti, pa nasumično pogađanje daje oko 13 od 40. Baza bez ikakvog učenja ima 11.

**Valjan JSON nije točan JSON.** Svih pet redaka ima 40/40 valjanih JSON-a jer shema jamči oblik. Na Q2_K nijedan zapisnik nije u cijelosti točan. Evo prvog zapisnika iz zlatnog skupa: stroj za pranje suđa poplavio je kuhinju, guma je pukla i traži se dolazak još danas. Točno je `perilica posuđa`, `curi voda`, `brtva`, `visoka`.

```text
Q8_0 3/4 {"uredaj": "zamrzivač", "kvar": "curi voda",
          "dio": "brtva", "hitnost": "visoka"}
Q2_K 0/4 {"uredaj": "zamrzivač", "kvar": "ne hladi",
          "dio": "kompresor", "hitnost": "srednja"}
```

Odgovor na Q2_K zvuči uvjerljivo: zamrzivač ne hladi, a kompresor je kriv. U probnom razgovoru takav odgovor lako prolazi. Samo usporedba s točnim odgovorom pokazuje da nema veze sa zapisnikom.

Oba instrumenta na Q2_K pokazuju slom, a do Q4_K_M nijedan ne pokazuje razliku veću od šuma. Modeli su različiti, pa to samo pokazuje smjer. Q6_K, Q5_K_M i Q3_K_M na zlatnom skupu nisu mjereni.

## Što dobivaš za tu štetu

Iz poglavlja 11 znaš cijenu na drugoj strani vage. Na SmolLM3, s istog laptopa:

| Korak | Datoteka | Generiranje, tok/s | PPL HR |
|---|---:|---:|---:|
| Q8_0 na Q4_K_M | 3,28 na 1,92 GB | 4,38 na 7,65 | unutar šuma |
| Q4_K_M na Q3_K_M | 1,92 na 1,57 GB | 7,65 na 8,23 | +19 % |
| Q3_K_M na Q2_K | 1,57 na 1,25 GB | 8,23 na 9,57 | 2,3 puta |

Prvi korak daje 1,7 puta manju datoteku i 1,75 puta veću brzinu, a šteta se ne vidi kroz šum. Svaki sljedeći štedi oko 0,3 GB, a cijena raste naglo. Cijeli put od Q8_0 do Q2_K daje 2,6 puta manju datoteku i 2,2 puta veću brzinu, uz trostruku perpleksnost na hrvatskom.

Ni dobitak nije stalan: na malom podešenom modelu Q2_K generira samo oko 8 % brže od Q8_0 (126,6 prema 117,3 tok/s), a brzine se na ovom stroju istog dana razlikuju i do dva puta. Ako ti nedostaje memorije, prvo smanji kontekst (poglavlje 11).

## Pravilo odluke za Kvaku

**Izaberi najnižu razinu na kojoj zlatni skup ne pada izvan tolerancije.** Postupak:

1. **Odredi toleranciju prije mjerenja.** Kvaka uzima najviše 5 polja od 160 ukupno (oko 3 boda) i najviše 3 od 40 u bilo kojem polju. To je njezina odluka, bez statističkog dokaza: razlika od 5 polja već je u poglavlju 9 bila premala da bi se tumačila.
2. **Izmjeri referencu**, najvišu razinu koja stane, obično Q8_0.
3. **Silazi po razinama** i svaku uspoređuj s referencom, a ne sa susjednom. Inače se mali padovi neopaženo zbrajaju.
4. **Stani** na zadnjoj razini koja prolazi. Perpleksnost koristi kao jeftin prvi filter: razinu koja se na hrvatskom već očito raspada, kao Q2_K, ne moraš ni voditi kroz zlatni skup.
5. **Provjeri ciljeve** iz poglavlja 1: točnost ≥ 90 %, p95 ≤ 5 s, memoriju.

Primijenjeno na izmjereni LoRA niz, Q4_K_M prolazi (2 polja manje, najveći pad 3), a Q2_K ne prolazi (`kvar` −16). Možda bi prošao i Q3_K_M, ali on nije mjeren.

Prolazak znači samo da kvantizacija nije krivac, a model time ne postaje dobar. Ni Gemma sa 74,4 % ni mali model sa 45,6 % ne dosežu 90 %. Što tada, odlučuje poglavlje 13.

Kvakina tablica za Gemmu 4 E2B. Izmjeren je samo jedan redak, ostale popunjavaš sam, a gotove razine potraži u repozitoriju iz poglavlja 11:

| Razina | Točnost | Najslabije polje | p95 | Datoteka |
|---|---:|---:|---:|---:|
| Q8_0 (referenca) | | | | |
| Q6_K | | | | |
| Q5_K_M | | | | |
| Q4_K_M | 74,4 % | hitnost 26/40 | 6,7 s | 3,11 GB |
| Q3_K_M | | | | |

## Česta greška: predložak izmjeren kao kvaliteta

Perpleksnost čita sirovi tekst iz `-f`, bez predloška. Zlatni skup ide kroz `llama-server` i chat predložak iz poglavlja 5. Ako se predložak među razinama promijeni, zlatni skup će pasti, a ti ćeš pad pripisati kvantizaciji.

Do toga lako dolazi kad su razine iz različitih repozitorija ili jedna radi uz `--chat-template`, a druga bez. U poglavlju 5 pogrešan predložak dao je 3 tokena prompta umjesto 47 i tekst o Llami 2, bez ikakve greške.

Zato prije usporedbe prikaži iste poruke na obje razine (poglavlje 5) i usporedi nizove i broj tokena prompta. Pazi i na SmolLM3, čiji predložak sam upisuje datum, pa se niz mijenja iz dana u dan. Znak za uzbunu: PPL je miran, a zlatni skup se ruši već na Q8_0. Drži iste i ostale uvjete: `--no-rea`, sistemsku poruku, `--max`.

::: {.vjezba}
**Vježba: izmjeri štetu na svojim razinama** `CPU` · RAM 8 GB · disk bez novih modela · 20 min za PPL, plus zlatni skup

Radi u mapi iz poglavlja 11. Autor je mjerio na laptopu i5-10210U, 16 GB, bez GPU-a. Izmjeri svoje.

**1. Odreži kratke tekstove.** Autorove su datoteke bile upravo ovi počeci punih tekstova, a tvoji će se možda razlikovati jer se Wikipedija mijenja.

```bash
cd models/tekst
head -c 5725 ppl_hr.txt > ppl_hr_krat.txt
head -c 9720 ppl_en.txt > ppl_en_krat.txt
cd ../..
```

**2. Izmjeri svih devet datoteka na oba jezika.** Na autorovom laptopu tih 18 prolaza trajalo je ukupno oko 16 minuta.

```bash
for T in F16 Q8_0 Q6_K Q5_K_M Q4_K_M Q4_K_M-imat \
         Q3_K_M Q3_K_M-imat Q2_K; do
  for J in hr en; do
    ./llama/llama-perplexity -m models/smol3/SmolLM3-$T.gguf \
      -f models/tekst/ppl_${J}_krat.txt -t 4 -c 512 -b 512 \
      2>&1 | tee -a logovi/ppl.txt | grep 'Final estimate'
  done
done
```

::: {.neprovjereno}
Autor je iste naredbe pokrenuo kroz skriptu `prilozi/vjezbe/l6_kvantizacija.py`, a ova petlja s `tee` i `grep` nije pokrenuta u tom obliku.
:::

**3. Popuni tablicu** s ± i rastom prema F16. Koje razine ne možeš poredati? Pada li i tebi hrvatski jače na Q2_K? Izračunaj ln(Q2_K / F16) za oba jezika. U logu usporedi pomak F16 između komada `[1]`, `[2]` i `[3]` s razlikom F16 i Q4_K_M.

**4. Provuci razine kroz zlatni skup**, barem tri:

```bash
for T in Q8_0 Q4_K_M Q3_K_M; do
  python -X utf8 skripte/l8_tocnost.py \
    models/smol3/SmolLM3-$T.gguf SmolLM3-$T podaci \
    logovi/l12_$T.txt grafovi/tocnost_zlatni.csv \
    --no-rea --nacini shema
done
```

::: {.neprovjereno}
Autor SmolLM3 na zlatnom skupu nije pokrenuo, pa za ovaj korak nema izlaza ni trajanja. Gemma je za 40 zapisnika s `shema` trebala 235 s, a SmolLM3 je sporiji.
:::

**5. Odluči.** Primijeni Kvakino pravilo. Slažu li se PPL i zlatni skup?
:::

::: {.kvar}
**Simptom → uzrok**

- U razgovoru je model izgledao dobro, a na zlatnom skupu pada → razgovor hvata samo katastrofu. Vjeruj skupu.
- Valjan JSON 40/40, a nula cijelih zapisnika → shema jamči oblik, ne sadržaj. Gledaj točnost po polju i čitaj odgovore.
- Dvije se razine razlikuju za manje od ± → to nije rezultat. Uzmi dulji tekst, nemoj ih poredati.
- Niska razina dobro prolazi na engleskom, a hrvatski se raspada → šteta ovisi o jeziku. Mjeri na hrvatskom i idi razinu više.
- Drugi model ima manji PPL pa izgleda bolje → PPL se ne uspoređuje među modelima. Usporedi ih zlatnim skupom (poglavlje 9).
- PPL je miran, a zlatni skup se ruši već na visokoj razini → predložak. Usporedi prikazani niz i broj tokena prompta (poglavlje 5).
- Disk se puni pri KLD-u → bazna datoteka čuva sve izlaze modela. Uzmi kratak tekst.
:::

## Sažetak

Probni razgovor hvata samo katastrofu, pa štetu mjeriš s dva instrumenta. Perpleksnost je prosječno iznenađenje modela stvarnim tekstom, izraženo kao broj jednako vjerojatnih mogućnosti, i uspoređuješ je samo unutar istog modela na istom tekstu, jer univerzalnih pragova nema. Na SmolLM3 razine do Q4_K_M ne razlikuju se izvan šuma od oko ± 2,2, dok Q2_K hrvatski pogađa otprilike dvostruko jače od engleskog (s 19,77 na 58,80, prema 7,08 na 12,88), što je izmjereno na samo tri komada teksta. Perpleksnost i KLD (kod nas 0,0035 za Q8_0, 0,084 za Q4_K_M i 1,26 za Q2_K na hrvatskom tekstu) ne govore je li model koristan, pa razinu biraš zlatnim skupom: kod malog podešenog modela Q8_0 i Q4_K_M daju 45,6 i 44,4 %, a Q2_K 25,6 %, uvijek uz 40/40 valjanih JSON-a. Kvaka uzima najnižu razinu koja ne pada izvan unaprijed određene tolerancije prema referenci, a prije usporedbe provjerava da se predložak nije promijenio.
