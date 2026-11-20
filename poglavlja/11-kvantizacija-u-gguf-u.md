# Kvantizacija u GGUF-u

::: {.cilj}
**Nakon ovog poglavlja znaš:**

- zašto zaokruživanje na malo razina štedi memoriju i što pritom gubiš
- pročitati oznake kao Q4_K_M i IQ3_M i izračunati stvarnu veličinu modela
- što imatrix radi, a što ne radi
- sam pretvoriti model u GGUF, kvantizirati ga na šest razina i izabrati razinu
:::

Llama 3.1 8B u izvornom obliku zauzima 32,1 GB, a nakon kvantizacije 4,9 GB. Na mjernom laptopu sa 16 GB RAM-a prva brojka znači da model neće raditi, a druga da hoće. Isti broj parametara, isti slojevi, a datoteka je više od šest puta manja. U ovom poglavlju vidiš gdje je ta razlika nestala i to napraviš vlastitim rukama na modelu SmolLM3-3B.

## Ideja: malo razina u malom bloku

Zamisli fotografiju s milijunima nijansi koju treba spremiti u mali broj boja. Ako cijela slika dijeli jednu paletu od 16 boja, nebo i trava dobiju po nekoliko grubih tonova i slika postaje mrljava. Ako sliku razrežeš na pločice, svaka može imati vlastitih 16 boja. Pločica neba dobije 16 plavih tonova i razlika se jedva vidi. Kvantizacija (quantization) težina radi isto, samo što su boje brojevi.

![Šesnaest 16-bitnih težina zaokružuje se na 16 razina unutar svog bloka, a uz njih se pamte skala i pomak](slike/kvantizacija-ideja.svg)

Prati sliku redom:

1. Uzmi blok od 16 težina u FP16. To je 16 × 16 = 256 bita.
2. Pronađi najmanju i najveću vrijednost u bloku, ovdje −0,48 i 0,72.
3. Podijeli taj raspon na 16 razina. Za broj od 0 do 15 dovoljna su 4 bita.
4. Umjesto svake težine spremi broj njezine razine, a uz blok spremi skalu (0,08) i pomak (−0,48).

Pri učitavanju vrijednost se vraća računom `pomak + skala × razina`. Težina 0,26 pala je na razinu 9, što daje −0,48 + 0,08 × 9 = 0,24. Pogreška je 0,02.

Blok je malen zato što jedna neobično velika težina razvuče cijeli raspon. Kad bi cijeli tenzor imao jedan zajednički raspon, takav bi jedan broj sve male težine stjerao na istih nekoliko razina. U malom bloku šteta ostaje lokalna.

**Što dobivaš:** umjesto 256 bita spremaš 64 bita razina uz skalu i pomak. Težine su više od tri puta manje, a toliko manje treba im i memorije.

**Što gubiš:** sve razlike manje od razmaka između razina. Dvije različite težine u istoj razini postaju jedan broj i taj se podatak više ne može vratiti. Koliko to škodi, ovisi o modelu, jeziku i tekstu, pa šteta nema stalnu vrijednost po razini. Mjeriš je u poglavlju 12.

**Zašto je model usput i brži:** u poglavlju 8 vidiš da je generiranje na CPU-u ograničeno propusnošću memorije jer za svaki token treba proći kroz sve težine. Manje bajtova znači manje čekanja. U vježbi ćeš to izmjeriti.

## Kako se čita Q4_K_M

Oznaka ima tri dijela, a svaki odgovara na drugo pitanje.

**Q4** je nazivni broj bita po težini za većinu tenzora: 4 bita, dakle 16 razina.

**K** znači k-kvant (k-quant), zapis s dvije razine blokova. Tenzor se reže na natblokove (super-blocks) od 256 težina, a svaki natblok na podblokove od 16 ili 32 težine. Svaki podblok ima vlastitu skalu i pomak. Da oni ne bi pojeli uštedu, zapisani su sa samo 6 bita, a natblok čuva dva 16-bitna broja koja ih skaliraju. Račun za Q4_K, koji ima 8 podblokova po 32 težine:

```text
razine            256 × 4 bita        = 1024 bita
skale i pomaci    8 × (6 + 6) bita    =   96 bita
natblok           2 × 16 bita         =   32 bita
ukupno                                  1152 bita
1152 / 256                            = 4,5 bita po težini
```

Otud nazivnih 4,5. Slika iznad crta blok od 16 težina radi preglednosti, a načelo je isto.

**M** kaže koliko tenzora dobiva više bita od nazivnog broja. Oznake S, M i L (small, medium, large) određuju smjesu, dok veličina bloka ostaje ista. Evo kako izgleda Q4_K_M na modelu SmolLM3, iz stvarnog ispisa alata `llama-quantize`, skraćeno:

```text
token_embd.weight   converting to q6_K .. 501.00 MiB -> 205.49 MiB
blk.0.attn_q.weight converting to q4_K ..   8.00 MiB ->   2.25 MiB
blk.0.attn_v.weight converting to q6_K ..   2.00 MiB ->   0.82 MiB
blk.0.ffn_down.weight converting to q6_K .. 43.00 MiB -> 17.64 MiB
blk.0.ffn_up.weight converting to q4_K ..  43.00 MiB ->  12.09 MiB
blk.4.attn_v.weight converting to q4_K ..   2.00 MiB ->   0.56 MiB
blk.4.ffn_down.weight converting to q4_K .. 43.00 MiB -> 12.09 MiB
```

Zbroj za cijeli model iz istog loga:

- 216 tenzora ide u Q4_K.
- 37 tenzora ide u Q6_K: embedding i po 18 od 36 tenzora `attn_v` i `ffn_down`. Isti tenzor u sloju 0 dobije 6 bita, a u sloju 4 samo 4.
- 73 mala tenzora normalizacije ostaju u FP32 jer na njih po 0,008 MiB nema što štedjeti.

Zato Q4_K_M izlazi iznad 4,5 bita. S znači manje tenzora s više bita, L više, pa je Llama 3.1 8B prema README-u llama.cpp na razini Q3 redom 3,64, 4,00 i 4,30 bita po težini (bits per weight, bpw).

Q6_K i Q8_0 nemaju slovo jer svi veliki tenzori dobivaju istu preciznost. Q2_K također nema slovo, a ipak je smjesa: na SmolLM3 ima 144 tenzora Q2_K, 72 Q3_K, 36 Q4_K i embedding u Q6_K. Zastavica `--pure` isključuje takve smjese.

**`_0`** je stariji i jednostavniji zapis. Q8_0 ima blok od 32 težine po 8 bita i jednu 16-bitnu skalu, bez pomaka. To je (32 × 8 + 16) / 32 = 8,5 bita, točno ono što se mjeri. Bilo koji drugi tip s nastavkom `_0` danas rijetko susrećeš.

**IQ** je druga obitelj (i-quants), građena za vrlo malo bita: IQ1_S, IQ2_XXS do IQ2_M, IQ3_XXS do IQ3_M, IQ4_XS i IQ4_NL. Slova su opet oznake veličine. Prema izvornom kodu llama.cpp, IQ1_S, IQ2_XXS i IQ2_XS bez imatrixa ne rade: alat prekida posao s porukom da bi rezultat bio smeće. IQ tipove autor nije mjerio, pa za njih u tablici stoje samo brojke iz README-a.

| Tip | Osnovni blok | Llama 3.1 8B (README) | SmolLM3 (mjereno) |
|---|---:|---:|---:|
| IQ1_S | | 2,00 | |
| IQ2_M | | 2,93 | |
| Q2_K | 2,625 | 3,16 | 3,24 |
| IQ3_M | | 3,76 | |
| Q3_K_M | 3,4375 | 4,00 | 4,07 |
| IQ4_XS | | 4,46 | |
| Q4_K_M | 4,5 | 4,89 | 4,96 |
| Q5_K_M | 5,5 | 5,70 | 5,74 |
| Q6_K | 6,5625 | 6,56 | 6,56 |
| Q8_0 | 8,5 | 8,50 | 8,50 |
| F16 | 16 | 16,00 | 16,00 |

