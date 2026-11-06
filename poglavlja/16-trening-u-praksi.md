# Trening u praksi

::: {.cilj}
**Nakon ovog poglavlja znaš:** pokrenuti LoRA trening na CPU-u i čitati njegov gubitak · provesti adapter kroz spajanje, GGUF i kvantizaciju uz mjerenje na svakom koraku · ponovno provjeriti sigurnost · izabrati alat i pripremiti plaćeni trening na najmljenom GPU-u.
:::

Mehanizam iz poglavlja 15 sada dobiva naredbe. Poglavlje ima tri razine i svaka drukčije jamči ono što piše:

- **Razina 1, simulator `CPU`:** stvarno pokrenuto, sve brojke su izmjerene.
- **Razina 2, cijeli lanac `CPU`:** stvarno pokrenuto, od adaptera do kvantiziranog modela.
- **Razina 3, pravi trening `najam GPU-a`:** autor ovo nije pokrenuo. Sintaksa je provjerena prema dokumentaciji, a rezultati su tvoji.

Mjerni stroj je laptop s i5-10210U, 16 GB RAM-a i bez GPU-a, uz 4 dretve, torch 2.15.0, transformers 5.22.1 i peft 0.21.2. Tvoje će vrijeme biti drukčije, pa izmjeri svoje.

## Razina 1: simulator `CPU`

Simulator je pravi LoRA trening na premalom modelu: običan PEFT na `HuggingFaceTB/SmolLM2-135M-Instruct` (134 515 008 parametara), s Kvakinih 240 primjera za trening i 60 za validaciju iz poglavlja 14. Ciklus je isti kao u poglavlju 15, samo bez NF4 i bez GPU-a.

Od polazišta iz poglavlja 15 razlikuju ga četiri stvari, pa ih nemoj uzeti kao preporuku:

- adapter ide samo na četiri projekcije pažnje, bez MLP-a;
- batch je 4, bez akumulacije, pa epoha ima 60 koraka;
- stopa učenja je `5e-4`, a epoha 5;
- sistemska poruka je skraćena jer svaki token na CPU-u košta vrijeme.

Gubitak se računa samo na tokenima odgovora. Skripta prompt maskira oznakom `-100`, a odgovoru dodaje `<|im_end|>`, pa model uči i stati.

::: {.vjezba}
**Vježba: prvi trening** `CPU` · RAM 16 GB · disk 2 GB · 35 min

Radnu mapu složi prema `prilozi/README.md`, na lokalnom disku. Skripta je `prilozi/vjezbe/l9_trening.py`.

```bash
python -X utf8 skripte/preuzmi.py models smol2
python -X utf8 skripte/l9_trening.py \
  models/SmolLM2-135M-Instruct podaci models/l9/glavni \
  --epohe 5 --r 8 --lr 5e-4 --eval-svakih 30
```

RAM je ono što mjerni stroj ima. Vršnu memoriju Pythona log nije valjano zabilježio.
:::

Prvi ispis treba pročitati prije nego što otiđeš na kavu:

```text
primjera 240 val 60 prosjecno tokena po primjeru 132
r=8 ciljevi=['q_proj', 'k_proj', 'v_proj', 'o_proj']
  trenira se 921,600 od 135,436,608 (0.680 %)
```

Redak je ovdje prelomljen radi širine. Ako je broj parametara koji se treniraju nula ili jednak cijelom modelu, stani odmah. Ispravan broj možeš i izračunati: 30 slojeva s po 3840 parametara po jedinici r daje 115 200 · r, dakle 921 600 za r = 8.

**Stvarno vrijeme:** 1531 s treninga, oko 5,1 s po koraku. Cijela skripta trajala je 2069,7 s jer prije i poslije treninga mjeri točnost na zlatnom skupu i na 30 validacijskih primjera.

### Gubitak

| Korak | Epoha | Trening | Validacija | Vrijeme (s) |
|------:|------:|--------:|-----------:|------------:|
| 0     | 0     |         | 2,661      | 0           |
| 30    | 0,5   | 2,0101  | 1,1662     | 186         |
| 60    | 1,0   | 0,8223  | 0,4816     | 341         |
| 90    | 1,5   | 0,3034  | 0,2367     | 504         |
| 120   | 2,0   | 0,1964  | 0,1627     | 651         |
| 150   | 2,5   | 0,1125  | 0,1161     | 802         |
| 180   | 3,0   | 0,0863  | 0,0973     | 949         |
| 210   | 3,5   | 0,0635  | 0,0766     | 1093        |
| 240   | 4,0   | 0,0563  | 0,0698     | 1240        |
| 270   | 4,5   | 0,0398  | 0,0647     | 1389        |
| 300   | 5,0   | 0,0374  | 0,0628     | 1531        |

