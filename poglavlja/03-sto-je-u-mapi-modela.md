# Što je u mapi modela

::: {.cilj}
**Nakon ovog poglavlja znaš:**

- zašto se model sastoji od težina i zasebnog programa koji ih izvodi
- čemu služi svaka datoteka u mapi modela i što se dogodi ako nedostaje
- pročitati `config.json` i iz zaglavlja izračunati broj parametara
- što model otvorenih težina daje, a što ne daje
- pročitati naziv poput `gemma-4-E2B-it-Q4_K_M.gguf`
:::

U poglavlju 2 model je bio jedna datoteka od 3,11 GB. Jedna naredba je učita i dobiješ odgovor. Lako je zaključiti da je ta datoteka program koji razmišlja, nešto poput `.exe` datoteke. Ta slika kasnije smeta: ne objašnjava zašto isti model radi u više alata, zašto mu brzina ovisi o alatu ni zašto noviji model zna odbiti stari alat.

## Težine i program

Model se sastoji od dva odvojena dijela.

**Težine (weights)** su brojevi. Trening ih namješta dok model ne počne davati dobre odgovore, a nakon treninga više se ne mijenjaju. Jedan takav broj zove se **parametar**. Brojevi su složeni u imenovane tablice koje se zovu **tenzori**, a poglavlje 7 objašnjava kako su zapisani. U datoteci nema uputa ni logike, samo brojevi i malo teksta koji ih opisuje.

**Program za izvođenje** (runtime) zna što s tim brojevima treba računati. U poglavlju 2 to je bio llama.cpp. Odnos je sličan onom između MP3 datoteke i svirača: datoteka nosi sadržaj, a sama od sebe ne svira.

Iz te podjele slijede tri praktične posljedice.

- **Isti model radi u različitim programima.** Istu GGUF datoteku mogu izvoditi `llama-cli`, `llama-server`, Ollama i LM Studio.
- **Program možeš ažurirati bez novog preuzimanja modela.** Vrijedi i obrnuto: model izdan nakon tvog programa može tražiti račun koji tvoj program još ne zna, pa treba novija inačica programa.
- **Brzina nije svojstvo modela.** Gemma 4 E2B Q4_K_M, s 4 dretve, na laptopu s procesorom i5-10210U, 16 GB RAM-a i bez GPU-a, istog je dana generirala 5,61 tok/s u `llama-completion`, 11,09 tok/s u `llama-server` i 12,06 tok/s u `llama-bench`. Dio te razlike šum je jer stroj nije bio izoliran, ali datoteka je u svim mjerenjima bila ista. Izmjeri na svom računalu i uz broj uvijek zapiši alat.

## Hugging Face: garaža i trgovina dijelova

Modeli se najčešće nalaze na Hugging Faceu (huggingface.co), koji je za mehaničara garaža i trgovina dijelova u jednom. Svaki je model repozitorij s nazivom oblika `vlasnik/model`, primjerice `HuggingFaceTB/SmolLM3-3B`. Repozitorij radi poput Gita: ima datoteke, povijest izmjena i oznake inačica. Velike datoteke čuvaju se posebnim mehanizmom, pa se i one mogu preuzimati pojedinačno.

Stranica modela ima tri dijela koja te zasad zanimaju:

- **Kartica modela (model card)**, opis modela: namjena, ograničenja, licenca, rezultati.
- **Files and versions**, popis datoteka s veličinama.
- **Metapodaci**, primjerice licenca i `base_model`, izvorni model od kojeg ovaj potječe.

Kako karticu modela čitati kritički i kako izabrati model, obrađuje poglavlje 9. Kako prikvačiti točnu reviziju (pin), vidjet ćeš u poglavlju 10.

## Obilazak mape

GGUF te dijelove skriva u jednoj datoteci, pa uzmi model u izvornom obliku. **SmolLM3-3B** je mali, nezaključan model s licencom Apache 2.0. Ovako izgleda njegova mapa nakon preuzimanja:

```text
== datoteke
        17,452  README.md
         5,598  chat_template.jinja
         1,915  config.json
           182  generation_config.json
 4,966,315,264  model-00001-of-00002.safetensors
 1,183,919,744  model-00002-of-00002.safetensors
        26,899  model.safetensors.index.json
           289  special_tokens_map.json
    17,208,819  tokenizer.json
        50,387  tokenizer_config.json
 6,167,546,549  UKUPNO (6.17 GB)
```