Sve su vrijednosti u bitovima po težini, a F16 je GGUF oznaka za FP16. Q2_K, Q3_K i Q6_K imaju 16 podblokova po 16 težina, a Q4_K i Q5_K 8 podblokova po 32.

::: {.napomena}
**Q4_K_M nije uvijek 4,9 bpw.** Izmjereno: Llama 3.1 8B 4,89 (README), Qwen3-4B 4,95, SmolLM3 4,96, Gemma 4 E2B 5,32. Udio tenzora s više bita ovisi o građi modela. Samo embedding SmolLM3 zauzima 205 od 1819 MiB. Veličinu zato čitaj iz datoteke, a oznaka ti kaže samo način zapisa.
:::

Stvarnu vrijednost vidiš u prvim retcima ispisa svakog alata llama.cpp. Za Gemmu:

```text
print_info: file size   = 2.88 GiB (5.32 BPW)
```

Veličina još nepreuzete datoteke piše na stranici modela na Hubu. Ako znaš broj parametara, bpw lako izračunaš: 8 × bajtova / parametara. Za Qwen3-4B to je 8 × 2 497 280 256 / 4,02 milijarde = 4,97, malo više od ispisanih 4,95 jer datoteka nosi i metapodatke.

## imatrix: isti bitovi, pametnije zaokruživanje

Obično zaokruživanje svaku težinu tretira jednako: pogreška od 0,02 uvijek je pogreška od 0,02. U radu modela te pogreške nisu jednake. Težina se množi s nekom aktivacijom, a to je broj koji u tenzor ulazi tijekom rada. Ako je aktivacija na tom mjestu obično velika, pogreška se pojača. Ako je gotovo nula, pogreška se jedva osjeti.

Matrica važnosti (importance matrix, imatrix) to mjeri na stvarnom tekstu:

1. Model se pušta kroz kalibracijski tekst.
2. `llama-imatrix` za svaki tenzor bilježi prosječne kvadrate aktivacija.
3. `llama-quantize` tim brojevima važe pogrešku kad bira skale i razine:

```text
F = [Sum_j (q_j - w_j) a_j]^2
```

Tu je `w_j` izvorna težina, `q_j` zaokružena, a `a_j` izmjerena aktivacija. Kvantizator radije griješi tamo gdje se to manje čuje.

Pritom nijedna težina **ne** dobiva više bita. Datoteka Q4_K_M s imatrixom na SmolLM3 ima 1 915 306 112 bajtova, a bez njega 1 915 305 888. Razlika je 224 bajta, vjerojatno metapodaci o kalibraciji. Mijenja se samo izbor razine i skale.

Iz toga slijedi da je kalibracijski tekst bitan. Model mjeri aktivacije na onome što vidi, pa imatrix izračunat samo na engleskom štiti ono što je važno za engleski. Za hrvatski sadržaj u tekst stavi hrvatski. Autor metode preporučuje oko 50 tisuća tokena. Izlaz je datoteka `imatrix.gguf`, koja vrijedi za sve razine istog modela: u vježbi ista datoteka služi i za Q4_K_M i za Q3_K_M. Tenzori `output.weight` i `token_embd.weight` po zadanom se ne važu, pa je alat učitao 252 unosa.

Vježba je radila s malo teksta: 2048 tokena (4 × 512) iz mješavine hrvatske i engleske Wikipedije, a izračun na Q8_0 trajao je 167 s. Perpleksnost (perplexity), objašnjenu u poglavlju 12, ovdje samo čitaš kao "manje je bolje":

| Razina | HR bez | HR s | EN bez | EN s |
|---|---:|---:|---:|---:|
| Q4_K_M | 21,14 | 20,97 | 7,51 | 7,26 |
| Q3_K_M | 25,17 | 23,06 | 8,19 | 7,92 |

