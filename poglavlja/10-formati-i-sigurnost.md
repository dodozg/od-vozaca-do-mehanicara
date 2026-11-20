# Formati i sigurnost

::: {.cilj}
**Nakon ovog poglavlja znaš:**

- zašto je pickle program, a safetensors i GGUF podaci
- pročitati zaglavlje safetensors datoteke bez učitavanja težina
- gdje opasnost ostaje i u sigurnim formatima i kako provjeriti model prije pokretanja
- gdje držati modele i kako očistiti cache
:::

U poglavlju 9 izabereš model. Prije preuzimanja ostaje pitanje što zapravo stiže na tvoj disk.

Datoteka modela je jedno od dvoje: podaci ili program. Podatke tvoj alat samo čita. Program se izvršava s tvojim ovlastima, pa može čitati tvoje datoteke, uzeti pristupne tokene i otvoriti mrežnu vezu. Modele preuzimaš od ljudi koje ne poznaješ, pa ova razlika dolazi prije svih ostalih.

## Pickle: datoteka koja je program

Pickle je Pythonov način da se bilo koji objekt spremi u datoteku i kasnije vrati. Da bi mogao vratiti bilo što, pickle ne sprema samo vrijednosti. Sprema niz uputa za ponovnu izgradnju objekta, a jedna vrsta upute glasi "pozovi ovu funkciju s ovim argumentima". Učitati pickle znači izvršiti te upute.

PyTorch je dugo spremao težine upravo tako. Pickle prepoznaješ po nastavcima `.bin`, `.pt`, `.pth`, `.ckpt` i `.pkl`. Ovih nekoliko redaka pokazuje problem bezopasnom funkcijom `print`:

```python
import pickle

class Zamka:
    def __reduce__(self):
        return (print, ("Ovaj tekst ispisao je kod iz datoteke.",))

bajtovi = pickle.dumps(Zamka())
print("Datoteka je spremna. Slijedi pickle.loads:")
pickle.loads(bajtovi)
```

```text
Datoteka je spremna. Slijedi pickle.loads:
Ovaj tekst ispisao je kod iz datoteke.
```

Na mjestu funkcije `print` može stajati bilo koja funkcija. To se događa i u stvarnosti. U veljači 2024. JFrog je objavio da je na Hugging Faceu pronašao oko stotinu modela koji pri učitavanju izvršavaju kod. Prema JFrogu većina tih sadržaja izgleda kao pokušaji istraživača i lovaca na nagrade za pronađene propuste, a ne kao stvarni napadi. Opisani primjer `baller423/goober2` ipak je pri učitavanju kroz `__reduce__` otvarao obrnutu ljusku (reverse shell) prema stvarnoj IP adresi: računalo žrtve samo se spaja na tuđi poslužitelj i predaje mu naredbeni redak. Među pronađenim modelima PyTorch je bio najzastupljeniji.

Skeneri pomažu, ali ne daju jamstvo. Hugging Face pregledava pickle datoteke i prikazuje popis onoga što uvoze, a sumnjive označava bez zabrane preuzimanja. U vlastitoj dokumentaciji piše da provjera nije stopostotna. PickleScan se može zaobići: ReversingLabs je 2025. opisao namjerno oštećene pickle datoteke koje je skener propuštao, a Python ih izvršava redom sve do mjesta oštećenja. Novije inačice PyTorcha zadano učitavaju s ograničenjem `weights_only=True`, ali i ono je imalo kritičan propust (CVE-2025-32434, do inačice 2.5.1), a dokumentacija i dalje upozorava da se ne učitavaju podaci iz nepouzdanog izvora.

Čist izvještaj skenera ne dokazuje da je pickle siguran, pa tuđi pickle ne učitavaj na svom računalu.

## Safetensors: samo podaci

Safetensors obavlja isti posao bez ijedne upute za izvršavanje. Datoteka ima tri dijela:

```text
[8 bajtova: duljina N] [N bajtova: JSON zaglavlje] [sirovi bajtovi]
```

Zaglavlje je običan JSON. Za svaki tenzor navodi tip brojeva, oblik i gdje mu u bloku bajtova počinju i završavaju podaci. Neobvezni ključ `__metadata__` smije sadržavati samo tekst. Ostatak su brojevi iz poglavlja 7, jedan do drugoga.

Iz toga slijede dvije praktične prednosti:

- **Mapiranje u memoriju (mmap).** Operacijski sustav prikaže datoteku programu kao da je već u memoriji, a s diska stvarno čita samo dijelove koje program dira.
- **Lijeno čitanje.** Iz zaglavlja znaš gdje je tenzor, pa možeš pročitati jedan i preskočiti sve ostale.