Ovo je izvorni ispis skripte, pa su veličine u bajtovima i s engleskim razdjelnicima. Dvije datoteke s težinama čine 99,7 % mape (izračun). Sve ostalo stane u 17,3 MB, od čega je 17,2 MB `tokenizer.json`. Datoteka koja određuje građu modela ima 1915 bajtova.

Skripta za preuzimanje uzela je samo datoteke koje model treba. Repozitorij još sadrži `.gitattributes` i `notebook.ipynb` (stanje u studenom 2026.).

![Datoteke u mapi modela po skupinama: nacrt, tokeni, težine i opis](slike/mapa-modela.svg)

Slijedi svaka datoteka redom i ono što se pokvari kad nedostaje.

**`config.json`** je nacrt: vrsta modela, broj slojeva, dimenzije. Težine su samo imenovane tablice brojeva i same ne govore kako se spajaju. Bez ove datoteke Transformers ne zna koju arhitekturu treba složiti i odbija učitavanje. Pretvorba u GGUF također počinje čitanjem ove datoteke.

**`model-*.safetensors`** su same težine, ovdje u dva dijela (shards). Mali modeli imaju jednu datoteku `model.safetensors`. Bez ijednog dijela modela nema, a ako nedostaje samo jedan, učitavanje staje ili javlja nepotpune težine. Format je tema poglavlja 10.

**`model.safetensors.index.json`** je kazalo: za svaki tenzor piše u kojem je dijelu. Postoji samo kad dijelova ima više. Bez njega biblioteka ne zna da dijelovi čine cjelinu, pa javlja da težine nije našla iako su na disku. Ako ručno mijenjaš tenzore, ovo kazalo mora ostati točno.

**`tokenizer.json`** sadrži rječnik modela i pravila po kojima se tekst pretvara u brojeve i natrag. Model prima samo brojeve, pa mu bez ove datoteke ne možeš predati nijednu riječ. Gora je pogreška tuđi tokenizator: ako je veličina rječnika ista, sve se učita bez greške, a izlaz je besmislen. Tokenizator detaljno upoznaješ u poglavlju 4.

**`tokenizer_config.json`** opisuje kako koristiti tokenizator: koji su tokeni posebni, koji je token kraja, koja ga klasa učitava. Kod starijih modela u njoj je često i chat predložak. Bez nje alat može krivo prepoznati posebne tokene, a greške nema, samo su odgovori lošiji. `special_tokens_map.json` je mala pomoćna datoteka s nazivima posebnih tokena (kod SmolLM3 to je `<|im_end|>`) i često se preklapa s prethodnom.

**`chat_template.jinja`** je predložak (chat template): pravilo po kojem se tvoje poruke pretvaraju u tekst koji model stvarno prima. Ako nedostaje, neki alati javljaju grešku, a neki primijene zamjenski predložak i model tada odgovara slabije bez ikakvog upozorenja. To je toliko čest kvar da mu je posvećeno poglavlje 5.

**`generation_config.json`** sadrži zadane postavke generiranja. Kod SmolLM3 to su `temperature` 0,6 i `top_p` 0,95, koje objašnjava poglavlje 6. Model radi i bez nje, ali s tuđim zadanim vrijednostima. Kod nekih modela samo ova datoteka navodi sve tokene kraja, pa bez nje generiranje ne stane na vrijeme.

**`README.md`** je kartica modela. Tehnički se bez njega ništa ne pokvari, no gubiš namjenu, ograničenja i upute. Na vrhu mu je blok s metapodacima, a kod SmolLM3 tamo piše `license: apache-2.0` i `base_model: HuggingFaceTB/SmolLM3-3B-Base`.

**`LICENSE`** je zasebna datoteka s tekstom licence. U mapi SmolLM3 nema je jer je licenca navedena u metapodacima, a neki je repozitoriji imaju. Program radi i bez nje, pa se ovaj kvar ne vidi u terminalu. Ako licenca nije navedena nigdje, nemaš potvrdu da model smiješ koristiti. Što pojedine licence dopuštaju, čitaš u poglavlju 9.

## config.json kao tehnički list

`config.json` se čita kao tehnički list automobila: kratko, a dovoljno da znaš s čime imaš posla. Evo glavnih polja SmolLM3-3B (skraćeno):

```text
architectures: ["SmolLM3ForCausalLM"]
model_type: "smollm3"
vocab_size: 128256
hidden_size: 2048
intermediate_size: 11008
num_hidden_layers: 36
num_attention_heads: 16
num_key_value_heads: 4
max_position_embeddings: 65536
torch_dtype: "bfloat16"
tie_word_embeddings: true
```

Pet polja najviše govori:

| Polje | Vrijednost | Što znači | Više |
|---|---:|---|---|
| `hidden_size` | 2048 | koliko brojeva opisuje token unutar modela | pogl. 6 |
| `num_hidden_layers` | 36 | kroz koliko slojeva prolazi svaki token | pogl. 6, 8 |
| `num_attention_heads` | 16 | koliko usporednih "pogleda" ima pažnja | pogl. 6 |
| `vocab_size` | 128 256 | koliko različitih tokena model poznaje | pogl. 4 |
| `max_position_embeddings` | 65 536 | najveća predviđena duljina konteksta, u tokenima | pogl. 6, 8 |

Riječi poput "pažnja" (attention) i "sloj" zasad ne moraš razumjeti do kraja jer poglavlje 6 prati token kroz cijeli model. Važnije je da već sada možeš usporediti dva modela: više slojeva i širi `hidden_size` znače više brojeva i više memorije. Poglavlje 8 te vrijednosti pretvara u gigabajte. `max_position_embeddings` je gornja granica modela, a stvarnu duljinu konteksta biraš sam pri pokretanju i plaćaš je memorijom.

Polje `torch_dtype` kaže da su brojevi zapisani u formatu BF16, dakle po 2 bajta (poglavlje 7).

## Virni u težine

Nacrt tvrdi da model ima 36 slojeva širine 2048. Zaglavlje datoteke s težinama pokazuje stoji li to doista. Safetensors datoteka počinje s 8 bajtova koji kažu koliko je dugo zaglavlje, a zaglavlje je običan JSON s nazivom i oblikom svakog tenzora. Dovoljno je pročitati sam početak datoteke. Ovdje samo viriš; format i njegova sigurnost tema su poglavlja 10.

::: {.vjezba}
**Vježba: prebroji parametre iz zaglavlja** `CPU` · RAM 1 GB · disk 1 MB · 5 min

Treba ti internet i Python bez dodatnih paketa. U bashu preuzmi samo prvih 100 kB svakog dijela. Zaglavlje je kraće od toga.

```bash
B=https://huggingface.co/HuggingFaceTB/SmolLM3-3B/resolve/main
for d in model-00001-of-00002 model-00002-of-00002; do
  curl -sL -r 0-99999 "$B/$d.safetensors" -o $d.safetensors
done
```

Spremi skriptu kao `zaglavlje.py`:

```python
import json, math, struct, sys

ukupno = 0
for put in sys.argv[1:]:
    with open(put, "rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]    # duljina zaglavlja
        z = json.loads(f.read(n))                # samo JSON, bez težina
    z.pop("__metadata__", None)
    par = sum(math.prod(t["shape"]) for t in z.values())
    print(put, n, "B,", len(z), "tenzora,", par, "par.")
    ukupno += par
print("UKUPNO", ukupno, "parametara,", ukupno * 2, "bajtova")
```

Množenje s 2 vrijedi jer su svi tenzori ovog modela BF16. Pokreni je:

```text
$ python zaglavlje.py model-00001-of-00002.safetensors \
    model-00002-of-00002.safetensors
model-00001-of-00002.safetensors 29944 B, 258 tenzora, 2483142656 par.
model-00002-of-00002.safetensors 7800 B, 68 tenzora, 591955968 par.
UKUPNO 3075098624 parametara, 6150197248 bajtova
```

Skripta ne ovisi o brzini stroja, pa ćeš dobiti iste brojeve dok god se repozitorij ne promijeni. Pokreni je i usporedi. Preuzete datoteke od 100 kB nisu model, pa ih poslije obriši.

Cijeli model možeš pregledati skriptom `prilozi/vjezbe/l2_mapa_modela.py`, ali za nju treba 6,17 GB preuzetih datoteka.
:::

Tenzori prvog sloja i oni izvan slojeva izgledaju ovako (ispis skripte iz priloga, sa suženim stupcima):

```text
model.embed_tokens.weight                      [128256, 2048] BF16
model.layers.0.input_layernorm.weight          [2048]         BF16
model.layers.0.mlp.down_proj.weight            [2048, 11008]  BF16
model.layers.0.mlp.gate_proj.weight            [11008, 2048]  BF16
model.layers.0.mlp.up_proj.weight              [11008, 2048]  BF16
model.layers.0.post_attention_layernorm.weight [2048]         BF16
model.layers.0.self_attn.k_proj.weight         [512, 2048]    BF16
model.layers.0.self_attn.o_proj.weight         [2048, 2048]   BF16
model.layers.0.self_attn.q_proj.weight         [2048, 2048]   BF16
model.layers.0.self_attn.v_proj.weight         [512, 2048]    BF16
model.norm.weight                              [2048]         BF16
```

