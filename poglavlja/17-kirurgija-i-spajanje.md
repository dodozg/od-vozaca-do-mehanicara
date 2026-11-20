# Kirurgija i spajanje

::: {.cilj}
**Nakon ovog poglavlja znaš:**

- pregledati model tenzor po tenzor bez punjenja memorije
- dodati posebne tokene i ukloniti slojeve tako da nacrt i težine ostanu složni
- procijeniti što YaRN daje, a što ne
- spojiti modele Mergekitom i prepoznati kad rezultat nema smisla
:::

::: {.napomena}
**Izborna radionica.** Jezgra knjige završava poglavljem 16 i Kvaki ništa odavde nije potrebno. Ovo poglavlje čitaj ako želiš zahvate izravno na težinama ili ako naiđeš na model koji je netko tako izmijenio.
:::

Dosad je model dobivao novo znanje kroz trening. Kirurgija mijenja datoteku izravno: dodaje retke u tablicu, briše slojeve, računa s težinama dvaju modela. Takav zahvat traje sekundama, a često završi bez ikakve greške. U tome je opasnost, pa za svaki zahvat u ovom poglavlju vrijede dva pravila:

1. Radi na kopiji, a izvornik ne diraj.
2. Nakon zahvata pusti zlatni skup (poglavlje 9) i usporedi ga s rezultatom prije zahvata. Program koji nije pao ne govori ništa o kvaliteti.

Pokusi su izvedeni na laptopu i5-10210U sa 16 GB RAM-a i bez GPU-a, na modelu `SmolLM2-135M-Instruct`, uz Transformers 5.22.1 i Mergekit 0.1.5. Model je namjerno malen. Na svom stroju izmjeri svoje.

::: {.vjezba}
**Vježba: kirurgija na malom modelu** `CPU` · RAM 16 GB · disk 2 GB · 5 min

```bash
python -X utf8 skripte/l10_kirurgija.py \
  models/SmolLM2-135M-Instruct models/l10
```

Skripta je u `prilozi/vjezbe/l10_kirurgija.py`. Izvodi sva tri zahvata iz prvog dijela poglavlja i ispisuje rezultate koji slijede.
:::

## Sigurna inspekcija

Sjeti se poglavlja 7: jedan NaN dovoljan je da model prestane davati smislen izlaz. Treba dakle pregledati svaki broj, a da se pritom ne učita cijeli model.

Safetensors to omogućuje jer `safe_open` čita samo zaglavlje datoteke (poglavlje 10). Podaci tenzora stižu tek kad pozoveš `get_tensor`, i tada su stvarno u memoriji. Tu je zamka. Skripta koja svaki tenzor provjeri, a zatim ga ostavi u rječniku, na kraju drži cijeli model u RAM-u, iako je `safe_open` na početku djelovao štedljivo. Kod modela od 16 GB na stroju sa 16 GB to lako završi zamrzavanjem. Rješenje je jedno: tenzor pročitaj, provjeri i baci prije nego što uzmeš sljedeći.

Izvadak iz skripte, preformatiran za širinu stranice:

```python
los = []; najveca = (0, ""); najmanja = (math.inf, "")
with safe_open(datoteka, "pt") as f:
    for ime in f.keys():
        t = f.get_tensor(ime).float()
        nan = int(torch.isnan(t).sum())
        inf = int(torch.isinf(t).sum())
        nule = int((t == 0).sum())
        n = float(torch.linalg.vector_norm(t))
        if nan or inf or nule == t.numel():
            los.append((ime, nan, inf, nule))
        if n > najveca[0]: najveca = (n, ime)
        if n < najmanja[0]: najmanja = (n, ime)
        del t  # bez gomilanja
```

Četiri su provjere. NaN i Inf su pokvareni brojevi. Tenzor u kojem je sve nula najčešće znači izgubljene podatke. **L2 norma** je korijen iz zbroja kvadrata svih brojeva u tenzoru, dakle jedan broj koji kaže koliko je tenzor "velik". Izlaz na zdravom modelu:

```text
tenzora 272, 0.9 s, problematicnih 0: []
najveca L2 norma 720.19 model.embed_tokens.weight;
najmanja 0.96 model.layers.0.input_layernorm.weight
```

Normu uspoređuj samo među tenzorima iste vrste, primjerice `q_proj` kroz sve slojeve. Tablica `embed_tokens` velika je jer ima desetke tisuća redaka, a `input_layernorm` ima samo jedan niz brojeva, pa razlika 720 prema 0,96 sama po sebi nije kvar. Sumnjiv je jedan `q_proj` deset puta veći od ostalih.

Alat treba provjeriti i na nečemu što je pokvareno. Na kopiji u koju smo upisali jedan NaN i jedan tenzor nula pronašao je oba (razmaci skraćeni):

```text
model.layers.0.input_layernorm.weight  nan=1 sve_nule=False norma=0.96
model.layers.0.mlp.down_proj.weight    nan=0 sve_nule=True norma=0.00
```

Pogledaj prvi redak: norma je 0,96, jednaka kao kod zdravog tenzora, jer ovaj ispis prije računanja norme zamjenjuje NaN nulom. Bez te zamjene norma bi i sama bila NaN, a usporedbe `n > najveca` u izvatku gore tiho bi je preskočile. Ovako jedan pokvaren broj među mnogima normu gotovo ne pomakne, pa kvar otkriva brojač `nan`. Zato se ne oslanjaj na jednu provjeru.

## Novi posebni tokeni

Poglavlje 4 pokazuje da je token za model samo ID, a da svakom ID-ju odgovara redak u tablici. Kvaka bi mogla poželjeti oznake poput `<|kvaka_zapisnik|>` i `<|kvaka_kraj|>`, koje se nikad ne mogu pomiješati s običnim tekstom i uvijek zauzimaju po jedan token.

Prije zahvata pogledaj ima li model rezervirana mjesta. SmolLM3 ih ima (poglavlje 4), a tada nije potrebno mijenjati tablicu. SmolLM2 ih nema, pa smo mu dodali dva tokena:

```python
tok.add_special_tokens({"additional_special_tokens":
    ["<|kvaka_zapisnik|>", "<|kvaka_kraj|>"]})
m.resize_token_embeddings(len(tok))
```

Stvarni izlaz, redom kako ga skripta ispisuje:

```text
prije: len(tok) 49152 embed (49152, 576) lm_head (49152, 576)
  vezano True vocab_size 49152
dodano 2 len(tok) 49154 tokeni poslije: [49152, 456, 301, 4127, 49153]
BEZ resize_token_embeddings pada: IndexError index out of range in self
poslije: embed (49154, 576) lm_head (49154, 576) vocab_size 49154
norma stare zadnje retke 3.8968284130096436
norme novih redaka 2.1782994270324707 2.178276538848877
izlaz logita: torch.Size([1, 5, 49154])
```

Tokenizator je dobio ID-jeve 49152 i 49153, kojih u tablici još nema, pa bez proširenja model pada na `IndexError`. Taj je pad dobar jer odmah kaže što ne valja.

Mijenjaju se **dvije** tablice jer token ima dvije uloge. `embed_tokens` omogućuje da model token pročita, a `lm_head` da ga napiše: bez retka u glavi logiti nemaju mjesta za taj ID (poglavlje 6) i model ga nikad ne može izabrati. Kod SmolLM2 piše `vezano True`, što znači da obje uloge dijele jednu tablicu. Kod modela s odvojenim tablicama `resize_token_embeddings` proširuje obje.

**Novi redak ne zna ništa.** Transformers ga puni nasumičnim brojevima sličnima starim recima. Obje nove norme su 2,178, gotovo jednake, a stari je redak imao 3,897. Stari su reci naučeni, a novi su šum koji model ne razlikuje ni od čega. Oznaka počinje nešto značiti tek kad je trening vidi. Te dvije tablice zato moraš uključiti među ono što se uči, primjerice kroz `modules_to_save` u PEFT-u, pa adapter iz poglavlja 15 postaje znatno veći. Tu postavku nismo pokrenuli.

