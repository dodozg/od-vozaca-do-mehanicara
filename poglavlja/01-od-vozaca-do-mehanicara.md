# Od vozača do mehaničara

::: {.cilj}
**Nakon ovog poglavlja znaš:**

- je li ova knjiga za tebe i što ćeš nakon nje moći
- što se mijenja kad težine modela držiš sam, a što ostaje tvoja briga
- kako svojim brojkama izračunati prag isplativosti za API, najam GPU-a i vlastiti hardver
- kako je knjiga složena i što ti treba za početak
:::

Ovo je stvarni ispis s običnog laptopa. Model je dobio jedan zadatak na hrvatskom: u tri rečenice objasni zašto perilica rublja ne izbacuje vodu i što prvo treba provjeriti. Nakon 38 sekundi ispis je završio ovako:

```text
[Start thinking]

Thinking Process:

1.  **Analyze the Request:** The user wants an explanation [...]
[...]
5.  **Refine and Translate to Croatian (Focusing on clarity

[ Prompt: 87.8 t/s | Generation: 8.2 t/s ]
```

Odgovora nema. Zadnja rečenica staje na pola, a nijedna poruka ne javlja grešku.

U ChatGPT-u, Claudeu ili Geminiju takvo što rijetko vidiš jer netko drugi već brine o tim postavkama. Tko zna gledati, ovdje odmah vidi uzrok. Naredba je dopustila najviše 256 tokena (komadića teksta, poglavlje 4), a model je po zadanim postavkama krenuo razmišljati naglas i na to potrošio sve. Jedna zastavica, `-rea off`, gasi razmišljanje (thinking), pa isti model na istom laptopu daje odgovor za 25 sekundi. Sposobnost da to prepoznaš tema je ove knjige.

## Vozač i mehaničar

Vjerojatno već dobro voziš. Svaki dan radiš s jezičnim modelima, znaš pisati promptove, osjetiš kad model izmišlja i znaš koji alat uzeti za koji posao. To je prava vještina koju ova knjiga ne omalovažava.

Vozač ipak ima granicu. Kad se na cesti pojavi čudan zvuk, može promijeniti stil vožnje ili otići u servis. Ne zna što taj zvuk znači, pa ne može procijeniti je li popravak skup ni ima li smisla ugraditi drugi dio. Isto vrijedi za korisnika modela. Zašto je odgovor odjednom gori? Zašto hrvatski tekst košta više od engleskog? Treba li nam fino podešavanje (fine-tuning), kako tvrdi prodavač, ili bi bolji prompt riješio stvar? Iz vozačkog sjedala možeš samo nagađati.

Mehaničar ne mora biti bolji vozač jer radi drugi posao: otvara haubu, mjeri, mijenja dio, pa opet mjeri. Odatle naslov knjige, a poglavlja prate isti redoslijed: najprije voziš, zatim otvaraš, mjeriš, mijenjaš i na kraju isporučuješ.

Knjiga je za tebe ako dobro poznaješ AI alate, a model još ne pokrećeš sam, pa te zanima što se događa ispod haube. Programiranje ti pomaže, ali ne moraš biti programer. Na kraju ćeš moći pokrenuti model lokalno, otvoriti ga i razumjeti što vidiš, izračunati koliko hardvera treba, kvantizirati ga, to jest smanjiti zapis brojeva (quantization), izmjeriti štetu, odlučiti treba li fino podešavanje, napraviti LoRA adapter i dijagnosticirati kvar.

Ne mora svaki vozač postati mehaničar. Tko razumije motor, bolje vozi i teže ga je prevariti u servisu. Ovo znanje vrijedi i ako nikad ne napustiš API: lakše čitaš ponude, razumiješ račun za tokene i prepoznaješ obećanja koja se ne mogu ispuniti.

## Što se mijenja kad držiš težine

Težine (weights) su milijarde brojeva koji čine model. Kad radiš preko API-ja, ti šalješ tekst, a one ostaju kod dobavljača. Model otvorenih težina (open weight) možeš preuzeti kao datoteku.