Smjer je isti u sva četiri para, a učinak je veći na nižoj razini. Rezultat je ipak samo pokazatelj: tekst je kratak, mjereno je na tri komada od po 512 tokena, a mjerna nesigurnost (za hrvatski oko ± 2,3 do 2,8, za engleski oko ± 0,6 do 0,7) veća je od svih ovih razlika. Hrvatsku i englesku kalibraciju nismo uspoređivali zasebno, pa koliko točno jezik vrijedi moraš izmjeriti na svom modelu.

## Vježba

::: {.vjezba}
**Vježba: kvantiziraj SmolLM3 sam** `CPU` · RAM 8 GB · disk 29 GB · 30 min, plus preuzimanje

Mjereno je na laptopu s i5-10210U, 16 GB RAM-a, bez GPU-a, s llama.cpp b12110 i 4 dretve. Izmjeri svoje brojke: bit će drukčije, a za tvoj stroj vrijede samo one. Radi u mapi iz poglavlja 2, na lokalnom disku (poglavlje 10). Naredbe su za bash, na Windowsu za Git Bash. Python okruženje i kopiranje skripti opisani su u `prilozi/README.md`. Disk: 6,2 GB izvornik, 6,2 GB F16, 12,8 GB za šest razina i 3,5 GB za dvije varijante s imatrixom.

**1. Dohvati izvorni kod iste oznake**, jer skripta za pretvorbu ne dolazi u paketu s programima:

```bash
u=https://github.com/ggml-org/llama.cpp/archive/refs/tags
curl -L -o llama-src.zip $u/b12110.zip
unzip -q llama-src.zip -d llama-src
```

::: {.drugacije}
Autor je koristio izvorni kod iste oznake b12110, ali način preuzimanja nije zabilježen u logu, pa ove tri naredbe nisu pokrenute baš u ovom obliku.
:::

**Zamka:** ne instaliraj zaseban paket `gguf`. Inačica 0.19.0 s PyPI-ja ne odgovara skripti iz b12110. Autoru su zato prva dva pokušaja pala nakon 13,5 i 6,4 s:

```text
AttributeError: module 'gguf' has no attribute 'LazyChunkedTensor'
```

Skripta sama dodaje mapu `gguf-py` koja stoji do nje, pod uvjetom da mapa postoji i da nije postavljena varijabla `NO_LOCAL_GGUF`. Zato raspakiraj cijeli izvorni kod, a skriptu i `gguf-py` uzmi iz iste oznake.

**2. Preuzmi model i tekstove.** Uz knjigu dolaze samo izvadci korišteni u mjerenju (`prilozi/podaci/tekst`, CC BY-SA). Puni tekstovi s Wikipedije preuzimaju se ovako, a skripta čeka 8 s između zahtjeva:

```bash
python -X utf8 skripte/preuzmi.py models smol3
python -X utf8 skripte/l6_tekstovi.py models/tekst
python -X utf8 -c "
t = 'models/tekst/'
h = open(t + 'kal_hr.txt', encoding='utf-8').read()[:3500]
e = open(t + 'kal_en.txt', encoding='utf-8').read()[:3500]
f = open(t + 'kal_mix.txt', 'w', encoding='utf-8', newline='\n')
f.write(h + '\n' + e); f.close()
"
mkdir -p models/smol3
```

Kalibracijski tekst tako ima po 3500 znakova hrvatskog i engleskog, koliko je imao i u mjerenju. Wikipedija se mijenja, pa tvoj tekst može biti drukčiji.

**3. Pretvori u GGUF F16.** Na mjernom laptopu 86 s:

```bash
python -X utf8 llama-src/llama.cpp-b12110/convert_hf_to_gguf.py \
  models/SmolLM3-3B --outtype f16 \
  --outfile models/smol3/SmolLM3-F16.gguf
```

U ovom koraku može se izvršiti tuđi kod: skripta za neke arhitekture učitava tokenizator uz `trust_remote_code=True`. Primijeni poglavlje 10: nepoznat model pretvaraj u izoliranom okruženju.

**4. Kvantiziraj na šest razina.** Zadnji argument je broj dretvi:

```bash
for T in Q8_0 Q6_K Q5_K_M Q4_K_M Q3_K_M Q2_K; do
  ./llama/llama-quantize models/smol3/SmolLM3-F16.gguf \
    models/smol3/SmolLM3-$T.gguf $T 4
done
```

