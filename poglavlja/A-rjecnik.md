# Rječnik

Pojmovi su poredani po engleskom nazivu. Iza strelice je naziv koji knjiga koristi, a broj upućuje na poglavlje s glavnim objašnjenjem. Gdje nema strelice, naziv ostaje izvoran.

| Pojam | Značenje | Pogl. |
|---|-----|-|
| abliteration → abliteracija | namjerno uklanjanje odbijanja iz težina; samo kao pojam | 17 |
| accuracy per field → točnost po polju | udio točnih vrijednosti za svako polje JSON-a | 9 |
| active parameters → aktivni parametri | parametri koji se stvarno računaju za jedan token | 6 |
| adapter | male dodatne težine koje mijenjaju ponašanje modela | 15 |
| attention → pažnja | dio sloja u kojem tokeni čitaju jedni druge | 6 |
| AWQ | stariji kvantizirani oblik za GPU; AutoAWQ je napušten | 18 |
| backpropagation → propagacija unatrag | računa gradijente; knjiga je ne izvodi | 15 |
| base model → bazni model, baza | model bez chat treninga; u LoRA-i model ispod adaptera | 3 |
| batch | skupina primjera obrađena u jednom koraku | 15 |
| bpw (bits per weight) → bita po težini | prosječan broj bita za jednu težinu | 7 |
| calibration → kalibracija | skale se određuju iz uzorka tvojih podataka | 18 |
| chat template → predložak, chat predložak | program koji poruke pretvara u niz za model | 5 |
| chunk → komad | dio dokumenta koji RAG zasebno indeksira i dohvaća | 13 |
| context → kontekst | koliko teksta model drži u glavi, u tokenima | 8 |
| continuous batching → kontinuirano spajanje u serije | sastav serije mijenja se u svakom koraku | 18 |
| cross-entropy → unakrsna entropija | uobičajeni gubitak: −ln P točnog tokena | 15 |
| data leakage → curenje | validacija je već vidjela iste ili slične primjere | 14 |
| embedding model → ugradbeni model | model koji tekst pretvara u vektor za RAG | 13 |
| embedding (ugrađivanje) | token ili tekst zapisan kao vektor brojeva | 6 |
| EOS → token kraja | posebni token kojim model završava odgovor | 4 |
| epoch → epoha | jedan prolaz kroz cijeli skup za trening | 15 |
| expert → stručnjak | jedna od usporednih MLP mreža u MoE-u | 6 |
| fine-tuning → fino podešavanje | daljnji trening gotovog modela na tvojim podacima | 13 |
| floating point → pomični zarez | zapis broja znakom, eksponentom i mantisom | 7 |
| FP8, FP16, FP32, BF16 | formati brojeva s 8, 16 i 32 bita | 7 |
| GGUF | jedna datoteka s težinama, tokenizatorom i predloškom | 10 |
| gold set → zlatni skup | 40 odvojenih primjera za svako mjerenje | 9 |
| GQA → grupna pažnja | glave dijele ključeve i vrijednosti, pa treba manje memorije | 6 |
| gradient → gradijent | smjer u kojem gubitak raste, za svaki parametar | 15 |
| grammar → gramatika | pravila koja ograničavaju što model smije ispisati | 13 |
| head → glava | jedan neovisan komad pažnje | 6 |
| i-quants → IQ | porodica kvantizacije za vrlo malo bita | 11 |
| imatrix | izmjerene aktivacije kojima se važe pogreška zaokruživanja | 11 |
| k-quant → k-kvant | blokovna kvantizacija, na primjer Q4_K_M | 11 |
| KLD (Kullback–Leibler divergence) | razlika izlaza kvantiziranog i punog modela | 12 |
| KV cache | memorija u kojoj model čuva K i V prošlih tokena | 8 |
| layer → sloj | pažnja i MLP zajedno; model ih slaže u niz | 6 |
| learning rate → stopa učenja | veličina koraka pri promjeni težina | 15 |
| load test → test opterećenja | mjerenje uz više istodobnih klijenata | 18 |
| logits → logiti | sirovi brojevi za svaki token prije uzorkovanja | 6 |
| looped model → model s petljama | isti blokovi ponavljaju se više puta za svaki token | 19 |
| LoRA | ispravak matrice kao umnožak dviju tankih matrica | 15 |
| loss → gubitak | broj koji kaže koliko model griješi | 15 |
| master | najprecizniji oblik modela koji imaš; iz njega kvantiziraš | 11 |
| merged model → spojeni model | adapter ugrađen u težine baze | 15 |
| merging → spajanje | računanje s težinama više modela, bez treninga | 17 |
| MLP | dio sloja koji prerađuje ono što je pažnja prikupila | 6 |
| model card → kartica modela | README modela: namjena, ograničenja, licenca | 3 |
| MoE (Mixture of Experts) | građa u kojoj token prolazi samo kroz dio stručnjaka | 6 |
| NF4 (NormalFloat 4) | 4-bitni zapis za QLoRA; nije isto što i Q4 u GGUF-u | 15 |
| NVFP4 | 4-bitni broj s pomičnim zarezom, blok od 16 elemenata | 18 |
| open weight → model otvorenih težina | težine su javne, a podaci i postupak najčešće nisu | 3 |
| overfitting → prenaučenost | model pamti primjere, a validacija ne napreduje | 15 |
| overflow → prelijevanje | broj prevelik za format postaje `Inf` | 7 |
| p95 latency → latencija p95 | 95 % zahtjeva završi unutar tog vremena | 18 |
| parameter → parametar | jedan broj u težinama | 7 |
| partial offload → djelomično prebacivanje | dio slojeva je na kartici, a dio u RAM-u | 8 |
| perplexity → perpleksnost, PPL | koliko model iznenađuje stvarni tekst; manje je bolje | 12 |
| pickle | Pythonov zapis koji pri učitavanju može izvršiti kod | 10 |
| prefill | obrada prompta prije prvog generiranog tokena | 8 |
| prompt injection → podmetnuta naredba | uputa skrivena u dohvaćenom tekstu | 13 |
| QLoRA | LoRA trening na bazi kvantiziranoj u NF4 | 15 |
| quantization → kvantizacija | zapis težina s manje bita, uz gubitak preciznosti | 11 |
| RAG | dohvati dijelove dokumenata i ubaci ih u prompt | 13 |
| rank → rang (r) | koliko smjerova ispravak ima; određuje veličinu adaptera | 15 |
| reasoning, thinking → razmišljanje | skriveni tekst prije odgovora; troši proračun tokena | 5 |
| repeat penalty → kazna za ponavljanje | smanjuje izglede već viđenih tokena; kvari JSON | 6 |
| revision → revizija | točna inačica repozitorija, zadana hashom commita | 10 |
| safetensors | format samo s podacima, bez izvršnog koda | 10 |
| sampling → uzorkovanje | izbor sljedećeg tokena iz vjerojatnosti | 6 |
| scale → skala | broj kojim se razine vraćaju u stvarne vrijednosti | 11 |
| seed, sjeme | početna vrijednost za ponovljivo uzorkovanje | 6 |
| serving → posluživanje | model radi kao usluga za druge programe | 18 |
| shard → dio | jedna od datoteka velikog modela | 3 |
| sliding window → klizni prozor | sloj pamti samo zadnjih nekoliko tokena | 8 |
| slot | dio konteksta za jednog korisnika, `-c` dijeljen s `-np` | 8 |
| special tokens → posebni tokeni | oznake uloga, početka i kraja koje nisu običan tekst | 4 |
| streaming → strujanje | odgovor stiže token po token | 4 |
| structured output → strukturirani izlaz | izlaz prisiljen na zadani oblik, najčešće JSON | 13 |
| system message → sistemska poruka | stalna uputa modelu na početku niza | 5 |
| target modules → ciljni moduli | matrice na koje se stavlja adapter | 15 |
| task vector → vektor zadatka | razlika između podešenog i baznog modela | 17 |
| temperature → temperatura | koliko je uzorkovanje slučajno; 0 je najvjerojatniji token | 6 |
| tensor → tenzor | imenovana tablica brojeva u težinama | 7 |
| throughput → tok/s ukupno | svi tokeni podijeljeni s ukupnim vremenom testa | 18 |
| TIES, DARE | metode spajanja koje čiste vektore zadatka | 17 |
| token | komad teksta koji model vidi kao jednu jedinicu | 4 |
| tokenizer → tokenizator | program s rječnikom koji tekst pretvara u tokene | 4 |
| tool call → poziv alata | model predlaže poziv, a tvoj ga kod izvodi | 13 |
| top-k, top-p | uzorkovanje samo iz najvjerojatnijih tokena | 6 |
| training set → skup za trening | primjeri iz kojih model uči | 14 |
| trust_remote_code | dopušta izvršavanje koda iz repozitorija modela | 10 |
| TTFT | vrijeme od slanja zahtjeva do prvog tokena | 18 |
| unified memory → jedinstvena memorija | CPU i GPU dijele isti RAM, kao kod Applea | 8 |
| validation set → validacijski skup | primjeri izvan treninga za praćenje tijekom treninga | 14 |
| vLLM | poslužitelj za GPU, za više korisnika istodobno | 18 |
| VRAM | memorija grafičke kartice | 8 |
| warmup → zagrijavanje | stopa učenja postupno raste na početku treninga | 15 |
| weights → težine | svi brojevi naučeni u treningu; to je model | 3 |
| YaRN | produljuje kontekst preračunavanjem položaja | 17 |