**Model se ne mijenja bez tvoje odluke.** Datoteka na disku danas i za tri godine daje isti model. Dobavljač ga ne može povući s ponude ni tiho zamijeniti novom inačicom.

**Podaci ne moraju nikamo.** Ako model radi na tvom stroju, tekst ne izlazi iz tvoje mreže.

**Vidiš sve.** Možeš pročitati točan tekst koji model prima (poglavlje 5), svaki token i svako vrijeme u ispisu. Kvar s početka ovog poglavlja vidljiv je upravo zato.

**Možeš mijenjati.** Biraš preciznost zapisa, duljinu konteksta i uzorkovanje (sampling), a možeš dodati i adapter naučen na svojim primjerima.

Ima to i svoju cijenu. Sve što se pokvari tvoje je: ažuriranja, memorija, sigurnost datoteka koje preuzimaš (poglavlje 10), licenca modela (poglavlje 9) i zaštitni slojevi koje je dobavljač dosad vodio umjesto tebe. Trošak se seli s računa za tokene na hardver i tvoje sate.

## Kada se isplati, a kada ne

Često je ispravna odluka ostati na API-ju. Za većinu malih i neravnomjernih poslova tako ispada i račun. Ostani na API-ju ako:

- imaš malo zahtjeva ili ih imaš povremeno
- trebaš najbolju kvalitetu koju možeš kupiti, a ona dolazi od modela koji se ne može preuzeti
- nemaš nikoga tko će održavati stroj
- još ne znaš hoće li posao uopće zaživjeti
- ugovor s dobavljačem i tvoja pravna procjena dopuštaju slanje tih podataka

Vlastite težine imaju smisla ako:

- podaci ne smiju izaći iz tvoje kontrole, zbog ugovora ili procjene rizika
- imaš velik i stalan promet, pa račun iz sljedećeg odjeljka izlazi u tvoju korist
- trebaš istu inačicu modela godinama ili rad bez interneta
- trebaš preinaku koju dobavljač ne nudi
- želiš naučiti zanat, što je dovoljan razlog za učenje, ali ne i za odluku o pogonu

Između API-ja i vlastitog stroja stoji **najam GPU-a**: po satu plaćaš tuđi stroj s grafičkom karticom i sam na njemu pokrećeš model. GPU je kartica s vlastitom brzom memorijom, a u poglavlju 8 vidjet ćeš zašto toliko mijenja brzinu.

| Mjerilo | API | Najam GPU-a | Vlastiti hardver |
|---|------|------|------|
| Privatnost, GDPR | Tekst ide dobavljaču, koji je izvršitelj obrade | Podaci su na tuđem stroju, a softver vodiš ti | Obrada ostaje kod tebe, obveze ostaju |
| Obrazac troška | Po potrošnji (tokeni) | Po satu, i kad miruje | Unaprijed, zatim struja i održavanje |
| Kontrola | Mala: što dobavljač ponudi | Velika, dok traje najam | Potpuna |
| Trud | Mali | Srednji do velik | Najveći |
| Strop kvalitete | Svi ponuđeni modeli, i zatvoreni | Veliki otvoreni modeli, ako stanu u najmljenu memoriju | Što stane u kupljeni stroj |

Redak o GDPR-u zaslužuje dvije rečenice više, uz napomenu da ovo nije pravni savjet. Čim tekst sadrži osobne podatke, ti ostaješ voditelj obrade na sva tri načina. Tko ih obrađuje za tebe, mora s tobom imati ugovor (članak 28. GDPR-a), a prijenos izvan Europskoga gospodarskog prostora ima vlastita pravila (poglavlje V., članci 44. do 50.). Vlastiti stroj uklanja vanjskog izvršitelja, ali ne i obvezu da odrediš svrhu, rokove čuvanja, zaštitu i zapisnike. Lokalni model nije automatski i usklađen.

## Prag isplativosti: metoda

Jedna brojka koja vrijedi za sve ne postoji, ali metoda je jednostavna i ima pet koraka:

1. **Izmjeri posao.** Koliko zahtjeva mjesečno i koliko ulaznih i izlaznih tokena po zahtjevu?
2. **Izračunaj API.** Tokeni puta cijena, plus sati održavanja.
3. **Izračunaj najam.** Sati rada puta satnica, plus disk i tvoji sati.
4. **Izračunaj vlastiti stroj.** Cijena podijeljena s mjesecima korištenja, plus struja i tvoji sati.
5. **Nađi prag i provjeri kapacitet.** Pri kojem se prometu krivulje sijeku i može li stroj uopće toliko obraditi?

U primjeru koji slijedi **sve su ulazne vrijednosti izmišljene i okrugle**, namjerno. To nisu cijene nijednog dobavljača. Prije bilo kakve odluke zamijeni ih stvarnima, s datumom.

| Ulaz (pretpostavka, zamijeni) | Vrijednost |
|---|---:|
| Zapisnici: zahtjeva mjesečno, tokena ulaz / izlaz | 1320, 300 / 100 |
| Pitanja: zahtjeva mjesečno, tokena ulaz / izlaz | 660, 1500 / 200 |
| Cijena API-ja, ulaz / izlaz, za milijun tokena | 1 / 4 EUR |
| Satnica najma, radni sati mjesečno | 0,50 EUR, 198 h |
| Disk kod najma | 5 EUR |
| Stroj, razdoblje korištenja | 2000 EUR, 36 mjeseci |
| Prosječna snaga, cijena struje | 200 W, 0,20 EUR/kWh |
| Tvoji sati mjesečno: API / najam / vlastito | 1 / 4 / 5 h |
| Cijena tvog sata | 30 EUR |

```text
Promet    1320 + 660                     = 1980 zahtjeva
Ulaz      1320 × 300 + 660 × 1500        = 1 386 000 tokena
Izlaz     1320 × 100 + 660 × 200         =   264 000 tokena

API       1,386 × 1 + 0,264 × 4          =   2,44 EUR tokeni
          2,44 + 1 h × 30                =  32,44 EUR

Najam     198 × 0,50 + 5 + 4 h × 30      = 224,00 EUR

Vlastito  2000 / 36                      =  55,56 EUR stroj
          0,2 kW × 198 h × 0,20          =   7,92 EUR struja
          55,56 + 7,92 + 5 h × 30        = 213,48 EUR

Po zahtjevu na API-ju   2,44 / 1980      = 0,001233 EUR
Prag vlastito           (213,48 - 30) / 0,001233
                                         = oko 149 000 zahtjeva
Prag najam              (224 - 30) / 0,001233
                                         = oko 157 000 zahtjeva
```

Od praga se oduzima 30 EUR jer API uvijek nosi taj sat održavanja, a tokene plaća po zahtjevu. Tokeni pri ovom prometu koštaju 2,44 EUR, a najveći su trošak na svakom putu tvoji sati. Vlastiti stroj postaje jeftiniji tek pri oko 75 puta većem prometu. Mnoge to iznenadi, pa računaj prije kupnje. Račun je k tome blag prema vlastitom putu jer ne sadrži početno postavljanje, kvarove ni rezervni stroj.

Zato pogledaj što pomiče rezultat. Ako je model koji ti treba deset puta skuplji po tokenu, prag pada na oko 15 000 zahtjeva, što je samo 7,5 puta više od početnog prometa. Ako zapisnike možeš obrađivati u skupini, jedan sat dnevno, 22 sata najma daju 136 EUR umjesto 224 EUR.

Peti se korak najčešće preskače. Prag od 149 000 zahtjeva u 198 radnih sati znači oko 750 zahtjeva na sat, odnosno prosječno oko 28 tokena u sekundi generiranja i oko 146 tokena u sekundi ulaza, bez ikakvih vršnih opterećenja. Stroj koji to ne može ne dostiže prag, bez obzira na to što račun kaže. Kako iz hardvera izračunati gornju granicu brzine, naučit ćeš u poglavlju 8.

::: {.vjezba}
**Vježba: tvoj račun** `samo čitanje` · 20 min

Uzmi jedan stvarni posao koji sada radiš preko API-ja. S računa ili iz zapisa o upotrebi prepiši zahtjeve i tokene za prošli mjesec. Zamijeni sve retke tablice stvarnim vrijednostima, zapiši im datum i izračunaj prag. Spremi rezultat: na njega se možeš vratiti nakon poglavlja 8, kad znaš provjeriti i kapacitet.
:::