::: {.vjezba}
**Vježba: pročitaj zaglavlje bez težina** `CPU` · RAM 1 GB · disk 3 MB · 10 min

Treba ti samo Python, bez dodatnih paketa. Prvo ručno složi malu datoteku (`stvori.py`):

```python
import json, struct

prvi = struct.pack("<6f", 1, 2, 3, 4, 5, 6)     # 6 x 4 = 24 bajta
drugi = struct.pack("<2f", 0.5, 0.25)           # 2 x 4 = 8 bajtova
zaglavlje = {
    "__metadata__": {"format": "pt"},
    "sloj.tezine": {"dtype": "F32", "shape": [2, 3],
                    "data_offsets": [0, 24]},
    "sloj.pomak": {"dtype": "F32", "shape": [2],
                   "data_offsets": [24, 32]},
}
z = json.dumps(zaglavlje).encode("utf-8")
with open("mali.safetensors", "wb") as f:
    f.write(struct.pack("<Q", len(z)) + z + prvi + drugi)
```

Zatim pročitaj samo zaglavlje (`citaj.py`):

```python
import json, struct, sys

with open(sys.argv[1], "rb") as f:
    duljina = struct.unpack("<Q", f.read(8))[0]
    zaglavlje = json.loads(f.read(duljina))

for ime, t in zaglavlje.items():
    if ime != "__metadata__":
        od, do = t["data_offsets"]
        print(ime, t["dtype"], t["shape"], do - od, "bajtova")
```

```text
$ python citaj.py mali.safetensors
sloj.tezine F32 [2, 3] 24 bajtova
sloj.pomak F32 [2] 8 bajtova
```

Isti kod radi na pravom modelu. U bashu preuzmi samo prva 2 MB drugog dijela SmolLM3:

```bash
B=https://huggingface.co/HuggingFaceTB/SmolLM3-3B/resolve/main
curl -sL -r 0-2097151 "$B/model-00002-of-00002.safetensors" \
  -o pocetak.bin
python citaj.py pocetak.bin
```

```text
model.layers.28.input_layernorm.weight BF16 [2048] 4096 bajtova
model.layers.28.mlp.down_proj.weight BF16 [2048, 11008] 45088768 bajtova
model.layers.28.mlp.up_proj.weight BF16 [11008, 2048] 45088768 bajtova
model.layers.28.post_attention_layernorm.weight BF16 [2048] 4096 bajtova
```

Skripta ispiše 68 redaka, a prikazana su prva četiri. Provjeri račun iz poglavlja 7: 2048 × 11008 × 2 bajta = 45 088 768. Zaglavlje ovog dijela ima 7800 bajtova, a cijela datoteka 1,18 GB.

Za kraj dohvati jedan tenzor iz male datoteke:

```python
import json, struct

with open("mali.safetensors", "rb") as f:
    duljina = struct.unpack("<Q", f.read(8))[0]
    zaglavlje = json.loads(f.read(duljina))
    od, do = zaglavlje["sloj.pomak"]["data_offsets"]
    f.seek(8 + duljina + od)        # preskoči sve ostale težine
    print(struct.unpack("<2f", f.read(do - od)))
```

Ispisuje `(0.5, 0.25)`.
:::

### Model u više dijelova

Veliki model dolazi podijeljen na dijelove (shards), primjerice `model-00001-of-00002.safetensors`. Uz njih stoji `model.safetensors.index.json`, čiji `weight_map` za svaki tenzor kaže u kojem je dijelu. Ovako izgleda kod SmolLM3:

```json
{
  "metadata": {"total_size": 6150197248},
  "weight_map": {
    "model.embed_tokens.weight":
      "model-00001-of-00002.safetensors",
    "model.norm.weight":
      "model-00002-of-00002.safetensors"
  }
}
```

Isječak je skraćen jer indeks navodi svih 326 tenzora. Zbroj je 6,15 GB, raspoređen na dijelove od 4,97 GB i 1,18 GB.

Veličina dijela sama po sebi ne znači ništa. Starije inačice biblioteke Transformers dijelile su modele na komade od oko 5 GB, pa ih na Hubu vidiš posvuda. Transformers v5 pri spremanju zadano dijeli tek na 50 GB. Ako ručno mijenjaš tenzore (poglavlje 17), `weight_map` mora ostati točan jer ga alati slijede bez dodatne provjere.

## GGUF: sve u jednoj datoteci