Još dvije stvari. Oznake moraju doći i u predložak i u podatke za trening (poglavlja 5 i 14). I pazi na format pri spremanju: skripta je model učitala u FP32, pa je spremljena datoteka imala 538 095 016 B, dvostruko više od izvornih 269 060 280 B. Učitaj model u `dtype` koji želiš zadržati.

## Uklanjanje slojeva

Manje slojeva znači manju datoteku. Iz modela s 30 slojeva izbacili smo gornjih šest. Svaki sloj ima devet tenzora (poglavlje 6), pa je od 272 ostalo 218, a datoteka je pala s 269 060 280 na 226 573 296 B, oko 16 %.

Slojevi se prepoznaju po nazivu tenzora, `model.layers.N.`, što je shema iz poglavlja 6. Ako brišeš iz sredine, moraš preimenovati sve slojeve iznad jer program očekuje neprekinut niz. Zato je brisanje s vrha jednostavnije.

### Iznenađenje: ne pada

Što se događa kad u novu mapu kopiramo stari `config.json`, koji i dalje tvrdi da je slojeva 30? Očekivali bismo grešku. `from_pretrained` je nije javio:

```text
model.layers.{24, 25, 26, 27, 28, 29}.self_attn.q_proj.weight | MISSING |
[...]
- MISSING: those params were newly initialized because missing from
  the checkpoint. Consider training on your downstream task.
  NIJE PALO. from_pretrained je vratio model s 30 slojeva;
  zadnji sloj je nasumicno inicijaliziran, |q_proj| = 0.0333
  izlaz: 'Zagreb je glavni grad 2.\n\n[ 2. 2. 2'
```

Dobiješ model s 30 slojeva od kojih je zadnjih šest šum, pa će se tvoj izlaz razlikovati: u ponovljenom pokretanju bio je `'Zagreb je glavni grad.\n\n[ 2017- 201'`. Jedini trag je izvještaj u logu, koji se lako izgubi među porukama učitavanja, a program nastavlja. To je slučaj najavljen u poglavlju 3. Strogo učitavanje isti kvar odmah hvata:

```text
-- a2) strogo ucitavanje load_state_dict(strict=True):
  PALO: RuntimeError Error(s) in loading state_dict for LlamaForCausalLM:
    Missing key(s) in state_dict:
    "model.layers.24.self_attn.q_proj.weight", [...]
```

Zato nakon svake ručne izmjene usporedi nacrt s težinama i čitaj izvještaj učitavanja. Svaki `MISSING` je kvar dok ne dokažeš suprotno.

Popravak je u `config.json`: `num_hidden_layers` mora biti 24. Skripta skraćuje i popis `layer_types` ako ga model ima, jer i on broji slojeve. Tada učitavanje javlja `slojeva 24 parametara 113,274,432`.

### Što to radi kvaliteti

Evo izlaza na istom promptu:

```text
popravljeni, 24 sloja: 'Zagreb je glavni grad.\n\n- 1. 2. 3. '
izvorni, 30 slojeva:  'Zagreb je glavni grad, kako se se nije uvedlje.\n'
```

Oba su izlaza besmislena, a izvorni je tek malo bolji jer je model malen i na hrvatskom slab i prije zahvata. Iz jednog prompta ne slijedi ništa o mjeri štete, a zlatni skup ovdje nismo pustili. Razlog za oprez je jednostavan: gornji slojevi nose dio obrade koji donji nisu naučili nadoknaditi, a bez treninga nitko ih to neće naučiti. Ovaj pokus pokazuje kako se zahvat izvodi, a dobar rezultat ne obećava. Ako želiš manji model, kvantizacija (poglavlje 11) ili manji model iz iste obitelji obično je bolji put.

### Model u više dijelova

Kod modela u više dijelova (poglavlje 10) izmjena ima još jedan korak. `model.safetensors.index.json` u `weight_map` navodi svaki tenzor i dio u kojem se nalazi, a alati mu vjeruju. Moraš obrisati retke uklonjenih tenzora, preimenovane upisati pod novim imenom, a `total_size` uskladiti sa zbrojem preostalih bajtova. Radi dio po dio: pročitaj jedan dio, zapiši novi, oslobodi memoriju. Naša skripta drži sve zadržane tenzore u rječniku prije spremanja, što kod 226 MB ne smeta, a kod velikog modela je upravo ona zamka s početka poglavlja. Taj postupak na modelu u više dijelova nismo pokrenuli.

