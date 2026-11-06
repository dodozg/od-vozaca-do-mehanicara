# Unutar motora

::: {.cilj}
**Nakon ovog poglavlja znaš:**

- što se događa s tokenom od ulaska u model do izbora sljedećeg tokena
- čitati nazive poput `model.layers.5.self_attn.q_proj.weight` i reći čemu služe
- koje postavke uzorkovanja mijenjati i kada
- zašto MoE model s malo aktivnih parametara ipak traži golemu memoriju
:::

Model znaš pokrenuti (poglavlje 2) i znaš što je u njegovoj mapi (poglavlje 3). Ostaje pitanje što te milijarde brojeva zapravo rade. Za odgovor ne treba matematika matrica. Dovoljno je pratiti jedan token kroz motor, redom kojim ga model obrađuje.

![Put tokena kroz model: embedding, N puta pažnja i MLP, glava i logiti](slike/motor.svg)

## Embedding: token postaje vektor

Iz poglavlja 4 znaš da tokenizator tekst pretvara u ID-eve. ID je samo redni broj. Token 5000 nije ništa sličniji tokenu 5001 nego tokenu 90, pa model iz samog ID-a ne može iščitati značenje.

Zato model drži veliku tablicu s jednim retkom za svaki token iz rječnika. Redak je popis brojeva, a takav popis zovemo vektor. Tijekom treninga brojevi se slože tako da tokeni sličnog značenja dobiju slične vektore. Taj korak zove se ugrađivanje, ali u praksi svi kažu embedding, pa ćemo i mi.

Tablica se u datoteci težina zove `model.embed_tokens.weight`, a oblik joj je `[vocab_size, hidden_dim]`. U Llama 3 8B to je 128 256 redaka s po 4096 brojeva. Širina vektora, `hidden_dim`, u `config.json` piše kao `hidden_size` i provlači se kroz cijeli model. Sam embedding je obično čitanje retka iz tablice, pa isti token ovdje uvijek dobije isti vektor. Kontekst stiže tek u sljedećim koracima.

## Položaj: odakle modelu redoslijed

Usporedi "Prvo isključi pumpu, pa otvori ventil" i "Prvo otvori ventil, pa isključi pumpu". Riječi su iste, a postupak obrnut. Pažnja (attention), koju upoznajemo u sljedećem odjeljku, sama po sebi vidi samo skup vektora i ne zna koji je prvi, pa se položaj mora dodati posebno. Današnji modeli uglavnom koriste RoPE (Rotary Position Embedding): prije usporedbe vektore zakrene za kut koji ovisi o položaju tokena, pa zakret u usporedbu unese razmak među tokenima. Taj se račun izvodi usput i ne traži vlastitu tablicu težina. Model je ipak treniran na ograničenoj duljini, zapisanoj u `config.json` kao `max_position_embeddings`. Kako se ta granica pomiče s pomoću YaRN-a, vidjet ćeš u poglavlju 17.

## Pažnja: tokeni gledaju jedni druge

Uzmi rečenicu tehničara iz Kvake: "Perilica curi jer je puklo crijevo. Zamijeni ga." Da bi nastavio smisleno, model mora znati da se "ga" odnosi na crijevo, a ne na perilicu. Vektor tokena "ga" sam to ne sadrži jer je pročitan iz tablice bez ikakvog konteksta. Pažnja rješava upravo to: svaki token skuplja informacije od tokena prije sebe. Pri generiranju token gleda samo unatrag jer ono što slijedi još ne postoji.

### Upit, ključ, vrijednost

Zamisli knjižnicu. Dolaziš s pitanjem, knjige na hrptu imaju natpise, a kad natpis odgovara, čitaš sadržaj. Pažnja od svakog vektora s pomoću triju naučenih tablica napravi tri nova vektora:

- **Upit (Query):** što ovaj token traži.
- **Ključ (Key):** što ovaj token nudi drugima, natpis na hrptu.
- **Vrijednost (Value):** što token predaje ako ga netko izabere, sadržaj knjige.

Upit tokena "ga" uspoređuje se s ključem svakog ranijeg tokena i svaka usporedba daje ocjenu. Ocjene se preračunaju u udjele čiji je zbroj 1, a token dobije smjesu vrijednosti prema tim udjelima. Ako je model dobro treniran, "crijevo" dobije velik udio. Na kraju četvrta tablica, izlaz (Output), složi rezultat u vektor koji ide dalje.

