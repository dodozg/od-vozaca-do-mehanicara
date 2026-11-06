# Provjerene činjenice (stanje 4. 11. 2026.)

## Alati
- llama.cpp: github.com/ggml-org/llama.cpp. Tim ggml.ai prešao je u Hugging Face 20. 2. 2026.; licenca MIT ostaje. Alati: llama-cli, llama-server, llama-quantize, llama-imatrix, llama-perplexity, convert_hf_to_gguf.py.
- llama-quantize: `--imatrix`, `--pure`, `--allow-requantize`, `--leave-output-tensor`, `--output-tensor-type`, `--token-embedding-type`, `--tensor-type`, `--prune-layers`, `--override-kv`, `--keep-split`. Tipovi: IQ1_S, IQ1_M, IQ2_XXS, IQ2_XS, IQ2_S, IQ2_M, IQ3_XXS, IQ3_XS, IQ3_S, IQ3_M, IQ4_XS, IQ4_NL, Q2_K_S, Q2_K, Q3_K_S, Q3_K_M, Q3_K_L, Q4_K_S, Q4_K_M, Q5_K_S, Q5_K_M, Q6_K, Q8_0, F16.
- README llama.cpp za Llama 3.1 8B: Q4_K_M 4,58 GiB / 4,8944 bpw; Q8_0 7,95 GiB / 8,5008 bpw; F16 14,96 GiB / 16,0005 bpw; IQ1_S 1,87 GiB / 2,0042 bpw. Izvorno 32,1 GB, Q4_K_M 4,9 GB; 70B: 280,9 → 43,1 GB; 405B: 1625,1 → 249,1 GB. "memory and disk requirements are the same".
- Gubitak se mjeri perpleksnošću (ppl) i Kullback–Leiblerovom divergencijom (kld). Bazni logiti za KLD na Wikitext-2: 37 GiB za LLaMA 3 (README perplexity), pa za vježbu uzmi kratak tekst.
- imatrix (PR #4861): model se pušta kroz tekst, mjere se prosječni kvadrati aktivacija koje ulaze u tenzor, a kvantizator time važe pogrešku zaokruživanja: `F = [Sum_j (q_j - w_j) a_j]^2`. Sve težine ostaju na istom broju bita. Autor preporučuje oko 50 tisuća tokena; računanje je izvorno radilo samo na CPU-u, a 7B je trajao oko 10 min na 32 jezgre. output.weight i token_embd.weight se po zadanom ne važu. Izlaz je imatrix.gguf (`--output-format {gguf,dat}`).
- Na istom stroju Ollama i LM Studio (na NVIDIA/AMD) koriste llama.cpp. Ollama API port 11434; llama-server zadani 8080. LM Studio ima headless poslužitelj (llmster) od siječnja 2026. Na Apple Siliconu LM Studio ima MLX.
- vLLM: službeno Linux; za Windows WSL. Preporučeno kvantiziranje: LLM Compressor (FP8 W8A8, INT4 W4A16, INT8...). AutoAWQ je napušten, ali vLLM i dalje učitava AWQ modele. `--kv-cache-dtype` prima auto, fp8, fp8_e4m3, fp8_e5m2; bez kalibracije fp8 ima skale 1,0, preporučena je kalibracija. NVFP4 i MXFP8 kroz ModelOpt: `--quantization modelopt_fp4` (NVFP4) odnosno `--quantization modelopt_mxfp8` (MXFP8). Tiha degradacija: provjeri u logu da su učitane nativne FP4 jezgre.
- NVFP4: 4-bitni float, NVIDIA Blackwell ili noviji, blokovi od 16 elemenata, oko 4,5 bita sa skalama, kalibracija potrebna. MXFP8/MXFP4: OCP MX specifikacija, grupe od 32. FP8 W8A8: Ada, Hopper, Blackwell.
- Transformers v5: `BitsAndBytesConfig(load_in_4bit=True)` kroz `quantization_config`; `config.rope_parameters`; `safe_serialization` uklonjen; zadani shard 50 GB; `use_auth_token` → `token`.
- Axolotl: `type: chat_template` s `field_messages` (u v0.21.1 `message_field_*` je zastario, nasljednik `message_property_mappings`); `chat_template: tokenizer_default`. ShareGPT zastarijeva.
- Unsloth: pogodan za jedan GPU; treniranje ne radi na CPU-u. Axolotl i TRL za više kartica i posebne ciljeve (DPO, GRPO).
- Mergekit: LGPL v3 od 31. 10. 2025. Metode: linear, slerp, nuslerp, multislerp, karcher, task_arithmetic, ties, dare_linear, dare_ties, della, della_linear, breadcrumbs, breadcrumbs_ties, sce, model_stock, nearswap, arcee_fusion, passthrough. "All non-vocabulary dimensions must match". `mergekit-yaml config.yml ./izlaz [--cuda] [--lazy-unpickle] [--allow-crimes]`. mergekit-moe: Mistral ili Llama modeli iste veličine; izlaz Mixtral, DeepSeek MoE ili Qwen MoE.

## Modeli (samo primjeri, ne rang-lista)
- Apache 2.0, nezaključani: Gemma 4 (`google/gemma-4-E2B-it`; GGUF `unsloth/gemma-4-E2B-it-GGUF`, Q4_K_M 3,11 GB), Qwen3 (`Qwen/Qwen3-4B-GGUF`, Q4_K_M 2,5 GB), SmolLM3 (`HuggingFaceTB/SmolLM3-3B`, 6,15 GB safetensors).
- Llama 3 je zaključan i star (2024.); koristi se samo za računicu.
- Rang-liste se ne slažu (listopad 2026.: Kimi K3, MiMo-V2.6-Pro, DeepSeek V4.1 Flash...). Kimi K3: 2,8 bilijuna ukupno, 104 milijarde aktivnih parametara, što je dobar primjer MoE-a (sekundarni izvor). Muse Spark Open ima vlastitu licencu; Kimi K3 i GLM-5.3 imaju posebne uvjete, DeepSeek V4.1 Flash MIT (sekundarni izvori, provjeriti licencu).
- NVIDIA Dory1.0-4B (16. 10. 2026.; `nvidia/NVIDIA-Nemotron-Labs-Dory1.0-4B-BF16`, -GGUF, -NVFP4): OpenMDW-1.1; looped; 8 ulaznih + 20 ponavljajućih + 8 izlaznih blokova; ulaz se ponovno ubacuje u svaku petlju; broj petlji mijenja se pri izvođenju bez ponovnog treniranja; zadano 2 petlje; kontekst do 256K; last-loop KV cache drži KV memoriju ravnom; prednaučen u NVFP4; engleski. Istraživački prethodnik: arXiv 2311.12424, gdje petlje nakon trenirane granice brzo divergiraju.

## Sigurnost
- JFrog 2024.: stotinjak zlonamjernih modela na HF, pickle s __reduce__. PickleScan se može zaobići.
- Radionica ICLR 2026 (Trustworthy AI), arXiv 2602.04653: backdoor preko Jinja chat predloška u GGUF-u bez diranja težina; HF skeniranje ne analizira logiku predložaka.
- Abliteracija: Arditi i sur., odbijanje je uglavnom jedan smjer u aktivacijama; zahvat ga uklanja iz težina. arXiv 2512.13655: matematičko rezoniranje najosjetljivije, GSM8K od +1,51 do −18,81 postotnih bodova. U knjizi samo pojam, bez postupka.

- convert_hf_to_gguf za neke arhitekture koristi trust_remote_code=True, dakle pretvorba može izvršiti kod iz repozitorija (llama.cpp conversion/base.py).

## Regulativa (nije pravni savjet)
- AI Act, smjernice za GPAI (srpanj 2025.): onaj tko podešava model postaje pružatelj novog modela samo ako bitno promijeni općenitost, sposobnosti ili sustavni rizik; orijentir je više od trećine računalnih resursa treniranja izvornog modela; ako nije poznat, trećina od 10^23 FLOP. Obveze se ograničavaju na samu izmjenu.
- Digitalni omnibus: Uredba (EU) 2026/1744, na snazi 27. 7. 2026. (sekundarni izvori): visokorizični sustavi iz Priloga III odgođeni na 2. 12. 2027., ugrađeni u proizvode na 2. 8. 2028. Članak 50 i ovlasti AI Officea nad GPAI od 2. 8. 2026.

## Izračunato (tools/racun.py)
KV cache = 2·c·L·h·d·b/8. Llama 3 8B (L=32, h=8, d=128), FP16: 4096 tokena 0,54 GB; 32768: 4,29 GB; 131072: 17,18 GB. FP8 polovica, 4-bit četvrtina. Llama 3 70B (L=80), FP16: 32768: 10,74 GB; 131072: 42,95 GB.
Llama 3 8B: ugrađivanja i glava 1,05 mlrd; pažnja 1,34; MLP 5,64; ukupno 8,03 mlrd. MoE 3× ≈ 19,3 mlrd, a ne 22.
Puni trening 8B: težine 16 + gradijenti 16 + AdamW 64 = 96 GB, plus aktivacije 16–32 GB.
LoRA na 4096×4096, r=16: 16 777 216 → 131 072 parametara (0,78 %). Cijeli 8B, svih 7 projekcija: r=8 21 M (42 MB), r=16 42 M (84 MB), r=32 84 M (168 MB), r=64 168 M (336 MB, 2,09 % modela).
Dimenzioniranje 8B Q4_K_M, kontekst 32768, KV FP16, 1 GB sustavno: 5,13 + 4,29 + 1,0 = 10,43 GB.
Gornja granica brzine ≈ propusnost / veličina modela. DDR5 dvokanalni 80 GB/s, model 4,9 GB: 16 tok/s. M4 Max 546 GB/s: 111 tok/s. RTX 4090 1008 GB/s: 206 tok/s. Stvarne su brzine niže.

## Kvaka d.o.o. (fiktivno, zajedničko svim poglavljima)
Ciljevi: točnost po polju ≥ 90 %, p95 latencija ≤ 5 s, trošak ≤ 150 EUR mjesečno (izmišljena granica). Na mjernom laptopu cilj točnosti nije dosegnut (najbolje 74,4 %, L8). Pogl. 1 obećava: pogl. 8 objašnjava zašto Gemma s većom datotekom troši manje RAM-a (klizni prozor, L5) i kako izračunati gornju granicu brzine; pogl. 9 kako se radi zlatni skup; pogl. 13 je li LoRA uopće potreban.

## Nadopune (studeni 2026.)
- llama-server: novi README navodi zadani port 9931, a starije upute 8080. Naredbe u knjizi uvijek izričito navode `--port 8080`. Izgradnja b12110 je ona na kojoj je mjereno; najnovija oznaka je v0.9.0.
- Gemma 4 E2B: "E" = effective; 2,3 mlrd efektivnih parametara, 5,1 mlrd s embeddingom (model card).
- Poglavlje 3 obećava da 17 pokriva nepodudaran broj slojeva (L10); poglavlje 4 da 12 pokazuje kako hrvatski pati pri kvantizaciji, a 17 Mergekit i dodavanje tokena; poglavlje 2 da 8 objašnjava zašto Qwenova manja datoteka troši više memorije te GPU pakete i Apple čipove, 5 razmišljanje i prazne odgovore, 13 API i pozive alata, 9 usporedbu modela.
- Ispravak mjerenja: u mjerenja.md, "Što je iznenadilo" 5, "pet puta manji model je pet puta brži" je pogrešno; podaci L6: Q8_0 → Q2_K 2,6 puta manji, 2,2 puta brži. Vrijednosti `peakWS_MB` su zapravo MiB. `-c` je ukupan kontekst koji `-np` dijeli na slotove: 4 korisnika po 8192 tokena traže `-c 32768`. Poglavlje 8 obećava `-ctk`/FP8 za KV cache u poglavlju 18.