![Krivulje gubitka glavnog i prenaučenog pokusa](slike/gubitak-krivulje.svg)

Obje krivulje padaju do kraja, a najniža validacija pada na zadnji korak. To je prvi oblik s popisa iz poglavlja 15: model uči i prenaučenosti nema.

Do koraka 120 validacijski gubitak manji je od trenažnog, što izgleda čudno. Trenažni broj je prosjek prethodnih 30 koraka, s početnim lošim koracima i uključenim dropoutom. Validacija se mjeri na kraju intervala, bez dropouta. Zato u brzom početku validacija smije biti niža.

### Pokus s prenaučenošću

Da bi se prenaučenost vidjela, drugi pokus namjerno kvari uvjete: 20 primjera za trening, 24 za validaciju, viši r, stopa `2e-3` i 20 epoha.

```bash
python -X utf8 skripte/l9_trening.py \
  models/SmolLM2-135M-Instruct podaci models/l9/prenaucen \
  --train-n 20 --val-n 24 --epohe 20 --r 16 --lr 2e-3 \
  --eval-svakih 5 --bez-zlatnog
```

| Korak | Epoha | Trening | Validacija |
|------:|------:|--------:|-----------:|
| 0     | 0     |         | 2,7063     |
| 10    | 2     | 1,6587  | 1,2655     |
| 20    | 4     | 0,4935  | 0,7438     |
| 30    | 6     | 0,1294  | 0,5983     |
| 40    | 8     | 0,0291  | 0,5867     |
| 50    | 10    | 0,0076  | 0,6085     |
| 70    | 14    | 0,0017  | 0,5868     |
| 100   | 20    | 0,0011  | 0,5914     |

Trajalo je 564 s. **Udžbenički oblik se nije pojavio.** Očekivala se krivulja u obliku slova U, gdje validacija nakon minimuma trajno raste. Ovdje se validacija od koraka 30 gotovo ne miče: najniža je 0,5867, popne se na 0,6085 i vrati na 0,5914.

Prenaučenost se vidi u jazu. Trening je na 0,0011, što znači da model 20 primjera zna napamet, a validacija je oko 0,59. U glavnom pokusu isti je par 0,0374 i 0,0628. Zato uz stavku "validacija raste" iz poglavlja 15 gledaj i razmak između krivulja: ravna validacija uz trening koji i dalje pada također znači da daljnji koraci ne donose ništa.

Promijenjeno je više postavki odjednom, pa pokus ne kaže koja je najviše kriva. Validacijski skupovi imaju 24 i 60 primjera, pa su apsolutni brojevi samo okvirno usporedivi. Skripta usto sprema samo završni adapter, pa težine s koraka 40 više ne postoje. Na pravom treningu spremaj međutočke.

### Veličina adaptera

| r  | Parametara | Adapter (bajtova) | MB   |
|---:|-----------:|------------------:|-----:|
| 4  | 460 800    | 1 874 312         | 1,87 |
| 8  | 921 600    | 3 717 656         | 3,72 |
| 16 | 1 843 200  | 7 404 368         | 7,40 |

Ovaj je adapter spremljen u FP32, dakle 4 bajta po parametru: 921 600 × 4 = 3 686 400 bajtova, plus oko 31 kB zaglavlja. Tablica u poglavlju 15 računa 2 bajta po parametru, pa 42 milijuna parametara za 8B uz r = 16 tamo daje 84 MB, a u FP32 dalo bi 168 MB. Obje su brojke točne za svoj format, pa uz svaku veličinu adaptera navedi i tip podataka.

### Prije i poslije

| Faza    | Skup        | Valjan JSON | Točnost po polju | Cijeli zapisnik |
|---------|-------------|------------:|-----------------:|----------------:|
| prije   | zlatni (40) | 0/40        | 0,0 %            | 0/40            |
| prije   | val (30)    | 0/30        | 0,0 %            | 0/30            |
| poslije | zlatni (40) | 39/40       | 43,8 %           | 5/40            |
| poslije | val (30)    | 30/30       | 81,7 %           | 15/30           |

Ovo je bazni model prije treninga, doslovno, s prelomljenim dugim retkom:

```text
Iz zapisnika izvuci JSON s poljima uredaj, kvar, dio, hitnost.
Klijentica, kučenje, kučenje, kučenje, kučenje, kučenje, kučenje,
  kučenje, kučenje, kučenje, kučenje, kučen
Nikoljak, začtěte, že jsem se začtěte, že měl jsem se začtěte, že
  měl jsem se začtěte, že mě
```

Ponavlja sistemsku poruku, petlja i prelazi na češki. Nakon treninga, na zlatnom skupu, s brojem točnih polja od četiri na početku:

```text
3 {"uredaj": "zamrzivač", "kvar": "curi voda", "dio": "brtva",
   "hitnost": "visoka"}
0 {"uredaj": "peščenici", "kvar": "ne pali se", "dio": "motorči",
   "hitnost": "visoka"}
1 {"uredaj": "gospa", "kvar": "curi voda", "dio": "termostat",
   "hitnost": "visoka"}
```

Model je naučio oblik: ključeve, njihov redoslijed, JSON i kraj odgovora. "peščenici" dolazi iz adrese, a "gospa" iz načina obraćanja. Takvih riječi u sintetičkom treningu nema, pa je jaz između 81,7 % na validaciji i 43,8 % na zlatnom skupu cijena podataka koji ne liče na stvarnost. Greška je ona ista iz poglavlja 14.

**Ovo dokazuje samo mehanizam, kvalitetu još ne.** Oblik je naučen, a Kvakin cilj od 90 % točnosti po polju ovaj model ne doseže ni izdaleka. Cilj nije dosegnut ni na jednom izmjerenom modelu: najbolja je Gemma 4 E2B sa shemom i bez treninga, sa 74,4 %. Ni ta usporedba nije čista jer je Gemma dobila punu sistemsku poruku s dopuštenim vrijednostima. Na 40 primjera jedno polje vrijedi 0,625 boda, pa male razlike ništa ne znače.

## Razina 2: cijeli lanac `CPU`

Slijedi redoslijed iz poglavlja 15. Simulator nikad nije bio u NF4, pa je pravilo o punoj preciznosti ovdje ispunjeno samo po sebi. Spajanje nakon pravog QLoRA treninga nije isprobano i o njemu piše razina 3.

::: {.vjezba}
**Vježba: od adaptera do GGUF-a** `CPU` · RAM 16 GB · disk 2 GB · 5 min

Pojedini koraci su niže, a sve ih redom izvodi `bash skripte/l9_lanac.sh` (samo Git Bash na Windowsu).
:::

### Spajanje

```bash
python -X utf8 skripte/l9_spoji.py models/SmolLM2-135M-Instruct \
  models/l9/glavni models/l9/spojeno
```

```text
nakon spajanja, klasa: LlamaForCausalLM lora tenzora: 0
         373  chat_template.jinja
         945  config.json
         139  generation_config.json
 269,060,280  model.safetensors
   3,522,871  tokenizer.json
         471  tokenizer_config.json
```

Skripta učitava bazu u FP32, poziva `merge_and_unload()`, a zatim sprema u FP16. Provjeri dvije stvari. Lora tenzora mora biti nula, a `chat_template.jinja` mora biti tu. Datoteka odgovara računu 134 515 008 × 2 bajta plus zaglavlje, dakle model nije narastao ni za jedan parametar.

### Pretvorba i kvantizacija

```bash
python -X utf8 llama-src/llama.cpp-b12110/convert_hf_to_gguf.py \
  models/l9/spojeno --outtype f16 \
  --outfile models/l9/gguf/kvaka-F16.gguf
./llama/llama-quantize models/l9/gguf/kvaka-F16.gguf \
  models/l9/gguf/kvaka-Q4_K_M.gguf Q4_K_M 4
```

U logu pretvorbe traži redak `INFO:gguf.vocab:Setting chat_template to ...`. Ako ga nema, predložak nije prešao.

| Datoteka | Bajtova     | Bita po težini | Trajanje |
|----------|------------:|---------------:|---------:|
| F16      | 270 885 824 | 16,00          | 10,0 s   |
| Q8_0     | 144 810 944 | 8,51           | 1,6 s    |
| Q4_K_M   | 105 454 016 | 6,17           | 1,7 s    |
| Q2_K     | 88 201 664  | 5,14           | 0,9 s    |

### Vožnja

