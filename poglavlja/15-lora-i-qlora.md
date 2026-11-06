# LoRA i QLoRA

::: {.cilj}
**Nakon ovog poglavlja znaš:** što se događa u treningu i kako čitati krivulju gubitka · zašto puno fino podešavanje traži više od 100 GB memorije · kako LoRA i QLoRA to spuštaju na jednu običnu karticu · kojim se redom spaja i kvantizira i s kojim postavkama početi.
:::

Odluka je donesena u poglavlju 13, a Kvakini zapisnici čekaju pripremljeni iz poglavlja 14. Ovo poglavlje objašnjava mehanizam. Same naredbe i pravi trening dolaze u poglavlju 16.

## Što trening radi

Zamisli model kao ploču s osam milijardi vijaka. Svaki vijak je jedna težina, a tvornica ih je već podesila. Trening je postupak koji te vijke malo pomiče, tisuće puta, dok model ne počne raditi ono što mu pokazuješ. Svaki pomak nastaje u istom ciklusu: predviđanje, gubitak, gradijent, ispravak.

### Predviđanje i gubitak

Uzmi jedan Kvakin primjer: zapisnik tehničara i točan JSON iza njega. Model čita tekst do mjesta `"hitnost": "` i daje logite (poglavlje 6), a oni se pretvaraju u vjerojatnosti za sljedeći token. Točan nastavak je `visoka`, pa pitamo samo jedno: kolika je vjerojatnost pripala baš tom tokenu?

Odgovor se pretvara u **gubitak** (loss), broj koji kaže koliko je model iznenađen točnim odgovorom. Mjera se zove unakrsna entropija (cross-entropy). Računaš je kao negativni logaritam vjerojatnosti, a dovoljno je vidjeti kako se ponaša:

| Vjerojatnost točnog tokena | Gubitak | Model je |
|----------------------------|---------|---------------|
| 0,90                       | 0,11    | gotovo siguran |
| 0,30                       | 1,20    | u dvojbi |
| 0,01                       | 4,61    | zatečen |

Gubitak primjera je prosjek po svim tokenima odgovora. Manji broj znači manje iznenađenja.

### Gradijent i stopa učenja

**Gradijent** je jedan broj za svaku težinu. Kaže u kojem smjeru pomaknuti vijak da se gubitak smanji i koliko je gubitak osjetljiv na taj vijak. Računa ga propagacija unatrag (backpropagation), koja ide kroz model od izlaza prema ulazu. Taj račun nećemo izvoditi, dovoljno je znati što daje: smjer ispravka za svaku težinu.

**Stopa učenja** (learning rate) određuje koliko se daleko ide u tom smjeru u jednom koraku.

- Previsoka: ispravci preskaču cilj, gubitak skače, a može postati i `NaN` (broj koji se više ne može izračunati).
- Preniska: gubitak pada tako sporo da trening izgleda zamrznut, a najmljeni GPU se plaća po satu.

### Batch, korak, epoha

- **Batch** je skupina primjera koji se obrađuju zajedno. Njihovi se gradijenti uprosječuju, pa je smjer ispravka manje slučajan.
- **Korak** (step) je jedan ispravak težina.
- **Epoha** (epoch) je jedan prolaz kroz cijeli skup za trening.

Primjer: ako za trening ostane 240 zapisnika, a ispravak se radi nakon svakih 8 primjera, epoha ima 30 koraka. Tri epohe daju 90 koraka.

### Validacijski skup i prenaučenost

Model može smanjivati gubitak na dva načina: tako da nauči pravilo ili tako da napamet zapamti primjere. Na skupu za trening ta se dva načina ne razlikuju. Zato postoji validacijski skup iz poglavlja 14: primjeri na kojima se gubitak samo mjeri, a težine se zbog njih ne mijenjaju. Kad model pamti umjesto da uči, to se zove **prenaučenost** (overfitting).

Krivulje gubitka čitaj po obliku jer apsolutni broj ovisi o zadatku:

- **Obje padaju:** model uči, nastavi.
- **Trening pada, validacija se poravna:** korist je pri kraju, uskoro stani.
- **Trening pada, validacija raste:** prenaučenost. Uzmi težine spremljene u trenutku kad je validacijski gubitak bio najniži.
- **Obje stoje:** ništa se ne uči. Provjeri stopu učenja i postavke (okvir na kraju poglavlja).
- **Skokovi ili `NaN`:** stopa je previsoka ili podaci imaju grešku.

Stvarne krivulje našeg glavnog i prenaučenog pokusa nacrtane su u poglavlju 16.

Validacijski gubitak mjeri tokene, a Kvaku zanima točnost po polju. Konačnu ocjenu zato i dalje daje zlatni skup iz poglavlja 9.

## Zašto je puno fino podešavanje skupo

Puno fino podešavanje pomiče sve težine. Računica za model od 8 milijardi parametara u 16 bita izgleda ovako:

| Što se drži u memoriji | Račun | Memorija |
|------------------------|-------------------|----------|
| Težine                 | 8 mlrd × 2 bajta  | 16 GB    |
| Gradijenti             | 8 mlrd × 2 bajta  | 16 GB    |
| Stanje AdamW-a         | 8 mlrd × 2 × 4 bajta | 64 GB |
| Zbroj                  |                   | 96 GB    |
| Aktivacije             | ovisi o batchu    | 16–32 GB |

**Težine** već poznaješ iz poglavlja 8. **Gradijenti** su po jedan broj za svaku težinu, u istom formatu. **AdamW** je optimizator, dio koji iz gradijenta računa stvarni pomak. Za svaku težinu pamti dva tekuća prosjeka u FP32: kamo gradijent obično pokazuje i koliko jako varira. Zato je najveća stavka. **Aktivacije** su međurezultati svakog sloja za svaki token u batchu, a trebaju propagaciji unatrag. Rastu s veličinom batcha i duljinom primjera.

Ukupno je to 112–128 GB. Isti model za posluživanje staje u 4,9 GB (Q4_K_M, poglavlje 11), a trening ne stane ni na jednu karticu od 80 GB.

## Ideja LoRA-e

Ako se težine ne mijenjaju, za njih ne trebaju ni gradijenti ni stanje optimizatora. LoRA (Low-Rank Adaptation) zato tvorničke vijke zapečati i uči samo mali dodatak, ispravak koji se pribraja izvornoj matrici:

```text
W_novo = W0 + (α/r) · (B × A)
```

`W0` je izvorna matrica i ostaje zamrznuta. `B` i `A` su dvije nove uske matrice koje se treniraju.

![LoRA u mjerilu: zamrznuta W0 i dvije tanke trake B i A](slike/lora.svg)

### Što znači nizak rang

Uzmi matricu projekcije `q_proj` iz poglavlja 6, dimenzija 4096 × 4096. Ona ima 16 777 216 brojeva. Ispravak iste veličine možeš dobiti umnoškom dviju traka: `B` veličine 4096 × 16 i `A` veličine 16 × 4096. To je 65 536 + 65 536 = 131 072 parametra, odnosno 0,78 % izvorne matrice.

Cijena je manja sloboda. Svaki redak ispravka smjesa je istih 16 redaka matrice `A`, pa ispravak ima najviše 16 neovisnih smjerova. Taj broj je **rang** (r). Oblik ispravka je pun, a slobodnih mu je smjerova malo. U praksi je to često dovoljno jer promjena navike rijetko traži promjenu u svih 4096 smjerova.

Matrica `B` kreće od nule, a `A` od malih slučajnih brojeva. Umnožak je zato na početku nula i model se ponaša točno kao izvorni. Trening kreće od poznatog stanja i odmiče se od njega samo koliko podaci traže.

### Hiperparametri

Hiperparametar je postavka koju biraš ti, a trening je ne mijenja.