Prepoznaješ brojeve iz `config.json`: 128256, 2048 i 11008. Nazive tenzora čitaš u poglavlju 6, a zasad je dovoljno znati da je oblik obična tablica: `[2048, 2048]` su 2048 redaka po 2048 brojeva. Broj parametara dobiješ množenjem, pa cijeli model možeš izračunati i ručno.

```text
tablica tokena   128256 x 2048              =   262 668 288

jedan sloj:
  3 x MLP        3 x 11008 x 2048           =    67 633 152
  q_proj, o_proj 2 x 2048 x 2048            =     8 388 608
  k_proj, v_proj 2 x 512 x 2048             =     2 097 152
  2 normalizacije 2 x 2048                  =         4 096
  jedan sloj ukupno                         =    78 123 008

36 slojeva       36 x 78 123 008            = 2 812 428 288
završna norm.                               =         2 048
UKUPNO                                      = 3 075 098 624
```

Ručni račun i skripta daju isti broj: 3,075 milijardi, odnosno **3B** iz naziva modela. Pomnoženo s 2 bajta daje 6 150 197 248 bajtova, što je i `total_size` u kazalu. Nacrt, težine i naziv se slažu.

Račun otkriva još jednu sitnicu. Nema zasebnog tenzora za izlaz modela jer `tie_word_embeddings: true` znači da model za ulaz i izlaz koristi istu tablicu tokena, pa je ona u datoteci samo jednom.

Nacrt i težine moraju se slagati. U vježbi s drugim modelom, opisanoj u poglavlju 17, iz težina je uklonjeno šest slojeva, a `config.json` je i dalje tvrdio da ih je 30. `from_pretrained` nije javio grešku: nedostajuće slojeve popunio je nasumičnim brojevima, a izlaz je bio loš.

Ova je mapa zamišljena za rad u Pythonu i za izmjene modela, pa je svaki dio u svojoj datoteci. GGUF iz poglavlja 2 sve to pakira u jednu datoteku, s metapodacima, tokenizatorom, predloškom i obično kvantiziranim težinama, pa je pogodniji za samo pokretanje (poglavlje 10).

## Otvorene težine i otvoreni kod

Model s Hugging Facea često se naziva "open source". Točniji naziv za većinu takvih modela je **model otvorenih težina (open weight)**. Kod otvorenog softvera dobivaš izvorni kod, možeš ga pročitati, izmijeniti i iznova prevesti. Težine više nalikuju gotovom prevedenom programu: možeš ih koristiti, ali recept po kojem su nastale ostaje kod autora.

| Što | Obično dobivaš? |
|---|---|
| Težine, `config.json`, tokenizator, predložak | da |
| Dopuštenje za korištenje | ovisi o licenci |
| Podaci za trening | obično ne |
| Kod i postavke treninga | obično ne |
| Mogućnost da model ponovno izradiš | gotovo nikad |

Postoje iznimke. SmolLM3 na svojoj kartici modela objavljuje dio podataka, konfiguracije i kod treninga, ali i tamo piše da će podaci iz kasnijih faza treninga biti objavljeni naknadno (stanje u studenom 2026.). Zato čitaj što je stvarno objavljeno i ne oslanjaj se na oznaku.

U praksi razlika znači sljedeće.

**Ne možeš provjeriti podrijetlo.** Bez podataka za trening ne znaš što je model vidio, koliko je tu bilo hrvatskog ni smije li se taj sadržaj koristiti. To može biti važno kad model ide u poslovni sustav.

**Ne možeš ga ponovno izgraditi, ali ga možeš doraditi.** Kod običnog programa popravak u izvornom kodu i novo prevođenje rješavaju stvar. Kod modela polaziš od gotovih težina i podešavaš ih, što je tema poglavlja 15.

**Otvorene težine ne možeš pregledati čitanjem.** Tri milijarde brojeva možeš otvoriti, prebrojiti i usporediti, ali iz njih ne možeš pročitati što model zna ni ima li skriveno ponašanje. Pregled koda ovdje nema pravu zamjenu. Možeš samo mjeriti ponašanje na vlastitim primjerima, što počinje zlatnim skupom (gold set) u poglavlju 9, i provjeravati sve što nije broj, primjerice predložak, kao u poglavlju 10.

