# Kad prerasteš llama-server

::: {.cilj}
**Nakon ovog poglavlja znaš:**

- izmjeriti poslužitelj pod opterećenjem i pročitati TTFT, brzinu po klijentu, ukupnu brzinu i p95
- odlučiti je li `llama-server` dovoljan ili treba prijeći na vLLM
- izabrati format kvantizacije za poslužitelj s GPU-om i prepoznati tihi pad na sporiji put
- što pratiti u pogonu i što provjeriti prije nego što poslužitelj otvoriš korisnicima
:::

Ovo je poglavlje izborno. Dosad je model služio jednom korisniku. Što se dogodi kad ih stigne četvero odjednom? Odgovor daje mjerenje, a alat biraš tek nakon njega.

## Test opterećenja

Skripta `l11_opterecenje.py` sama pokreće `llama-server`, šalje mu istodobne zahtjeve i mjeri svaki od njih. Koristi samo standardnu biblioteku Pythona.

::: {.vjezba}
**Vježba: opteretiti poslužitelj** `CPU` · RAM 8 GB · disk 3,2 GB · 15 min

Koristiš radnu mapu iz `prilozi/README.md` i Gemmu iz poglavlja 2, a putanju modela prilagodi svojoj. Skripta radi na Windowsima jer pokreće `llama/llama-server.exe` i koristi `mjeri.py`.

```bash
python -X utf8 skripte/l11_opterecenje.py \
  models/gemma-4-E2B-it-GGUF/gemma-4-E2B-it-Q4_K_M.gguf \
  logovi/l11_server.txt grafovi/opterecenje.csv
```

Za svaki `--parallel` skripta pokrene ovakav poslužitelj (sama koristi port 8094):

```bash
llama/llama-server.exe -m GEMMA.gguf --port 8080 --host 127.0.0.1 \
  -c 8192 -t 4 -np 4 --reasoning off
```

Svaki klijent traži popis koraka za provjeru kvara, uz `max_tokens` 48, `ignore_eos` i `stream`, pa svaki zahtjev daje točno 48 tokena. Početak poruke razlikuje se od klijenta do klijenta, da prompt cache ne bude zajednički. Ispis izgleda ovako (redak je ovdje prelomljen):

```text
### --parallel 4 []: total_slots=4, n_ctx po slotu=2048
  klijenata 4 zahtjeva 8 tokena 384: TTFT p50 4.91 s p95 5.05 s |
  latencija p50 13.17 s p95 13.36 s | po klijentu 5.7 tok/s |
  ukupno 14.61 tok/s | peak WS 2798 MB
```

Stupac peak WS zapravo je u MiB. Zadnji prolaz skripte, sa `--no-kv-unified`, zanemari: log pokazuje `kv_unified = 'false'` i u prolazima bez te zastavice, pa usporedba ništa ne mjeri. Dretve (`-t`) i slučajeve mijenjaš u popisu `SLUCAJ` na vrhu skripte.
:::

Rezultat s laptopa (i5-10210U, 16 GB, bez GPU-a), s Gemmom 4 E2B Q4_K_M. Vremena su u sekundama. Izmjeri svoje jer je ovo jedan model i jedna vrsta zahtjeva.

| `-np` / klijenata | TTFT p50 / p95 | Latencija p50 / p95 | tok/s po klijentu | tok/s ukupno |
|:---|---:|---:|---:|---:|
| 1 / 1 | 0,57 / 0,57 | 4,78 / 4,78 | 11,31 | 10,23 |
| 1 / 4 | 14,31 / 14,46 | 18,49 / 18,77 | 11,13 | 10,4 |
| 2 / 2 | 2,49 / 2,6 | 8,43 / 8,51 | 7,88 | 11,37 |
| 2 / 4 | 9,12 / 10,2 | 16,24 / 16,29 | 7,6 | 12,34 |
| 4 / 4 | 4,91 / 5,05 | 13,17 / 13,36 | 5,7 | 14,61 |
| 4 / 8 | 13,79 / 13,8 | 21,85 / 21,86 | 5,81 | 17,56 |

### Što znači koji stupac