## Dulji kontekst: YaRN

Poglavlje 6 uvelo je RoPE i `max_position_embeddings`, granicu duljine na kojoj je model treniran. RoPE nema tablicu težina jer se kutovi računaju usput, pa ta granica ne prijeti padom. Ona kaže do kuda je model *učio*. Iza nje model dobiva kutove kakve u treningu nije vidio, a što tada radi s njima, mora se izmjeriti.

Zamisli kutove kao kazaljke sata različitih brzina. Brze razlikuju susjedne tokene, a spore prate daleke odnose. **YaRN** (Yet another RoPE extensioN; Peng i sur., 2023.) brze kazaljke ostavlja kako jesu jer odnosi među susjedima ostaju isti, a spore usporava da i na većoj udaljenosti ostanu u poznatom rasponu. Između je postupni prijelaz, uz malu korekciju jačine pažnje. Težine se ne mijenjaju, mijenja se samo račun, pa se zahvat svodi na postavku.

U Transformersu 5 te su postavke u `rope_parameters` (ranije `rope_scaling`, s ključem `type`; stari se zapis još prevodi). Prema dokumentaciji, stanje u studenom 2026., primjer s granice 8192 na 32768:

```json
{
  "max_position_embeddings": 32768,
  "rope_parameters": {
    "rope_type": "yarn",
    "rope_theta": 10000.0,
    "factor": 4.0,
    "original_max_position_embeddings": 8192
  }
}
```

`rope_theta` prepiši iz izvornog nacrta modela. Neki modeli imaju odvojene postavke po vrsti sloja, pa je rječnik ugniježđen. U llama.cpp isto se traži pri pokretanju:

```bash
llama-server -m MODEL.gguf --port 8080 -c 32768 -np 1 \
  --rope-scaling yarn --rope-scale 4 --yarn-orig-ctx 8192
```

::: {.neprovjereno}
Autor YaRN nije pokrenuo ni u jednom alatu. Ključevi i zastavice preuzeti su iz dokumentacije Transformersa i README-a llama-servera u studenom 2026. Provjeri ih za svoju inačicu.
:::

Postavka se upiše za minutu, ali nije besplatna:

- **Kvaliteta iza trenirane duljine nije zajamčena.** Autori metode izvještavaju o dobrim rezultatima na modelima LLaMA, što ne znači da će tvoj model zadržati isto razumijevanje. Rezultat ovisi o modelu. Naknadno fino podešavanje na dugim tekstovima može pomoći, ali to je opet trening.
- **Račun za memoriju i dalje stiže.** Četiri puta dulji kontekst znači četiri puta veći KV cache i dulji prefill (poglavlje 8). Na malom stroju memorija te zaustavi prije granice modela.
- **Obični zlatni skup to ne vidi.** Kvakin zapisnik ima desetke tokena, pa bi prošao i s pokvarenim YaRN-om. Napravi zasebne primjere u kojima odgovor stoji duboko u dugom tekstu, ispred i iza izvorne granice, pa usporedi točnost s istim pitanjima na kraćem tekstu.

Prije svega provjeri treba li ti to. SmolLM3 već ima granicu 65 536, a dulji tekst često bolje rješava RAG (poglavlje 13).

## Spajanje modela Mergekitom

Spajanje (merging) računa s težinama više modela bez treninga i GPU-a. Radi to Mergekit, koji je od 31. 10. 2025. ponovno pod licencom LGPL v3.

### Zašto to uopće može raditi

Na prvi pogled prosjek dvaju modela djeluje kao miješanje dviju knjiga po slovima. Tako i bude, osim u jednom slučaju: kad oba modela potječu iz iste baze. Fino podešavanje malo pomiče težine, pa broj na istoj adresi u oba modela i dalje znači približno isto. Promjenu je tada moguće izdvojiti:

**vektor zadatka** (task vector) τ = podešeni model − baza

Taj vektor je ono što je model naučio. Vektori zadatka iz iste baze mogu se zbrajati jer su promjene iste stvari. Odmah vidiš i jednu zamku: kopija baze pod drugim imenom ima vektor nula i ne donosi ništa, pa je prije spajanja usporedi sa SHA256 sažetkom (poglavlje 10).

![Passthrough prepisuje tenzore iz jednog modela. TIES i DARE spajaju razliku od baze](slike/spajanje.svg)

### Metode

**Linear** je težinski prosjek svih težina. Najjednostavniji je i često razuman prvi pokus.

**TIES** i **DARE** spajaju vektore zadatka i rješavaju dva problema. Prvi je šum: velik dio promjena sitan je i slučajan. TIES zadržava samo najveće promjene, a DARE nasumično izbacuje dio promjena i pojačava ostatak tako da ukupni pomak ostane približno isti. Udio koji ostaje zove se `density`. Drugi je sukob: ako jedan model neku težinu gura gore, a drugi dolje, prosjek poništi oba. TIES zato glasa o predznaku i zadržava samo promjene većinskog smjera. `dare_ties` spaja izbacivanje iz DARE-a i glasanje iz TIES-a. Na kraju se rezultat dodaje bazi.

**Passthrough** ne računa ništa: svaki tenzor prepisuje iz jednog modela. Tako se slažu slojevi, primjerice donja polovica iz jednog modela i gornja iz drugog:

```yaml
slices:
  - sources:
      - model: models/l9/spojeno
        layer_range: [0, 15]
  - sources:
      - model: models/l9/spojeno_prenaucen
        layer_range: [15, 30]
merge_method: passthrough
dtype: float16
```

::: {.neprovjereno}
Autor ovu konfiguraciju nije pokrenuo. Sintaksa slijedi primjere iz repozitorija Mergekita. Poslije provjeri `num_hidden_layers` u izlaznom nacrtu.
:::

Preklopljeni rasponi, recimo `[0, 20]` i `[10, 30]`, daju dublji model od 40 slojeva. Više slojeva znači više memorije, a za bolju kvalitetu to samo po sebi nije nikakav dokaz.

Metoda je mnogo i popis raste. Stanje u studenom 2026.: linear, slerp, nuslerp, multislerp, karcher, task_arithmetic, ties, dare_linear, dare_ties, della, della_linear, breadcrumbs, breadcrumbs_ties, sce, model_stock, nearswap, arcee_fusion, passthrough. Parametre svake čitaj u README-u i dokumentaciji svoje inačice jer se mijenjaju.

### Što se mora poklapati

README Mergekita kaže: "All non-vocabulary dimensions must match". Sve dimenzije osim rječnika moraju biti jednake, dakle `hidden_size`, broj glava i sve što određuje oblik tablica. Mi smo spajali modele iste arhitekture, pa odbijanje nismo sami vidjeli.

Rječnik je iznimka jer se može uskladiti, a tu je i zamka najavljena u poglavlju 4. Ako token ID 49152 u jednom modelu znači jedno, a u drugom drugo, prosjek njihovih redaka u `embed_tokens` i `lm_head` nema značenja, a glava pokazuje na krive tokene. Program to sam ne može znati ako mu ne kažeš. Zato postoji `tokenizer_source` (noviji `tokenizer` s poljem `source`, koji README sada preporučuje): `base` zadržava rječnik baze, `union` spaja rječnike, a može se navesti i put do modela. Vrijedi i pravilo iz poglavlja 4: rezultat spajanja koristi samo tokenizator koji je izašao iz spajanja. Zastavica `--unsafe-truncate-embeddings` odsijeca zadnje retke, a pomoć je sama označava kao UNSAFE jer pretpostavlja iste ID-jeve. Ako su tvoji modeli dobili dodane tokene, kao u ovom poglavlju, to je upravo situacija u kojoj ta pretpostavka može biti kriva.

### Pada ili radi besmisleno

Razlikuj dva ishoda.

