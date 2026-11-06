# Memorija i brzina

::: {.cilj}
**Nakon ovog poglavlja znaš:**

- što ograničava prefill, a što generiranje, i kako izračunati gornju granicu brzine
- izračunati KV cache iz `config.json` i procijeniti ukupnu memoriju modela
- zašto Gemma s većom datotekom troši manje RAM-a od Qwena s manjom
- koji paket llama.cpp odgovara tvom hardveru i što gledati pri kupnji
:::

Prije pokretanja modela postavljaš dva pitanja: stane li i koliko će brzo raditi. Računica iz poglavlja 7 daje samo prvi pribrojnik. Za ostatak gledamo što motor iz poglavlja 6 radi s memorijom.

## Dvije faze rada

Svaki odgovor nastaje u dvije faze, a svaku ograničava nešto drugo.

![Prefill i generiranje: što radi svaka faza i što je ograničava](slike/prefill-generiranje.svg)

**Prefill** obrađuje prompt. Svi su tokeni unaprijed poznati, pa ih model računa zajedno, u serijama. Jedan prolaz kroz težine obavi posao za mnogo tokena, a računanje se dobro dijeli na jezgre procesora ili grafičke kartice (GPU). Zato prefill ograničava računska snaga. Dulji prompt znači dulje čekanje na prvi token.

**Generiranje** radi token po token. Sljedeći token ne postoji dok prethodni nije gotov, pa svaki novi token traži cijeli prolaz kroz model, a taj prolaz čita sve aktivne težine iz memorije. Cijena jednog tokena je dakle čitanje gigabajta podataka. Zato generiranje ograničava **propusnost memorije** (memory bandwidth): koliko bajtova u sekundi memorija može isporučiti.

Razlika se vidi u mjerenju. Svi brojevi u ovom poglavlju izmjereni su na laptopu s procesorom i5-10210U, 16 GB RAM-a i bez GPU-a, pa ih shvati kao primjer i izmjeri svoje. Gemma 4 E2B Q4_K_M uz 4 dretve u `llama-bench`: prefill 149,87 tok/s, generiranje 12,06 tok/s. Generiranje je dvanaest puta sporije.

## Zašto je grafička kartica brza

Kartice se obično opisuju kao "jače" od procesora. Za prefill to vrijedi. Za generiranje je važnije nešto drugo: kartica ima memoriju zalemljenu uz čip i vrlo široku vezu do nje. Snažan motor ne pomaže ako je dovod goriva uzak, a ovdje je dovod goriva propusnost memorije.

Odatle slijedi račun koji možeš izvesti napamet. Ako svaki token mora pročitati cijeli model, u sekundi ih ne može biti više od:

```text
tok/s (gornja granica) ≈ propusnost / veličina modela
```

| Hardver | Propusnost | Model 4,9 GB | Model 16 GB |
|:---|---:|---:|---:|
| DDR5, dva kanala | 80 GB/s | 16 tok/s | 5 tok/s |
| Apple M4 Pro | 273 GB/s | 56 tok/s | 17 tok/s |
| Apple M4 Max | 546 GB/s | 111 tok/s | 34 tok/s |
| NVIDIA RTX 4090 | 1008 GB/s | 206 tok/s | 63 tok/s |

To su izračunate gornje granice iz nazivnih propusnosti, a stvarne su brzine niže.

### Što kaže mjerenje

Na mjernom laptopu SmolLM3 je kvantiziran na šest razina (kako se to radi, vidjet ćeš u poglavlju 11), pa imamo isti model u šest veličina. Pomnoži li se veličina s brzinom, dobije se približno ista brojka:

| Razina | Veličina (GiB) | Generiranje (tok/s) | Umnožak (GiB/s) |
|:---|---:|---:|---:|
| Q8_0 | 3,04 | 4,38 | 13,33 |
| Q6_K | 2,35 | 5,53 | 12,99 |
| Q5_K_M | 2,05 | 5,69 | 11,69 |
| Q4_K_M | 1,78 | 7,65 | 13,59 |
| Q3_K_M | 1,46 | 8,23 | 11,98 |
| Q2_K | 1,16 | 9,57 | 11,10 |