- **TTFT** (time to first token) je vrijeme od slanja zahtjeva do prvog tokena. Uključuje čekanje u redu i prefill. To je trenutak u kojem korisnik vidi da se nešto događa.
- **Latencija** je vrijeme do zadnjeg tokena, dakle cijeli zahtjev.
- **p50 i p95**: polovica zahtjeva završi unutar p50, a 95 % unutar p95. Cilj se postavlja na p95 jer prosjek skriva one koji najdulje čekaju.
- **tok/s po klijentu** je brzina teksta nakon prvog tokena. Čekanje nije uračunato.
- **tok/s ukupno** su svi tokeni podijeljeni s ukupnim vremenom testa. To je kapacitet poslužitelja, na engleskom throughput.

Pazi na veličinu uzorka: svaki red ima 2 do 8 zahtjeva. Uz toliko malo uzoraka skripta za p95 uzima najsporiji zahtjev, a uz dva zahtjeva to je i p50, pa su u prvom redu oba broja ista. Za pravu odluku pošalji stotine zahtjeva.

### Kako čitati redove

**Jedan broj vara.** U redu 1 / 4 brzina po klijentu je odličnih 11,13 tok/s, a korisnik čeka 14,31 s na prvi token. Klijenti stoje u redu, a kad dođu na red, tekst teče punom brzinom.

**Više slotova skraćuje čekanje, a usporava tekst.** Četiri klijenta na četiri slota dočekaju prvi token za 4,91 s, ali brzina po klijentu pada na 5,7 tok/s.

**Kapacitet raste umjereno.** S ista četiri klijenta ukupna brzina ide 10,4, pa 12,34, pa 14,61 tok/s, što je 1,4 puta za četiri puta više slotova. Stroj je isti, dretve iste i memorija ista.

**Zbroj ne odgovara.** Četiri klijenta po 5,7 tok/s dala bi 22,8 tok/s, a izmjereno je 14,61. Brzina po klijentu ne računa vrijeme do prvog tokena, a ukupna ga računa.

### Kako slotovi dijele kontekst

Iz poglavlja 8 znaš da je `-c` ukupan broj koji `-np` dijeli na slotove. Log to potvrđuje za `-c 8192` (redak je prelomljen):

```text
load_model: initializing, n_slots = 4, n_ctx_slot = 2048,
  kv_unified = 'false'
```

| `-np` | Kontekst po slotu | Vršni RSS |
|---:|---:|---:|
| 1 | 8192 | 2681 do 2698 MiB |
| 2 | 4096 | 2709 do 2741 MiB |
| 4 | 2048 | 2798 do 2812 MiB |

RAM gotovo miruje jer je ukupan kontekst isti. Cijena je u tome što svaki korisnik dobiva četvrtinu konteksta, pa poruka koja je radila na jednom slotu na četiri može prijeći granicu. Broj slotova zadaj izričito: u našem pokusu `-c 4096` bez `-np` sam je dao 4 slota.

### Što to znači za Kvaku

Cilj je p95 ≤ 5 s.

| Istodobno | Najbolji p95 latencije | Cilj |
|---:|---:|:---|
| 1 | 4,78 s (`-np 1`) | ispunjen, za 0,22 s |
| 2 | 8,51 s (`-np 2`) | nije ispunjen |
| 4 | 13,36 s (`-np 4`) | nije ispunjen |

Na četiri slota već i sam prvi token stiže za 5,05 s. Račun pokazuje zašto slotovi ne mogu spasiti cilj: četiri odgovora od 48 tokena u 5 s traže 4 × 48 / 5 = 38,4 tok/s, i to prije prefilla, a laptop daje 14,61 do 17,56 tok/s. Nedostaje više nego dvostruko.

I red s jednim klijentom je povoljan slučaj: 48 tokena i dva zahtjeva. Pravi zapisnici iz poglavlja 9 imaju p95 od 6,7 s, jedan po jedan. Ovaj laptop dakle ne ispunjava Kvakin cilj ni za jednog korisnika na pravom poslu, a za više njih ni približno. To je problem kapaciteta hardvera, a vLLM ga na ovom stroju ne rješava jer traži Linux i, za svoju glavnu namjenu, GPU. Kvakin idući korak je jedna kartica prema računici iz poglavlja 8, isti test i mjerenje koliko zahtjeva stvarno stiže istodobno.

## Pravilo: kada prijeći

Prvo pokreni test na hardveru na kojem ćeš raditi, s brojem klijenata koji stvarno očekuješ. Ako je cilj ispunjen, ostani. Promjena poslužitelja donosi dodatan posao, a ovdje ništa ne bi popravila.