Mapa modela iz poglavlja 3 praktična je za rad u Pythonu, ali program koji model samo pokreće želi manje. Zato je llama.cpp dobio vlastiti format: GGUF. Jedna datoteka sadrži težine, tokenizator, chat predložak i metapodatke (arhitektura, licenca, tko je kvantizirao). Dovoljna je da se model pokrene, a i ona se mapira u memoriju. Težine su najčešće kvantizirane, što učiš u poglavlju 11. Vrlo veliki GGUF modeli također dolaze u dijelovima (`-00001-of-00009.gguf`).

| | safetensors | GGUF |
|---|---|---|
| Tko ga koristi | Transformers, alati za trening, vLLM | llama.cpp, Ollama, LM Studio |
| Sadržaj | težine; ostalo je u mapi | težine, tokenizator, predložak, metapodaci |
| Preciznost | obično BF16 ili FP16 | obično kvantizirano |
| Namjena | mijenjanje, fino podešavanje, kvantizacija | pokretanje |

Pravilo je kratko: safetensors je za mijenjanje, GGUF za vožnju. Kvaka d.o.o. zato čuva izvorni safetensors za LoRA trening (poglavlja 15 i 16), a na servisnom računalu pokreće GGUF. Iz kvantiziranog GGUF-a izgubljena se preciznost ne može vratiti, pa izvornik ne briši dok ti možda još treba.

Tri oblika susrećeš u poslužiteljskom svijetu, a detalji su u poglavlju 18:

- **compressed-tensors:** kvantizirane težine u safetensors datotekama, s opisom kvantizacije u `config.json`.
- **AWQ:** stariji kvantizirani oblik za GPU; AutoAWQ je napušten, a vLLM takve modele i dalje učitava.
- **FP8 checkpoint:** 8-bitne težine sa skalama, za posluživanje na novijim NVIDIA karticama.

## Gdje opasnost ostaje

Safetensors i GGUF rješavaju jedan problem: čitanje težina ne izvršava kod. Tri druga puta ostaju otvorena.

### trust_remote_code=True

Neki repozitoriji uz težine nose vlastiti Python, obično `modeling_*.py` i `configuration_*.py`, na koje upućuje `auto_map` u `config.json`. Argument `trust_remote_code=True` kaže biblioteci Transformers da taj kod preuzme i izvrši, s tvojim ovlastima i bez ikakve izolacije. Težine pritom mogu biti savršeno čist safetensors.

To je ponekad opravdano: nova arhitektura izlazi prije nego što je Transformers dobije. Zato prvo provjeri treba li ti uopće taj argument, jer novija inačica biblioteke možda već podržava model. Ako treba:

1. Preuzmi repozitorij bez učitavanja i pročitaj te `.py` datoteke. Sumnjivi su mrežni pozivi, `subprocess`, `eval`, `exec`, kodirani nizovi i pisanje izvan mape modela.
2. Provjeri upućuje li `auto_map` na neki drugi repozitorij. Onda čitaš i njega.
3. Prikvači reviziju (pin) na točan commit. Commit je jedan zapis u povijesti repozitorija, a prepoznaješ ga po hashu od 40 znakova. Naziv `main` pokazuje na zadnji commit, pa sutra može izvršiti nepročitan kod.

```python
from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained(
    "organizacija/model",
    trust_remote_code=True,
    revision="<hash commita koji je pročitan>",
)
```

::: {.neprovjereno}
Autor ovaj primjer nije pokrenuo jer traži PyTorch i pravi model s vlastitim kodom. Provjeri inačice alata.
:::

Pazi i na pretvorbu u GGUF iz poglavlja 11. Sam llama.cpp ne izvršava Python iz repozitorija, ali skripta za pretvorbu za neke arhitekture učitava tokenizator uz `trust_remote_code=True`. Nepoznat model pretvaraj u izoliranom okruženju.

### Logika u chat predlošku

U poglavlju 5 vidiš da je predložak mali program u Jinji koji se izvršava pri svakom pozivu. Rad Fogela i suradnika (arXiv 2602.04653, radionica ICLR 2026) pokazuje što to znači za sigurnost. Autori u postojeći predložak dodaju kratak uvjet: ako se u poruci korisnika pojavi određena fraza, predložak umetne skrivenu sistemsku uputu. Težine ostaju netaknute, a bez fraze model radi kao prije. Na 18 modela točnost odgovora uz okidač pala je u prosjeku s 90 % na 15 %, a uspješnost ubacivanja napadačeva URL-a prelazila je 80 %. Autori navode da su takvi GGUF modeli, privremeno postavljeni na Hugging Face, prošli automatske sigurnosne provjere.

Provjere koje možeš obaviti prije stavljanja modela u pogon:

- **Izvuci predložak.** Hub ima preglednik metapodataka GGUF datoteke (ključ `tokenizer.chat_template`), a `llama-server` ga vraća u polju `chat_template` na `GET /props`.
- **Usporedi ga s izvornikom.** Izvornik je u `chat_template.jinja` ili `tokenizer_config.json` službenog repozitorija. Razlika postoji i kad je sve u redu, jer kvantizatori katkad popravljaju predložak. Zato svaku razliku pročitaj.
- **Traži sumnjive uzorke.** To su uvjeti koji provjeravaju sadržaj korisnikove poruke, ugrađene rečenice s uputama, URL-ovi, HTML komentari i Base64 nizovi.
- **Zamijeni ga.** `llama-server --chat-template-file izvornik.jinja` zaobilazi predložak iz datoteke.

Predložak utječe na to što model kaže, a kod agenata i na to što model radi. Takav model tehničaru Kvake može mirno predložiti pogrešan dio ili zlonamjernu poveznicu. Postoji i stariji propust: llama-cpp-python prije inačice 0.2.72 izvršavao je predložak bez izolacije, pa je GGUF mogao pokrenuti kod (CVE-2024-34359). Alate zato drži ažuriranima.

### Kopije i slična imena

Na Hub svatko može postaviti model. Kopija iz zajednice može imati prepisanu karticu modela, uvjerljiv naziv i mnogo preuzimanja, a ništa od toga ne govori o sadržaju. Napadači mogu koristiti i imena s jednim promijenjenim slovom. Unit 42 je u rujnu 2025. opisao i suptilniji put: ime obrisanog računa može ponovno registrirati netko drugi, pa stari put `autor/model` odjednom vodi na njegov repozitorij.

Do službenog repozitorija dođi preko stranice proizvođača, jer tražilica lako ponudi pogrešnu kopiju. Kad netko tvrdi da je njegov safetensors kopija izvornika, usporedi SHA256 sažetke: jednak sažetak znači iste bajtove. Kod kvantiziranih GGUF-ova usporedba težina nije moguća, pa biraš poznatog kvantizatora i čitaš predložak.

## Higijena: kratak popis

- **Izvor:** službena organizacija ili poznat kvantizator.
- **Revizija:** `revision` prikvačen na hash commita, i u kodu i pri preuzimanju.
- **Sažetak:** SHA256 sa stranice datoteke na Hubu jednak je onom na tvom disku.
- **Bez picklea:** preuzimaj samo safetensors ili GGUF.
- **Izolacija:** kad sumnjaš, pokreni u virtualnom stroju ili kontejneru bez mreže i bez svojih tokena.
- **Izvanmrežni rad:** nakon preuzimanja `HF_HUB_OFFLINE=1` ili `llama-server --offline`. To sprječava da alati tiho dohvate novu inačicu, ali ne zaustavlja zlonamjeran kod. Za to služi izolacija iz prethodne stavke.

```bash
hf download unsloth/gemma-4-E2B-it-GGUF \
  --revision <hash_commita> --include "*Q4_K_M*.gguf"
hf cache verify unsloth/gemma-4-E2B-it-GGUF --revision <hash_commita>
```

::: {.neprovjereno}
Autor naredbe `hf` u ovom poglavlju nije pokrenuo jer je modele preuzimao skriptom, bez Hub cachea. Sintaksa je prema dokumentaciji `huggingface_hub`, stanje u studenom 2026. Provjeri inačicu alata.
:::

Sažetak datoteke ručno računaš naredbom `sha256sum datoteka` na Linuxu ili `Get-FileHash datoteka` u PowerShellu. Na stranici datoteke na Hubu vrijednost stoji uz oznaku SHA256. Jednak sažetak dokazuje samo da imaš istu datoteku. O njezinoj bezopasnosti ne govori ništa.

## Disk

Stvarne veličine pomažu pri planiranju:

| Model | Oblik | Veličina |
|---|---|---|
| Qwen3-4B | GGUF Q4_K_M | 2,5 GB |
| Gemma 4 E2B | GGUF Q4_K_M | 3,11 GB |
| SmolLM3-3B | safetensors | 6,15 GB |
| Llama 3.1 8B | izvorno / Q4_K_M | 32,1 / 4,9 GB |
| Llama 3.1 70B | izvorno / Q4_K_M | 280,9 / 43,1 GB |
| Llama 3.1 405B | izvorno / Q4_K_M | 1625,1 / 249,1 GB |

Oznaku Q4_K_M objašnjava poglavlje 11. Repozitorij GGUF modela obično sadrži mnogo kvantizacija, pa preuzimaj jednu, kao u naredbi iznad.