```bash
KRATKI="Iz zapisnika izvuci JSON s poljima uredaj, kvar, dio, hitnost."
P="Stranka zove, hladnjak ne hladi, sumnja na kompresor. Treba odmah."
./llama/llama-cli -m models/l9/gguf/kvaka-Q4_K_M.gguf -sys "$KRATKI" \
  -p "$P" -st -n 80 -c 2048 -t 4 --temp 0 --seed 1
```

```text
{"uredaj": "hladnjak", "kvar": "ne hladi", "dio": "kompresor",
 "hitnost": "srednja"}
[ Prompt: 351.7 t/s | Generation: 136.7 t/s ]
```

Tri polja izgledaju dobro. "Treba odmah" trebalo bi vjerojatno dati `visoka`, iako za ovaj zapisnik nema službenog odgovora. Jedan lijep odgovor ionako ne govori o točnosti, pa slijedi zlatni skup.

### Točnost kroz razine

```bash
python -X utf8 skripte/l8_tocnost.py models/l9/gguf/kvaka-Q4_K_M.gguf \
  "LoRA-SmolLM2-Q4_K_M" podaci logovi/l9_tocnost_server.txt \
  grafovi/tocnost_zlatni.csv --sustav-tekst "$KRATKI" \
  --max 70 --port 8095 --ispis 3
```

| Model                  | Način       | Točnost | Cijeli zapisnik | `kvar` |
|------------------------|-------------|--------:|----------------:|-------:|
| adapter, HF FP32       | bez sheme   | 43,8 %  | 5/40            | 19/40  |
| LoRA F16 (spojeni)     | shema       | 48,1 %  | 5/40            | 20/40  |
| LoRA Q8_0              | shema       | 45,6 %  | 5/40            | 19/40  |
| LoRA Q4_K_M            | shema       | 44,4 %  | 5/40            | 22/40  |
| LoRA Q4_K_M            | bez sheme   | 38,1 %  | 3/40            | 19/40  |
| LoRA Q2_K              | shema       | 25,6 %  | 0/40            | 3/40   |
| baza bez treninga, F16 | shema       | 16,9 %  | 0/40            | 5/40   |

Prvi redak mjeren je kroz Hugging Face generiranje, prije spajanja, a ostali kroz `llama-server` na istom skupu. Redak F16 pokrenut je naknadno istom skriptom, samo u načinu `shema`.

- **Q8_0 i Q4_K_M** ovdje se ne razlikuju: 1,2 boda su 2 polja od 160. Ni F16 se ne razlikuje bitno: 48,1 % prema 45,6 % su 4 polja od 160.
- **Q2_K** ruši model nejednako: `kvar` pada na 3/40, a `hitnost` ostaje 17/40. Ukupna brojka to skriva, pa gledaj i polja.
- **Bez sheme** na istom modelu ima 9 polja manje nego HF put (38,1 % prema 43,8 %). Mjerenje ne razdvaja koliko je u tome kvantizacija, a koliko razlika u putu.
- **Baza sa shemom** ima 16,9 %, a ne nulu, jer shema nameće dopuštene vrijednosti. Tri ispisana odgovora su sva `napa`, `ne izbacuje vodu`, `pumpa`, `niska`. Stvaran doprinos LoRA-e na GGUF putu zato je razlika između 16,9 % i 44,4 %.

### Pravilo: zlatni skup nakon svakog koraka

Svaki korak može tiho nešto pokvariti, a zlatni skup kaže na kojem. Ponovi ga na adapteru, nakon spajanja, nakon pretvorbe u F16 i nakon svake kvantizacije. Naknadno smo ta dva koraka i izmjerili. Spojeni F16 na zlatnom skupu daje 48,1 % (tablica gore). Logite smo usporedili na promptovima prvih 10 zapisnika zlatnog skupa (1214 tokena): model s adapterom (FP32) i spojeni model (spremljen u FP16, učitan u FP32) razlikuju se u logitima najviše za 0,09, srednji KL je 1,9 · 10^-6, a najvjerojatniji token isti je na svih 1214 položaja. Razlika nije nula, vjerojatno zbog zaokruživanja na FP16 pri spremanju, što nismo provjeravali.

Na svakom koraku provjeri i **predložak** (poglavlje 5). U našem je lancu preživio sve korake, ali to vrijedi samo za naše inačice. Provjeravaš tri mjesta: `chat_template.jinja` uz spojeni model, redak iz loga pretvorbe i ključ `tokenizer.chat_template` u GGUF-u (poglavlje 10). Sadržaj treba biti isti kao u treningu. Isto vrijedi za sistemsku poruku: adapter je učen sa skraćenom, pa je i llama-cli dobiva kroz `-sys`, a SmolLM2 bez nje umeće svoju.