| Pitanje | `llama-server` | vLLM ili SGLang |
|:---|:---|:---|
| Korisnika istodobno | šačica | mnogo, s vršnim opterećenjima |
| Hardver | CPU, Apple, jedan GPU, miješano | Linux, jedan ili više GPU-a |
| Format | GGUF | safetensors s kvantizacijom za GPU |
| Prioritet | jednostavnost | tok/s po euru |

Prije prelaska isprobaj jeftinije poteze: kraći `max_tokens`, kraći prompt, manji model koji cijeli stane u VRAM i drugi `-np`. Prijeđi kad na GPU-u s optimalnim postavkama p95 i dalje ne prolazi, kad imaš više kartica ili kad na računu ima smisla izvući više tok/s iz istog najma. Usporedba je poštena samo na istoj kartici, s istim zahtjevima i na istom cilju p95: bilježiš najveću ukupnu brzinu uz koju se cilj još drži, pa je dijeliš s cijenom.

## Što vLLM dodaje

vLLM je poslužitelj građen za mnogo istodobnih zahtjeva. Službeno radi na Linuxu, a na Windowsima preko WSL-a. Govori isti OpenAI-kompatibilan API iz poglavlja 13, pa klijent ostaje gotovo isti.

**Kontinuirano spajanje u serije** (continuous batching). Klasična serija čeka da svi zahtjevi završe, pa kratak odgovor stoji uz dugi. Ovdje se sastav serije mijenja u svakom koraku: čim jedan zahtjev završi, novi uskače. `llama-server` također ima tu mogućnost (`--cont-batching`, zadano uključeno), ali unutar broja slotova zadanog pri pokretanju. vLLM ima raspoređivač koji sam odlučuje koliko zahtjeva pušta u rad prema tome koliko ima memorije.

**PagedAttention.** To je odgovor na pitanje dijeljenja `-c`. Operacijski sustav programu daje memoriju u stranicama koje mogu biti bilo gdje i dodjeljuje ih kad zatrebaju. PagedAttention isto radi s KV cacheom: dijeli ga na blokove stalne veličine, a tablica blokova povezuje redoslijed tokena s njihovim stvarnim mjestom u memoriji. Blokovi se uzimaju tek kad nastanu novi tokeni, pa kratki razgovor ne drži rezervu dugog. Zahtjevi s istim početkom mogu dijeliti iste blokove.

Posljedica za tebe: više ne dijeliš kontekst na jednake dijelove. Zadaješ koliko kartice poslužitelj smije uzeti i koliki smije biti jedan zahtjev, a ostalo je zajednički bazen.

**SGLang** je alternativa iste vrste, s OpenAI-kompatibilnim API-jem i podrškom za više GPU-a. Dokumentacija kao glavnu značajku navodi RadixAttention i prefix caching, ponovnu upotrebu već izračunatog KV cachea za zajednički početak prompta, a sam se projekt opisuje kao optimiziran za rad s agentima. Ima smisla kad mnogo zahtjeva dijeli dugačak početak, primjerice istu sistemsku poruku. Između ta dva alata ne biraj po tuđim tablicama: pusti isti test na svojem opterećenju.

### Naredba

Provjereno na docs.vllm.ai 5. 11. 2026.; zadnja inačica na PyPI-ju tada je 0.33.0. Dokumentacija se brzo mijenja, pa provjeri sa `vllm serve --help`.

```bash
vllm serve ./SmolLM3-3B-FP8-Dynamic \
  --host 127.0.0.1 --port 8000 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.90 \
  --tensor-parallel-size 1 \
  --api-key "$VLLM_API_KEY"
```

::: {.neprovjereno}
Autor ovaj primjer nije pokrenuo jer traži GPU i Linux. Zastavice su prepisane iz dokumentacije. Provjeri inačicu alata.
:::

| Zastavica | Značenje |
|:---|:-----|
| `--max-model-len` | najveća duljina jednog zahtjeva, prompt i odgovor zajedno; bez nje uzima se iz `config.json`, što može biti mnogo |
| `--gpu-memory-utilization` | udio memorije kartice za ovu instancu, od 0 do 1; bez njega 0,92 ili 1,0, ovisno o načinu vođenja KV cachea |
| `--tensor-parallel-size` | na koliko se kartica dijeli model; zadano 1 |
| `--quantization` | metoda kvantizacije; bez nje čita se `quantization_config` iz modela, a ako je nema, model se smatra nekvantiziranim |