Unatoč tome dobivaš mnogo: model radi na tvom računalu, podaci ne izlaze van, a inačica se ne mijenja bez tvog znanja. Licenca zasebno određuje što smiješ raditi. Oznaka "open" sama po sebi ne jamči komercijalnu upotrebu, a licence obrađuje poglavlje 9.

## Kako čitati naziv modela

Naziv modela najčešće je sažeta specifikacija. Rastavi datoteku iz poglavlja 2:

| Dio | Što znači |
|---|---|
| `gemma` | obitelj modela (autor Google) |
| `4` | generacija |
| `E2B` | veličina |
| `it` | instruction-tuned, naučen slijediti upute |
| `Q4_K_M` | način kvantizacije (poglavlje 11) |
| `.gguf` | format datoteke (poglavlje 10) |

**Veličina.** `B` je *billion*, na hrvatskom milijarda parametara, a `M` milijun, kao u `SmolLM2-135M-Instruct`. Slovo `B` u nazivu nema veze s bajtovima, o čemu više u poglavlju 7. Upozorenje daje upravo ovaj primjer: slovo `E` znači *effective*. Prema kartici modela, E2B ima 2,3 milijarde efektivnih parametara i 5,1 milijardu s tablicama embeddinga. Broj u nazivu zato nije uvijek broj koji ćeš naći u datoteci, pa ga provjeri.

**Bazni i podešeni model.** Bazni model (base) treniran je da nastavlja tekst. Daš li mu pitanje, može nastaviti nizom sličnih pitanja. Instrukcijski model dodatno je treniran da odgovara na upute, a tu inačicu želiš za razgovor. Oznake su različite: `-it` kod Gemme, `-Instruct` kod SmolLM2. Pravilo nije univerzalno jer `SmolLM3-3B` nema nikakvu oznaku, a bazni mu se model zove `SmolLM3-3B-Base`. Provjeri `base_model` u metapodacima.

**Tko je objavio.** Dio ispred kose crte često je važniji od naziva datoteke:

- **Izvornik:** `google/gemma-4-E2B-it`, od autora, u safetensorsu.
- **Kvantizirana kopija:** `unsloth/gemma-4-E2B-it-GGUF`, težine istog modela, koje je netko drugi pretvorio i kvantizirao. U metapodacima kao `base_model` stoji `google/gemma-4-E2B-it`. Takav repozitorij sadrži više od dvadeset GGUF inačica, od kojih ti treba jedna.
- **Fino podešen model (fine-tune):** netko je na izvornik dodao vlastiti trening, pa to više nije isti model. Prihvati ga kao novi model nepoznate kvalitete i ispitaj ga.

Sumnjiv ili nepoznat vlasnik nosi i sigurnosni rizik, koji obrađuje poglavlje 10.

::: {.kvar}
**Simptom → uzrok**

- Program javlja da ne poznaje arhitekturu modela → program je stariji od modela. Ažuriraj program, težine ne diraj.
- Biblioteka ne nalazi težine iako su `.safetensors` na disku → nedostaje `model.safetensors.index.json` ili jedan dio. Usporedi popis s repozitorijem.
- Učitavanje prolazi, a izlaz je besmislen → `config.json` ili tokenizator ne pripadaju tim težinama. Preuzmi sve datoteke iz istog repozitorija.
- Model nastavlja tvoje pitanje umjesto da odgovori → bazni model ili predložak koji nedostaje. Provjeri oznaku u nazivu i `base_model`, zatim predložak (poglavlje 5).
- Model ne prestaje generirati → krivi token kraja ili predložak. Provjeri `generation_config.json` i predložak.
- Preuzimanje traje satima, a disk se puni → preuzimaš cijeli GGUF repozitorij. Preuzmi samo jednu datoteku.
- Licencu ne možeš naći → nemaš potvrdu da model smiješ koristiti. Provjeri metapodatke i karticu modela, a bez potvrde ga ne koristi u poslu.
:::

## Sažetak

Model se sastoji od težina, koje su brojevi u datoteci, i zasebnog programa koji s njima računa. Mapa modela uz težine sadrži nacrt (`config.json`), tokenizator, predložak, postavke generiranja i opis, a zajedno čine manje od 0,3 % veličine. Račun iz samog zaglavlja daje 3 075 098 624 parametra, što potvrđuje naziv "3B" i oznaku od 6,15 GB. Otvorene težine možeš pokrenuti i doraditi, ali podaci i recept treninga obično nisu objavljeni, a ponašanje modela ne možeš provjeriti čitanjem brojeva. U poglavlju 4 ulaziš u prvu od tih datoteka: tokenizator.