Priča o traženju imenice služi samo razumijevanju. Nitko nije programirao što upit znači. Ti su se brojevi složili tijekom treninga jer su pomagali predviđanju.

### Više glava

Jedna usporedba hvata jednu vrstu odnosa, a jezik ih ima mnogo: na što se zamjenica odnosi, koji glagol ide uz koji subjekt, što je negirano. Zato se vektor reže na komade i svaki komad radi vlastitu usporedbu. Takav komad zove se glava (head), a postupak višeglava pažnja (multi-head attention). Llama 3 8B ima 32 glave, pa širinu 4096 dijeli na 32 komada od po 128 brojeva. Izlazna tablica zatim spaja rezultate svih glava.

Riječ "glava" koristi se i za `lm_head` na kraju modela. To je drugi dio, a ime je slučajno isto.

### GQA

Grupna pažnja (GQA, Grouped-Query Attention) štedi tako da sve glave i dalje postavljaju vlastite upite, a ključeve i vrijednosti dijele u grupama. Llama 3 8B ima 32 glave, ali samo 8 kompleta ključeva i vrijednosti, što u `config.json` piše kao `num_key_value_heads`. Taj broj trebat će ti u poglavlju 8 jer model ključeve i vrijednosti ranijih tokena drži u memoriji za vrijeme generiranja.

## MLP: svaki token prerađuje što je skupio

Pažnja skuplja informacije, ali ih malo prerađuje. Preradu obavlja MLP (Multi-Layer Perceptron), blok koji svaki token obrađuje zasebno, bez gledanja u druge. U modernim modelima ima tri tablice:

- `up_proj` širi vektor, u Llama 3 8B s 4096 na 14 336 brojeva. Širi prostor daje više mjesta za kombiniranje onoga što je stiglo.
- `gate_proj` također širi vektor i iz njega računa ventil: za svaki broj odlučuje koliko će ga propustiti.
- `down_proj` vraća rezultat na 4096 brojeva da može u idući korak.

Spoj ventila i širenja zove se SwiGLU. Taj ćeš naziv vidjeti u dokumentaciji, a dovoljno je znati da su `gate_proj` i `up_proj` par koji radi zajedno.

## Slojevi, zaobilaznice i normalizacija

Pažnja i MLP zajedno čine sloj (layer). Sloj prima vektore širine 4096 i vraća vektore iste širine, pa se slojevi slažu jedan na drugi poput jednakih karika. Llama 3 8B ima 32 sloja. Grubo rečeno, prvi slojevi hvataju jednostavnije odnose, a kasniji grade na njihovim rezultatima.

Oko pažnje i oko MLP-a vodi zaobilaznica (residual): ulaz se pribroji izlazu. Dio zato samo računa što treba promijeniti, a izvorna informacija teče dalje netaknuta. Bez toga bi se duboki modeli vrlo teško trenirali.

Prije svakog dijela stoji i normalizacija, kod Llame `RMSNorm`, koja brojeve drži u stalnom rasponu da ne narastu ili ne iščeznu kroz 32 koraka. Ima malo parametara i rijetko će te zanimati. Zapamti samo njezina imena jer ih susrećeš u datoteci.

## Kako se tenzori zovu

Sad možeš čitati nazive. Tablicu brojeva u datoteci zovemo tenzor (detaljno u poglavlju 7), a naziv mu opisuje adresu u modelu:

```text
model.layers.{i}.self_attn.q_proj.weight
             sloj  pažnja   upit   težine
```

Umjesto `{i}` stoji broj sloja, u Llama 3 8B od 0 do 31. Svaki sloj ima isti komplet, pa u tablici izostavljamo početak `model.layers.{i}.` i završetak `.weight`. Oblik je zapisan kao `[izlaz, ulaz]`.

| Naziv | Što je | Oblik u Llama 3 8B |
|---|---|---|
| `model.embed_tokens.weight` | embedding | 128256, 4096 |
| `self_attn.q_proj` | upit | 4096, 4096 |
| `self_attn.k_proj` | ključ | 1024, 4096 |
| `self_attn.v_proj` | vrijednost | 1024, 4096 |
| `self_attn.o_proj` | izlaz pažnje | 4096, 4096 |
| `mlp.gate_proj` | ventil | 14336, 4096 |
| `mlp.up_proj` | širenje | 14336, 4096 |
| `mlp.down_proj` | sužavanje | 4096, 14336 |
| `input_layernorm` | norma prije pažnje | 4096 |
| `post_attention_layernorm` | norma prije MLP-a | 4096 |
| `model.norm.weight` | završna norma | 4096 |
| `lm_head.weight` | glava | 128256, 4096 |