Alati Hugging Facea spremaju preuzeto u cache, zadano `~/.cache/huggingface/hub`, na Windowsu `C:\Users\ime\.cache\huggingface\hub`. Lokaciju mijenjaš varijablom `HF_HOME`; cache je tada u `$HF_HOME/hub`. Ista mapa čuva i tvoj pristupni token. Ollama ima vlastitu lokaciju koju mijenjaš varijablom `OLLAMA_MODELS`, a LM Studio svoju mapu u postavkama.

```bash
export HF_HOME=/mnt/brzi-ssd/huggingface     # Linux, macOS
setx HF_HOME D:\huggingface                  # Windows, novi terminal
```

::: {.neprovjereno}
Autor ove naredbe nije pokrenuo da ne promijeni postavke računala na kojem se izvode mjerenja.
:::

### Modeli ne idu na sinkronizirani disk

Google Drive, OneDrive i Dropbox građeni su za dokumente. Datoteka od više desetaka GB na njima se ponaša loše:

- **Djelomična sinkronizacija:** datoteka se vidi, a na disku je samo zamjenski zapis ili njezin dio. Mapiranje u memoriju tada čita preko mreže ili pada.
- **Datoteke od 0 bajtova:** ime postoji, sadržaja nema, a alat javlja nerazumljivu grešku o neispravnom zaglavlju.
- **Sukobi:** dva računala stvore kopiju s dodatkom u imenu, pa `weight_map` pokazuje na staru datoteku.
- **Struktura cachea:** cache se oslanja na simboličke poveznice, koje sinkronizacija ne čuva pouzdano.
- **Token:** `HF_HOME` na sinkroniziranom disku šalje i tvoj token u oblak.

Modeli idu na lokalni SSD. Na sinkronizirani disk stavi kod, bilješke i popis preuzetih modela s hashom commita, jer se time model uvijek može ponovno preuzeti.

### Pregled i čišćenje

Cache sam od sebe ne briše ništa: kad preuzmeš noviju reviziju, stara ostaje. Stanje u studenom 2026.:

```bash
hf cache ls                     # repozitoriji i veličine
hf cache ls --revisions         # svaka revizija zasebno
hf cache rm model/organizacija/model --dry-run
hf cache prune --dry-run        # stare revizije, prekinuta preuzimanja
hf cache verify organizacija/model
```

::: {.neprovjereno}
Autor ove naredbe nije pokrenuo jer je modele preuzimao skriptom, bez Hub cachea. Bez `--dry-run` naredbe stvarno brišu.
:::

Na Windowsu bez uključenog načina za razvojne programere (Developer Mode) cache radi bez simboličkih poveznica, pa ista datoteka iz dviju revizija zauzima dvostruko više mjesta.

::: {.kvar}
**Simptom → uzrok**

- Greška o neispravnom zaglavlju, datoteka ima 0 B ili je premala → prekinuto preuzimanje ili sinkronizacija. Pokreni `hf cache verify`, zatim preuzmi ponovno na lokalni disk.
- Disk se puni, a koristiš jedan model → stare revizije i prekinuta preuzimanja u cacheu. Pokreni `hf cache ls --revisions`, zatim `hf cache prune`.
- Datoteka s dodatkom "(1)" ili "conflicted copy" u imenu → sukob sinkronizacije. Premjesti modele na lokalni disk.
- Traži se `trust_remote_code` → arhitektura nije u tvojoj inačici biblioteke. Ažuriraj Transformers ili pročitaj kod i prikvači reviziju.
- Isti naziv modela odjednom daje drukčije rezultate → `main` se pomaknuo. Prikvači reviziju na hash commita.
- Model griješi ili ubacuje poveznice samo uz neke fraze → sumnjiv predložak. Usporedi ga s izvornikom ili ga zamijeni.
- Repozitorij nudi samo `.bin` → pickle. Potraži safetensors inačicu ili ga pokreni samo u izolaciji.
:::

## Sažetak

Pickle pri učitavanju izvršava upute iz datoteke, pa tuđi `.bin` i `.pt` ne učitavaš izvan izolacije, a skener tu nije dovoljan. Safetensors sadrži JSON zaglavlje i sirove bajtove i služi za mijenjanje modela, dok GGUF u jednoj datoteci nosi sve za pokretanje. Opasnost ostaje u `trust_remote_code`, u logici chat predloška i u lažnim kopijama, a braniš se čitanjem koda, usporedbom predloška, prikvačivanjem revizije i provjerom SHA256 sažetka. Modeli idu na lokalni SSD, a cache pratiš i čistiš naredbama `hf cache`. U poglavlju 11 prvi put kvantiziraš model.