`--quantization` obično ne trebaš za compressed-tensors, oblik iz poglavlja 10. Dokumentacija ga izričito traži za modele iz ModelOpta: `modelopt_fp4` za NVFP4 i `modelopt_mxfp8` za MXFP8. Za starije AWQ modele navodi `auto_awq`.

## Porodice kvantizacije za poslužitelj

GGUF iz poglavlja 11 građen je za llama.cpp. Kartice imaju vlastite formate koje mogu računati izravno. Oznaka W8A8 znači 8 bitova za težine (weights) i 8 za aktivacije, međurezultate koji teku kroz slojeve. W4A16 znači 4 bita za težine i 16 za aktivacije.

| Format | Bitovi | Hardver | Alat | Kalibracija |
|:---|:---|:---|:---|:---|
| GGUF Q4_K_M | oko 5 po težini | CPU, Apple, razne kartice | `llama-quantize` | samo imatrix, izborno |
| FP8 W8A8 | 8 | NVIDIA Ada, Hopper, Blackwell | LLM Compressor | `FP8_DYNAMIC`: ne |
| AWQ (INT4 W4A16) | 4 za težine | NVIDIA, od Turinga | LLM Compressor | da |
| NVFP4 | 4, oko 4,5 sa skalama | NVIDIA Blackwell ili noviji | ModelOpt, LLM Compressor | da |
| MXFP8 | 8, grupe od 32 | novije NVIDIA, provjeri | ModelOpt | provjeri za shemu |

Stanje u studenom 2026. Podršku po karticama provjeri u tablici na docs.vllm.ai, koja za FP8 W8A8 navodi i AMD.

**Kalibracija** znači da kvantizator kroz model pusti uzorak tvojih podataka i iz njega odredi skale. `FP8_DYNAMIC` je ne treba jer se težine zaokružuju bez podataka, a aktivacije se kvantiziraju u hodu za svaki token.

**AWQ** (Activation-aware Weight Quantization) na malom uzorku gleda aktivacije, pa težine zaokružuje tako da greška manje škodi. Biblioteka AutoAWQ je napuštena i njezin je posao preuzeo LLM Compressor. vLLM i dalje učitava postojeće AWQ modele, pa stare repozitorije možeš koristiti.

**NVFP4** je 4-bitni broj s pomičnim zarezom. Svaki blok od 16 elemenata ima vlastitu skalu, otud oko 4,5 bita. **MXFP8** dolazi iz otvorene OCP MX specifikacije.

### Zašto ovdje ne koristiš GGUF

vLLM ima GGUF na popisu formata, pa pitanje ima smisla. Dokumentacija podršku opisuje kao vrlo eksperimentalnu i neoptimiziranu, moguće nespojivu s drugim značajkama, a premještena je u zaseban dodatak `vllm-gguf-plugin`. Sve što vLLM čini brzim očekuje safetensors s formatima iz gornje tablice. Zato Kvaka prema poglavlju 10 čuva izvorni safetensors: iz njega nastaje FP8, a iz GGUF-a ne može.

### Recept za FP8

::: {.vjezba}
**Vježba: FP8 model i posluživanje** `najam GPU-a` · VRAM 8 GB · disk 15 GB · 30 min

Instalacija je `pip install llmcompressor`. Recept prati primjer iz repozitorija LLM Compressora:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from llmcompressor import oneshot
from llmcompressor.modifiers.quantization import QuantizationModifier

MODEL_ID = "HuggingFaceTB/SmolLM3-3B"
SAVE_DIR = "SmolLM3-3B-FP8-Dynamic"

model = AutoModelForCausalLM.from_pretrained(MODEL_ID)
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

recipe = QuantizationModifier(
    targets="Linear", scheme="FP8_DYNAMIC", ignore=["lm_head"]
)
oneshot(model=model, recipe=recipe)