## Što može ovaj laptop

Sve brojke u knjizi izmjerene su na slabom stroju: laptop s procesorom Intel i5-10210U (osam dretvi, u mjerenjima četiri), 16 GB RAM-a, bez GPU-a, Windows 11 Pro, llama.cpp b12110. Na njemu radi Gemma 4 E2B u datoteci od 3,11 GB: zauzima oko 2,8 GB radne memorije i generira između 5,6 i 12,1 tokena u sekundi, ovisno o alatu, iako su model i dan isti. Qwen3-4B, datoteka od 2,50 GB, zauzima oko 4,9 GB i kroz `llama-cli` generira 5,7 do 6,3 tokena u sekundi. Zašto veća datoteka ovdje troši manje memorije, tema je poglavlja 8. Odgovor Gemme od 107 tokena kroz `llama-server` trajao je oko 10,5 s. Kvaliteta je skromna: na pitanje o perilici Gemma je dala upotrebljiv, ali nespretan odgovor, a Qwen je izmislio "vodni kolut" i "ventilatorno vratilo". Takav stroj nije za pogon, ali model od 2,5 do 3 GB na njemu stvarno radi, a to je dovoljno za učenje gotovo cijelog zanata. Tvoje će brojke biti drukčije, zato ih izmjeri.

## Kvaka d.o.o.

Da račun i mjerenja ne bi visjeli u zraku, kroz knjigu nas prati tvrtka **Kvaka d.o.o.**, servis kućanskih aparata. Tvrtka je izmišljena, kao i svi njezini podaci. Ima dva posla.

**Pitanja iz priručnika.** Tehničar na terenu pita, recimo, koliko vrijedi jamstvo na zamijenjeni dio. Dokumentacija se stalno mijenja, pa bi model koji je napamet naučio prošlogodišnju inačicu davao zastarjele odgovore. Tu pomaže RAG: sustav najprije pronađe odgovarajuće dijelove priručnika, ubaci ih u prompt, a model odgovara iz njih. Detalji su u poglavlju 13.

**Servisni zapisnici.** Tehničari pišu slobodno i žurno, a tvrtki treba strojno čitljiv zapis s četiri stalna polja. Ovo je jedan ručno napisan primjer:

```text
Vešmašina na Peščenici stane usred programa i bubanj ostane
pun vode. Začepljenja nema, filtar čist, motorčić pumpe ne
reagira. Dogovoreno za četvrtak.
```

```json
{
  "uredaj": "perilica rublja",
  "kvar": "ne izbacuje vodu",
  "dio": "pumpa",
  "hitnost": "srednja"
}
```

Oblik se ovdje stalno ponavlja, a tehničari imaju svoj rječnik, pa je ovo dobar kandidat za LoRA adapter: mali adapter koji se trenira na primjerima i modelu dodaje naviku, bez promjene njegovih težina. Hoće li ga Kvaka stvarno trebati, odlučuje se u poglavlju 13, jer su prompt i strukturirani izlaz možda već dovoljni.

Kvaka unaprijed zapisuje što znači "gotovo":

| Cilj | Granica | Što znači |
|---|---|---------|
| Točnost po polju | ≥ 90 % | udio točnih polja na zlatnom skupu |
| Latencija p95 | ≤ 5 s | 95 % zahtjeva završi unutar tog vremena |
| Mjesečni trošak | ≤ 150 EUR | izmišljen limit, sve stavke iz računa |

Zlatni skup (gold set) je 40 zapisnika s poznatim točnim odgovorima, a u poglavlju 9 učiš kako nastaje. Bez ovakvih ciljeva svaka se promjena samo čini boljom. S njima se ne možeš zavarati, ni kad ih ne dosegneš: na mjernom laptopu točnost od 90 % nije dosegnuta, a knjiga to pokazuje u brojkama.