- **r** određuje koliko smjerova ispravak ima. Premalen ne može uhvatiti promjenu, a prevelik lakše pamti primjere napamet. Polazište je 16, a za skup od nekoliko stotina zapisnika ima smisla probati i 8.
- **α (alpha)** određuje jačinu ispravka kroz omjer α/r. Obično se uzima α = r ili α = 2r, a polazište je `r=16`, `α=32`. Ako povećaš r i ne diraš α, omjer pada i ispravak slabi.
- **Dropout** tijekom treninga nasumce gasi dio signala koji ulazi u adapter, pa se on ne može osloniti na pojedine putove. Polazište je 0,05.
- **Ciljni moduli** (target modules) su matrice na koje stavljaš adapter. Kod Llama arhitekture to su projekcije pažnje `q_proj`, `k_proj`, `v_proj`, `o_proj` i MLP-a `gate_proj`, `up_proj`, `down_proj`. Drugi modeli mogu imati druga imena, pa ih provjeri u popisu tenzora. Polazište je svih sedam.

Veličina adaptera za cijeli Llama 3 8B, svih 7 projekcija u sva 32 sloja:

| r  | Parametara | Veličina | Udio modela |
|----|------------|----------|-------------|
| 8  | 21 M       | 42 MB    | 0,26 %      |
| 16 | 42 M       | 84 MB    | 0,52 %      |
| 32 | 84 M       | 168 MB   | 1,04 %      |
| 64 | 168 M      | 336 MB   | 2,09 %      |

Veličina vrijedi uz 2 bajta po parametru. Alat koji sprema u FP32 daje dvostruko veću datoteku.

::: {.vjezba}
**Vježba: procijeni adapter** `samo čitanje` · 5 min

Matrica `gate_proj` ima 14336 × 4096 elemenata. Koliko parametara ima ispravak uz r = 32 i koliki je to udio matrice? Formula je r × (d + k). Rješenje: 32 × 18 432 = 589 824 od 58 720 256, što je oko 1,00 %.
:::

### Za što je LoRA dobra

LoRA uči oblik, stil, shemu i navike. Kod Kvake to znači: odgovaraj samo JSON-om, uvijek ista polja istim redom, `hitnost` uzima samo dopuštene vrijednosti, kratice tehničara prepoznaj kao uređaje i kvarove. To se ponavlja u svakom primjeru, pa se dobro sažima u malo smjerova.

Slabo uči nove činjenice. Ako iz treninga zapamti šifru dijela, zapamtit će je nepouzdano i izmišljat će slične šifre, a kad se katalog promijeni, treniraš ponovno. Zato pitanja iz priručnika ostaju kod RAG-a (poglavlje 13).

### Adapter ili spojeni model

Nakon treninga imaš **adapter**: datoteku s matricama `A` i `B` i opisom postavki. Vrijedi samo uz točno onu bazu za koju je naučen, pa prikvači reviziju (poglavlje 10). Prednost mu je što na jednoj bazi možeš držati više adaptera i brzo ih mijenjati.

**Spojeni model** (merged) nastaje kad se ispravak jednom izračuna i pribroji težinama. Umnožak `B × A` ima isti oblik kao `W0`, pa model ne raste ni za jedan parametar. Spojeni model je samostalan i može se kvantizirati kao svaki drugi.

## QLoRA

LoRA uklanja gradijente i optimizator za bazu, ali baza i dalje mora biti u memoriji: 16 GB. QLoRA (Quantized LoRA) smanjuje i nju, tako da je tijekom treninga drži u 4 bita. To smije jer su zamrznute težine samo za čitanje. Ne treba ih pomicati, pa im nije potrebna ni preciznost za sitne pomake. Za svako množenje razmataju se u BF16, a adapter cijelo vrijeme ostaje u većoj preciznosti.

::: {.napomena}
**NF4 je zasebna stvar od GGUF Q4 i od FP8/AWQ.**