model.save_pretrained(SAVE_DIR)
tokenizer.save_pretrained(SAVE_DIR)
```

Zatim mapu posluži naredbom iz prethodnog odjeljka, pusti zlatni skup iz poglavlja 12 i ponovi test opterećenja na istoj kartici.
:::

::: {.neprovjereno}
Autor ovaj primjer nije pokrenuo jer traži GPU. Izvorni primjer koristi zaključanu Llamu 3 8B, a ovdje ju je zamijenio SmolLM3, što nije isprobano; RAM, disk i vrijeme u oznaci vježbe samo su procjena. Provjeri inačicu alata (llmcompressor 0.15.0 na PyPI-ju, studeni 2026.).
:::

## FP8 za KV cache

U poglavlju 8 ostalo je otvoreno: `-ctk q8_0` u llama.cpp smanjuje samo ključeve. Kod Qwena pri `-c 8192` K pada s 576 na 306 MiB, V ostaje 576 MiB, pa ukupno ide s 1152 na 882 MiB.

vLLM `--kv-cache-dtype` postavlja i ključeve i vrijednosti. Račun za Llamu 3 8B pri 32 768 tokena iz poglavlja 8 daje pad s 4,29 na 2,15 GB. Riječ je o formuli, mjerenja nema.

| Vrijednost | Značenje |
|:---|:-----|
| `auto` | tip podataka modela, zadano |
| `fp8` | isto što i `fp8_e4m3` |
| `fp8_e4m3` | 4 bita eksponenta i 3 mantise iz poglavlja 7, CUDA 11.8+ i ROCm |
| `fp8_e5m2` | veći raspon, grublji koraci, CUDA 11.8+ |

Novije inačice nude i druge vrijednosti, primjerice `nvfp4`, pa popis provjeri u `--help`.

Dvije su zamke. Bez kalibracije sve su skale 1,0, što znači da se brojevi ne prilagođavaju stvarnom rasponu, a dokumentacija preporučuje kalibraciju kroz LLM Compressor. Slojevi s kliznim prozorom, poznati iz Gemme u poglavlju 8, osjetljiviji su na ovu kvantizaciju, pa ih možeš izuzeti:

```bash
vllm serve ./model --kv-cache-dtype fp8 \
  --kv-cache-dtype-skip-layers sliding_window
```

::: {.neprovjereno}
Autor ovaj primjer nije pokrenuo jer traži GPU. Provjeri inačicu alata.
:::

KV cache u FP8 mijenja brojke s kojima pažnja računa, pa i on može promijeniti odgovore. Nakon njega ponovi zlatni skup.

## Zamka: model radi, a sporiji put je tih

Kvantizirani model ne javlja grešku kad kartica nema pravu jezgru za njega. Dokumentacija za NVFP4 kaže: na kartici bez izvorne FP4 jezgre vLLM prelazi na izvođenje W4A16 kroz Marlin i ispiše samo upozorenje. Model se učita, odgovori stižu, a propusnost može biti slabija od one zbog koje format biraš.

Zato nakon svakog pokretanja pregledaj log:

```bash
vllm serve ORG/MODEL-NVFP4 --quantization modelopt_fp4 \
  --host 127.0.0.1 --port 8000 2>&1 | tee vllm.log