Na kraju svakog prolaza piše izvorna i nova veličina. Za Q4_K_M:

```text
llama_model_quantize_impl: model size  =  5865.57 MiB (16.00 BPW)
llama_model_quantize_impl: quant size  =  1819.10 MiB (4.96 BPW)
```

**5. Izmjeri brzinu**, za svaku razinu posebno:

```bash
./llama/llama-bench -m models/smol3/SmolLM3-Q4_K_M.gguf \
  -t 4 -p 128 -n 32 -r 2 -o csv
```

**6. Izračunaj imatrix** i kvantiziraj s njim (i za Q3_K_M):

```bash
./llama/llama-imatrix -m models/smol3/SmolLM3-Q8_0.gguf \
  -f models/tekst/kal_mix.txt -o models/smol3/imatrix.gguf \
  -t 4 -c 512 -b 512 --no-ppl
./llama/llama-quantize --imatrix models/smol3/imatrix.gguf \
  models/smol3/SmolLM3-F16.gguf \
  models/smol3/SmolLM3-Q4_K_M-imat.gguf Q4_K_M 4
```

```text
compute_imatrix: computing over 4 chunks, n_ctx=512, batch_size=512, n_seq=1
load_imatrix: loaded 252 importance matrix entries from
  models/smol3/imatrix.gguf computed on 4 chunks
```

**Memorija.** Vršna memorija (RSS) pri kvantizaciji bila je do 7,5 GB, od toga oko 1,4 GB privatno, a ostatak čine mapirane stranice F16. Za imatrix je bila 3,9 GB. Memoriju pretvorbe log ne bilježi pouzdano. Ako nemaš diska, napravi samo Q8_0 i Q4_K_M.

**Zapiši** svoju tablicu i usporedi je s tablicom ispod.
:::

Rezultati s mjernog laptopa (i5-10210U, 16 GB, bez GPU-a):

| Tip | Datoteka | bpw | Trajanje | Generiranje, tok/s |
|---|---:|---:|---:|---:|
| F16 | 6,15 GB | 16,00 | 86 s | nije mjereno |
| Q8_0 | 3,28 GB | 8,50 | 49,5 s | 4,38 ± 0,72 |
| Q6_K | 2,53 GB | 6,56 | 122,0 s | 5,53 ± 0,96 |
| Q5_K_M | 2,21 GB | 5,74 | 167,6 s | 5,69 ± 0,59 |
| Q4_K_M | 1,92 GB | 4,96 | 164,8 s | 7,65 ± 0,49 |
| Q3_K_M | 1,57 GB | 4,07 | 151,1 s | 8,23 ± 0,23 |
| Q2_K | 1,25 GB | 3,24 | 177,0 s | 9,57 ± 0,97 |

Kod F16 trajanje je pretvorba iz safetensors, a ostalo kvantizacija iz F16. Veličina F16 odnosi se na tenzore.

![Veličina datoteke i brzina generiranja SmolLM3 po razini kvantizacije, izmjerene na laptopu](slike/kvant-velicina.svg)

Tri stvari vrijedi uočiti.

**Q8_0 se kvantizira najbrže.** Log ne kaže zašto, a vjerojatan je razlog što Q8_0 računa jednu skalu po bloku, dok k-kvantovi traže skale za svaki podblok. Ostale razine trajale su 2 do 3 minute i među njima nema reda.

**Generiranje prati veličinu.** Kad pomnožiš veličinu tenzora i brzinu, na svih šest razina dobiješ otprilike isti broj, od 12 do 15 GB/s (autorov izračun, alat to ne ispisuje). To je trag ograničenja propusnošću memorije iz poglavlja 8. Razlike susjednih razina često su unutar mjerne pogreške, pa Q6_K i Q5_K_M iz ove tablice ne možeš poredati.