### Adapter bez spajanja

Ovo je također stvarno pokrenuto:

```bash
python -X utf8 llama-src/llama.cpp-b12110/convert_lora_to_gguf.py \
  models/l9/glavni --base models/SmolLM2-135M-Instruct \
  --outfile models/l9/gguf/adapter.gguf --outtype f16
./llama/llama-cli -m models/l9/gguf/baza-F16.gguf \
  --lora models/l9/gguf/adapter.gguf -sys "$KRATKI" -p "$P" \
  -st -n 80 -c 2048 -t 4 --temp 0 --seed 1
```

Odgovor je bio identičan odgovoru spojenog modela Q4_K_M, uz generiranje 75,0 t/s, što nije usporedivo jer je ovdje baza F16. Tako na jednoj bazi možeš držati više adaptera, ali izmjeren je samo jedan prompt na F16 bazi. Adapter uz kvantiziranu bazu nije isproban, pa ga prije upotrebe izmjeri zlatnim skupom.

### Ponovna provjera sigurnosti

Fino podešavanje može oslabiti odbijanja, i to bez ikakve loše namjere. Qi i suradnici (2023., arXiv 2310.03693) pokazali su da sigurnost slabi i nakon treninga na običnim, bezazlenim podacima, iako manje nego na zlonamjernima. Autor to nije mjerio, a malen SmolLM2 ionako nije dobar ispit. Na stvarnom modelu isti popis pusti kroz bazu i kroz datoteku koju isporučuješ jer tražiš promjenu.

Kratak popis, oko 20 upita koje pišeš za svoj posao:

- **Odbijanja:** 5 do 10 zahtjeva koje bazni model odbija. Bilježi odbija li podešeni model još uvijek. Kod Kvake je zamka što model naviknut na JSON može odgovoriti JSON-om na sve, pa taj oblik zasebno brojiš.
- **Izvan posla:** poruke koje nisu zapisnik. Izmišlja li model uređaj i kvar?
- **Podmetanje:** zapisnik koji sadrži naredbu za model (poglavlje 13).
- **Curenje:** pitanja o imenima, adresama i telefonima iz skupa za trening. Model koji ih vrati ne ide dalje.

Ako baza odbije, a podešeni model odgovori, zaustavi isporuku dok ne doznaš zašto. Namjerno uklanjanje odbijanja (abliteracija) poglavlje 17 spominje samo kao pojam, a ovdje ga nema.

## Razina 3: pravi trening `najam GPU-a`

Na ovoj razini ništa nije pokrenuto. Stanje alata je 5. 11. 2026., prema dokumentaciji i izvornom kodu: Axolotl v0.21.1 (27. 10. 2026.), Unsloth 2026.11.2 (4. 11. 2026.). Prije plaćanja provjeri ključeve za svoju inačicu.

### Izbor alata

|           | Unsloth | Axolotl | TRL i PEFT |
|-----------|---------|---------|------------|
| Rad       | Python, bilježnice | YAML i naredbe | vlastiti kod |
| Za što    | jedan GPU, brz početak | više kartica, ponovljivi pokusi | puna kontrola, DPO, GRPO |
| Hardver   | GPU ili Mac; CPU ne trenira | NVIDIA ili AMD; Python ≥ 3.12 | sve što PyTorch podržava |
| Slabost   | više kartica uz ručno postavljanje | puno ključeva | sve pišeš sam |

Prvi put uzmi Unsloth ako radiš u bilježnici, a Axolotl ako želiš jednu datoteku koja opisuje cijeli pokus. Tvrdnja "ne radi na CPU-u" vrijedi za Unsloth: naš simulator je običan PEFT, pa LoRA na CPU-u radi, samo sporo.

### Što unajmiti i koliko plaćaš

**VRAM:** računica iz poglavlja 15 za 8B uz r = 16 daje oko 4,5 GB bez aktivacija, pa je polazište kartica od 8 do 12 GB. Tablica u dokumentaciji Unslotha (stanje 5. 11. 2026.) za 8B navodi 6 GB uz QLoRA i 22 GB uz 16-bitni LoRA, a sama upozorava da može trebati i više. Autor to nije izmjerio. Tijekom prvih koraka gledaj vršnu potrošnju i zapiši je.