Umnožak ostaje između 11 i 13,6 GiB/s. Mjeri `llama-bench` uz 4 dretve i dva ponavljanja, pa u brojkama ima i šuma. Model 2,6 puta manji je 2,2 puta brži, a upravo se to očekuje kad generiranje koči memorija. Dokaz to ipak nije jer se s razinom mijenja i računski posao.

### Tri ograde

**Formula broji ono što se stvarno pročita.** Gemma 4 E2B ima datoteku od 2,88 GiB i 12,06 tok/s, što daje oko 35 GiB/s, gotovo tri puta više nego SmolLM3 na istom stroju. Kartica modela (model card) navodi 2,3 milijarde efektivnih parametara i 5,1 milijarde s embeddingom. Iz tablice embeddinga svaki token čita samo svoj redak, pa je vjerojatno objašnjenje da veći dio te datoteke nije dio posla po tokenu. To je zaključak iz brojki, a nismo ga izravno izmjerili. Za model s velikim embeddingom veličina datoteke dakle podcjenjuje granicu.

**MoE čita samo aktivne težine.** Računski primjer iz poglavlja 6, 3 stručnjaka na Llami 3 8B u BF16, zauzima 38,6 GB, a po tokenu čita 16 GB. Za brzinu uzmi aktivni dio: na M4 Max 546 / 16 daje 34 tok/s, a ne 14. Za memoriju uzmi ukupni dio jer svi stručnjaci moraju biti pri ruci. Na RTX 4090 s 24 GB memorije taj model ne stane, koliko god aktivni dio izgledao skromno.

**Alat mijenja rezultat.** Ista Gemma, 4 dretve, isti dan:

| Alat | Generiranje (tok/s) |
|:---|---:|
| `llama-completion` | 5,61 |
| `llama-cli` | 8,2 do 9,0 |
| `llama-server` | 11,09 |
| `llama-bench` | 12,06 ± 0,74 |

Zato uvijek navedi raspon i alat, a jedan broj nikad ne nazivaj "brzinom modela". Raspon između alata, oko 2,2 puta, velik je kao cijeli raspon šest razina iz prethodne tablice. Brzine na istom stroju u istom danu razlikovale su se i do dva puta.

Kvaka ima cilj p95 latencije od 5 s. Na ovom laptopu `llama-server` s Gemmom potroši 0,93 s na prefill, a zatim generira 11,09 tok/s, pa u 5 s stane oko 45 tokena. Test opterećenja to potvrđuje: 48 tokena uz jednog klijenta trajalo je 4,78 s. Odgovor od 107 tokena trajao je 10,5 s. Računica unaprijed kaže koliko dug JSON smije biti.

## Tri dijela memorije

Memorija koju model zauzima dijeli se na težine, KV cache i sustav.

![Težine, KV cache i sustav u mjerilu za tri duljine konteksta](slike/memorija-stog.svg)

Težine znaš iz poglavlja 7. Pod sustav idu međuspremnici za računanje (izmjereno od 272 do 595 MiB) i ostalo što alat treba. KV cache je novi dio i jedini koji raste s kontekstom.

### Zašto model pamti prošle tokene

Vrati se pažnji iz poglavlja 6. Upit novog tokena uspoređuje se s ključem svakog ranijeg tokena i zatim uzima smjesu njihovih vrijednosti. Ključevi i vrijednosti ranijih tokena ne mijenjaju se kad stigne novi token, a računanje im je skupo. Bez spremanja bi model za svaki novi token ponovno računao sve od početka razgovora. Zato ih drži u memoriji, u svakom sloju, za svaki token u kontekstu. Taj se spremnik zove **KV cache** (Key-Value cache). Prefill ga puni, a generiranje mu u svakom koraku dodaje po jedan redak.

Upiti se ne spremaju jer upit postavlja samo novi token.

### Formula

```text
KV (bajtovi) = 2 · c · L · h · d · b / 8
```

| Oznaka | Značenje | Gdje piše |
|:---|:-----|:-----|
| 2 | ključevi i vrijednosti | stalno |
| c | duljina konteksta u tokenima | zadaješ sam, `-c` |
| L | broj slojeva | `num_hidden_layers` |
| h | kompleti K i V | `num_key_value_heads` |
| d | širina glave | `head_dim` |
| b | bitova po broju | 16 za FP16, zadano u llama.cpp |