**Brojke su grube.** Prefill je bio 13 do 29 tok/s bez urednog poretka: Q5_K_M je ispao brži od Q4_K_M, a Q3_K_M brži od Q2_K. Tu vidiš šum dvaju ponavljanja, pa iz toga ne zaključuj ništa o tim razinama. Ista Gemma istog je dana generirala od 5,6 do 12,1 tok/s, ovisno o alatu. Zato nijedan od ovih brojeva nije "brzina modela".

## Povratak na formulu

U poglavlju 8 računaš potrebnu memoriju kao zbroj težina, KV cachea i sustava. Sad imaš stvarni prvi pribrojnik. Model građe Llame 3 8B, Q4_K_M, kontekst 32768, KV cache u FP16:

```text
težine     8 mlrd × 4,89 / 8 = 4,89 GB
           uz 5 % rezerve    = 5,13 GB
KV cache   FP16, 32768 tok.  = 4,29 GB
sustav                       = 1,00 GB
ukupno                       = 10,43 GB
```

S razinom se mijenja samo prvi redak. Isti zbroj uz Q8_0 daje 8,93 + 4,29 + 1,00 = 14,22 GB, a uz Q3_K_M 4,20 + 4,29 + 1,00 = 9,49 GB. Prijelaz s Q4_K_M na Q3_K_M štedi manje od 1 GB, a kontekst 8192 umjesto 32768 štedi 3,22 GB (KV cache pada na 1,07 GB). Ako ti memorija malo nedostaje, prvo smanji kontekst, a tek onda kvalitetu težina.

Provjera na izmjerenom modelu: SmolLM3 Q4_K_M s `-c 32768` po ovom računu daje 2,01 + 2,42 + 1,00 = 5,43 GB, a izmjereni vršni RSS bio je 5,75 GB. Račun je dobra gruba procjena, malo optimističan na malom modelu, pa uzmi rezervu.

Isto načelo vrijedi za brzinu. Gornja granica je propusnost / veličina modela, a na ovom laptopu efektivno 12 do 15 GB/s. Za 8B Q4_K_M od 4,9 GB to znači oko 3 tok/s. To je procjena autora jer taj model na laptopu nije pokretan.

## Nikad ne kvantiziraj kvantizirano

Imaš Q4_K_M i treba ti manji Q3_K_M. Prirodan je potez uzeti datoteku koju već imaš, ali upravo to ne smiješ. Razine iz prvog prolaza postale su tvoje ulazne vrijednosti, pa drugi prolaz zaokružuje već zaokruženo. Kvantizator bira skale prema podacima koji sadrže prvu pogrešku, a izvornih vrijednosti nema gdje vidjeti, pa se pogreške slažu jedna na drugu. Izgubljeno iz prvog prolaza ne vraća ni kvantizacija na višu razinu: Q8_0 napravljen iz Q4_K_M veća je datoteka s istom štetom.

Zato `llama-quantize` po zadanom odbija takav ulaz porukom `requantizing from type ... is disabled` (iz izvornog koda, autor nije izazivao tu grešku). Zastavica `--allow-requantize` postoji, a README uz nju upozorava da može jako smanjiti kvalitetu u odnosu na kvantizaciju iz 16 ili 32 bita.

**Čuvaj master.** Master je najprecizniji oblik koji imaš, safetensors u BF16 ili GGUF u F16 (ili BF16). Svaka razina nastaje izravno iz njega, kao u koraku 4 vježbe. Ako imaš samo tuđi Q4_K_M, a treba ti druga razina, preuzmi drugu datoteku. Računanje imatrixa na Q8_0 je u redu jer rezultat ne ulazi u težine, a težine se i dalje kvantiziraju iz F16.

## Koju razinu izabrati

| Situacija | Kreni od | Napomena |
|---|---|---|
| Ne znaš | Q4_K_M | Razumna početna točka |
| Memorije ima dovoljno | Q8_0 | Najveća i najsporija od ovih razina |
| Između | Q5_K_M, Q6_K | Kad Q4_K_M griješi, a Q8_0 ne stane |
| Q4_K_M ne stane | manji kontekst, pa Q3_K_M | Uz imatrix; razmisli o manjem modelu |
| Ispod Q3 (Q2_K, IQ1, IQ2) | pokus | Očekuj vidljivu štetu |