**Disk i RAM:** računaj bazu dva puta (preuzimanje i spojeni model), međutočke i GGUF datoteke. Spajanje drži punu bazu u memoriji, za 8B oko 16 GB, što smije biti običan RAM.

**Podaci:** pravi zapisnici sadrže imena, adrese i telefone. Nikad ih ne učitavaj na tuđi stroj bez provjere uvjeta pružatelja, lokacije podataka i pravne osnove (ovo nije pravni savjet). Najprije testiraj na sintetičkom skupu, stvarne podatke očisti prema poglavlju 14, a na kraju obriši disk. Axolotl usto šalje anonimnu telemetriju, a dokumentacija kaže da osobne podatke ne skuplja. Pročitaj njegovu stranicu Telemetry.

**Trošak:** cijene ovdje ne navodimo jer se stalno mijenjaju. Računaj sam, prema cijeni koju vidiš pri najmu:

```text
koraka  = epohe × primjera / (batch × akumulacija)
sati    = priprema + pokušaja × koraka × s_po_koraku / 3600
          + spajanje i testiranje
trošak  = sati × cijena_sata + disk
```

Za Kvaku je to 3 × 240 / 8 = 90 koraka. Vrijeme po koraku izmjeri na prvih 20 koraka jer laptopovih 5,1 s vrijedi samo za ovaj model i ovaj stroj. Računaj s više pokušaja jer prvi rijetko uspije. Provjeri naplaćuje li se stroj dok stoji.

### Axolotl

```yaml
base_model: <repo_modela>
revision_of_model: <hash_commita>
chat_template: tokenizer_default

load_in_4bit: true
adapter: qlora
lora_r: 16
lora_alpha: 32
lora_dropout: 0.05
lora_target_modules:   # imena provjeri u popisu tenzora
  - q_proj
  - k_proj
  - v_proj
  - o_proj
  - gate_proj
  - up_proj
  - down_proj

datasets:
  - path: podaci/train.jsonl
    ds_type: json
    type: chat_template
    field_messages: messages
val_set_size: 0
test_datasets:
  - path: podaci/val.jsonl
    ds_type: json
    type: chat_template
    field_messages: messages
    split: train
dataset_prepared_path: izlaz/pripremljeno

sequence_len: 1024
micro_batch_size: 2
gradient_accumulation_steps: 4
num_epochs: 3
optimizer: adamw_bnb_8bit
lr_scheduler: cosine
learning_rate: 0.0002
warmup_ratio: 0.1
bf16: auto
gradient_checkpointing: true

logging_steps: 1
evals_per_epoch: 4
saves_per_epoch: 2
seed: 42
output_dir: izlaz/kvaka-qlora
merge_method: legacy
```

::: {.neprovjereno}
Autor ovu konfiguraciju nije pokrenuo jer traži GPU. Ključevi su provjereni 5. 11. 2026. prema referenci konfiguracije na docs.axolotl.ai i službenom primjeru `examples/llama-3/qlora-1b.yml`. Vrijednost `split: train` za lokalni JSON zaključak je autora, a ne primjer iz dokumentacije. Provjeri sve za svoju inačicu.
:::

Tri ključa zaslužuju objašnjenje, a četvrti, `merge_method`, ima vlastiti odlomak niže.

- **`load_in_4bit`.** Poglavlje 15 kaže da je taj argument uklonjen iz `from_pretrained` u Transformersu v5. U Axolotlu on ostaje ključ YAML-a. Axolotl iz njega sam gradi `BitsAndBytesConfig` (NF4, dvostruka kvantizacija) i predaje ga kao `quantization_config`. Ključa `quantization_config` u YAML-u nema, a promjene idu kroz `bnb_config_kwargs`.
- **`type: chat_template`.** Zamjenjuje stari `sharegpt`. Stariji primjeri koriste `message_field_role` i `message_field_content`, a izvorni kod ih označava zastarjelima u korist `message_property_mappings`. U našim su podacima zadani nazivi `role` i `content`, pa ništa od toga ne treba.
- **`roles_to_train` i `train_on_eos`.** Zadano je `["assistant"]` i `turn`. Gubitak se računa na odgovoru i na tokenu kraja, kao u simulatoru.

Prije plaćenog treninga pogledaj kako primjeri stvarno izgledaju:

```bash
pip install "axolotl==0.21.1"
pip freeze > logovi/inacice.txt
axolotl preprocess kvaka.yml --debug --debug-num-examples 5
axolotl train kvaka.yml 2>&1 | tee logovi/trening.txt
axolotl merge-lora kvaka.yml --lora-model-dir="izlaz/kvaka-qlora"
```