grep -iE "warn|fallback|marlin|backend" vllm.log
```

::: {.neprovjereno}
Autor ovaj primjer nije pokrenuo jer traži GPU, pa ni točan tekst upozorenja nije viđen. Riječi u `grep` su polazište. Provjeri inačicu alata.
:::

Potvrdi da su učitane izvorne FP4 jezgre. Usporedi i zauzeće u `nvidia-smi` s računom iz poglavlja 8, a ukupnu brzinu s testom opterećenja. Jezgru možeš zadati izričito zastavicom `--linear-backend`.

## Što pratiti u pogonu

vLLM izlaže metrike na `/metrics`, u formatu alata Prometheus. `llama-server` ih daje uz `--metrics`, a stanje slotova na `/slots`.

| Metrika | Što pokazuje | U vLLM-u |
|:---|:-----|:-----|
| TTFT | red i prefill | `vllm:time_to_first_token_seconds` |
| razmak između tokena (ITL) | brzina generiranja | `vllm:inter_token_latency_seconds` |
| ukupna brzina | kapacitet | `vllm:generation_tokens_total` |
| memorija GPU-a | stane li sve | `nvidia-smi`, `vllm:kv_cache_usage_perc` |
| duljina reda | čekaju li zahtjevi | `vllm:num_requests_waiting` |

Cilj prati kroz `vllm:e2e_request_latency_seconds`, cijelo trajanje zahtjeva. Metrike se čitaju zajedno. Kad raste TTFT, a ITL miruje, krivi su red ili dugački promptovi. Rast ITL-a znači previše zahtjeva u seriji. Red koji raste dok ukupna brzina stoji znači da je dosegnut kapacitet. KV cache blizu 100 % uz zahtjeve koji čekaju u redu znači da je memorija postala usko grlo. Starija metrika `vllm:num_requests_swapped` u dokumentaciji je označena kao zastarjela.

## Sigurnosni popis prije otvaranja

- **Autentikacija.** Postavi ključ, ali znaj što pokriva. `--api-key` u vLLM-u štiti samo putove pod `/v1`, `/v2`, `/inference` i `/cohere`. Put `/invocations` daje iste mogućnosti bez ključa, a bez ključa rade i `/pause` i `/update_weights`. Dokumentacija zato izričito kaže da se ne oslanjaš samo na ključ.
- **Obrnuti proxy.** Stavi nginx ili sličan poslužitelj ispred vLLM-a, propusti samo putove koje koristiš i dodaj TLS te ograničenje broja zahtjeva.
- **Nema javno otvorenog porta.** Veži se na `127.0.0.1` ili na privatnu mrežu. Vatrozid neka pušta samo API port. `torch.distributed` može i na jednom stroju slušati na svim mrežnim sučeljima, a komunikacija među čvorovima nije zaštićena.
- **Bez razvojnih načina.** `VLLM_SERVER_DEV_MODE=1` nikad u pogonu: otvara proizvoljno izvršavanje RPC metoda.
- **Logovi i privatnost.** Prompt je podatak korisnika, a Kvakini zapisnici mogu sadržavati podatke o kupcima. `--enable-log-requests` je zadano isključen, a uz razinu DEBUG upisuje i tekst prompta. Ne uključuj ga u pogonu bez dogovora o tome tko čita log i koliko se čuva.
- **`trust_remote_code` isključen.** U vLLM-u je zadano isključen. Ako ti zaista treba, slijedi postupak iz poglavlja 10 i prikvači točan commit.

::: {.kvar}
**Simptom → uzrok**

- Brzina po klijentu je dobra, a korisnici se žale → gledaš pogrešan stupac. Izmjeri TTFT, koji pokazuje red.
- Više slotova, a p95 i dalje ne prolazi → kapacitet. Izračunaj potrebne tok/s i usporedi ih s ukupnom brzinom.
- Nakon povećanja `-np` poruke prelaze kontekst → `-c` se dijeli. Povećaj `-c` razmjerno slotovima.
- Odmah nakon pokretanja vLLM drži gotovo cijelu karticu → to je zadano ponašanje. Smanji `--gpu-memory-utilization`.
- NVFP4 model radi, a sporiji je od očekivanog → pad na W4A16. Provjeri upozorenja u logu i `--linear-backend`.
- Kvantizirani model troši memoriju kao nekvantizirani → nedostaje opis kvantizacije. Provjeri `config.json` i `--quantization`.
- Nakon `--kv-cache-dtype fp8` točnost pada → nema kalibracije ili su osjetljivi slojevi s kliznim prozorom. Kalibriraj, izuzmi ih i ponovi zlatni skup.
- `--api-key` je postavljen, a netko svejedno dobiva odgovore → koristi nezaštićeni put poput `/invocations`. Stavi proxy s popisom dopuštenih putova.
:::

## Sažetak

Test opterećenja na laptopu pokazuje da više slotova skraćuje čekanje i usporava tekst, a ukupnu brzinu diže samo 1,4 puta, pa Kvakin p95 ≤ 5 s ne prolazi čim stigne više korisnika. `llama-server` ostaje pravi izbor za šačicu korisnika, CPU ili jednu karticu, a vLLM ili SGLang imaju smisla tek kad mjerenje pokaže da cilj pada ili kad računaš tok/s po euru na više GPU-a. Njihova prednost je u kontinuiranom spajanju u serije i KV cacheu koji se dodjeljuje po blokovima, a formati su FP8, AWQ i NVFP4 iz LLM Compressora ili ModelOpta, dok GGUF ostaje za llama.cpp. Nakon pokretanja provjeri log jer pad na sporiji put ne javlja grešku, pa zatim prati TTFT, ITL, ukupnu brzinu, memoriju i red. Ključ na API-ju nije dovoljan, pa poslužitelj drži iza proxyja, bez javnog porta, s pažljivim logovima i isključenim `trust_remote_code`.