Primijeni limit na račun iz prošlog odjeljka. Uz izmišljene ulaze i limit od 150 EUR prolazi samo API, s 32,44 EUR. Vlastiti stroj od 213,48 EUR i stalni najam od 224 EUR ne prolaze. Kad bi zapisnici sadržavali imena i adrese stranaka, a ugovor s klijentom priječio slanje dobavljaču, odluka bi se otvorila iznova: trošak je samo jedan stupac, ali mora biti poznat prije rasprave.

## Karta knjige

![Karta knjige: vozi, otvori, mjeri, mijenjaj, isporuči, s poglavljima 1 do 19 i povratkom s mijenjanja na mjerenje](slike/karta-knjige.svg)

Jezgra su poglavlja 1 do 16. Poglavlja 17 i 18 izborna su radionica, za one koji žele kirurgiju modela i posluživanje (serving) većih razmjera. Poglavlje 19 prolazi cijeli put s Kvakom i možeš ga čitati i bez izbornih poglavlja. Pogledaj strelicu povratka na slici: nakon svake promjene mjeri ponovno.

Svaka vježba nosi oznaku s potrebnim RAM-om, diskom i vremenom:

- `CPU`: radi na običnom računalu i autor je vježbu stvarno pokrenuo
- `najam GPU-a`: traži karticu koju možeš unajmiti na nekoliko sati
- `samo čitanje`: računaš ili procjenjuješ, bez pokretanja

Ako kod nije pokrenut, odmah iza njega stoji okvir koji to kaže i objašnjava zašto. U mapi `prilozi/` nalaze se skripte i podaci za vježbe, uključujući sintetičke zapisnike i zlatni skup. Skripte su pisane i pokretane na Windowsu 11, a neke traže Git Bash.

## Što ti treba, a što knjiga neće

Za početak ti trebaju računalo, internet, lokalni disk koji se ne sinkronizira u oblak i spremnost da kopiraš naredbe u terminal. Prva je vožnja na mjernom stroju trebala oko 3 GB diska i oko 2,8 GB memorije za Gemmu. U jezgri knjige GPU treba tek pravi trening u poglavlju 16, a tada ga možeš unajmiti.

Ova knjiga ne izvodi backpropagation i ne uči te PyTorch, a ni za istraživački rad te neće pripremiti. Objasnit će što trening radi i kako ga čitati, ali ne i matematiku u pozadini. Neće ti dati ni rang-listu najboljih modela jer takve liste brzo zastarijevaju i međusobno se ne slažu. Umjesto toga pokazat će ti kako izmjeriti koji je model najbolji za tvoj posao. Regulativu spominjemo da znaš što pitati, ali to nije pravni savjet.

Alati stare brzo. Sve u knjizi datirano je **studenim 2026.**: naredbe, inačice i stanje modela. Ako naredba više ne radi, najprije usporedi inačice. Ideje stare sporije: računica memorije, zlatni skup i navika ponovnog mjerenja vrijedit će i kad se imena modela promijene.

::: {.kvar}
**Simptom → uzrok**

- Račun kaže da se vlastiti stroj isplati, a prijedlog ne prolazi → često su izostavljeni tvoji sati ili provjera kapaciteta. Dodaj oboje.
- Tokeni izgledaju skupo, a ukupni iznos je malen → gledaš cijenu za milijun tokena, a ne svoj promet. Pomnoži.
- Lokalni model "ne odgovara", a greške nema → provjeri ograničenje tokena i razmišljanje, kao u primjeru s početka poglavlja.
:::

## Sažetak

Ova knjiga vodi iskusnog korisnika AI alata do mehaničarskog zanata: pokrenuti, otvoriti, izmjeriti, promijeniti i isporučiti model. Držati težine znači dobiti stabilnost, privatnost, uvid i mogućnost preinake, ali i preuzeti sve kvarove, a API je često ispravan izbor. Odluku donosi račun s tvojim brojkama i provjerom kapaciteta, uz pravnu procjenu podataka. Izmišljena Kvaka d.o.o. kroz cijelu knjigu ima dva posla, RAG za priručnik i LoRA za zapisnike, te mjerljive ciljeve. U poglavlju 2 pokrećeš prvi model jednom naredbom.