**Pada** kad se oblici ne poklapaju: model od 8B i model od 7B obično imaju tablice različitih dimenzija. To je povoljan ishod jer odmah znaš da je spajanje nemoguće. Zastavica `--allow-crimes` ("Allow mixing architectures") dopušta miješanje arhitektura, ali ne jamči da rezultat vrijedi.

**Radi, a nema smisla** kad se oblici slučajno poklope, ali su modeli trenirani neovisno. Dva tako trenirana modela nemaju zajedničko značenje adresa: redak 17 u `q_proj` jednog modela i redak 17 drugog naučili su nešto nepovezano. Tablice su iste veličine, pa je račun valjan i datoteka uredna, a prosjek je šum. Isto vrijedi za TIES i DARE: razlika od modela koji nije prava baza samo je razlika dvaju neovisnih modela, pa vektora zadatka tu nema. Provjeri zajedničko podrijetlo prije spajanja: `base_model` u metapodacima (poglavlje 3), a zatim i normu razlike od baze, koja bi trebala biti malena u odnosu na normu same baze.

### Instalacija na Pythonu 3.14

Na našem stroju `pip install mergekit` nije prošao:

```text
error: Microsoft Visual C++ 14.0 or greater is required.
ERROR: Failed building wheel for immutables
```

Paket `immutables` nema gotovu inačicu za Python 3.14, pa se pokušava prevesti, a prevoditelja nema. `pip install --no-deps mergekit` uspije, ali zatim `mergekit-yaml --help` javi `ModuleNotFoundError: No module named 'pydantic'`. `immutables` ima i čistu Python inačicu, pa je zaobilazak bio ovakav:

```bash
V=models/venv_mk/Scripts
venv/Scripts/python -m pip download immutables==0.21 --no-deps \
  --no-binary :all: --no-build-isolation -d models/mk_dep
tar -xzf models/mk_dep/immutables-0.21.tar.gz -C models/mk_dep \
  immutables-0.21/immutables
$V/python.exe -m pip install pydantic click tqdm pyyaml \
  typing-extensions sentencepiece protobuf scipy einops
SP="$(cygpath -w "$PWD/venv/Lib/site-packages")"
IM="$(cygpath -w "$PWD/models/mk_dep/immutables-0.21")"
export PYTHONPATH="$IM;$SP" PYTHONUTF8=1
```

To je zasebno okruženje samo za Mergekit, koje ostale pakete uzima iz glavnog okruženja preko `PYTHONPATH`. pip pritom upozorava na nezadovoljene ovisnosti, ali naredbe rade. Cjelovito je u `prilozi/vjezbe/l10_mergekit.sh` i `l10_mergekit2.sh`. Stariji Python ili instalirani prevoditelj vjerojatno bi riješili problem čišće, ali to nismo isprobali.

### Dva stvarna pokretanja

Spajali smo dva modela iz poglavlja 16, podešena iz iste baze: dobar (`spojeno`) i prenaučen (`spojeno_prenaucen`). Podrijetlo je dakle uredno.

```yaml
merge_method: linear
dtype: float16
models:
  - model: models/l9/spojeno
    parameters: {weight: 0.5}
  - model: models/l9/spojeno_prenaucen
    parameters: {weight: 0.5}
tokenizer_source: base
```

```yaml
merge_method: dare_ties
base_model: models/SmolLM2-135M-Instruct
dtype: float16
models:
  - model: models/l9/spojeno
    parameters: {weight: 1.0}
  - model: models/l9/spojeno_prenaucen
    parameters: {weight: 1.0}
parameters: {k: 0.3}
tokenizer_source: base
```

```bash
mergekit-yaml models/l10/mk/linear.yml models/l10/mk/izlaz_linear \
  --lazy-unpickle
```

Makni `HF_HUB_OFFLINE=1` ako ga imaš postavljenog. S njim je `dare_ties` pao pri pisanju opisa modela (`OfflineModeIsEnabled`), kad je `model.safetensors` već bio zapisan, a tokenizatora u mapi još nije bilo.