Dijeljenje s 8 pretvara bitove u bajtove. Ako `config.json` nema `num_key_value_heads`, model ne koristi GQA pa uzmi `num_attention_heads`. Ako nema `head_dim`, računaj `hidden_size / num_attention_heads`.

Primjer je SmolLM3, čiji `config.json` iz poglavlja 3 ima `hidden_size` 2048, `num_attention_heads` 16, `num_key_value_heads` 4 i `num_hidden_layers` 36. Širina glave je 2048 / 16 = 128, pa za kontekst od 2048 tokena:

```text
2 · 2048 · 36 · 4 · 128 · 16 / 8 = 150 994 944 B = 144 MiB
```

Za Llamu 3 8B (L = 32, h = 8, d = 128), koju i ovdje uzimamo samo za računicu, izlazi:

| Kontekst | FP16 | FP8 | 4-bit |
|---:|---:|---:|---:|
| 4096 | 0,54 GB | 0,27 GB | 0,13 GB |
| 32 768 | 4,29 GB | 2,15 GB | 1,07 GB |
| 131 072 | 17,18 GB | 8,59 GB | 4,29 GB |

Ako negdje vidiš upola manje brojke, netko je izostavio faktor 2.

Stupci FP8 i 4-bit samo su formula s drukčijim b. U alatu llama.cpp zastavica `-ctk q8_0` smanjuje samo ključeve: Qwen pri `-c 8192` pada s 1152 na 882 MiB, a ne na polovicu. Vrijednosti ostaju FP16. Na FP8 za KV cache vraćamo se u poglavlju 18.

### Provjera na stvarnim modelima

llama.cpp uz `-v` ispisuje što je rezervirao (redak je ovdje prelomljen):

```text
llama_kv_cache: size =  576.00 MiB (  8192 cells,  36 layers,  1/1 seqs),
  K (f16):  288.00 MiB, V (f16):  288.00 MiB
```

Formula i log slažu se točno:

| Model | Kontekst | Formula | Log |
|:---|---:|---:|---:|
| SmolLM3 | 2048 | 144 MiB | 144,0 MiB |
| Qwen3-4B | 2048 | 288 MiB | 288,0 MiB |
| SmolLM3 | 32 768 | 2304 MiB | 2304,0 MiB |
| Qwen3-4B | 32 768 | 4608 MiB | 4608,0 MiB |
| Gemma 4 E2B | 2048 | 140 MiB | 24,0 MiB |

Zadnji redak odudara, a upravo on odgovara na pitanje iz poglavlja 1 i 2.

Svaki je pokus generirao samo 8 tokena, a Qwen je svejedno zauzeo punih 4608 MiB: KV cache rezervira se pri pokretanju prema `-c`.

### Zašto Gemma s većom datotekom troši manje

| | Gemma 4 E2B | Qwen3-4B |
|:---|---:|---:|
| Datoteka | 3,11 GB | 2,5 GB |
| KV, `-c 2048` | 24 MiB | 288 MiB |
| KV, `-c 32768` | 204 MiB | 4608 MiB |
| Vršni RSS, `-c 2048` | 2623 MiB | 4418 MiB |
| Vršni RSS, `-c 32768` | 2804 MiB | 8734 MiB |

RSS je RAM koji proces stvarno zauzima, uključujući i stranice datoteke modela koje je sustav učitao u memoriju.

Formula pretpostavlja da svi slojevi jednako pamte sve tokene, a Gemma to ne radi. Ima **klizni prozor** (sliding window): većina slojeva s pažnjom gleda samo zadnjih 512 tokena (`n_swa = 512` u logu), pa im stariji tokeni ne trebaju. Uz to, log pokazuje KV cache samo za 15 od 35 slojeva:

- 3 globalna sloja: 2048 ćelija, širina 512, ukupno 12 MiB
- 12 slojeva s kliznim prozorom: uvijek 1024 ćelije, širina 256, ukupno 12 MiB

Pri `-c 32768` raste samo globalni dio, na 192 MiB, a drugi ostaje 12 MiB. Zato 16 puta dulji kontekst Qwenu podigne KV 16 puta, a Gemmi 8,5 puta. Cijena je da ti slojevi izravno ne vide starije tokene.

Formulu zato primjenjuj samo na modele s jednakim slojevima i bez kliznog prozora. U `config.json` provjeri `use_sliding_window`, `sliding_window` i `layer_types` (SmolLM3 ima `false` i `null`), a u logu `n_swa`.