Na manjim tablicama `k_proj` i `v_proj` vidi se GQA: 8 kompleta po 128 brojeva daje 1024. Na ovim nazivima počiva gađanje slojeva u LoRA treningu (poglavlje 15) i kirurgija nad modelom (poglavlje 17).

Dvije stvari te mogu zbuniti. Neki modeli dijele istu tablicu za embedding i glavu, pa `lm_head.weight` u njihovoj datoteci uopće nema, i to nije kvar. GGUF koristi vlastita imena, primjerice `token_embd.weight` i `output.weight` (poglavlje 11).

## Logiti i glava

Nakon zadnjeg sloja imamo vektor širine 4096 za zadnji token. Glava (`lm_head`) ga pretvara u 128 256 brojeva, po jedan za svaki token iz rječnika. Ti se brojevi zovu logiti (logits). Oni još nisu vjerojatnosti: mogu biti i negativni i ne zbrajaju se u 1. Veći logit znači da model taj token smatra boljim nastavkom. Jednostavna formula, softmax, pretvara ih u vjerojatnosti.

Ovdje računanje staje. Model je dao ocjene za sve moguće tokene, a izbor još nije napravljen. Izabrani token dodaje se na kraj teksta i krug kreće ispočetka.

## Uzorkovanje: kako se bira sljedeći token

Uzorkovanje (sampling) je pravilo izbora. Nije dio težina i možeš ga mijenjati pri svakom pozivu. Pretpostavimo da model nastavlja "Zamijeni" i da je svaka riječ jedan token. Logiti u tablici izmišljeni su za primjer, a račun je pravi.

| Token | Logit | T = 0,5 | T = 1 | T = 2 |
|---|---|---|---|---|
| crijevo | 5,0 | 93,4 % | 70,9 % | 47,3 % |
| brtvu | 3,5 | 4,7 % | 15,8 % | 22,4 % |
| pumpu | 3,0 | 1,7 % | 9,6 % | 17,4 % |
| filter | 2,0 | 0,2 % | 3,5 % | 10,6 % |
| ljubav | −1,0 | 0,0 % | 0,2 % | 2,4 % |

**Temperatura (`temperature`)** dijeli logite prije pretvaranja u vjerojatnosti. Ispod 1 pojačava razlike i model se drži najboljih kandidata. Iznad 1 ih poravnava, pa i "ljubav" dobije pravu priliku. Temperatura 0 uvijek uzima najvjerojatniji token.

**Top-k** zadržava samo k najboljih tokena i ostale odbacuje. Uz k = 2 i T = 1 ostaju crijevo i brtvu.

**Top-p** zadržava najmanju skupinu najboljih tokena čiji zbroj vjerojatnosti doseže p. Uz p = 0,9 i T = 1 ostaju tri tokena jer 70,9 + 15,8 = 86,7 % još nije dovoljno, a s pumpom je zbroj 96,3 %. Veličina skupine prilagođava se situaciji: kad je model siguran, ostaje ih malo, a kad nije, više.

**Kazna za ponavljanje (`repeat_penalty`)** smanjuje izglede tokenima koji su se nedavno pojavili, po zadanome u zadnja 64 tokena. Vrijednost 1,0 znači da je isključena.

### Što mijenjati u praksi

U llama.cpp zastavice su `--temp`, `--top-k`, `--top-p` i `--repeat-penalty`, a u API-ju polja `temperature`, `top_k`, `top_p` i `repeat_penalty`. Zadane vrijednosti u dokumentaciji za `llama-cli` su 0,80, 40, 0,95 i 1,00, uz još jedan filtar, `--min-p 0.05`, koji odbacuje tokene s manje od 5 % vjerojatnosti najboljeg (stanje u studenom 2026.; provjeri `--help` svoje inačice). Ostali alati imaju svoje zadane vrijednosti.

Pravila za početak:

1. **Mijenjaj najprije temperaturu.** Ostalo ostavi na zadanim vrijednostima. Top-k i top-p rade sličan posao, pa rijetko ima smisla dirati više postavki odjednom.
2. **Izvlačenje podataka, odgovori iz dokumentacije:** temperatura od 0 do 0,3. Za Kvakine zapisnike uzmi 0 jer ti trebaju isti ulaz i isti izlaz.
3. **Slobodno pisanje i ideje:** temperatura od 0,7 do 1,0.
4. **Kazna za ponavljanje:** samo ako model stvarno vrti isti tekst, i to blago, od 1,05 do 1,15. Kod JSON-a je drži na 1,0 jer JSON mora ponavljati navodnike, zagrade i nazive polja.
5. **Usporedba dvaju modela ili postavki:** učvrsti slučajnost sa `--seed` ili uzmi temperaturu 0.

To su uobičajene polazne točke, bez mjerenja iza njih. Što je najbolje za tvoj zadatak, pokazat će zlatni skup iz poglavlja 9.

::: {.vjezba}
**Vježba: temperatura u ruci** `CPU` · RAM zanemariv · disk zanemariv · 5 min

Spremi kao `temperatura.py` i pokreni s `python temperatura.py`. Dodaj u popis `0.1` i `5.0` pa gledaj što se događa s "ljubavi".

```python
import math

logiti = {"crijevo": 5.0, "brtvu": 3.5, "pumpu": 3.0,
          "filter": 2.0, "ljubav": -1.0}

for T in (0.5, 1.0, 2.0):
    e = {t: math.exp(v / T) for t, v in logiti.items()}
    zbroj = sum(e.values())
    print(f"T={T}:", *(f"{t} {x / zbroj * 100:.1f}"
                       for t, x in e.items()))
```

Zatim isto probaj na stvarnom modelu: naredbi iz poglavlja 2 dodaj jednu od ovih postavki i dvaput postavi isto pitanje.

```bash
--temp 0 --seed 42
--temp 1.8
```

Python skripta pokrenuta je i daje brojke iz tablice.

Zastavice smo pokrenuli na Gemmi 4 E2B Q4_K_M, llama.cpp b12110, laptop s i5-10210U bez GPU-a, pitanje iz poglavlja 2, `-n 40 -rea off --seed 42`, svaka postavka dvaput. Izlaz je skraćen na prvih 40 tokena:

| `--temp` | Početak odgovora |
|---|---|
| 0 | Perilica rublja ne izbacuje vodu jer je kanal za odvod za vodu začepljen ili blokiran. |
| 0,8 | Perilica rublja ne izbacuje vodu jer je možda začepljena cijev za odvod ili filter za vodu blokiran. |
| 1,8 | Perilica rublja ne izbacuje vodu jer je problem najčešće blokiran ispušni otvor ili filter za vodu. |

Dva pokretanja s istim `--seed` dala su istu rečenicu pri svakoj temperaturi, a razlika među temperaturama vidi se već u prvoj rečenici. Temperatura 1,8 ipak nije dala besmislicu. Razlog je redoslijed u lancu: ispis `llama-completion` pokazao je da se `top-k`, `top-p` i `min-p` primjenjuju prije temperature, pa visoka temperatura bira samo među tokenima koji su prošli filtre. Isti ispis pokazao je i da su zadane vrijednosti za ovu Gemmu 1,0, 64, 0,95 i 0,05, a ne one iz dokumentacije. Razlog nismo istraživali.
:::

## Gdje parametri zapravo sjede

Pažnja je slavni dio ovih modela, pa bi se očekivalo da nosi i većinu težina. Račun iz tablice oblika kaže drukčije. Evo Llame 3 8B:

| Dio | Milijarde parametara | Udio |
|---|---|---|
| embedding i glava | 1,05 | 13 % |
| pažnja | 1,34 | 17 % |
| MLP | 5,64 | 70 % |
| ukupno | 8,03 | 100 % |

Račun je jednostavan. Jedna tablica MLP-a ima 4096 × 14 336 ≈ 58,7 milijuna parametara, a u sloju su tri, dakle oko 176 milijuna. Pažnja ima dvije tablice od 16,8 milijuna i dvije od 4,2 milijuna, dakle 42 milijuna po sloju. Sve to puta 32 sloja daje brojke iz tablice. MLP je težak zato što širi vektor i što ima tri takve tablice, a GQA dodatno stanjuje pažnju. Norme zajedno imaju oko 0,27 milijuna parametara i ne vide se u zaokruživanju.

Omjer se razlikuje od modela do modela, a slika je obično slična: kad gledaš veličinu datoteke, gledaš pretežno MLP. Zato sljedeći korak množi baš taj blok.

## MoE: više MLP-a, a isti posao po tokenu