Na CPU-u je `linear` trajao 28 s, a `dare_ties` 33 s. Obje su datoteke bile uredne, po 269 060 280 B, s predloškom u mapi. Po tome se ne bi moglo reći ništa loše ni za jednu. Provjera (`l10_provjera_spoja.py`, gubitak na 30 validacijskih primjera) otkriva razliku:

| Model | Val gubitak |
|---|---:|
| `spojeno` | 0,0511 |
| `izlaz_linear` | 0,3037 |
| `spojeno_prenaucen` | 0,6653 |
| `izlaz_dare` | 1,7574 |
| bazni SmolLM2 | 2,6587 |

Odgovori na zapisnik "Stranka zove, hladnjak ne hladi, sumnja na kompresor. Treba odmah." (prelomljeno zbog širine):

```text
spojeno:
  {"uredaj": "hladnjak", "kvar": "ne hladi",
   "dio": "kompresor", "hitnost": "srednja"}
izlaz_linear:
  {"uredaj": "hladnjak", "kvar": "ne hladi",
   "dio": "kompresor", "hitnost": "niska"}
izlaz_dare:
  {"uredaj\xa0:\xa0 \xa0-\xa0 \xa0( hladičs spacesrila\xa0 \xa0-\xa0
  \xa0c \xa0- \xa0srednya";uredr\xa0:\xa0 hv IV\xa0 \xa0{"\xa0 \xa0-\xa0
  \xa0{"\xa0
```

Linearni prosjek pao je između roditelja: bolji je od lošeg, a gori od dobrog. Spajanje ovdje nije donijelo ništa jer drugi roditelj vjerojatno ne zna ništa što prvi ne zna. Koristan pokus tražio bi modele s različitim znanjem, a toga ovdje nismo imali.

`dare_ties` dao je neupotrebljiv model, bez ijedne greške u izvođenju. Gubitak mu je niži od baznog, a odgovor je ipak smeće, što je još jedan razlog da uz broj uvijek pročitaš i odgovore. Uzrok nije utvrđen, a ovaj pokus **ne** govori da je metoda loša. Vjerojatnije je da je naša konfiguracija bila kriva. `k` nije među parametrima koje dokumentacija navodi za `dare_ties`, a `density` nije postavljen. Uz to izvorni kod `dare_ties` po zadanom ne normalizira težine, pa `weight: 1.0` na oba modela može značiti da bazi dodajemo obje promjene gotovo cijele, a ne njihov prosjek. Dokumentiranim parametrima pokus bi izgledao ovako:

```yaml
merge_method: dare_ties
base_model: models/SmolLM2-135M-Instruct
dtype: float16
models:
  - model: models/l9/spojeno
    parameters: {weight: 0.5, density: 0.5}
  - model: models/l9/spojeno_prenaucen
    parameters: {weight: 0.5, density: 0.5}
tokenizer_source: base
```

Ovu smo popravljenu inačicu pokrenuli (`mergekit-yaml`, 89 s uključujući učitavanje, izlaz opet uredan). Gubitak na istih 30 validacijskih primjera je 0,3125, a odgovor na isti zapisnik glasi `{"uredaj": "hladnjak", "kvar": "ne hladi", "dio": "kompresor", "hitnost": "niska"}`. Model dakle daje valjan JSON i gubitak blizu linearnog prosjeka (0,3037), a ne razoren izlaz kao s 1,7574. Time je kvar vezan uz staru konfiguraciju (`k`, bez `density`, `weight: 1.0`), ali nismo pokusom razdvojili koji je od tri razloga presudan. Linearni prosjek nismo pustili kroz zlatni skup niti kroz GGUF.

Spojene modele nismo pretvorili u GGUF niti smo ih pustili kroz zlatni skup, a 30 validacijskih primjera sintetičkih je podataka. Prije upotrebe napravi oboje, kao u poglavlju 16.

## FrankenMoE