Klizni prozor ne objašnjava cijelu razliku. Pri `-c 32768` KV čini oko tri četvrtine razlike u RSS-u (4404 od 5930 MiB). Pri `-c 2048` čini je mnogo manje (264 od 1795 MiB). Ostatak mjerenje ne razlaže do kraja. Gemmin RSS manji je od same datoteke jer sustav učitava samo dijelove koje model stvarno čita, a to se slaže s ogradom o embeddingu. Qwen ima i veću dodatnu kopiju težina, `CPU_REPACK`, koju llama.cpp na procesoru stvara radi bržeg računanja (1683 prema 1069 MiB).

### Više korisnika

Svaki korisnik ima vlastiti kontekst, pa ako četiri korisnika trebaju po 8192 tokena, KV računaš za 32 768. Pazi kako to llama.cpp zadaje. `-c` je ukupan broj, a `-np` ga dijeli: `-c 8192 -np 4` daje svakom korisniku 2048 tokena, a KV kod Qwena ostaje 1152 MiB. Za 8192 po korisniku treba `-c 32768 -np 4`, što je za Qwena 4608 MiB. Brzina se pritom također dijeli: uz 4 slota brzina po klijentu pala je s 11,31 na 5,7 tok/s, a ukupna je narasla s 10,23 na 14,61 tok/s (Gemma, mali uzorak). Više u poglavlju 18.

## Cijela računica

```text
memorija ≈ težine + KV cache + sustav
```

Primjer: Llama 3 8B, Q4_K_M, kontekst 32 768, KV cache u FP16, 1 GB za sustav. Težine su 8 milijardi × 4,89 bita / 8 = 4,89 GB, a na to dodajemo 5 % rezerve:

```text
4,89 × 1,05 = 5,13 GB   težine
              4,29 GB   KV cache
              1,0  GB   sustav
             10,43 GB   ukupno
```

Računica se vraća u poglavlju 11, kad znaš odakle dolaze veličine kvantiziranih datoteka.

Za svakodnevnu procjenu dovoljno je pravilo: **datoteka + kontekst + rezerva**. Evo kako prolazi na stvarnim modelima, uz rezervu od 1 GB:

| Model | `-c` | Pravilo | Izmjereni RSS |
|:---|---:|---:|---:|
| SmolLM3 | 8192 | 3,52 GB | 3,94 GB |
| SmolLM3 | 32 768 | 5,33 GB | 5,75 GB |
| Qwen3-4B | 8192 | 4,71 GB | 5,54 GB |
| Qwen3-4B | 32 768 | 8,33 GB | 9,16 GB |
| Gemma 4 E2B | 8192 | 4,17 GB | 2,79 GB |

Na procesoru pravilo za guste modele podbaci za 0,4 do 0,8 GB zbog kopije `CPU_REPACK`, pa tamo računaj 2 GB rezerve. Za Gemmu pretjeruje, što je sigurna strana. Sve je to samo potrošnja modela. Windows i ostali programi uzimaju svoje: na laptopu sa 16 GB prije pokusa bilo je slobodno od 3,1 do 9,3 GB.

## Hardver

Stanje u studenom 2026. Nazivi paketa potječu s izdanja llama.cpp `b12110`: puni naziv počinje s `llama-b12110-`, a za Linux umjesto `win` stoji `ubuntu`. Provjeri ih pri preuzimanju. Sve osim CPU paketa autor nije pokrenuo.

| Hardver | Pozadina | Paket |
|:---|:---|:-----|
| NVIDIA | CUDA | `bin-win-cuda-13.4-x64` |
| AMD | Vulkan ili ROCm | `bin-win-vulkan-x64`, `bin-win-rocm-10.0-x64` |
| Intel | Vulkan ili SYCL | `bin-win-vulkan-x64`, `bin-win-sycl-x64` |
| Apple Silicon | Metal | `bin-macos-arm64` |
| samo procesor | CPU | `bin-win-cpu-x64` |

### NVIDIA i VRAM

Memorija na kartici zove se VRAM i ona je prva brojka koju gledaš. Težine i KV cache trebaju stati u nju. CUDA paketu na Windowsima treba i `cudart` arhiva iste inačice, a inačicu biraš prema inačici upravljačkog programa koju ispisuje `nvidia-smi`.