Šteta ovisi o jeziku. Na SmolLM3 perpleksnost hrvatskog teksta na Q2_K porasla je gotovo tri puta (s 19,77 na 58,80), a engleskog oko 1,8 puta. Tablica je zato samo početak. Svaki izbor provjeri na hrvatskom i na svom zlatnom skupu, kako pokazuje poglavlje 12.

## Preuzeti gotovo ili napraviti sam

Najčešće preuzimaš. Repozitoriji poput `unsloth/gemma-4-E2B-it-GGUF` i `Qwen/Qwen3-4B-GGUF` već imaju gotove razine, pa štediš 30 minuta i desetke GB. Pravila iz poglavlja 10 i dalje vrijede, a predložak u GGUF-u svejedno pročitaj.

Sam kvantiziraš u ovim slučajevima:

- **Model je fino podešen.** Spojeni LoRA model nitko drugi nema. Kvaka d.o.o. preuzima gotov Gemma GGUF dok radi s izvornim modelom, a nakon finog podešavanja kvantizira sama (poglavlje 16).
- **Nema GGUF-a** za novi ili rijedak model.
- **Želiš imatrix na svom tekstu.** Kod gotove datoteke često ne znaš na kojem je tekstu imatrix izračunat, a tebi treba hrvatski ili stručni servisni jezik.
- **Trebaš posebnu smjesu.** Zastavicama `--tensor-type`, `--output-tensor-type` i `--token-embedding-type` određuješ tip za pojedine tenzore.
- **Ne vjeruješ tuđem predlošku** i želiš sve izvesti iz službenih safetensors datoteka.

::: {.kvar}
**Simptom → uzrok**

- `AttributeError: ... 'LazyChunkedTensor'` → skripta je uzela paket `gguf` s PyPI-ja. Raspakiraj cijeli izvorni kod iste oznake, tako da `gguf-py` stoji uz skriptu.
- Pretvorba ispisuje niz `Failed to load model module ...` s `has no attribute` → isti uzrok, skripta i `gguf` nisu iz iste oznake.
- `requantizing from type ... is disabled` → ulaz je već kvantiziran. Kreni od F16 ili BF16.
- `Missing importance matrix ...` → najniži IQ tipovi traže imatrix. Dodaj `--imatrix` ili izaberi drugi tip.
- Datoteka je veća nego što kaže račun iz naziva → to je normalno: smjesa tenzora i metapodaci. Računaj iz stvarne datoteke.
- Datoteka s imatrixom iste je veličine → tako i treba biti. Bitovi su isti, a mijenjaju se izabrane razine.
- Brzine ti se razlikuju od tablice, čak i među ponavljanjima → normalno, razlika može biti i dvostruka. Mjeri više puta na mirnom stroju.
- Na niskoj razini engleski još radi, a hrvatski se raspada → razina je preniska za tvoj jezik. Idi razinu više i izmjeri (poglavlje 12).
- Tijekom kvantizacije RAM je pun → najvećim dijelom to su mapirane stranice ulazne datoteke, koje sustav može osloboditi. Ako disk neprestano radi, zatvori ostale programe.
:::

## Sažetak

Kvantizacija zaokružuje težine na malo razina unutar malih blokova i uz njih pamti skalu i pomak, pa model zauzima manje i na CPU-u brže generira, uz trajan gubitak preciznosti. U oznaci Q4_K_M broj je nazivni broj bita, K znači natblokove od 256 s podblokovima od 16 ili 32, a M smjesu u kojoj dio tenzora dobiva više bita, pa stvarnu veličinu čitaš iz datoteke. imatrix izmjerenom važnošću aktivacija važe pogrešku zaokruživanja i pritom ne dodaje bitove, pa kalibracijski tekst treba biti na tvom jeziku. Sve razine radiš izravno iz F16 ili BF16 mastera, a kreneš od Q4_K_M, s Q8_0 kad ima memorije i s razinama ispod Q3 samo kao pokusom. Koliko je pritom stvarno štete, posebno za hrvatski, mjeriš u poglavlju 12.