`mergekit-moe` složi više modela u MoE (poglavlje 6). Dokumentacija traži Mistral ili Llama modele iste veličine, a izlaz je Mixtral, DeepSeek MoE ili Qwen MoE. Pažnja i normalizacija ostaju zajednički, a umnožava se samo MLP. Računica za 3×8B na Llami 3: 8,03 mlrd za prvi model plus po 5,64 mlrd MLP-a za svaka dva sljedeća stručnjaka, dakle 8,03 + 2 × 5,64 ≈ 19,3 mlrd parametara. Svi moraju stati u memoriju, iako se po tokenu koristi samo dio. Vrijedi isto upozorenje o podrijetlu: stručnjaci dijele pažnju s baznim modelom, pa stručnjak iz druge obitelji dobiva pažnju koju nikad nije vidio. Ovo nismo pokrenuli.

## Abliteracija

Abliteraciju spominjemo samo kao pojam, bez postupka. Arditi i suradnici pokazali su da je odbijanje u modelu uglavnom jedan smjer u aktivacijama, a zahvat taj smjer uklanja iz težina. Time ne dobivaš samo model koji manje odbija. Težine su jedne, pa zahvat dira i ostalo: rad arXiv 2512.13655 mjeri da je matematičko zaključivanje najosjetljivije, s promjenom na GSM8K, testu matematičkih zadataka, od +1,51 do −18,81 postotnih bodova. Pravna i etička odgovornost za model bez zaštita tada je tvoja, kao i za sve što on proizvede i kome ga isporučiš. Naiđeš li na takav model, ili ga nesvjesno preuzmeš, ponovi zlatni skup i sigurnosnu provjeru iz poglavlja 16.

::: {.kvar}
**Simptom → uzrok**

- Skripta za pregled puni RAM → tenzori se gomilaju u rječniku. Obriši svaki nakon provjere, a pri pisanju radi dio po dio.
- Norma izgleda zdravo, a izlaz je `nan` → alat možda NaN pretvara u nulu, pa ga norma ne pokazuje. Gledaj brojač NaN-ova i Infova.
- `IndexError: index out of range in self` nakon dodavanja tokena → nedostaje `resize_token_embeddings`.
- Novi token model ignorira ili ga nikad ne piše → novi redak nije treniran. Uključi `embed_tokens` i `lm_head` u trening.
- Datoteka se udvostručila nakon spremanja → model je učitan u FP32. Zadaj `dtype`.
- Učitavanje prolazi, u logu `MISSING`, izlaz loš → `num_hidden_layers` ne odgovara težinama, pa su slojevi nasumični. Popravi `config.json`.
- Biblioteka ne nalazi tenzor nakon izmjene → `weight_map` nije usklađen s dijelovima.
- Kratki upiti rade, dugi tekst daje lošije odgovore → duljina je iza trenirane granice. Izmjeri primjerima s odgovorom duboko u tekstu.
- Spajanje prolazi, odgovori su smeće, podrijetlo isto → provjeri parametre metode i normalizaciju. Počni s `linear`.
- Spajanje prolazi, odgovori su smeće, podrijetlo različito → rezultat nema smisla i parametri ga neće popraviti.
- Spojeni model piše krive riječi → rječnici nisu usklađeni. Postavi `tokenizer_source` ili `tokenizer`.
- Vektor zadatka je nula, a rezultat isti kao baza → "podešeni" model je kopija baze. Usporedi SHA256.
- `Failed building wheel for immutables` → Python 3.14 bez prevoditelja. Upotrijebi zaobilazak iz ovog poglavlja.
:::

## Sažetak

Modele pregledavaj tenzor po tenzor i ne čuvaj ih u memoriji, a alat provjeri i na namjerno pokvarenoj kopiji. Dodani tokeni traže proširenje obiju tablica i trening jer novi redak ne zna ništa. Uklanjanje slojeva bez popravka nacrta ne javlja grešku i daje nasumične slojeve, a YaRN pomiče granicu konteksta bez jamstva kvalitete. Mergekit ima smisla za modele zajedničkog podrijetla, uz usklađen rječnik: naš `linear` pao je između roditelja, a `dare_ties` s pogrešno zadanim parametrima dao je neupotrebljiv model bez ikakve greške, dok je s dokumentiranima (`density` i `weight` 0,5) dao valjan JSON i gubitak 0,3125. Zato nakon svakog zahvata pusti zlatni skup jer uredna datoteka ne dokazuje ništa.