Više parametara obično znači više znanja, ali i sporiji model jer svaki token prolazi kroz sve njih. MoE (Mixture of Experts) to zaobilazi. Umjesto jednog MLP-a sloj ima više paralelnih, koji se zovu stručnjaci (experts). Pažnja ostaje zajednička.

![Sloj MoE modela: usmjerivač bira stručnjake, a svi ostaju u memoriji](slike/moe.svg)

Mala mreža zvana usmjerivač (router) gleda vektor tokena i svakom stručnjaku daje ocjenu. Pravilo Top-K zatim propušta K najbolje ocijenjenih, na gornjem dijelu slike 2 od 8. Računaju samo oni, a njihovi se izlazi zbroje s težinama prema ocjenama. Izbor se ponavlja za svaki token, u svakom sloju. Stručnjacima nitko ne dodjeljuje teme, pa "stručnjak za matematiku" obično nije točna slika onoga što se u njima dogodi tijekom treninga.

Pazi na dvije podudarnosti u imenima. Top-K ovdje bira stručnjake i nema veze s top-k uzorkovanjem. Usmjerivač se u kodu često zove `gate`, što nema veze s `gate_proj`.

Odatle dva broja na opisu modela:

- **Ukupni parametri:** sve što model ima.
- **Aktivni parametri:** koliko ih računa za jedan token.

Na računskom primjeru s donjeg dijela slike, Llama 3 8B s 3 stručnjaka i K = 1: umnožava se samo MLP, pa je ukupno 8,03 + 2 × 5,64 ≈ 19,3 milijarde, a aktivnih ostaje 8,03 milijarde. Takav model ne postoji, a računica pokazuje odnos. Stvarni primjer je Kimi K3: 2,8 bilijuna parametara ukupno i 104 milijarde aktivnih, dakle oko 3,7 % (sekundarni izvor, stanje u studenom 2026.).

Sad dolazi posljedica. Usmjerivač za sljedeći token može izabrati bilo kojeg stručnjaka, pa svi moraju biti pri ruci. **Aktivni broj ne govori koliko memorije treba.** Računaj s ukupnim. Ako parametar zauzima 2 bajta (zapis BF16 iz poglavlja 7), naš primjer treba oko 38,6 GB, a aktivni broj bi naveo na 16 GB. Kimi K3 bi uz isti zapis tražio 5,6 TB, a aktivni broj sugerira 208 GB. Aktivni broj govori nešto o računskom poslu po tokenu. Memoriju i brzinu detaljno računamo u poglavlju 8.

::: {.kvar}
**Simptom → uzrok**

- Model vrti istu rečenicu → najprije provjeri predložak i token kraja (poglavlje 5). Ako su u redu, podigni temperaturu ili uzmi blagu kaznu od 1,1.
- Model ne staje i piše u ime korisnika → gotovo uvijek predložak (poglavlje 5). Uzorkovanje to ne popravlja.
- Besmislene riječi i miješanje jezika → možda previsoka temperatura. Spusti je, a ako ne pomogne, provjeri predložak i datoteku.
- Besmislica i uz temperaturu 0 → uzorkovanje nije krivo. Provjeri predložak, datoteku (poglavlje 10) i kvantizaciju (poglavlja 11 i 12).
- JSON se raspada, polja nestaju ili se izobličuju → kazna za ponavljanje iznad 1,0. Vrati je na 1,0, a za stalni oblik vidi poglavlje 13.
- Rezultati testa skaču između dva pokretanja → uzorkovanje je slučajno. Uzmi temperaturu 0 ili fiksni `--seed`.
- Tekst je bezbojan i uvijek isti → preniska temperatura za taj posao.
- MoE model "od 100 milijardi" ne stane u memoriju → gledaš aktivne parametre. Računaj s ukupnima.
:::

## Sažetak

Token postaje vektor u tablici `embed_tokens`, položaj mu daje RoPE, a zatim kroz svaki sloj prolazi pažnju, koja skuplja informacije od drugih tokena, i MLP, koji ih prerađuje. Glava na kraju daje logit za svaki token iz rječnika, a uzorkovanje bira sljedeći; u praksi najčešće mijenjaš samo temperaturu. Nazivi tenzora slijede stalnu shemu, a u Llama 3 8B oko 70 % parametara sjedi u MLP-u, ne u pažnji. MoE zato umnožava baš MLP i po tokenu računa samo dio stručnjaka. U memoriji ipak mora biti sve, pa za RAM vrijedi ukupan broj parametara, a aktivni o tome ne govori.