- **NF4:** samo za trening, u memoriji, kroz biblioteku bitsandbytes. Kad trening završi, nestaje. Nikad ga ne isporučuješ.
- **GGUF Q4_K_M:** datoteka za posluživanje kroz llama.cpp (poglavlje 11).
- **FP8 i AWQ:** formati za posluživanje kroz vLLM (poglavlje 18).

Sličan naziv i broj bitova ne znače da su međusobno zamjenjivi.
:::

**NF4** (NormalFloat 4) ima 16 razina kao i svaki 4-bitni zapis (poglavlje 11), ali su razmještene prema zvonolikoj krivulji kojom su težine približno raspoređene. U svaku razinu tako upada podjednak broj težina.

**Dvostruka kvantizacija** (double quantization) smanjuje trošak faktora skaliranja. Svaki blok od 64 težine ima svoj faktor od 32 bita, što je 0,5 bita po parametru. Ako se i sami faktori kvantiziraju, ostaje oko 0,13 bita. Ušteda je oko 0,37 bita po parametru, što je na 8 milijardi parametara oko 0,37 GB.

**Straničeni optimizator** (paged optimizer) stanje optimizatora drži u posebnoj memoriji. Kad VRAM-a ponestane, ta se stanja sele u običan RAM, a trening se nastavlja umjesto da se sruši. U alatima se zove `paged_adamw_8bit` i to stanje drži u 8 bita. Konfiguracija u poglavlju 16 koristi `adamw_bnb_8bit`, isti 8-bitni AdamW bez straničenja. Za oba je stavka za AdamW u tablici ispod gornja granica.

**Gradient checkpointing** na putu naprijed čuva samo dio aktivacija, a ostale na povratku ponovno računa, pa štedi memoriju i troši vrijeme.

Postavke se u Transformersu v5 predaju kroz `quantization_config` jer je argument `load_in_4bit` uklonjen iz `from_pretrained`:

```python
from transformers import BitsAndBytesConfig

kv4 = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype="bfloat16",
)
```

::: {.neprovjereno}
Autor ovaj primjer nije pokrenuo jer bitsandbytes za trening traži GPU. Provjeri inačice alata. Konfiguracija Axolotla ima vlastiti ključ sličnog imena, o čemu više u poglavlju 16.
:::

### Što staje na 8–12 GB

Za 8B uz r = 16 i svih 7 projekcija:

| Stavka               | Memorija |
|----------------------|----------|
| Baza u NF4           | oko 4 GB |
| Težine adaptera      | 84 MB    |
| Gradijenti adaptera  | 84 MB    |
| AdamW adaptera, FP32 | 336 MB   |
| Ukupno bez aktivacija | oko 4,5 GB |

Od 96 GB ostaje oko 4,5 GB. Baza je stvarno nešto veća jer dio slojeva ostaje u većoj preciznosti. Ostatak kartice od 8–12 GB, dakle najviše nekoliko GB, odlazi na aktivacije i sustav. Zato na takvoj kartici duljinu primjera i batch držiš malima, a gradient checkpointing uključenim.

### Pravilo spajanja

Redoslijed je uvijek isti:

```text
baza u 4 bita + trening → adapter
baza u punoj preciznosti + adapter → spojeni model
spojeni model → GGUF Q4_K_M
```

Alati pritom mogu birati drukčiji put. Axolotl u v0.21.1 po zadanom koristi `merge_method: memory_efficient`, a pravilo gore odgovara metodi `legacy`; razlika je objašnjena u poglavlju 16.

Razlozi su sasvim mehanički:

1. **Ispravak je sitan.** U zapisu sa 16 razina većina ispravaka zaokružila bi se na istu vrijednost i adapter bi se izgubio.
2. **NF4 baza je već zaokružena.** Daljnja kvantizacija bi zaokruživala zaokruženo, a greške bi se zbrajale. Isti oprez vidiš kod `llama-quantize`, koji ponovno kvantiziranje dopušta samo uz izričit `--allow-requantize`.
3. **Kvantizator mjeri svoju grešku prema izvoru.** Blokovi Q4_K_M i imatrix (poglavlje 11) trebaju prave vrijednosti težina.