Zastavica `-ngl` zadaje koliko se slojeva modela stavlja na karticu:

```bash
llama-server -m model.gguf -c 8192 -ngl all --port 8080
```

::: {.neprovjereno}
Autor ovaj primjer nije pokrenuo jer traži GPU. Zadane vrijednosti `-ngl auto` i `--fit on` navodi README llama-servera u studenom 2026. Provjeri inačicu alata.
:::

Ako model ne stane, ostali slojevi rade na procesoru, u RAM-u. To se zove djelomično prebacivanje (partial offload) i tu brzina naglo pada jer svaki token mora proći sve slojeve, pa memorija sporijeg dijela određuje ukupno vrijeme. Za model od 4,9 GB, s RTX 4090 i DDR5 iz tablice, gornja je granica:

| Slojeva u RAM-u | Gornja granica |
|---:|---:|
| 0 % | 206 tok/s |
| 10 % | 95 tok/s |
| 25 % | 53 tok/s |
| 50 % | 30 tok/s |
| 100 % | 16 tok/s |

To je račun, a ne mjerenje. Desetina slojeva u RAM-u više nego prepolovi granicu. Zato je manji model koji cijeli stane u VRAM često brži od većeg koji ne stane.

Pazi i na zadano ponašanje. README navodi da je za `-ngl` zadano `auto`, a `--fit` uključen, pa alat sam prilagođava ono što nisi zadao. Model se može tiho naći djelomično na kartici. U logu potraži redak `offloaded N/M layers to GPU`: N mora biti jednak M.

### Apple

Apple Silicon ima jedinstvenu memoriju (unified memory): procesor i grafički dio dijele isti RAM, pa model nema što prebacivati preko sabirnice. Zato stroj s mnogo memorije drži modele koji ne stanu na običnu karticu. Sustav grafičkom dijelu ne daje cijelu memoriju, pa ostavi rezervu. Propusnost ovisi o čipu, a memorija se kasnije ne može dodati. LM Studio ovdje nudi i MLX.

### AMD i Intel

Vulkan radi na većini grafičkih kartica, pa je dobar prvi pokušaj. AMD ima i ROCm, a Intel SYCL. Integrirana grafika koristi obični RAM, pa ima njegovu propusnost: pomaže u prefillu, a gornju granicu generiranja ne pomiče.

### Samo procesor

Na procesoru su izvedena sva mjerenja u ovoj knjizi. Dretve se ponašaju ovako (Gemma, `llama-bench`, `-r 2`):

| Dretve | Prefill (tok/s) | Generiranje (tok/s) |
|---:|---:|---:|
| 1 | 65,53 | 6,88 |
| 2 | 98,90 | 9,81 |
| 4 | 149,87 | 12,06 |
| 6 | 139,28 | 12,76 |
| 8 | 167,71 | 13,19 |

Osam puta više dretvi daje 1,9 puta brže generiranje. Procesor ima 4 fizičke jezgre i 8 dretvi prema Intelovoj specifikaciji, a iznad 4 dobitak je u rasponu šuma (šest dretvi u prefillu ispada sporije od četiri). Vjerojatni razlog je propusnost memorije, ali log to ne dokazuje. Kreni s `-t` jednakim broju fizičkih jezgri i izmjeri.

Na poslužitelju s više procesora (NUMA) memorija je podijeljena po procesorima, a pokretanje sa `numactl --interleave=all` raspoređuje model ravnomjerno po njima.

## Što gledati pri kupnji

Redoslijed je uvijek isti: najprije memorija, jer model koji ne stane ne radi nikako ili radi vrlo sporo, a zatim propusnost.

| Želiš | Prvo: memorija | Zatim: propusnost | Smjer |
|:---|:---|:---|:---|
| Učiti, modeli do 4B | 16 GB RAM-a | dva kanala | stroj koji već imaš |
| 8B, kontekst do 4096 | 8 GB VRAM-a | što veća | kartica s barem toliko memorije |
| 8B, kontekst 32 768 | 12 do 16 GB | što veća | kartica s više VRAM-a |
| 70B, Q4_K_M | oko 55 GB | barem 500 GB/s | velika jedinstvena memorija |
| Trening | vidi poglavlje 15 | | najam GPU-a prije kupnje |