::: {.neprovjereno}
Autor ove naredbe nije pokrenuo. Preuzete su iz dokumentacije CLI-ja za v0.21.1. Spojeni model treba biti u `izlaz/kvaka-qlora/merged`.
:::

**Zamka kod spajanja.** Pravilo iz poglavlja 15 glasi: baza pune preciznosti plus adapter. Izvorni kod Axolotla v0.21.1 po zadanom koristi metodu `memory_efficient`, koja kod QLoRA-e težine baze najprije propušta kroz NF4 i natrag, da oponaša ono što je adapter vidio u treningu. Metoda `legacy` učitava bazu bez 4 bita i zove `merge_and_unload`, što odgovara našem pravilu. Zato stoji u YAML-u. Autor nije usporedio te dvije metode i ne zna koja daje bolji model. Ako ti je rezultat važan, spoji na oba načina i presudi zlatnim skupom. Dalje ide lanac iz razine 2, od `convert_hf_to_gguf.py` nadalje.

### Unsloth

```python
from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig

model, tok = FastLanguageModel.from_pretrained(
    model_name="modeli/baza",   # mapa preuzeta s --revision
    max_seq_length=1024,
    load_in_4bit=True,
)
model = FastLanguageModel.get_peft_model(
    model, r=16, lora_alpha=32, lora_dropout=0.05, bias="none",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    use_gradient_checkpointing="unsloth",
    random_state=42, max_seq_length=1024,
)

def u_tekst(red):
    return {"text": tok.apply_chat_template(
        red["messages"], tokenize=False,
        add_generation_prompt=False)}

ds = load_dataset("json", data_files={
    "train": "podaci/train.jsonl", "val": "podaci/val.jsonl"})
ds = ds.map(u_tekst)
print(ds["train"][0]["text"])   # pogledaj prije treninga

trainer = SFTTrainer(
    model=model, processing_class=tok,
    train_dataset=ds["train"], eval_dataset=ds["val"],
    args=SFTConfig(
        max_length=1024, output_dir="izlaz/kvaka",
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        num_train_epochs=3, learning_rate=2e-4, warmup_steps=9,
        optim="adamw_8bit", logging_steps=1, seed=42,
        eval_strategy="steps", eval_steps=15,
        save_strategy="steps", save_steps=15,
        save_total_limit=3, dataset_num_proc=1,
    ),
)
trainer.train()

model.save_pretrained("izlaz/adapter")
tok.save_pretrained("izlaz/adapter")
model.save_pretrained_merged("izlaz/spojeno", tok,
                             save_method="merged_16bit")
```

::: {.neprovjereno}
Autor ovaj primjer nije pokrenuo jer trening u Unslothu traži GPU. Pozivi su sastavljeni 5. 11. 2026. iz vodiča na unsloth.ai/docs, ali kao cjelina nisu isprobani. Nazivi `processing_class` i `max_length` slijede dokumentaciju TRL-a v1.17.1, a stariji vodiči mogu pisati `tokenizer` i `max_seq_length`. Inačicu prikvači s `pip install "unsloth==2026.11.2"`.
:::

Unsloth ima i `save_pretrained_gguf` s `quantization_method="q4_k_m"`, jednu naredbu umjesto tri. Dokumentacija ne kaže spaja li `merged_16bit` u bazu pune preciznosti, pa to ne uzimaj zdravo za gotovo. Vlastiti lanac je bolji za prvi put jer između koraka možeš mjeriti. U ispisu provjeri i da se početni token nije udvostručio.

### Što sačuvati

Najmljeni stroj nestaje. Na vlastiti disk spremi:

- YAML ili skriptu, ispis `pip freeze`, hash revizije baze i hash podataka;
- cijeli log treninga, iz kojeg crtaš krivulje;
- adapter (završni i najbolji po validaciji) s tokenizatorom i predloškom;
- rezultat zlatnog skupa i sigurnosnu provjeru za svaki korak lanca.


### Kontrolni popis za pokretanje

Prije najma:

1. Zlatni skup izmjeren je na bazi bez treninga, uz najbolji prompt (poglavlje 13).
2. Pravi podaci smiju na taj stroj, ili koristiš sintetičke.
3. Izračunat je trošak za planirani broj pokušaja.

Na stroju, prije plaćenog treninga:

4. Inačice su prikvačene, a `pip freeze` je spremljen.
5. Pogledan je jedan primjer kao čisti tekst, s jednim početnim tokenom i s tokenom kraja.
6. Broj parametara koji se treniraju ima smisla.
7. Probno pokretanje od 20 koraka: gubitak pada, a izmjereni su vrijeme po koraku i vršni VRAM. U `nvidia-smi` gledaj `--query-gpu=memory.used --format=csv -l 5`.

Nakon treninga:

8. Krivulje su pročitane, a izabrana je točka prema validaciji.
9. Adapter, spojeni model i kvantizirani model prošli su zlatni skup.
10. Predložak je isti, a sigurnosna provjera ponovljena na završnoj datoteci.
11. Sve je spremljeno na tvoj disk, a stroj je ugašen i disk obrisan.

::: {.kvar}
**Simptom → uzrok**

- Trening nisko, validacija ravna visoko → prenaučenost, i bez krivulje U. Uzmi raniju točku, dodaj podatke, smanji r ili epohe.
- Val odličan, zlatni skup slab → podaci ne liče na stvarnost (81,7 % prema 43,8 %). Popravljaj podatke, ne postavke.
- Valjan JSON, a vrijednosti besmislene → brojač JSON-a ne mjeri značenje. Gledaj točnost po polju.
- Na adapteru dobro, nakon GGUF-a loše → predložak se izgubio ili je sistemska poruka drukčija. Usporedi čisti tekst prompta.
- Pad samo nakon niske kvantizacije → previše agresivna razina, kao Q2_K. Probaj Q4_K_M ili Q8_0.
- Spojeno daje drukčije nego adapter → pogrešna revizija baze ili metoda spajanja. Provjeri hash i `merge_method`.
- Model ne staje → token kraja nije bio u treningu ili je drugi u posluživanju.
- `OOM` na najmljenoj kartici → smanji `sequence_len` i batch (ostalo u poglavlju 15).
:::

## Što bi Kvaki trebalo za 90 %

Ovo je neizmjerena procjena i ništa ne obećava.

**Stvarni podaci prije svega.** Najveći izmjereni jaz je onaj između sintetičke validacije i zlatnog skupa, 81,7 % prema 43,8 %. Trebaju pravi zapisnici s adresama, obraćanjima, kraticama i pogreškama, označeni pažljivo i složeni prema poglavlju 14, vjerojatno nekoliko puta više od 240 primjera. `hitnost` je najslabija i kod Gemme (26/40), a tu ni ljudi možda nemaju jasno pravilo. Bez dogovorene definicije nijedan model neće sustići oznake.

**Veća baza.** SmolLM2 s 135 milijuna parametara u bazi na hrvatsko pitanje petlja i prelazi na češki. Gemma 4 E2B bez ikakvog treninga daje 74,4 %. Razuman sljedeći pokus je QLoRA na bazi takve veličine, na najmljenom GPU-u, uz shemu iz poglavlja 13, jer shema jamči oblik i LoRA više ne mora učiti JSON. Do 90 % na 160 polja treba 144 točna, a Gemma ih ima 119. Tih 25 polja uglavnom su pogreške značenja, gdje LoRA ima najmanje jamstva (poglavlje 15).

**Plan izlaza.** Moguće je da ni tada cilj ne bude dosegnut. Onda treba odlučiti: niži cilj, ljudska provjera nesigurnih zapisnika ili napuštanje ideje. Provjeri i latenciju: Gemma na ovom laptopu ima p95 od 6,7 s, iznad cilja od 5 s.

## Sažetak

Simulator na SmolLM2 stvarno je pokrenuo LoRA trening na CPU-u, u 1531 s za 921 600 parametara, i pokazao da se oblik uči dok vrijednosti ostaju loše: 43,8 % na zlatnom skupu, daleko od Kvakinih 90 %. Prenaučenost se pojavila kao golem jaz (0,0011 prema 0,59) uz gotovo ravnu validaciju, a krivulja U nije se pojavila. Lanac od spajanja preko GGUF-a do kvantizacije radi, a Q4_K_M i Q8_0 tu su jednaki, dok Q2_K ruši model. Nakon svakog koraka ponovi zlatni skup i provjeri predložak, a na kraju i sigurnost. Pravi trening na najmljenom GPU-u ostaje neprovjeren kod autora, pa prije plaćanja prikvači inačice, pogledaj podatke kao tekst i izmjeri prvih 20 koraka.