Konačna kvantizacija i dalje može pojesti dio ispravka, pa zlatni skup ponavljaš na kvantiziranom modelu, onom koji ćeš stvarno posluživati (poglavlje 12).

## Izbor postavki

Ovo je polazište za prvi pokušaj, a krivulje gubitka reći će što dalje mijenjati:

| Postavka               | Polazište     | Kada mijenjati |
|------------------------|---------------|-----------------------|
| Stopa učenja           | `2e-4`        | skokovi: smanji |
| Zagrijavanje (warmup)  | 5–10 % koraka | rijetko |
| Epohe                  | 3             | prema validaciji |
| Batch + akumulacija    | 2 + 4         | prema memoriji |

**Zagrijavanje** podiže stopu učenja od nule tijekom prvih koraka, da prvi još nasumični ispravci adaptera ne budu veliki. Izražavaj ga u postotku koraka: gotov primjer sa `warmup_steps: 50` na Kvakinih 90 koraka potrošio bi više od pola treninga.

**Akumulacija gradijenta** (gradient accumulation) skuplja gradijente kroz nekoliko batcheva i tek onda radi jedan korak. Uz batch 2 i akumulaciju 4 ispravak se temelji na 8 primjera, a memorija se troši kao za 2. To je ona osmica iz računice s epohama.

### Isti predložak u treningu i posluživanju

Model u treningu vidi točan niz tokena koji proizlazi iz chat predloška (poglavlje 5). Adapter uči: nakon ovih posebnih tokena slijedi JSON. Ako posluživanje koristi drukčiji predložak, model dobiva niz koji nikad nije vidio i naučena navika se ne aktivira ili se aktivira napola. Isto vrijedi za token kraja: ako ga nije bilo u treningu, model ne zna stati. Predložak zato prikvači s modelom i prije treninga pogledaj jedan primjer kao čisti tekst.

::: {.kvar}
**Simptom → uzrok**

- `NaN` u gubitku → previsoka stopa učenja, računanje u FP16 umjesto BF16 ili prazan primjer. Smanji stopu i provjeri podatke.
- Validacijski gubitak raste → prenaučenost. Uzmi raniju spremljenu točku, smanji broj epoha ili r, dodaj podatke.
- Gubitak se ne miče → preniska stopa, ciljni moduli ne odgovaraju imenima u modelu pa se ništa ne trenira ili su sve oznake maskirane. Provjeri broj parametara koji se treniraju.
- Savršeno na treningu, pogrešno na zlatnom skupu → pamćenje primjera, skup za trening premalo raznolik ili isti primjeri u treningu i validaciji. Usporedi i razdiobu po uređajima i kvarovima.
- Odgovor u pogrešnom formatu → najčešće drukčiji predložak u treningu i posluživanju. Provjeri i je li adapter uopće učitan ili spojen.
- `OOM` (out of memory) → smanji duljinu primjera i batch, a akumulacijom vrati broj primjera po koraku. Uključi gradient checkpointing, smanji r ili ciljne module.
:::

## Sažetak

Trening mjeri koliko je model iznenađen točnim odgovorom, gradijentom nalazi smjer ispravka i pomiče težine za iznos koji određuje stopa učenja, a validacijska krivulja otkriva pamćenje napamet. Puno fino podešavanje modela 8B traži 96 GB plus aktivacije jer svaka težina nosi gradijent i stanje optimizatora. LoRA zamrzava bazu i uči uzak ispravak `B × A`, što je dobro za oblik i navike, a loše za nove činjenice. QLoRA uz to bazu tijekom treninga drži u NF4, što ne treba brkati s GGUF Q4, a spaja se uvijek u bazu pune preciznosti pa tek onda kvantizira. U poglavlju 16 sve to pokrećeš na stvarnom treningu, uz predložak koji je isti u treningu i posluživanju.