Redak za 70B zbraja 43,1 GB težina, 10,74 GB KV cachea i 1 GB sustava. Na 546 GB/s granica je oko 13 tok/s. Usporedbu s najmom i API-jem imaš u poglavlju 1.

::: {.vjezba}
**Vježba: izračunaj, pa izmjeri** `CPU` · RAM 8 GB · disk 2,5 GB · 20 min

Koristiš Qwen3-4B, drugog kandidata iz poglavlja 2, i radnu mapu iz `prilozi/README.md`. U poglavlju 2 nije preuzet, pa ga dohvati naredbom `python -X utf8 skripte/preuzmi.py models qwen`.

1. Izračunaj KV cache. Isti kod možeš prepraviti za svoj model:

```python
def kv(c, L, h, d, b=16):
    return 2 * c * L * h * d * b / 8

for c in (2048, 8192, 32768):
    bajtova = kv(c, L=36, h=8, d=128)   # Qwen3-4B
    print(c, round(bajtova / 2**20), "MiB",
          round(bajtova / 1e9, 2), "GB")
```

Stvarni izlaz:

```text
2048 288 MiB 0.3 GB
8192 1152 MiB 1.21 GB
32768 4608 MiB 4.83 GB
```

2. Zapiši očekivani RSS prema pravilu datoteka + kontekst + rezerva. Zatim izmjeri (`mjeri.py` radi samo na Windowsima):

```bash
python skripte/mjeri.py log.txt -- llama/llama-completion.exe \
  -m models/Qwen3-4B-GGUF/Qwen3-4B-Q4_K_M.gguf -no-cnv \
  -p "Perilica rublja" -n 8 -c 8192 -t 4 -v --no-display-prompt
grep -E "llama_kv_cache: +size|n_head_kv|n_embd_head_k" log.txt
```

Isti se retci u logu pojave dvaput jer alat najprije napravi probni prolaz. Na mjernom laptopu: KV 1152,00 MiB, `peakWS_MB=5282`. Skripta dijeli s 2^20^, pa je to zapravo MiB. Ako KV odstupa od računa, potraži `n_swa` i klizni prozor.

3. Izmjeri utjecaj dretvi na Gemmi:

```bash
llama/llama-bench.exe \
  -m models/gemma-4-E2B-it-GGUF/gemma-4-E2B-it-Q4_K_M.gguf \
  -t 1,2,4,6,8 -p 128 -n 48 -r 2 -o md
```

Usporedi s tablicom dretvi. Na svom stroju dobit ćeš druge brojke, važnije od naših.
:::

::: {.kvar}
**Simptom → uzrok**

- Prvi token dugo kasni, a zatim tekst teče → prefill. Skrati prompt ili daj više računske snage.
- Prvi token stiže brzo, a tekst puže → generiranje. Uzmi manji model ili brži hardver i provjeri jesu li svi slojevi na kartici.
- Imaš GPU, a brzina je blizu procesorske → dio slojeva je u RAM-u ili je preuzet CPU paket. Provjeri `offloaded N/M`.
- Model se učita, a sruši se kad povećaš `-c` → KV cache raste s kontekstom i rezervira se odmah. Izračunaj ga i smanji `-c`.
- Uz `-np 4` poruke prelaze kontekst iako je `-c` velik → `-c` se dijeli na slotove.
- KV u logu ne odgovara formuli → klizni prozor ili različiti slojevi. Vjeruj logu.
- Dva mjerenja istog modela jako se razlikuju → drugi alat ili zauzet stroj. Navedi raspon i alat.
:::

## Sažetak

Prefill ograničava računska snaga, a generiranje propusnost memorije, pa je gornja granica brzine približno propusnost podijeljena s onim što se po tokenu stvarno pročita, kod MoE-a samo aktivne težine. Memorija je zbroj težina, KV cachea i sustava, a KV cache za modele s jednakim slojevima računaš kao `2·c·L·h·d·b/8`. Ta formula točno pogađa SmolLM3 i Qwen, a Gemma je zaobilazi kliznim prozorom, što je glavni razlog zašto joj pri dugom kontekstu treba mnogo manje RAM-a. Djelomično prebacivanje na karticu naglo ruši brzinu, pa pri kupnji najprije gledaš memoriju, a zatim propusnost. Sve brojke s jednog stroja provjeri na svom, jer ih alat i stanje stroja mijenjaju i do dva puta.
